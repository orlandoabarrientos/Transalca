import time
import threading
from collections import OrderedDict
from copy import deepcopy

from componente_ia.automotive_entities import AutomotiveEntities, extract_entities


class SessionMemory:
    def __init__(self, ttl_seconds=1800, max_sessions=200):
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions = OrderedDict()
        self._lock = threading.RLock()

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
        with self._lock:
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
            or bool(entities.uses)
            or bool(entities.need)
            or bool(entities.budget)
            or bool(entities.max_price)
        )
        if not merge_allowed:
            return entities
        merged = deepcopy(entities)
        vehicle = state.get('vehicle') or {}
        tire = state.get('tire') or {}
        need = state.get('need') or {}
        explicit_service = entities.need == 'servicio'
        explicit_tire_change = bool(entities.tire_size or entities.rim)

        explicit_vehicle_change = False
        if entities.model and vehicle.get('model') and entities.model != vehicle.get('model'):
            explicit_vehicle_change = True
        if entities.make and vehicle.get('make') and entities.make != vehicle.get('make'):
            explicit_vehicle_change = True

        if not explicit_vehicle_change and not explicit_service:
            merged.make = merged.make or vehicle.get('make')
            merged.model = merged.model or vehicle.get('model')
            merged.year = merged.year or vehicle.get('year')
            if not explicit_tire_change:
                merged.rim = merged.rim or tire.get('rim') or vehicle.get('rim')
                inherited_size = tire.get('tire_size') or vehicle.get('tire_size')
                if not merged.tire_size and inherited_size:
                    merged.tire_size = inherited_size
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
        with self._lock:
            self._cleanup()
            reset_context = 'sesion nueva' in entities.clean or 'nueva sesion' in entities.clean
            state = ({} if reset_context else self._sessions.get(session_id, {})) or {
                'time': time.time(),
                'vehicle': {},
                'tire': {},
                'usage': [],
                'vehicles': [],
                'need': {},
                'last_candidates': [],
                'last_inventory_results': [],
                'last_sources': [],
                'last_question_type': None,
                'history': [],
            }
            previous_vehicle = dict(state.get('vehicle') or {})
            new_vehicle = self._vehicle_from_entities(entities, {})
            vehicle_changed = bool(
                (entities.model and previous_vehicle.get('model') and entities.model != previous_vehicle.get('model'))
                or (entities.make and previous_vehicle.get('make') and entities.make != previous_vehicle.get('make'))
            )
            if vehicle_changed:
                state['vehicle'] = self._vehicle_from_entities(entities, {})
                state['tire'] = self._tire_from_entities(entities, {})
                state['last_candidates'] = []
                state['last_inventory_results'] = []
                state['last_sources'] = []
            else:
                state['vehicle'] = self._vehicle_from_entities(entities, state.get('vehicle') or {})
                state['tire'] = self._tire_from_entities(entities, state.get('tire') or {})
            if new_vehicle:
                vehicles = list(state.get('vehicles') or [])
                vehicle_key = (new_vehicle.get('make'), new_vehicle.get('model'), new_vehicle.get('year'), new_vehicle.get('rim'), new_vehicle.get('size'))
                vehicles = [
                    item for item in vehicles
                    if (item.get('make'), item.get('model'), item.get('year'), item.get('rim'), item.get('size')) != vehicle_key
                ]
                vehicles.append(new_vehicle)
                state['vehicles'] = vehicles[-4:]
            state['need'] = self._need_from_entities(entities, state.get('need') or {})
            state['usage'] = sorted(set((state.get('usage') or [])) | set(state['need'].get('uses') or []))
            if candidates:
                state['last_candidates'] = list(candidates or [])[:6]
                state['last_inventory_results'] = list(candidates or [])[:6]
            else:
                state['last_candidates'] = list(state.get('last_candidates') or [])[:6]
                state['last_inventory_results'] = list(state.get('last_inventory_results') or [])[:6]
            state['last_question_type'] = entities.intent_hint
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
            self._cleanup()

    def clear(self):
        with self._lock:
            self._sessions.clear()

    def stats(self):
        with self._lock:
            self._cleanup()
            return {
                'sessions': len(self._sessions),
                'max_sessions': self.max_sessions,
                'ttl_seconds': self.ttl_seconds,
            }

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

    def _tire_from_entities(self, entities, current=None):
        current = dict(current or {})
        changed = False
        if entities.rim:
            current['rim'] = entities.rim
            current.pop('tire_size', None)
            current.pop('size', None)
            changed = True
        if entities.tire_size:
            current['tire_size'] = entities.tire_size
            current['size'] = entities.tire_size.normalized
            current['rim'] = entities.tire_size.rim
            changed = True
        if entities.tire_type:
            current['type'] = entities.tire_type
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
