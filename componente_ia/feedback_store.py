"""Captura local, acotada y privada de señales para aprendizaje offline.

La persistencia es opt-in. Una peticion nunca entrena, modifica reglas ni promueve
modelos: este almacen solo crea candidatos ``pending_review``. Si la anonimización
no puede demostrar que mensaje, historial y respuesta son seguros, el registro se
descarta antes de llegar a disco.
"""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .anomaly_detector import anomaly_detector
from .feedback_anonymizer import FeedbackAnonymizer, anonymize_text, session_hash


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sanitize_entities_checked(
    entities: Any,
    anonymizer: FeedbackAnonymizer | None = None,
) -> tuple[dict[str, Any], bool]:
    """Allow-list only non-identifying automotive/commercial annotations."""

    cleaner = anonymizer or FeedbackAnonymizer()
    if hasattr(entities, "to_dict"):
        entities = entities.to_dict()
    elif hasattr(entities, "__dataclass_fields__"):
        entities = asdict(entities)
    if not isinstance(entities, dict):
        return {}, True
    allowed = {
        "vehicle_type", "make", "model", "submodel", "year", "trim", "engine",
        "drivetrain", "current_rim", "current_tire_size", "requested_rim",
        "requested_tire_size", "tire_type", "load_index", "speed_rating",
        "load_range", "usage", "budget", "branch", "product_category", "service",
        "asks_price", "asks_stock", "asks_comparison", "rim", "tire_size",
    }
    clean: dict[str, Any] = {}
    safe = True
    for key in sorted(allowed & set(entities)):
        value = entities[key]
        if value in (None, "", [], {}):
            continue
        if isinstance(value, bool):
            clean[key] = value
        elif isinstance(value, (int, float)):
            clean[key] = value
        elif isinstance(value, str):
            result = cleaner.anonymize(value, 120)
            safe = safe and result.safe
            clean[key] = result.text
        elif isinstance(value, (list, tuple, set)):
            values: list[str] = []
            for item in list(value)[:12]:
                result = cleaner.anonymize(item, 80)
                safe = safe and result.safe
                values.append(result.text)
            clean[key] = values
        elif isinstance(value, dict):
            nested: dict[str, Any] = {}
            for nested_key, nested_value in list(value.items())[:12]:
                if not isinstance(nested_value, (str, int, float, bool)):
                    continue
                if isinstance(nested_value, str):
                    result = cleaner.anonymize(nested_value, 100)
                    safe = safe and result.safe
                    nested[str(nested_key)[:40]] = result.text
                else:
                    nested[str(nested_key)[:40]] = nested_value
            clean[key] = nested
    return clean, safe


def sanitize_entities(entities: Any) -> dict[str, Any]:
    """Compatibility API used in public responses; returns only the safe allow-list."""

    clean, safe = _sanitize_entities_checked(entities)
    return clean if safe else {}


