from model.connection import Connection


class BitacoraModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self, limit=100, offset=0):
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id ORDER BY b.fecha DESC LIMIT %s OFFSET %s",
            (limit, offset))

    def get_by_user(self, user_id):
        return self.fetch_all("mantenimiento",
            "SELECT * FROM bitacora WHERE usuario_id = %s ORDER BY fecha DESC", (user_id,))

    def get_by_module(self, modulo):
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id WHERE b.modulo = %s ORDER BY b.fecha DESC",
            (modulo,))

    def get_by_date_range(self, start, end):
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id WHERE b.fecha BETWEEN %s AND %s ORDER BY b.fecha DESC",
            (start, end))

    def log_action(self, user_id, accion, modulo, descripcion, ip='127.0.0.1'):
        return self.insert("mantenimiento",
            "INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (%s, %s, %s, %s, %s)",
            (user_id, accion, modulo, descripcion, ip))

    def count_all(self):
        result = self.fetch_one("mantenimiento", "SELECT COUNT(*) as total FROM bitacora")
        return result['total'] if result else 0

    def search(self, query):
        search = f"%{query}%"
        return self.fetch_all("mantenimiento",
            "SELECT b.*, u.nombre, u.apellido FROM bitacora b INNER JOIN usuarios u ON b.usuario_id = u.id WHERE b.accion LIKE %s OR b.modulo LIKE %s OR b.descripcion LIKE %s ORDER BY b.fecha DESC",
            (search, search, search))
