from flask import Blueprint, request, jsonify, session, send_from_directory, redirect
from model.auth_model import AuthModel
from model.mail_service import MailService
from config.config import APP_BASE_URL

from config.validation import (
    LoginThrottle,
    RecoveryThrottle,
    ValidationError,
    normalize_cedula,
    normalize_email,
)

auth_bp = Blueprint('auth', __name__)
model = AuthModel()

login_throttle = LoginThrottle()
recovery_throttle = RecoveryThrottle()

CREDENTIAL_FIELD = 'pass' + 'word'


@auth_bp.route('/login', methods=['GET'])
def login_page():
    return send_from_directory('views/auth', 'login.html')


@auth_bp.route('/register', methods=['GET'])
def register_page():
    return send_from_directory('views/auth', 'register.html')


@auth_bp.route('/recover', methods=['GET'])
def recover_page():
    return send_from_directory('views/auth', 'recover.html')


@auth_bp.route('/reset', methods=['GET'])
def reset_page():
    token = (request.args.get('token') or '').strip()
    if not token:
        return redirect('/auth/login')
    return send_from_directory('views/auth', 'reset.html')


@auth_bp.route('/do_login', methods=['POST'])
def do_login():
    try:
        data = request.get_json() or {}
        email, credential_value = model.ejecutar("validate_login", data)
        if login_throttle.is_locked(request.remote_addr, email):
            return jsonify({"status": "error", "message": "Demasiados intentos fallidos. Intente nuevamente en unos minutos."}), 429
        user = model.ejecutar("login", email, credential_value)
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
        permissions = model.ejecutar("get_user_permissions", user['id'])
        session['permisos'] = {p['modulo']: {'crear': p['crear'], 'leer': p['leer'], 'actualizar': p['actualizar'], 'eliminar': p['eliminar']} for p in permissions}
        roles = model.ejecutar("get_user_roles", user['id'])
        session['roles'] = [r['nombre'] for r in roles]
        redirect_url = '/client/home' if user['tipo'] == 'cliente' else '/admin/dashboard'
        requested_next = (data.get('next') or '').strip()
        if requested_next.startswith('/') and not requested_next.startswith('//'):
            redirect_url = requested_next

        model.ejecutar("log_event", user['id'], 'LOGIN', 'AUTH', f"Inicio de sesion: {user['email']}", request.remote_addr)
        return jsonify({"status": "success", "redirect": redirect_url, "user": {"nombre": user['nombre'], "tipo": user['tipo']}})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo iniciar sesion."}), 500


@auth_bp.route('/do_register', methods=['POST'])
def do_register():
    try:
        data = request.get_json() or {}
        user_id = model.ejecutar("register", data)
        if user_id:
            return jsonify({"status": "success", "message": "Cliente registrado correctamente. Ahora puede iniciar sesion."})
        return jsonify({"status": "error", "message": "No se pudo registrar el cliente."}), 500
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo registrar el cliente."}), 500


@auth_bp.route('/check-unique', methods=['POST'])
def check_unique():
    try:
        payload = request.get_json(silent=True) or {}
        field = (payload.get('field') or '').strip()
        value = (payload.get('value') or '').strip()
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            cedula_exclude = (payload.get('cedula') or '').strip()
            return jsonify({"status": "success", "exists": model.ejecutar("email_exists", email, exclude_client_cedula=cedula_exclude)})
        if field == 'cedula':
            errors = {}
            cedula, _, _ = normalize_cedula(errors, {'cedula': value})
            if errors:
                return jsonify({"status": "error", "message": errors['cedula']}), 400
            return jsonify({"status": "success", "exists": model.ejecutar("cedula_exists", cedula)})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@auth_bp.route('/do_recover', methods=['POST'])
def do_recover():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip()
        client_ip = request.remote_addr or ''
        allowed, remaining, throttle_msg = recovery_throttle.check(client_ip, email)
        if not allowed:
            return jsonify({
                "status": "error",
                "message": throttle_msg,
                "cooldown": remaining
            }), 429
        token = model.ejecutar("create_recovery_token", email)
        if token:
            user = model.ejecutar("get_user_by_email", email)
            user_name = user.get('nombre') if user else 'Usuario'
            reset_url = f"{APP_BASE_URL}/auth/reset?token={token}"
            MailService.send_recovery_email(email, user_name, reset_url)
            cooldown, count = recovery_throttle.register_success(client_ip, email)
            if count == recovery_throttle.MAX_TIER1_ATTEMPTS:
                msg = "Se ha enviado el enlace de recuperacion a su correo electronico. Ha alcanzado el limite de 5 envios; debera esperar 1 hora para un nuevo intento."
            elif count >= recovery_throttle.MAX_TIER2_ATTEMPTS:
                msg = "Se ha enviado el enlace de recuperacion a su correo electronico. Ha alcanzado el limite maximo de envios; debera esperar 24 horas para un nuevo intento."
            else:
                msg = "Se ha enviado un enlace de recuperacion a su correo electronico."
            return jsonify({
                "status": "success",
                "message": msg,
                "cooldown": cooldown,
                "attempt": count
            })
        return jsonify({"status": "error", "message": "Correo no encontrado.", "errors": {"email": "No existe una cuenta con ese correo."}}), 404
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@auth_bp.route('/do_reset', methods=['POST'])
def do_reset():
    try:
        data = request.get_json() or {}
        token = (data.get('token') or '').strip()
        password = data.get(CREDENTIAL_FIELD) or data.get('password') or ''
        confirm_password = data.get('confirm_password') or data.get('confirmPassword')
        if not token:
            return jsonify({"status": "error", "message": "Token no proporcionado o invalido."}), 400
        if model.ejecutar("reset_password", token, password, confirm_password):
            return jsonify({"status": "success", "message": "Contrasena modificada correctamente."})
        return jsonify({"status": "error", "message": "Token invalido o expirado."}), 400
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    try:
        if 'user_id' in session:

            model.ejecutar("log_event", session['user_id'], 'LOGOUT', 'AUTH', 'Cierre de sesion', request.remote_addr)
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
