"""Extraccion determinista de entidades automotrices y comerciales.

No requiere modelos pesados. Conserva tanto valores normalizados como detalles
de la expresion original y acepta acceso estilo diccionario o atributo.
"""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from componente_ia.vehicle_resolver import resolve_vehicle


_TYPO_REPLACEMENTS = {
    "cauxos": "cauchos", "cauchoz": "cauchos", "caucos": "cauchos",
    "yantas": "llantas", "neumaticoz": "neumaticos", "gomaas": "gomas",
    "rinn": "rin", "rrin": "rin", "arito": "aro", "presio": "precio",
    "stok": "stock", "stoc": "stock", "disponivle": "disponible",
    "balanseo": "balanceo", "balansio": "balanceo", "alineasion": "alineacion",
    "alinasion": "alineacion", "rotasion": "rotacion", "escanner": "scanner",
    "scaner": "scanner", "aseite": "aceite", "aceyte": "aceite",
    "vateria": "bateria", "vaterias": "baterias", "frenoz": "frenos",
    "forruner": "4runner", "forrunner": "4runner", "corola": "corolla",
    "autanna": "autana", "cheroky": "cherokee", "explore": "explorer",
    "silveradoo": "silverado", "fronetier": "frontier",
}

_SERVICE_ALIASES = {
    "alignment": ("alineacion", "alinear", "jala", "desvia", "tira hacia"),
    "balancing": ("balanceo", "balancear", "vibra", "vibracion", "tiembla"),
    "rotation": ("rotacion", "rotar", "permutacion"),
    "mounting": ("montaje", "montar", "instalar cauchos", "instalacion de cauchos"),
    "tire_repair": ("reparacion de caucho", "parchar", "parche", "pinchazo"),
    "valve": ("valvula", "cambio de valvula"),
    "oil_change": ("cambio de aceite", "aceite"),
    "filters": ("filtro", "filtros"),
    "brakes": ("freno", "frenos", "pastillas", "discos"),
    "scanner": ("scanner", "diagnostico", "check engine"),
    "batteries": ("bateria", "baterias"),
    "injectors": ("inyector", "inyectores", "inyeccion"),
    "suspension": ("suspension", "amortiguador", "amortiguadores"),
    "front_end": ("tren delantero", "terminal", "rotula"),
    "preventive_maintenance": ("mantenimiento preventivo", "mantenimiento"),
    "heavy_vehicle_inspection": ("revision de carga", "vehiculo de carga", "camion"),
}

_PRODUCT_CATEGORIES = {
    "tires": ("caucho", "cauchos", "llanta", "llantas", "goma", "gomas", "neumatico", "neumaticos"),
    "batteries": ("bateria", "baterias"),
    "oil": ("aceite", "lubricante"),
    "filters": ("filtro", "filtros"),
    "brakes": ("freno", "frenos", "pastilla", "pastillas", "disco", "discos"),
    "parts": ("repuesto", "repuestos", "pieza", "piezas"),
}

_USAGE_ALIASES = {
    "city": ("ciudad", "urbano"),
    "highway": ("autopista", "carretera", "asfalto", "viaje"),
    "rain": ("lluvia", "mojado", "agua", "hidroplaneo"),
    "gravel": ("grava", "piedra"),
    "dirt": ("tierra", "trocha", "rustiqueo", "off road", "offroad"),
    "mud": ("barro", "lodo", "fango", "pantano"),
    "load": ("carga", "cargar", "peso", "mercancia"),
    "trailer": ("remolque", "remolcar", "trailer"),
    "fleet": ("flota", "flotas"),
    "quiet": ("silencioso", "silenciosa", "sin ruido", "no haga ruido"),
}


