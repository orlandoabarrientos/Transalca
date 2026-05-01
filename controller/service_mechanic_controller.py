from flask import Blueprint, request, jsonify, session
from model.service_mechanic_model import ServiceMechanicModel
from model.bitacora_model import BitacoraModel
from model.commission_model import CommissionModel

service_mechanic_bp = Blueprint('service_mechanics', __name__)
model = ServiceMechanicModel()
bitacora = BitacoraModel()
commission_model = CommissionModel()


@service_mechanic_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_mechanic_bp.route('/<int:aid>', methods=['GET'])
def get_one(aid):
    try:
        item = model.get_by_id(aid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_mechanic_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('servicio_id'):
            errors['servicio_id'] = 'Debe seleccionar un servicio'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        aid = model.assign(data)
        message = 'Servicio registrado sin mecanico' if not (data.get('mecanico_cedula') or '').strip() else 'Mecanico asignado'
        bitacora.log_action(session['user_id'], 'CREAR', 'SERVICIO_MECANICO',
            f"Registro servicio mecanico ID: {aid}", request.remote_addr)
        return jsonify({"status": "success", "message": message, "id": aid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_mechanic_bp.route('/<int:aid>/mechanic', methods=['PUT'])
def update_mechanic(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip()
        if not mecanico_cedula:
            return jsonify({"status": "error", "message": "Debe seleccionar un mecanico"}), 400
        model.update_mechanic(aid, mecanico_cedula)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'SERVICIO_MECANICO',
            f"Mecanico actualizado en asignacion ID: {aid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico asignado correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_mechanic_bp.route('/<int:aid>/status', methods=['PUT'])
def update_status(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        model.update_status(aid, data['estado'])
        commission_id = None
        if data.get('estado') == 'completado':
            commission_id = commission_model.create_from_service(aid)
        response = {"status": "success", "message": "Estado actualizado"}
        if commission_id:
            response["commission_id"] = commission_id
        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
