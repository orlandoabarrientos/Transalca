from flask import Blueprint, request, jsonify, session
from model.brand_model import BrandModel
from model.bitacora_model import BitacoraModel

brand_bp = Blueprint('brands', __name__)
model = BrandModel()
bitacora = BitacoraModel()


@brand_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/<int:bid>', methods=['GET'])
def get_one(bid):
    try:
        item = model.get_by_id(bid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Marca no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.nombre_exists(data['nombre'].strip()):
            return jsonify({"status": "error", "message": "La marca ya existe", "errors": {"nombre": "La marca ya existe"}}), 400
        bid = model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'MARCAS',
            f"Marca creada: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca creada", "id": bid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/<int:bid>', methods=['PUT'])
def update(bid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.nombre_exists(data['nombre'].strip(), bid):
            return jsonify({"status": "error", "message": "La marca ya existe", "errors": {"nombre": "La marca ya existe"}}), 400
        model.update_brand(bid, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'MARCAS',
            f"Marca modificada ID: {bid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca actualizada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/<int:bid>', methods=['DELETE'])
def delete(bid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(bid)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'MARCAS',
            f"Marca desactivada ID: {bid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca desactivada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/<int:bid>/toggle', methods=['PUT'])
def toggle(bid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.toggle_estado(bid)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