@dataclass(frozen=True)
class TireSize:
    raw: str
    normalized: str
    format: str
    width: float | None = None
    aspect_ratio: float | None = None
    rim: float | int | None = None
    prefix: str | None = None
    overall_diameter_in: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExtractedEntities(dict):
    """Diccionario con accesores compatibles para migraciones graduales."""

    _ALIASES = {
        "rim": "requested_rim",
        "tire_size": "requested_tire_size",
        "uses": "usage",
        "max_price": "budget_max",
    }

    def __getattr__(self, name: str) -> Any:
        key = self._ALIASES.get(name, name)
        if key == "requested_rim" and not self.get(key):
            return self.get("current_rim")
        if key == "requested_tire_size" and not self.get(key):
            return self.get("current_tire_size")
        if key == "usage":
            return set(self.get(key) or [])
        if key == "tokens":
            return set(self.get(key) or [])
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def to_dict(self) -> dict[str, Any]:
        return dict(self)

    def to_public_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def has_vehicle(self) -> bool:
        return bool(self.get("make") or self.get("model") or self.get("year"))

    def has_tire_request(self) -> bool:
        return bool(
            self.get("requested_tire_size") or self.get("current_tire_size")
            or self.get("requested_rim") or self.get("current_rim")
            or self.get("tire_type") or self.get("product_category") == "tires"
        )


def _strip_accents(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return text.encode("ascii", "ignore").decode("ascii")


def normalize_message(value: Any) -> str:
    text = html.unescape(str(value or "")).strip()
    text = re.sub(r"<[^>]{0,500}>", " ", text)
    text = _strip_accents(text).lower()
    text = text.replace("todo-terreno", "todo terreno")
    text = re.sub(r"\b4\s+runner\b", "4runner", text)
    tokens = []
    for token in re.split(r"(\W+)", text):
        tokens.append(_TYPO_REPLACEMENTS.get(token, token))
    text = "".join(tokens)
    text = re.sub(r"[^a-z0-9$€./+_\-\sx]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _number(value: str) -> float | int:
    number = float(value)
    return int(number) if number.is_integer() else number


def _metric_diameter(width_mm: float, aspect: float, rim_in: float) -> float:
    return round((2 * width_mm * (aspect / 100.0) / 25.4) + rim_in, 3)


def extract_tire_sizes(value: Any) -> list[TireSize]:
    text = normalize_message(value).upper()
    found: list[tuple[int, int, TireSize]] = []

    metric = re.compile(
        r"(?<![A-Z0-9])(?P<prefix>LT|P)?\s*(?P<w>\d{3})\s*[/ .-]\s*(?P<a>\d{2})\s*(?:R\s*|[/ .-]\s*)(?P<r>\d{2}(?:\.5)?)(?!\d)",
        re.IGNORECASE,
    )
    flotation = re.compile(
        r"(?<![A-Z0-9])(?P<h>\d{2}(?:\.\d+)?)\s*X\s*(?P<w>\d{1,2}(?:\.\d+)?)\s*R\s*(?P<r>\d{2}(?:\.5)?)(?!\d)",
        re.IGNORECASE,
    )
    conventional = re.compile(
        r"(?<![A-Z0-9.])(?P<w>\d{1,2}(?:\.\d{1,2})?)\s*R\s*(?P<r>\d{2}(?:\.5)?)(?!\d)",
        re.IGNORECASE,
    )
    compact = re.compile(r"(?<![A-Z0-9])(?P<w>\d{3,4})\s*R\s*(?P<r>\d{2}(?:\.5)?)(?!\d)", re.IGNORECASE)

    for match in metric.finditer(text):
        width = float(match.group("w"))
        aspect = float(match.group("a"))
        rim = float(match.group("r"))
        prefix = (match.group("prefix") or "").upper()
        rim_text = str(_number(match.group("r")))
        normalized = f"{prefix}{int(width)}/{int(aspect)}R{rim_text}"
        found.append((match.start(), match.end(), TireSize(
            raw=match.group(0).replace(" ", ""), normalized=normalized, format="metric",
            width=int(width), aspect_ratio=int(aspect), rim=_number(match.group("r")),
            prefix=prefix or None, overall_diameter_in=_metric_diameter(width, aspect, rim),
        )))
    for match in flotation.finditer(text):
        height = float(match.group("h"))
        width = _number(match.group("w"))
        rim = _number(match.group("r"))
        normalized = f"{_number(match.group('h'))}X{width}R{rim}".upper()
        found.append((match.start(), match.end(), TireSize(
            raw=match.group(0).replace(" ", ""), normalized=normalized, format="flotation",
            width=float(width), rim=rim, overall_diameter_in=height,
        )))
    occupied = [(start, end) for start, end, _ in found]
    for pattern, compact_format in ((conventional, False), (compact, True)):
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in occupied):
                continue
            raw_width = match.group("w")
            if compact_format:
                numeric = int(raw_width)
                width_text = f"{numeric / 100:.2f}"
            else:
                width_text = f"{float(raw_width):.2f}" if "." in raw_width else raw_width
            rim = _number(match.group("r"))
            normalized = f"{width_text}R{rim}"
            found.append((match.start(), match.end(), TireSize(
                raw=match.group(0).replace(" ", ""), normalized=normalized,
                format="commercial", width=float(width_text), rim=rim,
            )))
            occupied.append((match.start(), match.end()))

    unique: list[TireSize] = []
    seen: set[str] = set()
    for _, _, size in sorted(found, key=lambda item: item[0]):
        if size.normalized not in seen:
            seen.add(size.normalized)
            unique.append(size)
    return unique


def normalize_tire_size(value: Any) -> str | None:
    sizes = extract_tire_sizes(value)
    return sizes[0].normalized if sizes else None


def _contains_phrase(text: str, phrases: tuple[str, ...] | list[str]) -> bool:
    return any(re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) for phrase in phrases)


