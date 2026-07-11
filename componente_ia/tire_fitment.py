"""Fitment local curado y calculos geometricos sin afirmar compatibilidad final."""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from componente_ia.entity_extractor import extract_tire_sizes
from componente_ia.vehicle_aliases import normalize_alias, resolve_make, resolve_model


DATA_PATH = Path(__file__).with_name("data") / "curated_fitment.json"


class FitmentResult(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def to_dict(self) -> dict[str, Any]:
        return dict(self)


@lru_cache(maxsize=2)
def load_curated_fitment(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path else DATA_PATH
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        payload = {"version": "unavailable", "updated_at": None, "disclaimer": "", "records": []}
    if not isinstance(payload.get("records"), list):
        payload["records"] = []
    return payload


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default) if value is not None else default


def _canonical_make(value: Any) -> str | None:
    return resolve_make(value) or (normalize_alias(value) or None)


def _canonical_model(value: Any) -> str | None:
    resolved = resolve_model(value)
    return resolved.get("model") if resolved else (normalize_alias(value) or None)


class TireFitmentRepository:
    def __init__(self, path: str | Path | None = None):
        self.path = path

    @property
    def data(self) -> dict[str, Any]:
        return load_curated_fitment(self.path)

    def lookup(
        self,
        entities: Any = None,
        *,
        make: Any = None,
        model: Any = None,
        year: int | None = None,
        rim: float | int | None = None,
        trim: str | None = None,
    ) -> FitmentResult:
        make = _canonical_make(make or _get(entities, "make"))
        model = _canonical_model(model or _get(entities, "model"))
        year = year or _get(entities, "year")
        rim = rim or _get(entities, "requested_rim") or _get(entities, "current_rim")
        trim = trim or _get(entities, "trim")

        missing = [name for name, value in (("model", model), ("year", year)) if not value]
        if missing:
            return FitmentResult({
                "status": "insufficient_data",
                "make": make,
                "model": model,
                "year": year,
                "rim": rim,
                "trim": trim,
                "sizes": [],
                "records": [],
                "confidence": 0.0,
                "missing": missing,
                "requires_confirmation": True,
                "disclaimer": self.data.get("disclaimer") or "Confirmar con fabricante y etiqueta del vehiculo.",
                "evidence_type": "local_fitment",
            })
        matches: list[dict[str, Any]] = []
        for raw in self.data["records"]:
            record = deepcopy(raw)
            if make and _canonical_make(record.get("make")) != make:
                continue
            if model and _canonical_model(record.get("model")) != model:
                continue
            if year and not (int(record.get("year_start", 0)) <= int(year) <= int(record.get("year_end", 9999))):
                continue
            sizes = list(record.get("sizes") or [])
            if rim:
                rim_sizes = []
                for size in sizes:
                    parsed = extract_tire_sizes(size)
                    if parsed and float(parsed[0].rim or 0) == float(rim):
                        rim_sizes.append(size)
                if rim_sizes:
                    record["sizes"] = rim_sizes
                else:

                    record["rim_not_in_local_reference"] = True
            record["source_type"] = "local_curated_fitment"
            record["source_version"] = self.data.get("version")
            record["updated_at"] = self.data.get("updated_at")
            record["requires_confirmation"] = True
            matches.append(record)

        sizes = sorted({size for record in matches for size in record.get("sizes", [])})
        if matches:
            status = "local_reference"
            confidence = max(float(record.get("confidence") or 0.0) for record in matches)
        elif make or model:
            status = "not_found"
            confidence = 0.0
        else:
            status = "insufficient_data"
            confidence = 0.0
        if missing and matches:
            status = "ambiguous_local_reference"

        return FitmentResult({
            "status": status,
            "make": make,
            "model": model,
            "year": year,
            "rim": rim,
            "trim": trim,
            "sizes": sizes,
            "records": matches,
            "confidence": round(confidence, 3),
            "missing": missing,
            "requires_confirmation": True,
            "disclaimer": self.data.get("disclaimer") or "Confirmar con fabricante y etiqueta del vehiculo.",
            "evidence_type": "local_fitment",
        })


def tire_dimensions(size: Any) -> dict[str, Any] | None:
    parsed = extract_tire_sizes(size)
    if not parsed:
        return None
    item = parsed[0]
    result = item.to_dict()
    if item.overall_diameter_in is not None:
        result["overall_diameter_mm"] = round(item.overall_diameter_in * 25.4, 2)
        result["circumference_in"] = round(item.overall_diameter_in * 3.141592653589793, 3)
    else:
        result["overall_diameter_mm"] = None
        result["circumference_in"] = None
    return result


def compare_tire_sizes(current_size: Any, requested_size: Any) -> FitmentResult:
    current = tire_dimensions(current_size)
    requested = tire_dimensions(requested_size)
    if not current or not requested:
        return FitmentResult({
            "status": "invalid_size", "current": current, "requested": requested,
            "diameter_difference_percent": None, "requires_confirmation": True,
        })
    current_diameter = current.get("overall_diameter_in")
    requested_diameter = requested.get("overall_diameter_in")
    if not current_diameter or not requested_diameter:
        return FitmentResult({
            "status": "geometry_unavailable", "current": current, "requested": requested,
            "diameter_difference_percent": None, "requires_confirmation": True,
            "note": "El formato comercial requiere tabla tecnica del fabricante para comparar diametro real.",
        })
    difference = ((requested_diameter - current_diameter) / current_diameter) * 100.0
    indicated_at_100 = 100.0 / (1.0 + difference / 100.0)
    return FitmentResult({
        "status": "requires_vehicle_validation",
        "current": current,
        "requested": requested,
        "diameter_difference_percent": round(difference, 2),
        "absolute_diameter_difference_percent": round(abs(difference), 2),
        "within_common_three_percent_geometry_guideline": abs(difference) <= 3.0,
        "speedometer_indication_when_actual_100": round(indicated_at_100, 1),
        "requires_confirmation": True,
        "checks_required": [
            "medida homologada por fabricante", "indice de carga", "indice de velocidad",
            "ancho de rin", "despeje en suspension y carroceria", "offset y capacidad de frenado",
        ],
        "note": "La similitud de diametro no demuestra compatibilidad ni seguridad.",
    })


def assess_tire_change(current_size: Any, requested_size: Any, fitment: Any = None) -> FitmentResult:
    result = compare_tire_sizes(current_size, requested_size)
    fitment_sizes = set(_get(fitment, "sizes", []) or [])
    normalized_requested = extract_tire_sizes(requested_size)
    requested = normalized_requested[0].normalized if normalized_requested else None
    result["listed_in_local_reference"] = bool(requested and requested in fitment_sizes)
    result["fitment_evidence_available"] = bool(fitment_sizes)

    result["compatible"] = None
    return result


_DEFAULT_REPOSITORY = TireFitmentRepository()


def get_vehicle_fitment(entities: Any = None, **kwargs: Any) -> FitmentResult:
    return _DEFAULT_REPOSITORY.lookup(entities, **kwargs)


lookup_fitment = get_vehicle_fitment


__all__ = [
    "DATA_PATH", "FitmentResult", "TireFitmentRepository", "assess_tire_change",
    "compare_tire_sizes", "get_vehicle_fitment", "load_curated_fitment",
    "lookup_fitment", "tire_dimensions",
]
