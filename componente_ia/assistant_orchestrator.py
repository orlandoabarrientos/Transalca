"""Orquestador híbrido y grounded del asistente automotriz de Transalca."""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from componente_ia.business_knowledge import BusinessKnowledge
from componente_ia.catalog_retriever import CatalogProvider
from componente_ia.conversation_memory import ConversationMemory
from componente_ia.entity_extractor import ExtractedEntities, extract, normalize_message
from componente_ia.feedback_store import feedback_store, sanitize_entities
from componente_ia.guardrails import Guardrails
from componente_ia.intent_router import IntentResult, IntentRouter
from componente_ia.inventory_retriever import InventoryRetriever
from componente_ia.knowledge_types import Evidence, RetrievalResult
from componente_ia.metrics import assistant_metrics
from componente_ia.providers.fallback_provider import FallbackProvider
from componente_ia.response_composer import ResponseComposer
from componente_ia.semantic_intent_retriever import SemanticIntentRetriever
from componente_ia.service_retriever import ServiceRetriever
from componente_ia.source_quality import evaluate_source
from componente_ia.technical_knowledge import TechnicalKnowledge
from componente_ia.tire_fitment import TireFitmentRepository, assess_tire_change
from componente_ia.training_pipeline import IntentModel
from componente_ia.web_search import SearchProvider, WebSearchService


MAX_MESSAGE_LENGTH = int(os.getenv("ASSISTANT_MAX_MESSAGE_LENGTH", "1000"))
MODEL_DIR = Path(__file__).resolve().parent / "models"


@dataclass(slots=True)
class AssistantPlan:
    primary_intent: str
    secondary_intents: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    web_policy: str = "never"
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def _intent_names(intent: IntentResult | Mapping[str, Any] | str) -> set[str]:
    if isinstance(intent, str):
        return {intent}
    if isinstance(intent, Mapping):
        primary = intent.get("primary")
        secondary = intent.get("secondary") or []
    else:
        primary = intent.primary
        secondary = intent.secondary
    return {str(value) for value in [primary, *secondary] if value}


