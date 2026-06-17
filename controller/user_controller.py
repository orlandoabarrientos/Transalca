from flask import Blueprint, request, jsonify, session
from model.user_model import UserModel

from config.validation import normalize_cedula, normalize_email, ValidationError

user_bp = Blueprint('users', __name__)
model = UserModel()


@user_bp.route('/', methods=['GET'])
def get_all():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        return jsonify({"status": "success", "data": model.ejecutar("get_all", request.args.get('tipo', None))})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los usuarios."}), 500


@user_bp.route('/check-unique', methods=['POST'])
def check_unique():
    try:
        payload = request.get_json(silent=True) or {}
        field = (payload.get('field') or '').strip()
        value = payload.get('value') or ''
        exclude = payload.get('exclude') or None
        errors = {}
        if field == 'email':
            email = normalize_email(errors, value)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            cedula_exclude = (payload.get('cedula') or '').strip()
            if exclude:
                return jsonify({"status": "success", "exists": model.ejecutar("email_exists", email, exclude)})
            return jsonify({"status": "success", "exists": model.ejecutar("email_exists_globally", email, {"cliente_cedula": cedula_exclude})})
        if field == 'cedula':
            cedula, _, _ = normalize_cedula(errors, {'cedula': value})
            if errors:
                return jsonify({"status": "error", "message": errors['cedula']}), 400
            return jsonify({"status": "success", "exists": model.ejecutar("cedula_exists", cedula, exclude)})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_one(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        user = model.ejecutar("get_by_id", user_id)
        if user:
            user['roles'] = model.ejecutar("get_user_roles", user_id)
            return jsonify({"status": "success", "data": user})
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el usuario."}), 500

@user_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        user_id = model.ejecutar("create", request.get_json() or {})
        if user_id:
            return jsonify({"status": "success", "message": "Usuario registrado correctamente.", "id": user_id})
        return jsonify({"status": "error", "message": "No se pudo registrar el usuario."}), 500
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el usuario."}), 500


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        model.ejecutar("update_user", user_id, request.get_json() or {})
        return jsonify({"status": "success", "message": "Usuario modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el usuario."}), 500


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        result = model.ejecutar("soft_delete", user_id)
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
        model.ejecutar("update_status", user_id, estado)
        return jsonify({"status": "success", "message": "Usuario eliminado correctamente." if str(estado) == '0' else "Estado modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del usuario."}), 500


@user_bp.route('/search', methods=['GET'])
def search():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        query = request.args.get('q', '')
        return jsonify({"status": "success", "data": model.ejecutar("search", query[:80])})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo buscar usuarios."}), 500
