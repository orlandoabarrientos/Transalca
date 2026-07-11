"""Composicion determinista que mantiene separadas las fuentes de evidencia."""

from __future__ import annotations

from typing import Any, Iterable

from componente_ia.guardrails import DOMAIN_RESPONSE, SENSITIVE_RESPONSE
from componente_ia.lightweight_rag import normalize_text


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default) if value is not None else default


def _primary(intent: Any) -> str:
    return str(_get(intent, "primary", intent) or "clarification")


def _items(result: Any) -> list[Any]:
    if result is None:
        return []
    if isinstance(result, list):
        return result
    values = _get(result, "evidence", None)
    if values is not None:
        return list(values or [])
    if isinstance(result, dict) and "items" in result:
        return list(result.get("items") or [])
    return []


def _data(item: Any) -> dict[str, Any]:
    value = _get(item, "data", {})
    return dict(value or {}) if isinstance(value, dict) else {}


def _kind(item: Any) -> str:
    return str(_get(item, "kind", "") or "")


def _safe_text(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def _money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return ""


class ResponseComposer:
    def compose(self, intent: Any, entities: Any = None, context: Any = None, evidence: Any = None) -> str:
        name = _primary(intent)
        evidence = evidence if isinstance(evidence, dict) else {}
        if name == "out_of_scope":
            return DOMAIN_RESPONSE
        if name == "sensitive_request":
            return SENSITIVE_RESPONSE
        if name == "clarification":
            return DOMAIN_RESPONSE

        if name.startswith("service_"):
            return self._service(name, entities, evidence)
        if name in {"product_inventory", "product_recommendation", "product_price", "tire_inventory"}:
            return self._inventory(name, entities, evidence)
        if name in {
            "tire_size_lookup", "tire_recommendation", "tire_comparison",
            "tire_change_compatibility", "tire_technical_explanation", "truck_tire_advice",
        }:
            return self._tire(name, entities, evidence)
        if name in {
            "promotion", "branch", "business_hours", "payment", "order_status", "upload_receipt",
            "warranty", "credit", "fleet_service", "business_customer",
            "business_info",
        }:
            return self._business(name, evidence)
        if name == "followup":
            if _get(context, "last_products"):
                return "Puedo continuar con los productos anteriores. Indícame si quieres precio, stock o sucursal del primero."
            return "Necesito la referencia anterior o un dato concreto, por ejemplo medida, rin, vehículo, producto o servicio."
        return DOMAIN_RESPONSE

    def _inventory(self, intent: str, entities: Any, evidence: dict[str, Any]) -> str:
        result = evidence.get("inventory") or evidence.get("products")
        items = [item for item in _items(result) if _kind(item) in {"inventory_product", "product"}]
        available = _get(result, "available", evidence.get("catalog_available", False))
        if not available:
            return "No puedo consultar el inventario de Transalca en este momento. No voy a asumir stock ni precio; puedes intentar de nuevo o indicar medida, rin o categoría para dejar la búsqueda lista."
        if not items:
            requested = _get(entities, "requested_tire_size") or (f"rin {_get(entities, 'requested_rim')}" if _get(entities, "requested_rim") else "los filtros indicados")
            return f"Inventario Transalca: no encontré coincidencias verificadas para {requested}. No asumiré una alternativa como compatible; puedo buscar otra medida o categoría si me das el vehículo, año y medida actual."

        lines: list[str] = []
        for item in items[:4]:
            data = _data(item)
            name = _safe_text(data.get("name") or _get(item, "title") or "Producto")
            details = []
            stock_status = data.get("stock_status")
            if stock_status == "available" and data.get("stock") is not None:
                details.append(f"stock {int(data['stock'])}")
            elif stock_status == "out_of_stock":
                details.append("sin stock")
            else:
                details.append("stock por confirmar")
            if data.get("price_available") and data.get("price") is not None:
                details.append(_money(data["price"]))
            else:
                details.append("precio por confirmar")
            if data.get("branch_available") and data.get("branch"):
                details.append(_safe_text(data["branch"], 80))
            match = data.get("match")
            if match == "mismo_rin_no_confirma_fitment":
                details.append("mismo rin; compatibilidad no confirmada")
            lines.append(f"- {name}: {', '.join(details)}")
        prefix = "Inventario Transalca (datos consultados):"
        suffix = "\nLa coincidencia de medida o rin no sustituye validar fitment, carga y velocidad para el vehículo."
        answer = f"{prefix}\n" + "\n".join(lines) + suffix
        if intent == "product_recommendation" and evidence.get("web_sources"):
            references = []
            for source in list(evidence.get("web_sources") or [])[:3]:
                title = _safe_text(_get(source, "title") or "Manual/fuente técnica", 150)
                domain = _safe_text(_get(source, "domain"), 100)
                references.append(f"- {title}" + (f" ({domain})" if domain else ""))
            answer += "\nFuente técnica externa para la especificación del vehículo:\n" + "\n".join(references)
            answer += "\nLa fuente técnica no confirma por sí sola disponibilidad ni compatibilidad del producto del catálogo."
        return answer

    def _service(self, intent: str, entities: Any, evidence: dict[str, Any]) -> str:
        result = evidence.get("services") or evidence.get("service")
        items = _items(result)
        knowledge = [item for item in items if _kind(item) == "service_knowledge"]
        availability = [item for item in items if _kind(item) == "service_availability"]
        if intent == "service_list":
            active = [item for item in availability if _data(item).get("availability") == "active"]
            if not _get(result, "available", False):
                return "No puedo consultar ahora la lista activa de servicios. Prefiero no afirmar disponibilidad hasta verificar el catálogo."
            if not active:
                return "No encontré servicios activos verificables en el catálogo consultado. La disponibilidad debe confirmarse con Transalca."
            names = [_safe_text(_data(item).get("name") or _get(item, "title"), 100) for item in active]
            return "Servicios activos en el catálogo consultado:\n" + "\n".join(f"- {name}" for name in names if name)

        static = knowledge[0] if knowledge else None
        dynamic = availability[0] if availability else None
        static_data = _data(static)
        dynamic_data = _data(dynamic)
        parts: list[str] = []
        query_text = _safe_text(_get(entities, "normalized") or _get(entities, "raw"), 300).lower()
        is_comparison = "diferencia" in query_text or "compar" in query_text
        if intent == "service_explanation" and is_comparison and len(knowledge) >= 2:
            normalized_query = normalize_text(query_text)
            explicitly_named = [
                item for item in knowledge
                if any(
                    normalize_text(alias) in normalized_query
                    for alias in (_data(item).get("names") or [])
                    if normalize_text(alias)
                )
            ]
            if len(explicitly_named) >= 2:
                knowledge = explicitly_named
            comparisons = []
            for item in knowledge[:3]:
                data = _data(item)
                title = _safe_text(_get(item, "title") or "Servicio", 100)
                explanation = _safe_text(data.get("what_it_does") or _get(item, "content"), 330)
                if title and explanation:
                    comparisons.append(f"- {title}: {explanation}")
            if comparisons:
                parts.append("Diferencia entre los servicios:\n" + "\n".join(comparisons))
                parts.append("La alineación corrige la geometría de las ruedas; el balanceo corrige desequilibrios de masa. Uno no sustituye al otro.")
                static = None
        if static:
            title = _safe_text(_get(static, "title") or (_get(entities, "service") or "Servicio"), 100)
            parts.append(f"Referencia general — {title}: {_safe_text(_get(static, 'content'), 420)}")
            if static_data.get("what_it_does"):
                parts.append(f"Cómo funciona: {_safe_text(static_data['what_it_does'], 420)}")
            if intent == "service_recommendation" and static_data.get("recommended_when"):
                recommended = "; ".join(_safe_text(item, 140) for item in static_data["recommended_when"][:3])
                parts.append(f"Cuándo conviene revisarlo: {recommended}.")
            if static_data.get("not_a_substitute_for"):
                parts.append("Esto orienta, pero no sustituye una inspección del vehículo.")
        if dynamic:
            status = dynamic_data.get("availability")
            if status == "active":
                parts.append("Disponibilidad Transalca: aparece activo en el catálogo consultado.")
                if intent == "service_price":
                    parts.append(f"Precio: {_money(dynamic_data['price'])}." if dynamic_data.get("price_available") else "Precio: no está registrado en la fuente consultada; debe confirmarse.")
                if intent == "service_duration":
                    parts.append(f"Duración registrada: {_safe_text(dynamic_data['duration'], 80)}." if dynamic_data.get("duration_available") else "Duración: no está registrada en la fuente consultada; debe confirmarse.")
                if dynamic_data.get("branch"):
                    parts.append(f"Sucursal registrada: {_safe_text(dynamic_data['branch'], 100)}.")
            elif status == "inactive_or_unlisted":
                parts.append("Disponibilidad Transalca: no aparece activo en el catálogo consultado; no puedo confirmar que se ofrezca actualmente.")
            else:
                parts.append("Disponibilidad, precio y duración: no se pudieron verificar en la fuente comercial.")
        elif static:
            parts.append("Disponibilidad, precio y duración: requieren consulta al catálogo activo.")
        if not parts:
            return "No encontré evidencia suficiente para afirmar ese servicio. Indícame el nombre o el síntoma y lo verifico sin asumir disponibilidad, precio ni duración."
        return "\n\n".join(parts)

    def _tire(self, intent: str, entities: Any, evidence: dict[str, Any]) -> str:
        if intent == "tire_change_compatibility":
            comparison = evidence.get("size_comparison") or {}
            difference = _get(comparison, "diameter_difference_percent")
            if difference is None:
                return "No puedo calcular o confirmar el cambio con esos formatos. Necesito ambas medidas completas y luego validar carga, velocidad, rin, despeje y homologación del vehículo."
            current = _get(entities, "current_tire_size")
            requested = _get(entities, "requested_tire_size")
            listed = _get(comparison, "listed_in_local_reference", False)
            reference = "La medida solicitada aparece en la referencia local, pero aún exige validar la versión exacta." if listed else "No tengo evidencia suficiente para tratar la medida solicitada como compatible."
            return (
                f"Comparación geométrica: pasar de {current} a {requested} cambia el diámetro aproximadamente {float(difference):+.2f}%. "
                f"{reference}\nPara confirmarlo: etiqueta/manual, índice de carga y velocidad, ancho de rin, offset y despeje físico."
            )

        technical = evidence.get("technical") or []
        if intent in {"tire_technical_explanation", "tire_comparison"} and technical:
            texts = [_safe_text(_get(item, "content", item), 500) for item in technical]
            return "Referencia técnica general:\n" + "\n".join(text for text in texts if text)

        fitment = evidence.get("fitment") or {}
        sizes = list(_get(fitment, "sizes", []) or [])
        web_sources = list(evidence.get("web_sources") or [])
        parts: list[str] = []
        has_driving_preferences = bool(
            _get(entities, "usage")
            or _get(entities, "tire_type")
            or _get(entities, "budget")
            or _get(entities, "budget_max")
        )
        if technical and (
            intent == "truck_tire_advice"
            or (intent == "tire_recommendation" and has_driving_preferences)
        ):
            general = _safe_text(_get(technical[0], "content", technical[0]), 520)
            if general:
                parts.append("Orientación general (no confirma medida ni fitment): " + general)
        if sizes:
            parts.append("Referencia técnica local (no confirmación final): " + ", ".join(sizes[:6]) + ".")
            parts.append(_safe_text(_get(fitment, "disclaimer"), 380))
        elif web_sources:
            references = []
            for source in web_sources[:3]:
                title = _safe_text(_get(source, "title") or "Fuente técnica", 150)
                domain = _safe_text(_get(source, "domain"), 100)
                references.append(f"- {title}" + (f" ({domain})" if domain else ""))
            parts.append(
                "Fuente externa consultada:\n" + "\n".join(references)
                + "\nLa fuente es una referencia; la medida debe validarse contra año, versión, etiqueta y manual exactos antes de vender o instalar."
            )
        else:
            parts.append("No puedo confirmar una medida exacta todavía con la evidencia disponible.")

        inventory = evidence.get("inventory")
        if inventory is not None:
            parts.append(self._inventory("tire_inventory", entities, {"inventory": inventory}))
        if not sizes:
            missing = []
            if not _get(entities, "year"):
                missing.append("año")
            if not (_get(entities, "requested_rim") or _get(entities, "current_rim")):
                missing.append("rin o medida actual")
            if not _get(entities, "model"):
                missing.insert(0, "modelo")
            parts.append("Para avanzar: dime " + ", ".join(missing or ["versión y medida actual"]) + ".")
        return "\n\n".join(part for part in parts if part)

    def _business(self, intent: str, evidence: dict[str, Any]) -> str:
        result = evidence.get("business")
        items = _items(result)
        verified: list[str] = []
        unavailable_dynamic = False
        for item in items:
            dynamic = bool(_get(item, "dynamic", False))
            is_verified = bool(_get(item, "verified", False))
            data = _data(item)
            if dynamic and not is_verified:
                unavailable_dynamic = True
                continue
            content = _safe_text(_get(item, "content"), 600)
            records = data.get("records") if is_verified else None
            if content:
                verified.append(content)
            if records:
                verified.extend(_safe_text(record, 300) for record in records[:5])
        if verified:
            suffix = "\nLos datos dinámicos se muestran solo cuando la fuente del negocio los confirma." if unavailable_dynamic else ""
            return "\n".join(verified[:6]) + suffix
        return "No puedo confirmar ese dato comercial en este momento. No voy a inventar disponibilidad, precio, horario, política ni estado; debe verificarse en la fuente de Transalca."


_DEFAULT_COMPOSER = ResponseComposer()


def compose(intent: Any, entities: Any = None, context: Any = None, evidence: Any = None) -> str:
    return _DEFAULT_COMPOSER.compose(intent=intent, entities=entities, context=context, evidence=evidence)


__all__ = ["ResponseComposer", "compose"]
