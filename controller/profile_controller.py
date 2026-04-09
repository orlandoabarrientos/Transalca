from flask import Blueprint, request, jsonify, session
from model.profile_model import ProfileModel
from model.bitacora_model import BitacoraModel
import os
import re
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)
model = ProfileModel()
bitacora = BitacoraModel()
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'profile_pics')
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'


@profile_bp.route('/', methods=['GET'])
def get_profile():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        profile = model.get_profile(session['user_id'])
        if profile:
            return jsonify({"status": "success", "data": profile})
        return jsonify({"status": "error", "message": "Perfil no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@profile_bp.route('/', methods=['PUT'])
def update_profile():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        if not data.get('apellido') or len(data['apellido'].strip()) < 2:
            errors['apellido'] = 'El apellido debe tener al menos 2 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_profile(session['user_id'], data)
        session['user_nombre'] = data['nombre']
        session['user_apellido'] = data['apellido']
        return jsonify({"status": "success", "message": "Perfil actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@profile_bp.route('/email', methods=['PUT'])
def update_email():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        if not data.get('email') or not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')):
            return jsonify({"status": "error", "message": "Correo invalido", "errors": {"email": "Ingrese un correo valido"}}), 400
        result = model.update_email(session['user_id'], data['email'].strip())
        if result:
            session['user_email'] = data['email']
            return jsonify({"status": "success", "message": "Correo actualizado"})
        return jsonify({"status": "error", "message": "El correo ya esta en uso", "errors": {"email": "El correo ya esta en uso"}}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@profile_bp.route('/password', methods=['PUT'])
def change_password():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('old_password'):
            errors['old_password'] = 'Ingrese su contrasena actual'
        if not data.get('new_password') or not re.match(PASSWORD_REGEX, data.get('new_password', '')):
            errors['new_password'] = 'Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero, 1 especial (@$!%*?&#.)'
        if data.get('new_password') != data.get('confirm_password'):
            errors['confirm_password'] = 'Las contrasenas no coinciden'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        result = model.change_password(session['user_id'], data['old_password'], data['new_password'])
        if result:
            bitacora.log_action(session['user_id'], 'MODIFICAR', 'PERFIL', 'Contrasena cambiada', request.remote_addr)
            return jsonify({"status": "success", "message": "Contrasena actualizada"})
        return jsonify({"status": "error", "message": "Contrasena actual incorrecta", "errors": {"old_password": "Contrasena actual incorrecta"}}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@profile_bp.route('/photo', methods=['POST'])
def update_photo():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if 'photo' not in request.files:
            return jsonify({"status": "error", "message": "No se envio archivo"}), 400
        file = request.files['photo']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Archivo vacio"}), 400
        allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed:
            return jsonify({"status": "error", "message": "Solo se permiten imagenes (png, jpg, jpeg, gif, webp)"}), 400
        filename = f"user_{session['user_id']}_{secure_filename(file.filename)}"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        model.update_photo(session['user_id'], filename)
        session['user_foto'] = filename
        return jsonify({"status": "success", "message": "Foto actualizada", "filename": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
