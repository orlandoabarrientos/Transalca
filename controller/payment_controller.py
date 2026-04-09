from flask import Blueprint, request, jsonify, session
from model.payment_model import PaymentModel
from model.bitacora_model import BitacoraModel

payment_bp = Blueprint('payments', __name__)
model = PaymentModel()
bitacora = BitacoraModel()


@payment_bp.route('/pending', methods=['GET'])
def get_pending():
    try:
        return jsonify({"status": "success", "data": model.get_pending()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@payment_bp.route('/', methods=['GET'])
def get_all():
    try:
        estado = request.args.get('estado', None)
        return jsonify({"status": "success", "data": model.get_all(estado)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@payment_bp.route('/<int:comp_id>', methods=['GET'])
def get_one(comp_id):
    try:
        payment = model.get_by_id(comp_id)
        if payment:
            return jsonify({"status": "success", "data": payment})
        return jsonify({"status": "error", "message": "Comprobante no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@payment_bp.route('/<int:comp_id>/approve', methods=['POST'])
def approve(comp_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        result = model.approve(comp_id, session['user_id'])
        if result:
            bitacora.log_action(session['user_id'], 'MODIFICAR', 'PAGOS',
                f"Pago aprobado comprobante ID: {comp_id}", request.remote_addr)
            comp = model.get_by_id(comp_id)
            email_data = model.get_order_info_for_email(comp['orden_venta_id'])
            return jsonify({"status": "success", "message": "Pago aprobado", "email_data": email_data})
        return jsonify({"status": "error", "message": "Error al aprobar"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@payment_bp.route('/<int:comp_id>/reject', methods=['POST'])
def reject(comp_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        result = model.reject(comp_id, session['user_id'], data.get('observaciones', ''))
        if result:
            bitacora.log_action(session['user_id'], 'MODIFICAR', 'PAGOS',
                f"Pago rechazado comprobante ID: {comp_id}", request.remote_addr)
            return jsonify({"status": "success", "message": "Pago rechazado"})
        return jsonify({"status": "error", "message": "Error al rechazar"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