@dataclass(slots=True)
class FeedbackRecord:
    case_id: str
    timestamp: str
    session_hash: str
    message_anonymized: str
    history_anonymized: list[str]
    intent_predicted: str
    intent_confidence: float
    entities_predicted: dict[str, Any]
    answer: str
    fallback: bool
    web_attempted: bool
    inventory_matches: int
    service_matches: int
    user_reformulated: bool
    user_corrected: bool
    operator_rating: str | None
    candidate_reason: list[str]
    status: str = "pending_review"
    candidate_for_training: bool = True
    schema_version: int = 2

    intent: str = "unknown"
    confidence: float = 0.0
    entities: dict[str, Any] = field(default_factory=dict)
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FeedbackStore:
    """Thread-safe bounded store; disk writes are disabled unless explicitly enabled."""

    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        persist: bool | None = None,
        max_records: int | None = None,
        anonymizer: FeedbackAnonymizer | None = None,
    ) -> None:
        default_path = Path(__file__).resolve().parent / "data" / "production_feedback.jsonl"
        self.path = Path(path or os.getenv("ASSISTANT_FEEDBACK_PATH") or default_path)
        if persist is None:
            persist = os.getenv("ASSISTANT_FEEDBACK_PERSIST", "0").strip().lower() in {"1", "true", "yes"}
        self.persist = bool(persist)
        self.max_records = max(10, int(max_records or os.getenv("ASSISTANT_FEEDBACK_MEMORY_LIMIT", "2000")))
        self.anonymizer = anonymizer or FeedbackAnonymizer()
        self._records: deque[dict[str, Any]] = deque(maxlen=self.max_records)
        self._lock = threading.RLock()
        self._counters = {
            "captured": 0, "candidates": 0, "approved": 0, "rejected": 0,
            "persist_errors": 0, "privacy_drops": 0,
        }

    def capture_passive_signal(
        self,
        message: str,
        intent: str | None = None,
        entities: Any = None,
        answer: str = "",
        confidence: float | int | None = None,
        fallback: bool = False,
        signals: Iterable[str] | None = None,
        user_reformulated: bool = False,
        operator_rating: str | None = None,
        candidate_for_training: bool | None = None,
        *,
        session_id: Any = None,
        history: Any = None,
        web_attempted: bool = False,
        web_sources: int | None = None,
        inventory_matches: int | None = None,
        service_matches: int | None = None,
        user_corrected: bool = False,
        previous_message: Any = "",
        error: Any = None,
        novel_terms: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        message_result = self.anonymizer.anonymize(message)
        answer_result = self.anonymizer.anonymize(answer, 1800)
        clean_history, history_safe, _history_reasons = self.anonymizer.anonymize_history(history)
        clean_entities, entities_safe = _sanitize_entities_checked(entities, self.anonymizer)
        if not message_result.text or not all((message_result.safe, answer_result.safe, history_safe, entities_safe)):
            with self._lock:
                self._counters["privacy_drops"] += 1
            return {}

        score = self._confidence(confidence)
        clean_intent = self.anonymizer.anonymize(intent or "unknown", 80)
        if not clean_intent.safe:
            with self._lock:
                self._counters["privacy_drops"] += 1
            return {}
        anomaly = anomaly_detector.detect(
            message=message,
            answer=answer,
            intent=clean_intent.text,
            confidence=score,
            entities=clean_entities,
            fallback=fallback,
            web_attempted=web_attempted,
            web_sources=web_sources,
            inventory_matches=inventory_matches,
            service_matches=service_matches,
            user_reformulated=user_reformulated,
            user_corrected=user_corrected,
            previous_message=previous_message,
            signals=signals,
            error=error,
            novel_terms=novel_terms,
        )
        rating = self._rating(operator_rating)
        reasons = {
            reason if re.fullmatch(r"[a-z0-9_.-]{1,80}", reason) else "external_signal"
            for reason in anomaly.reasons
        }
        if rating == "bad":
            reasons.add("operator_bad")
        elif rating == "good":
            reasons.add("operator_good")
        if candidate_for_training is None:
            candidate_for_training = anomaly.candidate or rating is not None
        case_id = f"FB-{uuid.uuid4().hex[:20].upper()}"
        record = FeedbackRecord(
            case_id=case_id,
            timestamp=utc_now(),
            session_hash=session_hash(session_id),
            message_anonymized=message_result.text,
            history_anonymized=clean_history,
            intent_predicted=clean_intent.text,
            intent_confidence=score,
            entities_predicted=clean_entities,
            answer=answer_result.text,
            fallback=bool(fallback),
            web_attempted=bool(web_attempted),
            inventory_matches=self._match_count(inventory_matches),
            service_matches=self._match_count(service_matches),
            user_reformulated=bool(user_reformulated),
            user_corrected=bool(user_corrected or "user_corrected" in reasons),
            operator_rating=rating,
            candidate_reason=sorted(reasons),
            status="pending_review",
            candidate_for_training=bool(candidate_for_training),
            intent=clean_intent.text,
            confidence=score,
            entities=clean_entities,
            signals=sorted(reasons),
        ).to_dict()
        with self._lock:
            self._records.append(record)
            self._counters["captured"] += 1
            if record["candidate_for_training"]:
                self._counters["candidates"] += 1
            if self.persist:
                self._append(record)
        return record

    def rate(self, case_id: str, rating: str) -> bool:
        clean_rating = self._rating(rating)
        if clean_rating is None:
            return False
        with self._lock:
            for record in reversed(self._records):
                if record.get("case_id") != case_id:
                    continue
                record["operator_rating"] = clean_rating
                reason = f"operator_{clean_rating}"
                record["candidate_reason"] = sorted(set(record.get("candidate_reason") or []) | {reason})
                record["signals"] = list(record["candidate_reason"])
                record["candidate_for_training"] = True
                return True
        return False

    def records(self, candidates_only: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            rows = [dict(item) for item in self._records]
        return [item for item in rows if item.get("candidate_for_training")] if candidates_only else rows

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                **self._counters,
                "in_memory": len(self._records),
                "persistence_enabled": self.persist,
                "schema_version": 2,
            }

    def clear_memory(self) -> None:
        with self._lock:
            self._records.clear()

    def _append(self, record: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            self._counters["persist_errors"] += 1

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            return round(max(0.0, min(1.0, float(value))), 4)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _match_count(value: Any) -> int:
        if value is None:
            return -1
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return -1

    @staticmethod
    def _rating(value: Any) -> str | None:
        mapping = {
            "good": "good", "buena": "good", "bueno": "good", "1": "good",
            "bad": "bad", "mala": "bad", "malo": "bad", "-1": "bad",
        }
        return mapping.get(str(value or "").strip().lower())


feedback_store = FeedbackStore()


__all__ = [
    "FeedbackRecord", "FeedbackStore", "anonymize_text", "feedback_store",
    "sanitize_entities",
]
