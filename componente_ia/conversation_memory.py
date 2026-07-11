"""Memoria conversacional estructurada, aislada por sesion y con TTL."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Callable

from componente_ia.entity_extractor import ExtractedEntities, extract


STATE_TEMPLATE = {
    "vehicle": {},
    "tire": {},
    "usage": [],
    "budget": None,
    "last_intent": None,
    "last_products": [],
    "last_services": [],
    "last_sources": [],
    "pending_question": None,
}


class ConversationContext(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def to_dict(self) -> dict[str, Any]:
        value = dict(self)
        entities = value.get("entities")
        if hasattr(entities, "to_dict"):
            value["entities"] = entities.to_dict()
        return value


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default) if value is not None else default


def _new_state(now: float) -> dict[str, Any]:
    state = deepcopy(STATE_TEMPLATE)
    state["updated_at"] = now
    return state


class ConversationMemory:
    def __init__(
        self,
        ttl_seconds: int = 1800,
        max_sessions: int = 500,
        max_items: int = 6,
        clock: Callable[[], float] | None = None,
    ):
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.max_sessions = max(1, int(max_sessions))
        self.max_items = max(1, int(max_items))
        self._clock = clock or time.time
        self._sessions: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()

    @staticmethod
    def _session_key(session_id: Any) -> str | None:
        if session_id in (None, ""):
            return None
        value = str(session_id).strip()
        if not value or len(value) > 160 or any(ord(char) < 32 for char in value):
            return None
        return value

    def _cleanup_locked(self) -> None:
        now = self._clock()
        for key in list(self._sessions):
            if now - float(self._sessions[key].get("updated_at") or 0) > self.ttl_seconds:
                self._sessions.pop(key, None)
        while len(self._sessions) > self.max_sessions:
            self._sessions.popitem(last=False)

    def _from_history(self, history: Any) -> dict[str, Any]:
        state = _new_state(self._clock())
        if not isinstance(history, list):
            return state
        for item in history[-12:]:
            if isinstance(item, str):
                message = item
            elif isinstance(item, dict):
                role = str(item.get("role") or item.get("type") or "user").lower()
                if role not in {"user", "usuario", "human"}:
                    continue
                message = item.get("content") or item.get("text") or item.get("message") or ""
            else:
                continue
            self._apply_entities(state, extract(message), clear_on_vehicle_change=True)
        return state

    def get(self, session_id: Any, history: Any = None) -> dict[str, Any] | None:
        key = self._session_key(session_id)
        with self._lock:
            self._cleanup_locked()
            if key and key in self._sessions:
                state = deepcopy(self._sessions[key])
                self._sessions.move_to_end(key)
                return state
        history_state = self._from_history(history)
        return history_state if any(history_state.get(name) for name in STATE_TEMPLATE) else None

    def resolve(self, session_id: Any = None, history: Any = None, entities: Any = None) -> ConversationContext:
        incoming = entities if isinstance(entities, ExtractedEntities) else ExtractedEntities(dict(entities or {})) if isinstance(entities, dict) else extract(entities or "")
        key = self._session_key(session_id)
        with self._lock:
            self._cleanup_locked()
            stored = deepcopy(self._sessions.get(key)) if key and key in self._sessions else None
        history_state = self._from_history(history)
        state = stored or history_state or _new_state(self._clock())

        merged = ExtractedEntities(dict(incoming))
        previous_vehicle = state.get("vehicle") or {}
        incoming_make = incoming.get("make")
        incoming_model = incoming.get("model")
        vehicle_changed = bool(
            (incoming_model and previous_vehicle.get("model") and incoming_model != previous_vehicle.get("model"))
            or (incoming_make and previous_vehicle.get("make") and incoming_make != previous_vehicle.get("make"))
        )
        inherited: list[str] = []
        if not vehicle_changed:
            for key_name in ("make", "model", "submodel", "year", "trim", "engine", "drivetrain", "vehicle_type"):
                if not merged.get(key_name) and previous_vehicle.get(key_name) is not None:
                    merged[key_name] = previous_vehicle[key_name]
                    inherited.append(key_name)
            tire = state.get("tire") or {}
            for key_name in ("current_rim", "current_tire_size", "requested_rim", "requested_tire_size", "tire_type", "load_index", "speed_rating", "load_range"):
                if not merged.get(key_name) and tire.get(key_name) is not None:
                    merged[key_name] = tire[key_name]
                    inherited.append(key_name)
        if not merged.get("usage") and state.get("usage"):
            merged["usage"] = list(state["usage"])
            inherited.append("usage")
        if not merged.get("budget") and state.get("budget"):
            merged["budget"] = state["budget"]
            inherited.append("budget")

        snapshot = deepcopy(state)
        snapshot.update({
            "entities": merged,
            "session_id": key,
            "context_used": bool(inherited),
            "inherited_fields": inherited,
            "vehicle_changed": vehicle_changed,
            "expires_in_seconds": self.ttl_seconds,
        })
        return ConversationContext(snapshot)

    def _apply_entities(self, state: dict[str, Any], entities: Any, clear_on_vehicle_change: bool = True) -> None:
        vehicle = dict(state.get("vehicle") or {})
        tire = dict(state.get("tire") or {})
        make = _get(entities, "make")
        model = _get(entities, "model")
        changed = bool(
            (model and vehicle.get("model") and model != vehicle.get("model"))
            or (make and vehicle.get("make") and make != vehicle.get("make"))
        )
        if changed and clear_on_vehicle_change:
            vehicle, tire = {}, {}
            state["last_products"] = []
            state["last_sources"] = []
            state["pending_question"] = None
        for key_name in ("make", "model", "submodel", "year", "trim", "engine", "drivetrain", "vehicle_type"):
            value = _get(entities, key_name)
            if value is not None:
                vehicle[key_name] = value
        for key_name in ("current_rim", "current_tire_size", "requested_rim", "requested_tire_size", "tire_type", "load_index", "speed_rating", "load_range"):
            value = _get(entities, key_name)
            if value is not None:
                tire[key_name] = value
        usage = _get(entities, "usage") or []
        if usage:
            state["usage"] = list(dict.fromkeys(str(item) for item in usage))[-self.max_items:]
        if _get(entities, "budget") is not None:
            state["budget"] = _get(entities, "budget")
        if _get(entities, "budget_max") is not None:
            state["budget_max"] = _get(entities, "budget_max")
        state["vehicle"] = vehicle
        state["tire"] = tire

    def update(
        self,
        session_id: Any = None,
        entities: Any = None,
        evidence: Any = None,
        answer: Any = None,
        intent: str | None = None,
        pending_question: str | None = None,
    ) -> dict[str, Any] | None:
        key = self._session_key(session_id)
        if not key:
            return None
        evidence = evidence if isinstance(evidence, dict) else {}
        with self._lock:
            self._cleanup_locked()
            state = deepcopy(self._sessions.get(key) or _new_state(self._clock()))
            self._apply_entities(state, entities or {}, clear_on_vehicle_change=True)
            state["last_intent"] = intent or evidence.get("intent") or _get(entities, "intent") or state.get("last_intent")
            products = evidence.get("inventory") or evidence.get("products") or []
            services = evidence.get("services") or []
            sources = evidence.get("web_sources") or evidence.get("sources") or []
            if products:
                state["last_products"] = deepcopy(list(products)[:self.max_items])
            if services:
                state["last_services"] = deepcopy(list(services)[:self.max_items])
            if sources:
                state["last_sources"] = deepcopy(list(sources)[:self.max_items])
            state["pending_question"] = pending_question if pending_question is not None else evidence.get("pending_question")
            state["updated_at"] = self._clock()
            self._sessions[key] = state
            self._sessions.move_to_end(key)
            self._cleanup_locked()
            return deepcopy(state)

    def clear(self, session_id: Any = None) -> None:
        key = self._session_key(session_id)
        with self._lock:
            if key:
                self._sessions.pop(key, None)
            else:
                self._sessions.clear()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            self._cleanup_locked()
            return {
                "sessions": len(self._sessions),
                "max_sessions": self.max_sessions,
                "ttl_seconds": self.ttl_seconds,
            }


SessionMemory = ConversationMemory
_DEFAULT_MEMORY = ConversationMemory()


def resolve(session_id: Any = None, history: Any = None, entities: Any = None) -> ConversationContext:
    return _DEFAULT_MEMORY.resolve(session_id=session_id, history=history, entities=entities)


def update(session_id: Any = None, entities: Any = None, evidence: Any = None, answer: Any = None, **kwargs: Any) -> dict[str, Any] | None:
    return _DEFAULT_MEMORY.update(session_id=session_id, entities=entities, evidence=evidence, answer=answer, **kwargs)


def clear(session_id: Any = None) -> None:
    _DEFAULT_MEMORY.clear(session_id)


__all__ = [
    "ConversationContext", "ConversationMemory", "STATE_TEMPLATE", "SessionMemory",
    "clear", "resolve", "update",
]
