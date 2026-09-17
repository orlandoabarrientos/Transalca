"""Asistente automotriz y comercial híbrido de Transalca."""

__version__ = "2.0.0"


def answer_user_message(message, session_id=None, history=None):
    """Lazy public entrypoint that avoids initializing providers on package import."""

    from componente_ia.ai_mode import build_response as _answer

    return _answer(message, session_id=session_id, history=history)


__all__ = ["__version__", "answer_user_message"]
