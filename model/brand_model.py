from model.connection import Connection


class BrandModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT m.*, (SELECT COUNT(*) FROM productos WHERE marca = m.nombre) as total_productos FROM marcas m ORDER BY m.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM marcas WHERE estado = 1 ORDER BY nombre")

    def get_by_nombre(self, nombre):
        return self.fetch_one("transalca", "SELECT * FROM marcas WHERE nombre = %s", (nombre,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO marcas (nombre, descripcion) VALUES (%s, %s)",
            (data['nombre'].strip(), data.get('descripcion', '').strip()))

    def update_brand(self, old_nombre, data):
        return self.update("transalca",
            "UPDATE marcas SET nombre = %s, descripcion = %s WHERE nombre = %s",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), old_nombre))

    def soft_delete(self, nombre):
        return self.update("transalca", "UPDATE marcas SET estado = 0 WHERE nombre = %s", (nombre,))

    def toggle_estado(self, nombre):
        return self.update("transalca", "UPDATE marcas SET estado = IF(estado=1,0,1) WHERE nombre = %s", (nombre,))

    def nombre_exists(self, nombre, exclude_nombre=None):
        if exclude_nombre:
            return self.fetch_one("transalca", "SELECT nombre FROM marcas WHERE nombre = %s AND nombre != %s", (nombre, exclude_nombre)) is not None
        return self.fetch_one("transalca", "SELECT nombre FROM marcas WHERE nombre = %s", (nombre,)) is not None
