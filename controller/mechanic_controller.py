from flask import Blueprint, request, jsonify, session
from model.mechanic_model import MechanicModel
from model.bitacora_model import BitacoraModel
from config.validation import normalize_cedula, normalize_phone, optional_text, require_text
from werkzeug.utils import secure_filename
import os
import time

mechanic_bp = Blueprint('mechanics', __name__)
model = MechanicModel()
bitacora = BitacoraModel()
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _validate_mechanic(data):
    errors = {}
    cedula, cedula_prefijo, _ = normalize_cedula(errors, data)
    clean = {
        'cedula': cedula,
        'cedula_prefijo': cedula_prefijo,
        'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=60, person=True),
        'apellido': require_text(errors, 'apellido', data.get('apellido'), 'El apellido', min_len=2, max_len=60, person=True),
        'telefono': normalize_phone(errors, data.get('telefono'), required=False),
        'especialidad': optional_text(errors, 'especialidad', data.get('especialidad'), 'La especialidad', max_len=120, allow_serial=False)
    }
    return clean, errors


def _save_photo(file, cedula):
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS or file.mimetype not in {'image/png', 'image/jpeg', 'image/webp'}:
        return None, 'El archivo debe ser una imagen png, jpg, jpeg o webp.'
    filename = secure_filename(f"mec_{cedula.replace('-', '')}_{int(time.time() * 1000)}.{ext}")
    path = os.path.join('public', 'assets', 'profile_pics', filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(path)
    return filename, None


@mechanic_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los mecanicos."}), 500


@mechanic_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        errors = {}
        cedula, _, _ = normalize_cedula(errors, {'cedula': request.args.get('value', '')})
        exclude = request.args.get('exclude') or None
        if errors:
            return jsonify({"status": "error", "message": errors.get('cedula')}), 400
        return jsonify({"status": "success", "exists": model.cedula_exists(cedula, exclude)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar la cedula."}), 500


@mechanic_bp.route('/<path:cedula>', methods=['GET'])
def get_one(cedula):
    try:
        item = model.get_by_cedula(cedula)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Mecanico no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el mecanico."}), 500


@mechanic_bp.route('/history/<path:cedula>', methods=['GET'])
def get_history(cedula):
    try:
        return jsonify({"status": "success", "data": model.get_service_history(cedula)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el historial."}), 500


@mechanic_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data, errors = _validate_mechanic(request.form.to_dict())
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.cedula_exists(data['cedula']):
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        filename, file_error = _save_photo(request.files.get('foto_perfil'), data['cedula'])
        if file_error:
            return jsonify({"status": "error", "message": file_error, "errors": {"foto_perfil": file_error}}), 400
        if filename:
            data['foto_perfil'] = filename
        model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'MECANICOS', f"Mecanico creado: {data['cedula']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico registrado correctamente.", "cedula": data['cedula']})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el mecanico."}), 500


@mechanic_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        raw = request.form.to_dict()
        old_cedula = raw.get('old_cedula', '')
        data, errors = _validate_mechanic(raw)
        if not old_cedula:
            errors['old_cedula'] = 'Identificador requerido.'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if data['cedula'] != old_cedula and model.cedula_exists(data['cedula']):
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        filename, file_error = _save_photo(request.files.get('foto_perfil'), data['cedula'])
        if file_error:
            return jsonify({"status": "error", "message": file_error, "errors": {"foto_perfil": file_error}}), 400
        if filename:
            data['foto_perfil'] = filename
        model.update_mechanic(old_cedula, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'MECANICOS', f"Mecanico modificado: {old_cedula}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el mecanico."}), 500


@mechanic_bp.route('/delete', methods=['DELETE'])
def delete():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        cedula = (data.get('cedula') or '').strip()
        result = model.soft_delete(cedula)
        if result is None:
            return jsonify({"status": "error", "message": "Mecanico no encontrado."}), 404
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'MECANICOS', f"Estado mecanico cambiado: {cedula}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico eliminado correctamente.", "estado": 0})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del mecanico."}), 500
