import secrets
from datetime import datetime

from flask import Blueprint, Flask, jsonify, request

from componente_ia.asistente_engine import MAX_MESSAGE_LENGTH, build_response


asistente_bp = Blueprint('asistente_ia', __name__)


def generar_id_aleatorio(longitud=20):
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(alfabeto[secrets.randbelow(len(alfabeto))] for _ in range(longitud))


@asistente_bp.route("/mensaje", methods=["POST"])
def procesar_mensaje():
    data = request.get_json(silent=True) or {}
    mensaje = str(data.get("mensaje") or "").strip()
    session_id = str(data.get("session_id") or data.get("id_aleatorio") or "").strip() or generar_id_aleatorio(20)
    history = data.get("history") if isinstance(data.get("history"), list) else []

    if len(mensaje) > MAX_MESSAGE_LENGTH:
        return jsonify({
            "status": "error",
            "session_id": session_id,
            "message": "La pregunta no puede superar 255 caracteres."
        }), 400

    payload, status_code = build_response(mensaje, session_id=session_id, client_history=history[-6:])
    payload["session_id"] = session_id
    payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return jsonify(payload), status_code


def create_app():
    standalone = Flask(__name__)
    standalone.register_blueprint(asistente_bp, url_prefix="/api/asistente")
    return standalone


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5090)
