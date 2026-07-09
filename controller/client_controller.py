from flask import Blueprint, request, jsonify
from model.client_model import ClientModel
from model.vehicle_model import VehicleModel

from controller._guards import can_access_client, deny, is_employee, require_login
from config.validation import ValidationError, normalize_cedula, normalize_email

client_bp = Blueprint('client_admin', __name__)
model = ClientModel()
vehicle_model = VehicleModel()


@client_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        search = request.args.get('q')
        estado = request.args.get('estado')
        tipo_cliente = request.args.get('tipo_cliente', 'persona')
        if tipo_cliente == 'all':
            tipo_cliente = None
        return jsonify({"status": "success", "data": model.ejecutar("get_all", search, estado, tipo_cliente)})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_stats", 'persona')})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/check-unique', methods=['POST'])
def check_unique():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        payload = request.get_json(silent=True) or {}
        field = (payload.get('field') or '').strip()
        value = (payload.get('value') or '').strip()
        exclude = (payload.get('exclude') or '').strip()
        if field == 'cedula':
            errors = {}
            cedula, _, _ = normalize_cedula(errors, {'cedula': value})
            if errors:
                return jsonify({"status": "error", "message": errors['cedula']}), 400
            client = model.ejecutar("get_by_cedula", cedula)
            exists = bool(client and cedula != exclude)
            return jsonify({"status": "success", "exists": exists, "active": bool(client.get('estado')) if client else False})
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value, required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            exists = model.ejecutar("email_exists_globally", email, {"cliente_cedula": exclude, "usuario_cedula": exclude})
            return jsonify({"status": "success", "exists": exists})
        if field == 'placa':
            placa = value.upper()
            if not placa:
                return jsonify({"status": "error", "message": "La placa es obligatoria."}), 400
            owner = (payload.get('cedula') or '').strip()
            exists = vehicle_model.ejecutar("owner_has_placa", owner, placa, exclude or None)
            return jsonify({"status": "success", "exists": exists})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@client_bp.route('/<cedula>', methods=['GET'])
def get_one(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula) or cedula == 'V-00000000':
            return deny()
        c = model.ejecutar("get_by_cedula", cedula)
        if not c:
            return jsonify({"status": "error", "message": "Cliente no encontrado"}), 404
        c['vehiculos'] = model.ejecutar("get_vehicles", cedula)
        c['servicios'] = model.ejecutar("get_services", cedula)
        c['tickets'] = model.ejecutar("get_tickets", cedula)
        c['ordenes'] = model.ejecutar("get_orders", cedula)
        c['notificaciones'] = model.ejecutar("get_notifications", cedula)
        c['bitacora'] = model.ejecutar("get_bitacora", cedula)
        return jsonify({"status": "success", "data": c})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        result = model.ejecutar("create", data)
        return jsonify({"status": "success", "message": "Cliente registrado correctamente.", "id": result.get('cedula')}), 201
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/<cedula>', methods=['PUT'])
def update(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee() or cedula == 'V-00000000':
            return deny()
        data = request.get_json() or {}
        model.ejecutar("update_client", cedula, data)
        return jsonify({"status": "success", "message": "Cliente modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except LookupError:
        return jsonify({"status": "error", "message": "Cliente no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/<cedula>/toggle', methods=['PUT'])
def toggle(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee() or cedula == 'V-00000000':
            return deny()
        estado = model.ejecutar("soft_delete", cedula)

        return jsonify({"status": "success", "message": "Cliente eliminado correctamente.", "estado": estado})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/<cedula>/vehicles', methods=['GET'])
def get_vehicles(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_vehicles", cedula)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/<cedula>/vehicles', methods=['POST'])
def add_vehicle(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return deny()
        data = request.get_json() or {}
        data['cliente_cedula'] = cedula
        vid = vehicle_model.ejecutar("create", data)
        return jsonify({"status": "success", "message": "Vehiculo registrado correctamente.", "id": vid}), 201
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/<cedula>/vehicles/<path:vid>', methods=['PUT'])
def update_vehicle(cedula, vid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return deny()
        data = request.get_json() or {}
        vehicle = vehicle_model.ejecutar("get_by_id", vid)
        if not vehicle or cedula not in vehicle.get('cliente_cedula', '').split(','):
            return jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404
        vehicle_model.ejecutar("update_vehicle", vid, data)
        return jsonify({"status": "success", "message": "Vehiculo modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/<cedula>/vehicles/<path:vid>', methods=['DELETE'])
def delete_vehicle(cedula, vid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return deny()
        vehicle = vehicle_model.ejecutar("get_by_id", vid)
        if not vehicle or cedula not in vehicle.get('cliente_cedula', '').split(','):
            return jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404
        vehicle_model.ejecutar("soft_delete_relationship", cedula, vid)
        return jsonify({"status": "success", "message": "Vehiculo eliminado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
