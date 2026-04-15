from flask import Blueprint, request, jsonify, session, send_from_directory
from model.auth_model import AuthModel
from model.bitacora_model import BitacoraModel
import re

auth_bp = Blueprint('auth', __name__)
model = AuthModel()
bitacora = BitacoraModel()

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
        data = request.get_json()
        errors = {}
        if not data.get('email') or not data['email'].strip():
            errors['email'] = 'El correo es requerido'
        if not data.get('password') or not data['password'].strip():
            errors['password'] = 'La contrasena es requerida'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        user = model.login(data['email'].strip(), data['password'])
        if not user:
            return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401
        if not user['estado']:
            return jsonify({"status": "error", "message": "Usuario inactivo. Contacte al administrador"}), 403
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
        redirect_url = '/admin/dashboard' if user['tipo'] == 'empleado' else '/client/home'
        requested_next = (data.get('next') or '').strip()
        if requested_next.startswith('/') and not requested_next.startswith('//'):
            redirect_url = requested_next
        bitacora.log_action(user['id'], 'LOGIN', 'AUTH', f"Inicio de sesion: {user['email']}", request.remote_addr)
        # Sync user to db_transalca (clientes or usuarios table)
        model.sync_to_transalca(user)
        return jsonify({"status": "success", "redirect": redirect_url, "user": {"nombre": user['nombre'], "tipo": user['tipo']}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/do_register', methods=['POST'])
def do_register():
    try:
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        if not data.get('apellido') or len(data['apellido'].strip()) < 2:
            errors['apellido'] = 'El apellido debe tener al menos 2 caracteres'
        if not data.get('cedula') or len(data['cedula'].strip()) < 5:
            errors['cedula'] = 'La cedula debe tener al menos 5 caracteres'
        if not data.get('email') or not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')):
            errors['email'] = 'Ingrese un correo valido'
        if not data.get('password') or not re.match(PASSWORD_REGEX, data.get('password', '')):
            errors['password'] = 'La contrasena debe tener minimo 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial (@$!%*?&#.)'
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = 'Las contrasenas no coinciden'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.email_exists(data['email'].strip()):
            return jsonify({"status": "error", "message": "El correo ya esta registrado", "errors": {"email": "El correo ya esta registrado"}}), 400
        if model.cedula_exists(data['cedula'].strip()):
            return jsonify({"status": "error", "message": "La cedula ya esta registrada", "errors": {"cedula": "La cedula ya esta registrada"}}), 400
        user_id = model.register(data)
        if user_id:
            # Sync new client to db_transalca.clientes
            model.sync_client_to_transalca(data)
            return jsonify({"status": "success", "message": "Registro exitoso. Ahora puede iniciar sesion"})
        return jsonify({"status": "error", "message": "Error al registrar"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/do_recover', methods=['POST'])
def do_recover():
    try:
        data = request.get_json()
        if not data.get('email') or not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')):
            return jsonify({"status": "error", "message": "Ingrese un correo valido", "errors": {"email": "Ingrese un correo valido"}}), 400
        token = model.create_recovery_token(data['email'].strip())
        if token:
            return jsonify({"status": "success", "message": "Se ha generado un enlace de recuperacion", "token": token})
        return jsonify({"status": "error", "message": "Correo no encontrado", "errors": {"email": "No existe una cuenta con ese correo"}}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/do_reset', methods=['POST'])
def do_reset():
    try:
        data = request.get_json()
        if not data.get('password') or not re.match(PASSWORD_REGEX, data.get('password', '')):
            return jsonify({"status": "error", "message": "La contrasena debe tener minimo 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial", "errors": {"password": "Contrasena no cumple requisitos"}}), 400
        if model.reset_password(data.get('token', ''), data['password']):
            return jsonify({"status": "success", "message": "Contrasena actualizada"})
        return jsonify({"status": "error", "message": "Token invalido o expirado"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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
    return jsonify({"status": "error", "message": "No autenticado"}), 401
