from flask import Blueprint, request, jsonify, session
from model.service_model import ServiceModel

from config.validation import ValidationError

service_bp = Blueprint('services', __name__)
model = ServiceModel()


@service_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        value = request.args.get('value', '').strip()
        exclude = request.args.get('exclude', '').strip()
        if not value:
            return jsonify({"status": "success", "unique": True})
        exists = model.ejecutar("nombre_exists", value, exclude if exclude else None)
        return jsonify({"status": "success", "unique": not exists})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@service_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/<int:sid>', methods=['GET'])
def get_one(sid):
    try:
        item = model.ejecutar("get_by_id", sid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Servicio no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el servicio."}), 500


@service_bp.route('/sucursal/<int:suc_id>', methods=['GET'])
def get_by_sucursal(suc_id):
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_by_sucursal", suc_id)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los servicios."}), 500


@service_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        sid = model.ejecutar("create", data)
        return jsonify({"status": "success", "message": "Servicio registrado correctamente.", "id": sid})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el servicio."}), 500


@service_bp.route('/<int:sid>', methods=['PUT'])
def update(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        if not model.ejecutar("get_by_id", sid):
            return jsonify({"status": "error", "message": "Servicio no encontrado."}), 404
        data = request.get_json() or {}
        model.ejecutar("update_service", sid, data)
        return jsonify({"status": "success", "message": "Servicio modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el servicio."}), 500


@service_bp.route('/<int:sid>', methods=['DELETE'])
def delete(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        if not model.ejecutar("get_by_id", sid):
            return jsonify({"status": "error", "message": "Servicio no encontrado."}), 404
        model.ejecutar("soft_delete", sid)


        return jsonify({"status": "success", "message": "Servicio eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el servicio."}), 500


@service_bp.route('/<int:sid>/toggle', methods=['PUT'])
def toggle(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        if not model.ejecutar("get_by_id", sid):
            return jsonify({"status": "error", "message": "Servicio no encontrado."}), 404
        model.ejecutar("toggle_estado", sid)


        item = model.ejecutar("get_by_id", sid)
        msg = "Servicio reactivado correctamente." if item and item.get('estado') else "Servicio eliminado correctamente."
        return jsonify({"status": "success", "message": msg})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del servicio."}), 500
