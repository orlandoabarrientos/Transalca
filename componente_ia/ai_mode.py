from __future__ import annotations

import os
import sys

MAX_MESSAGE_LENGTH = int(os.getenv("ASSISTANT_MAX_MESSAGE_LENGTH", "1000"))

def is_lite_mode() -> bool:
    mode = os.getenv("TRANSALCA_AI_MODE", "").strip().lower()
    if mode == "full":
        return False
    if mode == "lite":
        return True
    if "componente_ia.assistant_orchestrator" in sys.modules:
        return False
    try:
        import componente_ia.assistant_orchestrator
        return False
    except ImportError:
        return True

def get_default_orchestrator():
    if is_lite_mode():
        from componente_ia.lite.lite_assistant import get_default_assistant

        return get_default_assistant()
    try:
        from componente_ia.assistant_orchestrator import get_default_orchestrator as full
        return full()
    except Exception:
        from componente_ia.lite.lite_assistant import get_default_assistant
        return get_default_assistant()

def build_response(message, session_id=None, history=None, **kwargs):
    if is_lite_mode():
        return get_default_orchestrator().respond(
            message, session_id=session_id, history=history, **kwargs,
        )
    try:
        from componente_ia.assistant_orchestrator import build_response as full
        return full(message, session_id=session_id, history=history, **kwargs)
    except Exception:
        return get_default_orchestrator().respond(
            message, session_id=session_id, history=history, **kwargs,
        )
