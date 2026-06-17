from flask import Blueprint, request, jsonify, session
from model.tasa_cambio_model import TasaCambioModel
from config.validation import ValidationError

from model.bcv_sync_model import sync_bcv_rate_if_needed

tasa_bp = Blueprint('tasas', __name__)
model = TasaCambioModel()



def _ensure_bcv_auto_sync():
    try:
        sync_bcv_rate_if_needed(force=False)
    except Exception:
        return


@tasa_bp.route('/', methods=['GET'])
def get_all():
    try:
        _ensure_bcv_auto_sync()
        limit = request.args.get('limit', 30, type=int)
        return jsonify({"status": "success", "data": model.ejecutar("get_all", limit)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@tasa_bp.route('/today', methods=['GET'])
def get_today():
    try:
        _ensure_bcv_auto_sync()
        tasa = model.ejecutar("get_today")
        if tasa:
            return jsonify({"status": "success", "data": tasa})
        return jsonify({"status": "error", "message": "No hay tasa registrada hoy."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@tasa_bp.route('/latest', methods=['GET'])
def get_latest():
    try:
        _ensure_bcv_auto_sync()
        tasa = model.ejecutar("get_latest")
        if tasa:
            return jsonify({"status": "success", "data": tasa})
        return jsonify({"status": "error", "message": "No hay tasas registradas."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@tasa_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        tasa_id = model.ejecutar("create", request.get_json() or {})
        return jsonify({"status": "success", "message": "Tasa registrada correctamente.", "id": tasa_id})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@tasa_bp.route('/<int:tasa_id>', methods=['PUT'])
def update(tasa_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        model.ejecutar("update_tasa", tasa_id, request.get_json() or {})
        return jsonify({"status": "success", "message": "Tasa modificada correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@tasa_bp.route('/<int:tasa_id>', methods=['DELETE'])
def delete(tasa_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        model.ejecutar("delete_tasa", tasa_id)


        return jsonify({"status": "success", "message": "Tasa eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@tasa_bp.route('/sync-scraping', methods=['POST'])
def sync_scraping():
    try:
        result = sync_bcv_rate_if_needed(force=True)
        if not result.get('synced'):
            return jsonify({
                "status": "error",
                "message": "No se pudo sincronizar BCV.",
                "reason": result.get('reason')
            }), 502
        action = "actualizada" if result.get('action') == 'updated' else "registrada"
        monto = result.get('monto')
        monto_text = f"{float(monto):.2f}" if monto is not None else "--"
        return jsonify({
            "status": "success",
            "message": f"Tasa BCV {action}: {monto_text} Bs",
            "id": result.get('id'),
            "action": result.get('action')
        })
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