def _elapsed(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


class AssistantOrchestrator:
    def __init__(
        self,
        *,
        catalog_provider: CatalogProvider | None = None,
        search_service: WebSearchService | None = None,
        memory: ConversationMemory | None = None,
        router: IntentRouter | None = None,
        inventory: InventoryRetriever | None = None,
        services: ServiceRetriever | None = None,
        business: BusinessKnowledge | None = None,
        fitment: TireFitmentRepository | None = None,
        technical: TechnicalKnowledge | None = None,
        composer: ResponseComposer | None = None,
        guardrails: Guardrails | None = None,
    ) -> None:
        self.started_at = time.time()
        self.catalog_provider = catalog_provider or CatalogProvider()
        self.inventory = inventory or InventoryRetriever(catalog_provider=self.catalog_provider)
        self.services = services or ServiceRetriever(catalog_provider=self.catalog_provider)
        self.business = business or BusinessKnowledge()
        self.search_service = search_service or WebSearchService()
        self.memory = memory or ConversationMemory(
            ttl_seconds=int(os.getenv("ASSISTANT_MEMORY_TTL_SECONDS", "1800")),
            max_sessions=int(os.getenv("ASSISTANT_MEMORY_MAX_SESSIONS", "200")),
        )
        self.fitment = fitment or TireFitmentRepository()
        self.technical = technical or TechnicalKnowledge()
        self.composer = composer or ResponseComposer()
        self.guardrails = guardrails or Guardrails(max_message_length=MAX_MESSAGE_LENGTH)
        self.local_only = True
        self.fallback = FallbackProvider()
        self.local_model, self.model_status = self._load_model()
        self.semantic = self._load_semantic()
        self.router = router or IntentRouter(
            local_classifier=self.local_model,
            semantic_retriever=self.semantic,
        )

    @staticmethod
    def _load_model() -> tuple[IntentModel | None, str]:
        active = MODEL_DIR / "intent_model.active.json"
        candidate = MODEL_DIR / "intent_model.json"
        selected = active
        status = "active"
        if not active.exists() and _flag("ASSISTANT_ALLOW_CANDIDATE_MODEL", False):
            selected, status = candidate, "candidate_opt_in"
        if not selected.exists():
            return None, "not_promoted"
        try:
            return IntentModel.load(selected), status
        except Exception:
            return None, "invalid"

    @staticmethod
    def _load_semantic() -> SemanticIntentRetriever | None:
        try:
            return SemanticIntentRetriever()
        except Exception:
            return None

    def build_plan(self, intent: IntentResult | Mapping[str, Any] | str, entities: Any, context: Any = None) -> AssistantPlan:
        names = _intent_names(intent)
        primary = str(intent if isinstance(intent, str) else intent.get("primary") if isinstance(intent, Mapping) else intent.primary)
        secondary = [] if isinstance(intent, str) else list(intent.get("secondary") or []) if isinstance(intent, Mapping) else list(intent.secondary)
        actions: list[str] = []
        reasons: list[str] = []

        tire_intents = {
            "tire_inventory", "tire_size_lookup", "tire_recommendation", "tire_comparison",
            "tire_change_compatibility", "tire_technical_explanation", "truck_tire_advice",
        }
        service_intents = {name for name in names if name.startswith("service_")} | ({"fleet_service"} & names)
        product_intents = {"product_inventory", "product_recommendation", "product_price"} & names
        business_intents = {
            "promotion", "branch", "business_hours", "payment", "order_status", "upload_receipt",
            "warranty", "credit", "fleet_service", "business_customer", "service_booking",
            "business_info",
        } & names

        if names & tire_intents:
            if names & {"tire_size_lookup", "tire_recommendation", "tire_change_compatibility", "truck_tire_advice"}:
                actions.append("get_vehicle_fitment")
            if names & {"tire_inventory", "tire_recommendation"} or bool(getattr(entities, "asks_stock", False)) or bool(getattr(entities, "asks_price", False)):
                actions.append("search_inventory")
            if names & {"tire_comparison", "tire_change_compatibility", "tire_technical_explanation", "truck_tire_advice", "tire_recommendation"}:
                actions.append("search_technical_knowledge")
        if product_intents:
            actions.append("search_inventory")
        if service_intents:
            actions.append("search_services")
        if business_intents:
            actions.append("search_business_faq")
        last_products = context.get("last_products") if isinstance(context, Mapping) else None
        if last_products and primary in {"followup", "branch"}:
            actions.append("resolve_product_followup")
            if primary == "branch" and "search_business_faq" in actions:
                actions.remove("search_business_faq")

        unknown_vehicle = bool((entities.get("vehicle_resolution") or {}).get("needs_web")) if isinstance(entities, Mapping) else False
        requires_web = bool(names & {"tire_size_lookup", "tire_change_compatibility", "truck_tire_advice"})
        technical_web = bool(names & {"tire_technical_explanation"})
        if unknown_vehicle:
            web_policy = "required_if_enabled"
            reasons.append("unknown_vehicle")
        elif requires_web:
            web_policy = "if_local_insufficient"
            reasons.append("fitment_or_compatibility")
        elif "product_recommendation" in names and bool(entities.get("make") or entities.get("model")):
            web_policy = "if_local_insufficient"
            reasons.append("vehicle_product_specification")
        elif technical_web:
            web_policy = "if_local_insufficient"
            reasons.append("technical_specification")
        else:
            web_policy = "never"
        if web_policy != "never":
            actions.append("search_web_conditionally")
        return AssistantPlan(
            primary_intent=primary,
            secondary_intents=secondary,
            actions=list(dict.fromkeys(actions)),
            web_policy=web_policy,
            reasons=reasons,
        )

    def execute_plan(
        self,
        plan: AssistantPlan,
        *,
        message: str,
        entities: ExtractedEntities,
        context: Any = None,
        inventory: InventoryRetriever | None = None,
        services: ServiceRetriever | None = None,
        search_service: WebSearchService | None = None,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        evidence: dict[str, Any] = {"intent": plan.primary_intent}
        timings: dict[str, float] = {}
        inventory = inventory or self.inventory
        services = services or self.services
        search_service = search_service or self.search_service

        if "get_vehicle_fitment" in plan.actions:
            started = time.perf_counter()
            fitment = self.fitment.lookup(entities)
            evidence["fitment"] = fitment
            if plan.primary_intent == "tire_change_compatibility":
                evidence["size_comparison"] = assess_tire_change(
                    entities.get("current_tire_size"), entities.get("requested_tire_size"), fitment,
                )
            timings["fitment"] = _elapsed(started)

        if "search_technical_knowledge" in plan.actions:
            started = time.perf_counter()
            technical = self.technical.search(message, limit=3)
            evidence["technical_result"] = technical
            evidence["technical"] = technical.evidence
            timings["technical"] = _elapsed(started)

        if "search_inventory" in plan.actions:
            started = time.perf_counter()
            include_out = not bool(entities.get("asks_stock"))
            result = inventory.search(
                message,
                entities=entities,
                limit=6,
                include_out_of_stock=include_out,
            )
            evidence["inventory"] = result
            timings["inventory"] = _elapsed(started)

        if "resolve_product_followup" in plan.actions:
            started = time.perf_counter()
            previous = list(context.get("last_products") or []) if isinstance(context, Mapping) else []
            code = previous[0].get("codigo") if previous and isinstance(previous[0], Mapping) else None
            if code:
                evidence["inventory"] = inventory.get_by_code(str(code))
                evidence["product_followup"] = True
            timings["product_followup"] = _elapsed(started)

        if "search_services" in plan.actions:
            started = time.perf_counter()
            if plan.primary_intent == "service_list":
                result = services.list_active(limit=20)
            else:
                normalized = str(entities.get("normalized") or "")
                comparing_services = plan.primary_intent == "service_explanation" and (
                    "diferencia" in normalized or "compar" in normalized
                )
                result = services.search(
                    message,
                    service=None if comparing_services else entities.get("service"),
                    entities=None if comparing_services else entities,
                    limit=4,
                )
            evidence["services"] = result
            timings["services"] = _elapsed(started)

        if "search_business_faq" in plan.actions:
            started = time.perf_counter()
            evidence["business"] = self.business.search(message, limit=4, resolve_dynamic=True)
            timings["business"] = _elapsed(started)

        if "search_web_conditionally" in plan.actions and self._should_use_web(plan, evidence, entities):
            started = time.perf_counter()
            query = self._web_query(message, plan, entities)
            raw_sources = search_service.search(query, max_results=4)
            accepted = []
            for source in raw_sources or []:
                quality = evaluate_source(source, entities, query)
                source.quality = quality
                if quality.get("accepted"):
                    accepted.append(source)
            evidence["web_sources"] = accepted
            evidence["web_attempted"] = True
            timings["web"] = _elapsed(started)
        else:
            evidence["web_sources"] = []
            evidence["web_attempted"] = False
        return evidence, timings

    def _should_use_web(self, plan: AssistantPlan, evidence: Mapping[str, Any], entities: ExtractedEntities) -> bool:
        if not _flag("ASSISTANT_WEB_ENABLED", True):
            return False
        if plan.web_policy == "required_if_enabled":
            return True
        if _flag("ASSISTANT_WEB_VERIFY", False):
            return True
        if plan.primary_intent == "product_recommendation":
            return True
        fitment = evidence.get("fitment") or {}
        if plan.web_policy == "if_local_insufficient" and not fitment.get("sizes"):
            technical = evidence.get("technical_result")
            if technical is not None and getattr(technical, "evidence", None) and plan.primary_intent == "tire_technical_explanation":
                return False
            return True
        return False

    @staticmethod
    def _web_query(message: str, plan: AssistantPlan, entities: ExtractedEntities) -> str:
        vehicle = " ".join(str(entities.get(key) or "") for key in ("year", "make", "model", "trim")).strip()
        sizes = " ".join(entities.get("tire_sizes") or [])
        if plan.primary_intent == "tire_technical_explanation":
            return f"{sizes or normalize_message(message)[:160]} tire manufacturer technical specification load speed index"
        if plan.primary_intent == "truck_tire_advice":
            return f"{vehicle} {sizes} official manual commercial truck tire size load axle".strip()
        if plan.primary_intent == "product_recommendation":
            category = str(entities.get("product_category") or "automotive product")
            return f"{vehicle} official owner manual {category} specification".strip()
        return f"{vehicle} {sizes} official owner manual tire size fitment".strip()

    def handle(
        self,
        message: Any,
        session_id: str | None = None,
        history: list[Any] | None = None,
        request_id: str | None = None,
        catalog_provider: CatalogProvider | None = None,
        search_provider: SearchProvider | WebSearchService | None = None,
    ) -> tuple[dict[str, Any], int]:
        started = time.perf_counter()
        raw = str(message or "").strip()
        stage_ms: dict[str, float] = {}

        guard_started = time.perf_counter()
        safety = self.guardrails.check(raw)
        stage_ms["guardrails"] = _elapsed(guard_started)
        if not safety.allowed:
            status_code = 400 if safety.category == "invalid_input" else 200
            payload = {
                "status": "error" if status_code == 400 else "success",
                "respuesta": safety.response,
                "message": safety.response,
                "intent": safety.intent or "clarification",
                "primary_intent": safety.intent or "clarification",
                "secondary_intents": [],
                "confidence": round(1.0 - safety.risk if safety.category == "invalid_input" else safety.risk, 3),
                "needs_clarification": safety.category == "invalid_input",
                "matches": [],
                "sources": [],
                "fallback": False,
                "request_id": request_id,
                "diagnostics": {"duration_ms": _elapsed(started), "guardrail": safety.category},
            }
            assistant_metrics.record_request(
                _elapsed(started), success=status_code < 400, intent=payload["intent"],
                security_rejected=safety.intent == "sensitive_request",
                confidence=payload["confidence"],
            )
            return payload, status_code

        entity_started = time.perf_counter()
        original_entities = extract(raw)
        context = self.memory.resolve(session_id=session_id, history=history, entities=original_entities)
        entities = context.entities
        stage_ms["entities_memory"] = _elapsed(entity_started)

        intent_started = time.perf_counter()
        intent = self.router.classify(raw, entities=original_entities, context=context)
        intent = self._contextual_intent(intent, original_entities, context)
        stage_ms["intent"] = _elapsed(intent_started)

        plan_started = time.perf_counter()
        plan = self.build_plan(intent, entities, context)
        stage_ms["planning"] = _elapsed(plan_started)

        per_inventory = None
        per_services = None
        if catalog_provider is not None:
            per_inventory = InventoryRetriever(catalog_provider=catalog_provider)
            per_services = ServiceRetriever(catalog_provider=catalog_provider)
        if isinstance(search_provider, WebSearchService):
            per_search = search_provider
        elif search_provider is not None:
            per_search = WebSearchService(provider=search_provider)
        else:
            per_search = None

        evidence, execution_ms = self.execute_plan(
            plan,
            message=raw,
            entities=entities,
            context=context,
            inventory=per_inventory,
            services=per_services,
            search_service=per_search,
        )
        stage_ms.update(execution_ms)

        compose_started = time.perf_counter()
        if evidence.get("product_followup"):
            answer = self._compose_product_followup(raw, evidence.get("inventory"))
        else:
            answer = self.composer.compose(intent, entities, context, evidence)
        output_check = self.guardrails.validate_output(answer)
        if not output_check.allowed:
            fallback = self.fallback.complete(
                [], intent=intent.to_dict(), entities=entities, evidence=self._flatten_evidence(evidence),
                reason="unsafe_or_empty_output",
            )
            answer = fallback.answer
        stage_ms["compose"] = _elapsed(compose_started)

        fallback_used = self._is_fallback(intent, evidence, answer)
        needs_clarification = bool(intent.needs_clarification or self._needs_clarification(intent.primary, entities, evidence))
        safe_inventory = self._inventory_matches(evidence.get("inventory"))
        safe_sources = [self._source_dict(source) for source in evidence.get("web_sources") or []]
        duration_ms = _elapsed(started)
        payload = {
            "status": "success",
            "respuesta": answer,
            "message": answer,
            "intent": intent.primary,
            "primary_intent": intent.primary,
            "secondary_intents": list(intent.secondary),
            "model_intent": intent.primary if intent.method == "local_model" else None,
            "intent_method": intent.method,
            "confidence": round(float(intent.confidence), 4),
            "needs_clarification": needs_clarification,
            "fallback": fallback_used,
            "matches": safe_inventory,
            "sources": safe_sources,
            "entities": sanitize_entities(entities),
            "evidence_summary": self._evidence_summary(evidence),
            "request_id": request_id,
            "diagnostics": {
                "duration_ms": duration_ms,
                "stage_ms": stage_ms,
                "catalog_available": self._result_available(evidence.get("inventory"), evidence.get("services")),
                "web_available": self._web_available(per_search or self.search_service),
                "web_attempted": bool(evidence.get("web_attempted")),
                "web_used": bool(safe_sources),
                "generation_mode": "local_only",
                "model_status": self.model_status,
                "plan_actions": plan.actions,
            },
        }

        memory_evidence = {
            "intent": intent.primary,
            "inventory": safe_inventory,
            "services": self._service_memory(evidence.get("services")),
            "web_sources": safe_sources,
            "pending_question": answer if needs_clarification else None,
        }
        self.memory.update(
            session_id=session_id,
            entities=entities,
            evidence=memory_evidence,
            answer=answer,
            intent=intent.primary,
            pending_question=answer if needs_clarification else None,
        )
        signals = []
        if fallback_used:
            signals.append("fallback")
        if intent.confidence < 0.65:
            signals.append("low_confidence")
        if evidence.get("web_attempted") and not safe_sources:
            signals.append("web_without_source")
        inventory_result = evidence.get("inventory")
        if inventory_result is not None and getattr(inventory_result, "status", None) == "empty":
            signals.append("inventory_without_results")
        normalized_raw = normalize_message(raw)
        user_reformulated = bool(
            any(marker in normalized_raw for marker in (
                "no entendiste", "no me entendiste", "quise decir", "en realidad", "te corrijo", "corrijo",
            ))
        )
        if user_reformulated:
            signals.append("user_reformulated")
        record = feedback_store.capture_passive_signal(
            raw,
            intent=intent.primary,
            entities=entities,
            answer=answer,
            confidence=intent.confidence,
            fallback=fallback_used,
            signals=signals,
            user_reformulated=user_reformulated,
            candidate_for_training=bool(signals),
        )
        payload["feedback_case_id"] = record.get("case_id") or None
        assistant_metrics.record_learning_signal(
            candidate=bool(record.get("candidate_for_training")),
            reformulated=user_reformulated,
        )
        assistant_metrics.record_stages(stage_ms)
        assistant_metrics.record_request(
            duration_ms,
            success=True,
            intent=intent.primary,
            catalog_available=payload["diagnostics"]["catalog_available"],
            match_count=len(safe_inventory),
            web_used=bool(safe_sources),
            domains=[source.get("domain") for source in safe_sources],
            fallback=fallback_used,
            security_rejected=False,
            confidence=intent.confidence,
        )
        return payload, 200

    @staticmethod
    def _contextual_intent(intent: IntentResult, original: ExtractedEntities, context: Mapping[str, Any]) -> IntentResult:
        if intent.primary not in {"clarification", "followup"}:
            return intent
        last = context.get("last_intent")
        incremental = bool(
            original.get("year") or original.get("requested_rim") or original.get("requested_tire_size")
            or original.get("tire_type") or original.get("usage") or original.get("budget")
            or original.get("make") or original.get("model")
        )
        if incremental and last and last not in {"out_of_scope", "sensitive_request", "clarification"}:
            return IntentResult(
                primary=str(last), secondary=["followup"], confidence=max(0.78, intent.confidence),
                method="context_followup", needs_clarification=False,
            )
        return intent

    @staticmethod
    def _flatten_evidence(evidence: Mapping[str, Any]) -> list[Evidence]:
        values: list[Evidence] = []
        seen = set()
        for raw in evidence.values():
            candidates = []
            if isinstance(raw, RetrievalResult):
                candidates = raw.evidence
            elif isinstance(raw, list):
                candidates = [item for item in raw if isinstance(item, Evidence)]
            for item in candidates:
                if item.id not in seen:
                    seen.add(item.id)
                    values.append(item)
        for source in evidence.get("web_sources") or []:
            item = source.to_evidence()
            if item.id not in seen:
                seen.add(item.id)
                values.append(item)
        return values

    @staticmethod
    def _compose_product_followup(message: str, result: Any) -> str:
        if not isinstance(result, RetrievalResult) or not result.available or not result.evidence:
            return "No pude volver a verificar el producto anterior en el catálogo. Indícame la medida o el producto para buscarlo de nuevo."
        data = dict(result.evidence[0].data)
        name = str(data.get("name") or "el producto anterior")
        normalized = normalize_message(message)
        details = []
        if any(word in normalized for word in ("precio", "cuesta", "barato")):
            details.append(f"precio ${float(data['price']):.2f}" if data.get("price_available") and data.get("price") is not None else "precio por confirmar")
        if any(word in normalized for word in ("stock", "disponible", "quedan")):
            status = data.get("stock_status")
            details.append(f"stock {int(data['stock'])}" if status == "available" else "sin stock" if status == "out_of_stock" else "stock por confirmar")
        if any(word in normalized for word in ("sucursal", "sede", "donde")):
            details.append(f"sucursal {data['branch']}" if data.get("branch_available") and data.get("branch") else "sucursal por confirmar")
        if not details:
            if data.get("price_available") and data.get("price") is not None:
                details.append(f"precio ${float(data['price']):.2f}")
            if data.get("stock_status") == "available":
                details.append(f"stock {int(data['stock'])}")
            if data.get("branch_available") and data.get("branch"):
                details.append(f"sucursal {data['branch']}")
        return f"El producto anterior es {name}" + (": " + ", ".join(details) if details else ".") + ". Datos verificados nuevamente en el catálogo; valida compatibilidad antes de comprar."

    @staticmethod
    def _inventory_matches(result: Any) -> list[dict[str, Any]]:
        if not isinstance(result, RetrievalResult):
            return []
        matches = []
        for item in result.evidence:
            data = dict(item.data)
            if data.get("stock_status") != "available":
                continue
            matches.append({
                "codigo": data.get("code"),
                "nombre": data.get("name"),
                "descripcion": data.get("description"),
                "categoria": data.get("category"),
                "marca": data.get("brand"),
                "precio": data.get("price") if data.get("price_available") else None,
                "stock": data.get("stock"),
                "sucursal": data.get("branch") if data.get("branch_available") else None,
                "sizes": data.get("sizes") or [],
                "compatibility": data.get("match"),
                "score": data.get("score"),
            })
        return matches

    @staticmethod
    def _source_dict(source: Any) -> dict[str, Any]:
        return {
            "title": str(getattr(source, "title", ""))[:160],
            "url": str(getattr(source, "url", ""))[:800],
            "domain": str(getattr(source, "domain", ""))[:160],
            "snippet": str(getattr(source, "snippet", ""))[:500],
            "provider": str(getattr(source, "provider", ""))[:80],
            "quality": dict(getattr(source, "quality", {}) or {}),
        }

    @staticmethod
    def _service_memory(result: Any) -> list[dict[str, Any]]:
        if not isinstance(result, RetrievalResult):
            return []
        values = []
        for item in result.evidence:
            if item.kind == "service_availability" and item.data.get("availability") == "active":
                values.append({"name": item.data.get("name"), "service_id": item.data.get("service_id")})
        return values

    @staticmethod
    def _result_available(*results: Any) -> bool | None:
        values = [value.available for value in results if isinstance(value, RetrievalResult)]
        if not values:
            return None
        return any(values)

    @staticmethod
    def _web_available(service: WebSearchService) -> bool:
        try:
            health = service.health()
        except Exception:
            return False
        return bool(health.get("enabled", True)) and not bool((health.get("circuit") or {}).get("open"))

    @staticmethod
    def _evidence_summary(evidence: Mapping[str, Any]) -> dict[str, Any]:
        summary = {
            "local_fitment": bool((evidence.get("fitment") or {}).get("sizes")),
            "inventory": len(getattr(evidence.get("inventory"), "evidence", []) or []),
            "services": len(getattr(evidence.get("services"), "evidence", []) or []),
            "business": len(getattr(evidence.get("business"), "evidence", []) or []),
            "technical": len(evidence.get("technical") or []),
            "web_sources": len(evidence.get("web_sources") or []),
        }
        return summary

    @staticmethod
    def _needs_clarification(intent: str, entities: ExtractedEntities, evidence: Mapping[str, Any]) -> bool:
        if intent in {"tire_size_lookup", "tire_recommendation", "truck_tire_advice"}:
            if not entities.get("model") or not entities.get("year"):
                return True
            fitment = evidence.get("fitment") or {}
            return not bool(fitment.get("sizes") or evidence.get("web_sources"))
        if intent == "tire_change_compatibility":
            return not bool(entities.get("current_tire_size") and entities.get("requested_tire_size"))
        return False

    @staticmethod
    def _is_fallback(intent: IntentResult, evidence: Mapping[str, Any], answer: str) -> bool:
        if intent.primary in {"out_of_scope", "sensitive_request"}:
            return False
        results = [value for value in evidence.values() if isinstance(value, RetrievalResult)]
        unavailable = bool(results) and all(not value.available for value in results)
        no_evidence = not any(
            [
                (evidence.get("fitment") or {}).get("sizes"), evidence.get("technical"),
                evidence.get("web_sources"),
                any(value.evidence for value in results),
            ]
        )
        return unavailable or (no_evidence and intent.primary not in {"clarification", "followup"}) or "No puedo confirmar" in answer

    def health(self) -> dict[str, Any]:
        try:
            web = self.search_service.health()
        except Exception as exc:
            web = {"status": "degraded", "error": exc.__class__.__name__}
        catalog_health = self.inventory.catalog_access.health() if self.inventory.catalog_access else {"available": False}
        return {
            "status": "ok",
            "catalog": {
                "status": "ok" if catalog_health.get("cached") else "degraded",
                "available": bool(catalog_health.get("cached")),
            },
            "web": {
                "status": "ok" if not (web.get("circuit") or {}).get("open") else "degraded",
                "enabled": web.get("enabled", True),
                "provider": web.get("provider"),
                "circuit_open": bool((web.get("circuit") or {}).get("open")),
            },
            "memory": {"status": "ok", **self.memory.stats()},
            "intent_model": {
                "status": self.model_status,
                "available": self.local_model is not None,
                "model_version": self.local_model.artifact.get("version") if self.local_model else None,
            },
            "semantic_retrieval": {"status": "ok" if self.semantic else "degraded", "available": self.semantic is not None},
            "generation": {"status": "ok", "provider": "local_only", "available": True},
        }

    def answer_user_message(self, message: Any, session_id: str | None = None, history: list[Any] | None = None, **kwargs: Any) -> tuple[dict[str, Any], int]:
        return self.handle(message, session_id=session_id, history=history, **kwargs)


_DEFAULT_ORCHESTRATOR: AssistantOrchestrator | None = None


def get_default_orchestrator() -> AssistantOrchestrator:
    global _DEFAULT_ORCHESTRATOR
    if _DEFAULT_ORCHESTRATOR is None:
        _DEFAULT_ORCHESTRATOR = AssistantOrchestrator()
    return _DEFAULT_ORCHESTRATOR


def build_plan(intent: IntentResult | Mapping[str, Any] | str, entities: Any, context: Any = None) -> AssistantPlan:
    return get_default_orchestrator().build_plan(intent, entities, context)


def execute_plan(plan: AssistantPlan, *, message: str = "", entities: Any = None, context: Any = None) -> dict[str, Any]:
    evidence, _ = get_default_orchestrator().execute_plan(
        plan, message=message, entities=entities or ExtractedEntities(), context=context,
    )
    return evidence


def build_response(message: Any, session_id: str | None = None, history: list[Any] | None = None, **kwargs: Any) -> tuple[dict[str, Any], int]:
    return get_default_orchestrator().handle(message, session_id=session_id, history=history, **kwargs)


def answer_user_message(message: Any, session_id: str | None = None, history: list[Any] | None = None) -> tuple[dict[str, Any], int]:
    return build_response(message, session_id=session_id, history=history)


__all__ = [
    "AssistantOrchestrator", "AssistantPlan", "MAX_MESSAGE_LENGTH", "answer_user_message",
    "build_plan", "build_response", "execute_plan", "get_default_orchestrator",
]
