from model.connection import Connection
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta


class AuthModel(Connection):
    def __init__(self):
        super().__init__()

    def login(self, email, password):
        user = self.fetch_one("mantenimiento",
            "SELECT * FROM usuarios WHERE email = %s AND estado = 1", (email,))
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    def register(self, data):
        password_hash = generate_password_hash(data['password'])
        user_id = self.insert("mantenimiento",
            "INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data['nombre'], data['apellido'], data['cedula'], data['email'],
             data.get('telefono', ''), data.get('direccion', ''), password_hash, 'cliente'))
        self.insert("mantenimiento",
            "INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (%s, 3)", (user_id,))
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
