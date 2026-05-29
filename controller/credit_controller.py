from datetime import datetime

from flask import Blueprint, jsonify, request, session

from controller._guards import deny, is_employee, require_login
from model.bitacora_model import BitacoraModel
from model.credit_model import CreditModel


credit_bp = Blueprint('credit', __name__)
model = CreditModel()
bitacora = BitacoraModel()
ALLOWED_STATUS = {'pendiente', 'aprobado', 'activo', 'pagado', 'vencido', 'anulado'}


def _parse_date(value, field, errors):
    raw = (value or '').strip()
    if not raw:
        errors[field] = "La fecha es obligatoria."
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        errors[field] = "La fecha no es valida."
        return None


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
        updated = model.update_status(order_id, estado)
        if not updated:
            return jsonify({"status": "error", "message": "Credito no encontrado."}), 404
        if session.get('user_id'):
            bitacora.log_action(session['user_id'], 'MODIFICAR', 'CREDITO', f"Credito actualizado orden: {order_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Credito modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@credit_bp.route('/<int:order_id>/dates', methods=['PUT'])
def update_dates(order_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        errors = {}
        start = _parse_date(data.get('fecha_inicio'), 'fecha_inicio', errors)
        end = _parse_date(data.get('fecha_fin'), 'fecha_fin', errors)
        if start and end and end < start:
            errors['fecha_fin'] = "La fecha fin no puede ser menor a la fecha inicio."
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        updated = model.update_dates(order_id, start, end)
        if not updated:
            return jsonify({"status": "error", "message": "Credito no encontrado."}), 404
        if session.get('user_id'):
            bitacora.log_action(session['user_id'], 'MODIFICAR', 'CREDITO', f"Fechas de credito actualizadas orden: {order_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Credito modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@credit_bp.route('/<int:order_id>/paid', methods=['PUT'])
def mark_paid(order_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        updated = model.mark_paid(order_id)
        if not updated:
            return jsonify({"status": "error", "message": "Credito no encontrado."}), 404
        if session.get('user_id'):
            bitacora.log_action(session['user_id'], 'MODIFICAR', 'CREDITO', f"Credito pagado orden: {order_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Credito pagado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
