from flask import Blueprint, request, jsonify
from model.client_model import ClientModel
from model.vehicle_model import VehicleModel

from controller._guards import can_access_client, deny, is_employee, require_login
from config.validation import (
    normalize_cedula,
    normalize_email,
    normalize_int,
    normalize_phone,
    optional_text,
    require_text,
    validate_choice,
)
from config.constants import TIPOS_COMBUSTIBLE

client_bp = Blueprint('client_admin', __name__)
model = ClientModel()
vehicle_model = VehicleModel()



def _validate_client(data, require_cedula=True):
    errors = {}
    clean = {}
    clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=100, person=True)
    clean['apellido'] = require_text(errors, 'apellido', data.get('apellido'), 'El apellido', min_len=2, max_len=100, person=True)
    clean['telefono'] = normalize_phone(errors, data.get('telefono'))
    clean['email'] = normalize_email(errors, data.get('email'), required=False)
    clean['direccion'] = optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=300)
    if require_cedula:
        cedula, prefijo, _ = normalize_cedula(errors, data)
        clean['cedula'] = cedula
        clean['cedula_prefijo'] = prefijo
    return clean, errors


def _validate_vehicle(data):
    errors = {}
    clean = {}
    clean['marca'] = require_text(errors, 'marca', data.get('marca'), 'La marca', min_len=2, max_len=100, allow_serial=False)
    clean['modelo'] = require_text(errors, 'modelo', data.get('modelo'), 'El modelo', min_len=1, max_len=100, allow_serial=False)
    clean['anio'] = normalize_int(errors, 'anio', data.get('anio'), 'El ano', min_value=1900, max_value=2100) if data.get('anio') not in (None, '') else None
    clean['placa'] = optional_text(errors, 'placa', data.get('placa'), 'La placa', max_len=20).upper()
    clean['color'] = optional_text(errors, 'color', data.get('color'), 'El color', max_len=50, allow_serial=False)
    clean['tipo_vehiculo'] = optional_text(errors, 'tipo_vehiculo', data.get('tipo_vehiculo'), 'El tipo de vehiculo', max_len=50, allow_serial=False)
    clean['tipo_combustible'] = validate_choice(errors, 'tipo_combustible', data.get('tipo_combustible') or 'gasolina', TIPOS_COMBUSTIBLE)
    clean['kilometraje_actual'] = normalize_int(errors, 'kilometraje_actual', data.get('kilometraje_actual') or 0, 'El kilometraje', min_value=0, max_value=9999999)
    return clean, errors


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
        return jsonify({"status": "success", "data": model.get_all(search, estado, tipo_cliente)})
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
        return jsonify({"status": "success", "data": model.get_stats('persona')})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@client_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        field = (request.args.get('field') or '').strip()
        value = (request.args.get('value') or '').strip()
        exclude = (request.args.get('exclude') or '').strip()
        if field == 'cedula':
            errors = {}
            cedula, _, _ = normalize_cedula(errors, {'cedula': value})
            if errors:
                return jsonify({"status": "error", "message": errors['cedula']}), 400
            client = model.get_by_cedula(cedula)
            exists = bool(client and cedula != exclude)
            return jsonify({"status": "success", "exists": exists, "active": bool(client.get('estado')) if client else False})
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value, required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            exists = model.email_exists_globally(email, {"cliente_cedula": exclude, "usuario_cedula": exclude})
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
        c = model.get_by_cedula(cedula)
        if not c:
            return jsonify({"status": "error", "message": "Cliente no encontrado"}), 404
        c['vehiculos'] = model.get_vehicles(cedula)
        c['servicios'] = model.get_services(cedula)
        c['tickets'] = model.get_tickets(cedula)
        c['ordenes'] = model.get_orders(cedula)
        c['notificaciones'] = model.get_notifications(cedula)
        c['bitacora'] = model.get_bitacora(cedula)
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
        clean, errors = _validate_client(data, True)
        clean['tipo_cliente'] = 'persona'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        existing = model.get_by_cedula(clean['cedula'])
        if existing and existing.get('estado'):
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        if clean.get('email') and model.email_exists_globally(clean['email'], {"cliente_cedula": clean['cedula'], "usuario_cedula": clean['cedula']}):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        result = model.create(clean)

        if result.get('reactivated'):
            return jsonify({"status": "success", "message": "Cliente registrado correctamente.", "id": result.get('cedula')}), 201
        return jsonify({"status": "success", "message": "Cliente registrado correctamente.", "id": result.get('cedula')}), 201
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
        clean, errors = _validate_client({**data, 'cedula': cedula}, True)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if clean.get('email') and model.email_exists_globally(clean['email'], {"cliente_cedula": cedula, "usuario_cedula": cedula}):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        model.update_client(cedula, clean)

        return jsonify({"status": "success", "message": "Cliente modificado correctamente."})
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
        estado = model.toggle_estado(cedula)

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
        return jsonify({"status": "success", "data": model.get_vehicles(cedula)})
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
        clean, errors = _validate_vehicle(data)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        clean['cliente_cedula'] = cedula
        if clean.get('placa') and vehicle_model.placa_exists(clean['placa']):
            return jsonify({"status": "error", "message": "Esta placa ya esta registrada.", "errors": {"placa": "Esta placa ya esta registrada."}}), 400
        vid = vehicle_model.create(clean)
        return jsonify({"status": "success", "message": "Vehiculo registrado correctamente.", "id": vid}), 201
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
        clean, errors = _validate_vehicle(data)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        vehicle = vehicle_model.get_by_id(vid)
        if not vehicle or vehicle.get('cliente_cedula') != cedula:
            return jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404
        if clean.get('placa') and vehicle_model.placa_exists(clean['placa'], exclude_id=vid):
            return jsonify({"status": "error", "message": "Esta placa ya esta registrada.", "errors": {"placa": "Esta placa ya esta registrada."}}), 400
        vehicle_model.update_vehicle(vid, clean)
        return jsonify({"status": "success", "message": "Vehiculo modificado correctamente."})
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
        vehicle = vehicle_model.get_by_id(vid)
        if not vehicle or vehicle.get('cliente_cedula') != cedula:
            return jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404
        vehicle_model.soft_delete(vid)
        return jsonify({"status": "success", "message": "Vehiculo eliminado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
