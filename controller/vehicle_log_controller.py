from flask import Blueprint, request, jsonify, session
from model.vehicle_log_model import VehicleLogModel
from model.vehicle_model import VehicleModel
from controller._guards import can_access_client, require_login

vehicle_log_bp = Blueprint('vehicle_log_bp', __name__)
model = VehicleLogModel()
vehicle_model = VehicleModel()


def load_vehicle(vid):
    auth = require_login()
    if auth:
        return None, auth
    vehicle = vehicle_model.get_by_id(vid)
    if not vehicle:
        return None, (jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404)
    if not can_access_client(vehicle.get('cliente_cedula')):
        return None, (jsonify({"status": "error", "message": "No autorizado"}), 403)
    return vehicle, None


@vehicle_log_bp.route('/vehicle/<path:vid>', methods=['GET'])
def get_by_vehicle(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        return jsonify({"status": "success", "data": model.get_by_vehicle(vid)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/client/<cedula>', methods=['GET'])
def get_by_client(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        return jsonify({"status": "success", "data": model.get_by_cliente(cedula)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/<int:lid>', methods=['GET'])
def get_one(lid):
    try:
        auth = require_login()
        if auth:
            return auth
        entry = model.get_by_id(lid)
        if not entry:
            return jsonify({"status": "error", "message": "Registro no encontrado"}), 404
        if not can_access_client(entry.get('cliente_cedula')):
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        return jsonify({"status": "success", "data": entry})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        data = request.get_json() or {}
        if not data.get('vehiculo_id') or not data.get('cliente_cedula'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        if not can_access_client(data.get('cliente_cedula')):
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        vehicle, error = load_vehicle(data['vehiculo_id'])
        if error:
            return error
        if vehicle.get('cliente_cedula') != data.get('cliente_cedula'):
            return jsonify({"status": "error", "message": "Vehiculo no pertenece al cliente"}), 400
        lid = model.create(data)
        return jsonify({"status": "success", "message": "Registro creado", "id": lid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/oil-changes/<path:vid>', methods=['GET'])
def oil_changes(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        count = model.count_oil_changes(vid)
        return jsonify({"status": "success", "data": {"count": count, "km_estimated": count * 5000}})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
