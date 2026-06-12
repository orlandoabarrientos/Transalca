from flask import Blueprint, request, jsonify, session
from model.service_mechanic_model import ServiceMechanicModel

from model.commission_model import CommissionModel
from config.constants import ESTADOS_SERVICIO_MECANICO
from config.validation import SELECT_TAMPER_MESSAGE, normalize_int, optional_text, validate_choice

service_mechanic_bp = Blueprint('service_mechanics', __name__)
model = ServiceMechanicModel()

commission_model = CommissionModel()

ESTADOS_REQUIEREN_DATOS = {'en_proceso', 'completado'}


def _missing_required_data(item, estado, mecanico_cedula=None):
    """Valida datos obligatorios antes de permitir un cambio de estado."""
    errors = {}
    if estado not in ESTADOS_REQUIEREN_DATOS:
        return errors
    mecanico = mecanico_cedula if mecanico_cedula is not None else (item or {}).get('mecanico_cedula')
    if not mecanico:
        errors['mecanico_cedula'] = 'Debe asignar un mecanico antes de cambiar el estado.'
    if not (item or {}).get('cliente_cedula'):
        errors['cliente_cedula'] = 'Debe asignar un cliente antes de cambiar el estado.'
    if not (item or {}).get('vehiculo_placa'):
        errors['vehiculo_placa'] = 'Debe asignar un vehiculo antes de cambiar el estado.'
    return errors


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
    estado_default = 'asignado' if mecanico_cedula else 'sin_asignar'
    estado = validate_choice(errors, 'estado', data.get('estado') or estado_default, ESTADOS_SERVICIO_MECANICO)
    fecha = (data.get('fecha') or '').strip().replace('T', ' ') or None

    current = model.ejecutar("get_by_id", current_id) if current_id else None

    if servicio_id:
        is_current_service = current and current.get('servicio_id') == servicio_id
        if not is_current_service and not model.ejecutar("service_exists", servicio_id):
            errors['servicio_id'] = SELECT_TAMPER_MESSAGE

    if mecanico_cedula:
        is_current_mechanic = current and current.get('mecanico_cedula') == mecanico_cedula
        if not is_current_mechanic and not model.ejecutar("mechanic_exists", mecanico_cedula):
            errors['mecanico_cedula'] = SELECT_TAMPER_MESSAGE

    if orden_venta_id and not model.ejecutar("order_exists", orden_venta_id):
        errors['orden_venta_id'] = 'La orden seleccionada no existe.'

    if estado in ESTADOS_REQUIEREN_DATOS and not errors:
        candidate = {
            'mecanico_cedula': mecanico_cedula,
            'cliente_cedula': cliente_cedula or (current or {}).get('cliente_cedula'),
            'vehiculo_placa': vehiculo_placa or (current or {}).get('vehiculo_placa'),
        }
        errors.update(_missing_required_data(candidate, estado, mecanico_cedula))
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
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios mecanicos"}), 500


@service_mechanic_bp.route('/<int:aid>', methods=['GET'])
def get_one(aid):
    try:
        item = model.ejecutar("get_by_id", aid)
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
        payload = request.get_json() or {}
        data, errors = _validate_assignment(payload)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        aid = model.ejecutar("assign", data)
        porcentaje = payload.get('porcentaje_comision')
        if porcentaje not in (None, '') and data.get('mecanico_cedula'):
            try:
                commission_model.ejecutar("set_percentage", aid, float(porcentaje))
            except (TypeError, ValueError):
                pass
        message = 'Servicio mecanico registrado correctamente'

        return jsonify({"status": "success", "message": message, "id": aid})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el servicio mecanico"}), 500


@service_mechanic_bp.route('/<int:aid>/mechanic', methods=['PUT'])
def update_mechanic(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.ejecutar("get_by_id", aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        data = request.get_json() or {}
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip()
        if not mecanico_cedula or not model.ejecutar("mechanic_exists", mecanico_cedula):
            return jsonify({"status": "error", "message": SELECT_TAMPER_MESSAGE, "errors": {"mecanico_cedula": SELECT_TAMPER_MESSAGE}}), 400
        model.ejecutar("update_mechanic", aid, mecanico_cedula)
        porcentaje = data.get('porcentaje_comision')
        if porcentaje not in (None, ''):
            try:
                commission_model.ejecutar("set_percentage", aid, float(porcentaje))
            except (TypeError, ValueError):
                pass

        return jsonify({"status": "success", "message": "Mecanico asignado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo asignar el mecanico"}), 500


@service_mechanic_bp.route('/<int:aid>/status', methods=['PUT'])
def update_status(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        item = model.ejecutar("get_by_id", aid)
        if not item:
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        data = request.get_json() or {}
        errors = {}
        estado = validate_choice(errors, 'estado', data.get('estado'), ESTADOS_SERVICIO_MECANICO)
        if not errors:
            errors.update(_missing_required_data(item, estado))
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.ejecutar("update_status", aid, estado)
        commission_id = None
        if estado == 'completado':
            porcentaje = data.get('porcentaje_comision')
            try:
                porcentaje = float(porcentaje) if porcentaje not in (None, '') else None
            except (TypeError, ValueError):
                porcentaje = None
            commission_id = commission_model.ejecutar("create_from_service", aid, porcentaje)
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
        if not model.ejecutar("get_by_id", aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        payload = request.get_json() or {}
        data, errors = _validate_assignment(payload, aid)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.ejecutar("update_assignment", aid, data)
        porcentaje = payload.get('porcentaje_comision')
        if porcentaje not in (None, '') and data.get('mecanico_cedula'):
            try:
                commission_model.ejecutar("set_percentage", aid, float(porcentaje))
            except (TypeError, ValueError):
                pass

        return jsonify({"status": "success", "message": "Servicio mecanico modificado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el servicio mecanico"}), 500


@service_mechanic_bp.route('/<int:aid>', methods=['DELETE'])
def delete(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.ejecutar("get_by_id", aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        model.ejecutar("delete_assignment", aid)

        return jsonify({"status": "success", "message": "Servicio mecanico eliminado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el servicio mecanico"}), 500
