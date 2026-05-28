from flask import Blueprint, request, jsonify, session, send_from_directory
from model.auth_model import AuthModel
from model.bitacora_model import BitacoraModel
from config.validation import (
    LoginThrottle,
    normalize_cedula,
    normalize_email,
    normalize_phone,
    optional_text,
    require_text,
)
import re

auth_bp = Blueprint('auth', __name__)
model = AuthModel()
bitacora = BitacoraModel()
login_throttle = LoginThrottle()

PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'


@auth_bp.route('/login', methods=['GET'])
def login_page():
    return send_from_directory('views/auth', 'login.html')


@auth_bp.route('/register', methods=['GET'])
def register_page():
    return send_from_directory('views/auth', 'register.html')


@auth_bp.route('/recover', methods=['GET'])
def recover_page():
    return send_from_directory('views/auth', 'recover.html')


@auth_bp.route('/do_login', methods=['POST'])
def do_login():
    try:
        data = request.get_json() or {}
        errors = {}
        email = normalize_email(errors, data.get('email'), required=True)
        password = data.get('password')
        if not password or not str(password).strip():
            errors['password'] = 'La contrasena es obligatoria.'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if login_throttle.is_locked(request.remote_addr, email):
            return jsonify({"status": "error", "message": "Demasiados intentos fallidos. Intente nuevamente en unos minutos."}), 429
        user = model.login(email, password)
        if not user:
            login_throttle.register_failure(request.remote_addr, email)
            return jsonify({"status": "error", "message": "Credenciales incorrectas."}), 401
        if not user['estado']:
            return jsonify({"status": "error", "message": "Usuario inactivo. Contacte al administrador."}), 403
        login_throttle.clear(request.remote_addr, email)
        session['user_id'] = user['id']
        session['user_cedula'] = user['cedula']
        session['user_nombre'] = user['nombre']
        session['user_apellido'] = user['apellido']
        session['user_email'] = user['email']
        session['user_tipo'] = user['tipo']
        session['user_foto'] = user['foto_perfil']
        permissions = model.get_user_permissions(user['id'])
        session['permisos'] = {p['modulo']: {'crear': p['crear'], 'leer': p['leer'], 'actualizar': p['actualizar'], 'eliminar': p['eliminar']} for p in permissions}
        roles = model.get_user_roles(user['id'])
        session['roles'] = [r['nombre'] for r in roles]
        redirect_url = '/client/home' if user['tipo'] == 'cliente' else '/admin/dashboard'
        requested_next = (data.get('next') or '').strip()
        if requested_next.startswith('/') and not requested_next.startswith('//'):
            redirect_url = requested_next
        bitacora.log_action(user['id'], 'LOGIN', 'AUTH', f"Inicio de sesion: {user['email']}", request.remote_addr)
        return jsonify({"status": "success", "redirect": redirect_url, "user": {"nombre": user['nombre'], "tipo": user['tipo']}})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo iniciar sesion."}), 500


@auth_bp.route('/do_register', methods=['POST'])
def do_register():
    try:
        data = request.get_json() or {}
        errors = {}
        nombre = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=100, person=True)
        apellido = require_text(errors, 'apellido', data.get('apellido'), 'El apellido', min_len=2, max_len=100, person=True)
        cedula, cedula_prefijo, _ = normalize_cedula(errors, data)
        telefono = normalize_phone(errors, data.get('telefono'))
        email = normalize_email(errors, data.get('email'))
        direccion = optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=300)
        if not data.get('password') or not re.match(PASSWORD_REGEX, data.get('password', '')):
            errors['password'] = 'La contrasena debe tener minimo 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial.'
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = 'Las contrasenas no coinciden.'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        data.update({
            'nombre': nombre,
            'apellido': apellido,
            'cedula': cedula,
            'cedula_prefijo': cedula_prefijo,
            'telefono': telefono,
            'email': email,
            'direccion': direccion
        })
        if model.email_exists(email, exclude_client_cedula=cedula):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        if model.cedula_exists(cedula):
            return jsonify({"status": "error", "message": "Esta cedula ya esta registrada.", "errors": {"cedula": "Esta cedula ya esta registrada."}}), 400
        user_id = model.register(data)
        if user_id:
            return jsonify({"status": "success", "message": "Cliente registrado correctamente. Ahora puede iniciar sesion."})
        return jsonify({"status": "error", "message": "No se pudo registrar el cliente."}), 500
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo registrar el cliente."}), 500


@auth_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        field = (request.args.get('field') or '').strip()
        value = (request.args.get('value') or '').strip()
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            cedula_exclude = (request.args.get('cedula') or '').strip()
            return jsonify({"status": "success", "exists": model.email_exists(email, exclude_client_cedula=cedula_exclude)})
        if field == 'cedula':
            errors = {}
            cedula, _, _ = normalize_cedula(errors, {'cedula': value})
            if errors:
                return jsonify({"status": "error", "message": errors['cedula']}), 400
            return jsonify({"status": "success", "exists": model.cedula_exists(cedula)})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@auth_bp.route('/do_recover', methods=['POST'])
def do_recover():
    try:
        data = request.get_json()
        if not data.get('email') or not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')):
            return jsonify({"status": "error", "message": "Ingrese un correo valido.", "errors": {"email": "Ingrese un correo valido."}}), 400
        token = model.create_recovery_token(data['email'].strip())
        if token:
            return jsonify({"status": "success", "message": "Se ha generado un enlace de recuperacion.", "token": token})
        return jsonify({"status": "error", "message": "Correo no encontrado.", "errors": {"email": "No existe una cuenta con ese correo."}}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@auth_bp.route('/do_reset', methods=['POST'])
def do_reset():
    try:
        data = request.get_json()
        if not data.get('password') or not re.match(PASSWORD_REGEX, data.get('password', '')):
            return jsonify({"status": "error", "message": "La contrasena debe tener minimo 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial.", "errors": {"password": "Contrasena no cumple requisitos."}}), 400
        if model.reset_password(data.get('token', ''), data['password']):
            return jsonify({"status": "success", "message": "Contrasena modificada correctamente."})
        return jsonify({"status": "error", "message": "Token invalido o expirado."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    try:
        if 'user_id' in session:
            bitacora.log_action(session['user_id'], 'LOGOUT', 'AUTH', 'Cierre de sesion', request.remote_addr)
        session.clear()
        return jsonify({"status": "success", "redirect": "/auth/login"})
    except Exception:
        session.clear()
        return jsonify({"status": "success", "redirect": "/auth/login"})


@auth_bp.route('/session', methods=['GET'])
def get_session():
    if 'user_id' in session:
        return jsonify({
            "status": "success",
            "user": {
                "id": session['user_id'],
                "cedula": session.get('user_cedula', ''),
                "nombre": session['user_nombre'],
                "apellido": session.get('user_apellido', ''),
                "email": session['user_email'],
                "tipo": session['user_tipo'],
                "foto": session.get('user_foto', 'default.png'),
                "permisos": session.get('permisos', {}),
                "roles": session.get('roles', [])
            }
        })
    return jsonify({"status": "error", "message": "No autenticado."}), 401
