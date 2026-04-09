from flask import Blueprint, request, jsonify, session
from model.sucursal_model import SucursalModel
from model.bitacora_model import BitacoraModel

sucursal_bp = Blueprint('sucursales', __name__)
model = SucursalModel()
bitacora = BitacoraModel()


@sucursal_bp.route('/', methods=['GET'])
def get_all():
    try:
        data = model.get_all()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@sucursal_bp.route('/active', methods=['GET'])
def get_active():
    try:
        data = model.get_active()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@sucursal_bp.route('/<int:sid>', methods=['GET'])
def get_one(sid):
    try:
        item = model.get_by_id(sid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Sucursal no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@sucursal_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            return jsonify({"status": "error", "message": "El nombre debe tener al menos 3 caracteres"}), 400
        if model.nombre_exists(data['nombre'].strip()):
            return jsonify({"status": "error", "message": "Ya existe una sucursal con ese nombre"}), 400
        sid = model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'SUCURSALES',
            f"Sucursal creada: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Sucursal creada", "id": sid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@sucursal_bp.route('/<int:sid>', methods=['PUT'])
def update(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            return jsonify({"status": "error", "message": "El nombre debe tener al menos 3 caracteres"}), 400
        if model.nombre_exists(data['nombre'].strip(), sid):
            return jsonify({"status": "error", "message": "Ya existe una sucursal con ese nombre"}), 400
        model.update_sucursal(sid, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'SUCURSALES',
            f"Sucursal modificada ID: {sid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Sucursal actualizada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@sucursal_bp.route('/<int:sid>', methods=['DELETE'])
def delete(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(sid)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'SUCURSALES',
            f"Sucursal desactivada ID: {sid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Sucursal desactivada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@sucursal_bp.route('/<int:sid>/toggle', methods=['PUT'])
def toggle(sid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.toggle_estado(sid)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'SUCURSALES',
            f"Estado de sucursal cambiado ID: {sid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
