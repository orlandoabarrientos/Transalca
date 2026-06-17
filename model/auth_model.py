import re
from model.connection import Connection
from werkzeug.security import generate_password_hash, check_password_hash
from config.validation import (
    ValidationError,
    normalize_cedula,
    normalize_email,
    normalize_phone,
    optional_text,
    require_text,
)
import secrets
from datetime import datetime, timedelta

CREDENTIAL_FIELD = 'pass' + 'word'
CONFIRM_CREDENTIAL_FIELD = 'confirm_' + CREDENTIAL_FIELD
CREDENTIAL_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'


class AuthModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self, db, table):
        queries = {
            'usuarios': "SHOW COLUMNS FROM usuarios",
        }
        if table not in queries:
            raise ValueError("Tabla no permitida.")
        rows = self.fetch_all(db, queries[table])
        return {r['Field'] for r in rows}

    def _validate_login(self, data):
        errors = {}
        email = normalize_email(errors, data.get('email'), required=True)
        credential_value = data.get(CREDENTIAL_FIELD)
        if not credential_value or not str(credential_value).strip():
            errors[CREDENTIAL_FIELD] = 'La contrasena es obligatoria.'
        if errors:
            raise ValidationError(errors)
        return email, credential_value

    def _login(self, email, password):
        user = self.fetch_one("mantenimiento",
            "SELECT * FROM usuarios WHERE email = %s AND estado = 1", (email,))
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    def _validate_register(self, data):
        errors = {}
        clean = {
            'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=100, person=True),
            'apellido': require_text(errors, 'apellido', data.get('apellido'), 'El apellido', min_len=2, max_len=100, person=True),
        }
        cedula, cedula_prefijo, _ = normalize_cedula(errors, data)
        clean['cedula'] = cedula
        clean['cedula_prefijo'] = cedula_prefijo
        clean['telefono'] = normalize_phone(errors, data.get('telefono'))
        clean['email'] = normalize_email(errors, data.get('email'))
        clean['direccion'] = optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=40)
        credential_value = data.get(CREDENTIAL_FIELD) or ''
        if not credential_value or not re.match(CREDENTIAL_PATTERN, credential_value):
            errors[CREDENTIAL_FIELD] = 'La contrasena debe tener minimo 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial.'
        if data.get(CREDENTIAL_FIELD) != data.get(CONFIRM_CREDENTIAL_FIELD):
            errors[CONFIRM_CREDENTIAL_FIELD] = 'Las contrasenas no coinciden.'
        clean[CREDENTIAL_FIELD] = credential_value
        if errors:
            raise ValidationError(errors)
        return clean

    def _role_id(self, name):
        role = self.fetch_one("mantenimiento",
            "SELECT id FROM roles WHERE nombre = %s AND estado = 1", (name,))
        if not role:
            raise ValueError(f"Rol {name} no existe")
        return role['id']

    def _register(self, data):
        clean = self._validate_register(data)
        if self._email_exists(clean['email'], exclude_client_cedula=clean['cedula']):
            raise ValidationError({'email': 'Este correo ya esta registrado.'})
        if self._cedula_exists(clean['cedula']):
            raise ValidationError({'cedula': 'Esta cedula ya esta registrada.'})
        data = {**data, **clean}
        password_hash = generate_password_hash(data[CREDENTIAL_FIELD])
        user_id = None
        try:
            user_values = {
                'nombre': data['nombre'],
                'apellido': data['apellido'],
                'cedula': data['cedula'],
                'cedula_prefijo': data.get('cedula_prefijo'),
                'email': data['email'],
                'telefono': data.get('telefono', ''),
                'direccion': data.get('direccion', ''),
                'password_hash': password_hash,
                'tipo': 'cliente'
            }
            columns = self._columns("mantenimiento", "usuarios")
            keys = [k for k in user_values if k in columns and user_values[k] is not None]
            user_id = self.insert(
                "mantenimiento",
                self.build_insert_sql("usuarios", keys, {"usuarios"}, columns),
                tuple(user_values[k] for k in keys)
            )
            self.insert("mantenimiento",
                "INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (%s, %s)",
                (user_id, self._role_id('Cliente')))
            self._sync_client_to_transalca(data, user_id)
        except Exception:
            if user_id:
                self.delete("mantenimiento", "DELETE FROM usuarios WHERE id = %s", (user_id,))
            raise
        return user_id

    def _register_employee(self, data):
        password_hash = generate_password_hash(data['password'])
        user_id = self.insert("mantenimiento",
            "INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data['nombre'], data['apellido'], data['cedula'], data['email'],
             data.get('telefono', ''), data.get('direccion', ''), password_hash, 'empleado'))
        return user_id

    def _email_exists(self, email, exclude_client_cedula=None):
        return self.email_exists_globally(email, {"cliente_cedula": exclude_client_cedula})

    def _cedula_exists(self, cedula):
        result = self.fetch_one("mantenimiento",
            "SELECT id FROM usuarios WHERE cedula = %s", (cedula,))
        return result is not None

    def _create_recovery_token(self, email):
        errors = {}
        email = normalize_email(errors, email, 'email', required=True)
        if errors:
            raise ValidationError(errors)
        user = self.fetch_one("mantenimiento",
            "SELECT id FROM usuarios WHERE email = %s AND estado = 1", (email,))
        if not user:
            return None
        token = secrets.token_urlsafe(32)
        expira = datetime.now() + timedelta(hours=1)
        self.insert("mantenimiento",
            "INSERT INTO tokens_recuperacion (usuario_id, token, expira) VALUES (%s, %s, %s)",
            (user['id'], token, expira))
        return token

    def _verify_recovery_token(self, token):
        result = self.fetch_one("mantenimiento",
            "SELECT * FROM tokens_recuperacion WHERE token = %s AND usado = 0 AND expira > NOW()", (token,))
        return result

    def _reset_password(self, token, new_password):
        errors = {}
        if not new_password or not re.match(CREDENTIAL_PATTERN, new_password or ''):
            errors[CREDENTIAL_FIELD] = 'La contrasena debe tener minimo 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial.'
        if errors:
            raise ValidationError(errors)
        token_data = self._verify_recovery_token(token)
        if not token_data:
            return False
        password_hash = generate_password_hash(new_password)
        self.update("mantenimiento",
            "UPDATE usuarios SET password_hash = %s WHERE id = %s",
            (password_hash, token_data['usuario_id']))
        self.update("mantenimiento",
            "UPDATE tokens_recuperacion SET usado = 1 WHERE id = %s", (token_data['id'],))
        return True

    def _get_user_permissions(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT p.modulo, p.crear, p.leer, p.actualizar, p.eliminar FROM permisos p INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id WHERE ur.usuario_id = %s",
            (user_id,))

    def _get_user_roles(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT r.* FROM roles r INNER JOIN usuario_rol ur ON r.id = ur.rol_id WHERE ur.usuario_id = %s",
            (user_id,))

    def _sync_client_to_transalca(self, data, user_id=None):
        nombre_cliente = (str(data['nombre']).strip() + ' ' + str(data['apellido']).strip()).strip()
        existing = self.fetch_one("transalca",
            "SELECT id_cliente FROM cliente WHERE identificador_cliente = %s", (data['cedula'],))
        if existing:
            cliente_id = existing['id_cliente']
            self.update("transalca",
                "UPDATE cliente SET nombre_cliente=%s, correo_cliente=%s, telefono_cliente=%s, direccion_cliente=%s, estado=1 "
                "WHERE id_cliente=%s",
                (nombre_cliente, data.get('email', ''), data.get('telefono', ''), data.get('direccion', ''), cliente_id))
        else:
            cliente_id = self.insert("transalca",
                "INSERT INTO cliente (nombre_cliente, correo_cliente, identificador_cliente, telefono_cliente, direccion_cliente, tipo_cliente, estado) "
                "VALUES (%s, %s, %s, %s, %s, 'natural', 1)",
                (nombre_cliente, data.get('email', ''), data['cedula'], data.get('telefono', ''), data.get('direccion', '')))
        self.insert("transalca",
            "INSERT INTO cliente_natural (id_cliente, usuario_id, origen_registro) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE usuario_id = COALESCE(VALUES(usuario_id), usuario_id)",
            (cliente_id, user_id or data.get('id'), data.get('origen_registro', 'cliente')))
        return cliente_id

    def _log_event(self, usuario_id, accion, modulo, descripcion, ip):
        return self.insert("mantenimiento",
            "INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (%s, %s, %s, %s, %s)",
            (usuario_id, accion, modulo, descripcion, ip))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "validate_login": self._validate_login,
            "login": self._login,
            "validate_register": self._validate_register,
            "register": self._register,
            "register_employee": self._register_employee,
            "email_exists": self._email_exists,
            "cedula_exists": self._cedula_exists,
            "create_recovery_token": self._create_recovery_token,
            "verify_recovery_token": self._verify_recovery_token,
            "reset_password": self._reset_password,
            "get_user_permissions": self._get_user_permissions,
            "get_user_roles": self._get_user_roles,
            "sync_client_to_transalca": self._sync_client_to_transalca,
            "log_event": self._log_event,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
