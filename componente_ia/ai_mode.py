"""Small, removable runtime switch; full remains the default.

Import the selected assistant lazily so Lite does not initialize models,
registries, candidate packs or the full orchestrator.
"""

from __future__ import annotations

import os

MAX_MESSAGE_LENGTH = int(os.getenv("ASSISTANT_MAX_MESSAGE_LENGTH", "1000"))


def is_lite_mode() -> bool:
    return os.getenv("TRANSALCA_AI_MODE", "full").strip().lower() == "lite"


def get_default_orchestrator():
    if is_lite_mode():
        from componente_ia.lite.lite_assistant import get_default_assistant

        return get_default_assistant()
    from componente_ia.assistant_orchestrator import get_default_orchestrator as full

    return full()


def build_response(message, session_id=None, history=None, **kwargs):
    if is_lite_mode():
        return get_default_orchestrator().respond(
            message, session_id=session_id, history=history, **kwargs,
        )
    from componente_ia.assistant_orchestrator import build_response as full

    return full(message, session_id=session_id, history=history, **kwargs)
