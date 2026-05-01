from flask import Blueprint, request, jsonify
from model.client_model import ClientModel
from model.vehicle_model import VehicleModel
from controller._guards import can_access_client, deny, is_employee, require_login
from config.constants import PHONE_REGEX
import re

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
        return jsonify({"status": "success", "data": model.get_all(search, estado)})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.get_stats()})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/<cedula>', methods=['GET'])
def get_one(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
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
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        if not data or not data.get('cedula') or not data.get('nombre') or not data.get('apellido'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        if not data.get('telefono') or not re.match(PHONE_REGEX, data.get('telefono', '').strip()):
            return jsonify({"status": "error", "message": "Telefono invalido"}), 400
        if model.get_by_cedula(data['cedula'].strip()):
            return jsonify({"status": "error", "message": "La cedula ya existe"}), 400
        cid = model.create(data)
        return jsonify({"status": "success", "message": "Cliente registrado", "id": cid}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/<cedula>', methods=['PUT'])
def update(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        if not data or not data.get('nombre') or not data.get('apellido'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        if not data.get('telefono') or not re.match(PHONE_REGEX, data.get('telefono', '').strip()):
            return jsonify({"status": "error", "message": "Telefono invalido"}), 400
        model.update_client(cedula, data)
        return jsonify({"status": "success", "message": "Cliente actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/<cedula>/toggle', methods=['PUT'])
def toggle(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.toggle_estado(cedula)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/<cedula>/vehicles', methods=['POST'])
def add_vehicle(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return deny()
        data = request.get_json()
        if not data or not data.get('marca') or not data.get('modelo'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        data['cliente_cedula'] = cedula
        vid = vehicle_model.create(data)
        return jsonify({"status": "success", "message": "Vehiculo registrado", "id": vid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/<cedula>/vehicles/<int:vid>', methods=['PUT'])
def update_vehicle(cedula, vid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return deny()
        data = request.get_json()
        if not data or not data.get('marca') or not data.get('modelo'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        vehicle = vehicle_model.get_by_id(vid)
        if not vehicle or vehicle.get('cliente_cedula') != cedula:
            return jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404
        vehicle_model.update_vehicle(vid, data)
        return jsonify({"status": "success", "message": "Vehiculo actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@client_bp.route('/<cedula>/vehicles/<int:vid>', methods=['DELETE'])
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
        return jsonify({"status": "success", "message": "Vehiculo eliminado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
