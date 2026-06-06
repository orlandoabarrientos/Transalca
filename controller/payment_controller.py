from flask import Blueprint, request, jsonify, session
from model.payment_model import PaymentModel
from model.notification_model import NotificationModel

from config.validation import optional_text

payment_bp = Blueprint('payments', __name__)
model = PaymentModel()
notification_model = NotificationModel()



@payment_bp.route('/pending', methods=['GET'])
def get_pending():
    try:
        return jsonify({"status": "success", "data": model.get_pending()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los pagos pendientes"}), 500


@payment_bp.route('/', methods=['GET'])
def get_all():
    try:
        estado = request.args.get('estado', None)
        return jsonify({"status": "success", "data": model.get_all(estado)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los pagos"}), 500


@payment_bp.route('/<int:comp_id>', methods=['GET'])
def get_one(comp_id):
    try:
        payment = model.get_by_id(comp_id)
        if payment:
            return jsonify({"status": "success", "data": payment})
        return jsonify({"status": "error", "message": "Comprobante no encontrado"}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el comprobante"}), 500


@payment_bp.route('/<int:comp_id>/approve', methods=['POST'])
def approve(comp_id):
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.get_by_id(comp_id):
            return jsonify({"status": "error", "message": "Comprobante no encontrado"}), 404
        result = model.approve(comp_id, session['user_cedula'])
        if result:


            comp = model.get_by_id(comp_id)
            if comp:
                notification_model.notify_payment_status(comp.get('cliente_cedula'), comp.get('orden_venta_id'), True)
            email_data = model.get_order_info_for_email(comp['orden_venta_id']) if comp else None
            return jsonify({"status": "success", "message": "Pago verificado correctamente", "email_data": email_data})
        return jsonify({"status": "error", "message": "No se pudo verificar el pago"}), 500
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo verificar el pago"}), 500


@payment_bp.route('/<int:comp_id>/reject', methods=['POST'])
def reject(comp_id):
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.get_by_id(comp_id):
            return jsonify({"status": "error", "message": "Comprobante no encontrado"}), 404
        data = request.get_json() or {}
        errors = {}
        observaciones = optional_text(errors, 'observaciones', data.get('observaciones'), 'El motivo', max_len=255, allow_serial=True)
        if not observaciones:
            errors['observaciones'] = 'El motivo es obligatorio.'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        result = model.reject(comp_id, session['user_cedula'], observaciones)
        if result:


            comp = model.get_by_id(comp_id)
            if comp:
                notification_model.notify_payment_status(comp.get('cliente_cedula'), comp.get('orden_venta_id'), False, observaciones)
            return jsonify({"status": "success", "message": "Pago rechazado correctamente"})
        return jsonify({"status": "error", "message": "No se pudo rechazar el pago"}), 500
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo rechazar el pago"}), 500
