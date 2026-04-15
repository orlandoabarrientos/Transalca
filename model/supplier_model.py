from model.connection import Connection


class SupplierModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT p.*, (SELECT COUNT(*) FROM ordenes_compra WHERE proveedor_rif = p.rif) as total_ordenes FROM proveedores p ORDER BY p.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM proveedores WHERE estado = 1 ORDER BY nombre")

    def get_by_rif(self, rif):
        return self.fetch_one("transalca", "SELECT * FROM proveedores WHERE rif = %s", (rif,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO proveedores (rif, nombre, telefono, email, direccion) VALUES (%s, %s, %s, %s, %s)",
            (data['rif'].strip(), data['nombre'].strip(), data.get('telefono', '').strip(),
             data.get('email', '').strip(), data.get('direccion', '').strip()))

    def update_supplier(self, old_rif, data):
        return self.update("transalca",
            "UPDATE proveedores SET rif = %s, nombre = %s, telefono = %s, email = %s, direccion = %s WHERE rif = %s",
            (data['rif'].strip(), data['nombre'].strip(), data.get('telefono', '').strip(),
             data.get('email', '').strip(), data.get('direccion', '').strip(), old_rif))

    def soft_delete(self, rif):
        return self.update("transalca",
            "UPDATE proveedores SET estado = 0 WHERE rif = %s", (rif,))

    def toggle_estado(self, rif):
        return self.update("transalca",
            "UPDATE proveedores SET estado = IF(estado=1,0,1) WHERE rif = %s", (rif,))

    def rif_exists(self, rif, exclude_rif=None):
        if exclude_rif:
            result = self.fetch_one("transalca",
                "SELECT rif FROM proveedores WHERE rif = %s AND rif != %s", (rif, exclude_rif))
        else:
            result = self.fetch_one("transalca",
                "SELECT rif FROM proveedores WHERE rif = %s", (rif,))
        return result is not None
