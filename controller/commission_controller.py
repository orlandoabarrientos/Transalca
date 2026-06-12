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
        mecanico = request.args.get('mecanico')
        roles = [r.lower() for r in session.get('roles', [])]
        if 'mecanico' in roles:
            mecanico = session.get('user_cedula')
        if mecanico:
            return jsonify({"status": "success", "data": model.ejecutar("get_by_mecanico", mecanico)})
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@commission_bp.route('/<int:cid>', methods=['GET'])
def get_one(cid):
    try:
        auth = require_login()
        if auth:
            return auth
        c = model.ejecutar("get_by_id", cid)
        if not c:
            return jsonify({"status": "error", "message": "Comision no encontrada"}), 404
        if not mechanic_cedula_allowed(c.get('mecanico_cedula')):
            return deny()
        return jsonify({"status": "success", "data": c})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@commission_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        required = ['servicio_mecanico_id', 'precio_servicio']
        if not data or not all(data.get(k) for k in required):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        cid = model.ejecutar("create", data)
        return jsonify({"status": "success", "message": "Comision registrada", "id": cid}), 201
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@commission_bp.route('/auto/<int:sm_id>', methods=['POST'])
def auto_create(sm_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json(silent=True) or {}
        cid = model.ejecutar("create_from_service", sm_id, data.get('porcentaje_comision'))
        if not cid:
            return jsonify({"status": "error", "message": "No se pudo crear comision"}), 400
        return jsonify({"status": "success", "message": "Comision generada", "id": cid}), 201
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@commission_bp.route('/<int:sm_id>/percentage', methods=['PUT'])
def update_percentage(sm_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        try:
            porcentaje = float(data.get('porcentaje_comision'))
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Porcentaje de comision invalido"}), 400
        if porcentaje <= 0 or porcentaje > 100:
            return jsonify({"status": "error", "message": "El porcentaje debe estar entre 0 y 100"}), 400
        cid = model.ejecutar("set_percentage", sm_id, porcentaje)
        if not cid:
            return jsonify({"status": "error", "message": "El servicio no tiene mecanico asignado"}), 400
        return jsonify({"status": "success", "message": "Porcentaje de comision actualizado"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@commission_bp.route('/summary/<cedula>', methods=['GET'])
def summary(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not mechanic_cedula_allowed(cedula):
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_summary", cedula)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
