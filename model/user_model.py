from model.connection import Connection
from werkzeug.security import generate_password_hash


class UserModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self):
        rows = self.fetch_all("mantenimiento", "SHOW COLUMNS FROM usuarios")
        return {r['Field'] for r in rows}

    def get_all(self, tipo=None):
        if tipo:
            return self.fetch_all("mantenimiento",
                "SELECT u.*, GROUP_CONCAT(r.nombre) as roles FROM usuarios u LEFT JOIN usuario_rol ur ON u.id = ur.usuario_id LEFT JOIN roles r ON ur.rol_id = r.id WHERE u.tipo = %s AND u.estado = 1 GROUP BY u.id ORDER BY u.id DESC",
                (tipo,))
        return self.fetch_all("mantenimiento",
            "SELECT u.*, GROUP_CONCAT(r.nombre) as roles FROM usuarios u LEFT JOIN usuario_rol ur ON u.id = ur.usuario_id LEFT JOIN roles r ON ur.rol_id = r.id WHERE u.estado = 1 GROUP BY u.id ORDER BY u.id DESC")

    def get_by_id(self, user_id):
        return self.fetch_one("mantenimiento",
            "SELECT * FROM usuarios WHERE id = %s", (user_id,))

    def create(self, data):
        password_hash = generate_password_hash(data['password'])
        tipo = 'cliente' if data.get('tipo') == 'cliente' else 'empleado'
        values = {
            'nombre': data['nombre'].strip(),
            'apellido': data['apellido'].strip(),
            'cedula': data['cedula'].strip(),
            'cedula_prefijo': data.get('cedula_prefijo'),
            'email': data['email'].strip(),
            'telefono': data.get('telefono', '').strip(),
            'direccion': data.get('direccion', '').strip(),
            'password_hash': password_hash,
            'tipo': tipo,
            'foto_perfil': data.get('foto_perfil', 'default.png')
        }
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        user_id = self.insert("mantenimiento",
            f"INSERT INTO usuarios ({', '.join(keys)}) VALUES ({', '.join(['%s'] * len(keys))})",
            tuple(values[k] for k in keys))
        return user_id

    def update_info(self, user_id, data):
        tipo = 'cliente' if data.get('tipo') == 'cliente' else 'empleado'
        values = {
            'nombre': data['nombre'].strip(),
            'apellido': data['apellido'].strip(),
            'cedula': data.get('cedula', '').strip(),
            'cedula_prefijo': data.get('cedula_prefijo'),
            'email': data.get('email', '').strip(),
            'telefono': data.get('telefono', '').strip(),
            'direccion': data.get('direccion', '').strip(),
            'tipo': tipo
        }
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        params = [values[k] for k in keys] + [user_id]
        return self.update("mantenimiento",
            f"UPDATE usuarios SET {', '.join([f'{k} = %s' for k in keys])} WHERE id = %s",
            tuple(params))

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
        exclude = {"usuario_id": exclude_id}
        if exclude_id:
            user = self.get_by_id(exclude_id)
            if user:
                exclude["cliente_cedula"] = user.get('cedula')
        return self.email_exists_globally(email, exclude)

    def cedula_exists(self, cedula, exclude_id=None):
        if exclude_id:
            return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE cedula = %s AND id != %s AND estado = 1", (cedula, exclude_id)) is not None
        return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE cedula = %s AND estado = 1", (cedula,)) is not None

    def assign_role(self, user_id, rol_id):
        existing = self.fetch_one("mantenimiento",
            "SELECT id FROM usuario_rol WHERE usuario_id = %s AND rol_id = %s", (user_id, rol_id))
        role = self.fetch_one("mantenimiento", "SELECT nombre FROM roles WHERE id = %s", (rol_id,))
        if role:
            tipo = 'cliente' if role['nombre'] == 'Cliente' else 'empleado'
            self.update("mantenimiento", "UPDATE usuarios SET tipo = %s WHERE id = %s", (tipo, user_id))
        if not existing:
            return self.insert("mantenimiento",
                "INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (%s, %s)", (user_id, rol_id))
        return existing['id']

    def role_exists(self, rol_id):
        if not rol_id:
            return True
        return self.fetch_one("mantenimiento", "SELECT id FROM roles WHERE id = %s AND estado = 1", (rol_id,)) is not None

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

    def get_by_cedula(self, cedula):
        return self.fetch_one("mantenimiento", "SELECT * FROM usuarios WHERE cedula = %s", (cedula,))

    def get_by_email(self, email):
        return self.fetch_one("mantenimiento", "SELECT * FROM usuarios WHERE email = %s", (email,))
