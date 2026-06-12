from model.connection import Connection


class BitacoraModel(Connection):
    def __init__(self):
        super().__init__()

    def _get_all(self, limit=100, offset=0):
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id ORDER BY b.fecha DESC LIMIT %s OFFSET %s",
            (limit, offset))

    def _get_by_user(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT * FROM bitacora WHERE usuario_id = %s ORDER BY fecha DESC", (user_id,))

    def _get_by_module(self, modulo):
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id WHERE b.modulo = %s ORDER BY b.fecha DESC",
            (modulo,))

    def _get_by_date_range(self, start, end):
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id WHERE b.fecha BETWEEN %s AND %s ORDER BY b.fecha DESC",
            (start, end))

    def _log_action(self, user_id, accion, modulo, descripcion, ip='127.0.0.1'):
        return self.insert("mantenimiento",
            "INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (%s, %s, %s, %s, %s)",
            (user_id, accion, modulo, descripcion, ip))

    def _count_all(self):
        result = self.fetch_one("mantenimiento", "SELECT COUNT(*) as total FROM bitacora")
        return result['total'] if result else 0

    def _search(self, query):
        search = f"%{query}%"
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id WHERE b.accion LIKE %s OR b.modulo LIKE %s OR b.descripcion LIKE %s ORDER BY b.fecha DESC",
            (search, search, search))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_user": self._get_by_user,
            "get_by_module": self._get_by_module,
            "get_by_date_range": self._get_by_date_range,
            "log_action": self._log_action,
            "count_all": self._count_all,
            "search": self._search,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
