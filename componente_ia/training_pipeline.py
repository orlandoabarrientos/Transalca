"""Entrenamiento offline y ciclo de vida del clasificador local de intenciones.

Solo usa la librería estándar. El algoritmo es un perceptrón multiclase con
features lingüísticas hasheadas; no carga catálogos, fitment ni código productivo.

Comandos::

    python -m componente_ia.training_pipeline train
    python -m componente_ia.training_pipeline promote
    python -m componente_ia.training_pipeline rollback
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import math
import os
import random
import re
import shutil
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from componente_ia.model_registry import ModelRegistry


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = PACKAGE_DIR / "data" / "generated_training_cases.jsonl"
DEFAULT_MODEL = PACKAGE_DIR / "models" / "intent_model.json"
DEFAULT_ACTIVE_MODEL = PACKAGE_DIR / "models" / "intent_model.active.json"
DEFAULT_HISTORY_DIR = PACKAGE_DIR / "models" / "history"
DEFAULT_PROMOTION_LOG = PACKAGE_DIR / "models" / "promotion_history.jsonl"
DEFAULT_CYCLE_REPORT = PACKAGE_DIR / "artifacts" / "ia_training_cycle_results.json"
DEFAULT_CANDIDATE_COMPARISON = PACKAGE_DIR / "artifacts" / "ia_candidate_comparison.json"
DEFAULT_RELEASE_EVIDENCE = PACKAGE_DIR / "artifacts" / "ia_release_evidence.json"
DEFAULT_REGISTRY_SNAPSHOT = PACKAGE_DIR / "artifacts" / "ia_model_registry_snapshot.json"

TOKEN_RE = re.compile(r"[a-z0-9]+(?:[./-][a-z0-9]+)*", re.IGNORECASE)
ALGORITHM = "hashed_multiclass_perceptron"
SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(text: str) -> str:
    folded = unicodedata.normalize("NFKD", str(text).casefold())
    return "".join(char for char in folded if not unicodedata.combining(char))


def _history_text(history: Sequence[Any] | None) -> str:
    chunks: list[str] = []
    for item in history or ():
        if isinstance(item, str):
            chunks.append(item)
        elif isinstance(item, dict):
            content = item.get("content") or item.get("message") or item.get("text")
            if content:
                chunks.append(str(content))
    return " \u241e ".join(chunks)


def combined_text(message: str, history: Sequence[Any] | None = None) -> str:
    previous = _history_text(history)
    return f"{previous} \u241f {message}" if previous else str(message)


def feature_names(message: str, history: Sequence[Any] | None = None) -> set[str]:
    text = normalize_text(combined_text(message, history))
    words = TOKEN_RE.findall(text)
    features = {f"w:{word}" for word in words}
    features.update(f"b:{left}_{right}" for left, right in zip(words, words[1:]))

    for word in words:
        compact = re.sub(r"[^a-z0-9]", "", word)
        if len(compact) >= 5 and not compact.isdigit():
            features.add(f"p:{compact[:3]}")
            features.add(f"s:{compact[-3:]}")
        if len(compact) >= 8 and not compact.isdigit():
            features.add(f"p4:{compact[:4]}")
            features.add(f"s4:{compact[-4:]}")
    if history:
        features.add("meta:has_history")
    features.add(f"meta:length_{min(len(words) // 5, 8)}")
    return features


def stable_bucket(feature: str, buckets: int) -> int:
    digest = hashlib.blake2s(feature.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big") % buckets


def hashed_features(message: str, history: Sequence[Any] | None, buckets: int) -> tuple[int, ...]:
    return tuple(sorted({stable_bucket(name, buckets) for name in feature_names(message, history)}))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL inválido en {path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Fila no-objeto en {path}:{line_number}")
            rows.append(row)
    return rows


def dataset_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _argmax(scores: Sequence[float]) -> int:

    return max(range(len(scores)), key=lambda index: (scores[index], -index))


class IntentModel:
    """Modelo de inferencia pequeño, serializable y sin dependencias externas."""

    def __init__(self, artifact: dict[str, Any]):
        self.artifact = artifact
        self.labels = tuple(artifact["labels"])
        params = artifact["parameters"]
        self.buckets = int(params["feature_buckets"])
        self.bias = tuple(float(value) for value in artifact["bias"])
        self.weights: dict[int, tuple[tuple[int, float], ...]] = {}
        for bucket, pairs in artifact["feature_weights"].items():
            self.weights[int(bucket)] = tuple((int(pair[0]), float(pair[1])) for pair in pairs)
        fallback = artifact.get("fallback", {})
        self.fallback_label = fallback.get("label", "clarification")
        self.min_confidence = float(fallback.get("min_confidence", 0.0))

    @classmethod
    def load(cls, path: Path = DEFAULT_MODEL) -> "IntentModel":
        artifact = json.loads(Path(path).read_text(encoding="utf-8"))
        if artifact.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Versión de artefacto no soportada")
        if artifact.get("parameters", {}).get("algorithm") != ALGORITHM:
            raise ValueError("Algoritmo de artefacto no soportado")
        return cls(artifact)

    def scores(self, message: str, history: Sequence[Any] | None = None) -> list[float]:
        scores = list(self.bias)
        for bucket in hashed_features(message, history, self.buckets):
            for label_index, weight in self.weights.get(bucket, ()):
                scores[label_index] += weight
        return scores

    def predict(self, message: str, history: Sequence[Any] | None = None) -> dict[str, Any]:
        scores = self.scores(message, history)
        best_index = _argmax(scores)
        scale = max(1.0, math.sqrt(len(feature_names(message, history))) * 1.8)
        shifted = [(score - scores[best_index]) / scale for score in scores]
        denominator = sum(math.exp(max(-60.0, value)) for value in shifted)
        confidence = 1.0 / denominator if denominator else 0.0
        raw_label = self.labels[best_index]
        label = raw_label if confidence >= self.min_confidence else self.fallback_label
        return {
            "intent": label,
            "raw_intent": raw_label,
            "confidence": round(confidence, 6),
            "fallback": label != raw_label,
        }


def _score_features(
    features: Sequence[int],
    weights: dict[int, dict[int, int]],
    bias: Sequence[int],
) -> list[int]:
    scores = list(bias)
    for bucket in features:
        for label_index, value in weights.get(bucket, {}).items():
            scores[label_index] += value
    return scores


def _predict_index(
    features: Sequence[int],
    weights: dict[int, dict[int, int]],
    bias: Sequence[int],
) -> int:
    return _argmax(_score_features(features, weights, bias))


def classification_metrics(expected: Sequence[str], predicted: Sequence[str]) -> dict[str, Any]:
    if len(expected) != len(predicted):
        raise ValueError("Longitudes de evaluación distintas")
    labels = sorted(set(expected) | set(predicted))
    total = len(expected)
    correct = sum(left == right for left, right in zip(expected, predicted))
    per_label: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    for label in labels:
        tp = sum(e == label and p == label for e, p in zip(expected, predicted))
        fp = sum(e != label and p == label for e, p in zip(expected, predicted))
        fn = sum(e == label and p != label for e, p in zip(expected, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1_values.append(f1)
        per_label[label] = {
            "support": sum(e == label for e in expected),
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
        }
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 6) if total else 0.0,
        "macro_f1": round(sum(f1_values) / len(f1_values), 6) if f1_values else 0.0,
        "per_label": per_label,
    }


def evaluate_model_rows(model: IntentModel, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    selected = list(rows)
    expected = [str(row["intent"]) for row in selected]
    predicted = [model.predict(str(row["message"]), row.get("history"))["raw_intent"] for row in selected]
    metrics = classification_metrics(expected, predicted)
    critical_pairs = [(e, p) for row, e, p in zip(selected, expected, predicted) if row.get("critical")]
    security_pairs = [
        (e, p) for row, e, p in zip(selected, expected, predicted)
        if row.get("category") == "I_security_scope"
    ]
    out_scope_pairs = [(e, p) for e, p in zip(expected, predicted) if e == "out_of_scope"]

    def accuracy(pairs: Sequence[tuple[str, str]]) -> float:
        return round(sum(e == p for e, p in pairs) / len(pairs), 6) if pairs else 1.0

    metrics.update({
        "critical_accuracy": accuracy(critical_pairs),
        "critical_total": len(critical_pairs),
        "security_scope_accuracy": accuracy(security_pairs),
        "security_scope_total": len(security_pairs),
        "out_of_scope_accuracy": accuracy(out_scope_pairs),
        "out_of_scope_total": len(out_scope_pairs),
    })
    return metrics


def _artifact_from_state(
    *,
    labels: list[str],
    weights: dict[int, dict[int, int]],
    bias: list[int],
    buckets: int,
    seed: int,
    epochs: int,
    dataset_path: Path,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    sparse_weights: dict[str, list[list[int]]] = {}
    for bucket, label_weights in sorted(weights.items()):
        nonzero = [[label_index, value] for label_index, value in sorted(label_weights.items()) if value]
        if nonzero:
            sparse_weights[str(bucket)] = nonzero
    digest = dataset_sha256(dataset_path)
    return {
        "schema_version": SCHEMA_VERSION,
        "version": f"intent-{digest[:12]}-s{seed}",
        "created_at": utc_now(),
        "dataset": {
            "path_hint": "data/generated_training_cases.jsonl",
            "sha256": digest,
            "holdout_policy": "evaluated_once_after_model_selection_not_used_for_tuning",
        },
        "labels": labels,
        "metrics": metrics,



        "release_evidence": {
            "status": "not_evaluated",
            "inventory_hallucination_rate": None,
            "price_hallucination_rate": None,
            "service_hallucination_rate": None,
            "security_accuracy": None,
            "critical_behavior_accuracy": None,
            "performance_p95_ms": None,
            "performance_budget_ms": None,
        },
        "parameters": {
            "algorithm": ALGORITHM,
            "feature_buckets": buckets,
            "epochs_selected_on_validation": epochs,
            "seed": seed,
            "features": ["word_unigrams", "word_bigrams", "prefix_suffix", "history_marker"],
        },
        "fallback": {
            "label": "clarification",
            "min_confidence": 0.0,
            "policy": "orchestrator_may_apply_a_stricter_runtime_threshold",
        },
        "bias": bias,
        "feature_weights": sparse_weights,
    }


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def train_model(
    dataset_path: Path = DEFAULT_DATASET,
    output_path: Path = DEFAULT_MODEL,
    *,
    seed: int = 20260710,
    max_epochs: int = 14,
    buckets: int = 8192,
) -> dict[str, Any]:
    rows = load_jsonl(Path(dataset_path))
    train_rows = [row for row in rows if row.get("split") == "train"]
    validation_rows = [row for row in rows if row.get("split") == "validation"]
    holdout_rows = [row for row in rows if row.get("split") == "holdout"]
    if not train_rows or not validation_rows or not holdout_rows:
        raise ValueError("El dataset debe contener train, validation y holdout")

    labels = sorted({str(row["intent"]) for row in train_rows})
    label_index = {label: index for index, label in enumerate(labels)}
    missing_labels = sorted({str(row["intent"]) for row in rows} - set(labels))
    if missing_labels:
        raise ValueError(f"Etiquetas ausentes de train: {missing_labels}")

    def prepare(row: dict[str, Any]) -> tuple[tuple[int, ...], int]:
        return (
            hashed_features(str(row["message"]), row.get("history"), buckets),
            label_index[str(row["intent"])],
        )

    prepared_train = [prepare(row) for row in train_rows]
    prepared_validation = [prepare(row) for row in validation_rows]
    weights: dict[int, dict[int, int]] = defaultdict(dict)
    bias = [0 for _ in labels]
    best_accuracy = -1.0
    best_epoch = 0
    best_weights: dict[int, dict[int, int]] = {}
    best_bias = list(bias)
    rng = random.Random(seed)
    epoch_metrics: list[dict[str, Any]] = []

    for epoch in range(1, max_epochs + 1):
        order = list(range(len(prepared_train)))
        rng.shuffle(order)
        mistakes = 0
        for row_index in order:
            features, target = prepared_train[row_index]
            predicted = _predict_index(features, weights, bias)
            if predicted == target:
                continue
            mistakes += 1
            bias[target] += 1
            bias[predicted] -= 1
            for bucket in features:
                bucket_weights = weights[bucket]
                bucket_weights[target] = bucket_weights.get(target, 0) + 1
                bucket_weights[predicted] = bucket_weights.get(predicted, 0) - 1

        validation_correct = sum(
            _predict_index(features, weights, bias) == target
            for features, target in prepared_validation
        )
        validation_accuracy = validation_correct / len(prepared_validation)
        epoch_metrics.append({
            "epoch": epoch,
            "train_mistakes": mistakes,
            "validation_accuracy": round(validation_accuracy, 6),
        })
        if validation_accuracy > best_accuracy:
            best_accuracy = validation_accuracy
            best_epoch = epoch
            best_bias = list(bias)
            best_weights = {bucket: dict(values) for bucket, values in weights.items()}

    provisional = _artifact_from_state(
        labels=labels,
        weights=best_weights,
        bias=best_bias,
        buckets=buckets,
        seed=seed,
        epochs=best_epoch,
        dataset_path=Path(dataset_path),
        metrics={},
    )
    model = IntentModel(provisional)

    metrics = {
        "train": evaluate_model_rows(model, train_rows),
        "validation": evaluate_model_rows(model, validation_rows),
        "holdout": evaluate_model_rows(model, holdout_rows),
        "selection_history": epoch_metrics,
        "scope": "intent_classification_only",
        "grounding_hallucination": "not_applicable_to_intent_classifier",
    }
    artifact = _artifact_from_state(
        labels=labels,
        weights=best_weights,
        bias=best_bias,
        buckets=buckets,
        seed=seed,
        epochs=best_epoch,
        dataset_path=Path(dataset_path),
        metrics=metrics,
    )
    _atomic_json_write(Path(output_path), artifact)
    return artifact


def _promotion_failures(
    candidate: dict[str, Any],
    active: dict[str, Any] | None,
    release_evidence: dict[str, Any] | None = None,
    *,
    strict_learning_cycle: bool = False,
) -> list[str]:
    metrics = candidate.get("metrics", {})
    holdout = metrics.get("holdout", {})
    evidence = release_evidence or candidate.get("release_evidence") or {}
    failures: list[str] = []
    if float(holdout.get("accuracy", 0.0)) < 0.97:
        failures.append("intent_accuracy_below_0.97")
    if float(holdout.get("macro_f1", 0.0)) < 0.96:
        failures.append("macro_f1_below_0.96")
    if float(holdout.get("accuracy", 0.0)) < 0.94:
        failures.append("holdout_accuracy_below_0.94")



    if not isinstance(evidence.get("critical_behavior_accuracy"), (int, float)) and float(holdout.get("critical_accuracy", 0.0)) < 1.0:
        failures.append("critical_accuracy_below_1.0")
    if float(holdout.get("security_scope_accuracy", 0.0)) < 1.0:
        failures.append("security_scope_accuracy_below_1.0")
    if float(holdout.get("out_of_scope_accuracy", 0.0)) < 1.0:
        failures.append("out_of_scope_accuracy_below_1.0")

    required_rates = (
        "inventory_hallucination_rate",
        "price_hallucination_rate",
        "service_hallucination_rate",
    )
    for field in required_rates:
        value = evidence.get(field)
        if not isinstance(value, (int, float)):
            failures.append(f"missing_{field}")
        elif float(value) != 0.0:
            failures.append(f"{field}_above_zero")
    for field in ("security_accuracy", "critical_behavior_accuracy"):
        value = evidence.get(field)
        if not isinstance(value, (int, float)):
            failures.append(f"missing_{field}")
        elif float(value) < 1.0:
            failures.append(f"{field}_below_1.0")
    p95 = evidence.get("performance_p95_ms")
    budget = evidence.get("performance_budget_ms")
    if not isinstance(p95, (int, float)):
        failures.append("missing_performance_p95_ms")
    if not isinstance(budget, (int, float)):
        failures.append("missing_performance_budget_ms")
    if isinstance(p95, (int, float)) and isinstance(budget, (int, float)) and float(p95) > float(budget):
        failures.append("performance_p95_above_budget")
    if evidence.get("performance_passed") is not True:
        failures.append("performance_validation_not_passed")
    for name, maximum in (("catalog_p95_ms", 700.0), ("web_p95_ms", 1500.0)):
        value = evidence.get(name)
        if not isinstance(value, (int, float)):
            failures.append(f"missing_{name}")
        elif float(value) >= maximum:
            failures.append(f"{name}_above_budget")
    if strict_learning_cycle:
        strict_minimums = (
            ("entity_f1", 0.97),
            ("independent_holdout_accuracy", 0.94),
            ("multiturn_accuracy", 0.96),
        )
        for field, minimum in strict_minimums:
            value = evidence.get(field)
            if not isinstance(value, (int, float)):
                failures.append(f"missing_{field}")
            elif float(value) < minimum:
                failures.append(f"{field}_below_{minimum}")
        if evidence.get("conversation_regressions") not in (None, 0, [], {}):
            failures.append("conversation_regressions_detected")
        memory = evidence.get("memory_peak_bytes")
        if not isinstance(memory, (int, float)):
            failures.append("missing_memory_peak_bytes")
        evaluated_hash = evidence.get("dataset_sha256")
        expected_hash = (candidate.get("dataset") or {}).get("sha256")
        if not evaluated_hash:
            failures.append("missing_evaluated_dataset_hash")
        elif expected_hash and str(evaluated_hash) != str(expected_hash):
            failures.append("stale_release_evidence_dataset_hash_mismatch")
    if active:
        old = active.get("metrics", {}).get("holdout", {})
        for field in ("accuracy", "macro_f1", "critical_accuracy", "security_scope_accuracy", "out_of_scope_accuracy"):
            if float(holdout.get(field, 0.0)) < float(old.get(field, 0.0)):
                failures.append(f"regression_{field}")
        old_evidence = active.get("release_evidence") or {}
        for field in required_rates:
            old_value, new_value = old_evidence.get(field), evidence.get(field)
            if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)) and float(new_value) > float(old_value):
                failures.append(f"regression_{field}")
        old_p95 = old_evidence.get("performance_p95_ms")
        if (
            isinstance(old_p95, (int, float))
            and isinstance(p95, (int, float))
            and float(p95) > float(old_p95) * 1.15 + 1e-9
        ):
            failures.append("performance_regression_above_15_percent")
        old_memory = old_evidence.get("memory_peak_bytes")
        new_memory = evidence.get("memory_peak_bytes")
        if (
            isinstance(old_memory, (int, float))
            and isinstance(new_memory, (int, float))
            and float(new_memory) > float(old_memory) * 1.20 + 1e-9
        ):
            failures.append("memory_regression_above_20_percent")
    return sorted(set(failures))


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def _read_json_object(path: Path | None) -> dict[str, Any]:
    if path is None or not Path(path).is_file():
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Se esperaba un objeto JSON en {path}")
    return payload


def load_cycle_evidence(evidence_path: Path | None = None) -> dict[str, Any]:
    """Consolida evidencia local; no ejecuta red ni reutiliza mensajes reales."""

    report = _read_json_object(evidence_path or DEFAULT_RELEASE_EVIDENCE)
    evidence = dict(report.get("release_evidence", report))
    evaluation = _read_json_object(PACKAGE_DIR / "artifacts" / "ia_5000_cases_results.json")
    performance = _read_json_object(PACKAGE_DIR / "artifacts" / "ia_performance_results.json")
    holdout = _read_json_object(PACKAGE_DIR / "artifacts" / "ia_holdout_results.json")
    real_holdout = _read_json_object(PACKAGE_DIR / "artifacts" / "ia_real_holdout_results.json")

    entity = evaluation.get("entity_extraction") or {}
    multiturn = evaluation.get("multiturn") or {}
    if isinstance(entity.get("f1"), (int, float)):
        evidence.setdefault("entity_f1", entity["f1"])
    if isinstance(multiturn.get("accuracy"), (int, float)):
        evidence.setdefault("multiturn_accuracy", multiturn["accuracy"])
        if evaluation.get("passed") is True:
            evidence.setdefault("conversation_regressions", 0)
    memory = performance.get("memory") or {}
    if isinstance(memory.get("peak_traced_bytes"), (int, float)):
        evidence.setdefault("memory_peak_bytes", memory["peak_traced_bytes"])
    if holdout.get("dataset_sha256"):
        evidence.setdefault("dataset_sha256", holdout["dataset_sha256"])

    independent_metrics = real_holdout.get("metrics") if isinstance(real_holdout.get("metrics"), dict) else real_holdout
    independent_accuracy = independent_metrics.get("accuracy") if isinstance(independent_metrics, dict) else None
    if isinstance(independent_accuracy, (int, float)):
        evidence.setdefault("independent_holdout_accuracy", independent_accuracy)
    return evidence


def promote_model(
    candidate_path: Path = DEFAULT_MODEL,
    active_path: Path = DEFAULT_ACTIVE_MODEL,
    evidence_path: Path | None = None,
) -> dict[str, Any]:
    candidate_path, active_path = Path(candidate_path), Path(active_path)
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    IntentModel(candidate)
    active = json.loads(active_path.read_text(encoding="utf-8")) if active_path.exists() else None
    release_evidence = None
    if evidence_path is not None:
        report = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
        release_evidence = report.get("release_evidence", report)
    failures = _promotion_failures(candidate, active, release_evidence)
    event = {
        "timestamp": utc_now(),
        "action": "promote",
        "candidate_version": candidate.get("version"),
        "previous_version": active.get("version") if active else None,
        "accepted": not failures,
        "failures": failures,
    }
    if failures:
        _append_jsonl(DEFAULT_PROMOTION_LOG, event)
        raise RuntimeError("Promoción rechazada: " + ", ".join(failures))

    candidate["release_evidence"] = dict(release_evidence or candidate["release_evidence"])
    _atomic_json_write(candidate_path, candidate)
    if active:
        DEFAULT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        archive = DEFAULT_HISTORY_DIR / f"{active.get('version', 'unknown')}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        shutil.copy2(active_path, archive)
        event["archive"] = archive.name
    active_path.parent.mkdir(parents=True, exist_ok=True)
    temp = active_path.with_suffix(".tmp")
    shutil.copy2(candidate_path, temp)
    os.replace(temp, active_path)
    _append_jsonl(DEFAULT_PROMOTION_LOG, event)
    return event


def promote_registered_model(
    version: str,
    *,
    evidence_path: Path | None = None,
    registry: ModelRegistry | None = None,
) -> dict[str, Any]:
    """Promueve por versión solo tras evaluación integral y comparación activa."""

    registry = registry or ModelRegistry()
    registry.bootstrap_legacy_active()
    candidate_path = registry.artifact_path(version)
    candidate_record = registry.get(version)
    if candidate_record.get("status") != "candidate":
        raise RuntimeError("La versión solicitada no es candidata")
    candidate = _read_json_object(candidate_path)
    IntentModel(candidate)
    active_record = registry.active()
    active = _read_json_object(registry.artifact_path(active_record["version"])) if active_record else None
    evidence = load_cycle_evidence(evidence_path)
    failures = _promotion_failures(
        candidate,
        active,
        evidence,
        strict_learning_cycle=True,
    )
    event = {
        "timestamp": utc_now(),
        "action": "promote",
        "candidate_version": version,
        "previous_version": active_record.get("version") if active_record else None,
        "accepted": not failures,
        "failures": failures,
        "mode": "versioned_registry",
    }
    if failures:
        registry.reject(version, failures)
        _append_jsonl(registry.models_dir / "promotion_history.jsonl", event)
        raise RuntimeError("Promoción rechazada: " + ", ".join(failures))

    candidate["release_evidence"] = evidence
    _atomic_json_write(candidate_path, candidate)

    registry.register_candidate(candidate_path, extra={
        "promotion_gate_failures": [],
        "promotion_gate_checked_at": utc_now(),
    })
    registry_event = registry.promote(version, event_extra={"gates_passed": True})
    event["registry_event"] = registry_event
    _append_jsonl(registry.models_dir / "promotion_history.jsonl", event)
    return event


def rollback_model(active_path: Path = DEFAULT_ACTIVE_MODEL) -> dict[str, Any]:
    active_path = Path(active_path)
    archives = sorted(DEFAULT_HISTORY_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not archives:
        raise RuntimeError("No existe una versión archivada para rollback")
    current = json.loads(active_path.read_text(encoding="utf-8")) if active_path.exists() else None
    selected = archives[0]
    previous = json.loads(selected.read_text(encoding="utf-8"))
    IntentModel(previous)
    if current:
        backup = DEFAULT_HISTORY_DIR / f"rollback-from-{current.get('version', 'unknown')}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        shutil.copy2(active_path, backup)
    temp = active_path.with_suffix(".tmp")
    shutil.copy2(selected, temp)
    os.replace(temp, active_path)
    event = {
        "timestamp": utc_now(),
        "action": "rollback",
        "from_version": current.get("version") if current else None,
        "to_version": previous.get("version"),
        "archive": selected.name,
        "accepted": True,
    }
    _append_jsonl(DEFAULT_PROMOTION_LOG, event)
    return event


def rollback_registered_model(
    version: str | None = None,
    *,
    registry: ModelRegistry | None = None,
) -> dict[str, Any]:
    registry = registry or ModelRegistry()
    registry.bootstrap_legacy_active()
    event = registry.rollback(version)
    event["accepted"] = True
    event["mode"] = "versioned_registry"
    _append_jsonl(registry.models_dir / "promotion_history.jsonl", event)
    return event


def list_registered_models(registry: ModelRegistry | None = None) -> dict[str, Any]:
    registry = registry or ModelRegistry()
    registry.bootstrap_legacy_active()
    active = registry.active()
    result = {
        "active_version": active.get("version") if active else None,
        "models": registry.list_models(),
        "registry": str(registry.registry_path),
    }

    _write_pretty_json(DEFAULT_REGISTRY_SNAPSHOT, {
        "generated_at": utc_now(),
        "active_version": result["active_version"],
        "models": result["models"],
    })
    return result


def _write_pretty_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def _prepare_dataset_for_cycle(dataset_path: Path) -> dict[str, Any]:
    """Invoca el gestor local si está instalado; tolera ciclos sobre dataset ya construido."""

    try:
        module = importlib.import_module("componente_ia.dataset_manager")
    except ImportError:
        return {"status": "manager_unavailable", "used_existing_dataset": True}
    builder = getattr(module, "build_dataset_from_sources", None)
    if not callable(builder):
        builder = getattr(module, "build_dataset", None)
    if not callable(builder):
        return {"status": "builder_unavailable", "used_existing_dataset": True}

    signature = inspect.signature(builder)
    kwargs: dict[str, Any] = {}
    for name in signature.parameters:
        if name in {"output", "output_path", "dataset_path"}:
            kwargs[name] = Path(dataset_path)
    missing = [
        parameter.name
        for parameter in signature.parameters.values()
        if parameter.default is inspect.Parameter.empty
        and parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        and parameter.name not in kwargs
    ]
    if missing:
        return {
            "status": "builder_requires_explicit_inputs",
            "missing_parameters": missing,
            "used_existing_dataset": True,
        }
    result = builder(**kwargs)
    return {
        "status": "built",
        "used_existing_dataset": False,
        "result": result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else str(result),
    }


def run_full_cycle(
    dataset_path: Path = DEFAULT_DATASET,
    *,
    evidence_path: Path | None = None,
    output_path: Path = DEFAULT_CYCLE_REPORT,
    comparison_path: Path = DEFAULT_CANDIDATE_COMPARISON,
    seed: int = 20260710,
    max_epochs: int = 14,
    buckets: int = 8192,
    approve_promotion: bool = False,
    registry: ModelRegistry | None = None,
) -> dict[str, Any]:
    """Ejecuta entrenamiento y gates locales; promover exige aprobación explícita.

    Los casos aprobados deben haber sido incorporados previamente por el gestor
    de dataset. Esta función nunca consume feedback pendiente ni modifica reglas.
    """

    registry = registry or ModelRegistry()
    registry.bootstrap_legacy_active()
    dataset_preparation = _prepare_dataset_for_cycle(Path(dataset_path))
    candidate_working = registry.models_dir / "intent_model.json"
    artifact = train_model(
        Path(dataset_path), candidate_working,
        seed=seed, max_epochs=max_epochs, buckets=buckets,
    )
    version = str(artifact["version"])
    active_record = registry.active()
    if active_record and active_record.get("version") == version:
        result = {
            "generated_at": utc_now(),
            "status": "no_change",
            "candidate_version": version,
            "active_version": version,
            "promoted": False,
            "reason": "dataset_and_training_version_already_active",
            "silent_promotion": False,
            "dataset_preparation": dataset_preparation,
        }
        _write_pretty_json(Path(output_path), result)
        return result

    record = registry.register_candidate(candidate_working)
    evidence = load_cycle_evidence(evidence_path)
    active = _read_json_object(registry.artifact_path(active_record["version"])) if active_record else None
    failures = _promotion_failures(
        artifact, active, evidence, strict_learning_cycle=True,
    )


    try:
        from componente_ia.model_selection import benchmark_models, composite_model_score

        benchmark = benchmark_models(
            Path(dataset_path), candidate_working, Path(comparison_path), seed=seed,
        )
        candidate_score = composite_model_score(
            artifact["metrics"]["validation"],
            entity_f1=float(evidence.get("entity_f1", 0.0)),
            latency_p95_ms=float(evidence.get("performance_p95_ms", 10_000.0)),
            memory_bytes=int(evidence.get("memory_peak_bytes", 1 << 40)),
        )
    except (ImportError, RuntimeError) as exc:
        benchmark = {"status": "unavailable", "reason": str(exc), "holdout_accessed": False}
        candidate_score = 0.0
        failures.append("local_model_comparison_unavailable")

    failures = sorted(set(failures))
    result: dict[str, Any] = {
        "generated_at": utc_now(),
        "status": "candidate_ready" if not failures else "rejected",
        "candidate_version": version,
        "active_version_before": active_record.get("version") if active_record else None,
        "dataset_sha256": artifact["dataset"]["sha256"],
        "train_cases": artifact["metrics"]["train"]["total"],
        "validation_metrics": artifact["metrics"]["validation"],
        "holdout_metrics": artifact["metrics"]["holdout"],
        "composite_score": round(candidate_score, 6),
        "comparison": benchmark,
        "promotion_failures": failures,
        "promotion_explicitly_approved": bool(approve_promotion),
        "promoted": False,
        "silent_promotion": False,
        "registry_record": record,
        "dataset_preparation": dataset_preparation,
    }
    if failures:
        registry.reject(version, failures)
    elif approve_promotion:

        promotion = promote_registered_model(
            version, evidence_path=evidence_path, registry=registry,
        )
        result.update({"status": "promoted", "promoted": True, "promotion": promotion})
    else:
        result.update({
            "status": "awaiting_manual_promotion",
            "next_command": f"python -m componente_ia.training_pipeline promote --version {version}",
        })
    _write_pretty_json(Path(output_path), result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    train = subparsers.add_parser("train", help="Entrena y evalúa un candidato offline")
    train.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    train.add_argument("--output", type=Path, default=DEFAULT_MODEL)
    train.add_argument("--seed", type=int, default=20260710)
    train.add_argument("--max-epochs", type=int, default=14)
    train.add_argument("--buckets", type=int, default=8192)
    train.add_argument("--registry-dir", type=Path, default=PACKAGE_DIR / "models")
    train.add_argument("--no-register", action="store_true", help="Solo escribir el artefacto legado")
    promote = subparsers.add_parser("promote", help="Promueve si cumple todos los gates")
    promote.add_argument("--candidate", type=Path, default=DEFAULT_MODEL)
    promote.add_argument("--active", type=Path, default=DEFAULT_ACTIVE_MODEL)
    promote.add_argument("--evidence", type=Path, help="Reporte integral con release_evidence")
    promote.add_argument("--version", help="Versión candidata registrada")
    promote.add_argument("--registry-dir", type=Path, default=PACKAGE_DIR / "models")
    rollback = subparsers.add_parser("rollback", help="Restaura el activo archivado más reciente")
    rollback.add_argument("--active", type=Path, default=DEFAULT_ACTIVE_MODEL)
    rollback.add_argument("--version", help="Versión archivada concreta")
    rollback.add_argument("--registry-dir", type=Path, default=PACKAGE_DIR / "models")
    listing = subparsers.add_parser("list-models", help="Lista activo, candidatos y versiones reversibles")
    listing.add_argument("--registry-dir", type=Path, default=PACKAGE_DIR / "models")
    cycle = subparsers.add_parser("full-cycle", help="Entrena, compara y aplica gates sin promoción silenciosa")
    cycle.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    cycle.add_argument("--evidence", type=Path)
    cycle.add_argument("--output", type=Path, default=DEFAULT_CYCLE_REPORT)
    cycle.add_argument("--comparison", type=Path, default=DEFAULT_CANDIDATE_COMPARISON)
    cycle.add_argument("--seed", type=int, default=20260710)
    cycle.add_argument("--max-epochs", type=int, default=14)
    cycle.add_argument("--buckets", type=int, default=8192)
    cycle.add_argument("--registry-dir", type=Path, default=PACKAGE_DIR / "models")
    cycle.add_argument(
        "--approve-promotion", action="store_true",
        help="Aprobación administrativa explícita; sin este flag nunca promueve",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "train":
        artifact = train_model(args.dataset, args.output, seed=args.seed, max_epochs=args.max_epochs, buckets=args.buckets)
        registration: dict[str, Any] | None = None
        if not args.no_register:
            registry = ModelRegistry(args.registry_dir)
            registry.bootstrap_legacy_active()
            active = registry.active()
            if active and active.get("version") == artifact["version"]:
                registration = {"status": "already_active", "version": artifact["version"]}
            else:
                registration = registry.register_candidate(args.output)
        result = {
            "version": artifact["version"],
            "model": str(args.output),
            "selected_epoch": artifact["parameters"]["epochs_selected_on_validation"],
            "validation": artifact["metrics"]["validation"],
            "holdout": artifact["metrics"]["holdout"],
            "registration": registration,
            "promoted": False,
        }
    elif args.command == "promote":
        if args.version:
            result = promote_registered_model(
                args.version,
                evidence_path=args.evidence,
                registry=ModelRegistry(args.registry_dir),
            )
        else:
            result = promote_model(args.candidate, args.active, args.evidence)
    elif args.command == "rollback":
        if args.version:
            result = rollback_registered_model(
                args.version, registry=ModelRegistry(args.registry_dir),
            )
        else:

            result = rollback_model(args.active)
    elif args.command == "list-models":
        result = list_registered_models(ModelRegistry(args.registry_dir))
    else:
        result = run_full_cycle(
            args.dataset,
            evidence_path=args.evidence,
            output_path=args.output,
            comparison_path=args.comparison,
            seed=args.seed,
            max_epochs=args.max_epochs,
            buckets=args.buckets,
            approve_promotion=args.approve_promotion,
            registry=ModelRegistry(args.registry_dir),
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
