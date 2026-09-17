from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping

from componente_ia.tire_size_parser import normalize_tire_size, parse_tire_size

CANONICAL_ENTITY_FIELDS = (
    "vehicle_brand",
    "vehicle_model",
    "vehicle_year",
    "vehicle_version",
    "vehicle_type",
    "tire_size",
    "rim",
    "tire_type",
    "product_brand",
    "product_model",
    "service",
    "payment_method",
    "branch",
    "usage",
    "terrain",
    "truck_axle",
    "load_index",
    "speed_rating",
    "asks_price",
    "asks_stock",
    "asks_comparison",
)

BOOLEAN_FIELDS = frozenset({"asks_price", "asks_stock", "asks_comparison"})
LIST_FIELDS = frozenset({"usage", "terrain"})

LEGACY_ALIASES: dict[str, tuple[str, ...]] = {
    "vehicle_brand": ("vehicle_brand", "make"),
    "vehicle_model": ("vehicle_model", "model"),
    "vehicle_year": ("vehicle_year", "year"),

    "vehicle_version": ("vehicle_version", "trim"),
    "vehicle_type": ("vehicle_type",),
    "tire_size": (
        "tire_size", "requested_tire_size", "current_tire_size",
    ),
    "rim": ("rim", "requested_rim", "current_rim"),
    "tire_type": ("tire_type",),
    "product_brand": ("product_brand", "brand"),

    "product_model": ("product_name", "product_model"),
    "service": ("service",),
    "payment_method": ("payment_method",),
    "branch": ("branch",),
    "usage": ("usage",),
    "terrain": ("terrain",),
    "truck_axle": ("truck_axle",),
    "load_index": ("load_index",),
    "speed_rating": ("speed_rating",),
    "asks_price": ("asks_price",),
    "asks_stock": ("asks_stock",),
    "asks_comparison": ("asks_comparison",),
}

CONFIRMABLE_ENTITY_FIELDS = frozenset({
    "vehicle_brand", "vehicle_model", "vehicle_year", "vehicle_version",
    "vehicle_type", "tire_size", "rim", "tire_type", "branch",
})

_TERRAIN_VALUES = frozenset({"highway", "gravel", "dirt", "offroad", "mud"})

