"""Deterministic, non-hallucinatory last-resort responses."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from componente_ia.providers.base_provider import BaseProvider, ProviderRequest, ProviderResult, last_user_message


class FallbackProvider(BaseProvider):
    name = "fallback"

    def complete(
        self,
        messages: Sequence[Mapping[str, Any]] | ProviderRequest,
        tools: Sequence[Mapping[str, Any] | str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        request = messages if isinstance(messages, ProviderRequest) else ProviderRequest(
            message=last_user_message(messages),
            intent=kwargs.get("intent"),
            entities=kwargs.get("entities"),
            evidence=list(kwargs.get("evidence") or []),
        )
        intent = self._primary_intent(request.intent)
        entities = request.entities or {}
        if intent in {"out_of_scope", "sensitive_request"}:
            answer = "Puedo ayudarte con cauchos, productos, servicios, mantenimiento, inventario, pedidos y atención de Transalca."
        elif intent in {"tire_size_lookup", "tire_recommendation", "tire_change_compatibility"}:
            year = self._value(entities, "year")
            model = self._value(entities, "model")
            rim = self._value(entities, "requested_rim", "current_rim", "rim")
            missing = []
            if not model:
                missing.append("modelo")
            if not year:
                missing.append("año")
            if not rim:
                missing.append("rin o medida actual")
            if missing:
                answer = (
                    "No puedo confirmar una medida exacta todavía. Para avanzar, dime "
                    + ", ".join(missing)
                    + ". Con eso puedo buscar referencia técnica e inventario sin asumir compatibilidad."
                )
            else:
                answer = "No pude obtener evidencia técnica suficiente para confirmar compatibilidad. Verifica la etiqueta del vehículo o el manual antes de cambiar la medida."
        elif intent and intent.startswith("service_"):
            answer = "Puedo explicar el servicio de forma general, pero no pude verificar ahora su disponibilidad, precio ni duración. Dime el servicio o síntoma para avanzar."
        elif intent in {"tire_inventory", "product_inventory", "product_price", "promotion"}:
            answer = "No pude verificar el inventario activo en este momento. No voy a afirmar stock, precio ni promoción sin consultar el sistema."
        elif intent in {"branch", "business_hours", "payment", "warranty", "credit", "business_info"}:
            answer = "No pude verificar ese dato comercial vigente. No voy a inventar sucursales, horarios, métodos de pago ni políticas."
        else:
            answer = "Puedo ayudarte con cauchos, productos, servicios, mantenimiento, inventario, pedidos y atención de Transalca. Dime qué necesitas revisar."
        return ProviderResult(
            provider=self.name,
            answer=answer,
            evidence=list(request.evidence),
            confidence=0.55,
            grounded=True,
            status="fallback",
            metadata={"reason": kwargs.get("reason") or "insufficient_evidence"},
        )

    @staticmethod
    def _primary_intent(intent: Any) -> str | None:
        if isinstance(intent, str):
            return intent
        if isinstance(intent, Mapping):
            return intent.get("primary")
        return None

    @staticmethod
    def _value(entities: Any, *names: str) -> Any:
        for name in names:
            if isinstance(entities, Mapping) and entities.get(name) is not None:
                return entities.get(name)
            if getattr(entities, name, None) is not None:
                return getattr(entities, name)
        return None
