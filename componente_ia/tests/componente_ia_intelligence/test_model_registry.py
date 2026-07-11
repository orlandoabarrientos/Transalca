import json
from pathlib import Path

import pytest

from componente_ia.model_registry import ModelRegistry
from componente_ia.training_pipeline import (
    _promotion_failures,
    promote_registered_model,
    rollback_registered_model,
)


PACKAGE = Path(__file__).resolve().parents[2]


def artifact(version: str) -> dict:
    value = json.loads((PACKAGE / "models" / "intent_model.json").read_text(encoding="utf-8"))
    value["version"] = version
    return value


def write_artifact(path: Path, version: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact(version)), encoding="utf-8")
    return path


def evidence(path: Path, *, dataset_hash: str, p95: float = 10.0) -> Path:
    payload = {
        "release_evidence": {
            "dataset_sha256": dataset_hash,
            "inventory_hallucination_rate": 0.0,
            "price_hallucination_rate": 0.0,
            "service_hallucination_rate": 0.0,
            "security_accuracy": 1.0,
            "critical_behavior_accuracy": 1.0,
            "entity_f1": 0.99,
            "independent_holdout_accuracy": 0.96,
            "multiturn_accuracy": 0.98,
            "conversation_regressions": 0,
            "performance_p95_ms": p95,
            "performance_budget_ms": 150.0,
            "catalog_p95_ms": 100.0,
            "web_p95_ms": 1200.0,
            "memory_peak_bytes": 4_000_000,
            "performance_passed": True,
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def registry_with_active(tmp_path: Path) -> ModelRegistry:
    models = tmp_path / "models"
    legacy = write_artifact(models / "intent_model.active.json", "baseline-1")
    registry = ModelRegistry(models, legacy_active_path=legacy)
    bootstrapped = registry.bootstrap_legacy_active()
    assert bootstrapped and bootstrapped["status"] == "active"
    return registry


def test_registry_separates_candidate_active_archive_and_immediate_rollback(tmp_path):
    registry = registry_with_active(tmp_path)
    source = write_artifact(tmp_path / "candidate.json", "candidate-2")
    candidate = registry.register_candidate(source)
    assert candidate["status"] == "candidate"
    assert registry.artifact_path("candidate-2").parent.name == "candidates"

    promoted = registry.promote("candidate-2")
    assert promoted["previous_version"] == "baseline-1"
    assert registry.active()["version"] == "candidate-2"
    assert registry.get("baseline-1")["status"] == "archived"
    assert json.loads(registry.legacy_active_path.read_text())["version"] == "candidate-2"

    rolled_back = rollback_registered_model("baseline-1", registry=registry)
    assert rolled_back["to_version"] == "baseline-1"
    assert registry.active()["version"] == "baseline-1"
    assert registry.get("candidate-2")["status"] == "archived"


def test_versioned_promotion_runs_strict_gates_and_failed_candidate_is_rejected(tmp_path):
    registry = registry_with_active(tmp_path)
    source = write_artifact(tmp_path / "candidate.json", "candidate-bad")
    record = registry.register_candidate(source)
    report = evidence(
        tmp_path / "evidence.json",
        dataset_hash=record["dataset_hash"],
        p95=151.0,
    )
    with pytest.raises(RuntimeError, match="Promoción rechazada"):
        promote_registered_model("candidate-bad", evidence_path=report, registry=registry)
    rejected = registry.get("candidate-bad")
    assert rejected["status"] == "rejected"
    assert "performance_p95_above_budget" in rejected["rejection_reasons"]


def test_versioned_promotion_accepts_complete_local_evidence(tmp_path):
    registry = registry_with_active(tmp_path)
    source = write_artifact(tmp_path / "candidate.json", "candidate-good")
    record = registry.register_candidate(source)
    report = evidence(tmp_path / "evidence.json", dataset_hash=record["dataset_hash"])
    event = promote_registered_model("candidate-good", evidence_path=report, registry=registry)
    assert event["accepted"] is True
    assert registry.active()["version"] == "candidate-good"


def test_performance_and_memory_regression_tolerances_are_relative():
    candidate = artifact("candidate")
    active = artifact("active")
    active["release_evidence"].update({"performance_p95_ms": 100.0, "memory_peak_bytes": 1_000})
    base = dict(candidate["release_evidence"])
    base.update({"performance_p95_ms": 115.0, "memory_peak_bytes": 1_200})
    failures = _promotion_failures(candidate, active, base)
    assert "performance_regression_above_15_percent" not in failures
    assert "memory_regression_above_20_percent" not in failures

    base.update({"performance_p95_ms": 115.01, "memory_peak_bytes": 1_201})
    failures = _promotion_failures(candidate, active, base)
    assert "performance_regression_above_15_percent" in failures
    assert "memory_regression_above_20_percent" in failures


def test_registry_rejects_unsafe_version(tmp_path):
    registry = registry_with_active(tmp_path)
    source = write_artifact(tmp_path / "candidate.json", "../escape")
    with pytest.raises(ValueError, match="Versión"):
        registry.register_candidate(source)
