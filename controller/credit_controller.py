from flask import Blueprint, jsonify, request, session

from controller._guards import deny, is_employee, require_login
from config.validation import ValidationError

from model.credit_model import CreditModel


credit_bp = Blueprint('credit', __name__)
model = CreditModel()


@credit_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_all", request.args.get('q'), request.args.get('estado'))})
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
        return jsonify({"status": "success", "data": model.ejecutar("get_stats")})
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
        updated = model.ejecutar("update_status", order_id, data.get('estado'))
        if not updated:
            return jsonify({"status": "error", "message": "Crédito no encontrado."}), 404
        return jsonify({"status": "success", "message": "Crédito modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
        updated = model.ejecutar("update_dates", order_id, data.get('fecha_inicio'), data.get('fecha_fin'))
        if not updated:
            return jsonify({"status": "error", "message": "Crédito no encontrado."}), 404
        return jsonify({"status": "success", "message": "Crédito modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
        updated = model.ejecutar("mark_paid", order_id)
        if not updated:
            return jsonify({"status": "error", "message": "Crédito no encontrado."}), 404
        if session.get('user_id'):

            pass
        return jsonify({"status": "success", "message": "Crédito pagado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@credit_bp.route('/<int:order_id>/payment', methods=['PUT'])
def register_payment(order_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        result = model.ejecutar("register_payment", order_id, data.get('monto'))
        if not result.get('ok'):
            return jsonify({"status": "error", "message": result.get('message', 'No se pudo registrar el abono.')}), result.get('status_code', 400)
        message = "Crédito pagado correctamente." if result.get('pagado') else "Abono registrado correctamente."
        return jsonify({
            "status": "success",
            "message": message,
            "data": {
                "monto_deuda": str(result.get('monto_deuda', 0)),
                "pagado": bool(result.get('pagado'))
            }
        })
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@credit_bp.route('/', methods=['POST'])
def create_credit():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        result = model.ejecutar("create_credit", request.get_json() or {})
        if not result.get('ok'):
            return jsonify({"status": "error", "message": result.get('message')}), 400
        return jsonify({"status": "success", "message": result.get('message'), "data": {"id": result.get('id')}})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
