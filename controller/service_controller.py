from flask import Blueprint, request, jsonify, session
from model.service_model import ServiceModel
from model.bitacora_model import BitacoraModel
from config.validation import SELECT_TAMPER_MESSAGE, normalize_decimal, normalize_int, optional_text, require_text

service_bp = Blueprint('services', __name__)
model = ServiceModel()
bitacora = BitacoraModel()


def _validate_service(data):
    errors = {}
    clean = {}
    clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=200, allow_serial=False)
    clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=1000)
    clean['precio'] = normalize_decimal(errors, 'precio', data.get('precio'), 'El precio')
    clean['duracion_estimada'] = normalize_int(errors, 'duracion_estimada', data.get('duracion_estimada') or 60, 'La duracion', min_value=1, max_value=1440)
    clean['sucursal_id'] = data.get('sucursal_id') or None
    if clean['sucursal_id']:
        try:
            clean['sucursal_id'] = int(clean['sucursal_id'])
        except (TypeError, ValueError):
            errors['sucursal_id'] = SELECT_TAMPER_MESSAGE
        else:
            if not model.sucursal_exists(clean['sucursal_id']):
                errors['sucursal_id'] = SELECT_TAMPER_MESSAGE
    return clean, errors


@service_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/<int:sid>', methods=['GET'])
def get_one(sid):
    try:
        item = model.get_by_id(sid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Servicio no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el servicio."}), 500


@service_bp.route('/sucursal/<int:suc_id>', methods=['GET'])
def get_by_sucursal(suc_id):
    try:
        return jsonify({"status": "success", "data": model.get_by_sucursal(suc_id)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        clean, errors = _validate_service(data)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        sid = model.create(clean)
        bitacora.log_action(session['user_id'], 'CREAR', 'SERVICIOS',
            f"Servicio creado: {clean['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio registrado correctamente.", "id": sid})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el servicio."}), 500


@service_bp.route('/<int:sid>', methods=['PUT'])
def update(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        clean, errors = _validate_service(data)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        model.update_service(sid, clean)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'SERVICIOS',
            f"Servicio modificado ID: {sid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el servicio."}), 500


@service_bp.route('/<int:sid>', methods=['DELETE'])
def delete(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        model.soft_delete(sid)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'SERVICIOS',
            f"Servicio desactivado ID: {sid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el servicio."}), 500


@service_bp.route('/<int:sid>/toggle', methods=['PUT'])
def toggle(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        model.toggle_estado(sid)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'SERVICIOS',
            f"Estado cambiado servicio ID: {sid}", request.remote_addr)
        item = model.get_by_id(sid)
        msg = "Servicio reactivado correctamente." if item and item.get('estado') else "Servicio eliminado correctamente."
        return jsonify({"status": "success", "message": msg})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del servicio."}), 500
