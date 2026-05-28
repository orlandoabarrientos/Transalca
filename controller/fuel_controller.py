from flask import Blueprint, request, jsonify
from model.fuel_model import FuelModel
from model.vehicle_model import VehicleModel
from controller._guards import can_access_client, require_login

fuel_bp = Blueprint('fuel_bp', __name__)
model = FuelModel()
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


@fuel_bp.route('/vehicle/<path:vid>', methods=['GET'])
def get_by_vehicle(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        return jsonify({"status": "success", "data": model.get_by_vehicle(vid)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@fuel_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        data = request.get_json() or {}
        if not data.get('vehiculo_id'):
            return jsonify({"status": "error", "message": "Vehiculo requerido"}), 400
        _, error = load_vehicle(data['vehiculo_id'])
        if error:
            return error
        rid = model.create(data)
        return jsonify({"status": "success", "message": "Registro creado", "id": rid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@fuel_bp.route('/average/<path:vid>', methods=['GET'])
def average(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        avg = model.get_average_consumption(vid)
        return jsonify({"status": "success", "data": {"promedio_lkm": avg}})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@fuel_bp.route('/<int:rid>', methods=['DELETE'])
def delete(rid):
    try:
        auth = require_login()
        if auth:
            return auth
        record = model.get_by_id(rid)
        if not record:
            return jsonify({"status": "error", "message": "Registro no encontrado"}), 404
        _, error = load_vehicle(record['vehiculo_id'])
        if error:
            return error
        model.delete_record(rid)
        return jsonify({"status": "success", "message": "Registro eliminado"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
