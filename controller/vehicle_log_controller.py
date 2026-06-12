from flask import Blueprint, request, jsonify, session
from model.vehicle_log_model import VehicleLogModel
from model.vehicle_model import VehicleModel
from controller._guards import can_access_client, deny, is_employee, require_login

vehicle_log_bp = Blueprint('vehicle_log_bp', __name__)
model = VehicleLogModel()
vehicle_model = VehicleModel()


def load_vehicle(vid):
    auth = require_login()
    if auth:
        return None, auth
    vehicle = vehicle_model.ejecutar("get_by_id", vid)
    if not vehicle:
        return None, (jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404)
    cedulas = str(vehicle.get('cliente_cedula') or '').split(',')
    if not any(can_access_client(c) for c in cedulas if c):
        if not is_employee():
            return None, (jsonify({"status": "error", "message": "No autorizado"}), 403)
    return vehicle, None


@vehicle_log_bp.route('/vehicle/<path:vid>', methods=['GET'])
def get_by_vehicle(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        return jsonify({"status": "success", "data": model.ejecutar("get_by_vehicle", vid)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/client/<cedula>', methods=['GET'])
def get_by_client(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        return jsonify({"status": "success", "data": model.ejecutar("get_by_cliente", cedula)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/admin', methods=['GET'])
def admin_listing():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_admin_listing", 
            cliente=request.args.get('cliente'),
            vehiculo=request.args.get('vehiculo'),
            fecha_desde=request.args.get('fecha_desde'),
            fecha_hasta=request.args.get('fecha_hasta'))})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/predictions', methods=['GET'])
def predictions():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_predictions", 
            vehiculo=request.args.get('vehiculo'),
            cliente=request.args.get('cliente'),
            estado=request.args.get('estado'),
            prioridad=request.args.get('prioridad'))})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/predictions/client/<cedula>', methods=['GET'])
def predictions_by_client(cedula):
    try:
        auth = require_login()
        if auth:
            return auth
        if not can_access_client(cedula):
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        return jsonify({"status": "success", "data": model.ejecutar("get_predictions_by_client", cedula)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/predictions/<int:pid>/attend', methods=['PUT'])
def attend_prediction(pid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.ejecutar("mark_prediction_attended", pid)
        return jsonify({"status": "success", "message": "Prediccion marcada como atendida"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/run-cycle', methods=['POST'])
def run_cycle():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        result = model.ejecutar("run_automatic_cycle")
        return jsonify({"status": "success", "message": "Ciclo de bitacora ejecutado", "data": result})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/<int:lid>', methods=['GET'])
def get_one(lid):
    try:
        auth = require_login()
        if auth:
            return auth
        entry = model.ejecutar("get_by_id", lid)
        if not entry:
            return jsonify({"status": "error", "message": "Registro no encontrado"}), 404
        if not can_access_client(entry.get('cliente_cedula')) and not is_employee():
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        return jsonify({"status": "success", "data": entry})
    except Exception:
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
        cedulas = str(vehicle.get('cliente_cedula') or '').split(',')
        if data.get('cliente_cedula') not in cedulas:
            return jsonify({"status": "error", "message": "Vehiculo no pertenece al cliente"}), 400
        lid = model.ejecutar("create", data)
        return jsonify({"status": "success", "message": "Registro creado", "id": lid}), 201
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_log_bp.route('/oil-changes/<path:vid>', methods=['GET'])
def oil_changes(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        count = model.ejecutar("count_oil_changes", vid)
        return jsonify({"status": "success", "data": {"count": count, "km_estimated": count * 5000}})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
