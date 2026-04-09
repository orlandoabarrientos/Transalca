from flask import Blueprint, request, jsonify, session
from model.user_model import UserModel
from model.bitacora_model import BitacoraModel
import re

user_bp = Blueprint('users', __name__)
model = UserModel()
bitacora = BitacoraModel()

PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'


@user_bp.route('/', methods=['GET'])
def get_all():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        tipo = request.args.get('tipo', None)
        users = model.get_all(tipo)
        return jsonify({"status": "success", "data": users})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_one(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        user = model.get_by_id(user_id)
        if user:
            user['roles'] = model.get_user_roles(user_id)
            return jsonify({"status": "success", "data": user})
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@user_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        if not data.get('apellido') or len(data['apellido'].strip()) < 2:
            errors['apellido'] = 'El apellido debe tener al menos 2 caracteres'
        if not data.get('cedula') or len(data['cedula'].strip()) < 5:
            errors['cedula'] = 'La cedula debe tener al menos 5 caracteres'
        if not data.get('email') or not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')):
            errors['email'] = 'Ingrese un correo valido'
        if not data.get('password') or not re.match(PASSWORD_REGEX, data.get('password', '')):
            errors['password'] = 'Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero, 1 especial'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.email_exists(data['email'].strip()):
            return jsonify({"status": "error", "message": "El correo ya existe", "errors": {"email": "El correo ya existe"}}), 400
        if model.cedula_exists(data['cedula'].strip()):
            return jsonify({"status": "error", "message": "La cedula ya existe", "errors": {"cedula": "La cedula ya existe"}}), 400
        user_id = model.create(data)
        if user_id:
            if data.get('rol_id'):
                model.assign_role(user_id, data['rol_id'])
            bitacora.log_action(session['user_id'], 'CREAR', 'USUARIOS',
                f"Usuario creado: {data['nombre']} {data['apellido']}", request.remote_addr)
            return jsonify({"status": "success", "message": "Usuario creado", "id": user_id})
        return jsonify({"status": "error", "message": "Error al crear"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        if not data.get('apellido') or len(data['apellido'].strip()) < 2:
            errors['apellido'] = 'El apellido debe tener al menos 2 caracteres'
        if data.get('email') and not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')):
            errors['email'] = 'Ingrese un correo valido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if data.get('email') and model.email_exists(data['email'].strip(), user_id):
            return jsonify({"status": "error", "message": "El correo ya existe", "errors": {"email": "El correo ya existe"}}), 400
        model.update_info(user_id, data)
        if data.get('rol_id'):
            current_roles = model.get_user_roles(user_id)
            for role in current_roles:
                model.remove_role(user_id, role['id'])
            model.assign_role(user_id, data['rol_id'])
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'USUARIOS',
            f"Usuario modificado ID: {user_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Usuario actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        result = model.soft_delete(user_id)
        if result is False:
            return jsonify({"status": "error", "message": "No se puede desactivar al ultimo administrador"}), 400
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'USUARIOS',
            f"Usuario desactivado ID: {user_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Usuario desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@user_bp.route('/<int:user_id>/status', methods=['PUT'])
def toggle_status(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        model.update_status(user_id, data.get('estado', 1))
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'USUARIOS',
            f"Estado de usuario cambiado ID: {user_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@user_bp.route('/<int:user_id>/role', methods=['POST'])
def assign_role(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        model.assign_role(user_id, data['rol_id'])
        return jsonify({"status": "success", "message": "Rol asignado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@user_bp.route('/search', methods=['GET'])
def search():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        query = request.args.get('q', '')
        return jsonify({"status": "success", "data": model.search(query)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
