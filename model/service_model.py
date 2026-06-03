from model.connection import Connection


class ServiceModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT s.*, GROUP_CONCAT(ss.sucursal_id ORDER BY ss.sucursal_id) as sucursal_ids, "
            "GROUP_CONCAT(su.nombre ORDER BY su.nombre SEPARATOR ', ') as sucursal_nombre "
            "FROM servicios s "
            "LEFT JOIN servicio_sucursal ss ON s.id = ss.servicio_id AND ss.estado = 1 "
            "LEFT JOIN sucursales su ON ss.sucursal_id = su.id "
            "WHERE s.estado = 1 GROUP BY s.id ORDER BY s.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT s.*, GROUP_CONCAT(ss.sucursal_id ORDER BY ss.sucursal_id) as sucursal_ids, "
            "GROUP_CONCAT(su.nombre ORDER BY su.nombre SEPARATOR ', ') as sucursal_nombre "
            "FROM servicios s "
            "LEFT JOIN servicio_sucursal ss ON s.id = ss.servicio_id AND ss.estado = 1 "
            "LEFT JOIN sucursales su ON ss.sucursal_id = su.id "
            "WHERE s.estado = 1 GROUP BY s.id ORDER BY s.nombre")

    def get_by_id(self, sid):
        return self.fetch_one("transalca",
            "SELECT s.*, GROUP_CONCAT(ss.sucursal_id ORDER BY ss.sucursal_id) as sucursal_ids, "
            "GROUP_CONCAT(su.nombre ORDER BY su.nombre SEPARATOR ', ') as sucursal_nombre "
            "FROM servicios s "
            "LEFT JOIN servicio_sucursal ss ON s.id = ss.servicio_id AND ss.estado = 1 "
            "LEFT JOIN sucursales su ON ss.sucursal_id = su.id "
            "WHERE s.id = %s GROUP BY s.id", (sid,))

    def get_by_sucursal(self, suc_id):
        return self.fetch_all("transalca",
            "SELECT s.*, su.nombre as sucursal_nombre FROM servicios s "
            "INNER JOIN servicio_sucursal ss ON s.id = ss.servicio_id "
            "INNER JOIN sucursales su ON ss.sucursal_id = su.id "
            "WHERE ss.sucursal_id = %s AND ss.estado = 1 AND s.estado = 1 ORDER BY s.nombre", (suc_id,))

    def sucursal_exists(self, sucursal_id):
        return self.fetch_one("transalca", "SELECT id FROM sucursales WHERE id = %s AND estado = 1", (sucursal_id,)) is not None

    def _sync_sucursales(self, sid, sucursal_ids):
        ids = []
        for value in sucursal_ids or []:
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                continue
            if parsed not in ids:
                ids.append(parsed)
        self.update("transalca", "DELETE FROM servicio_sucursal WHERE servicio_id = %s", (sid,))
        for sucursal_id in ids:
            self.insert("transalca",
                "INSERT INTO servicio_sucursal (servicio_id, sucursal_id) VALUES (%s, %s)",
                (sid, sucursal_id))

    def create(self, data):
        duration = data.get('duracion_estimada', 60)
        sid = self.insert("transalca",
            "INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada) VALUES (%s, %s, %s, %s)",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), float(data['precio']),
             str(duration).strip()))
        self._sync_sucursales(sid, data.get('sucursal_ids') or [])
        return sid

    def update_service(self, sid, data):
        duration = data.get('duracion_estimada', 60)
        result = self.update("transalca",
            "UPDATE servicios SET nombre = %s, descripcion = %s, precio = %s, duracion_estimada = %s WHERE id = %s",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), float(data['precio']),
             str(duration).strip(), sid))
        self._sync_sucursales(sid, data.get('sucursal_ids') or [])
        return result

    def soft_delete(self, sid):
        return self.update("transalca", "UPDATE servicios SET estado = 0 WHERE id = %s", (sid,))

    def toggle_estado(self, sid):
        return self.soft_delete(sid)

    def nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            result = self.fetch_one("transalca", "SELECT id FROM servicios WHERE nombre = %s AND id != %s AND estado = 1", (nombre, exclude_id))
        else:
            result = self.fetch_one("transalca", "SELECT id FROM servicios WHERE nombre = %s AND estado = 1", (nombre,))
        return result is not None

    def get_by_nombre(self, nombre):
        return self.fetch_one("transalca", "SELECT * FROM servicios WHERE nombre = %s", (nombre,))
