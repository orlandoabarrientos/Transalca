from model.connection import Connection
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta


class AuthModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self, db, table):
        rows = self.fetch_all(db, f"SHOW COLUMNS FROM {table}")
        return {r['Field'] for r in rows}

    def login(self, email, password):
        user = self.fetch_one("mantenimiento",
            "SELECT * FROM usuarios WHERE email = %s AND estado = 1", (email,))
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    def _role_id(self, name):
        role = self.fetch_one("mantenimiento",
            "SELECT id FROM roles WHERE nombre = %s AND estado = 1", (name,))
        if not role:
            raise ValueError(f"Rol {name} no existe")
        return role['id']

    def _norm(self, value):
        text = (value or '').strip().lower()
        return '' if text == '0000000' else text

    def _existing_client_conflicts(self, data):
        client = self.fetch_one("transalca",
            "SELECT * FROM clientes WHERE cedula = %s", (data['cedula'],))
        if not client:
            return []
        checks = [
            ('nombre', 'nombre'),
            ('apellido', 'apellido'),
            ('telefono', 'telefono'),
            ('email', 'email')
        ]
        conflicts = []
        for field, label in checks:
            current = self._norm(client.get(field))
            incoming = self._norm(data.get(field))
            if current and incoming and current != incoming:
                conflicts.append(label)
        return conflicts

    def register(self, data):
        conflicts = self._existing_client_conflicts(data)
        if conflicts:
            raise ValueError("Los datos no coinciden con el cliente ya registrado: " + ", ".join(conflicts))
        password_hash = generate_password_hash(data['password'])
        user_id = None
        try:
            user_values = {
                'nombre': data['nombre'],
                'apellido': data['apellido'],
                'cedula': data['cedula'],
                'cedula_prefijo': data.get('cedula_prefijo'),
                'cedula_numero': data.get('cedula_numero'),
                'email': data['email'],
                'telefono': data.get('telefono', ''),
                'direccion': data.get('direccion', ''),
                'password_hash': password_hash,
                'tipo': 'cliente'
            }
            columns = self._columns("mantenimiento", "usuarios")
            keys = [k for k in user_values if k in columns and user_values[k] is not None]
            user_id = self.insert("mantenimiento",
                f"INSERT INTO usuarios ({', '.join(keys)}) VALUES ({', '.join(['%s'] * len(keys))})",
                tuple(user_values[k] for k in keys))
            self.insert("mantenimiento",
                "INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (%s, %s)",
                (user_id, self._role_id('Cliente')))
            self.sync_client_to_transalca(data, user_id)
        except Exception:
            if user_id:
                self.delete("mantenimiento", "DELETE FROM usuarios WHERE id = %s", (user_id,))
            raise
        return user_id

    def register_employee(self, data):
        password_hash = generate_password_hash(data['password'])
        user_id = self.insert("mantenimiento",
            "INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data['nombre'], data['apellido'], data['cedula'], data['email'],
             data.get('telefono', ''), data.get('direccion', ''), password_hash, 'empleado'))
        return user_id

    def email_exists(self, email):
        result = self.fetch_one("mantenimiento",
            "SELECT id FROM usuarios WHERE email = %s", (email,))
        return result is not None

    def cedula_exists(self, cedula):
        result = self.fetch_one("mantenimiento",
            "SELECT id FROM usuarios WHERE cedula = %s", (cedula,))
        return result is not None

    def create_recovery_token(self, email):
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

    def verify_recovery_token(self, token):
        result = self.fetch_one("mantenimiento",
            "SELECT * FROM tokens_recuperacion WHERE token = %s AND usado = 0 AND expira > NOW()", (token,))
        return result

    def reset_password(self, token, new_password):
        token_data = self.verify_recovery_token(token)
        if not token_data:
            return False
        password_hash = generate_password_hash(new_password)
        self.update("mantenimiento",
            "UPDATE usuarios SET password_hash = %s WHERE id = %s",
            (password_hash, token_data['usuario_id']))
        self.update("mantenimiento",
            "UPDATE tokens_recuperacion SET usado = 1 WHERE id = %s", (token_data['id'],))
        return True

    def get_user_permissions(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT p.modulo, p.crear, p.leer, p.actualizar, p.eliminar FROM permisos p INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id WHERE ur.usuario_id = %s",
            (user_id,))

    def get_user_roles(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT r.* FROM roles r INNER JOIN usuario_rol ur ON r.id = ur.rol_id WHERE ur.usuario_id = %s",
            (user_id,))

    def sync_client_to_transalca(self, data, user_id=None):
        columns = self._columns("transalca", "clientes")
        existing = self.fetch_one("transalca",
            "SELECT * FROM clientes WHERE cedula = %s", (data['cedula'],))
        values = {
            "cedula": data['cedula'],
            "cedula_prefijo": data.get('cedula_prefijo'),
            "cedula_numero": data.get('cedula_numero'),
            "nombre": data['nombre'],
            "apellido": data['apellido'],
            "telefono": data.get('telefono', ''),
            "email": data.get('email', ''),
            "direccion": data.get('direccion', ''),
            "estado": 1
        }
        if "usuario_id" in columns:
            values["usuario_id"] = user_id or data.get('id')
        if "origen_registro" in columns:
            values["origen_registro"] = (existing or {}).get('origen_registro') or data.get('origen_registro', 'cliente')
        keys = [k for k in values if k in columns]
        placeholders = ", ".join(["%s"] * len(keys))
        update_sql = ", ".join([f"{k}=VALUES({k})" for k in keys if k != "cedula"])
        sql = (
            f"INSERT INTO clientes ({', '.join(keys)}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_sql}"
        )
        return self.insert("transalca", sql, tuple(values[k] for k in keys))
