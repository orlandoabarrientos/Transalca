import logging
import hashlib
import os
import re
import secrets
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

from flask import Blueprint, Flask, current_app, jsonify, request, send_from_directory, session

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from componente_ia.ai_mode import MAX_MESSAGE_LENGTH, build_response, get_default_orchestrator, is_lite_mode
from componente_ia.decision_trace import decision_trace_store
from componente_ia.feedback_store import feedback_store
from componente_ia.health import assistant_health as assistant_health_monitor
from componente_ia.learning_observability import learning_metrics_snapshot
from componente_ia.metrics import assistant_metrics, short_hash
from componente_ia.model_registry import ModelRegistry


logger = logging.getLogger(__name__)


asistente_bp = Blueprint('asistente_ia', __name__)
_rate_window = {}
_rate_lock = threading.RLock()
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('ASSISTANT_RATE_WINDOW_SECONDS', '60'))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv('ASSISTANT_RATE_LIMIT', '60'))
ENGINE_VERSION = "universal-tire-advisor-v3"
ENGINE_MODULE = "assistant_orchestrator"


def _build_id():
    digest = hashlib.sha256()
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ("assistant_orchestrator.py", "intent_router.py", "entity_extractor.py", "chat_widget.js"):
        try:
            with open(os.path.join(base, name), "rb") as stream:
                digest.update(stream.read())
        except OSError:
            digest.update(name.encode("utf-8"))
    return digest.hexdigest()[:12]


try:
    BUILD_ID = "lite-v1" if is_lite_mode() else ModelRegistry().active_identity()["build_id"]
except Exception:
    BUILD_ID = _build_id()


def generar_id_aleatorio(longitud=20):
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(alfabeto[secrets.randbelow(len(alfabeto))] for _ in range(longitud))


def _runtime_health():
    runtime = get_default_orchestrator()
    if is_lite_mode():
        return runtime.health()
    return assistant_health_monitor.snapshot(runtime)


def _request_id():
    return request.headers.get('X-Request-ID') or uuid.uuid4().hex[:12]


def _development_metadata_enabled():
    environment = os.getenv("TRANSALCA_ENV", "local").strip().lower()
    return bool(current_app.config.get("TESTING") or current_app.debug or environment not in {"prod", "production"})


def _safe_session_id(value):
    session_id = str(value or "").strip()
    if not session_id:
        return generar_id_aleatorio(20)
    if re.fullmatch(r"[A-Za-z0-9_-]{8,80}", session_id):
        return session_id
    return generar_id_aleatorio(20)


def _rate_limited(remote_addr):
    if RATE_LIMIT_MAX_REQUESTS <= 0:
        return False
    now = time.time()
    key = str(remote_addr or 'unknown')[:80]
    with _rate_lock:
        if len(_rate_window) > 2048:
            for old_key in list(_rate_window):
                if not any(now - stamp < RATE_LIMIT_WINDOW_SECONDS for stamp in _rate_window.get(old_key, [])):
                    _rate_window.pop(old_key, None)
        bucket = [stamp for stamp in _rate_window.get(key, []) if now - stamp < RATE_LIMIT_WINDOW_SECONDS]
        if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
            _rate_window[key] = bucket
            return True
        bucket.append(now)
        _rate_window[key] = bucket
        return False


