from model.connection import Connection


class SupplierModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self):
        rows = self.fetch_all("transalca", "SHOW COLUMNS FROM proveedores")
        return {r['Field'] for r in rows}

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT p.*, (SELECT COUNT(*) FROM ordenes_compra WHERE proveedor_rif = p.rif) as total_ordenes FROM proveedores p WHERE p.estado = 1 ORDER BY p.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM proveedores WHERE estado = 1 ORDER BY nombre")

    def get_by_rif(self, rif):
        return self.fetch_one("transalca", "SELECT * FROM proveedores WHERE rif = %s", (rif,))

    def create(self, data):
        values = {
            'rif': data['rif'].strip(),
            'rif_prefijo': data.get('rif_prefijo'),
            'rif_numero': data.get('rif_numero'),
            'nombre': data['nombre'].strip(),
            'telefono': data.get('telefono', '').strip(),
            'email': data.get('email', '').strip(),
            'direccion': data.get('direccion', '').strip()
        }
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        return self.insert("transalca",
            f"INSERT INTO proveedores ({', '.join(keys)}) VALUES ({', '.join(['%s'] * len(keys))})",
            tuple(values[k] for k in keys))

    def update_supplier(self, old_rif, data):
        values = {
            'rif': data['rif'].strip(),
            'rif_prefijo': data.get('rif_prefijo'),
            'rif_numero': data.get('rif_numero'),
            'nombre': data['nombre'].strip(),
            'telefono': data.get('telefono', '').strip(),
            'email': data.get('email', '').strip(),
            'direccion': data.get('direccion', '').strip()
        }
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        params = [values[k] for k in keys] + [old_rif]
        return self.update("transalca",
            f"UPDATE proveedores SET {', '.join([f'{k} = %s' for k in keys])} WHERE rif = %s",
            tuple(params))

    def soft_delete(self, rif):
        return self.update("transalca",
            "UPDATE proveedores SET estado = 0 WHERE rif = %s", (rif,))

    def toggle_estado(self, rif):
        return self.soft_delete(rif)

    def rif_exists(self, rif, exclude_rif=None):
        if exclude_rif:
            result = self.fetch_one("transalca",
                "SELECT rif FROM proveedores WHERE rif = %s AND rif != %s", (rif, exclude_rif))
        else:
            result = self.fetch_one("transalca",
                "SELECT rif FROM proveedores WHERE rif = %s", (rif,))
        return result is not None
