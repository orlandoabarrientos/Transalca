"""Health aggregation for the assistant without leaking configuration details."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent


def _flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _safe_component(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": "unknown"}
    allowed = {
        "status", "available", "enabled", "configured", "provider", "cached_items",
        "cached_sessions", "active_sessions", "circuit_open", "last_success_at",
        "last_error_at", "error", "ttl_seconds", "max_sessions", "model_version",
    }
    result = {key: value[key] for key in allowed if key in value}

    if "error" in result:
        error = str(result["error"] or "")
        result["error"] = error.split(":", 1)[0][:80] if error else None
    return result or {"status": "unknown"}


class AssistantHealth:
    def __init__(self, cache_ttl: int = 60) -> None:
        self.started_at = time.time()
        self.cache_ttl = max(5, int(cache_ttl))
        self._lock = threading.RLock()
        self._asset_cache: tuple[float, dict[str, Any]] | None = None

    def snapshot(self, runtime: Any = None) -> dict[str, Any]:
        components: dict[str, Any] = {}
        if runtime is not None:
            health_method = getattr(runtime, "health", None)
            if callable(health_method):
                try:
                    raw = health_method()
                except Exception as exc:
                    components["orchestrator"] = {"status": "degraded", "error": exc.__class__.__name__}
                else:
                    if isinstance(raw, dict):
                        nested = raw.get("components") if isinstance(raw.get("components"), dict) else raw
                        for name, value in nested.items():
                            if name in {"status", "timestamp", "request_id", "uptime_seconds"}:
                                continue
                            components[str(name)[:48]] = _safe_component(value)
                        components.setdefault("orchestrator", {"status": str(raw.get("status") or "ok")})
        assets = self._assets()
        required_assets_ok = all(
            assets.get(name, {}).get("available")
            for name in ("business_knowledge", "service_knowledge", "vehicle_aliases", "technical_knowledge")
        )
        component_failure = any(
            value.get("status") in {"error", "down", "degraded"}
            for value in components.values()
            if isinstance(value, dict)
        )
        status = "ok" if required_assets_ok and not component_failure else "degraded"
        return {
            "status": status,
            "service": "transalca-automotive-assistant",
            "version": "2.0",
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "components": components,
            "assets": assets,
            "features": {
                "web_enabled": _flag("ASSISTANT_WEB_ENABLED", True),
                "generation_mode": "local_only",
                "feedback_persistence_enabled": _flag("ASSISTANT_FEEDBACK_PERSIST", False),
                "online_training_enabled": False,
            },
        }

    def _assets(self) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            if self._asset_cache and now - self._asset_cache[0] < self.cache_ttl:
                return json.loads(json.dumps(self._asset_cache[1]))
            assets = {
                "business_knowledge": self._json_asset(BASE_DIR / "data" / "business_faq.json"),
                "service_knowledge": self._json_asset(BASE_DIR / "data" / "service_knowledge.json"),
                "vehicle_aliases": self._json_asset(BASE_DIR / "data" / "vehicle_aliases.json"),
                "curated_fitment": self._json_asset(BASE_DIR / "data" / "curated_fitment.json", optional=True),
                "technical_knowledge": self._json_asset(BASE_DIR / "data" / "tire_technical_knowledge.json"),
                "intent_model": self._model_asset(BASE_DIR / "models" / "intent_model.json"),
                "training_dataset": self._jsonl_asset(BASE_DIR / "data" / "generated_training_cases.jsonl"),
            }
            self._asset_cache = (now, assets)
            return json.loads(json.dumps(assets))

    @staticmethod
    def _json_asset(path: Path, optional: bool = False) -> dict[str, Any]:
        if not path.exists():
            return {"available": False, "required": not optional}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"available": False, "valid": False, "required": not optional}
        items = len(value) if isinstance(value, (list, dict)) else 1
        return {"available": True, "valid": True, "items": items, "required": not optional}

    @staticmethod
    def _model_asset(path: Path) -> dict[str, Any]:
        result = AssistantHealth._json_asset(path, optional=True)
        if not result.get("available"):
            return result
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return result
        result["version"] = str(value.get("version") or "unknown")[:40] if isinstance(value, dict) else "unknown"
        result["labels"] = len(value.get("labels") or []) if isinstance(value, dict) else 0
        return result

    @staticmethod
    def _jsonl_asset(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"available": False, "required": False, "cases": 0}
        try:
            with path.open("r", encoding="utf-8") as stream:
                count = sum(1 for line in stream if line.strip())
        except OSError:
            return {"available": False, "valid": False, "required": False, "cases": 0}
        return {"available": True, "valid": count == 5000, "required": False, "cases": count}


assistant_health = AssistantHealth()


__all__ = ["AssistantHealth", "assistant_health"]
