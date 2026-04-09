from model.connection import Connection


class CategoryModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT c.*, (SELECT COUNT(*) FROM productos WHERE categoria_id = c.id) as total_productos FROM categorias c ORDER BY c.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM categorias WHERE estado = 1 ORDER BY nombre")

    def get_by_id(self, cid):
        return self.fetch_one("transalca", "SELECT * FROM categorias WHERE id = %s", (cid,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)",
            (data['nombre'].strip(), data.get('descripcion', '').strip()))

    def update_category(self, cid, data):
        return self.update("transalca",
            "UPDATE categorias SET nombre = %s, descripcion = %s WHERE id = %s",
            (data['nombre'].strip(), data.get('descripcion', '').strip(), cid))

    def soft_delete(self, cid):
        return self.update("transalca", "UPDATE categorias SET estado = 0 WHERE id = %s", (cid,))

    def toggle_estado(self, cid):
        return self.update("transalca", "UPDATE categorias SET estado = IF(estado=1,0,1) WHERE id = %s", (cid,))

    def nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            return self.fetch_one("transalca", "SELECT id FROM categorias WHERE nombre = %s AND id != %s", (nombre, exclude_id)) is not None
        return self.fetch_one("transalca", "SELECT id FROM categorias WHERE nombre = %s", (nombre,)) is not None
