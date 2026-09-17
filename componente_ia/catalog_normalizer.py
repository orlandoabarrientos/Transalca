from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from componente_ia.brand_model_normalizer import normalize_brand_model
from componente_ia.tire_size_parser import extract_tire_sizes
from componente_ia.tire_type_resolver import TireTypeResolver

_TEXT_FIELDS = (
    "codigo", "code", "sku", "nombre", "name", "descripcion", "description",
    "categoria", "categoria_nombre", "category", "marca", "marca_nombre", "brand",
    "atributos", "attributes", "detalle", "details", "texto", "text",
    "medida", "medidas", "size", "sizes", "tire_size", "tipo", "tipo_caucho",
    "tire_type", "aplicacion", "application",
)
_GLOBAL_STOCK_FIELDS = ("stock", "existencia", "quantity", "cantidad")
_PRICE_FIELDS = ("precio", "price", "precio_venta", "sale_price")

def _ascii(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return text.encode("ascii", "ignore").decode("ascii")

def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _ascii(value).strip())

def _display_text(value: Any) -> str:

    return re.sub(r"\s+", " ", str(value or "").strip())

def _first(raw: Mapping[str, Any], names: Iterable[str], default: Any = None) -> Any:
    for name in names:
        if name in raw and raw.get(name) not in (None, ""):
            return raw.get(name)
    return default

def _flatten_text(value: Any, *, depth: int = 0) -> list[str]:

    if depth > 3 or value is None:
        return []
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key, child in list(value.items())[:80]:
            if str(key).lower() in {"token", "cookie", "password", "secret"}:
                continue
            parts.extend(_flatten_text(child, depth=depth + 1))
        return parts
    if isinstance(value, (list, tuple, set)):
        parts = []
        for child in list(value)[:80]:
            parts.extend(_flatten_text(child, depth=depth + 1))
        return parts
    if isinstance(value, (str, int, float, Decimal)):
        text = _clean_text(value)
        return [text] if text else []
    return []

