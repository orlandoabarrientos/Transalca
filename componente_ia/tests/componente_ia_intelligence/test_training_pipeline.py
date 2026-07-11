import json
from pathlib import Path

from componente_ia.training_pipeline import IntentModel, _promotion_failures, dataset_sha256


def _artifact():
    path = Path(__file__).resolve().parents[2] / "models" / "intent_model.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_model_artifact_is_loadable_and_tied_to_exact_dataset():
    model_path, artifact = _artifact()
    model = IntentModel.load(model_path)
    dataset = Path(__file__).resolve().parents[2] / "data" / "generated_training_cases.jsonl"
    assert artifact["dataset"]["sha256"] == dataset_sha256(dataset)
    assert len(model.labels) >= 25
    prediction = model.predict("¿Qué servicios tienen?")
    assert prediction["intent"] in model.labels
    assert 0 <= prediction["confidence"] <= 1


def test_promotion_fails_closed_without_integral_release_evidence():
    _, candidate = _artifact()
    candidate.pop("release_evidence", None)
    failures = _promotion_failures(candidate, active=None, release_evidence=None)
    assert "missing_inventory_hallucination_rate" in failures
    assert "missing_performance_p95_ms" in failures
    assert "performance_validation_not_passed" in failures


def test_integral_system_evidence_can_gate_hybrid_fallback_model():
    _, candidate = _artifact()
    evidence = {
        "inventory_hallucination_rate": 0.0,
        "price_hallucination_rate": 0.0,
        "service_hallucination_rate": 0.0,
        "security_accuracy": 1.0,
        "critical_behavior_accuracy": 1.0,
        "performance_p95_ms": 20.0,
        "performance_budget_ms": 150.0,
        "catalog_p95_ms": 100.0,
        "web_p95_ms": 1300.0,
        "performance_passed": True,
    }
    assert _promotion_failures(candidate, active=None, release_evidence=evidence) == []


def test_model_comparison_is_validation_only_and_covers_lightweight_candidates():
    path = Path(__file__).resolve().parents[2] / "artifacts" / "ia_model_comparison.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["holdout_accessed"] is False
    assert report["selected_algorithm"] == "hashed_multiclass_perceptron"
    algorithms = {item["algorithm"] for item in report["candidates"]}
    assert {
        "hashed_multiclass_perceptron",
        "multinomial_naive_bayes",
        "logistic_regression_sgd",
        "linear_svm_sgd",
        "fasttext_like_char_ngram_centroid",
    } <= algorithms
    assert all(item["validation"]["total"] == 750 for item in report["candidates"])
