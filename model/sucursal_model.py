from model.connection import Connection


class SucursalModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT * FROM sucursales ORDER BY nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM sucursales WHERE estado = 1 ORDER BY nombre")

    def get_by_id(self, sucursal_id):
        return self.fetch_one("transalca",
            "SELECT * FROM sucursales WHERE id = %s", (sucursal_id,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO sucursales (nombre, direccion, telefono, email) VALUES (%s, %s, %s, %s)",
            (data['nombre'], data.get('direccion', ''), data.get('telefono', ''), data.get('email', '')))

    def update_sucursal(self, sucursal_id, data):
        return self.update("transalca",
            "UPDATE sucursales SET nombre = %s, direccion = %s, telefono = %s, email = %s WHERE id = %s",
            (data['nombre'], data.get('direccion', ''), data.get('telefono', ''), data.get('email', ''), sucursal_id))

    def toggle_estado(self, sucursal_id):
        return self.update("transalca",
            "UPDATE sucursales SET estado = IF(estado=1,0,1) WHERE id = %s", (sucursal_id,))

    def soft_delete(self, sucursal_id):
        return self.update("transalca",
            "UPDATE sucursales SET estado = 0 WHERE id = %s", (sucursal_id,))

    def nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            result = self.fetch_one("transalca",
                "SELECT id FROM sucursales WHERE nombre = %s AND id != %s", (nombre, exclude_id))
        else:
            result = self.fetch_one("transalca",
                "SELECT id FROM sucursales WHERE nombre = %s", (nombre,))
        return result is not None
