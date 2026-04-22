from model.connection import Connection


class ServiceModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT s.*, su.nombre as sucursal_nombre FROM servicios s LEFT JOIN sucursales su ON s.sucursal_id = su.id ORDER BY s.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT s.*, su.nombre as sucursal_nombre FROM servicios s LEFT JOIN sucursales su ON s.sucursal_id = su.id WHERE s.estado = 1 ORDER BY s.nombre")

    def get_by_id(self, sid):
        return self.fetch_one("transalca",
            "SELECT s.*, su.nombre as sucursal_nombre FROM servicios s LEFT JOIN sucursales su ON s.sucursal_id = su.id WHERE s.id = %s", (sid,))

    def get_by_sucursal(self, suc_id):
        return self.fetch_all("transalca",
            "SELECT s.*, su.nombre as sucursal_nombre FROM servicios s LEFT JOIN sucursales su ON s.sucursal_id = su.id WHERE s.sucursal_id = %s AND s.estado = 1 ORDER BY s.nombre", (suc_id,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, sucursal_id) VALUES (%s, %s, %s, %s, %s)",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), float(data['precio']),
             data.get('duracion_estimada', '').strip(), data.get('sucursal_id') or None))

    def update_service(self, sid, data):
        return self.update("transalca",
            "UPDATE servicios SET nombre = %s, descripcion = %s, precio = %s, duracion_estimada = %s, sucursal_id = %s WHERE id = %s",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), float(data['precio']),
             data.get('duracion_estimada', '').strip(), data.get('sucursal_id') or None, sid))

    def soft_delete(self, sid):
        return self.update("transalca", "UPDATE servicios SET estado = 0 WHERE id = %s", (sid,))

    def toggle_estado(self, sid):
        return self.update("transalca", "UPDATE servicios SET estado = NOT estado WHERE id = %s", (sid,))
