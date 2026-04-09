from flask import Blueprint, request, jsonify, session
from model.category_model import CategoryModel
from model.bitacora_model import BitacoraModel

category_bp = Blueprint('categories', __name__)
model = CategoryModel()
bitacora = BitacoraModel()


@category_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@category_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@category_bp.route('/<int:cid>', methods=['GET'])
def get_one(cid):
    try:
        item = model.get_by_id(cid)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Categoria no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@category_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.nombre_exists(data['nombre'].strip()):
            return jsonify({"status": "error", "message": "La categoria ya existe", "errors": {"nombre": "La categoria ya existe"}}), 400
        cid = model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'CATEGORIAS',
            f"Categoria creada: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Categoria creada", "id": cid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@category_bp.route('/<int:cid>', methods=['PUT'])
def update(cid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.nombre_exists(data['nombre'].strip(), cid):
            return jsonify({"status": "error", "message": "La categoria ya existe", "errors": {"nombre": "La categoria ya existe"}}), 400
        model.update_category(cid, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'CATEGORIAS',
            f"Categoria modificada ID: {cid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Categoria actualizada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@category_bp.route('/<int:cid>', methods=['DELETE'])
def delete(cid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(cid)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'CATEGORIAS',
            f"Categoria desactivada ID: {cid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Categoria desactivada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@category_bp.route('/<int:cid>/toggle', methods=['PUT'])
def toggle(cid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.toggle_estado(cid)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
