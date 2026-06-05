from flask import Blueprint, request, jsonify, session
from model.brand_model import BrandModel
# from model.bitacora_model import BitacoraModel
from config.validation import require_text, optional_text

brand_bp = Blueprint('brands', __name__)
model = BrandModel()
# bitacora = BitacoraModel()


@brand_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/check-unique', methods=['GET'])
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


@brand_bp.route('/<path:nombre>', methods=['GET'])
def get_one(nombre):
    try:
        item = model.get_by_nombre(nombre)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Marca no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        errors = {}
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=30, allow_serial=True)
        clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=150)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        existing = model.get_by_nombre(clean['nombre'])
        if existing:
            if existing['estado'] == 1:
                return jsonify({"status": "error", "message": "La marca ya existe", "errors": {"nombre": "La marca ya existe"}}), 400
            else:
                model.update_brand(existing['nombre'], clean)
                model.update("transalca", "UPDATE marcas SET estado = 1 WHERE nombre = %s", (existing['nombre'],))
                # bitacora.log_action(session['user_id'], 'CREAR', 'MARCAS', f"Marca creada: {clean['nombre']}", request.remote_addr)
                return jsonify({"status": "success", "message": "Marca registrada correctamente.", "nombre": existing['nombre']})
        model.create(clean)
        # bitacora.log_action(session['user_id'], 'CREAR', 'MARCAS',
            # f"Marca creada: {clean['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca registrada correctamente.", "nombre": clean['nombre']})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        errors = {}
        old_nombre = data.get('old_nombre', '').strip()
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=30, allow_serial=True)
        clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=150)
        if not old_nombre:
            errors['old_nombre'] = 'Identificador de marca requerido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        new_nombre = clean['nombre']
        if new_nombre != old_nombre and model.nombre_exists(new_nombre):
            return jsonify({"status": "error", "message": "La marca ya existe", "errors": {"nombre": "La marca ya existe"}}), 400
        model.update_brand(old_nombre, clean)
        # bitacora.log_action(session['user_id'], 'MODIFICAR', 'MARCAS',
            # f"Marca modificada: {old_nombre} -> {new_nombre}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca modificada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/delete', methods=['DELETE'])
def delete():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        nombre = data.get('nombre', '')
        model.soft_delete(nombre)
        # bitacora.log_action(session['user_id'], 'ELIMINAR', 'MARCAS',
            # f"Marca desactivada: {nombre}", request.remote_addr)
        return jsonify({"status": "success", "message": "Marca eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/toggle', methods=['PUT'])
def toggle():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        nombre = data.get('nombre', '')
        model.toggle_estado(nombre)
        return jsonify({"status": "success", "message": "Marca eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
