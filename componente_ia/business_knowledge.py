from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id, to_jsonable
from componente_ia.lightweight_rag import LightweightRAG, RAGDocument
from componente_ia.metrics import assistant_metrics

logger = logging.getLogger(__name__)
DEFAULT_FAQ_PATH = Path(__file__).with_name("data") / "business_faq.json"
DEFAULT_BUSINESS_CONFIG_PATH = Path(__file__).with_name("data") / "business_knowledge.json"

_UNSAFE_PUBLIC_DATA_RE = re.compile(
    r"(?i)(?:<\s*script|\b(?:select|union|sleep|benchmark|drop|insert|delete|update|"
    r"load_file|outfile|information_schema|password|token|cookie)\b|\.\.[\\/])"
)
_TEST_DATA_RE = re.compile(r"(?i)\b(?:test|prueba|dummy|fixture)\b")
_PAYMENT_TERMS = {
    "binance", "credito", "debito", "efectivo", "pago", "movil", "tarjeta",
    "transferencia", "zelle", "cheque", "paypal", "stripe", "punto", "divisa",
    "dolar", "dolares", "bolivar", "bolivares", "metodo", "contado",
}

def _public_text(value: Any, *, limit: int = 500) -> str:
    text = re.sub(r"<[^>]*>", " ", str(value or ""))
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]

def _safe_public_name(value: Any, *, semantic_terms: set[str] | None = None) -> str:

    text = _public_text(value, limit=200)
    if not text or _UNSAFE_PUBLIC_DATA_RE.search(text):
        return ""
    if not re.fullmatch(r"[\wÀ-ÿ .,+&'()/:-]{2,200}", text, flags=re.UNICODE):
        return ""
    folded = unicodedata.normalize("NFKD", text.casefold())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    words = set(re.findall(r"[a-z0-9]+", folded.replace("_", " ")))
    if semantic_terms is not None and not (words & semantic_terms):
        return ""
    return text

def _safe_public_description(value: Any, *, limit: int = 500) -> str:
    text = _public_text(value, limit=limit)
    if _UNSAFE_PUBLIC_DATA_RE.search(text):
        return ""
    return text

def _public_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on", "si", "sí"}
    return bool(value)

def _public_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None

@dataclass
class DynamicKnowledgeResult:
    source: str
    records: list[dict[str, Any]] = field(default_factory=list)
    available: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable({
            "source": self.source,
            "records": self.records,
            "available": self.available,
            "error": self.error,
        })

class BusinessDataProvider(Protocol):
    def resolve(self, source: str, topic: str) -> DynamicKnowledgeResult:
        pass

class UnavailableBusinessDataProvider:
    def resolve(self, source: str, topic: str) -> DynamicKnowledgeResult:
        return DynamicKnowledgeResult(source=source, available=False, error="provider_unavailable")

