from flask import Blueprint, jsonify, request, session

from controller._guards import deny, is_employee, require_login
from model.bitacora_model import BitacoraModel
from model.credit_model import CreditModel


credit_bp = Blueprint('credit', __name__)
model = CreditModel()
bitacora = BitacoraModel()
ALLOWED_STATUS = {'pendiente', 'aprobado', 'pagado', 'vencido', 'anulado'}


@credit_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.get_all(request.args.get('q'), request.args.get('estado'))})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@credit_bp.route('/stats', methods=['GET'])
def stats():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.get_stats()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@credit_bp.route('/<int:order_id>/status', methods=['PUT'])
def update_status(order_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        estado = (data.get('estado') or '').strip().lower()
        if estado not in ALLOWED_STATUS:
            return jsonify({"status": "error", "message": "El estado seleccionado no es valido."}), 400
        model.update_status(order_id, estado)
        if session.get('user_id'):
            bitacora.log_action(session['user_id'], 'MODIFICAR', 'CREDITO', f"Credito actualizado orden: {order_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Credito modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
