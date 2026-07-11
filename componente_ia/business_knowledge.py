"""Grounded business FAQ retrieval with optional dynamic, read-only adapters."""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id, to_jsonable
from componente_ia.lightweight_rag import LightweightRAG, RAGDocument
from componente_ia.metrics import assistant_metrics


logger = logging.getLogger(__name__)
DEFAULT_FAQ_PATH = Path(__file__).with_name("data") / "business_faq.json"


def _public_text(value: Any, *, limit: int = 500) -> str:
    text = re.sub(r"<[^>]*>", " ", str(value or ""))
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


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
        """Return public, whitelisted records for one configured source."""


class UnavailableBusinessDataProvider:
    def resolve(self, source: str, topic: str) -> DynamicKnowledgeResult:
        return DynamicKnowledgeResult(source=source, available=False, error="provider_unavailable")


class ModelBusinessDataProvider:
    """Read-only adapter over existing model actions; it never executes SQL itself.

    Only public fields are copied. Payment instructions/account details and internal
    identifiers are intentionally excluded even if a model returns them.
    """

    def __init__(self, model_factories: Mapping[str, Callable[[], Any]] | None = None) -> None:
        self._model_factories = dict(model_factories or {})

    def resolve(self, source: str, topic: str) -> DynamicKnowledgeResult:
        try:
            if source == "branch_database":
                records = self._execute("branches", self._branch_factory)
                return DynamicKnowledgeResult(source, [self._branch(item) for item in records], True)
            if source == "promotion_database":
                records = self._execute("promotions", self._promotion_factory)
                return DynamicKnowledgeResult(source, [self._promotion(item) for item in records], True)
            if source == "business_config" and topic == "payment_methods":
                records = self._execute("payment_methods", self._payment_factory)
                return DynamicKnowledgeResult(source, [self._payment(item) for item in records], True)
        except Exception as exc:
            logger.info("assistant.business.dynamic_source_failed", extra={"source": source, "topic": topic})
            return DynamicKnowledgeResult(source=source, available=False, error=exc.__class__.__name__)
        return DynamicKnowledgeResult(source=source, available=False, error="source_not_configured")

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
    def _branch(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": _public_text(row.get("nombre") or row.get("nombre_sucursal"), limit=160),
            "address": _public_text(row.get("direccion") or row.get("direccion_sucursal"), limit=240) or None,
            "phone": _public_text(row.get("telefono") or row.get("telefono_sucursal"), limit=80) or None,
            "email": _public_text(row.get("email") or row.get("email_sucursal"), limit=160) or None,
        }

    @staticmethod
    def _promotion(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": _public_text(row.get("nombre") or row.get("nombre_promocion"), limit=160),
            "description": _public_text(row.get("descripcion") or row.get("descripcion_promocion"), limit=400) or None,
            "type": _public_text(row.get("tipo") or row.get("tipo_promocion"), limit=80) or None,
            "starts_on": to_jsonable(row.get("fecha_inicio") or row.get("fecha_inicio_promocion")),
            "ends_on": to_jsonable(row.get("fecha_fin") or row.get("fecha_fin_promocion")),
        }

    @staticmethod
    def _payment(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": _public_text(row.get("nombre") or row.get("nombre_metodo_pago"), limit=120),
            "currency": _public_text(row.get("moneda"), limit=16) or None,
            "allows_credit": bool(row.get("permite_credito")),
        }


class CallableBusinessDataProvider:
    """Test/integration adapter mapping dynamic source names to callables."""

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
    """Short-budget cache/circuit wrapper with at most one daemon lookup in flight."""

    def __init__(
        self,
        provider: BusinessDataProvider,
        *,
        wait_timeout: float | None = None,
        cache_ttl: float = 60.0,
        failure_ttl: float = 5.0,
    ) -> None:
        self.provider = provider
        self.wait_timeout = max(0.01, float(
            wait_timeout if wait_timeout is not None else os.getenv("ASSISTANT_DB_RETRIEVAL_TIMEOUT", "0.08")
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
            else:
                event = threading.Event()
                self._event = event
                self._loading_key = key
                threading.Thread(
                    target=self._worker,
                    args=(key, event),
                    name="assistant-business-loader",
                    daemon=True,
                ).start()
        if event is not None and event.wait(self.wait_timeout):
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