def _extract_rim(text: str) -> float | int | None:
    match = re.search(r"\b(?:rin|rines|aro|aros|r)\s*-?\s*(1[2-9]|2\d(?:\.5)?)\b", text)
    if match:
        return _number(match.group(1))
    if re.fullmatch(r"(?:y\s+)?(?:rin|aro)?\s*(1[2-9]|2\d(?:\.5)?)", text):
        return _number(re.search(r"(1[2-9]|2\d(?:\.5)?)", text).group(1))
    return None


def _extract_year(text: str) -> int | None:
    match = re.search(r"\b(19[8-9]\d|20[0-3]\d)\b", text)
    if match:
        return int(match.group(1))
    short = re.search(
        r"(?:\b(?:ano|modelo)\s*['/]?\s*(0\d|1\d|2\d)\b|"
        r"\b['/](0\d|1\d|2\d)\b|^\s*(?:es\s+)?(0\d|1\d|2\d)\s*$)",
        text,
    )
    if short:
        year = int(next(group for group in short.groups() if group is not None))
        return 2000 + year if year <= 35 else 1900 + year
    return None


def _extract_tire_type(text: str) -> str | None:
    rules = (
        ("A/T", (r"\ba\s*/?\s*t\b", r"\ball terrain\b", r"\btodo terreno\b")),
        ("H/T", (r"\bh\s*/?\s*t\b", r"\bhighway terrain\b")),
        ("R/T", (r"\br\s*/?\s*t\b", r"\brugged terrain\b")),
        ("M/T", (r"\bm\s*/?\s*t\b", r"\bmud terrain\b")),
    )
    for value, patterns in rules:
        if any(re.search(pattern, text) for pattern in patterns):
            return value
    return None


def _extract_usage(text: str) -> list[str]:
    return [name for name, aliases in _USAGE_ALIASES.items() if _contains_phrase(text, aliases)]


