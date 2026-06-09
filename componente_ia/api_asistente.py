import logging
import os
import secrets
import sys
import time
import uuid
from datetime import datetime, timezone

from flask import Blueprint, Flask, jsonify, request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from componente_ia.asistente_engine import MAX_MESSAGE_LENGTH, assistant_health, build_response


logger = logging.getLogger(__name__)


asistente_bp = Blueprint('asistente_ia', __name__)
_rate_window = {}
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('ASSISTANT_RATE_WINDOW_SECONDS', '60'))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv('ASSISTANT_RATE_LIMIT', '60'))


def generar_id_aleatorio(longitud=20):
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(alfabeto[secrets.randbelow(len(alfabeto))] for _ in range(longitud))


def _request_id():
    return request.headers.get('X-Request-ID') or uuid.uuid4().hex[:12]


def _rate_limited(remote_addr):
    if RATE_LIMIT_MAX_REQUESTS <= 0:
        return False
    now = time.time()
    key = remote_addr or 'unknown'
    bucket = [stamp for stamp in _rate_window.get(key, []) if now - stamp < RATE_LIMIT_WINDOW_SECONDS]
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        _rate_window[key] = bucket
        return True
    bucket.append(now)
    _rate_window[key] = bucket
    return False


@asistente_bp.route("/mensaje", methods=["POST"])
def procesar_mensaje():
    rid = _request_id()
    if _rate_limited(request.remote_addr):
        return jsonify({
            "status": "error",
            "session_id": "",
            "message": "Demasiadas solicitudes. Intenta de nuevo en unos segundos.",
            "request_id": rid
        }), 429

    data = request.get_json(silent=True) or {}
    mensaje = str(data.get("mensaje") or "").strip()
    session_id = str(data.get("session_id") or data.get("id_aleatorio") or "").strip() or generar_id_aleatorio(20)
    history = data.get("history") if isinstance(data.get("history"), list) else []

    if len(mensaje) > MAX_MESSAGE_LENGTH:
        return jsonify({
            "status": "error",
            "session_id": session_id,
            "message": f"La pregunta no puede superar {MAX_MESSAGE_LENGTH} caracteres.",
            "request_id": rid
        }), 400

    try:
        started = time.perf_counter()
        payload, status_code = build_response(
            mensaje,
            session_id=session_id,
            client_history=history[-8:],
            request_id=rid,
        )
        payload["session_id"] = session_id
        payload["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        logger.info(
            "assistant.request",
            extra={
                "request_id": rid,
                "status_code": status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "intent": payload.get("intent"),
            },
        )
        return jsonify(payload), status_code
    except Exception:
        logger.exception("assistant.request_failed", extra={"request_id": rid})
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
        payload = assistant_health()
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


def create_app():
    standalone = Flask(__name__)
    logging.basicConfig(level=os.getenv('ASSISTANT_LOG_LEVEL', 'INFO'))
    standalone.register_blueprint(asistente_bp, url_prefix="/api/asistente")
    return standalone


if __name__ == "__main__":
    assistant_host = os.getenv("ASSISTANT_HOST", "127.0.0.1")
    assistant_port = int(os.getenv("ASSISTANT_PORT", "5090"))
    create_app().run(host=assistant_host, port=assistant_port)
