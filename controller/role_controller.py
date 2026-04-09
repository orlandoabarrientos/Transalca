from flask import Blueprint, request, jsonify, session
from model.role_model import RoleModel
from model.bitacora_model import BitacoraModel

role_bp = Blueprint('roles', __name__)
model = RoleModel()
bitacora = BitacoraModel()


@role_bp.route('/', methods=['GET'])
def get_all():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@role_bp.route('/<int:role_id>', methods=['GET'])
def get_one(role_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        role = model.get_by_id(role_id)
        if role:
            role['permisos'] = model.get_permissions(role_id)
            return jsonify({"status": "success", "data": role})
        return jsonify({"status": "error", "message": "Rol no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@role_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        role_id = model.create(data)
        if data.get('permisos'):
            model.save_all_permissions(role_id, data['permisos'])
        bitacora.log_action(session['user_id'], 'CREAR', 'ROLES',
            f"Rol creado: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Rol creado", "id": role_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@role_bp.route('/<int:role_id>', methods=['PUT'])
def update(role_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_role(role_id, data)
        if data.get('permisos'):
            model.save_all_permissions(role_id, data['permisos'])
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'ROLES',
            f"Rol modificado ID: {role_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Rol actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@role_bp.route('/<int:role_id>', methods=['DELETE'])
def delete(role_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        result = model.soft_delete(role_id)
        if result is False:
            return jsonify({"status": "error", "message": "No se puede desactivar el rol Administrador"}), 400
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'ROLES',
            f"Rol desactivado ID: {role_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Rol desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@role_bp.route('/<int:role_id>/permissions', methods=['GET'])
def get_permissions(role_id):
    try:
        return jsonify({"status": "success", "data": model.get_permissions(role_id)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@role_bp.route('/<int:role_id>/permissions', methods=['POST'])
def save_permissions(role_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        model.save_all_permissions(role_id, data.get('permisos', []))
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'ROLES',
            f"Permisos actualizados para rol ID: {role_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Permisos actualizados"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@role_bp.route('/modules', methods=['GET'])
def get_modules():
    try:
        return jsonify({"status": "success", "data": model.get_modules()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
