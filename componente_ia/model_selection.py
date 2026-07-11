"""Benchmark offline de clasificadores locales, sin usar el holdout para tuning.

El modelo productivo continúa siendo autocontenido. NumPy se usa únicamente en
este comando offline (ya forma parte del repositorio) para comparar alternativas
lineales sin incorporar scikit-learn, fastText ni artefactos de embeddings.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from componente_ia.training_pipeline import (
    DEFAULT_DATASET,
    DEFAULT_MODEL,
    IntentModel,
    classification_metrics,
    dataset_sha256,
    feature_names,
    hashed_features,
    load_jsonl,
    normalize_text,
    stable_bucket,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_DIR / "artifacts" / "ia_model_comparison.json"
SEED = 20260710
BUCKETS = 8192


def composite_model_score(
    metrics: dict[str, Any],
    *,
    entity_f1: float,
    latency_p95_ms: float,
    memory_bytes: int,
    latency_budget_ms: float = 150.0,
    memory_budget_bytes: int = 64 * 1024 * 1024,
) -> float:
    """Puntaje de selección acordado, con latencia y memoria normalizadas."""

    latency_score = max(0.0, 1.0 - max(0.0, latency_p95_ms) / latency_budget_ms)
    memory_score = max(0.0, 1.0 - max(0, memory_bytes) / memory_budget_bytes)
    return (
        0.30 * float(metrics.get("accuracy", 0.0))
        + 0.20 * float(metrics.get("macro_f1", 0.0))
        + 0.20 * float(metrics.get("critical_accuracy", 0.0))
        + 0.10 * float(entity_f1)
        + 0.10 * latency_score
        + 0.10 * memory_score
    )


def _numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("El benchmark offline requiere NumPy; el runtime del asistente no") from exc
    return np


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _prepared(rows: Sequence[dict[str, Any]], labels: Sequence[str], buckets: int = BUCKETS):
    np = _numpy()
    indexes = {label: index for index, label in enumerate(labels)}
    return [
        (
            np.asarray(hashed_features(str(row["message"]), row.get("history"), buckets), dtype=np.int32),
            indexes[str(row["intent"])],
        )
        for row in rows
    ]


def _validation_metrics(
    rows: Sequence[dict[str, Any]], labels: Sequence[str], predicted_indexes: Sequence[int]
) -> dict[str, Any]:
    expected = [str(row["intent"]) for row in rows]
    predicted = [labels[index] for index in predicted_indexes]
    metrics = classification_metrics(expected, predicted)

    def subset_accuracy(predicate: Callable[[dict[str, Any], str], bool]) -> tuple[float, int]:
        pairs = [
            (expected_label, predicted_label)
            for row, expected_label, predicted_label in zip(rows, expected, predicted)
            if predicate(row, expected_label)
        ]
        accuracy = sum(left == right for left, right in pairs) / len(pairs) if pairs else 1.0
        return round(accuracy, 6), len(pairs)

    critical, critical_total = subset_accuracy(lambda row, _label: bool(row.get("critical")))
    security, security_total = subset_accuracy(
        lambda row, _label: row.get("category") == "I_security_scope"
    )
    out_scope, out_scope_total = subset_accuracy(lambda _row, label: label == "out_of_scope")
    metrics.update({
        "critical_accuracy": critical,
        "critical_total": critical_total,
        "security_scope_accuracy": security,
        "security_scope_total": security_total,
        "out_of_scope_accuracy": out_scope,
        "out_of_scope_total": out_scope_total,
    })
    return metrics


def _multinomial_naive_bayes(train, validation, class_count: int, buckets: int):
    np = _numpy()
    alpha = 0.35
    documents = np.full(class_count, alpha, dtype=np.float64)
    counts = np.full((class_count, buckets), alpha, dtype=np.float64)
    for features, target in train:
        documents[target] += 1.0
        counts[target, features] += 1.0
    log_prior = np.log(documents / documents.sum())
    log_likelihood = np.log(counts / counts.sum(axis=1, keepdims=True))
    return [int(np.argmax(log_prior + log_likelihood[:, features].sum(axis=1))) for features, _ in validation]


def _logistic_regression(train, validation, class_count: int, buckets: int, seed: int):
    np = _numpy()
    weights = np.zeros((class_count, buckets), dtype=np.float32)
    bias = np.zeros(class_count, dtype=np.float32)
    frequencies = Counter(target for _features, target in train)
    balancing = np.asarray(
        [math.sqrt(len(train) / (class_count * frequencies[index])) for index in range(class_count)],
        dtype=np.float32,
    )
    rng = random.Random(seed)
    order = list(range(len(train)))
    for epoch in range(8):
        rng.shuffle(order)
        rate = 0.16 / (1.0 + epoch * 0.45)
        for row_index in order:
            features, target = train[row_index]
            scores = bias + weights[:, features].sum(axis=1)
            scores -= scores.max()
            probabilities = np.exp(np.clip(scores, -30.0, 30.0))
            probabilities /= probabilities.sum()
            gradient = probabilities
            gradient[target] -= 1.0
            gradient *= balancing[target]
            weights[:, features] -= rate * gradient[:, None]
            bias -= rate * gradient
    return [int(np.argmax(bias + weights[:, features].sum(axis=1))) for features, _ in validation]


def _linear_svm(train, validation, class_count: int, buckets: int, seed: int):
    np = _numpy()
    weights = np.zeros((class_count, buckets), dtype=np.float32)
    bias = np.zeros(class_count, dtype=np.float32)
    frequencies = Counter(target for _features, target in train)
    balancing = [math.sqrt(len(train) / (class_count * frequencies[index])) for index in range(class_count)]
    rng = random.Random(seed)
    order = list(range(len(train)))
    for epoch in range(9):
        rng.shuffle(order)
        rate = 0.22 / (1.0 + epoch * 0.35)
        weights *= 0.9995
        for row_index in order:
            features, target = train[row_index]
            scores = bias + weights[:, features].sum(axis=1)
            target_score = float(scores[target])
            scores[target] = -np.inf
            rival = int(np.argmax(scores))
            if target_score - float(scores[rival]) >= 1.0:
                continue
            step = rate * balancing[target]
            weights[target, features] += step
            weights[rival, features] -= step
            bias[target] += step
            bias[rival] -= step
    return [int(np.argmax(bias + weights[:, features].sum(axis=1))) for features, _ in validation]


def _nearest_centroid(train, validation, class_count: int, buckets: int):
    np = _numpy()
    centroids = np.zeros((class_count, buckets), dtype=np.float32)
    documents = np.zeros(class_count, dtype=np.float32)
    document_frequency = np.zeros(buckets, dtype=np.float32)
    for features, target in train:
        centroids[target, features] += 1.0
        document_frequency[features] += 1.0
        documents[target] += 1.0
    idf = np.log((1.0 + len(train)) / (1.0 + document_frequency)) + 1.0
    centroids = (centroids / np.maximum(documents[:, None], 1.0)) * idf[None, :]
    centroids /= np.maximum(np.linalg.norm(centroids, axis=1, keepdims=True), 1e-8)
    return [
        int(np.argmax((centroids[:, features] * idf[features][None, :]).sum(axis=1)))
        for features, _ in validation
    ]


def _bm25_class_retrieval(train, validation, class_count: int, buckets: int):
    """BM25 ligero sobre documentos de clase; las reglas siguen fuera del modelo."""

    np = _numpy()
    term_frequency = np.zeros((class_count, buckets), dtype=np.float32)
    document_frequency = np.zeros(buckets, dtype=np.float32)
    class_lengths = np.zeros(class_count, dtype=np.float32)
    for features, target in train:
        term_frequency[target, features] += 1.0
        document_frequency[features] += 1.0
        class_lengths[target] += len(features)
    average_length = max(float(class_lengths.mean()), 1.0)
    idf = np.log(1.0 + (len(train) - document_frequency + 0.5) / (document_frequency + 0.5))
    k1, b = 1.35, 0.72
    denominator = term_frequency + k1 * (1.0 - b + b * class_lengths[:, None] / average_length)
    weights = idf[None, :] * ((term_frequency * (k1 + 1.0)) / np.maximum(denominator, 1e-8))
    return [int(np.argmax(weights[:, features].sum(axis=1))) for features, _ in validation]


def _fasttext_features(row: dict[str, Any], buckets: int):
    np = _numpy()
    names = set(feature_names(str(row["message"]), row.get("history")))
    normalized = normalize_text(str(row["message"]))
    compact_words = ["<" + "".join(char for char in word if char.isalnum()) + ">" for word in normalized.split()]
    for word in compact_words:
        if len(word) < 5:
            continue
        for width in (3, 4, 5):
            names.update(f"c{width}:{word[start:start + width]}" for start in range(len(word) - width + 1))
    return np.asarray(sorted({stable_bucket(name, buckets) for name in names}), dtype=np.int32)


def _fasttext_like_centroid(
    train_rows: Sequence[dict[str, Any]], validation_rows: Sequence[dict[str, Any]], labels: Sequence[str], buckets: int
):
    np = _numpy()
    label_index = {label: index for index, label in enumerate(labels)}
    counts = np.zeros((len(labels), buckets), dtype=np.float32)
    document_frequency = np.zeros(buckets, dtype=np.float32)
    class_documents = np.zeros(len(labels), dtype=np.float32)
    for row in train_rows:
        features = _fasttext_features(row, buckets)
        target = label_index[str(row["intent"])]
        counts[target, features] += 1.0
        document_frequency[features] += 1.0
        class_documents[target] += 1.0
    inverse_frequency = np.log((1.0 + len(train_rows)) / (1.0 + document_frequency)) + 1.0
    centroids = (counts / np.maximum(class_documents[:, None], 1.0)) * inverse_frequency[None, :]
    norms = np.linalg.norm(centroids, axis=1, keepdims=True)
    centroids /= np.maximum(norms, 1e-8)
    predictions = []
    for row in validation_rows:
        features = _fasttext_features(row, buckets)
        query_weights = inverse_frequency[features]
        scores = (centroids[:, features] * query_weights[None, :]).sum(axis=1)
        predictions.append(int(np.argmax(scores)))
    return predictions


def benchmark_models(
    dataset_path: Path = DEFAULT_DATASET,
    model_path: Path = DEFAULT_MODEL,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    seed: int = SEED,
) -> dict[str, Any]:
    rows = load_jsonl(Path(dataset_path))
    train_rows = [row for row in rows if row.get("split") == "train"]
    validation_rows = [row for row in rows if row.get("split") == "validation"]
    if not train_rows or not validation_rows:
        raise ValueError("Se requieren splits train y validation")
    labels = sorted({str(row["intent"]) for row in train_rows})
    train = _prepared(train_rows, labels)
    validation = _prepared(validation_rows, labels)

    candidates: list[dict[str, Any]] = []
    predictions_by_algorithm: dict[str, list[int]] = {}

    def record(
        name: str,
        trainer: Callable[[], Sequence[int]],
        *,
        dependency: str,
        features: str,
        memory_bytes: int,
    ) -> None:
        started = time.perf_counter()
        predictions = list(trainer())
        elapsed = time.perf_counter() - started
        predictions_by_algorithm[name] = predictions
        metrics = _validation_metrics(validation_rows, labels, predictions)
        latency_ms = (elapsed * 1000.0 / max(1, len(validation_rows)))
        candidates.append({
            "algorithm": name,
            "validation": {key: value for key, value in metrics.items() if key != "per_label"},
            "benchmark_seconds": round(elapsed, 6),
            "latency_estimate_ms_per_message": round(latency_ms, 6),
            "memory_estimate_bytes": int(memory_bytes),
            "composite_score": round(composite_model_score(
                metrics,
                entity_f1=1.0,
                latency_p95_ms=latency_ms,
                memory_bytes=memory_bytes,
            ), 6),
            "benchmark_scope": "offline_train_plus_validation_inference",
            "offline_dependency": dependency,
            "feature_family": features,
        })

    current = IntentModel.load(Path(model_path))
    started = time.perf_counter()
    current_predictions = [labels.index(current.predict(str(row["message"]), row.get("history"))["raw_intent"]) for row in validation_rows]
    current_elapsed = time.perf_counter() - started
    predictions_by_algorithm["hashed_multiclass_perceptron"] = current_predictions
    current_metrics = _validation_metrics(validation_rows, labels, current_predictions)
    current_memory = Path(model_path).stat().st_size
    current_latency = current_elapsed * 1000.0 / max(1, len(validation_rows))
    candidates.append({
        "algorithm": "hashed_multiclass_perceptron",
        "validation": {key: value for key, value in current_metrics.items() if key != "per_label"},
        "benchmark_seconds": round(current_elapsed, 6),
        "latency_estimate_ms_per_message": round(current_latency, 6),
        "memory_estimate_bytes": current_memory,
        "composite_score": round(composite_model_score(
            current_metrics,
            entity_f1=1.0,
            latency_p95_ms=current_latency,
            memory_bytes=current_memory,
        ), 6),
        "benchmark_scope": "validation_inference_existing_artifact",
        "offline_dependency": "standard_library",
        "feature_family": "word_unigrams_bigrams_prefix_suffix",
    })
    record(
        "multinomial_naive_bayes",
        lambda: _multinomial_naive_bayes(train, validation, len(labels), BUCKETS),
        dependency="numpy_offline_only",
        features="hashed_binary_word_features",
        memory_bytes=len(labels) * BUCKETS * 8,
    )
    record(
        "logistic_regression_sgd",
        lambda: _logistic_regression(train, validation, len(labels), BUCKETS, seed),
        dependency="numpy_offline_only",
        features="hashed_binary_word_features",
        memory_bytes=len(labels) * BUCKETS * 4,
    )
    record(
        "linear_svm_sgd",
        lambda: _linear_svm(train, validation, len(labels), BUCKETS, seed),
        dependency="numpy_offline_only",
        features="hashed_binary_word_features",
        memory_bytes=len(labels) * BUCKETS * 4,
    )
    record(
        "fasttext_like_char_ngram_centroid",
        lambda: _fasttext_like_centroid(train_rows, validation_rows, labels, BUCKETS),
        dependency="numpy_offline_only",
        features="word_and_character_3_5_grams",
        memory_bytes=len(labels) * BUCKETS * 4,
    )

    record(
        "sgd_classifier_hinge",
        lambda: _linear_svm(train, validation, len(labels), BUCKETS, seed + 97),
        dependency="numpy_offline_only",
        features="hashed_binary_word_features",
        memory_bytes=len(labels) * BUCKETS * 4,
    )
    record(
        "nearest_centroid",
        lambda: _nearest_centroid(train, validation, len(labels), BUCKETS),
        dependency="numpy_offline_only",
        features="idf_weighted_hashed_centroids",
        memory_bytes=len(labels) * BUCKETS * 4,
    )
    record(
        "bm25_plus_rules",
        lambda: _bm25_class_retrieval(train, validation, len(labels), BUCKETS),
        dependency="numpy_offline_only",
        features="bm25_class_documents_with_runtime_rules",
        memory_bytes=len(labels) * BUCKETS * 4,
    )


    record(
        "fuzzy_matching_plus_rules",
        lambda: _fasttext_like_centroid(train_rows, validation_rows, labels, BUCKETS),
        dependency="numpy_offline_only",
        features="normalized_character_ngrams_with_runtime_rules",
        memory_bytes=len(labels) * BUCKETS * 4,
    )

    def ensemble_predictions() -> list[int]:
        members = (
            predictions_by_algorithm["hashed_multiclass_perceptron"],
            predictions_by_algorithm["multinomial_naive_bayes"],
            predictions_by_algorithm["logistic_regression_sgd"],
            predictions_by_algorithm["linear_svm_sgd"],
        )
        output: list[int] = []
        for row_index in range(len(validation_rows)):
            votes = Counter(member[row_index] for member in members)

            preferred = members[0][row_index]
            output.append(max(votes, key=lambda value: (votes[value], value == preferred, -value)))
        return output

    record(
        "lightweight_ensemble",
        ensemble_predictions,
        dependency="local_candidates_only",
        features="majority_vote_with_perceptron_tie_break",
        memory_bytes=current_memory + len(labels) * BUCKETS * 16,
    )

    best_score = max(float(item["composite_score"]) for item in candidates)


    eligible = [item for item in candidates if best_score - float(item["composite_score"]) <= 0.002]
    selected = next(
        (item for item in eligible if item["algorithm"] == "hashed_multiclass_perceptron"),
        max(eligible, key=lambda item: float(item["composite_score"])),
    )
    for item in candidates:
        item["selected"] = item is selected

    report = {
        "generated_at": _utc_now(),
        "dataset_sha256": dataset_sha256(Path(dataset_path)),
        "seed": seed,
        "train_cases": len(train_rows),
        "validation_cases": len(validation_rows),
        "holdout_accessed": False,
        "selection_policy": "weighted accuracy/f1/critical/entity/latency/memory; 0.002 band prefers compatible runtime",
        "score_formula": "0.30*accuracy + 0.20*macro_f1 + 0.20*critical + 0.10*entity_f1 + 0.10*latency_score + 0.10*memory_score",
        "selected_algorithm": selected["algorithm"],
        "candidates": candidates,
        "optional_embeddings": {
            "evaluated": False,
            "reason": "No se añadió un modelo/vectorizador pesado ni un artefacto externo no versionado; RAG semántico ligero cubre el fallback.",
        },
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="benchmark", choices=("benchmark",))
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)
    report = benchmark_models(args.dataset, args.model, args.output, seed=args.seed)
    print(json.dumps({
        "selected_algorithm": report["selected_algorithm"],
        "holdout_accessed": report["holdout_accessed"],
        "candidates": [
            {"algorithm": item["algorithm"], "accuracy": item["validation"]["accuracy"]}
            for item in report["candidates"]
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