def _semantic_token(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[\s_-]+", "_", text.casefold()).strip("_")

_VEHICLE_TYPES = {
    "sedan": "sedan", "hatchback": "hatchback", "suv": "suv",
    "crossover": "crossover", "pickup": "pickup", "camioneta": "pickup",
    "pick_up": "pickup", "4x4": "4x4",
    "camion": "camion_pesado",
    "camion_liviano": "camion_liviano", "camion_mediano": "camion_mediano",
    "camion_pesado": "camion_pesado", "gandola": "gandola",
    "autobus": "autobus", "vehiculo_comercial": "vehiculo_comercial",
    "flota": "flota",
}
_USAGE_VALUES = {
    "carretera": "highway", "autopista": "highway", "asfalto": "highway",
    "highway": "highway", "ciudad": "city", "urbano": "city", "city": "city",
    "tierra": "dirt", "dirt": "dirt", "grava": "gravel", "gravel": "gravel",
    "barro": "mud", "lodo": "mud", "mud": "mud", "montana": "offroad",
    "off_road": "offroad", "offroad": "offroad", "carga": "load", "load": "load",
    "lluvia": "rain", "rain": "rain", "silencioso": "quiet", "quiet": "quiet",
    "economico": "economy", "economy": "economy", "remolque": "trailer",
    "trailer": "trailer", "flota": "fleet", "fleet": "fleet",
}
_PAYMENT_VALUES = {
    "pago_movil": "pago_movil", "pagomovil": "pago_movil",
    "binance": "binance", "zelle": "zelle",
}

_SERVICE_VALUES = {
    "alignment": "alignment", "alineacion": "alignment",
    "balancing": "balancing", "balanceo": "balancing",
    "rotation": "rotation", "rotacion": "rotation", "rotacion_de_cauchos": "rotation",
    "mounting": "mounting", "montaje": "mounting", "montaje_de_cauchos": "mounting",
    "tire_repair": "tire_repair", "reparacion_de_cauchos": "tire_repair",
    "valve": "valve", "cambio_de_valvula": "valve",
    "oil_change": "oil_change", "cambio_de_aceite": "oil_change",
    "filters": "filters", "cambio_de_filtros": "filters",
    "brakes": "brakes", "revision_de_frenos": "brakes",
    "scanner": "scanner", "diagnostico_con_scanner": "scanner",
    "batteries": "batteries", "prueba_de_bateria": "batteries",
    "injectors": "injectors", "revision_de_inyectores": "injectors",
    "suspension": "suspension", "revision_de_suspension": "suspension",
    "front_end": "front_end", "revision_de_tren_delantero": "front_end",
    "preventive_maintenance": "preventive_maintenance",
    "mantenimiento_preventivo": "preventive_maintenance",
    "heavy_vehicle_inspection": "heavy_vehicle_inspection",
    "atencion_de_vehiculos_de_carga": "heavy_vehicle_inspection",
}

CANONICAL_SERVICE_VALUES = frozenset(_SERVICE_VALUES.values())
_AXLE_PATTERNS = (
    ("steer", re.compile(

        r"\b(?:eje\s+(?:delantero|direccional|de\s+direccion)|"
        r"posicion\s+direccional|steer(?:ing)?\s+axle)\b",
        re.IGNORECASE,
    )),
    ("drive", re.compile(
        r"\b(?:eje\s+(?:motriz|de\s+traccion)|traccion|drive\s+axle)\b",
        re.IGNORECASE,
    )),
    ("trailer", re.compile(
        r"\b(?:eje\s+de\s+remolque|remolque|trailer(?:\s+axle)?)\b",
        re.IGNORECASE,
    )),
)

def _present(value: Any) -> bool:
    return value not in (None, "", [], {}, (), False)

def _first_present(source: Mapping[str, Any], aliases: tuple[str, ...]) -> tuple[Any, str | None]:
    for alias in aliases:
        value = source.get(alias)
        if _present(value):
            return value, alias
    return None, None

def _dedupe(values: Any) -> list[str]:
    if values in (None, ""):
        return []
    if isinstance(values, str):
        values = [values]
    return list(dict.fromkeys(str(value) for value in values if _present(value)))

def _canonical_usage(values: Any) -> list[str]:
    result: list[str] = []
    for value in _dedupe(values):
        token = _semantic_token(value)
        canonical = _USAGE_VALUES.get(token, token)
        if canonical and canonical not in result:
            result.append(canonical)
    return result

def _normalize_rim(value: Any) -> int | float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not 10 <= number <= 26 or not (number.is_integer() or number % 1 == 0.5):
        return None
    return int(number) if number.is_integer() else number

def _extract_truck_axle(source: Mapping[str, Any]) -> str | None:
    value = source.get("truck_axle")
    if _present(value):
        clean = str(value).strip().casefold()
        if clean in {"steer", "drive", "trailer"}:
            return clean
    text = str(source.get("normalized") or source.get("raw") or "")
    for canonical, pattern in _AXLE_PATTERNS:
        if pattern.search(text):
            return canonical
    return None

@dataclass(frozen=True)
class CanonicalEntityResult:
    entities: dict[str, Any]
    provenance: dict[str, dict[str, Any]]
    aliases_used: dict[str, str]

    def to_dict(self, *, include_metadata: bool = True) -> dict[str, Any]:
        if not include_metadata:
            return dict(self.entities)
        return {
            "schema_version": "v8.1",
            "entities": dict(self.entities),
            "provenance": dict(self.provenance),
            "aliases_used": dict(self.aliases_used),
        }

def canonicalize_entities(
    value: Mapping[str, Any] | None,
    *,
    provenance: Mapping[str, Mapping[str, Any]] | None = None,
    include_empty: bool = True,
) -> CanonicalEntityResult:

    source = dict(value or {})
    source_provenance = dict(provenance or {})
    canonical: dict[str, Any] = {}
    canonical_provenance: dict[str, dict[str, Any]] = {}
    aliases_used: dict[str, str] = {}

    for field_name in CANONICAL_ENTITY_FIELDS:
        raw, alias = _first_present(source, LEGACY_ALIASES[field_name])
        if field_name in BOOLEAN_FIELDS:
            raw = bool(raw)
        elif field_name in LIST_FIELDS:
            raw = _canonical_usage(raw)
        elif field_name == "vehicle_year" and _present(raw):
            try:
                raw = int(raw)
            except (TypeError, ValueError):
                raw = None
        elif field_name == "tire_size" and _present(raw):
            raw = normalize_tire_size(raw)
        elif field_name == "rim" and _present(raw):
            raw = _normalize_rim(raw)
        elif field_name == "vehicle_type" and _present(raw):
            token = _semantic_token(raw)
            raw = _VEHICLE_TYPES.get(token, token)
        elif field_name == "payment_method" and _present(raw):
            token = _semantic_token(raw)
            raw = _PAYMENT_VALUES.get(token, str(raw).strip())
        elif field_name == "service" and _present(raw):
            token = _semantic_token(raw)
            raw = _SERVICE_VALUES.get(token, str(raw).strip().casefold())
        elif field_name == "tire_type" and _present(raw):
            token = str(raw).strip().upper().replace(" ", "")
            raw = token if "/" in token else ({"AT": "A/T", "HT": "H/T", "RT": "R/T", "MT": "M/T"}.get(token, token))
        elif field_name in {"vehicle_brand", "vehicle_model", "product_brand", "product_model"} and _present(raw):
            raw = re.sub(r"\s+", " ", str(raw)).strip()

        if include_empty or _present(raw) or field_name in BOOLEAN_FIELDS or field_name in LIST_FIELDS:
            canonical[field_name] = raw if _present(raw) or field_name not in BOOLEAN_FIELDS else bool(raw)
        if alias:
            aliases_used[field_name] = alias
            details = source_provenance.get(alias)
            if details:
                canonical_provenance[field_name] = dict(details)

    size = canonical.get("tire_size")
    if size:
        parsed = parse_tire_size(size)
        if parsed is not None:
            canonical["rim"] = parsed.rim
            aliases_used.setdefault("rim", "tire_size")
            canonical_provenance.setdefault(
                "rim", {"source": "exact_tire_size_parser", "confidence": 1.0},
            )

    brand = str(canonical.get("vehicle_brand") or "").strip()
    model = str(canonical.get("vehicle_model") or "").strip()
    if brand and model:
        reduced = re.sub(rf"^{re.escape(brand)}(?:[\s_-]+)", "", model, flags=re.IGNORECASE).strip()
        if reduced:
            canonical["vehicle_model"] = reduced

    usage = _canonical_usage(canonical.get("usage"))
    canonical["usage"] = usage
    explicit_terrain = _canonical_usage(canonical.get("terrain"))
    canonical["terrain"] = list(dict.fromkeys([
        *explicit_terrain,
        *(item for item in usage if item in _TERRAIN_VALUES),
    ]))
    if canonical["terrain"] and "terrain" not in canonical_provenance:
        canonical_provenance["terrain"] = {
            "source": "usage_dictionary_derivation", "confidence": 1.0,
        }

    axle = _extract_truck_axle(source)
    if axle:
        canonical["truck_axle"] = axle
        aliases_used["truck_axle"] = "truck_axle" if source.get("truck_axle") else "raw"
        canonical_provenance.setdefault(
            "truck_axle", {"source": "exact_parser", "confidence": 1.0},
        )

    if not include_empty:
        canonical = {
            key: item for key, item in canonical.items()
            if _present(item) or (key in BOOLEAN_FIELDS and bool(item))
        }
    return CanonicalEntityResult(canonical, canonical_provenance, aliases_used)

def canonical_to_legacy_patch(value: Mapping[str, Any]) -> dict[str, Any]:

    result: dict[str, Any] = {}
    reverse = {
        "vehicle_brand": "make",
        "vehicle_model": "model",
        "vehicle_year": "year",
        "vehicle_version": "trim",
        "vehicle_type": "vehicle_type",
        "tire_size": "requested_tire_size",
        "rim": "requested_rim",
        "tire_type": "tire_type",
        "product_brand": "brand",
        "product_model": "product_model",
        "service": "service",
        "payment_method": "payment_method",
        "branch": "branch",
        "usage": "usage",
        "truck_axle": "truck_axle",
        "load_index": "load_index",
        "speed_rating": "speed_rating",
    }
    for canonical, legacy in reverse.items():
        item = value.get(canonical)
        if _present(item):
            result[legacy] = item
    return result

__all__ = [
    "BOOLEAN_FIELDS", "CANONICAL_ENTITY_FIELDS", "CANONICAL_SERVICE_VALUES",
    "CONFIRMABLE_ENTITY_FIELDS",
    "CanonicalEntityResult", "LEGACY_ALIASES", "canonical_to_legacy_patch",
    "canonicalize_entities",
]