class ModelBusinessDataProvider:

    def __init__(
        self,
        model_factories: Mapping[str, Callable[[], Any]] | None = None,
        *,
        config_path: str | Path | None = None,
    ) -> None:
        self._strict_public_quality = not bool(model_factories)
        self._model_factories = dict(model_factories or {})
        self.config_path = Path(config_path) if config_path else DEFAULT_BUSINESS_CONFIG_PATH
        self._public_config = self._load_public_config(self.config_path)

    def resolve(self, source: str, topic: str) -> DynamicKnowledgeResult:
        try:
            if source == "catalog_database" and topic == "product_categories":
                records = self._execute("categories", self._category_factory)
                return DynamicKnowledgeResult(source, self._valid_records(records, self._category), True)
            if source == "branch_database":
                records = self._execute("branches", self._branch_factory)
                branches = self._valid_records(records, self._branch)
                if self._strict_public_quality:
                    branches = [item for item in branches if self._production_public_record(item)]
                return DynamicKnowledgeResult(source, branches, True)
            if source == "promotion_database":
                records = self._execute("promotions", self._promotion_factory)
                promotions = self._valid_records(records, self._promotion)
                if self._strict_public_quality:
                    promotions = [item for item in promotions if self._production_public_record(item, min_name=4)]
                return DynamicKnowledgeResult(source, promotions, True)
            if source == "business_config" and topic == "payment_methods":
                records = self._execute("payment_methods", self._payment_factory)
                methods = self._public_payment_records(records)
                return DynamicKnowledgeResult(source, methods, True)
            if source == "business_config" and topic == "business_hours":
                try:
                    records = self._execute("branches", self._branch_factory)
                    hours = self._valid_records(records, self._branch_hours)
                except Exception:
                    hours = []
                if hours:
                    return DynamicKnowledgeResult(source, hours, True)
                return self._configured_topic(source, topic, fallback_error="public_hours_not_configured")
            if source == "business_config" and topic == "contact":
                try:
                    records = self._execute("branches", self._branch_factory)
                    contacts = [item for item in self._valid_records(records, self._branch) if item.get("phone") or item.get("email")]
                except Exception:
                    contacts = []
                if contacts:
                    return DynamicKnowledgeResult(source, contacts, True)
                return self._configured_topic(source, topic, fallback_error="public_contact_not_configured")
            if source == "business_config" and topic == "credit":
                try:
                    records = self._execute("payment_methods", self._payment_factory)
                    methods = [
                        item for item in self._public_payment_records(records)
                        if item.get("allows_credit") is True
                    ]
                except Exception:
                    return self._configured_topic(source, topic, fallback_error="credit_source_unavailable")

                if not methods:
                    configured = self._configured_topic(source, topic)
                    if configured.available:
                        return configured
                return DynamicKnowledgeResult(source, methods, True)
            if source == "business_config" and topic == "fleet_service":
                try:
                    records = self._execute("services", self._service_factory)
                    services = self._valid_records(records, self._fleet_service)
                    branch_rows = self._execute("branches", self._branch_factory)
                    public_branches = {
                        str(item.get("name") or "").casefold()
                        for item in self._valid_records(branch_rows, self._branch)
                        if not self._strict_public_quality or self._production_public_record(item)
                    }
                    for item in services:
                        names = [
                            value.strip() for value in str(item.get("branches") or "").split(",")
                            if value.strip() and value.strip().casefold() in public_branches
                        ]
                        item["branches"] = ", ".join(names) or None
                except Exception:
                    return self._configured_topic(source, topic, fallback_error="fleet_service_source_unavailable")
                if not services:
                    configured = self._configured_topic(source, topic)
                    if configured.available:
                        return configured
                return DynamicKnowledgeResult(source, services, True)
            if source in {"business_config", "policy_database"}:
                return self._configured_topic(source, topic)
            if source == "order_public_status":
                return DynamicKnowledgeResult(
                    source=source,
                    available=False,
                    error="authenticated_public_order_tool_required",
                )
        except Exception as exc:
            logger.info("assistant.business.dynamic_source_failed", extra={"source": source, "topic": topic})
            return DynamicKnowledgeResult(source=source, available=False, error=exc.__class__.__name__)
        return DynamicKnowledgeResult(source=source, available=False, error="source_not_configured")

    @staticmethod
    def _load_public_config(path: Path) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, ValueError, TypeError):
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _valid_records(
        records: list[Mapping[str, Any]],
        sanitizer: Callable[[Mapping[str, Any]], dict[str, Any] | None],
    ) -> list[dict[str, Any]]:
        clean: list[dict[str, Any]] = []
        for row in records:
            value = sanitizer(row)
            if value:
                clean.append(value)
        return clean

    @staticmethod
    def _deduplicate_payments(records: list[dict[str, Any]]) -> list[dict[str, Any]]:

        merged: dict[str, dict[str, Any]] = {}
        for record in records:
            key = re.sub(r"[^a-z0-9]+", "", str(record.get("name") or "").casefold())
            if not key:
                continue
            current = merged.get(key)
            if current is None:
                merged[key] = dict(record)
                continue
            if current.get("allows_credit") != record.get("allows_credit"):
                current["allows_credit"] = None
            if current.get("currency") != record.get("currency"):
                current["currency"] = None
        return list(merged.values())

    def _public_payment_records(
        self, records: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        methods = self._valid_records(records, self._payment)
        if self._strict_public_quality:
            methods = [item for item in methods if self._production_payment_record(item)]
        return self._deduplicate_payments(methods)

    @staticmethod
    def _production_public_record(record: Mapping[str, Any], *, min_name: int = 2) -> bool:
        text = " ".join(str(value or "") for value in record.values())
        name = str(record.get("name") or "").strip()
        return bool(
            len(re.sub(r"\W+", "", name)) >= min_name
            and not _TEST_DATA_RE.search(text)
            and not _UNSAFE_PUBLIC_DATA_RE.search(text)
        )

    @classmethod
    def _production_payment_record(cls, record: Mapping[str, Any]) -> bool:
        if not cls._production_public_record(record):
            return False
        folded = unicodedata.normalize("NFKD", str(record.get("name") or "").casefold())
        folded = "".join(char for char in folded if not unicodedata.combining(char))
        words = set(re.findall(r"[a-z0-9]+", folded.replace("_", " ")))
        return bool(words & (_PAYMENT_TERMS - {"metodo"}))

    def _configured_topic(
        self,
        source: str,
        topic: str,
        *,
        fallback_error: str = "approved_public_config_unavailable",
    ) -> DynamicKnowledgeResult:
        topics = self._public_config.get("topics")
        entry = topics.get(topic) if isinstance(topics, Mapping) else None
        if not isinstance(entry, Mapping) or entry.get("status") != "approved":
            return DynamicKnowledgeResult(source=source, available=False, error=fallback_error)
        configured_source = str(entry.get("source") or "")
        if configured_source not in {source, "approved_business_config"}:
            return DynamicKnowledgeResult(source=source, available=False, error="configured_source_mismatch")
        values = entry.get("records")
        if not isinstance(values, list):
            return DynamicKnowledgeResult(source=source, available=False, error="configured_records_invalid")
        sanitizer = self._config_sanitizer(topic)
        records = self._valid_records(
            [item for item in values if isinstance(item, Mapping)], sanitizer,
        )
        if not records:
            return DynamicKnowledgeResult(source=source, available=False, error="approved_config_empty")
        return DynamicKnowledgeResult(source=source, records=records, available=True)

    @classmethod
    def _config_sanitizer(
        cls, topic: str,
    ) -> Callable[[Mapping[str, Any]], dict[str, Any] | None]:
        if topic == "business_hours":
            return cls._configured_hours
        allowed_by_topic = {
            "warranty": ("summary", "requirements", "exclusions", "contact_channel"),
            "delivery": ("availability", "coverage", "conditions", "contact_channel"),
            "contact": ("name", "phone", "email", "channel"),
            "credit": ("availability", "summary", "requirements", "contact_channel"),
            "business_customers": ("availability", "requirements", "contact_channel"),
            "fleet_service": ("availability", "requirements", "contact_channel"),
            "service_booking": ("availability", "channel", "requirements"),
            "reservations": ("availability", "conditions", "contact_channel"),
            "bring_own_parts": ("availability", "conditions", "warranty_note"),
            "returns_and_claims": ("summary", "requirements", "exclusions", "contact_channel"),
            "business_policies": ("summary", "version", "effective_on", "contact_channel"),
        }
        allowed = allowed_by_topic.get(topic, ())

        def sanitize(row: Mapping[str, Any]) -> dict[str, Any] | None:
            result: dict[str, Any] = {}
            for key in allowed:
                raw = row.get(key)
                if isinstance(raw, bool):
                    result[key] = raw
                elif isinstance(raw, list):
                    values = [_public_text(item, limit=240) for item in raw]
                    result[key] = [item for item in values if item][:12]
                else:
                    value = _public_text(raw, limit=500)
                    if value:
                        result[key] = value
            return result or None

        return sanitize

    def _execute(self, key: str, default_factory: Callable[[], Any]) -> list[Mapping[str, Any]]:
        model = self._model_factories.get(key, default_factory)()
        rows = model.ejecutar("get_active") or []
        return [row for row in rows if isinstance(row, Mapping)]

    @staticmethod
    def _branch_factory() -> Any:
        from model.sucursal_model import SucursalModel

        return SucursalModel()

    @staticmethod
    def _promotion_factory() -> Any:
        from model.promotion_model import PromotionModel

        return PromotionModel()

    @staticmethod
    def _payment_factory() -> Any:
        from model.payment_method_model import PaymentMethodModel

        return PaymentMethodModel()

    @staticmethod
    def _category_factory() -> Any:
        from model.category_model import CategoryModel

        return CategoryModel()

    @staticmethod
    def _service_factory() -> Any:
        from model.service_model import ServiceModel

        return ServiceModel()

    @staticmethod
    def _category(row: Mapping[str, Any]) -> dict[str, Any] | None:
        name = _safe_public_name(row.get("nombre") or row.get("nombre_categoria"))
        if not name:
            return None
        value: dict[str, Any] = {
            "name": name,
            "description": _safe_public_description(
                row.get("descripcion") or row.get("descripcion_categoria"), limit=300,
            ) or None,
        }
        total = row.get("total_productos")
        if total not in (None, ""):
            try:
                value["active_products"] = max(0, int(total))
            except (TypeError, ValueError):
                pass
        return value

    @staticmethod
    def _branch(row: Mapping[str, Any]) -> dict[str, Any] | None:
        name = _safe_public_name(row.get("nombre") or row.get("nombre_sucursal"))
        if not name:
            return None
        return {
            "name": name,
            "address": _public_text(row.get("direccion") or row.get("direccion_sucursal"), limit=240) or None,
            "phone": _public_text(row.get("telefono") or row.get("telefono_sucursal"), limit=80) or None,
            "email": _public_text(row.get("email") or row.get("email_sucursal"), limit=160) or None,
        }

    @staticmethod
    def _branch_hours(row: Mapping[str, Any]) -> dict[str, Any] | None:
        name = _safe_public_name(row.get("nombre") or row.get("nombre_sucursal"))
        hours = _public_text(
            row.get("horario")
            or row.get("horario_atencion")
            or row.get("horario_sucursal")
            or row.get("business_hours"),
            limit=300,
        )
        if not name or not hours:
            return None
        return {"branch": name, "hours": hours}

    @staticmethod
    def _configured_hours(row: Mapping[str, Any]) -> dict[str, Any] | None:
        branch = _public_text(row.get("branch") or row.get("name"), limit=160)
        hours = _public_text(row.get("hours"), limit=300)
        note = _public_text(row.get("note"), limit=240)
        if not branch or not hours:
            return None
        return {"branch": branch, "hours": hours, "note": note or None}

    @staticmethod
    def _promotion(row: Mapping[str, Any]) -> dict[str, Any] | None:
        name = _safe_public_name(row.get("nombre") or row.get("nombre_promocion"))
        description = _safe_public_description(
            row.get("descripcion") or row.get("descripcion_promocion"), limit=400,
        )
        if not name:
            return None
        starts_raw = row.get("fecha_inicio") or row.get("fecha_inicio_promocion")
        ends_raw = row.get("fecha_fin") or row.get("fecha_fin_promocion")
        starts_on = _public_date(starts_raw)
        ends_on = _public_date(ends_raw)
        today = date.today()
        if starts_on and starts_on > today:
            return None
        if ends_on and ends_on < today:
            return None
        return {
            "name": name,
            "description": description or None,
            "type": _public_text(row.get("tipo") or row.get("tipo_promocion"), limit=80) or None,
            "starts_on": to_jsonable(starts_raw),
            "ends_on": to_jsonable(ends_raw),
        }

    @staticmethod
    def _payment(row: Mapping[str, Any]) -> dict[str, Any] | None:
        name = _safe_public_name(
            row.get("nombre") or row.get("nombre_metodo_pago"), semantic_terms=_PAYMENT_TERMS,
        )
        if not name:
            return None
        return {
            "name": name,
            "currency": _public_text(row.get("moneda"), limit=16) or None,
            "allows_credit": _public_bool(row.get("permite_credito")),
        }

    @staticmethod
    def _fleet_service(row: Mapping[str, Any]) -> dict[str, Any] | None:
        name = _safe_public_name(row.get("nombre") or row.get("nombre_servicio"))
        description = _safe_public_description(
            row.get("descripcion") or row.get("descripcion_servicio"), limit=360,
        )
        service_type = _public_text(row.get("tipo") or row.get("tipo_servicio"), limit=100)
        searchable = f"{name} {description} {service_type}".casefold()
        if not name or not any(term in searchable for term in ("flota", "camion", "camión", "carga", "pesado", "gandola")):
            return None
        return {
            "name": name,
            "description": description or None,
            "service_type": service_type or None,
            "branches": _public_text(row.get("sucursal_nombre"), limit=240) or None,
        }

class CallableBusinessDataProvider:

    def __init__(self, resolvers: Mapping[str, Callable[[str], Any]]) -> None:
        self.resolvers = dict(resolvers or {})

    def resolve(self, source: str, topic: str) -> DynamicKnowledgeResult:
        resolver = self.resolvers.get(source)
        if not resolver:
            return DynamicKnowledgeResult(source, available=False, error="resolver_unavailable")
        try:
            value = resolver(topic)
            if isinstance(value, DynamicKnowledgeResult):
                return value
            if value is None:
                return DynamicKnowledgeResult(source, available=False, error="unavailable")
            records = value if isinstance(value, list) else [value]
            public_records = [to_jsonable(item) for item in records if isinstance(item, Mapping)]
            return DynamicKnowledgeResult(source, public_records, available=True)
        except Exception as exc:
            return DynamicKnowledgeResult(source, available=False, error=exc.__class__.__name__)

class ResilientBusinessDataProvider:

    def __init__(
        self,
        provider: BusinessDataProvider,
        *,
        wait_timeout: float | None = None,
        cold_start_timeout: float | None = None,
        cache_ttl: float = 60.0,
        failure_ttl: float = 5.0,
    ) -> None:
        self.provider = provider
        self.wait_timeout = max(0.01, float(
            wait_timeout if wait_timeout is not None else os.getenv("ASSISTANT_DB_RETRIEVAL_TIMEOUT", "0.08")
        ))
        default_cold_timeout = (
            self.wait_timeout
            if wait_timeout is not None and cold_start_timeout is None
            else os.getenv("ASSISTANT_DB_COLD_START_TIMEOUT", "1.25")
        )
        self.cold_start_timeout = max(self.wait_timeout, float(
            cold_start_timeout if cold_start_timeout is not None else default_cold_timeout
        ))
        self.cache_ttl = max(0.1, float(cache_ttl))
        self.failure_ttl = max(0.1, float(failure_ttl))
        self._lock = threading.RLock()
        self._cache: dict[tuple[str, str], tuple[float, DynamicKnowledgeResult]] = {}
        self._loading_key: tuple[str, str] | None = None
        self._event: threading.Event | None = None

    def resolve(self, source: str, topic: str) -> DynamicKnowledgeResult:
        key = (source, topic)
        now = time.monotonic()
        authoritative_wait = False
        with self._lock:
            cached = self._cache.get(key)
            if cached:
                ttl = self.cache_ttl if cached[1].available else self.failure_ttl
                if now - cached[0] < ttl:
                    return cached[1]
            if self._loading_key is not None:
                if self._loading_key != key:
                    return DynamicKnowledgeResult(source, available=False, error="dynamic_source_busy")
                event = self._event
                authoritative_wait = cached is None or cached[1].available
            else:
                event = threading.Event()
                self._event = event
                self._loading_key = key

                authoritative_wait = cached is None or cached[1].available
                threading.Thread(
                    target=self._worker,
                    args=(key, event),
                    name="assistant-business-loader",
                    daemon=True,
                ).start()
        wait_budget = (
            self.cold_start_timeout if authoritative_wait else self.wait_timeout
        )
        if event is not None and event.wait(wait_budget):
            with self._lock:
                cached = self._cache.get(key)
                if cached:
                    return cached[1]
        return DynamicKnowledgeResult(source, available=False, error="dynamic_source_timeout")

    def _worker(self, key: tuple[str, str], event: threading.Event) -> None:
        source, topic = key
        started = time.perf_counter()
        try:
            result = self.provider.resolve(source, topic)
            if not isinstance(result, DynamicKnowledgeResult):
                result = DynamicKnowledgeResult(
                    source=source,
                    available=False,
                    error="invalid_provider_result",
                )
        except Exception as exc:
            result = DynamicKnowledgeResult(source, available=False, error=exc.__class__.__name__)
        assistant_metrics.record_db_call(
            (time.perf_counter() - started) * 1000.0,
            status="ok" if result.available else "error",
        )
        with self._lock:
            self._cache[key] = (time.monotonic(), result)
            self._loading_key = None
            event.set()

class BusinessKnowledge:
    def __init__(
        self,
        path: str | Path | None = None,
        *,
        data_provider: BusinessDataProvider | None = None,
        resolvers: Mapping[str, Callable[[str], Any]] | None = None,
        use_model_provider: bool | None = None,
    ) -> None:
        self.path = Path(path) if path else DEFAULT_FAQ_PATH
        self.payload = self._load(self.path)
        self.entries: dict[str, dict[str, Any]] = {
            entry["id"]: entry for entry in self.payload.get("entries", [])
        }
        if use_model_provider is None:
            use_model_provider = os.getenv("ASSISTANT_BUSINESS_DYNAMIC_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}
        if data_provider is not None:
            self.data_provider = data_provider
        elif resolvers is not None:
            self.data_provider = CallableBusinessDataProvider(resolvers)
        elif use_model_provider:
            self.data_provider = ResilientBusinessDataProvider(ModelBusinessDataProvider())
        else:
            self.data_provider = UnavailableBusinessDataProvider()
        self.rag = LightweightRAG(self._documents())

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError("business_faq.json must contain non-empty entries")
        ids = [entry.get("id") for entry in entries]
        if any(not item for item in ids) or len(ids) != len(set(ids)):
            raise ValueError("business FAQ ids must be present and unique")
        for entry in entries:
            if entry.get("dynamic") and not entry.get("dynamic_source"):
                raise ValueError(f"dynamic business FAQ {entry['id']} has no dynamic_source")
        return payload

    def _documents(self) -> list[RAGDocument]:
        documents = []
        for entry in self.entries.values():
            keywords = tuple(entry.get("topics") or ()) + tuple(entry.get("questions") or ())
            documents.append(RAGDocument(
                id=entry["id"],
                title=(entry.get("questions") or [entry["id"]])[0],
                content=entry.get("answer") or "",
                kind="business_knowledge",
                source="business_faq.json",
                keywords=keywords,
                metadata={"topic": entry["id"], "dynamic": bool(entry.get("dynamic"))},
            ))
        return documents

    def get(self, topic: str, *, resolve_dynamic: bool = True) -> RetrievalResult:
        entry = self.entries.get(str(topic or ""))
        if not entry:
            return RetrievalResult(query=str(topic or ""), status="empty", reason="unknown_business_topic")
        evidence = self._entry_evidence(entry, resolve_dynamic=resolve_dynamic)
        available = not entry.get("dynamic") or evidence.verified
        return RetrievalResult(
            query=topic,
            evidence=[evidence],
            status="ok" if available else "unavailable",
            available=available,
            partial=bool(entry.get("dynamic") and not evidence.verified),
            reason=None if available else "dynamic_business_data_unavailable",
            diagnostics={"topic": entry["id"], "dynamic_source": entry.get("dynamic_source")},
        )

    def search(self, query: str, *, limit: int = 3, resolve_dynamic: bool = True) -> RetrievalResult:
        hits = self.rag.search(query, limit=limit)
        evidence = [self._entry_evidence(self.entries[hit.document.id], resolve_dynamic=resolve_dynamic, score=hit.score) for hit in hits]
        unresolved = [item for item in evidence if item.dynamic and not item.verified]
        verified = [item for item in evidence if item.verified or not item.dynamic]
        return RetrievalResult(
            query=query,
            evidence=evidence,
            status="ok" if verified else "unavailable" if evidence else "empty",
            available=bool(verified),
            partial=bool(unresolved),
            reason="dynamic_business_data_unavailable" if evidence and not verified else None,
            diagnostics={"matches": len(evidence), "unresolved_dynamic": len(unresolved)},
        )

    def _entry_evidence(self, entry: Mapping[str, Any], *, resolve_dynamic: bool, score: float = 1.0) -> Evidence:
        dynamic = bool(entry.get("dynamic"))
        data: dict[str, Any] = {
            "topic": entry["id"],
            "required_tool": entry.get("required_tool"),
            "availability": "curated" if not dynamic else "unavailable",
        }
        verified = not dynamic
        source = str(entry.get("source") or entry.get("dynamic_source") or "business_faq.json")
        if dynamic and resolve_dynamic:
            resolved = self.data_provider.resolve(str(entry.get("dynamic_source")), str(entry["id"]))
            data["availability"] = "available" if resolved.available else "unavailable"
            data["records"] = resolved.records if resolved.available else []
            data["source_error"] = resolved.error
            verified = resolved.available
        return Evidence(
            id=evidence_id("business", entry["id"], data.get("availability")),
            kind="business_knowledge",
            source=source,
            title=(entry.get("questions") or [entry["id"]])[0],
            content=str(entry.get("answer") or ""),
            confidence=min(0.98, 0.72 + max(0.0, float(score)) / 20.0),
            verified=verified,
            dynamic=dynamic,
            data=data,
        )

    def dynamic_topics(self) -> dict[str, str]:
        return {
            entry["id"]: str(entry["dynamic_source"])
            for entry in self.entries.values()
            if entry.get("dynamic")
        }

BusinessKnowledgeRetriever = BusinessKnowledge
