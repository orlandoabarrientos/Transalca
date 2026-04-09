from model.connection import Connection
from werkzeug.security import generate_password_hash


class UserModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self, tipo=None):
        if tipo:
            return self.fetch_all("mantenimiento",
                "SELECT u.*, GROUP_CONCAT(r.nombre) as roles FROM usuarios u LEFT JOIN usuario_rol ur ON u.id = ur.usuario_id LEFT JOIN roles r ON ur.rol_id = r.id WHERE u.tipo = %s GROUP BY u.id ORDER BY u.id DESC",
                (tipo,))
        return self.fetch_all("mantenimiento",
            "SELECT u.*, GROUP_CONCAT(r.nombre) as roles FROM usuarios u LEFT JOIN usuario_rol ur ON u.id = ur.usuario_id LEFT JOIN roles r ON ur.rol_id = r.id GROUP BY u.id ORDER BY u.id DESC")

    def get_by_id(self, user_id):
        return self.fetch_one("mantenimiento",
            "SELECT * FROM usuarios WHERE id = %s", (user_id,))

    def create(self, data):
        password_hash = generate_password_hash(data['password'])
        return self.insert("mantenimiento",
            "INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo, foto_perfil) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (data['nombre'].strip(), data['apellido'].strip(), data['cedula'].strip(), data['email'].strip(),
             data.get('telefono', '').strip(), data.get('direccion', '').strip(), password_hash,
             data.get('tipo', 'cliente'), data.get('foto_perfil', 'default.png')))

    def update_info(self, user_id, data):
        return self.update("mantenimiento",
            "UPDATE usuarios SET nombre = %s, apellido = %s, cedula = %s, email = %s, telefono = %s, direccion = %s, tipo = %s WHERE id = %s",
            (data['nombre'].strip(), data['apellido'].strip(), data.get('cedula', '').strip(), data.get('email', '').strip(),
             data.get('telefono', '').strip(), data.get('direccion', '').strip(), data.get('tipo', 'cliente'), user_id))

    def update_status(self, user_id, estado):
        return self.update("mantenimiento",
            "UPDATE usuarios SET estado = %s WHERE id = %s", (estado, user_id))

    def soft_delete(self, user_id):
        is_admin = self.fetch_one("mantenimiento",
            "SELECT ur.id FROM usuario_rol ur INNER JOIN roles r ON ur.rol_id = r.id WHERE ur.usuario_id = %s AND r.nombre = 'Administrador'",
            (user_id,))
        if is_admin:
            admin_count = self.fetch_one("mantenimiento",
                "SELECT COUNT(*) as total FROM usuario_rol ur INNER JOIN roles r ON ur.rol_id = r.id INNER JOIN usuarios u ON ur.usuario_id = u.id WHERE r.nombre = 'Administrador' AND u.estado = 1")
            if admin_count and admin_count['total'] <= 1:
                return False
        return self.update("mantenimiento",
            "UPDATE usuarios SET estado = 0 WHERE id = %s", (user_id,))

    def email_exists(self, email, exclude_id=None):
        if exclude_id:
            return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE email = %s AND id != %s", (email, exclude_id)) is not None
        return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE email = %s", (email,)) is not None

    def cedula_exists(self, cedula, exclude_id=None):
        if exclude_id:
            return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE cedula = %s AND id != %s", (cedula, exclude_id)) is not None
        return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE cedula = %s", (cedula,)) is not None

    def assign_role(self, user_id, rol_id):
        existing = self.fetch_one("mantenimiento",
            "SELECT id FROM usuario_rol WHERE usuario_id = %s AND rol_id = %s", (user_id, rol_id))
        if not existing:
            return self.insert("mantenimiento",
                "INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (%s, %s)", (user_id, rol_id))
        return existing['id']

    def remove_role(self, user_id, rol_id):
        return self.delete("mantenimiento",
            "DELETE FROM usuario_rol WHERE usuario_id = %s AND rol_id = %s", (user_id, rol_id))

    def get_user_roles(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT r.* FROM roles r INNER JOIN usuario_rol ur ON r.id = ur.rol_id WHERE ur.usuario_id = %s",
            (user_id,))

    def update_photo(self, user_id, filename):
        return self.update("mantenimiento",
            "UPDATE usuarios SET foto_perfil = %s WHERE id = %s", (filename, user_id))

    def search(self, query):
        search = f"%{query}%"
        return self.fetch_all("mantenimiento",
            "SELECT * FROM usuarios WHERE nombre LIKE %s OR apellido LIKE %s OR cedula LIKE %s OR email LIKE %s",
            (search, search, search, search))
