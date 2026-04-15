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


@brand_bp.route('/<path:nombre>', methods=['GET'])
def get_one(nombre):
    try:
        item = model.get_by_nombre(nombre)
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
        model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'MARCAS',
            f"Marca creada: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca creada", "nombre": data['nombre'].strip()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        old_nombre = data.get('old_nombre', '')
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        if not old_nombre:
            errors['old_nombre'] = 'Identificador de marca requerido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        new_nombre = data['nombre'].strip()
        if new_nombre != old_nombre and model.nombre_exists(new_nombre):
            return jsonify({"status": "error", "message": "La marca ya existe", "errors": {"nombre": "La marca ya existe"}}), 400
        model.update_brand(old_nombre, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'MARCAS',
            f"Marca modificada: {old_nombre} -> {new_nombre}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca actualizada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/delete', methods=['DELETE'])
def delete():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        nombre = data.get('nombre', '')
        model.soft_delete(nombre)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'MARCAS',
            f"Marca desactivada: {nombre}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca desactivada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@brand_bp.route('/toggle', methods=['PUT'])
def toggle():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        nombre = data.get('nombre', '')
        model.toggle_estado(nombre)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
