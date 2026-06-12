from flask import Blueprint, request, jsonify, session
from model.service_model import ServiceModel

from config.validation import SELECT_TAMPER_MESSAGE, normalize_decimal, normalize_int, optional_text, require_text

service_bp = Blueprint('services', __name__)
model = ServiceModel()



def _validate_service(data, current_id=None):
    errors = {}
    clean = {}
    clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=200, allow_serial=False)
    clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=1000)
    clean['precio'] = normalize_decimal(errors, 'precio', data.get('precio'), 'El precio')
    clean['duracion_estimada'] = normalize_int(errors, 'duracion_estimada', data.get('duracion_estimada') or 60, 'La duracion', min_value=1, max_value=1440)

    tipo = (data.get('tipo') or '').strip().lower()
    if not tipo:
        errors['tipo'] = 'El tipo de servicio es obligatorio.'
    elif tipo not in ('alineacion', 'rotacion', 'balanceo', 'cambio_aceite', 'general'):
        errors['tipo'] = SELECT_TAMPER_MESSAGE
    else:
        clean['tipo'] = tipo

    current = model.ejecutar("get_by_id", current_id) if current_id else None
    current_suc_ids = [int(v) for v in (current.get('sucursal_ids') or '').split(',') if v] if current else []

    raw_ids = data.get('sucursal_ids')
    if raw_ids is None:
        raw_ids = [data.get('sucursal_id')] if data.get('sucursal_id') else []
    if isinstance(raw_ids, str):
        raw_ids = [v for v in raw_ids.split(',') if v]
    clean['sucursal_ids'] = []
    for raw_id in raw_ids:
        try:
            sucursal_id = int(raw_id)
        except (TypeError, ValueError):
            errors['sucursal_id'] = SELECT_TAMPER_MESSAGE
        else:
            is_current_suc = sucursal_id in current_suc_ids
            if not is_current_suc and not model.ejecutar("sucursal_exists", sucursal_id):
                errors['sucursal_id'] = SELECT_TAMPER_MESSAGE
            elif sucursal_id not in clean['sucursal_ids']:
                clean['sucursal_ids'].append(sucursal_id)

    if not clean['sucursal_ids'] and not errors.get('sucursal_id'):
        errors['sucursal_id'] = 'Debe seleccionar al menos una sucursal.'

    return clean, errors


@service_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        value = request.args.get('value', '').strip()
        exclude = request.args.get('exclude', '').strip()
        if not value:
            return jsonify({"status": "success", "unique": True})
        exists = model.ejecutar("nombre_exists", value, exclude if exclude else None)
        return jsonify({"status": "success", "unique": not exists})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@service_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/<int:sid>', methods=['GET'])
def get_one(sid):
    try:
        item = model.ejecutar("get_by_id", sid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Servicio no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el servicio."}), 500


@service_bp.route('/sucursal/<int:suc_id>', methods=['GET'])
def get_by_sucursal(suc_id):
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_by_sucursal", suc_id)})
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
        existing = model.ejecutar("get_by_nombre", clean['nombre'])
        if existing:
            if existing['estado'] == 1:
                return jsonify({"status": "error", "message": "Ya existe un servicio con ese nombre.", "errors": {"nombre": "Ya existe un servicio con ese nombre."}}), 400
            else:
                model.ejecutar("update_service", existing['id'], clean)
                model.ejecutar("reactivar", existing['id'])

                return jsonify({"status": "success", "message": "Servicio registrado correctamente.", "id": existing['id']})
        sid = model.ejecutar("create", clean)


        return jsonify({"status": "success", "message": "Servicio registrado correctamente.", "id": sid})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el servicio."}), 500


@service_bp.route('/<int:sid>', methods=['PUT'])
def update(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        clean, errors = _validate_service(data, sid)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.ejecutar("nombre_exists", clean['nombre'], sid):
            return jsonify({"status": "error", "message": "Ya existe un servicio con ese nombre.", "errors": {"nombre": "Ya existe un servicio con ese nombre."}}), 400
        model.ejecutar("update_service", sid, clean)


        return jsonify({"status": "success", "message": "Servicio modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el servicio."}), 500


@service_bp.route('/<int:sid>', methods=['DELETE'])
def delete(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        model.ejecutar("soft_delete", sid)


        return jsonify({"status": "success", "message": "Servicio eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el servicio."}), 500


@service_bp.route('/<int:sid>/toggle', methods=['PUT'])
def toggle(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        model.ejecutar("toggle_estado", sid)


        item = model.ejecutar("get_by_id", sid)
        msg = "Servicio reactivado correctamente." if item and item.get('estado') else "Servicio eliminado correctamente."
        return jsonify({"status": "success", "message": msg})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del servicio."}), 500
