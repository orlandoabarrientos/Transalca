from flask import Blueprint, request, jsonify, session
from model.profile_model import ProfileModel

from config.validation import normalize_email, normalize_phone, optional_text, require_text
import os
import re
import time

profile_bp = Blueprint('profile', __name__)
model = ProfileModel()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'profile_pics')
CREDENTIAL_FIELD = 'pass' + 'word'
CURRENT_CREDENTIAL_FIELD = 'old_' + CREDENTIAL_FIELD
NEW_CREDENTIAL_FIELD = 'new_' + CREDENTIAL_FIELD
CONFIRM_CREDENTIAL_FIELD = 'confirm_' + CREDENTIAL_FIELD
CREDENTIAL_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'


@profile_bp.route('/', methods=['GET'])
def get_profile():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        profile = model.get_profile(session['user_id'])
        if profile:
            return jsonify({"status": "success", "data": profile})
        return jsonify({"status": "error", "message": "Perfil no encontrado."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo cargar el perfil."}), 500


@profile_bp.route('/', methods=['PUT'])
def update_profile():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        errors = {}
        clean = {
            'nombre': require_text(errors, 'fNombre', data.get('nombre'), 'El nombre', min_len=2, max_len=60, person=True),
            'apellido': require_text(errors, 'fApellido', data.get('apellido'), 'El apellido', min_len=2, max_len=60, person=True),
            'direccion': optional_text(errors, 'fDireccion', data.get('direccion'), 'La direccion', max_len=40)
        }
        current = model.get_profile(session['user_id'])
        if current and current.get('tipo') == 'cliente':
            clean['telefono'] = normalize_phone(errors, data.get('telefono'), 'fTelefono', required=True)
        else:
            clean['telefono'] = normalize_phone(errors, data.get('telefono'), 'fTelefono', required=False)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        model.update_profile(session['user_id'], clean)
        session['user_nombre'] = clean['nombre']
        session['user_apellido'] = clean['apellido']
        return jsonify({"status": "success", "message": "Perfil modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el perfil."}), 500


@profile_bp.route('/email', methods=['PUT'])
def update_email():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        errors = {}
        email = normalize_email(errors, data.get('email'), 'email', required=True)
        if errors:
            return jsonify({"status": "error", "message": "Correo invalido.", "errors": {"email": "Ingrese un correo valido."}}), 400
        result = model.update_email(session['user_id'], email)
        if result:
            session['user_email'] = email
            return jsonify({"status": "success", "message": "Correo modificado correctamente."})
        return jsonify({"status": "error", "message": "El correo ya esta en uso", "errors": {"email": "El correo ya esta en uso"}}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el correo."}), 500


@profile_bp.route('/password', methods=['PUT'])
def change_password():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        errors = {}
        if not data.get(CURRENT_CREDENTIAL_FIELD):
            errors[CURRENT_CREDENTIAL_FIELD] = 'Ingrese su contrasena actual'
        if not data.get(NEW_CREDENTIAL_FIELD) or not re.match(CREDENTIAL_PATTERN, data.get(NEW_CREDENTIAL_FIELD, '')):
            errors[NEW_CREDENTIAL_FIELD] = 'Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero, 1 especial (@$!%*?&#.)'
        if data.get(NEW_CREDENTIAL_FIELD) != data.get(CONFIRM_CREDENTIAL_FIELD):
            errors[CONFIRM_CREDENTIAL_FIELD] = 'Las contrasenas no coinciden'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        result = model.change_password(session['user_id'], data[CURRENT_CREDENTIAL_FIELD], data[NEW_CREDENTIAL_FIELD])
        if result:

            return jsonify({"status": "success", "message": "Contrasena modificada correctamente."})
        return jsonify({"status": "error", "message": "Contrasena actual incorrecta.", "errors": {CURRENT_CREDENTIAL_FIELD: "Contrasena actual incorrecta."}}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar la contrasena."}), 500


@profile_bp.route('/photo', methods=['POST'])
def update_photo():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        if 'photo' not in request.files:
            return jsonify({"status": "error", "message": "No se envio archivo."}), 400
        file = request.files['photo']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Archivo vacio."}), 400
        allowed = {'png', 'jpg', 'jpeg', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed:
            return jsonify({"status": "error", "message": "Solo se permiten imagenes png, jpg, jpeg o webp."}), 400
        if file.mimetype not in {'image/png', 'image/jpeg', 'image/webp'}:
            return jsonify({"status": "error", "message": "El archivo no es una imagen valida."}), 400
        profile = model.get_profile(session['user_id'])
        filename = f"user_{session['user_id']}_{int(time.time())}.{ext}"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        try:
            model.update_photo(session['user_id'], filename)
        except Exception:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise
        session['user_foto'] = filename
        old_photo = profile.get('foto_perfil') if profile else None
        if old_photo and old_photo != 'default.png' and old_photo != filename:
            old_path = os.path.join(UPLOAD_FOLDER, old_photo)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
        return jsonify({"status": "success", "message": "Foto modificada correctamente.", "filename": filename})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar la foto."}), 500
