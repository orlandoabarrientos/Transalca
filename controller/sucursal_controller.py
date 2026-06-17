from flask import Blueprint, request, jsonify, session
from model.sucursal_model import SucursalModel

from config.validation import ValidationError, normalize_email, require_text

sucursal_bp = Blueprint('sucursales', __name__)
model = SucursalModel()


@sucursal_bp.route('/', methods=['GET'])
def get_all():
    try:
        data = model.ejecutar("get_all")
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/active', methods=['GET'])
def get_active():
    try:
        data = model.ejecutar("get_active")
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/check-unique', methods=['POST'])
def check_unique():
    try:
        payload = request.get_json(silent=True) or {}
        field = (payload.get('field') or '').strip()
        value = (payload.get('value') or '').strip()
        exclude = payload.get('exclude') or None
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value, required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            return jsonify({"status": "success", "exists": model.ejecutar("email_exists_globally", email, {"sucursal_id": exclude})})
        if field == 'nombre':
            errors = {}
            nombre = require_text(errors, 'nombre', value, 'El nombre', min_len=3, max_len=200, allow_serial=False)
            if errors:
                return jsonify({"status": "error", "message": errors['nombre']}), 400
            return jsonify({"status": "success", "exists": model.ejecutar("nombre_exists", nombre, exclude)})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@sucursal_bp.route('/<int:sid>', methods=['GET'])
def get_one(sid):
    try:
        item = model.ejecutar("get_by_id", sid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Sucursal no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        sid = model.ejecutar("create", request.get_json() or {})
        return jsonify({"status": "success", "message": "Sucursal registrada correctamente.", "id": sid})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/<int:sid>', methods=['PUT'])
def update(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.ejecutar("update_sucursal", sid, request.get_json() or {})
        return jsonify({"status": "success", "message": "Sucursal modificada correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/<int:sid>', methods=['DELETE'])
def delete(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.ejecutar("soft_delete", sid)


        return jsonify({"status": "success", "message": "Sucursal eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/<int:sid>/toggle', methods=['PUT'])
def toggle(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.ejecutar("toggle_estado", sid)


        return jsonify({"status": "success", "message": "Sucursal eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
