from flask import Blueprint, request, jsonify, session
from model.sucursal_model import SucursalModel

from config.validation import normalize_email, normalize_phone, optional_text, require_text

sucursal_bp = Blueprint('sucursales', __name__)
model = SucursalModel()



def _validate_sucursal(data):
    errors = {}
    clean = {
        'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=200, allow_serial=False),
        'direccion': optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=40),
        'telefono': normalize_phone(errors, data.get('telefono'), required=False),
        'email': normalize_email(errors, data.get('email'), required=False)
    }
    return clean, errors


@sucursal_bp.route('/', methods=['GET'])
def get_all():
    try:
        data = model.get_all()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/active', methods=['GET'])
def get_active():
    try:
        data = model.get_active()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        field = (request.args.get('field') or '').strip()
        value = (request.args.get('value') or '').strip()
        exclude = request.args.get('exclude') or None
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value, required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            return jsonify({"status": "success", "exists": model.email_exists_globally(email, {"sucursal_id": exclude})})
        if field == 'nombre':
            errors = {}
            nombre = require_text(errors, 'nombre', value, 'El nombre', min_len=3, max_len=200, allow_serial=False)
            if errors:
                return jsonify({"status": "error", "message": errors['nombre']}), 400
            return jsonify({"status": "success", "exists": model.nombre_exists(nombre, exclude)})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@sucursal_bp.route('/<int:sid>', methods=['GET'])
def get_one(sid):
    try:
        item = model.get_by_id(sid)
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
        data, errors = _validate_sucursal(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        existing = model.get_by_nombre(data['nombre'])
        if existing:
            if existing['estado'] == 1:
                return jsonify({"status": "error", "message": "Ya existe una sucursal con ese nombre.", "errors": {"nombre": "Ya existe una sucursal con ese nombre."}}), 400
            else:
                model.update_sucursal(existing['id'], data)
                model.update("transalca", "UPDATE sucursales SET estado = 1 WHERE id = %s", (existing['id'],))

                return jsonify({"status": "success", "message": "Sucursal registrada correctamente.", "id": existing['id']})
        if data.get('email') and model.email_exists_globally(data['email']):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        sid = model.create(data)


        return jsonify({"status": "success", "message": "Sucursal registrada correctamente.", "id": sid})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/<int:sid>', methods=['PUT'])
def update(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data, errors = _validate_sucursal(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.nombre_exists(data['nombre'], sid):
            return jsonify({"status": "error", "message": "Ya existe una sucursal con ese nombre.", "errors": {"nombre": "Ya existe una sucursal con ese nombre."}}), 400
        if data.get('email') and model.email_exists_globally(data['email'], {"sucursal_id": sid}):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        model.update_sucursal(sid, data)


        return jsonify({"status": "success", "message": "Sucursal modificada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/<int:sid>', methods=['DELETE'])
def delete(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(sid)


        return jsonify({"status": "success", "message": "Sucursal eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@sucursal_bp.route('/<int:sid>/toggle', methods=['PUT'])
def toggle(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.toggle_estado(sid)


        return jsonify({"status": "success", "message": "Sucursal eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