def _search_text(raw: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in _TEXT_FIELDS:
        if key in raw:
            parts.extend(_flatten_text(raw.get(key)))

    for key in ("metadata", "specifications", "especificaciones"):
        if key in raw:
            parts.extend(_flatten_text(raw.get(key)))
    return re.sub(r"\s+", " ", " ".join(parts)).strip()

def detect_tire_type(value: Any) -> str | None:

    text = _ascii(value).upper()
    text = re.sub(r"[_]+", " ", text)
    patterns = (
        ("M/T", r"(?<![A-Z0-9])(?:M\s*[/.-]\s*T|MT|MUD[ -]?TERRAIN)(?![A-Z0-9])"),
        ("R/T", r"(?<![A-Z0-9])(?:R\s*[/.-]\s*T|RT|RUGGED[ -]?TERRAIN)(?![A-Z0-9])"),
        ("A/T", r"(?<![A-Z0-9])(?:A\s*[/.-]\s*T|AT|ALL[ -]?TERRAIN|TODO[ -]?TERRENO)(?![A-Z0-9])"),
        ("H/T", r"(?<![A-Z0-9])(?:H\s*[/.-]\s*T|HT|HIGHWAY[ -]?TERRAIN)(?![A-Z0-9])"),
        ("UHP", r"(?<![A-Z0-9])(?:UHP|ULTRA[ -]?HIGH[ -]?PERFORMANCE)(?![A-Z0-9])"),
        ("TOURING", r"(?<![A-Z0-9])(?:TOURING|TURISMO)(?![A-Z0-9])"),
        ("COMMERCIAL", r"(?<![A-Z0-9])(?:COMMERCIAL|COMERCIAL|CARGA)(?![A-Z0-9])"),
        ("HIGHWAY", r"(?<![A-Z0-9])HIGHWAY(?![A-Z0-9])"),
    )
    for canonical, pattern in patterns:
        if re.search(pattern, text):
            return canonical
    return None

def _decimal(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            number = Decimal(str(value))
            return float(number) if number.is_finite() and number >= 0 else None
        except InvalidOperation:
            return None
    text = re.sub(r"[^0-9,.-]", "", str(value).strip())
    if not text:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        tail = text.rsplit(",", 1)[-1]
        text = text.replace(",", ".") if len(tail) <= 2 else text.replace(",", "")
    try:
        number = Decimal(text)
        return float(number) if number.is_finite() and number >= 0 else None
    except InvalidOperation:
        return None

def _stock(value: Any) -> int | None:
    number = _decimal(value)
    if number is None:
        return None
    return max(0, int(number))

def _active(raw: Mapping[str, Any]) -> bool:
    value = _first(raw, ("activo", "active", "habilitado", "enabled", "status", "estado"), True)
    if isinstance(value, str):
        normalized = _ascii(value).strip().lower()
        return normalized not in {
            "0", "false", "no", "inactivo", "inactiva", "inactive", "disabled",
            "deshabilitado", "deshabilitada", "eliminado", "eliminada",
        }
    return bool(value)

def _branch_rows(raw: Mapping[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    candidates: list[Any] = []
    for field in (
        "branches", "sucursales", "inventario_sucursales", "stock_sucursales",
        "branch_stock", "stocks_by_branch",
    ):
        value = raw.get(field)
        if value not in (None, ""):
            if isinstance(value, Mapping):
                for key, child in value.items():
                    if isinstance(child, Mapping):
                        candidates.append({"name": key, **dict(child)})
                    else:
                        candidates.append({"name": key, "stock": child})
            elif isinstance(value, (list, tuple, set)):
                candidates.extend(value)
            else:
                candidates.append(value)

    single_name = _first(raw, ("sucursal_nombre", "branch_name", "sucursal", "branch"))
    if single_name not in (None, ""):
        candidates.append({
            "name": single_name,
            "stock": _first(raw, ("stock_sucursal", "branch_quantity", "branch_stock_value")),
        })

    names: list[str] = []
    rows: list[dict[str, Any]] = []
    by_key: dict[str, int] = {}
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            name = _first(candidate, ("name", "nombre", "branch", "sucursal", "sucursal_nombre"))
            quantity = _stock(_first(candidate, _GLOBAL_STOCK_FIELDS))
            code = _first(candidate, ("code", "codigo", "id"))
        else:
            name, quantity, code = candidate, None, None
        clean_name = _display_text(name)
        if not clean_name:
            continue
        key = clean_name.casefold()
        row = {"name": clean_name, "stock": quantity}
        if code not in (None, ""):
            row["code"] = str(code)
        if key in by_key:
            old = rows[by_key[key]]
            if old.get("stock") is None and quantity is not None:
                old["stock"] = quantity
            continue
        by_key[key] = len(rows)
        names.append(clean_name)
        rows.append(row)
    return names, rows

def _load_and_speed(text: str) -> tuple[str | None, str | None]:
    match = re.search(
        r"(?<!\d)(?P<load>\d{2,3}(?:\s*/\s*\d{2,3})?)\s*(?P<speed>[A-Z])(?=$|[^A-Z0-9])",
        text.upper(),
    )
    if not match:
        return None, None
    return re.sub(r"\s+", "", match.group("load")), match.group("speed")

def _infer_model_from_name(name: str, brand: str) -> str | None:

    candidate = _display_text(name)
    if not candidate:
        return None
    if brand:
        candidate = re.sub(
            rf"^\s*{re.escape(_display_text(brand))}\b[\s:-]*", "", candidate,
            count=1, flags=re.IGNORECASE,
        )
    candidate = re.split(
        r"\b(?:LT|P)?\d{3}\s*[/ .-]\s*\d{2}\s*R?\s*\d{2}(?:\.5)?\b|"
        r"\b\d{1,2}(?:\.\d{1,2})?\s*[xX]\s*\d{1,2}(?:\.\d{1,2})?\s*R\s*\d{2}(?:\.5)?\b|"
        r"\b\d{1,2}(?:\.\d{1,2})?\s*R\s*\d{2}(?:\.5)?\b",
        candidate, maxsplit=1, flags=re.IGNORECASE,
    )[0]
    candidate = re.sub(
        r"(?<![A-Z0-9])(?:A\s*[/.-]\s*T|H\s*[/.-]\s*T|R\s*[/.-]\s*T|M\s*[/.-]\s*T|"
        r"AT|HT|RT|MT)(?![A-Z0-9])", " ", candidate, flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r"\b(?:cauchos?|llantas?|neumaticos?|gomas?|radial|rin|aro)\b", " ",
        candidate, flags=re.IGNORECASE,
    )
    candidate = re.sub(r"\s+", " ", candidate).strip(" -/:,")
    return candidate or None

def normalize_catalog_product(raw: Mapping[str, Any]) -> dict[str, Any]:

    if not isinstance(raw, Mapping):
        raise TypeError("catalog product must be a mapping")
    search_text = _search_text(raw)
    sizes = extract_tire_sizes(search_text)
    primary = sizes[0] if sizes else None
    branches, branch_stock = _branch_rows(raw)
    explicit_stock_value = None
    stock_source = None
    for field in _GLOBAL_STOCK_FIELDS:
        if field in raw and raw.get(field) not in (None, ""):
            explicit_stock_value = raw.get(field)
            stock_source = field
            break
    stock = _stock(explicit_stock_value)
    known_branch_quantities = [row["stock"] for row in branch_stock if row.get("stock") is not None]
    load_index, speed_rating = _load_and_speed(search_text)
    type_resolution = TireTypeResolver().resolve(search_text)
    category = _display_text(_first(raw, ("categoria", "categoria_nombre", "category"), ""))
    is_tire = bool(sizes) or bool(re.search(r"\b(?:CAUCHO|LLANTA|NEUMATICO|GOMA)S?\b", search_text.upper()))
    display_name = _display_text(_first(raw, ("nombre", "name"), "Sin nombre"))
    display_brand = _display_text(_first(raw, ("marca", "marca_nombre", "brand"), ""))
    explicit_model = _display_text(_first(raw, ("modelo_producto", "product_model", "model"), "")) or None
    brand_model = normalize_brand_model(
        display_name,
        brand=display_brand,
        model=explicit_model,
    )
    normalized_brand = brand_model.normalized_brand or display_brand

    public_brand = (
        display_brand
        if display_brand and _clean_text(display_brand).casefold() == _clean_text(normalized_brand).casefold()
        else normalized_brand
    )
    normalized_model = (
        brand_model.normalized_model
        or explicit_model
        or _infer_model_from_name(display_name, display_brand)
    )
    return {
        "id": _first(raw, ("id", "producto_id", "product_id")),
        "code": str(_first(raw, ("codigo", "code", "sku", "id"), "")),
        "name": display_name,

        "display_name": display_name,
        "brand": public_brand,
        "model": normalized_model,
        "original_brand": display_brand or None,
        "original_model": explicit_model,
        "normalized_brand": brand_model.normalized_brand,
        "normalized_model": brand_model.normalized_model,
        "brand_model_confidence": brand_model.confidence,
        "brand_model_status": brand_model.status,
        "brand_model_resolution": brand_model.to_dict(),
        "description": _display_text(_first(raw, ("descripcion", "description", "detalle"), "")) or None,
        "category": category,
        "normalized_size": primary.normalized if primary else None,
        "size": primary.normalized if primary else None,
        "sizes": [size.normalized for size in sizes],
        "rim": primary.rim if primary else None,
        "tire_type": detect_tire_type(search_text) or type_resolution.primary_type,
        "applications": list(type_resolution.applications),
        "load_index": load_index,
        "speed_rating": speed_rating,

        "stock": stock,
        "stock_total": stock,
        "stock_known": stock_source is not None and stock is not None,
        "stock_source": stock_source,
        "inventory_provenance": dict(raw.get("inventory_provenance") or {}),
        "branch_stock_total": sum(known_branch_quantities) if known_branch_quantities else None,
        "price": _decimal(_first(raw, _PRICE_FIELDS)),
        "branches": branches,
        "branch_stock": branch_stock,
        "stock_by_branch": branch_stock,
        "promotion": _first(raw, ("promocion", "promotion")),
        "active": _active(raw),
        "is_tire": is_tire,
        "search_text": search_text,
        "raw": dict(raw),
    }

def normalize_catalog_item(raw: Mapping[str, Any], kind: str | None = None) -> dict[str, Any]:
    return normalize_catalog_product(raw)

def normalize_catalog(
    rows: Iterable[Mapping[str, Any]], *, active_only: bool = True,
) -> list[dict[str, Any]]:
    normalized = [normalize_catalog_product(row) for row in rows]
    return [row for row in normalized if row["active"]] if active_only else normalized

class CatalogNormalizer:

    normalize_product = staticmethod(normalize_catalog_product)
    normalize_item = staticmethod(normalize_catalog_item)
    normalize_many = staticmethod(normalize_catalog)
    detect_tire_type = staticmethod(detect_tire_type)

normalize_product = normalize_catalog_product
normalize_products = normalize_catalog

__all__ = [
    "CatalogNormalizer", "detect_tire_type", "normalize_catalog_product",
    "normalize_catalog_item", "normalize_catalog", "normalize_product",
    "normalize_products",
]
