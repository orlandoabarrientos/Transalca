"""Technical service knowledge crossed with the active service catalog."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping

from componente_ia.catalog_retriever import CatalogProvider, CatalogSnapshot, decimal_to_float, normalize_catalog_item
from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id, to_jsonable
from componente_ia.lightweight_rag import LightweightRAG, RAGDocument
from componente_ia.resilient_catalog import resilient_catalog_access


DEFAULT_SERVICE_PATH = Path(__file__).with_name("data") / "service_knowledge.json"
_DURATION_FIELDS = ("duracion_estimada", "duration", "duration_minutes", "duracion_minutos")


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _clean(value: Any, limit: int = 500) -> str:
    text = re.sub(r"<[^>]*>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


class ServiceRetriever:
    def __init__(
        self,
        catalog_provider: CatalogProvider | None = None,
        snapshot: CatalogSnapshot | None = None,
        *,
        knowledge_path: str | Path | None = None,
        knowledge: Mapping[str, Any] | None = None,
    ) -> None:
        self.catalog_provider = catalog_provider or (None if snapshot is not None else CatalogProvider())
        self.catalog_access = resilient_catalog_access(self.catalog_provider) if self.catalog_provider is not None else None
        self.snapshot = snapshot
        self.payload = dict(knowledge) if knowledge is not None else self._load(Path(knowledge_path) if knowledge_path else DEFAULT_SERVICE_PATH)
        services = self.payload.get("services") or []
        self.services: dict[str, dict[str, Any]] = {item["id"]: dict(item) for item in services}
        self._validate()
        self.rag = LightweightRAG(self._documents())

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _validate(self) -> None:
        if not self.services:
            raise ValueError("service_knowledge.json must contain services")
        if len(self.services) != len(self.payload.get("services") or []):
            raise ValueError("service knowledge ids must be unique")
        required = {
            "id", "names", "description", "what_it_does", "symptoms", "recommended_when",
            "not_a_substitute_for", "duration_source", "price_source", "safety_notes", "related_services",
        }
        for service in self.services.values():
            missing = required - set(service)
            if missing:
                raise ValueError(f"service {service.get('id')} missing fields: {sorted(missing)}")
            if service["price_source"] != "database":
                raise ValueError(f"service {service['id']} price_source must be database")

    def _documents(self) -> list[RAGDocument]:
        documents = []
        for service in self.services.values():
            content = " ".join((
                service["description"], service["what_it_does"],
                *service["symptoms"], *service["recommended_when"], *service["safety_notes"],
            ))
            documents.append(RAGDocument(
                id=service["id"],
                title=service["names"][0],
                content=content,
                kind="service_knowledge",
                source="service_knowledge.json",
                keywords=tuple(service["names"]) + tuple(service["symptoms"]),
                metadata={"service_id": service["id"]},
            ))
        return documents

    def search(
        self,
        query: str = "",
        *,
        service: str | None = None,
        symptoms: list[str] | tuple[str, ...] | set[str] | None = None,
        entities: Any = None,
        limit: int = 3,
        snapshot: CatalogSnapshot | None = None,
    ) -> RetrievalResult:
        search_text = " ".join(str(item) for item in (query, service or "", *(symptoms or ())) if item)
        if entities is not None:
            service_entity = entities.get("service") if isinstance(entities, Mapping) else getattr(entities, "service", None)
            if service_entity:
                search_text = f"{search_text} {service_entity}"
        selected: list[dict[str, Any]] = []
        if service and service in self.services:
            selected = [self.services[service]]
        else:
            hits = self.rag.search(search_text, limit=limit)
            selected = [self.services[hit.document.id] for hit in hits]

        catalog, load_error = self._load_snapshot(snapshot)
        service_source_available = bool(catalog is not None and not catalog.service_error and not load_error)
        active_services = [self._normalize_active(item) for item in (catalog.services if catalog else [])]
        evidence: list[Evidence] = []
        for item in selected:
            evidence.append(self._knowledge_evidence(item))
            active = self._match_active(item, active_services) if service_source_available else None
            evidence.append(self._availability_evidence(item, active, service_source_available, load_error or (catalog.service_error if catalog else None)))



        if not selected and service_source_available and search_text:
            active_matches = self._search_active(search_text, active_services, limit)
            evidence.extend(self._active_evidence(item, service_id=None) for item in active_matches)

        if not evidence:
            status = "unavailable" if not service_source_available else "empty"
            available = service_source_available
            reason = "service_source_unavailable" if not available else "no_service_match"
        else:
            status = "ok"
            available = True
            reason = None
        return RetrievalResult(
            query=query,
            evidence=evidence,
            status=status,
            available=available,
            partial=bool(selected and not service_source_available),
            reason=reason,
            diagnostics={
                "knowledge_matches": len(selected),
                "active_services": len(active_services),
                "service_source_available": service_source_available,
                "source_error": load_error or (catalog.service_error if catalog else None),
            },
        )

    def explain(self, service_id: str, *, snapshot: CatalogSnapshot | None = None) -> RetrievalResult:
        return self.search(service=service_id, query=service_id, limit=1, snapshot=snapshot)

    def recommend(
        self,
        symptoms: str | list[str] | tuple[str, ...] | set[str],
        *,
        limit: int = 3,
        snapshot: CatalogSnapshot | None = None,
    ) -> RetrievalResult:
        values = [symptoms] if isinstance(symptoms, str) else list(symptoms or [])
        return self.search(" ".join(values), symptoms=values, limit=limit, snapshot=snapshot)

    def list_active(self, *, snapshot: CatalogSnapshot | None = None, limit: int | None = None) -> RetrievalResult:
        catalog, error = self._load_snapshot(snapshot)
        if catalog is None or error or catalog.service_error:
            return RetrievalResult(
                query="active services", status="unavailable", available=False,
                reason="service_source_unavailable",
                diagnostics={"error": error or (catalog.service_error if catalog else None)},
            )
        services = [self._normalize_active(item) for item in catalog.services or []]
        if limit is not None:
            services = services[: max(0, limit)]
        evidence = [self._active_evidence(item, self._static_id_for_active(item)) for item in services]
        return RetrievalResult(
            query="active services", evidence=evidence,
            status="ok" if evidence else "empty", available=True,
            reason=None if evidence else "no_active_services",
            diagnostics={"active_services": len(evidence)},
        )

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
    def _normalize_active(item: Mapping[str, Any]) -> dict[str, Any]:
        if item.get("kind") == "servicio" and "text" in item:
            return dict(item)
        return normalize_catalog_item(dict(item), "servicio")

    def _match_active(self, service: Mapping[str, Any], active_services: list[dict[str, Any]]) -> dict[str, Any] | None:
        aliases = {_normalize(name) for name in service.get("names") or []}
        aliases.add(_normalize(service.get("id")))
        for active in active_services:
            active_text = _normalize(" ".join((
                str(active.get("nombre") or ""), str(active.get("descripcion") or ""), str(active.get("categoria") or "")
            )))
            if any(alias and (alias in active_text or active_text in alias) for alias in aliases):
                return active
        return None

    def _static_id_for_active(self, active: Mapping[str, Any]) -> str | None:
        for service_id, service in self.services.items():
            if self._match_active(service, [dict(active)]):
                return service_id
        return None

    @staticmethod
    def _search_active(query: str, active_services: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        tokens = set(_normalize(query).split())
        scored = []
        for active in active_services:
            text_tokens = set(_normalize(f"{active.get('nombre', '')} {active.get('descripcion', '')}").split())
            score = len(tokens & text_tokens)
            if score:
                scored.append((score, active))
        scored.sort(key=lambda item: (-item[0], str(item[1].get("nombre") or "")))
        return [item for _, item in scored[: max(0, limit)]]

    @staticmethod
    def _knowledge_evidence(service: Mapping[str, Any]) -> Evidence:
        return Evidence(
            id=evidence_id("service-knowledge", service["id"]),
            kind="service_knowledge",
            source="service_knowledge.json",
            title=service["names"][0],
            content=service["description"],
            confidence=0.93,
            verified=True,
            dynamic=False,
            data={
                "service_id": service["id"],
                "names": list(service["names"]),
                "what_it_does": service["what_it_does"],
                "symptoms": list(service["symptoms"]),
                "recommended_when": list(service["recommended_when"]),
                "not_a_substitute_for": list(service["not_a_substitute_for"]),
                "safety_notes": list(service["safety_notes"]),
                "related_services": list(service["related_services"]),
                "price_source": service["price_source"],
                "duration_source": service["duration_source"],
            },
        )

    def _availability_evidence(
        self,
        service: Mapping[str, Any],
        active: Mapping[str, Any] | None,
        source_available: bool,
        error: str | None,
    ) -> Evidence:
        if active is not None:
            return self._active_evidence(dict(active), service["id"])
        if source_available:
            status = "inactive_or_unlisted"
            content = "No se encontró una coincidencia para este servicio en el catálogo activo consultado."
            verified = True
        else:
            status = "unavailable"
            content = "No se pudo verificar la disponibilidad comercial del servicio."
            verified = False
        return Evidence(
            id=evidence_id("service-availability", service["id"], status),
            kind="service_availability",
            source="catalog_database",
            title=service["names"][0],
            content=content,
            confidence=0.98 if source_available else 0.0,
            verified=verified,
            dynamic=True,
            data={
                "service_id": service["id"],
                "availability": status,
                "price": None,
                "price_available": False,
                "duration": None,
                "duration_available": False,
                "source_error": error,
            },
        )

    @staticmethod
    def _active_evidence(active: Mapping[str, Any], service_id: str | None) -> Evidence:
        raw = active.get("raw") if isinstance(active.get("raw"), Mapping) else None
        price_known = bool(raw is not None and any(key in raw and raw.get(key) is not None for key in ("precio", "precio_servicio")))
        if raw is None:
            price_known = active.get("precio") is not None
        duration_field = next((key for key in _DURATION_FIELDS if raw is not None and raw.get(key) is not None), None)
        if raw is None:
            duration_field = next((key for key in _DURATION_FIELDS if active.get(key) is not None), None)
        duration = (raw.get(duration_field) if raw is not None else active.get(duration_field)) if duration_field else None
        branch = active.get("sucursal") or active.get("sucursal_nombre")
        name = _clean(active.get("nombre") or "Servicio activo", 200)
        return Evidence(
            id=evidence_id("service-active", active.get("codigo"), name, branch),
            kind="service_availability",
            source="catalog_database",
            title=name,
            content=f"Servicio recuperado del catálogo activo: {name}.",
            confidence=0.99,
            verified=True,
            dynamic=True,
            data={
                "service_id": service_id,
                "catalog_code": active.get("codigo"),
                "name": name,
                "description": _clean(active.get("descripcion"), 600) or None,
                "availability": "active",
                "price": decimal_to_float(active.get("precio")) if price_known else None,
                "price_available": price_known,
                "duration": to_jsonable(duration) if duration_field else None,
                "duration_available": bool(duration_field),
                "duration_field": duration_field,
                "branch": _clean(branch, 240) or None,
            },
        )


ServiceKnowledgeRetriever = ServiceRetriever
