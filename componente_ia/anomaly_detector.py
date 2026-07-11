"""Deteccion local de señales que ameritan revision de una interaccion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping


_CORRECTION_RE = re.compile(
    r"\b(?:no entendiste|no me entendiste|eso no fue|est[aá] mal|me refiero a|"
    r"en realidad|quise decir|perd[oó]n|te corrijo|corrijo)\b",
    re.I,
)
_AMBIGUITY_RE = re.compile(r"\b(?:no s[eé]|creo que|tal vez|quiz[aá]s|puede ser|uno de esos)\b", re.I)
_TIMEOUT_RE = re.compile(r"\b(?:timeout|tiempo de espera|connection error|excepci[oó]n|error interno)\b", re.I)
_GENERIC_ANSWERS = {
    "no tengo informacion", "no tengo información", "no se", "no sé",
    "puedes darme mas datos", "puedes darme más datos", "intenta de nuevo",
}
_VEHICLE_INTENTS = {
    "tire_size_lookup", "tire_recommendation", "tire_change_compatibility",
    "truck_tire_advice", "product_recommendation",
}


def _normalized(value: Any) -> str:
    return " ".join(re.findall(r"[a-záéíóúñ0-9]+", str(value or "").lower()))


@dataclass(frozen=True, slots=True)
class AnomalyResult:
    candidate: bool
    reasons: tuple[str, ...]
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return {"candidate": self.candidate, "reasons": list(self.reasons), "severity": self.severity}


class AnomalyDetector:
    """High-recall rules; it only proposes review and never changes a model."""

    def __init__(self, low_confidence: float = 0.65) -> None:
        self.low_confidence = max(0.0, min(1.0, float(low_confidence)))

    def detect(
        self,
        *,
        message: Any,
        answer: Any = "",
        intent: Any = "unknown",
        confidence: Any = 0.0,
        entities: Any = None,
        fallback: bool = False,
        web_attempted: bool = False,
        web_sources: int | None = None,
        inventory_matches: int | None = None,
        service_matches: int | None = None,
        user_reformulated: bool = False,
        user_corrected: bool = False,
        previous_message: Any = "",
        signals: Iterable[Any] | None = None,
        error: Any = None,
        novel_terms: Iterable[str] | None = None,
    ) -> AnomalyResult:
        reasons = {str(item).strip().lower() for item in (signals or []) if str(item).strip()}
        raw_message = str(message or "")
        raw_answer = str(answer or "")
        normalized_message = _normalized(raw_message)
        normalized_answer = _normalized(raw_answer)
        try:
            score = float(confidence)
        except (TypeError, ValueError):
            score = 0.0

        if score < self.low_confidence:
            reasons.add("low_confidence")
        if fallback:
            reasons.add("fallback")
        if _AMBIGUITY_RE.search(raw_message):
            reasons.add("ambiguous_intent")
        correction = bool(user_corrected or user_reformulated or _CORRECTION_RE.search(raw_message))
        if user_reformulated:
            reasons.add("user_reformulated")
        if correction:
            reasons.add("user_corrected")
        if previous_message:
            ratio = SequenceMatcher(None, normalized_message, _normalized(previous_message)).ratio()
            if ratio >= 0.88 and normalized_message:
                reasons.add("repeated_question")
        if inventory_matches == 0:
            reasons.add("inventory_without_results")
        if service_matches == 0:
            reasons.add("service_without_results")
        if web_attempted and not int(web_sources or 0):
            reasons.add("web_without_source")
        if error is not None or _TIMEOUT_RE.search(raw_answer):
            reasons.add("error_or_timeout")
        if novel_terms:
            reasons.add("new_vocabulary")
        if self._is_generic(raw_message, normalized_answer):
            reasons.add("generic_answer")
        if self._entities_incomplete(str(intent or ""), entities):
            reasons.add("entities_incomplete")

        severe = {"error_or_timeout", "user_corrected", "security_regression", "private_data"}
        severity = "high" if reasons & severe else "medium" if reasons else "none"
        return AnomalyResult(bool(reasons), tuple(sorted(reasons)), severity)

    @staticmethod
    def _is_generic(message: str, normalized_answer: str) -> bool:
        if len(message.strip()) < 8:
            return False
        if not normalized_answer or normalized_answer in _GENERIC_ANSWERS:
            return True
        return len(normalized_answer.split()) < 4

    @staticmethod
    def _entities_incomplete(intent: str, entities: Any) -> bool:
        if intent not in _VEHICLE_INTENTS:
            return False
        if hasattr(entities, "to_dict"):
            entities = entities.to_dict()
        if not isinstance(entities, Mapping):
            return True
        vehicle_known = bool(entities.get("model") or entities.get("vehicle_type"))
        tire_known = bool(
            entities.get("current_tire_size") or entities.get("requested_tire_size")
            or entities.get("current_rim") or entities.get("requested_rim") or entities.get("rim")
        )
        if intent == "truck_tire_advice":
            return not (vehicle_known and tire_known)
        return not vehicle_known


anomaly_detector = AnomalyDetector()


__all__ = ["AnomalyDetector", "AnomalyResult", "anomaly_detector"]
