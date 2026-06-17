from flask import Blueprint, request, jsonify, session
from model.service_mechanic_model import ServiceMechanicModel

from model.commission_model import CommissionModel
from config.validation import ValidationError

service_mechanic_bp = Blueprint('service_mechanics', __name__)
model = ServiceMechanicModel()

commission_model = CommissionModel()


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
        aid = model.ejecutar("assign", payload)
        porcentaje = payload.get('porcentaje_comision')
        if porcentaje not in (None, '') and (payload.get('mecanico_cedula') or '').strip():
            try:
                commission_model.ejecutar("set_percentage", aid, float(porcentaje))
            except (TypeError, ValueError):
                pass
        return jsonify({"status": "success", "message": 'Servicio mecanico registrado correctamente', "id": aid})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
        mecanico_cedula, porcentaje = model.ejecutar("validate_mechanic_update", data)
        if not data.get('confirmar') and model.ejecutar("mechanic_busy_elsewhere", mecanico_cedula, aid):
            return jsonify({"status": "confirm", "message": "Este mecanico ya se encuentra asignado a otro servicio. ¿Quieres volverlo a asignar?"})
        model.ejecutar("update_mechanic", aid, mecanico_cedula)
        commission_model.ejecutar("set_percentage", aid, porcentaje)

        return jsonify({"status": "success", "message": "Mecanico asignado correctamente"})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo asignar el mecanico"}), 500


@service_mechanic_bp.route('/<int:aid>/status', methods=['PUT'])
def update_status(aid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not model.ejecutar("get_by_id", aid):
            return jsonify({"status": "error", "message": "Asignacion no encontrada"}), 404
        data = request.get_json() or {}
        model.ejecutar("update_status", aid, data.get('estado'))
        commission_id = None
        if (data.get('estado') or '').strip().lower() == 'completado':
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
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
        model.ejecutar("update_assignment", aid, payload)
        porcentaje = payload.get('porcentaje_comision')
        if porcentaje not in (None, '') and (payload.get('mecanico_cedula') or '').strip():
            try:
                commission_model.ejecutar("set_percentage", aid, float(porcentaje))
            except (TypeError, ValueError):
                pass

        return jsonify({"status": "success", "message": "Servicio mecanico modificado correctamente"})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