def _extract_budget(text: str) -> tuple[str | None, float | None]:
    level = None
    if re.search(r"\b(?:economico|economica|economicos|economicas|barato|barata|baratos|baratas|presupuesto bajo)\b", text):
        level = "economy"
    elif re.search(r"\b(?:premium|alta gama|mejor calidad)\b", text):
        level = "premium"
    match = re.search(r"\b(?:hasta|maximo|max|presupuesto(?: de)?|menos de)\s*(?:usd|us\$|\$)?\s*([\d.,]+)", text)
    if not match:
        return level, None
    try:
        number = Decimal(match.group(1).replace(".", "").replace(",", ".") if "," in match.group(1) else match.group(1))
        return level or "maximum", float(number)
    except InvalidOperation:
        return level, None


def _extract_load(text: str) -> tuple[str | None, str | None, str | None]:
    code = re.search(r"\b(\d{2,3}(?:\s*/\s*\d{2,3})?)\s*([a-z])\b", text, re.IGNORECASE)
    if code:
        numeric_parts = [int(part.strip()) for part in code.group(1).split("/")]
        prefix = text[max(0, code.start() - 8):code.start()]
        valid_code = ("/" in code.group(1) or all(value >= 50 for value in numeric_parts)) and not re.search(r"\b(?:rin|aro)\s*$", prefix)
    else:
        valid_code = False
    load_index = re.sub(r"\s+", "", code.group(1)) if code and valid_code else None
    speed = code.group(2).upper() if code and valid_code else None
    load_range = None
    range_match = re.search(r"\b(?:load\s*range|rango\s+de\s+carga|rango)\s*([a-z])\b", text)
    ply_match = re.search(r"\b(\d{1,2})\s*(?:pr|ply)\b", text)
    if range_match:
        load_range = range_match.group(1).upper()
    elif ply_match:
        load_range = f"{ply_match.group(1)}PR"
    return load_index, speed, load_range


def _first_mapping(text: str, mapping: dict[str, tuple[str, ...]]) -> str | None:
    for canonical, aliases in mapping.items():
        if _contains_phrase(text, aliases):
            return canonical
    return None


def _extract_service(text: str) -> str | None:
    direct = _first_mapping(text, _SERVICE_ALIASES)
    if direct:
        product_question = bool(re.search(r"\b(?:tienen|hay|venden|precio|cuanto cuesta|usa|lleva|disponible|stock)\b", text))
        service_action = bool(re.search(r"\b(?:servicio|cambio|cambiar|revision|revisar|diagnostico|hacer|hacen|incluye|mantenimiento)\b", text))
        if direct in {"batteries", "filters", "brakes", "oil_change"} and product_question and not service_action:
            return None
        return direct
    return None


def _extract_branch(text: str) -> str | None:
    match = re.search(r"\b(?:sucursal|sede|tienda)\s+(?:de\s+|en\s+)?([a-z][a-z0-9 -]{1,40})", text)
    if not match:
        return None
    value = re.split(r"\b(?:tiene|tienen|hay|esta|queda|con|y|que)\b", match.group(1))[0].strip()
    return value or None


def _extract_order_reference(text: str) -> str | None:
    match = re.search(r"\b(?:pedido|orden|referencia|ref)\s*(?:numero|nro|no|#)?\s*[:#-]?\s*([a-z0-9][a-z0-9-]{3,30})\b", text)
    return match.group(1).upper() if match else None


def _extract_engine(text: str) -> str | None:
    match = re.search(r"\b(?:motor\s*)?(\d[.,]\d\s*(?:l|lts?)|v[468]|\d\.\d\s*(?:diesel|gasolina))\b", text)
    return match.group(1).replace(",", ".") if match else None


