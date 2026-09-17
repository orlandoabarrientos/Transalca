from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from componente_ia.automotive_entities import compact_text, normalize_text
from componente_ia.entity_extractor import extract as extract_entities
from componente_ia.catalog_retriever import (
    CatalogProvider,
    CatalogSnapshot,
    decimal_to_float,
    int_value,
    normalize_catalog_item,
    size_base,
)
from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id
from componente_ia.inventory_index import InventoryIndex
from componente_ia.resilient_catalog import resilient_catalog_access

@dataclass
class InventoryQuery:
    text: str = ""
    tire_size: str | None = None
    rim: int | float | None = None
    tire_type: str | None = None
    category: str | None = None
    brand: str | None = None
    branch: str | None = None
    usage: set[str] = field(default_factory=set)
    budget: str | None = None
    max_price: float | None = None
    in_stock: bool | None = None
    sort: str | None = None

    normalized_text: str = ""
    query_tokens: frozenset[str] = field(default_factory=frozenset)
    compact_query_tokens: tuple[tuple[str, str], ...] = ()
    tire_size_base: str | None = None
    tire_type_key: str = ""
    category_key: str = ""
    brand_key: str = ""
    branch_key: str = ""

_IGNORED_QUERY_TOKENS = frozenset({
    "cual", "cuanto", "dame", "dime", "el", "en", "es", "hay", "la",
    "las", "lo", "los", "mas", "me", "precio", "que", "stock", "tiene",
    "tienen", "un", "una", "y",
})

