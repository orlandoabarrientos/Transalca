"""Resolucion de vehiculos conocidos, regionales y desconocidos.

Resolver un nombre no equivale a validar una medida. Este modulo solo produce
identidad linguistica y banderas de incertidumbre para que el orquestador pueda
pedir datos o consultar una fuente tecnica.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any, Iterator

from componente_ia.vehicle_aliases import alias_indexes, normalize_alias, resolve_make, resolve_model


@dataclass
class VehicleResolution:
    make: str | None = None
    model: str | None = None
    submodel: str | None = None
    vehicle_type: str | None = None
    family: str | None = None
    confidence: float = 0.0
    matched_alias: str | None = None
    known_make: bool = False
    known_model: bool = False
    unknown_candidate: str | None = None
    needs_web: bool = False
    ambiguous: bool = False
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())


def _bounded_matches(text: str, aliases: dict[str, Any]) -> list[tuple[int, int, str, Any]]:
    matches: list[tuple[int, int, str, Any]] = []
    for alias, target in aliases.items():
        if not alias:
            continue

        if alias.isdigit() and not any(make in text for make in ("hino", "ram", "ford")):
            continue
        found = re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text)
        if found:
            matches.append((found.start(), found.end(), alias, target))
    return matches


def _best_known_model(text: str) -> tuple[str | None, dict[str, Any] | None, int]:
    matches = _bounded_matches(text, alias_indexes()["models"])
    if not matches:
        return None, None, -1

    correction = bool(re.search(r"\b(?:en realidad|mejor|no es|quise decir|corrijo)\b", text))
    if correction:
        chosen = max(matches, key=lambda item: (item[0], item[1] - item[0]))
    else:
        chosen = min(matches, key=lambda item: (item[0], -(item[1] - item[0])))
    return chosen[2], dict(chosen[3]), chosen[0]


def _best_make(text: str) -> tuple[str | None, str | None, int]:
    matches = _bounded_matches(text, alias_indexes()["makes"])
    if not matches:
        return None, None, -1
    correction = bool(re.search(r"\b(?:en realidad|mejor|no es|quise decir|corrijo)\b", text))
    chosen = max(matches, key=lambda item: item[0]) if correction else min(matches, key=lambda item: item[0])
    return chosen[3], chosen[2], chosen[0]


def _fuzzy_model(text: str) -> tuple[str | None, dict[str, Any] | None, float]:
    words = text.split()
    if not words:
        return None, None, 0.0
    best: tuple[str | None, dict[str, Any] | None, float] = (None, None, 0.0)
    aliases = alias_indexes()["models"]
    for length in (3, 2, 1):
        for index in range(max(0, len(words) - length + 1)):
            candidate = " ".join(words[index:index + length])
            if len(candidate) < 4 or candidate.isdigit():
                continue
            for alias, metadata in aliases.items():
                if abs(len(candidate) - len(alias)) > 3:
                    continue
                score = SequenceMatcher(None, candidate, alias).ratio()
                if score > best[2]:
                    best = (alias, dict(metadata), score)
    return best if best[2] >= 0.84 else (None, None, 0.0)


def _vehicle_type(text: str) -> str | None:
    matches = _bounded_matches(text, alias_indexes()["vehicle_types"])
    if not matches:
        return None
    return max(matches, key=lambda item: item[1] - item[0])[3]


def _unknown_candidate(text: str, known_make_alias: str | None = None) -> str | None:
    stop = {
        "caucho", "cauchos", "llanta", "llantas", "rin", "aro", "que", "cual",
        "necesito", "quiero", "busco", "tiene", "tienen", "usa", "para", "pero",
    }
    if known_make_alias:
        match = re.search(rf"\b{re.escape(known_make_alias)}\b\s+([a-z0-9-]+(?:\s+[a-z0-9-]+)?)", text)
        if match:
            words = [word for word in match.group(1).split() if word not in stop and not re.fullmatch(r"(?:19|20)\d{2}", word)]
            if words:
                return " ".join(words[:2])
    vehicle_context = bool(
        re.search(r"\b(?:tengo|manejo|mi|para (?:un|una)|vehiculo|carro|camioneta|camion)\b", text)
        and (re.search(r"\b(?:19|20)\d{2}\b", text) or re.search(r"\b(?:caucho|llanta|rin|aro)\b", text))
    )
    if not vehicle_context:
        return None
    match = re.search(r"\b(?:tengo|manejo|mi|para)\s+(?:un|una)?\s*([a-z][a-z0-9-]{2,})(?:\s+([a-z0-9-]{2,}))?", text)
    if not match:
        return None
    words = [part for part in match.groups() if part and part not in stop]
    return " ".join(words[:2]) or None


def resolve_vehicle(message: Any = "", make: Any = None, model: Any = None) -> VehicleResolution:
    text = normalize_alias(message)
    explicit_make = resolve_make(make) or (normalize_alias(make) or None)
    explicit_model_record = resolve_model(model)
    explicit_model = explicit_model_record.get("model") if explicit_model_record else (normalize_alias(model) or None)

    make_name, make_alias, _ = _best_make(text)
    model_alias, model_record, _ = _best_known_model(text)
    fuzzy_score = 0.0
    if not model_record:
        model_alias, model_record, fuzzy_score = _fuzzy_model(text)

    resolved_make = explicit_make or make_name
    resolved_model = explicit_model or (model_record.get("model") if model_record else None)
    metadata = explicit_model_record or model_record or {}
    inferred_make = metadata.get("make")
    conflicts: list[str] = []
    if resolved_make and inferred_make and resolved_make != inferred_make:
        conflicts.append("make_model_conflict")
    elif not resolved_make:
        resolved_make = inferred_make

    unknown = None if resolved_model else _unknown_candidate(text, make_alias)
    known_make = bool(resolve_make(resolved_make)) if resolved_make else False
    known_model = bool(metadata)
    confidence = 0.0
    if known_model and (resolved_make or inferred_make):
        confidence = 0.88 if fuzzy_score else 0.97
    elif known_model:
        confidence = 0.84
    elif known_make and unknown:
        confidence = 0.58
    elif known_make:
        confidence = 0.65
    elif unknown:
        confidence = 0.35

    return VehicleResolution(
        make=resolved_make,
        model=resolved_model,
        vehicle_type=metadata.get("type") or _vehicle_type(text),
        family=metadata.get("family"),
        confidence=confidence,
        matched_alias=model_alias or make_alias,
        known_make=known_make,
        known_model=known_model,
        unknown_candidate=unknown,
        needs_web=bool(unknown or (resolved_model and not known_model)),
        ambiguous=bool(conflicts or (not resolved_model and bool(unknown))),
        conflicts=conflicts,
    )


class VehicleResolver:
    def resolve(self, message: Any = "", make: Any = None, model: Any = None) -> VehicleResolution:
        return resolve_vehicle(message, make=make, model=model)


__all__ = ["VehicleResolution", "VehicleResolver", "resolve_vehicle"]
