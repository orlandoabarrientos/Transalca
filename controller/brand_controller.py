from flask import Blueprint, request, jsonify, session
from model.brand_model import BrandModel

from config.validation import require_text, optional_text

brand_bp = Blueprint('brands', __name__)
model = BrandModel()



@brand_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@brand_bp.route('/check-unique', methods=['GET'])
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


@brand_bp.route('/<path:nombre>', methods=['GET'])
def get_one(nombre):
    try:
        item = model.ejecutar("get_by_nombre", nombre)
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
        existing = model.ejecutar("get_by_nombre", clean['nombre'])
        if existing:
            if existing['estado'] == 1:
                return jsonify({"status": "error", "message": "La marca ya existe", "errors": {"nombre": "La marca ya existe"}}), 400
            else:
                model.ejecutar("update_brand", existing['nombre'], clean)
                model.ejecutar("reactivar", existing['nombre'])

                return jsonify({"status": "success", "message": "Marca registrada correctamente.", "nombre": existing['nombre']})
        model.ejecutar("create", clean)


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
        if new_nombre != old_nombre and model.ejecutar("nombre_exists", new_nombre):
            return jsonify({"status": "error", "message": "La marca ya existe", "errors": {"nombre": "La marca ya existe"}}), 400
        model.ejecutar("update_brand", old_nombre, clean)


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
        model.ejecutar("soft_delete", nombre)


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
        model.ejecutar("toggle_estado", nombre)
        return jsonify({"status": "success", "message": "Marca eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
