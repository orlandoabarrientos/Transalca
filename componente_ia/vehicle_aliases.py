"""Catalogo liviano de marcas, modelos y alias regionales.

El catalogo mejora la comprension, pero nunca se trata como evidencia de fitment.
Un modelo no listado puede conservarse como desconocido y resolverse por otra fuente.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


DATA_PATH = Path(__file__).with_name("data") / "vehicle_aliases.json"


def normalize_alias(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=1)
def load_alias_catalog(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path else DATA_PATH
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        data = {"version": "fallback", "makes": {}, "models": {}, "generic_types": {}}
    for key in ("makes", "models", "generic_types"):
        if not isinstance(data.get(key), dict):
            data[key] = {}
    return data


@lru_cache(maxsize=1)
def alias_indexes() -> dict[str, dict[str, Any]]:
    catalog = load_alias_catalog()
    makes: dict[str, str] = {}
    models: dict[str, dict[str, Any]] = {}
    vehicle_types: dict[str, str] = {}

    for canonical, aliases in catalog["makes"].items():
        for alias in {canonical, *(aliases or [])}:
            normalized = normalize_alias(alias)
            if normalized:
                makes[normalized] = canonical

    for canonical, metadata in catalog["models"].items():
        record = dict(metadata or {})
        record["model"] = canonical
        for alias in {canonical, *(record.get("aliases") or [])}:
            normalized = normalize_alias(alias)
            if normalized:
                models[normalized] = record

    for canonical, aliases in catalog["generic_types"].items():
        for alias in {canonical, *(aliases or [])}:
            normalized = normalize_alias(alias)
            if normalized:
                vehicle_types[normalized] = canonical
    return {"makes": makes, "models": models, "vehicle_types": vehicle_types}


def iter_aliases(kind: str) -> Iterable[tuple[str, Any]]:
    return alias_indexes().get(kind, {}).items()


def resolve_make(value: Any) -> str | None:
    return alias_indexes()["makes"].get(normalize_alias(value))


def resolve_model(value: Any) -> dict[str, Any] | None:
    match = alias_indexes()["models"].get(normalize_alias(value))
    return dict(match) if match else None


def resolve_vehicle_type(value: Any) -> str | None:
    return alias_indexes()["vehicle_types"].get(normalize_alias(value))


def model_make(model: Any) -> str | None:
    resolved = resolve_model(model)
    return resolved.get("make") if resolved else None


def aliases_version() -> str:
    return str(load_alias_catalog().get("version") or "unknown")


__all__ = [
    "DATA_PATH",
    "alias_indexes",
    "aliases_version",
    "iter_aliases",
    "load_alias_catalog",
    "model_make",
    "normalize_alias",
    "resolve_make",
    "resolve_model",
    "resolve_vehicle_type",
]
