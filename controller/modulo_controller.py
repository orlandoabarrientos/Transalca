from flask import Blueprint, request, jsonify, session

from model.modulo_model import ModuloModel
from controller._guards import require_login, require_module, is_admin
from config.validation import ValidationError

modulo_bp = Blueprint('modulos', __name__)
model = ModuloModel()


def _filtered_sidebar():
    modules = model.ejecutar("get_sidebar_modules")
    if is_admin():
        return modules
    perms = session.get('permisos') or {}
    visible = []
    for item in modules:
        if item.get('publico') or (perms.get(item['nombre']) or {}).get('leer'):
            visible.append(item)
    return visible


@modulo_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_module('modulos', 'leer')
        if auth:
            return auth
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los modulos."}), 500


@modulo_bp.route('/sidebar', methods=['GET'])
def sidebar():
    try:
        auth = require_login()
        if auth:
            return auth
        return jsonify({"status": "success", "data": _filtered_sidebar()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el menu."}), 500


@modulo_bp.route('/permissions-list', methods=['GET'])
def permissions_list():
    try:
        auth = require_login()
        if auth:
            return auth
        return jsonify({"status": "success", "data": model.ejecutar("get_permission_modules")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los modulos."}), 500


@modulo_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        auth = require_module('modulos', 'leer')
        if auth:
            return auth
        field = (request.args.get('field') or 'nombre').strip()
        value = (request.args.get('value') or '').strip()
        exclude = request.args.get('exclude') or None
        if not value:
            return jsonify({"status": "success", "unique": True})
        if field == 'ruta':
            exists = model.ejecutar("ruta_exists", value, exclude)
        else:
            exists = model.ejecutar("nombre_exists", value.lower(), exclude)
        return jsonify({"status": "success", "unique": not exists})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@modulo_bp.route('/<int:modulo_id>', methods=['GET'])
def get_one(modulo_id):
    try:
        auth = require_module('modulos', 'leer')
        if auth:
            return auth
        item = model.ejecutar("get_by_id", modulo_id)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Modulo no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el modulo."}), 500


@modulo_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_module('modulos', 'crear')
        if auth:
            return auth
        model.ejecutar("create", request.get_json() or {})
        return jsonify({"status": "success", "message": "Modulo registrado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el modulo."}), 500


@modulo_bp.route('/<int:modulo_id>', methods=['PUT'])
def update(modulo_id):
    try:
        auth = require_module('modulos', 'actualizar')
        if auth:
            return auth
        model.ejecutar("update_modulo", modulo_id, request.get_json() or {})
        return jsonify({"status": "success", "message": "Modulo modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el modulo."}), 500


@modulo_bp.route('/<int:modulo_id>', methods=['DELETE'])
def delete(modulo_id):
    try:
        auth = require_module('modulos', 'eliminar')
        if auth:
            return auth
        result = model.ejecutar("soft_delete", modulo_id)
        if result is None:
            return jsonify({"status": "error", "message": "Modulo no encontrado."}), 404
        return jsonify({"status": "success", "message": "Modulo eliminado correctamente.", "estado": result})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el modulo."}), 500
