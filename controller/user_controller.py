from flask import Blueprint, request, jsonify, session
from model.user_model import UserModel

from config.validation import normalize_cedula, normalize_email, normalize_phone, optional_text, require_text, validate_choice, SELECT_TAMPER_MESSAGE
import re

user_bp = Blueprint('users', __name__)
model = UserModel()


PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'
TIPOS_USUARIO = ['cliente', 'empleado']


def _validate_user(data, require_password=False, current_id=None):
    errors = {}
    cedula, cedula_prefijo, _ = normalize_cedula(errors, data)
    clean = {
        'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=60, person=True),
        'apellido': require_text(errors, 'apellido', data.get('apellido'), 'El apellido', min_len=2, max_len=60, person=True),
        'cedula': cedula,
        'cedula_prefijo': cedula_prefijo,
        'email': normalize_email(errors, data.get('email')),
        'telefono': normalize_phone(errors, data.get('telefono'), required=False),
        'direccion': optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=40),
        'tipo': validate_choice(errors, 'tipo', data.get('tipo') or 'empleado', TIPOS_USUARIO)
    }

    current = model.get_by_id(current_id) if current_id else None
    current_roles = model.get_user_roles(current_id) if current_id else []
    current_role_ids = [r['id'] for r in current_roles]

    rol_id = data.get('rol_id')
    if rol_id in (None, '', 0, '0'):
        errors['rol_id'] = "El rol es obligatorio."
    else:
        try:
            clean['rol_id'] = int(rol_id)
        except (TypeError, ValueError):
            errors['rol_id'] = SELECT_TAMPER_MESSAGE
        else:
            is_current_rol = clean['rol_id'] in current_role_ids
            if not is_current_rol and not model.role_exists(clean['rol_id']):
                errors['rol_id'] = SELECT_TAMPER_MESSAGE
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
        existing_by_cedula = model.get_by_cedula(data['cedula'])
        existing_by_email = model.get_by_email(data['email'])
        if existing_by_cedula and existing_by_cedula['estado'] == 1:
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        if existing_by_email and existing_by_email['estado'] == 1:
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400

        existing = existing_by_cedula or existing_by_email
        if existing:
            email_exclude = {"usuario_id": existing['id'], "cliente_cedula": data['cedula']}
            if model.email_exists_globally(data['email'], email_exclude):
                return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400

            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(data['password'])
            update_data = {
                'nombre': data['nombre'],
                'apellido': data['apellido'],
                'cedula': data['cedula'],
                'cedula_prefijo': data['cedula_prefijo'],
                'email': data['email'],
                'telefono': data.get('telefono'),
                'direccion': data.get('direccion'),
                'tipo': data['tipo']
            }
            model.update_info(existing['id'], update_data)
            model.update("mantenimiento", "UPDATE usuarios SET password_hash = %s, estado = 1 WHERE id = %s", (password_hash, existing['id']))

            current_roles = model.get_user_roles(existing['id'])
            for role in current_roles:
                model.remove_role(existing['id'], role['id'])
            if data.get('rol_id'):
                model.assign_role(existing['id'], data['rol_id'])


            return jsonify({"status": "success", "message": "Usuario registrado correctamente.", "id": existing['id']})

        email_exclude = {"cliente_cedula": data['cedula']} if data.get('tipo') == 'cliente' else {}
        if model.email_exists_globally(data['email'], email_exclude):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        user_id = model.create(data)
        if user_id:
            if data.get('rol_id'):
                model.assign_role(user_id, data['rol_id'])

            return jsonify({"status": "success", "message": "Usuario registrado correctamente.", "id": user_id})
        return jsonify({"status": "error", "message": "No se pudo registrar el usuario."}), 500
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el usuario."}), 500


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data, errors = _validate_user(request.get_json() or {}, require_password=False, current_id=user_id)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.email_exists(data['email'], user_id):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        if model.cedula_exists(data['cedula'], user_id):
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        # Prevent role change for the last active administrator
        current_roles = model.get_user_roles(user_id)
        was_admin = any(r['nombre'] == 'Administrador' for r in current_roles)
        if was_admin:
            new_rol_id = data.get('rol_id')
            new_role_info = model.fetch_one("mantenimiento", "SELECT nombre FROM roles WHERE id = %s", (new_rol_id,))
            is_new_admin = new_role_info and new_role_info['nombre'] == 'Administrador'
            if not is_new_admin:
                admin_count = model.fetch_one("mantenimiento",
                    "SELECT COUNT(*) as total FROM usuario_rol ur INNER JOIN roles r ON ur.rol_id = r.id INNER JOIN usuarios u ON ur.usuario_id = u.id WHERE r.nombre = 'Administrador' AND u.estado = 1")
                if admin_count and admin_count['total'] <= 1:
                    return jsonify({"status": "error", "message": "No se puede cambiar el rol del último administrador activo.", "errors": {"rol_id": "No se puede cambiar el rol del último administrador activo."}}), 400

        model.update_info(user_id, data)
        for role in current_roles:
            model.remove_role(user_id, role['id'])
        if data.get('rol_id'):
            model.assign_role(user_id, data['rol_id'])

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
