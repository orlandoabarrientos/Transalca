from flask import Blueprint, request, jsonify, session
from model.commission_model import CommissionModel
from controller._guards import deny, is_employee, require_login

commission_bp = Blueprint('commission_bp', __name__)
model = CommissionModel()


def mechanic_cedula_allowed(cedula):
    if is_employee():
        roles = [r.lower() for r in session.get('roles', [])]
        if 'mecanico' in roles and session.get('user_cedula') != cedula:
            return False
        return True
    return False


@commission_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        estado = request.args.get('estado_pago')
        mecanico = request.args.get('mecanico')
        roles = [r.lower() for r in session.get('roles', [])]
        if 'mecanico' in roles:
            mecanico = session.get('user_cedula')
        if mecanico:
            return jsonify({"status": "success", "data": model.get_by_mecanico(mecanico, estado)})
        return jsonify({"status": "success", "data": model.get_all(estado)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@commission_bp.route('/<int:cid>', methods=['GET'])
def get_one(cid):
    try:
        auth = require_login()
        if auth:
            return auth
        c = model.get_by_id(cid)
        if not c:
            return jsonify({"status": "error", "message": "Comision no encontrada"}), 404
        if not mechanic_cedula_allowed(c.get('mecanico_cedula')):
            return deny()
        return jsonify({"status": "success", "data": c})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@commission_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        required = ['mecanico_cedula', 'servicio_mecanico_id', 'orden_venta_id', 'precio_servicio']
        if not data or not all(data.get(k) for k in required):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        cid = model.create(data)
        return jsonify({"status": "success", "message": "Comision registrada", "id": cid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@commission_bp.route('/auto/<int:sm_id>', methods=['POST'])
def auto_create(sm_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        cid = model.create_from_service(sm_id)
        if not cid:
            return jsonify({"status": "error", "message": "No se pudo crear comision"}), 400
        return jsonify({"status": "success", "message": "Comision generada", "id": cid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@commission_bp.route('/<int:cid>/pay', methods=['PUT'])
def mark_paid(cid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.mark_paid(cid)
        return jsonify({"status": "success", "message": "Comision marcada como pagada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@commission_bp.route('/<int:cid>/cancel', methods=['PUT'])
def mark_cancelled(cid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.mark_cancelled(cid)
        return jsonify({"status": "success", "message": "Comision anulada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@commission_bp.route('/summary/<cedula>', methods=['GET'])
def summary(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not mechanic_cedula_allowed(cedula):
            return deny()
        return jsonify({"status": "success", "data": model.get_summary(cedula)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
