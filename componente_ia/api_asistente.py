import os
import secrets
from datetime import datetime

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()
ASISTENTE_PORT = int(os.getenv("ASISTENTE_PORT", "5090"))


def generar_id_aleatorio(longitud=20):
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(alfabeto[secrets.randbelow(len(alfabeto))] for _ in range(longitud))


@app.route("/api/asistente/mensaje", methods=["POST"])
def procesar_mensaje():
    data = request.get_json(silent=True) or {}
    mensaje = str(data.get("mensaje") or "").strip()
    session_id = str(data.get("session_id") or data.get("id_aleatorio") or "").strip() or generar_id_aleatorio(20)

    if not mensaje:
        return jsonify({"status": "error", "message": "Mensaje requerido"}), 400

    payload = {
        "session_id": session_id,
        "id_aleatorio": session_id,
        "mensaje": mensaje,
        "expected_response": "json",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "transalca_chat"
    }

    if not N8N_WEBHOOK_URL:
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "respuesta": "Webhook n8n no configurado. Define N8N_WEBHOOK_URL para conectar el asistente."
        })

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=25)
        if not response.ok:
            return jsonify({
                "status": "error",
                "session_id": session_id,
                "message": f"Webhook respondio con estado {response.status_code}"
            }), 502

        result = response.json() if response.content else {}
        respuesta = result.get("respuesta") or result.get("message") or result.get("output") or result.get("text")
        if not respuesta:
            respuesta = "Solicitud recibida. Un asesor te respondera pronto."

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "respuesta": respuesta,
            "raw": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "session_id": session_id,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=ASISTENTE_PORT)
