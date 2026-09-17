from __future__ import annotations

import re
import threading
from .lite_business_handler import LiteBusinessHandler
from .lite_entities import extract_entities, normalize
from .lite_inventory_handler import LiteInventoryHandler
from .lite_response_templates import GREETING, MISSING, UNSUPPORTED, UNVERIFIED_VEHICLE
from .lite_router import is_unsafe, route_intent
from .lite_state import LiteStateStore
from .lite_vehicle_handler import LiteVehicleHandler

INVENTORY_INTENTS = {"inventory_by_size", "inventory_by_brand", "inventory_by_type", "price", "stock", "cheapest", "most_stock"}

class LiteAssistant:
    def __init__(self, *, inventory_retriever=None, service_retriever=None,
                 business_retriever=None, catalog_path=None, state_store=None):
        if inventory_retriever is None:
            from componente_ia.inventory_retriever import InventoryRetriever
            inventory_retriever = InventoryRetriever()
        if service_retriever is None:
            from componente_ia.service_retriever import ServiceRetriever
            service_retriever = ServiceRetriever()
        if business_retriever is None:
            from componente_ia.business_retriever import BusinessRetriever
            business_retriever = BusinessRetriever()
        self.inventory = LiteInventoryHandler(inventory_retriever)
        self.business = LiteBusinessHandler(business_retriever, service_retriever, inventory_retriever)
        self.vehicle = LiteVehicleHandler(catalog_path)
        self.state_store = state_store or LiteStateStore()

    def health(self):
        return {"status": "ok", "ai_mode": "lite", "generation_mode": "deterministic",
                "web_enabled": False, "fitment_inference_enabled": False,
                "verified_vehicles": sum(row.get("status") == "VERIFIED" and bool(row.get("evidence")) for row in self.vehicle.vehicles)}

    def reset_session(self, session_id):
        self.state_store.reset(session_id)

    def respond(self, message, session_id=None, history=None, request_id=None, **kwargs):

        with self.state_store.lock:
            return self._respond(message, session_id, request_id)

    build_response = respond

    def _respond(self, message, session_id, request_id):
        if not isinstance(message, str) or not message.strip() or len(message) > 4000:
            return {"status": "error", "message": "Escribe una consulta de hasta 4000 caracteres.",
                    "respuesta": "Escribe una consulta de hasta 4000 caracteres.", "ai_mode": "lite"}, 400
        session_id = str(session_id)[:200] if session_id else None
        state = self.state_store.get(session_id)
        products = None
        available = None
        matches = []
        if is_unsafe(message):

            entities = extract_entities("")
            answer = UNSUPPORTED
            intent = "unsupported"
        else:
            try:
                products = self.inventory.load_products()
            except Exception:
                products = None
            catalog_brands = [item.get("marca") for item in products] if products else ()
            catalog_models = [item.get("modelo") for item in products] if products else ()
            catalog_branches = [name.strip() for item in products for name in (item.get("sucursal") or "").split(",") if name.strip()] if products else ()
            entities = self.vehicle.enrich(message, extract_entities(message, brands=catalog_brands, models=catalog_models, branches=catalog_branches))
            intent = route_intent(message, entities, state)

            new_vehicle = bool(entities.get("vehicle_model") and normalize(entities["vehicle_model"]) != normalize(state.get("vehicle_model")))
            new_size = entities.get("tire_size") is not None and entities["tire_size"] != state.get("tire_size")
            if new_vehicle or new_size:
                for key in ("tire_size", "rim", "tire_type", "brand", "model", "branch", "selected_product"):
                    state[key] = None
                state["last_products"] = []
                if new_vehicle:
                    state["vehicle_year"] = None
            if intent in INVENTORY_INTENTS and state.get("last_intent") in {"vehicle_fitment", "vehicle_followup"} and not state.get("tire_size") and not entities.get("tire_size"):
                answer = UNVERIFIED_VEHICLE
            elif intent in {"vehicle_fitment", "vehicle_followup"}:
                answer, verified_size = self.vehicle.handle(entities, state)
                if verified_size:
                    state["tire_size"] = verified_size
                    state["rim"] = extract_entities(verified_size)["rim"]
            elif intent in {"payment_methods", "branches", "services", "categories"}:
                try:
                    answer = self.business.handle(intent, entities)
                except Exception:
                    answer = MISSING
                    available = False
            elif intent in INVENTORY_INTENTS:
                malformed = bool(re.search(r"\d[\d/.Xx ]*R\s*\d", message, re.I)) and entities.get("tire_size") is None
                if malformed:
                    answer = "Indícame una medida válida, por ejemplo 265/65R17."
                else:
                    try:

                        ordinal = re.search(r"\b(primero|primera|segundo|segunda|tercero|tercera)\b", normalize(message))
                        if ordinal and state.get("last_products"):
                            index = {"primero": 0, "primera": 0, "segundo": 1, "segunda": 1, "tercero": 2, "tercera": 2}[ordinal.group(1)]
                            state["selected_product"] = state["last_products"][index] if index < len(state["last_products"]) else None
                            if index >= len(state["last_products"]):
                                answer = MISSING
                            else:
                                answer, matches, available = self.inventory.handle(intent, entities, state, products)
                        else:
                            if any(entities.get(key) for key in ("tire_size", "rim", "brand", "model", "tire_type", "branch")):
                                state["selected_product"] = None
                            answer, matches, available = self.inventory.handle(intent, entities, state, products)
                    except Exception:
                        answer = MISSING
                        available = False
                state["last_products"] = matches
                if len(matches) == 1:
                    state["selected_product"] = matches[0]
            elif intent == "greeting":
                answer = GREETING
            else:
                answer = UNSUPPORTED
            for key in ("vehicle_brand", "vehicle_model", "vehicle_year", "tire_size", "rim", "tire_type", "brand", "model", "branch"):
                if entities.get(key) is not None:
                    state[key] = entities[key]
            state["last_intent"] = intent
            self.state_store.save(session_id, state)
        payload = {"status": "success", "respuesta": answer, "message": answer,
                   "ai_mode": "lite", "intent": intent, "primary_intent": intent,
                   "secondary_intents": [], "intent_method": "lite_rules", "confidence": 1.0,
                   "needs_clarification": answer.startswith("Indícame"), "fallback": intent == "unsupported",
                   "matches": matches, "sources": [], "entities": entities, "request_id": request_id,
                   "diagnostics": {"ai_mode": "lite", "generation_mode": "deterministic", "catalog_available": available,
                                   "web_attempted": False, "web_used": False, "fitment_inferred": False}}
        return payload, 200

_default_assistant = None
_default_lock = threading.Lock()

def get_default_assistant():
    global _default_assistant
    with _default_lock:
        if _default_assistant is None:
            _default_assistant = LiteAssistant()
        return _default_assistant

def build_response(message, session_id=None, history=None, request_id=None, **kwargs):
    return get_default_assistant().respond(message, session_id=session_id, history=history, request_id=request_id, **kwargs)
