from model.connection import Connection


class RoleModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("mantenimiento", "SELECT * FROM roles ORDER BY id")

    def get_by_id(self, role_id):
        return self.fetch_one("mantenimiento", "SELECT * FROM roles WHERE id = %s", (role_id,))

    def create(self, data):
        return self.insert("mantenimiento",
            "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)",
            (data['nombre'].strip(), data.get('descripcion', '').strip()))

    def update_role(self, role_id, data):
        return self.update("mantenimiento",
            "UPDATE roles SET nombre = %s, descripcion = %s WHERE id = %s",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), role_id))

    def soft_delete(self, role_id):
        role = self.get_by_id(role_id)
        if role and role['nombre'] == 'Administrador':
            return False
        if not role:
            return None
        new_estado = 0 if int(role.get('estado') or 0) == 1 else 1
        self.update("mantenimiento", "UPDATE roles SET estado = %s WHERE id = %s", (new_estado, role_id))
        return new_estado

    def update_status(self, role_id, estado):
        return self.update("mantenimiento",
            "UPDATE roles SET estado = %s WHERE id = %s", (estado, role_id))

    def get_permissions(self, role_id):
        return self.fetch_all("mantenimiento",
            "SELECT * FROM permisos WHERE rol_id = %s", (role_id,))

    def set_permission(self, role_id, modulo, crear, leer, actualizar, eliminar):
        existing = self.fetch_one("mantenimiento",
            "SELECT id FROM permisos WHERE rol_id = %s AND modulo = %s", (role_id, modulo))
        if existing:
            return self.update("mantenimiento",
                "UPDATE permisos SET crear = %s, leer = %s, actualizar = %s, eliminar = %s WHERE id = %s",
                (crear, leer, actualizar, eliminar, existing['id']))
        return self.insert("mantenimiento",
            "INSERT INTO permisos (rol_id, modulo, crear, leer, actualizar, eliminar) VALUES (%s, %s, %s, %s, %s, %s)",
            (role_id, modulo, crear, leer, actualizar, eliminar))

    def save_all_permissions(self, role_id, permissions):
        self.delete("mantenimiento", "DELETE FROM permisos WHERE rol_id = %s", (role_id,))
        for perm in permissions:
            self.insert("mantenimiento",
                "INSERT INTO permisos (rol_id, modulo, crear, leer, actualizar, eliminar) VALUES (%s, %s, %s, %s, %s, %s)",
                (role_id, perm['modulo'], perm.get('crear', 0), perm.get('leer', 0),
                 perm.get('actualizar', 0), perm.get('eliminar', 0)))

    def get_modules(self):
        return [
            'usuarios', 'roles', 'productos', 'categorias', 'marcas',
            'proveedores', 'mecanicos', 'inventario', 'servicios',
            'promociones', 'ordenes', 'pagos', 'bitacora', 'reportes',
            'respaldos', 'qr', 'sucursales',
            'vehiculos', 'comisiones', 'tickets', 'notificaciones',
            'mantenimiento', 'tasas_avanzadas', 'cotizaciones', 'filtros',
            'combustible'
        ]
