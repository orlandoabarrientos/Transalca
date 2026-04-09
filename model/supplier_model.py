from model.connection import Connection


class SupplierModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT p.*, (SELECT COUNT(*) FROM ordenes_compra WHERE proveedor_id = p.id) as total_ordenes FROM proveedores p ORDER BY p.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM proveedores WHERE estado = 1 ORDER BY nombre")

    def get_by_id(self, supplier_id):
        return self.fetch_one("transalca", "SELECT * FROM proveedores WHERE id = %s", (supplier_id,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO proveedores (nombre, rif, telefono, email, direccion) VALUES (%s, %s, %s, %s, %s)",
            (data['nombre'].strip(), data['rif'].strip(), data.get('telefono', '').strip(), data.get('email', '').strip(), data.get('direccion', '').strip()))

    def update_supplier(self, supplier_id, data):
        return self.update("transalca",
            "UPDATE proveedores SET nombre = %s, rif = %s, telefono = %s, email = %s, direccion = %s WHERE id = %s",
            (data['nombre'].strip(), data['rif'].strip(), data.get('telefono', '').strip(), data.get('email', '').strip(), data.get('direccion', '').strip(), supplier_id))

    def soft_delete(self, supplier_id):
        return self.update("transalca",
            "UPDATE proveedores SET estado = 0 WHERE id = %s", (supplier_id,))

    def toggle_estado(self, supplier_id):
        return self.update("transalca",
            "UPDATE proveedores SET estado = IF(estado=1,0,1) WHERE id = %s", (supplier_id,))

    def rif_exists(self, rif, exclude_id=None):
        if exclude_id:
            result = self.fetch_one("transalca",
                "SELECT id FROM proveedores WHERE rif = %s AND id != %s", (rif, exclude_id))
        else:
            result = self.fetch_one("transalca",
                "SELECT id FROM proveedores WHERE rif = %s", (rif,))
        return result is not None