def _entity_value(entities: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(entities, Mapping) and entities.get(name) is not None:
            return entities.get(name)
        if entities is not None and getattr(entities, name, None) is not None:
            return getattr(entities, name)
    return default

def _tire_size_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        value = value.get("normalized") or value.get("value")
    else:
        value = getattr(value, "normalized", value)
    return str(value).upper() if value else None

def _known_dynamic_field(item: Mapping[str, Any], field: str) -> bool:
    raw = item.get("raw")
    if isinstance(raw, Mapping):
        candidates = {
            "precio": ("precio", "price"),
            "stock": ("stock", "existencia", "quantity"),
            "sucursal": ("sucursal", "sucursal_nombre", "branch"),
        }.get(field, (field,))
        return any(key in raw and raw.get(key) is not None for key in candidates)
    return field in item and item.get(field) is not None

def _category_key(value: Any) -> str:
    normalized = normalize_text(value or "", autocorrect=False)
    aliases = {
        "tire": "tires", "tires": "tires", "caucho": "tires", "cauchos": "tires",
        "llanta": "tires", "llantas": "tires", "neumatico": "tires", "neumaticos": "tires",
        "battery": "batteries", "batteries": "batteries", "bateria": "batteries", "baterias": "batteries",
        "oil": "oil", "oils": "oil", "aceite": "oil", "aceites": "oil", "lubricante": "oil", "lubricantes": "oil",
        "filter": "filters", "filters": "filters", "filtro": "filters", "filtros": "filters",
        "brake": "brakes", "brakes": "brakes", "freno": "brakes", "frenos": "brakes",
        "part": "parts", "parts": "parts", "repuesto": "parts", "repuestos": "parts", "pieza": "parts", "piezas": "parts",
    }
    return aliases.get(normalized, normalized)

class InventoryRetriever:

    def __init__(
        self,
        catalog_provider: CatalogProvider | None = None,
        snapshot: CatalogSnapshot | None = None,
    ) -> None:
        self.catalog_provider = catalog_provider or (None if snapshot is not None else CatalogProvider())
        self.catalog_access = resilient_catalog_access(self.catalog_provider) if self.catalog_provider is not None else None
        self.snapshot = snapshot
        self._index_key: tuple[int, float, int] | None = None
        self._index: InventoryIndex | None = None

    def search(
        self,
        query: str = "",
        *,
        entities: Any = None,
        filters: Mapping[str, Any] | InventoryQuery | None = None,
        limit: int = 6,
        include_out_of_stock: bool = True,
        snapshot: CatalogSnapshot | None = None,
    ) -> RetrievalResult:
        inventory_query = self._build_query(query, entities, filters)
        catalog, error = self._load_snapshot(snapshot)
        if error or catalog is None:
            return RetrievalResult(
                query=query,
                status="unavailable",
                available=False,
                reason="inventory_source_unavailable",
                diagnostics={"error": error or "CatalogProviderError"},
            )
        if catalog.product_error:
            return RetrievalResult(
                query=query,
                status="unavailable",
                available=False,
                reason="inventory_source_unavailable",
                diagnostics={"error": catalog.product_error},
            )

        ranked: list[tuple[float, dict[str, Any], str]] = []
        index = self._catalog_index(catalog)
        candidates = index.candidates(
            tire_size=inventory_query.tire_size,
            rim=inventory_query.rim,
            tire_type=inventory_query.tire_type,
        )
        for item in candidates:
            match = self._score(item, inventory_query)
            if match is None:
                continue
            score, compatibility = match
            stock_known = _known_dynamic_field(item, "stock")
            stock = int_value(item.get("stock")) if stock_known else None
            if inventory_query.in_stock is True and (stock is None or stock <= 0):
                continue
            if inventory_query.in_stock is False and stock is not None and stock > 0:
                continue
            if not include_out_of_stock and (stock is None or stock <= 0):
                continue
            ranked.append((score, item, compatibility))

        ranked = self._sort(ranked, inventory_query)
        evidence = [self._evidence(item, score, compatibility) for score, item, compatibility in ranked[: max(0, limit)]]
        return RetrievalResult(
            query=query,
            evidence=evidence,
            status="ok" if evidence else "empty",
            available=True,
            reason=None if evidence else "no_inventory_match",
            diagnostics={
                "catalog_products": len(index.rows),
                "index_candidates": len(candidates),
                "matches": len(ranked),
                "constraints": {
                    "size": inventory_query.tire_size,
                    "rim": inventory_query.rim,
                    "category": inventory_query.category,
                    "branch": inventory_query.branch,
                },
            },
        )

    def _catalog_index(self, catalog: CatalogSnapshot) -> InventoryIndex:
        key = (id(catalog.products), float(catalog.loaded_at or 0.0), len(catalog.products or []))
        if self._index is None or self._index_key != key:
            self._index = InventoryIndex.build(catalog.products or [], self._normalize_item)
            self._index_key = key
        return self._index

    def search_tires(
        self,
        query: str = "",
        *,
        entities: Any = None,
        size: str | None = None,
        rim: int | None = None,
        tire_type: str | None = None,
        limit: int = 6,
        include_out_of_stock: bool = True,
        snapshot: CatalogSnapshot | None = None,
    ) -> RetrievalResult:
        filters = {
            "category": "cauchos",
            "tire_size": size,
            "rim": rim,
            "tire_type": tire_type,
        }
        return self.search(
            query,
            entities=entities,
            filters={key: value for key, value in filters.items() if value is not None},
            limit=limit,
            include_out_of_stock=include_out_of_stock,
            snapshot=snapshot,
        )

    def get_by_code(self, code: str, *, snapshot: CatalogSnapshot | None = None) -> RetrievalResult:
        catalog, error = self._load_snapshot(snapshot)
        if error or catalog is None or catalog.product_error:
            return RetrievalResult(
                query=str(code or ""), status="unavailable", available=False,
                reason="inventory_source_unavailable",
                diagnostics={"error": error or (catalog.product_error if catalog else None)},
            )
        requested = str(code or "").strip().lower()
        evidence = []
        for item in self._catalog_index(catalog).rows:
            if str(item.get("codigo") or "").strip().lower() == requested:
                evidence.append(self._evidence(item, 100.0, "codigo_exacto"))
                break
        return RetrievalResult(
            query=str(code or ""), evidence=evidence,
            status="ok" if evidence else "empty", available=True,
            reason=None if evidence else "product_code_not_found",
        )

    def list_categories(self, *, snapshot: CatalogSnapshot | None = None) -> RetrievalResult:
        catalog, error = self._load_snapshot(snapshot)
        if error or catalog is None or catalog.product_error:
            return RetrievalResult(
                query="categories", status="unavailable", available=False,
                reason="inventory_source_unavailable",
                diagnostics={"error": error or (catalog.product_error if catalog else None)},
            )
        categories = sorted({str(item.get("categoria") or "").strip() for item in self._catalog_index(catalog).rows} - {""})
        item = Evidence(
            id=evidence_id("inventory-categories", *categories),
            kind="inventory_categories",
            source="catalog_database",
            title="Categorías activas",
            content="Categorías recuperadas del catálogo activo.",
            confidence=0.99,
            verified=True,
            dynamic=True,
            data={"categories": categories},
        )
        return RetrievalResult(query="categories", evidence=[item], status="ok", available=True)

    def _load_snapshot(self, override: CatalogSnapshot | None) -> tuple[CatalogSnapshot | None, str | None]:
        if override is not None:
            return override, None
        if self.snapshot is not None:
            return self.snapshot, None
        if self.catalog_access is None:
            return None, "CatalogProviderUnavailable"
        try:
            return self.catalog_access.load(), None
        except Exception as exc:
            return None, exc.__class__.__name__

    @staticmethod
    def _normalize_item(item: Mapping[str, Any]) -> dict[str, Any]:
        if item.get("kind") == "producto" and "text" in item:
            normalized = dict(item)
        else:
            normalized = normalize_catalog_item(dict(item), "producto")

        sizes = frozenset(
            str(value).upper() for value in normalized.get("sizes", ()) if value
        )
        normalized["_inventory_sizes_upper"] = sizes
        normalized["_inventory_size_bases"] = frozenset(size_base(value) for value in sizes)
        normalized["_inventory_category_key"] = _category_key(normalized.get("categoria"))
        normalized["_inventory_tire_type_key"] = str(
            normalized.get("tire_type") or ""
        ).upper()
        normalized["_inventory_brand_text"] = normalize_text(
            normalized.get("marca") or normalized.get("text") or "",
            autocorrect=False,
        )
        normalized["_inventory_branch_key"] = compact_text(
            normalized.get("sucursal") or normalized.get("sucursal_nombre") or ""
        )
        normalized["_inventory_text_tokens"] = frozenset(
            str(normalized.get("text") or "").split()
        )
        normalized["_inventory_compact_text"] = str(normalized.get("compact") or "")
        return normalized

    def _build_query(
        self,
        query: str,
        entities: Any,
        filters: Mapping[str, Any] | InventoryQuery | None,
    ) -> InventoryQuery:
        if entities is None and query:
            entities = extract_entities(query)
        values: dict[str, Any] = {}
        if isinstance(filters, InventoryQuery):
            values.update(vars(filters))
        elif filters:
            values.update(filters)
        size = values.get("tire_size") or values.get("requested_tire_size") or _entity_value(
            entities, "requested_tire_size", "current_tire_size", "tire_size"
        )
        rim = values.get("rim") or values.get("requested_rim") or _entity_value(
            entities, "requested_rim", "current_rim", "rim"
        )
        category = values.get("category") or values.get("product_category") or _entity_value(entities, "product_category")
        usage = values.get("usage") or values.get("uses") or _entity_value(entities, "usage", "uses", default=set())
        try:
            if rim not in (None, ""):
                numeric_rim = float(rim)
                rim = int(numeric_rim) if numeric_rim.is_integer() else numeric_rim
            else:
                rim = None
        except (TypeError, ValueError):
            rim = None
        request = InventoryQuery(
            text=str(values.get("text") or query or ""),
            tire_size=_tire_size_value(size),
            rim=rim,
            tire_type=values.get("tire_type") or _entity_value(entities, "tire_type"),
            category=category,
            brand=values.get("brand") or values.get("brand_preference") or _entity_value(entities, "brand", "brand_preference"),
            branch=values.get("branch") or _entity_value(entities, "branch"),
            usage=set(usage or []),
            budget=values.get("budget") or _entity_value(entities, "budget"),
            max_price=values.get("max_price") or values.get("budget_max") or _entity_value(entities, "max_price", "budget_max"),
            in_stock=values.get("in_stock"),
            sort=values.get("sort"),
        )
        request.normalized_text = normalize_text(request.text, autocorrect=False)
        request.query_tokens = frozenset(
            token
            for token in re.findall(r"[a-z0-9/.-]+", request.normalized_text)
            if len(token) >= 2 and token not in _IGNORED_QUERY_TOKENS
        )
        request.compact_query_tokens = tuple(
            (token, compact_text(token)) for token in sorted(request.query_tokens)
        )
        request.tire_size_base = size_base(request.tire_size) if request.tire_size else None
        request.tire_type_key = str(request.tire_type or "").upper()
        request.category_key = _category_key(request.category)
        request.brand_key = normalize_text(request.brand or "", autocorrect=False)
        request.branch_key = compact_text(request.branch or "")
        return request

    @staticmethod
    def _score(item: Mapping[str, Any], request: InventoryQuery) -> tuple[float, str] | None:
        score = 0.0
        compatibility = "textual"
        item_sizes = item.get("_inventory_sizes_upper")
        if not isinstance(item_sizes, (set, frozenset)):
            item_sizes = frozenset(
                str(value).upper() for value in item.get("sizes", ()) if value
            )
        item_bases = item.get("_inventory_size_bases")
        if not isinstance(item_bases, (set, frozenset)):
            item_bases = frozenset(size_base(value) for value in item_sizes)
        if request.tire_size:
            if request.tire_size in item_sizes:
                score += 90
                compatibility = "medida_exacta"
            elif request.tire_size_base in item_bases:
                score += 82
                compatibility = "medida_equivalente_sin_prefijo"
            else:
                return None
        if request.rim is not None:
            if item.get("rim") == request.rim:
                score += 36
                if compatibility == "textual":
                    compatibility = "mismo_rin_no_confirma_fitment"
            else:
                return None
        category = request.category_key
        item_category = str(
            item.get("_inventory_category_key") or _category_key(item.get("categoria"))
        )
        if category:
            category_is_tire = category == "tires"
            if category_is_tire and item.get("is_tire"):
                score += 24
            elif category == item_category or category in item_category or item_category in category:
                score += 20
            else:
                return None
        if request.tire_type:
            item_tire_type = str(
                item.get("_inventory_tire_type_key")
                or str(item.get("tire_type") or "").upper()
            )
            if item_tire_type == request.tire_type_key:
                score += 20
            elif item.get("tire_type"):
                return None
        if request.brand:
            item_brand = str(item.get("_inventory_brand_text") or "")
            if not item_brand:
                item_brand = normalize_text(
                    item.get("marca") or item.get("text") or "", autocorrect=False,
                )
            if request.brand_key in item_brand:
                score += 16
            else:
                return None
        if request.branch:
            item_branch = str(item.get("_inventory_branch_key") or "")
            if not item_branch:
                item_branch = compact_text(
                    item.get("sucursal") or item.get("sucursal_nombre") or ""
                )
            if request.branch_key and request.branch_key in item_branch:
                score += 18
            else:
                return None
        if request.max_price not in (None, ""):
            price_known = _known_dynamic_field(item, "precio")
            price = decimal_to_float(item.get("precio")) if price_known else None
            if price is None or price > float(request.max_price):
                return None
            score += 10
        query_tokens = request.query_tokens
        text_tokens = item.get("_inventory_text_tokens")
        if not isinstance(text_tokens, (set, frozenset)):
            text_tokens = frozenset(str(item.get("text") or "").split())
        compact_text_value = str(
            item.get("_inventory_compact_text") or item.get("compact") or ""
        )
        for token, compact in request.compact_query_tokens:
            if token in text_tokens:
                score += 4
            elif len(compact) >= 4 and compact in compact_text_value:
                score += 2
        if not any((request.tire_size, request.rim, request.category, request.tire_type, request.brand, request.branch)) and query_tokens and score <= 0:
            return None
        stock_known = _known_dynamic_field(item, "stock")
        stock = int_value(item.get("stock")) if stock_known else None
        if stock is not None and stock > 0:
            score += 6
        if request.usage:
            tire_type = str(item.get("tire_type") or "").upper()
            if tire_type == "A/T" and request.usage & {"tierra", "dirt", "grava", "gravel", "lluvia", "rain"}:
                score += 8
            if tire_type == "H/T" and request.usage & {"autopista", "highway", "ciudad", "city", "lluvia", "rain", "silencioso", "quiet"}:
                score += 8
            if tire_type == "M/T" and request.usage & {"barro", "mud"}:
                score += 9
        return score, compatibility

    @staticmethod
    def _sort(ranked: list[tuple[float, dict[str, Any], str]], request: InventoryQuery) -> list[tuple[float, dict[str, Any], str]]:
        sort = request.sort
        if not sort and request.budget in {"economy", "economico", "bajo", "barato"}:
            sort = "price_asc"
        if sort == "price_asc":
            key = lambda row: (
                0 if _known_dynamic_field(row[1], "precio") else 1,
                decimal_to_float(row[1].get("precio"), float("inf")),
                -row[0],
            )
        elif sort == "stock_desc":
            key = lambda row: (
                0 if _known_dynamic_field(row[1], "stock") else 1,
                -int_value(row[1].get("stock")) if _known_dynamic_field(row[1], "stock") else 0,
                -row[0],
            )
        else:
            key = lambda row: (
                -row[0],
                0 if _known_dynamic_field(row[1], "stock") and int_value(row[1].get("stock")) > 0 else 1,
                str(row[1].get("nombre") or ""),
            )
        return sorted(ranked, key=key)

    @staticmethod
    def _evidence(item: Mapping[str, Any], score: float, compatibility: str) -> Evidence:
        price_known = _known_dynamic_field(item, "precio")
        stock_known = _known_dynamic_field(item, "stock")
        branch_known = _known_dynamic_field(item, "sucursal")
        price = decimal_to_float(item.get("precio")) if price_known else None
        stock = int_value(item.get("stock")) if stock_known else None
        stock_status = "unknown" if stock is None else "available" if stock > 0 else "out_of_stock"
        code = item.get("codigo")
        name = str(item.get("nombre") or "Producto sin nombre")
        return Evidence(
            id=evidence_id("inventory", code, name, item.get("sucursal")),
            kind="inventory_product",
            source="catalog_database",
            title=name,
            content=f"Producto recuperado del catálogo activo: {name}.",
            confidence=min(0.99, 0.65 + max(0.0, score) / 180.0),
            verified=True,
            dynamic=True,
            data={
                "code": code,
                "name": name,
                "description": item.get("descripcion") or None,
                "category": item.get("categoria") or None,
                "brand": item.get("marca") or None,
                "model": item.get("modelo") or None,
                "display_name": item.get("display_name") or name,
                "original_brand": item.get("marca_original") or None,
                "normalized_brand": item.get("marca_normalizada") or item.get("marca") or None,
                "normalized_model": item.get("modelo_normalizado") or item.get("modelo") or None,
                "brand_model_confidence": item.get("brand_model_confidence"),
                "brand_model_status": item.get("brand_model_status"),
                "price": price,
                "price_available": price_known,
                "stock": stock,
                "stock_status": stock_status,
                "inventory_provenance": dict(item.get("inventory_provenance") or {}),
                "branch": (item.get("sucursal") or item.get("sucursal_nombre")) if branch_known else None,
                "branch_available": branch_known,
                "sizes": list(item.get("sizes") or []),
                "rim": item.get("rim"),
                "tire_type": item.get("tire_type"),
                "applications": list(item.get("applications") or []),
                "is_tire": bool(item.get("is_tire")),
                "match": compatibility,
                "score": round(float(score), 3),
                "active": bool(item.get("active", True)),
            },
        )

CatalogInventoryRetriever = InventoryRetriever
