"""Asistente automotriz y comercial híbrido de Transalca."""

__version__ = "2.0.0"


def answer_user_message(message, session_id=None, history=None):
    """Lazy public entrypoint that avoids initializing providers on package import."""

    from componente_ia.assistant_orchestrator import answer_user_message as _answer

    return _answer(message, session_id=session_id, history=history)


__all__ = ["__version__", "answer_user_message"]