def extract(message: Any) -> ExtractedEntities:
    raw = str(message or "").strip()
    clean = normalize_message(raw)
    sizes = extract_tire_sizes(raw)
    size_values = [size.normalized for size in sizes]
    compares = bool(re.search(r"\b(?:compar|diferencia|cambiar|cambio|paso|pasar|poner en vez)\w*\b", clean) and len(sizes) >= 2)
    current_size = None
    requested_size = None
    if len(sizes) >= 2:
        current_size, requested_size = sizes[0].normalized, sizes[-1].normalized
    elif sizes:
        marks_current = bool(re.search(r"\b(?:actual|tengo puesto|tiene puesto|uso actualmente|medida que tengo)\b", clean))
        current_size = sizes[0].normalized if marks_current else None
        requested_size = None if marks_current else sizes[0].normalized

    explicit_rim = _extract_rim(clean)
    current_rim = sizes[0].rim if current_size and sizes else None
    requested_rim = sizes[-1].rim if requested_size and sizes else explicit_rim
    if explicit_rim and re.search(r"\b(?:actual|tengo|uso|mi)\s+(?:es\s+)?(?:rin|aro)\b", clean):
        current_rim, requested_rim = explicit_rim, requested_rim if requested_size else None

    vehicle = resolve_vehicle(clean)
    model = vehicle.model or vehicle.unknown_candidate
    budget, budget_max = _extract_budget(clean)
    load_index, speed_rating, load_range = _extract_load(clean)
    service = _extract_service(clean)
    product_category = _first_mapping(clean, _PRODUCT_CATEGORIES)
    tokens = sorted(set(re.findall(r"[a-z0-9]+(?:/[a-z0-9]+)?", clean)))

    asks_price = bool(re.search(r"\b(?:precio|precios|cuanto cuesta|cuestan|valor|mas barato|barato|barata|baratos|baratas|economico|economica|economicos|economicas|menor precio|precio menor)\b", clean))
    asks_stock = bool(re.search(r"\b(?:stock|existencia|disponible|disponibles|tienen|hay)\b", clean))
    asks_comparison = compares or bool(re.search(r"\b(?:comparar|comparacion|diferencia|mejor entre|versus|vs)\b", clean))
    drivetrain_match = re.search(r"\b(4x4|4x2|awd|fwd|rwd)\b", clean)
    trim_match = re.search(r"\b(?:version|trim)\s+([a-z0-9][a-z0-9 -]{0,24})", clean)

    result = ExtractedEntities({
        "vehicle_type": vehicle.vehicle_type,
        "make": vehicle.make,
        "model": model,
        "submodel": vehicle.family,
        "year": _extract_year(clean),
        "trim": trim_match.group(1).strip() if trim_match else None,
        "engine": _extract_engine(clean),
        "drivetrain": drivetrain_match.group(1).upper() if drivetrain_match else None,
        "current_rim": current_rim,
        "current_tire_size": current_size,
        "requested_rim": requested_rim,
        "requested_tire_size": requested_size,
        "tire_type": _extract_tire_type(clean),
        "load_index": load_index,
        "speed_rating": speed_rating,
        "load_range": load_range,
        "usage": _extract_usage(clean),
        "budget": budget,
        "budget_max": budget_max,
        "branch": _extract_branch(clean),
        "product_category": product_category,
        "service": service,
        "order_reference": _extract_order_reference(clean),
        "asks_price": asks_price,
        "asks_stock": asks_stock,
        "asks_comparison": asks_comparison,
        "raw": raw,
        "normalized": clean,
        "clean": clean,
        "tokens": tokens,
        "tire_sizes": size_values,
        "tire_size_details": [size.to_dict() for size in sizes],
        "vehicle_resolution": vehicle.to_dict(),
        "followup": bool(clean.startswith(("y ", "el ", "la ", "ese ", "esa ", "en realidad", "no ")) or len(tokens) <= 5 and any(word in tokens for word in ("primero", "barato", "stock", "precio", "sirve"))),
    })
    return result


class EntityExtractor:
    def extract(self, message: Any) -> ExtractedEntities:
        return extract(message)

    def normalize(self, message: Any) -> str:
        return normalize_message(message)


extract_entities = extract


__all__ = [
    "EntityExtractor",
    "ExtractedEntities",
    "TireSize",
    "extract",
    "extract_entities",
    "extract_tire_sizes",
    "normalize_message",
    "normalize_tire_size",
]
