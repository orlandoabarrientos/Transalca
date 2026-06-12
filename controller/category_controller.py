from flask import Blueprint, request, jsonify, session
from model.category_model import CategoryModel
import os
import time
from werkzeug.utils import secure_filename

from config.validation import require_text, optional_text

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'images')

def _save_image(file, nombre):
    if not file or file.filename == '':
        return None, None
    allowed = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return None, "Solo se permiten imagenes png, jpg, jpeg o webp."
    if file.mimetype not in {'image/png', 'image/jpeg', 'image/webp', 'image/jpg'}:
        return None, "El archivo no es una imagen valida."
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        return None, "La imagen no debe superar los 2MB."
    safe_name = secure_filename(nombre)
    filename = f"cat_{safe_name}_{int(time.time())}.{ext}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filename, None


category_bp = Blueprint('categories', __name__)
model = CategoryModel()



@category_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/check-unique', methods=['GET'])
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


@category_bp.route('/<path:nombre>', methods=['GET'])
def get_one(nombre):
    try:
        item = model.ejecutar("get_by_nombre", nombre)
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
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        errors = {}
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=30, allow_serial=True)
        clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=150)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        
        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename != '':
            filename, img_err = _save_image(imagen_file, clean['nombre'])
            if img_err:
                return jsonify({"status": "error", "message": "Error al subir la imagen", "errors": {"imagen": img_err}}), 400
            clean['imagen'] = filename

        existing = model.ejecutar("get_by_nombre", clean['nombre'])
        if existing:
            if existing['estado'] == 1:
                return jsonify({"status": "error", "message": "La categoria ya existe", "errors": {"nombre": "La categoria ya existe"}}), 400
            else:
                model.ejecutar("update_category", existing['nombre'], clean)
                model.ejecutar("reactivar", existing['nombre'])

                return jsonify({"status": "success", "message": "Categoria registrada correctamente.", "nombre": existing['nombre']})
        model.ejecutar("create", clean)


        return jsonify({"status": "success", "message": "Categoria registrada correctamente.", "nombre": clean['nombre']})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@category_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        errors = {}
        old_nombre = data.get('old_nombre', '').strip()
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=30, allow_serial=True)
        clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=150)
        if not old_nombre:
            errors['old_nombre'] = 'Identificador de categoria requerido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        new_nombre = clean['nombre']
        if new_nombre != old_nombre and model.ejecutar("nombre_exists", new_nombre):
            return jsonify({"status": "error", "message": "La categoria ya existe", "errors": {"nombre": "La categoria ya existe"}}), 400

        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename != '':
            filename, img_err = _save_image(imagen_file, clean['nombre'])
            if img_err:
                return jsonify({"status": "error", "message": "Error al subir la imagen", "errors": {"imagen": img_err}}), 400
            clean['imagen'] = filename

        model.ejecutar("update_category", old_nombre, clean)


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
        model.ejecutar("soft_delete", nombre)


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
        model.ejecutar("toggle_estado", nombre)
        return jsonify({"status": "success", "message": "Categoria eliminada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
