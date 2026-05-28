from flask import Blueprint, request, jsonify
from model.maintenance_model import MaintenanceModel
from model.vehicle_model import VehicleModel
from controller._guards import can_access_client, deny, is_employee, require_login

maintenance_bp = Blueprint('maintenance_bp', __name__)
model = MaintenanceModel()
vehicle_model = VehicleModel()


def load_vehicle(vid):
    auth = require_login()
    if auth:
        return None, auth
    vehicle = vehicle_model.get_by_id(vid)
    if not vehicle:
        return None, (jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404)
    if not can_access_client(vehicle.get('cliente_cedula')):
        return None, deny()
    return vehicle, None


@maintenance_bp.route('/rules', methods=['GET'])
def get_rules():
    try:
        auth = require_login()
        if auth:
            return auth
        active = request.args.get('active', '1') == '1'
        return jsonify({"status": "success", "data": model.get_rules(active)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/rules', methods=['POST'])
def create_rule():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        if not data or not data.get('nombre') or not data.get('tipo_servicio'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        rid = model.create_rule(data)
        return jsonify({"status": "success", "message": "Regla creada", "id": rid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/rules/<int:rid>', methods=['PUT'])
def update_rule(rid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        model.update_rule(rid, data)
        return jsonify({"status": "success", "message": "Regla actualizada"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/rules/<int:rid>/toggle', methods=['PUT'])
def toggle_rule(rid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.toggle_rule(rid)
        return jsonify({"status": "success", "message": "Estado de regla cambiado"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/scheduled', methods=['GET'])
def get_scheduled():
    try:
        auth = require_login()
        if auth:
            return auth
        vid = request.args.get('vehiculo_id')
        if vid and not is_employee():
            _, error = load_vehicle(vid)
            if error:
                return error
        if not is_employee() and not vid:
            return jsonify({"status": "error", "message": "vehiculo_id requerido"}), 400
        return jsonify({"status": "success", "data": model.get_pending(vid)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/scheduled', methods=['POST'])
def create_scheduled():
    try:
        auth = require_login()
        if auth:
            return auth
        data = request.get_json()
        if not data or not data.get('vehiculo_id') or not data.get('tipo_mantenimiento'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        _, error = load_vehicle(data['vehiculo_id'])
        if error:
            return error
        mid = model.create_scheduled(data)
        return jsonify({"status": "success", "message": "Mantenimiento programado", "id": mid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/scheduled/<int:mid>/complete', methods=['PUT'])
def complete(mid):
    try:
        auth = require_login()
        if auth:
            return auth
        data = request.get_json() or {}
        item = model.get_scheduled_by_id(mid)
        if not item:
            return jsonify({"status": "error", "message": "Mantenimiento no encontrado"}), 404
        if not can_access_client(item.get('cliente_cedula')):
            return deny()
        model.complete_maintenance(mid, data.get('km_realizado'))
        return jsonify({"status": "success", "message": "Mantenimiento completado"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/calculate/<path:vid>', methods=['POST'])
def calculate(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        created = model.calculate_for_vehicle(vid)
        return jsonify({"status": "success", "message": f"{len(created)} mantenimientos programados", "created": created})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/check-overdue', methods=['POST'])
def check_overdue():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.check_overdue()
        return jsonify({"status": "success", "message": "Verificacion completada"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@maintenance_bp.route('/vehicle/<path:vid>', methods=['GET'])
def get_vehicle_maintenance(vid):
    try:
        _, error = load_vehicle(vid)
        if error:
            return error
        return jsonify({"status": "success", "data": model.get_by_vehicle(vid)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