@asistente_bp.route("/mensaje", methods=["POST"])
def procesar_mensaje():
    started = time.perf_counter()
    rid = _request_id()
    if _rate_limited(request.remote_addr):
        assistant_metrics.record_request(
            (time.perf_counter() - started) * 1000,
            success=False,
            error_type='rate_limited',
        )
        return jsonify({
            "status": "error",
            "session_id": "",
            "message": "Demasiadas solicitudes. Intenta de nuevo en unos segundos.",
            "request_id": rid
        }), 429

    data = request.get_json(silent=True) or {}
    mensaje = str(data.get("mensaje") or "").strip()
    session_id = _safe_session_id(data.get("session_id") or data.get("id_aleatorio"))
    history = data.get("history") if isinstance(data.get("history"), list) else []

    if len(mensaje) > MAX_MESSAGE_LENGTH:
        assistant_metrics.record_request(
            (time.perf_counter() - started) * 1000,
            success=False,
            error_type='message_too_long',
        )
        return jsonify({
            "status": "error",
            "session_id": session_id,
            "message": f"La pregunta no puede superar {MAX_MESSAGE_LENGTH} caracteres.",
            "request_id": rid
        }), 400

    try:
        payload, status_code = build_response(
            mensaje,
            session_id=session_id,
            history=history[-8:],
            request_id=rid,
        )
        payload["session_id"] = session_id
        payload["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if _development_metadata_enabled():
            payload.update({
                "engine_version": "lite-v1" if is_lite_mode() else ENGINE_VERSION,
                "engine_module": "lite_assistant" if is_lite_mode() else ENGINE_MODULE,
                "model_version": (payload.get("diagnostics") or {}).get("model_version"),
                "dataset_version": (payload.get("diagnostics") or {}).get("dataset_version"),
                "build_id": "lite-v1" if is_lite_mode() else BUILD_ID,
            })
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        diagnostics = payload.get("diagnostics") or {}
        sources = payload.get("sources") or []
        domains = [source.get("domain") for source in sources if isinstance(source, dict)]
        fallback = bool(payload.get("fallback"))
        logger.info(
            "assistant.request",
            extra={
                "request_id": rid,
                "session_hash": short_hash(session_id),
                "status_code": status_code,
                "duration_ms": duration_ms,
                "intent": payload.get("intent"),
                "catalog_available": diagnostics.get("catalog_available"),
                "matches": len(payload.get("matches") or []),
                "web_used": bool(sources),
                "source_domains": domains[:4],
                "fallback": fallback,
            },
        )
        return jsonify(payload), status_code
    except Exception as exc:
        decision_trace_store.capture(
            request_id=rid,
            normalized_message=mensaje,
            session_state_before={},
            entities={},
            domain=None,
            primary_intent="error",
            secondary_intents=[],
            followup_resolution={},
            pending_slots=[],
            actions=[],
            tools_selected=[],
            tool_results_summary={"completed": False, "error_type": exc.__class__.__name__},
            claims=[],
            response_type="internal_error",
            session_state_after={},
            abstained=False,
            fallback_reason="internal_error",
        )
        feedback_store.capture_passive_signal(
            mensaje,
            intent="error",
            answer="",
            confidence=0.0,
            fallback=True,
            signals=["error", exc.__class__.__name__],
            candidate_for_training=True,
        )
        assistant_metrics.record_learning_signal(candidate=True)
        assistant_metrics.record_request(
            (time.perf_counter() - started) * 1000,
            success=False,
            error_type=exc.__class__.__name__,
        )
        logger.exception("assistant.request_failed", extra={"request_id": rid, "session_hash": short_hash(session_id)})
        return jsonify({
            "status": "error",
            "session_id": session_id,
            "message": "Error interno del asistente.",
            "request_id": rid
        }), 500


@asistente_bp.route("/health", methods=["GET"])
def healthcheck():
    rid = _request_id()
    try:
        payload = _runtime_health()
        payload["engine_version"] = "lite-v1" if is_lite_mode() else ENGINE_VERSION
        payload["engine_module"] = "lite_assistant" if is_lite_mode() else ENGINE_MODULE
        payload["build_id"] = "lite-v1" if is_lite_mode() else BUILD_ID
        intent_model = (payload.get("components") or {}).get("intent_model") or {}
        payload["model_version"] = intent_model.get("model_version")
        payload["dataset_version"] = intent_model.get("dataset_hash")
        payload["request_id"] = rid
        payload["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return jsonify(payload), 200
    except Exception:
        logger.exception("assistant.health_failed", extra={"request_id": rid})
        return jsonify({
            "status": "error",
            "message": "Healthcheck del asistente no disponible.",
            "request_id": rid
        }), 500


@asistente_bp.route("/reset", methods=["POST"])
def reset_lite_session():
    if not is_lite_mode():
        return jsonify({"status": "error", "message": "Ruta disponible en Lite Mode."}), 404
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    if not isinstance(session_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", session_id):
        return jsonify({"status": "error", "message": "session_id inválido."}), 400
    get_default_orchestrator().reset_session(session_id)
    return jsonify({"status": "success", "session_id": session_id}), 200


@asistente_bp.route("/shadow/candidate", methods=["POST"])
def shadow_candidate():
    """Protected candidate runtime; disabled and fail-closed by default."""
    from componente_ia.candidate_shadow import candidate_shadow_message

    return candidate_shadow_message()


@asistente_bp.route("/shadow/health", methods=["GET"])
def shadow_healthcheck():
    """Identity-gated health endpoint for sealed candidate audits."""
    from componente_ia.candidate_shadow import candidate_shadow_health

    return candidate_shadow_health()


@asistente_bp.route("/metrics", methods=["GET"])
def metrics():
    rid = _request_id()
    if not _metrics_allowed():
        return jsonify({
            "status": "error",
            "message": "Metricas del asistente no disponibles para esta sesion.",
            "request_id": rid,
        }), 403
    payload = assistant_metrics.snapshot(runtime=_runtime_health())
    payload["status"] = "ok"
    payload["request_id"] = rid
    payload["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return jsonify(payload), 200


@asistente_bp.route("/feedback", methods=["POST"])
def operator_feedback():
    """Protected operator signal; it never accepts or stores a raw customer message."""
    rid = _request_id()
    if not _metrics_allowed():
        return jsonify({
            "status": "error",
            "message": "Feedback operativo no disponible para esta sesión.",
            "request_id": rid,
        }), 403
    data = request.get_json(silent=True) or {}
    case_id = str(data.get("case_id") or "").strip()
    rating = str(data.get("rating") or "").strip()
    if not re.fullmatch(r"FB-[0-9A-F]{20}", case_id) or rating.lower() not in {"good", "bad", "buena", "mala", "bueno", "malo", "1", "-1"}:
        return jsonify({
            "status": "error",
            "message": "Feedback inválido.",
            "request_id": rid,
        }), 400
    updated = feedback_store.rate(case_id, rating)
    return jsonify({
        "status": "success" if updated else "not_found",
        "updated": updated,
        "request_id": rid,
    }), 200 if updated else 404


@asistente_bp.route("/learning-metrics", methods=["GET"])
def learning_metrics():
    """Protected aggregate metrics; never returns messages or entity payloads."""
    rid = _request_id()
    if not _metrics_allowed():
        return jsonify({
            "status": "error",
            "message": "Métricas de aprendizaje no disponibles para esta sesión.",
            "request_id": rid,
        }), 403
    payload = learning_metrics_snapshot()
    payload.update({
        "status": "ok",
        "request_id": rid,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    })
    return jsonify(payload), 200


@asistente_bp.route("/admin/ia-learning", methods=["GET"])
def learning_admin_panel():
    if not _metrics_allowed():
        return "Acceso denegado.", 403
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "ia_learning_admin.html")


def _metrics_allowed():
    if os.getenv('ASSISTANT_METRICS_PUBLIC', '').strip().lower() in {'1', 'true', 'yes'}:
        return True
    if current_app and current_app.config.get('TESTING'):
        return True
    role = (
        session.get('rol')
        or session.get('role')
        or session.get('tipo_usuario')
        or session.get('user_role')
        or session.get('perfil')
    )
    if isinstance(role, dict):
        role = role.get('nombre') or role.get('name')
    return str(role or '').strip().lower() in {'admin', 'administrador', 'empleado', 'soporte'}


def create_app():
    standalone = Flask(__name__)
    logging.basicConfig(level=os.getenv('ASSISTANT_LOG_LEVEL', 'INFO'))
    standalone.register_blueprint(asistente_bp, url_prefix="/api/asistente")

    @standalone.get("/")
    def standalone_demo():
        return """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'">
<title>Asistente Transalca</title><link rel="stylesheet" href="/componente_ia/chat_widget.css"></head>
<body><main style="max-width:760px;margin:3rem auto;font-family:system-ui;padding:1rem">
<h1>Asistente Transalca</h1><p>Abre el botón de chat para probar el asesor automotriz y comercial.</p>
</main><script src="/componente_ia/chat_widget.js"></script></body></html>"""

    @standalone.get("/componente_ia/<path:filename>")
    def standalone_assets(filename):
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)

    return standalone


if __name__ == "__main__":
    assistant_host = os.getenv("ASSISTANT_HOST", "127.0.0.1")
    assistant_port = int(os.getenv("ASSISTANT_PORT", "5090"))
    create_app().run(host=assistant_host, port=assistant_port)
