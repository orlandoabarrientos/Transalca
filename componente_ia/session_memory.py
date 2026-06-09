import time
from collections import OrderedDict
from copy import deepcopy

from componente_ia.automotive_entities import AutomotiveEntities, extract_entities


class SessionMemory:
    def __init__(self, ttl_seconds=1800, max_sessions=200):
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions = OrderedDict()

    def _cleanup(self):
        now = time.time()
        expired = [
            session_id for session_id, value in self._sessions.items()
            if now - value.get('time', 0) > self.ttl_seconds
        ]
        for session_id in expired:
            self._sessions.pop(session_id, None)
        while len(self._sessions) > self.max_sessions:
            self._sessions.popitem(last=False)

    def get(self, session_id, client_history=None):
        self._cleanup()
        if not session_id:
            return None
        state = self._sessions.get(session_id)
        if state:
            state['time'] = time.time()
            self._sessions.move_to_end(session_id)
            return state
        state = self._state_from_history(client_history)
        if state:
            self._sessions[session_id] = state
            return state
        return None

    def _state_from_history(self, client_history):
        if not isinstance(client_history, list):
            return None
        vehicle = {}
        need = {}
        for item in client_history[-8:]:
            if not isinstance(item, dict) or item.get('type') != 'user':
                continue
            entities = extract_entities(item.get('text') or '')
            if entities.make or entities.model or entities.year or entities.rim or entities.tire_size:
                vehicle = self._vehicle_from_entities(entities, vehicle)
            if entities.tire_type or entities.uses or entities.budget:
                need = self._need_from_entities(entities, need)
        if not vehicle and not need:
            return None
        return {
            'time': time.time(),
            'vehicle': vehicle,
            'need': need,
            'last_candidates': [],
            'history': [],
        }

    def merge(self, entities: AutomotiveEntities, state):
        if not state:
            return entities
        merge_allowed = (
            entities.followup
            or entities.has_tire_request()
            or entities.has_vehicle()
            or bool(entities.need)
        )
        if not merge_allowed:
            return entities
        merged = deepcopy(entities)
        vehicle = state.get('vehicle') or {}
        need = state.get('need') or {}

        explicit_vehicle_change = False
        if entities.model and vehicle.get('model') and entities.model != vehicle.get('model'):
            explicit_vehicle_change = True
        if entities.make and vehicle.get('make') and entities.make != vehicle.get('make'):
            explicit_vehicle_change = True

        if not explicit_vehicle_change:
            merged.make = merged.make or vehicle.get('make')
            merged.model = merged.model or vehicle.get('model')
            merged.year = merged.year or vehicle.get('year')
            merged.rim = merged.rim or vehicle.get('rim')
            if not merged.tire_size and vehicle.get('tire_size'):
                merged.tire_size = vehicle.get('tire_size')
                merged.width = getattr(merged.tire_size, 'width', None)
                merged.profile = getattr(merged.tire_size, 'profile', None)
        merged.tire_type = merged.tire_type or need.get('tire_type')
        if not merged.uses and need.get('uses'):
            merged.uses = set(need.get('uses') or [])
        merged.budget = merged.budget or need.get('budget')
        merged.max_price = merged.max_price or need.get('max_price')
        return merged

    def update(self, session_id, entities, candidates=None, answer=''):
        if not session_id:
            return
        self._cleanup()
        state = self._sessions.get(session_id, {
            'time': time.time(),
            'vehicle': {},
            'need': {},
            'last_candidates': [],
            'history': [],
        })
        state['vehicle'] = self._vehicle_from_entities(entities, state.get('vehicle') or {})
        state['need'] = self._need_from_entities(entities, state.get('need') or {})
        if candidates:
            state['last_candidates'] = list(candidates or [])[:6]
        else:
            state['last_candidates'] = list(state.get('last_candidates') or [])[:6]
        history = state.get('history') or []
        history.append({
            'question': entities.raw[:240],
            'intent': entities.intent_hint,
            'answer': (answer or '')[:300],
        })
        state['history'] = history[-5:]
        state['time'] = time.time()
        self._sessions[session_id] = state
        self._sessions.move_to_end(session_id)

    def clear(self):
        self._sessions.clear()

    def _vehicle_from_entities(self, entities, current=None):
        current = dict(current or {})
        changed = False
        if entities.make:
            current['make'] = entities.make
            changed = True
        if entities.model:
            current['model'] = entities.model
            changed = True
        if entities.year:
            current['year'] = entities.year
            changed = True
        if entities.rim:
            current['rim'] = entities.rim
            changed = True
        if entities.tire_size:
            current['tire_size'] = entities.tire_size
            current['size'] = entities.tire_size.normalized
            changed = True
        return current if changed or current else {}

    def _need_from_entities(self, entities, current=None):
        current = dict(current or {})
        if entities.tire_type:
            current['tire_type'] = entities.tire_type
        if entities.uses:
            current['uses'] = sorted(entities.uses)
        if entities.budget:
            current['budget'] = entities.budget
        if entities.max_price:
            current['max_price'] = entities.max_price
        if entities.need:
            current['need'] = entities.need
        return current
