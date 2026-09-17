from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

from componente_ia.business_knowledge import (
    BusinessDataProvider,
    BusinessKnowledge,
    ModelBusinessDataProvider,
    ResilientBusinessDataProvider,
)
from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id

DEFAULT_BUSINESS_KNOWLEDGE_PATH = Path(__file__).with_name("data") / "business_knowledge.json"

def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("upload_receipt", re.compile(r"\b(?:subir|subo|cargar|cargo|adjuntar|adjunto|enviar|envio|donde)\b.{0,35}\b(?:comprobante|recibo|capture)\b|\bcomprobante\b.{0,30}\bpedido\b")),
    ("order_status", re.compile(r"\b(?:estado|estatus|seguimiento|rastrear|revisar|reviso|consultar|consulto|ver|veo|donde va)\b.{0,35}\b(?:pedido|orden)\b")),
    ("purchase_process", re.compile(r"\b(?:como|donde)\b.{0,25}\b(?:hacer|hago|realizar|realizo|crear|creo)\b.{0,25}\b(?:pedido|compra)\b|\bcomo comprar\b")),
    ("payment_methods", re.compile(r"\b(?:metodo|metodos|forma|formas)\b.{0,18}\bpago\b|\bcomo (?:puedo )?(?:pagar|pago)\b|\b(?:aceptan|reciben|tienen)\b.{0,20}\b(?:transferencia|tarjeta|efectivo|pago movil|zelle|binance|usdt|dolares)\b")),
    ("business_hours", re.compile(r"\b(?:horario|horarios|hora|abren|abre|cierran|cierra)\b")),
    ("branches", re.compile(r"\b(?:sede|sedes|sucursal|sucursales|ubicacion|ubicados|direccion|donde estan)\b")),
    ("promotions", re.compile(r"\b(?:promocion|promociones|oferta|ofertas|descuento|descuentos)\b")),
    ("warranty", re.compile(r"\b(?:garantia|garantias|cobertura|reclamo por defecto)\b")),
    ("credit", re.compile(r"\b(?:credito|financiamiento|financiar|cuotas)\b")),
    ("business_customers", re.compile(r"\b(?:empresa|empresas|corporativo|corporativa|mayorista|al mayor)\b")),
    ("fleet_service", re.compile(r"\b(?:flota|flotas|vehiculos de carga|camion|camiones|gandola|gandolas)\b.{0,35}\b(?:atienden|atencion|servicio|servicios|mantenimiento|convenio|politica)\b|\b(?:atienden|atencion|consulta|servicio|servicios)\b.{0,35}\b(?:flota|flotas|camion|camiones|gandola|gandolas)\b")),
    ("contact", re.compile(r"\b(?:contacto|contactar|telefono|correo|email|whatsapp|comunicar)\b")),
    ("reservations", re.compile(r"\b(?:apartar|separar|reservar)\b.{0,25}\b(?:producto|caucho|repuesto)\b")),
    ("delivery", re.compile(r"\b(?:delivery|envio|envios|despacho|domicilio)\b")),
    ("service_booking", re.compile(r"\b(?:cita|agendar|turno|reservar servicio)\b")),
    ("bring_own_parts", re.compile(r"\b(?:llevar|traer)\b.{0,25}\b(?:mis|propios|propias)\b.{0,20}\b(?:cauchos|repuestos|piezas)\b")),
    ("returns_and_claims", re.compile(r"\b(?:devolucion|devolver|cambiar producto|reclamo)\b")),
    ("business_policies", re.compile(r"\b(?:politica|politicas|terminos|condiciones generales)\b")),
    ("product_categories", re.compile(r"\b(?:que|cuales|tipo de|lista|enumera|muestra|dime|detalla)\b.{0,35}\b(?:productos|categorias(?:\s+de\s+productos)?|repuestos)\b")),
)

