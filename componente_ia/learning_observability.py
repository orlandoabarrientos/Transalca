"""Métricas agregadas del aprendizaje sin exponer conversaciones."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from componente_ia.feedback_store import feedback_store
from componente_ia.metrics import assistant_metrics


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    except (OSError, json.JSONDecodeError):
        return []
    return rows


def _registry_entries() -> list[dict[str, Any]]:
    payload = _read_json(MODELS_DIR / "registry.json")
    if isinstance(payload, dict):
        raw = payload.get("models", payload.get("versions", []))
        if isinstance(raw, dict):
            raw = list(raw.values())
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        if "version" in payload:
            return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _safe_model(item: dict[str, Any]) -> dict[str, Any]:
    metrics = item.get("validation_metrics") or item.get("metrics") or {}
    composite = item.get("composite_score")
    if composite is None and isinstance(metrics, dict):
        composite = metrics.get("composite_score")
    return {
        "version": str(item.get("version") or "unknown")[:80],
        "status": str(item.get("status") or "unknown")[:24],
        "dataset_hash": str(item.get("dataset_hash") or item.get("dataset_sha256") or "")[:64],
        "train_cases": int(item.get("train_cases") or 0),
        "composite_score": composite if isinstance(composite, (int, float)) else None,
    }


def learning_metrics_snapshot() -> dict[str, Any]:
    review_rows = _jsonl_rows(DATA_DIR / "production_feedback.jsonl")
    if not review_rows:
        review_rows = _jsonl_rows(DATA_DIR / "learning_review_queue.jsonl")
    status_counts = Counter(str(row.get("status") or "pending_review") for row in review_rows)
    approved_file = _jsonl_rows(DATA_DIR / "approved_feedback_cases.jsonl")
    rejected_file = _jsonl_rows(DATA_DIR / "rejected_feedback_cases.jsonl")
    registry = _registry_entries()
    registry_counts = Counter(str(item.get("status") or "unknown") for item in registry)
    events = _jsonl_rows(MODELS_DIR / "promotion_history.jsonl")
    promotions = sum(item.get("action") in {"promote", "promotion"} and item.get("accepted") is not False for item in events)
    rollbacks = sum(item.get("action") == "rollback" for item in events)
    active = next((item for item in registry if item.get("status") == "active"), None)
    if active is None:
        active_payload = _read_json(MODELS_DIR / "intent_model.active.json")
        active_version = active_payload.get("version") if isinstance(active_payload, dict) else None
    else:
        active_version = active.get("version")
    runtime = assistant_metrics.snapshot()
    schedule = str(os.getenv("ASSISTANT_TRAINING_SCHEDULE", "manual")).strip().lower()
    if schedule not in {"manual", "weekly", "biweekly", "semanal", "quincenal"}:
        schedule = "manual"
    return {
        "generation_mode": "local_only",
        "online_training_enabled": False,
        "automatic_promotion_enabled": False,
        "training_schedule": schedule,
        "active_version": str(active_version or "")[:80] or None,
        "responses": runtime.get("requests", {}).get("total", 0),
        "confidence": runtime.get("confidence", {}),
        "fallbacks": runtime.get("requests", {}).get("fallbacks", 0),
        "errors": runtime.get("requests", {}).get("errors", 0),
        "learning_runtime": runtime.get("learning", {}),
        "feedback": {
            "captured_in_memory": feedback_store.snapshot().get("in_memory", 0),
            "persistence_enabled": feedback_store.snapshot().get("persistence_enabled", False),
            "pending": status_counts.get("pending_review", 0) + status_counts.get("pending", 0),
            "needs_edit": status_counts.get("needs_edit", 0),
            "approved": max(status_counts.get("approved", 0), len(approved_file)),
            "rejected": max(status_counts.get("rejected", 0), len(rejected_file)),
        },
        "models": {
            "active": registry_counts.get("active", 0),
            "candidates": registry_counts.get("candidate", 0),
            "archived": registry_counts.get("archived", 0),
            "rejected": registry_counts.get("rejected", 0),
            "promotions": promotions,
            "rollbacks": rollbacks,
        },
        "model_versions": [_safe_model(item) for item in registry[-25:]],
    }


__all__ = ["learning_metrics_snapshot"]
