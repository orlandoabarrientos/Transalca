from model.connection import Connection


class RoleModel(Connection):
    def __init__(self):
        super().__init__()
        self._nombre = None
        self._descripcion = None

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

    @property
    def descripcion(self):
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._descripcion = valor

    def _get_all(self):
        return self.fetch_all("mantenimiento", "SELECT * FROM roles WHERE estado = 1 ORDER BY id")

    def _get_by_id(self, role_id):
        return self.fetch_one("mantenimiento", "SELECT * FROM roles WHERE id = %s", (role_id,))

    def _create(self, data):
        self.nombre = data['nombre']
        self.descripcion = data.get('descripcion', '')
        return self.insert("mantenimiento",
            "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)",
            (self._nombre, self._descripcion))

    def _update_role(self, role_id, data):
        self.nombre = data['nombre']
        self.descripcion = data.get('descripcion', '')
        return self.update("mantenimiento",
            "UPDATE roles SET nombre = %s, descripcion = %s WHERE id = %s",
            (self._nombre, self._descripcion, role_id))

    def _soft_delete(self, role_id):
        role = self._get_by_id(role_id)
        if role and role['nombre'] == 'Administrador':
            return False
        if not role:
            return None
        self.update("mantenimiento", "UPDATE roles SET estado = 0 WHERE id = %s", (role_id,))
        return 0

    def _update_status(self, role_id, estado):
        return self.update("mantenimiento",
            "UPDATE roles SET estado = %s WHERE id = %s", (estado, role_id))

    def _get_permissions(self, role_id):
        return self.fetch_all("mantenimiento",
            "SELECT * FROM permisos WHERE rol_id = %s", (role_id,))

    def _set_permission(self, role_id, modulo, crear, leer, actualizar, eliminar):
        existing = self.fetch_one("mantenimiento",
            "SELECT id FROM permisos WHERE rol_id = %s AND modulo = %s", (role_id, modulo))
        if existing:
            return self.update("mantenimiento",
                "UPDATE permisos SET crear = %s, leer = %s, actualizar = %s, eliminar = %s WHERE id = %s",
                (crear, leer, actualizar, eliminar, existing['id']))
        return self.insert("mantenimiento",
            "INSERT INTO permisos (rol_id, modulo, crear, leer, actualizar, eliminar) VALUES (%s, %s, %s, %s, %s, %s)",
            (role_id, modulo, crear, leer, actualizar, eliminar))

    def _save_all_permissions(self, role_id, permissions):
        self.delete("mantenimiento", "DELETE FROM permisos WHERE rol_id = %s", (role_id,))
        for perm in permissions:
            self.insert("mantenimiento",
                "INSERT INTO permisos (rol_id, modulo, crear, leer, actualizar, eliminar) VALUES (%s, %s, %s, %s, %s, %s)",
                (role_id, perm['modulo'], perm.get('crear', 0), perm.get('leer', 0),
                 perm.get('actualizar', 0), perm.get('eliminar', 0)))

    def _get_modules(self):
        return [
            'usuarios', 'roles', 'productos', 'categorias', 'marcas',
            'proveedores', 'mecanicos', 'stock', 'servicios',
            'empresas', 'creditos', 'metodos_pago',
            'promociones', 'ordenes', 'pagos', 'bitacora', 'reportes',
            'respaldos', 'qr', 'sucursales',
            'vehiculos', 'comisiones', 'tickets', 'notificaciones',
            'mantenimiento', 'tasas_avanzadas', 'filtros',
            'bitacora_vehiculo'
        ]

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_id": self._get_by_id,
            "create": self._create,
            "update_role": self._update_role,
            "soft_delete": self._soft_delete,
            "update_status": self._update_status,
            "get_permissions": self._get_permissions,
            "set_permission": self._set_permission,
            "save_all_permissions": self._save_all_permissions,
            "get_modules": self._get_modules,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
