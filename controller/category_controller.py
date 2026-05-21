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
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        value = request.args.get('value', '').strip()
        exclude = request.args.get('exclude', '').strip()
        if not value:
            return jsonify({"status": "success", "unique": True})
        exists = model.nombre_exists(value, exclude if exclude else None)
        return jsonify({"status": "success", "unique": not exists})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/<path:nombre>', methods=['GET'])
def get_one(nombre):
    try:
        item = model.get_by_nombre(nombre)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Categoria no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


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
        model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'CATEGORIAS',
            f"Categoria creada: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Categoria registrada correctamente.", "nombre": data['nombre'].strip()})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        old_nombre = data.get('old_nombre', '')
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if not old_nombre:
            errors['old_nombre'] = 'Identificador de categoria requerido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        new_nombre = data['nombre'].strip()
        if new_nombre != old_nombre and model.nombre_exists(new_nombre):
            return jsonify({"status": "error", "message": "La categoria ya existe", "errors": {"nombre": "La categoria ya existe"}}), 400
        model.update_category(old_nombre, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'CATEGORIAS',
            f"Categoria modificada: {old_nombre} -> {new_nombre}", request.remote_addr)
        return jsonify({"status": "success", "message": "Categoria modificada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/delete', methods=['DELETE'])
def delete():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        nombre = data.get('nombre', '')
        model.soft_delete(nombre)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'CATEGORIAS',
            f"Categoria desactivada: {nombre}", request.remote_addr)
        return jsonify({"status": "success", "message": "Categoria eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/toggle', methods=['PUT'])
def toggle():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        nombre = data.get('nombre', '')
        model.toggle_estado(nombre)
        return jsonify({"status": "success", "message": "Categoria eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
