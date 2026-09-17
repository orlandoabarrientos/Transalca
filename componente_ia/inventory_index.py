from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from componente_ia.automotive_entities import normalize_text
from componente_ia.catalog_retriever import size_base

@dataclass(frozen=True)
class IndexedCatalog:
    rows: tuple[dict[str, Any], ...]
    by_size: Mapping[str, frozenset[int]]
    by_rim: Mapping[float, frozenset[int]]
    by_type: Mapping[str, frozenset[int]]
    by_category: Mapping[str, frozenset[int]]

    @classmethod
    def build(
        cls,
        products: Iterable[Mapping[str, Any]],
        normalizer: Callable[[Mapping[str, Any]], dict[str, Any]],
    ) -> "IndexedCatalog":
        rows: list[dict[str, Any]] = []
        sizes: dict[str, set[int]] = defaultdict(set)
        rims: dict[float, set[int]] = defaultdict(set)
        types: dict[str, set[int]] = defaultdict(set)
        categories: dict[str, set[int]] = defaultdict(set)
        for raw in products:
            item = normalizer(raw)
            if not bool(item.get("active", True)):
                continue
            index = len(rows)
            rows.append(item)
            for size in item.get("sizes") or []:
                canonical = str(size).upper()
                sizes[canonical].add(index)
                sizes[size_base(canonical)].add(index)
            rim = item.get("rim")
            if isinstance(rim, (int, float)):
                rims[float(rim)].add(index)
            tire_type = str(item.get("tire_type") or "").upper()
            if tire_type:
                types[tire_type].add(index)
            category = normalize_text(item.get("categoria") or "", autocorrect=False)
            if category:
                categories[category].add(index)
        freeze = lambda values: {key: frozenset(item) for key, item in values.items()}
        return cls(tuple(rows), freeze(sizes), freeze(rims), freeze(types), freeze(categories))

    def candidates(
        self,
        *,
        tire_size: str | None = None,
        rim: int | float | None = None,
        tire_type: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        groups: list[frozenset[int]] = []
        if tire_size:
            canonical = str(tire_size).upper()
            groups.append(self.by_size.get(canonical) or self.by_size.get(size_base(canonical), frozenset()))
        if rim is not None:
            groups.append(self.by_rim.get(float(rim), frozenset()))
        if tire_type:
            groups.append(self.by_type.get(str(tire_type).upper(), frozenset()))
        if not groups:
            return self.rows
        selected = set(groups[0])
        for group in groups[1:]:
            selected.intersection_update(group)
        return tuple(self.rows[index] for index in sorted(selected))

InventoryIndex = IndexedCatalog

__all__ = ["IndexedCatalog", "InventoryIndex"]