class BusinessRetriever:

    def __init__(
        self,
        *,
        knowledge: BusinessKnowledge | None = None,
        data_provider: BusinessDataProvider | None = None,
        resilient: bool = True,
        config_path: str | Path | None = None,
    ) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_BUSINESS_KNOWLEDGE_PATH
        self._processes = self._load_processes(self.config_path)
        if knowledge is not None:
            self.knowledge = knowledge
            return
        provider = data_provider or ModelBusinessDataProvider(config_path=self.config_path)
        if resilient and not isinstance(provider, ResilientBusinessDataProvider):
            provider = ResilientBusinessDataProvider(provider)
        self.knowledge = BusinessKnowledge(data_provider=provider)

    @staticmethod
    def topics_for(query: str) -> list[str]:
        text = _normalize(query)
        topics: list[str] = []
        for topic, pattern in _TOPIC_PATTERNS:
            if pattern.search(text):
                topics.append(topic)
        return topics

    @staticmethod
    def _load_processes(path: Path) -> dict[str, Mapping[str, Any]]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError, TypeError):
            return {}
        processes = payload.get("curated_processes") if isinstance(payload, Mapping) else None
        if not isinstance(processes, Mapping):
            return {}
        return {
            str(key): value
            for key, value in processes.items()
            if isinstance(value, Mapping) and value.get("status") == "approved"
        }

    def resolve(self, topic: str, *, resolve_dynamic: bool = True) -> RetrievalResult:
        result = self.knowledge.get(topic, resolve_dynamic=resolve_dynamic)

        process = self._processes.get(topic)
        guidance = str(process.get("guidance") or "").strip() if process else ""
        if guidance and not any(not item.dynamic and item.verified for item in result.evidence):
            result.evidence.append(Evidence(
                id=evidence_id("business-process", topic, guidance),
                kind="business_process",
                source="business_knowledge.json",
                title=topic.replace("_", " "),
                content=guidance,
                confidence=0.99,
                verified=True,
                dynamic=False,
                data={"topic": topic, "claim_type": "process_guidance"},
            ))
            result.available = True
            result.status = "ok"
            result.partial = any(item.dynamic and not item.verified for item in result.evidence)
            result.reason = None
        return result

    get = resolve

    def search(
        self,
        query: str,
        *,
        limit: int = 4,
        resolve_dynamic: bool = True,
    ) -> RetrievalResult:
        topics = self.topics_for(query)[: max(1, int(limit))]
        if not topics:

            return self.knowledge.search(query, limit=1, resolve_dynamic=resolve_dynamic)

        evidence: list[Evidence] = []
        reasons: list[str] = []
        for topic in topics:
            current = self.resolve(topic, resolve_dynamic=resolve_dynamic)
            evidence.extend(current.evidence)
            if current.reason:
                reasons.append(current.reason)

        verified = [item for item in evidence if item.verified or not item.dynamic]
        unresolved = [item for item in evidence if item.dynamic and not item.verified]
        return RetrievalResult(
            query=query,
            evidence=evidence,
            status="ok" if verified else "unavailable" if evidence else "empty",
            available=bool(verified),
            partial=bool(verified and unresolved),
            reason=None if verified else reasons[0] if reasons else "business_data_unavailable",
            diagnostics={
                "topics": topics,
                "verified_topics": [
                    str(item.data.get("topic")) for item in verified if item.data.get("topic")
                ],
                "unresolved_topics": [
                    str(item.data.get("topic")) for item in unresolved if item.data.get("topic")
                ],
            },
        )

    @staticmethod
    def verified_records(
        result: RetrievalResult,
        *,
        topic: str | None = None,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for item in result.evidence:
            if item.dynamic and not item.verified:
                continue
            if topic and item.data.get("topic") != topic:
                continue
            values = item.data.get("records")
            if not isinstance(values, Iterable) or isinstance(values, (str, bytes, Mapping)):
                continue
            records.extend(dict(value) for value in values if isinstance(value, Mapping))
        return records

    def payment_methods(self) -> RetrievalResult:
        return self.resolve("payment_methods")

    def product_categories(self) -> RetrievalResult:
        return self.resolve("product_categories")

    def branches(self) -> RetrievalResult:
        return self.resolve("branches")

    def business_hours(self) -> RetrievalResult:
        return self.resolve("business_hours")

    def warranty(self) -> RetrievalResult:
        return self.resolve("warranty")

    def order_status_guidance(self) -> RetrievalResult:
        return self.resolve("order_status")

    def upload_receipt_guidance(self) -> RetrievalResult:
        return self.resolve("upload_receipt")

    def credit(self) -> RetrievalResult:
        return self.resolve("credit")

    def business_customers(self) -> RetrievalResult:
        return self.resolve("business_customers")

    def fleet_service(self) -> RetrievalResult:
        return self.resolve("fleet_service")

__all__ = ["BusinessRetriever"]
