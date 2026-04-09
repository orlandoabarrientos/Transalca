from model.connection import Connection
from werkzeug.security import generate_password_hash, check_password_hash


class ProfileModel(Connection):
    def __init__(self):
        super().__init__()

    def get_profile(self, user_id):
        return self.fetch_one("mantenimiento",
            "SELECT id, nombre, apellido, cedula, email, telefono, direccion, tipo, foto_perfil, created_at FROM usuarios WHERE id = %s",
            (user_id,))

    def update_profile(self, user_id, data):
        return self.update("mantenimiento",
            "UPDATE usuarios SET nombre = %s, apellido = %s, telefono = %s, direccion = %s WHERE id = %s",
            (data['nombre'], data['apellido'], data.get('telefono', ''), data.get('direccion', ''), user_id))

    def update_email(self, user_id, email):
        existing = self.fetch_one("mantenimiento",
            "SELECT id FROM usuarios WHERE email = %s AND id != %s", (email, user_id))
        if existing:
            return False
        self.update("mantenimiento",
            "UPDATE usuarios SET email = %s WHERE id = %s", (email, user_id))
        return True

    def change_password(self, user_id, old_password, new_password):
        user = self.fetch_one("mantenimiento",
            "SELECT password_hash FROM usuarios WHERE id = %s", (user_id,))
        if not user or not check_password_hash(user['password_hash'], old_password):
            return False
        password_hash = generate_password_hash(new_password)
        self.update("mantenimiento",
            "UPDATE usuarios SET password_hash = %s WHERE id = %s", (password_hash, user_id))
        return True

    def update_photo(self, user_id, filename):
        return self.update("mantenimiento",
            "UPDATE usuarios SET foto_perfil = %s WHERE id = %s", (filename, user_id))
