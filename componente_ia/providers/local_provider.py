"""Deterministic local provider that only returns retrieved evidence."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from componente_ia.business_knowledge import BusinessKnowledge
from componente_ia.catalog_retriever import CatalogProvider
from componente_ia.inventory_retriever import InventoryRetriever
from componente_ia.knowledge_types import Evidence, RetrievalResult
from componente_ia.providers.base_provider import BaseProvider, ProviderRequest, ProviderResult, last_user_message
from componente_ia.service_retriever import ServiceRetriever


_INVENTORY_INTENTS = {
    "tire_inventory", "tire_recommendation", "tire_comparison", "product_inventory",
    "product_recommendation", "product_price",
}
_SERVICE_INTENTS = {
    "service_list", "service_explanation", "service_recommendation", "service_price",
    "service_duration", "service_booking", "fleet_service",
}
_BUSINESS_INTENTS = {
    "branch", "business_hours", "payment", "order_status", "upload_receipt", "warranty",
    "credit", "business_customer", "promotion", "fleet_service", "service_booking",
    "business_info",
}


class LocalProvider(BaseProvider):
    name = "local"

    def __init__(
        self,
        inventory: InventoryRetriever | None = None,
        services: ServiceRetriever | None = None,
        business: BusinessKnowledge | None = None,
    ) -> None:
        if inventory is None and services is None:
            catalog_provider = CatalogProvider()
            inventory = InventoryRetriever(catalog_provider=catalog_provider)
            services = ServiceRetriever(catalog_provider=catalog_provider)
        self.inventory = inventory or InventoryRetriever()
        self.services = services or ServiceRetriever()
        self.business = business or BusinessKnowledge()

    def retrieve(
        self,
        message: str,
        *,
        intent: str | Mapping[str, Any] | None = None,
        entities: Any = None,
        limit: int = 5,
    ) -> RetrievalResult:
        intents = self._intent_names(intent)
        if not intents:
            intents = self._lexical_intents(message)
        results: list[RetrievalResult] = []
        if intents & _INVENTORY_INTENTS:
            results.append(self.inventory.search(message, entities=entities, limit=limit))
        if intents & _SERVICE_INTENTS:
            if "service_list" in intents:
                results.append(self.services.list_active(limit=limit))
            else:
                results.append(self.services.search(message, entities=entities, limit=limit))
        if intents & _BUSINESS_INTENTS:
            results.append(self.business.search(message, limit=min(3, limit)))
        if not results:


            results.append(self.business.search(message, limit=min(3, limit), resolve_dynamic=False))

        evidence: list[Evidence] = []
        seen: set[str] = set()
        for result in results:
            for item in result.evidence:
                if item.id not in seen:
                    seen.add(item.id)
                    evidence.append(item)
        available = any(result.available for result in results)
        status = "ok" if evidence else "unavailable" if not available else "empty"
        return RetrievalResult(
            query=message,
            evidence=evidence,
            status=status,
            available=available,
            partial=any(result.partial for result in results),
            reason=None if evidence else "no_local_evidence",
            diagnostics={"intents": sorted(intents), "retrievers": len(results)},
        )

    def complete(
        self,
        messages: Sequence[Mapping[str, Any]] | ProviderRequest,
        tools: Sequence[Mapping[str, Any] | str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        if isinstance(messages, ProviderRequest):
            request = messages
        else:
            request = ProviderRequest(
                message=last_user_message(messages),
                intent=kwargs.get("intent"),
                entities=kwargs.get("entities"),
                context=kwargs.get("context") or {},
                evidence=list(kwargs.get("evidence") or []),
            )
        result = self.retrieve(request.message, intent=request.intent, entities=request.entities, limit=int(kwargs.get("limit", 5)))
        evidence = list(request.evidence) + [item for item in result.evidence if item.id not in {ev.id for ev in request.evidence}]
        grounded = bool(evidence) and all(item.verified or not item.dynamic for item in evidence)
        return ProviderResult(
            provider=self.name,
            answer="",
            evidence=evidence,
            confidence=max((item.confidence for item in evidence), default=0.0),
            grounded=grounded,
            status=result.status,
            metadata={"retrieval": result.to_dict(), "timeout_ignored": timeout is not None},
        )

    @staticmethod
    def _intent_names(intent: str | Mapping[str, Any] | None) -> set[str]:
        if isinstance(intent, str):
            return {intent}
        if isinstance(intent, Mapping):
            values = {str(intent.get("primary") or "")}
            values.update(str(item) for item in (intent.get("secondary") or []))
            return values - {""}
        return set()

    @staticmethod
    def _lexical_intents(message: str) -> set[str]:
        text = str(message or "").lower()
        intents = set()
        if any(term in text for term in ("caucho", "llanta", "neumatic", " rin", "stock", "producto", "bateria", "filtro", "aceite")):
            intents.add("product_inventory")
        if any(term in text for term in ("servicio", "aline", "balance", "rotacion", "scanner", "vibra", "freno")):
            intents.add("service_explanation")
        if any(term in text for term in ("sucursal", "horario", "pago", "pedido", "garantia", "credito", "delivery", "promocion")):
            intents.add("branch")
        return intents
