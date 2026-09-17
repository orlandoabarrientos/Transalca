from collections import OrderedDict
from copy import deepcopy
from threading import RLock

def empty_state():
    return {"vehicle_brand": None, "vehicle_model": None, "vehicle_year": None,
            "tire_size": None, "tire_type": None, "last_intent": None,
            "last_products": [], "selected_product": None,
            "rim": None, "brand": None, "model": None, "branch": None}

class LiteStateStore:
    def __init__(self, max_sessions=1000):
        self.max_sessions = max(1, int(max_sessions))
        self._sessions = OrderedDict()
        self.lock = RLock()

    def get(self, session_id):
        with self.lock:
            if not session_id:
                return empty_state()
            value = self._sessions.get(str(session_id)[:200])
            return deepcopy(value) if value is not None else empty_state()

    def save(self, session_id, state):
        if not session_id:
            return
        with self.lock:
            key = str(session_id)[:200]
            self._sessions[key] = deepcopy(state)
            self._sessions.move_to_end(key)
            while len(self._sessions) > self.max_sessions:
                self._sessions.popitem(last=False)

    def reset(self, session_id):
        with self.lock:
            self._sessions.pop(str(session_id)[:200], None)
