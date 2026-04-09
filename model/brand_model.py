from model.connection import Connection


class BrandModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT m.*, (SELECT COUNT(*) FROM productos WHERE marca_id = m.id) as total_productos FROM marcas m ORDER BY m.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM marcas WHERE estado = 1 ORDER BY nombre")

    def get_by_id(self, bid):
        return self.fetch_one("transalca", "SELECT * FROM marcas WHERE id = %s", (bid,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO marcas (nombre, descripcion) VALUES (%s, %s)",
            (data['nombre'].strip(), data.get('descripcion', '').strip()))

    def update_brand(self, bid, data):
        return self.update("transalca",
            "UPDATE marcas SET nombre = %s, descripcion = %s WHERE id = %s",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), bid))

    def soft_delete(self, bid):
        return self.update("transalca", "UPDATE marcas SET estado = 0 WHERE id = %s", (bid,))

    def toggle_estado(self, bid):
        return self.update("transalca", "UPDATE marcas SET estado = IF(estado=1,0,1) WHERE id = %s", (bid,))

    def nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            return self.fetch_one("transalca", "SELECT id FROM marcas WHERE nombre = %s AND id != %s", (nombre, exclude_id)) is not None
        return self.fetch_one("transalca", "SELECT id FROM marcas WHERE nombre = %s", (nombre,)) is not None
