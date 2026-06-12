from model.connection import Connection
from werkzeug.security import generate_password_hash


class UserModel(Connection):
    def __init__(self):
        super().__init__()
        self._cedula = None
        self._nombre = None
        self._apellido = None
        self._email = None
        self._telefono = None
        self._direccion = None

    @property
    def cedula(self):
        return self._cedula

    @cedula.setter
    def cedula(self, valor):
        if valor:
            valor = str(valor).strip()
        self._cedula = valor

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

    @property
    def apellido(self):
        return self._apellido

    @apellido.setter
    def apellido(self, valor):
        if valor:
            valor = str(valor).strip()
        self._apellido = valor

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        if valor:
            valor = str(valor).strip()
        self._email = valor

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor:
            valor = str(valor).strip()
        self._telefono = valor

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._direccion = valor

    def _columns(self):
        rows = self.fetch_all("mantenimiento", "SHOW COLUMNS FROM usuarios")
        return {r['Field'] for r in rows}

    def _get_all(self, tipo=None):
        if tipo:
            return self.fetch_all("mantenimiento",
                "SELECT u.*, GROUP_CONCAT(r.nombre) as roles FROM usuarios u LEFT JOIN usuario_rol ur ON u.id = ur.usuario_id LEFT JOIN roles r ON ur.rol_id = r.id WHERE u.tipo = %s AND u.estado = 1 GROUP BY u.id ORDER BY u.id DESC",
                (tipo,))
        return self.fetch_all("mantenimiento",
            "SELECT u.*, GROUP_CONCAT(r.nombre) as roles FROM usuarios u LEFT JOIN usuario_rol ur ON u.id = ur.usuario_id LEFT JOIN roles r ON ur.rol_id = r.id WHERE u.estado = 1 GROUP BY u.id ORDER BY u.id DESC")

    def _get_by_id(self, user_id):
        return self.fetch_one("mantenimiento",
            "SELECT * FROM usuarios WHERE id = %s", (user_id,))

    def _create(self, data):
        password_hash = generate_password_hash(data['password'])
        tipo = 'cliente' if data.get('tipo') == 'cliente' else 'empleado'
        self.nombre = data['nombre']
        self.apellido = data['apellido']
        self.cedula = data['cedula']
        self.email = data['email']
        self.telefono = data.get('telefono', '')
        self.direccion = data.get('direccion', '')
        values = {
            'nombre': self._nombre,
            'apellido': self._apellido,
            'cedula': self._cedula,
            'cedula_prefijo': data.get('cedula_prefijo'),
            'email': self._email,
            'telefono': self._telefono,
            'direccion': self._direccion,
            'password_hash': password_hash,
            'tipo': tipo,
            'foto_perfil': data.get('foto_perfil', 'default.png')
        }
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        user_id = self.insert("mantenimiento",
            self.build_insert_sql("usuarios", keys, {"usuarios"}, columns),
            tuple(values[k] for k in keys))
        return user_id

    def _update_info(self, user_id, data):
        tipo = 'cliente' if data.get('tipo') == 'cliente' else 'empleado'
        self.nombre = data['nombre']
        self.apellido = data['apellido']
        self.cedula = data.get('cedula', '')
        self.email = data.get('email', '')
        self.telefono = data.get('telefono', '')
        self.direccion = data.get('direccion', '')
        values = {
            'nombre': self._nombre,
            'apellido': self._apellido,
            'cedula': self._cedula,
            'cedula_prefijo': data.get('cedula_prefijo'),
            'email': self._email,
            'telefono': self._telefono,
            'direccion': self._direccion,
            'tipo': tipo
        }
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        params = [values[k] for k in keys] + [user_id]
        return self.update("mantenimiento",
            self.build_update_by_key_sql("usuarios", keys, "id", {"usuarios"}, columns),
            tuple(params))

    def _update_status(self, user_id, estado):
        return self.update("mantenimiento",
            "UPDATE usuarios SET estado = %s WHERE id = %s", (estado, user_id))

    def _soft_delete(self, user_id):
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

    def _email_exists(self, email, exclude_id=None):
        exclude = {"usuario_id": exclude_id}
        if exclude_id:
            user = self._get_by_id(exclude_id)
            if user:
                exclude["cliente_cedula"] = user.get('cedula')
        return self.email_exists_globally(email, exclude)

    def _cedula_exists(self, cedula, exclude_id=None):
        if exclude_id:
            return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE cedula = %s AND id != %s AND estado = 1", (cedula, exclude_id)) is not None
        return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE cedula = %s AND estado = 1", (cedula,)) is not None

    def _assign_role(self, user_id, rol_id):
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

    def _role_exists(self, rol_id):
        if not rol_id:
            return True
        return self.fetch_one("mantenimiento", "SELECT id FROM roles WHERE id = %s AND estado = 1", (rol_id,)) is not None

    def _remove_role(self, user_id, rol_id):
        return self.delete("mantenimiento",
            "DELETE FROM usuario_rol WHERE usuario_id = %s AND rol_id = %s", (user_id, rol_id))

    def _get_user_roles(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT r.* FROM roles r INNER JOIN usuario_rol ur ON r.id = ur.rol_id WHERE ur.usuario_id = %s",
            (user_id,))

    def _update_photo(self, user_id, filename):
        return self.update("mantenimiento",
            "UPDATE usuarios SET foto_perfil = %s WHERE id = %s", (filename, user_id))

    def _search(self, query):
        search = f"%{query}%"
        return self.fetch_all("mantenimiento",
            "SELECT * FROM usuarios WHERE nombre LIKE %s OR apellido LIKE %s OR cedula LIKE %s OR email LIKE %s",
            (search, search, search, search))

    def _get_by_cedula(self, cedula):
        return self.fetch_one("mantenimiento", "SELECT * FROM usuarios WHERE cedula = %s", (cedula,))

    def _get_by_email(self, email):
        return self.fetch_one("mantenimiento", "SELECT * FROM usuarios WHERE email = %s", (email,))

    def _reactivar(self, user_id, password_hash):
        return self.update("mantenimiento", "UPDATE usuarios SET password_hash = %s, estado = 1 WHERE id = %s", (password_hash, user_id))

    def _get_role_name(self, rol_id):
        return self.fetch_one("mantenimiento", "SELECT nombre FROM roles WHERE id = %s", (rol_id,))

    def _count_active_admins(self):
        return self.fetch_one("mantenimiento",
            "SELECT COUNT(*) as total FROM usuario_rol ur INNER JOIN roles r ON ur.rol_id = r.id INNER JOIN usuarios u ON ur.usuario_id = u.id WHERE r.nombre = 'Administrador' AND u.estado = 1")

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_id": self._get_by_id,
            "create": self._create,
            "update_info": self._update_info,
            "update_status": self._update_status,
            "soft_delete": self._soft_delete,
            "email_exists": self._email_exists,
            "cedula_exists": self._cedula_exists,
            "assign_role": self._assign_role,
            "role_exists": self._role_exists,
            "remove_role": self._remove_role,
            "get_user_roles": self._get_user_roles,
            "update_photo": self._update_photo,
            "search": self._search,
            "get_by_cedula": self._get_by_cedula,
            "get_by_email": self._get_by_email,
            "reactivar": self._reactivar,
            "get_role_name": self._get_role_name,
            "count_active_admins": self._count_active_admins,
            "email_exists_globally": self.email_exists_globally,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
