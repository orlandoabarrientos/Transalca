from flask import Blueprint, request, jsonify, session
from model.service_model import ServiceModel
from model.bitacora_model import BitacoraModel

service_bp = Blueprint('services', __name__)
model = ServiceModel()
bitacora = BitacoraModel()


@service_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/<int:sid>', methods=['GET'])
def get_one(sid):
    try:
        item = model.get_by_id(sid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Servicio no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/sucursal/<int:suc_id>', methods=['GET'])
def get_by_sucursal(suc_id):
    try:
        return jsonify({"status": "success", "data": model.get_by_sucursal(suc_id)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/assignments', methods=['GET'])
def get_assignments():
    try:
        return jsonify({"status": "success", "data": model.get_assignments()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        try:
            precio = float(data.get('precio', 0))
            if precio <= 0:
                errors['precio'] = 'El precio debe ser mayor a 0'
        except (ValueError, TypeError):
            errors['precio'] = 'Precio invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        sid = model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'SERVICIOS',
            f"Servicio creado: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio creado", "id": sid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/<int:sid>', methods=['PUT'])
def update(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        try:
            precio = float(data.get('precio', 0))
            if precio <= 0:
                errors['precio'] = 'El precio debe ser mayor a 0'
        except (ValueError, TypeError):
            errors['precio'] = 'Precio invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_service(sid, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'SERVICIOS',
            f"Servicio modificado ID: {sid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/<int:sid>', methods=['DELETE'])
def delete(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(sid)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'SERVICIOS',
            f"Servicio desactivado ID: {sid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/assign', methods=['POST'])
def assign():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('servicio_id'):
            errors['servicio_id'] = 'Debe seleccionar un servicio'
        if not data.get('mecanico_id'):
            errors['mecanico_id'] = 'Debe seleccionar un mecanico'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        aid = model.assign_mechanic(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'SERVICIOS',
            f"Mecanico asignado a servicio", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico asignado", "id": aid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@service_bp.route('/assignment/<int:aid>/status', methods=['PUT'])
def update_assignment(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        model.update_assignment_status(aid, data['estado'])
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
