from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, session

from controller._guards import deny, is_employee, require_login

from model.credit_model import CreditModel


credit_bp = Blueprint('credit', __name__)
model = CreditModel()

ALLOWED_STATUS = {'pendiente', 'aprobado', 'activo', 'pagado', 'vencido', 'anulado'}


def _parse_date(value, field, errors):
    raw = (value or '').strip()
    if not raw:
        errors[field] = "La fecha es obligatoria."
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        errors[field] = "La fecha no es válida."
        return None


def _parse_amount(value, errors):
    raw = str(value or '').strip().replace(',', '.')
    if not raw:
        errors['monto'] = "El monto del abono es obligatorio."
        return None
    try:
        amount = Decimal(raw).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        errors['monto'] = "El monto del abono no es válido."
        return None
    if amount <= 0:
        errors['monto'] = "El monto del abono debe ser mayor a cero."
        return None
    return amount


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
        estado = (data.get('estado') or '').strip().lower()
        if estado not in ALLOWED_STATUS:
            return jsonify({"status": "error", "message": "El estado seleccionado no es válido."}), 400
        updated = model.ejecutar("update_status", order_id, estado)
        if not updated:
            return jsonify({"status": "error", "message": "Crédito no encontrado."}), 404
        if session.get('user_id'):

            pass
        return jsonify({"status": "success", "message": "Crédito modificado correctamente."})
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
            return jsonify({"status": "error", "message": "Errores de validación.", "errors": errors}), 400
        updated = model.ejecutar("update_dates", order_id, start, end)
        if not updated:
            return jsonify({"status": "error", "message": "Crédito no encontrado."}), 404
        if session.get('user_id'):

            pass
        return jsonify({"status": "success", "message": "Crédito modificado correctamente."})
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
        errors = {}
        amount = _parse_amount(data.get('monto'), errors)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validación.", "errors": errors}), 400
        result = model.ejecutar("register_payment", order_id, amount)
        if not result.get('ok'):
            return jsonify({"status": "error", "message": result.get('message', 'No se pudo registrar el abono.')}), result.get('status_code', 400)
        if session.get('user_id'):

            pass
        message = "Crédito pagado correctamente." if result.get('pagado') else "Abono registrado correctamente."
        return jsonify({
            "status": "success",
            "message": message,
            "data": {
                "monto_deuda": str(result.get('monto_deuda', 0)),
                "pagado": bool(result.get('pagado'))
            }
        })
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
        data = request.get_json() or {}
        errors = {}
        cliente_cedula = (data.get('cliente_cedula') or '').strip()
        if not cliente_cedula:
            errors['cliente_cedula'] = "La empresa es obligatoria."
        monto_raw = data.get('total')
        if monto_raw is None or str(monto_raw).strip() == '':
            errors['total'] = "El monto es obligatorio."
        else:
            try:
                total = Decimal(str(monto_raw).replace(',', '.')).quantize(Decimal("0.01"))
                if total <= 0:
                    errors['total'] = "El monto debe ser mayor a cero."
            except (InvalidOperation, ValueError):
                errors['total'] = "El monto no es válido."
        fecha_inicio = _parse_date(data.get('fecha_inicio'), 'fecha_inicio', errors)
        fecha_fin = _parse_date(data.get('fecha_fin'), 'fecha_fin', errors)
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            errors['fecha_fin'] = "La fecha fin no puede ser menor a la fecha inicio."
        if errors:
            return jsonify({"status": "error", "message": "Errores de validación.", "errors": errors}), 400
        result = model.ejecutar("create_credit", {
            'cliente_cedula': cliente_cedula,
            'total': total,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'observaciones': data.get('observaciones', '')
        })
        if not result.get('ok'):
            return jsonify({"status": "error", "message": result.get('message')}), 400
        if session.get('user_id'):

            pass
        return jsonify({"status": "success", "message": result.get('message'), "data": {"id": result.get('id')}})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
