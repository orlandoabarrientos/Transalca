from flask import Blueprint, request, jsonify, session
from model.category_model import CategoryModel
import os
import time
from werkzeug.utils import secure_filename

from config.validation import ValidationError

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
        clean = model.ejecutar("validate", data)
        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename != '':
            filename, img_err = _save_image(imagen_file, clean['nombre'])
            if img_err:
                return jsonify({"status": "error", "message": "Error al subir la imagen", "errors": {"imagen": img_err}}), 400
            data['imagen'] = filename
        elif str(data.get('imagen_remove') or '').strip() == '1':
            data['imagen'] = 'product-default-parts.png'
        nombre = model.ejecutar("create", data)
        return jsonify({"status": "success", "message": "Categoria registrada correctamente.", "nombre": nombre})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
        clean = model.ejecutar("validate", data)
        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename != '':
            filename, img_err = _save_image(imagen_file, clean['nombre'])
            if img_err:
                return jsonify({"status": "error", "message": "Error al subir la imagen", "errors": {"imagen": img_err}}), 400
            data['imagen'] = filename
        elif str(data.get('imagen_remove') or '').strip() == '1':
            data['imagen'] = 'product-default-parts.png'
        model.ejecutar("update_category", data.get('old_nombre', ''), data)
        return jsonify({"status": "success", "message": "Categoria modificada correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
