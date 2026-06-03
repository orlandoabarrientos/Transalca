from model.connection import Connection


class CategoryModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT c.*, (SELECT COUNT(*) FROM productos WHERE categoria = c.nombre AND estado = 1) as total_productos FROM categorias c WHERE c.estado = 1 ORDER BY c.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM categorias WHERE estado = 1 ORDER BY nombre")

    def get_by_nombre(self, nombre):
        return self.fetch_one("transalca", "SELECT * FROM categorias WHERE nombre = %s", (nombre,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)",
            (data['nombre'].strip(), data.get('descripcion', '').strip()))

    def update_category(self, old_nombre, data):
        return self.update("transalca",
            "UPDATE categorias SET nombre = %s, descripcion = %s WHERE nombre = %s",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), old_nombre))

    def soft_delete(self, nombre):
        return self.update("transalca", "UPDATE categorias SET estado = 0 WHERE nombre = %s", (nombre,))

    def toggle_estado(self, nombre):
        return self.soft_delete(nombre)

    def nombre_exists(self, nombre, exclude_nombre=None):
        if exclude_nombre:
            return self.fetch_one("transalca", "SELECT nombre FROM categorias WHERE nombre = %s AND nombre != %s AND estado = 1", (nombre, exclude_nombre)) is not None
        return self.fetch_one("transalca", "SELECT nombre FROM categorias WHERE nombre = %s AND estado = 1", (nombre,)) is not None
