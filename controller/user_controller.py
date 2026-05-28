from flask import Blueprint, request, jsonify, session
from model.user_model import UserModel
from model.bitacora_model import BitacoraModel
from config.validation import normalize_cedula, normalize_email, normalize_phone, optional_text, require_text, validate_choice, SELECT_TAMPER_MESSAGE
import re

user_bp = Blueprint('users', __name__)
model = UserModel()
bitacora = BitacoraModel()

PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'
TIPOS_USUARIO = ['cliente', 'empleado']


def _validate_user(data, require_password=False):
    errors = {}
    cedula, cedula_prefijo, _ = normalize_cedula(errors, data)
    clean = {
        'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=60, person=True),
        'apellido': require_text(errors, 'apellido', data.get('apellido'), 'El apellido', min_len=2, max_len=60, person=True),
        'cedula': cedula,
        'cedula_prefijo': cedula_prefijo,
        'email': normalize_email(errors, data.get('email')),
        'telefono': normalize_phone(errors, data.get('telefono'), required=False),
        'direccion': optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=255),
        'tipo': validate_choice(errors, 'tipo', data.get('tipo') or 'empleado', TIPOS_USUARIO)
    }
    rol_id = data.get('rol_id')
    if rol_id not in (None, ''):
        try:
            clean['rol_id'] = int(rol_id)
        except (TypeError, ValueError):
            errors['rol_id'] = SELECT_TAMPER_MESSAGE
        else:
            if not model.role_exists(clean['rol_id']):
                errors['rol_id'] = SELECT_TAMPER_MESSAGE
    else:
        clean['rol_id'] = None
    if require_password:
        password = data.get('password') or ''
        if not re.match(PASSWORD_REGEX, password):
            errors['password'] = 'La contrasena debe tener minimo 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial.'
        clean['password'] = password
    return clean, errors


@user_bp.route('/', methods=['GET'])
def get_all():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        tipo = request.args.get('tipo', None)
        if tipo and tipo not in TIPOS_USUARIO:
            return jsonify({"status": "error", "message": SELECT_TAMPER_MESSAGE}), 400
        return jsonify({"status": "success", "data": model.get_all(tipo)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los usuarios."}), 500


@user_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        field = (request.args.get('field') or '').strip()
        value = request.args.get('value') or ''
        exclude = request.args.get('exclude') or None
        errors = {}
        if field == 'email':
            email = normalize_email(errors, value)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            cedula_exclude = (request.args.get('cedula') or '').strip()
            if exclude:
                return jsonify({"status": "success", "exists": model.email_exists(email, exclude)})
            return jsonify({"status": "success", "exists": model.email_exists_globally(email, {"cliente_cedula": cedula_exclude})})
        if field == 'cedula':
            cedula, _, _ = normalize_cedula(errors, {'cedula': value})
            if errors:
                return jsonify({"status": "error", "message": errors['cedula']}), 400
            return jsonify({"status": "success", "exists": model.cedula_exists(cedula, exclude)})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_one(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        user = model.get_by_id(user_id)
        if user:
            user['roles'] = model.get_user_roles(user_id)
            return jsonify({"status": "success", "data": user})
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el usuario."}), 500


@user_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data, errors = _validate_user(request.get_json() or {}, require_password=True)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        email_exclude = {"cliente_cedula": data['cedula']} if data.get('tipo') == 'cliente' else {}
        if model.email_exists_globally(data['email'], email_exclude):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        if model.cedula_exists(data['cedula']):
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        user_id = model.create(data)
        if user_id:
            if data.get('rol_id'):
                model.assign_role(user_id, data['rol_id'])
            bitacora.log_action(session['user_id'], 'CREAR', 'USUARIOS', f"Usuario creado: {data['nombre']} {data['apellido']}", request.remote_addr)
            return jsonify({"status": "success", "message": "Usuario registrado correctamente.", "id": user_id})
        return jsonify({"status": "error", "message": "No se pudo registrar el usuario."}), 500
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el usuario."}), 500


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data, errors = _validate_user(request.get_json() or {}, require_password=False)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.email_exists(data['email'], user_id):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        if model.cedula_exists(data['cedula'], user_id):
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        model.update_info(user_id, data)
        current_roles = model.get_user_roles(user_id)
        for role in current_roles:
            model.remove_role(user_id, role['id'])
        if data.get('rol_id'):
            model.assign_role(user_id, data['rol_id'])
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'USUARIOS', f"Usuario modificado ID: {user_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Usuario modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el usuario."}), 500


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        result = model.soft_delete(user_id)
        if result is False:
            return jsonify({"status": "error", "message": "No se puede eliminar al ultimo administrador."}), 400
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'USUARIOS', f"Usuario eliminado ID: {user_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Usuario eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el usuario."}), 500


@user_bp.route('/<int:user_id>/status', methods=['PUT'])
def toggle_status(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        estado = data.get('estado')
        if estado not in (0, 1, '0', '1'):
            return jsonify({"status": "error", "message": SELECT_TAMPER_MESSAGE}), 400
        estado = int(estado)
        model.update_status(user_id, estado)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'USUARIOS', f"Estado de usuario cambiado ID: {user_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Usuario eliminado correctamente." if estado == 0 else "Estado modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del usuario."}), 500


@user_bp.route('/search', methods=['GET'])
def search():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        query = request.args.get('q', '')
        return jsonify({"status": "success", "data": model.search(query[:80])})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo buscar usuarios."}), 500
