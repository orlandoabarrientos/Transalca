"""Grounded inventory retrieval built on the existing catalog adapter."""

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
from componente_ia.resilient_catalog import resilient_catalog_access


@dataclass
class InventoryQuery:
    text: str = ""
    tire_size: str | None = None
    rim: int | None = None
    tire_type: str | None = None
    category: str | None = None
    brand: str | None = None
    branch: str | None = None
    usage: set[str] = field(default_factory=set)
    budget: str | None = None
    max_price: float | None = None
    in_stock: bool | None = None
    sort: str | None = None


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
    """Search active products without inferring missing commercial fields.

    A fixed ``CatalogSnapshot`` is convenient for tests. In production the existing
    ``CatalogProvider`` remains the single database boundary and can be injected.
    """

    def __init__(
        self,
        catalog_provider: CatalogProvider | None = None,
        snapshot: CatalogSnapshot | None = None,
    ) -> None:
        self.catalog_provider = catalog_provider or (None if snapshot is not None else CatalogProvider())
        self.catalog_access = resilient_catalog_access(self.catalog_provider) if self.catalog_provider is not None else None
        self.snapshot = snapshot

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
        for raw in catalog.products or []:
            item = self._normalize_item(raw)
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
                "catalog_products": len(catalog.products or []),
                "matches": len(ranked),
                "constraints": {
                    "size": inventory_query.tire_size,
                    "rim": inventory_query.rim,
                    "category": inventory_query.category,
                    "branch": inventory_query.branch,
                },
            },
        )

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
        for raw in catalog.products or []:
            item = self._normalize_item(raw)
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
        categories = sorted({str(self._normalize_item(item).get("categoria") or "").strip() for item in catalog.products or []} - {""})
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
            return dict(item)
        return normalize_catalog_item(dict(item), "producto")

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
            rim = int(rim) if rim not in (None, "") else None
        except (TypeError, ValueError):
            rim = None
        return InventoryQuery(
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

    @staticmethod
    def _score(item: Mapping[str, Any], request: InventoryQuery) -> tuple[float, str] | None:
        score = 0.0
        compatibility = "textual"
        item_sizes = {str(value).upper() for value in item.get("sizes", []) if value}
        item_bases = {size_base(value) for value in item_sizes}
        if request.tire_size:
            if request.tire_size in item_sizes:
                score += 90
                compatibility = "medida_exacta"
            elif size_base(request.tire_size) in item_bases:
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
        category = _category_key(request.category)
        item_category = _category_key(item.get("categoria"))
        if category:
            category_is_tire = category == "tires"
            if category_is_tire and item.get("is_tire"):
                score += 24
            elif category == item_category or category in item_category or item_category in category:
                score += 20
            else:
                return None
        if request.tire_type:
            if str(item.get("tire_type") or "").upper() == str(request.tire_type).upper():
                score += 20
            elif item.get("tire_type"):
                return None
        if request.brand:
            brand = normalize_text(request.brand, autocorrect=False)
            if brand in normalize_text(item.get("marca") or item.get("text") or "", autocorrect=False):
                score += 16
            else:
                return None
        if request.branch:
            branch = compact_text(request.branch)
            if branch and branch in compact_text(item.get("sucursal") or item.get("sucursal_nombre") or ""):
                score += 18
            else:
                return None
        if request.max_price not in (None, ""):
            price_known = _known_dynamic_field(item, "precio")
            price = decimal_to_float(item.get("precio")) if price_known else None
            if price is None or price > float(request.max_price):
                return None
            score += 10
        normalized_query = normalize_text(request.text, autocorrect=False)
        ignored = {
            "cual", "cuanto", "dame", "dime", "el", "en", "es", "hay", "la", "las", "lo", "los",
            "mas", "me", "precio", "que", "stock", "tiene", "tienen", "un", "una", "y",
        }
        query_tokens = {token for token in re.findall(r"[a-z0-9/.-]+", normalized_query) if len(token) >= 2 and token not in ignored}
        text_tokens = set(str(item.get("text") or "").split())
        for token in query_tokens:
            compact = compact_text(token)
            if token in text_tokens:
                score += 4
            elif len(compact) >= 4 and compact in str(item.get("compact") or ""):
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
                "price": price,
                "price_available": price_known,
                "stock": stock,
                "stock_status": stock_status,
                "branch": (item.get("sucursal") or item.get("sucursal_nombre")) if branch_known else None,
                "branch_available": branch_known,
                "sizes": list(item.get("sizes") or []),
                "rim": item.get("rim"),
                "tire_type": item.get("tire_type"),
                "is_tire": bool(item.get("is_tire")),
                "match": compatibility,
                "score": round(float(score), 3),
            },
        )


CatalogInventoryRetriever = InventoryRetriever
