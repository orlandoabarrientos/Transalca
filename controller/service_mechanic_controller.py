from flask import Blueprint, request, jsonify, session
from model.service_mechanic_model import ServiceMechanicModel
# from model.bitacora_model import BitacoraModel
from model.commission_model import CommissionModel
from config.constants import ESTADOS_SERVICIO_MECANICO
from config.validation import SELECT_TAMPER_MESSAGE, normalize_int, optional_text, validate_choice

service_mechanic_bp = Blueprint('service_mechanics', __name__)
model = ServiceMechanicModel()
# bitacora = BitacoraModel()
commission_model = CommissionModel()


def _validate_assignment(data, current_id=None):
    errors = {}
    servicio_id = normalize_int(errors, 'servicio_id', data.get('servicio_id'), 'El servicio')
    orden_venta_id = None
    if data.get('orden_venta_id') not in (None, ''):
        orden_venta_id = normalize_int(errors, 'orden_venta_id', data.get('orden_venta_id'), 'La orden')
    mecanico_cedula = (data.get('mecanico_cedula') or '').strip() or None
    observaciones = optional_text(errors, 'observaciones', data.get('observaciones'), 'Las observaciones', max_len=255, allow_serial=True)
    cliente_cedula = (data.get('cliente_cedula') or '').strip() or None
    vehiculo_placa = (data.get('vehiculo_placa') or '').strip().upper() or None
    estado = validate_choice(errors, 'estado', data.get('estado') or 'asignado', ESTADOS_SERVICIO_MECANICO)
    fecha = (data.get('fecha') or '').strip().replace('T', ' ') or None

    current = model.get_by_id(current_id) if current_id else None

    if servicio_id:
        is_current_service = current and current.get('servicio_id') == servicio_id
        if not is_current_service and not model.service_exists(servicio_id):
            errors['servicio_id'] = SELECT_TAMPER_MESSAGE
            
    if mecanico_cedula:
        is_current_mechanic = current and current.get('mecanico_cedula') == mecanico_cedula
        if not is_current_mechanic and not model.mechanic_exists(mecanico_cedula):
            errors['mecanico_cedula'] = SELECT_TAMPER_MESSAGE
            
    if orden_venta_id and not model.order_exists(orden_venta_id):
        errors['orden_venta_id'] = 'La orden seleccionada no existe.'
    return {
        'servicio_id': servicio_id,
        'mecanico_cedula': mecanico_cedula,
        'orden_venta_id': orden_venta_id,
        'observaciones': observaciones,
        'cliente_cedula': cliente_cedula,
        'vehiculo_placa': vehiculo_placa,
        'estado': estado,
        'fecha': fecha
    }, errors


@service_mechanic_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios mecanicos"}), 500


@service_mechanic_bp.route('/<int:aid>', methods=['GET'])
def get_one(aid):
    try:
        item = model.get_by_id(aid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar la asignacion"}), 500


@service_mechanic_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data, errors = _validate_assignment(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        aid = model.assign(data)
        message = 'Servicio mecanico registrado correctamente'
        # bitacora.log_action(session['user_id'], 'CREAR', 'SERVICIO_MECANICO', f"Registro servicio mecanico ID: {aid}", request.remote_addr)
        return jsonify({"status": "success", "message": message, "id": aid})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el servicio mecanico"}), 500


@service_mechanic_bp.route('/<int:aid>/mechanic', methods=['PUT'])
def update_mechanic(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.get_by_id(aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        data = request.get_json() or {}
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip()
        if not mecanico_cedula or not model.mechanic_exists(mecanico_cedula):
            return jsonify({"status": "error", "message": SELECT_TAMPER_MESSAGE, "errors": {"mecanico_cedula": SELECT_TAMPER_MESSAGE}}), 400
        model.update_mechanic(aid, mecanico_cedula)
        # bitacora.log_action(session['user_id'], 'MODIFICAR', 'SERVICIO_MECANICO', f"Mecanico actualizado en asignacion ID: {aid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico asignado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo asignar el mecanico"}), 500


@service_mechanic_bp.route('/<int:aid>/status', methods=['PUT'])
def update_status(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.get_by_id(aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        data = request.get_json() or {}
        errors = {}
        estado = validate_choice(errors, 'estado', data.get('estado'), ESTADOS_SERVICIO_MECANICO)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_status(aid, estado)
        commission_id = None
        if estado == 'completado':
            commission_id = commission_model.create_from_service(aid)
        response = {"status": "success", "message": "Estado modificado correctamente"}
        if commission_id:
            response["commission_id"] = commission_id
        return jsonify(response)
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el estado"}), 500


@service_mechanic_bp.route('/<int:aid>', methods=['PUT'])
def update(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.get_by_id(aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        data, errors = _validate_assignment(request.get_json() or {}, aid)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_assignment(aid, data)
        # bitacora.log_action(session['user_id'], 'MODIFICAR', 'SERVICIO_MECANICO', f"Servicio mecanico modificado ID: {aid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio mecanico modificado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el servicio mecanico"}), 500


@service_mechanic_bp.route('/<int:aid>', methods=['DELETE'])
def delete(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.get_by_id(aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        model.delete_assignment(aid)
        # bitacora.log_action(session['user_id'], 'ELIMINAR', 'SERVICIO_MECANICO', f"Servicio mecanico eliminado ID: {aid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Servicio mecanico eliminado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el servicio mecanico"}), 500
