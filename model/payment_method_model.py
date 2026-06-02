from model.connection import Connection


class PaymentMethodModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT mp.* "
            "FROM metodos_pago mp "
            "WHERE mp.estado = 1 ORDER BY mp.created_at DESC")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT id, nombre, datos, permite_credito FROM metodos_pago WHERE estado = 1 ORDER BY nombre")

    def get_by_id(self, method_id):
        return self.fetch_one("transalca",
            "SELECT * FROM metodos_pago WHERE id = %s", (method_id,))

    def name_exists(self, nombre, exclude_id=None):
        value = (nombre or '').strip()
        if not value:
            return False
        if exclude_id:
            return self.fetch_one("transalca",
                "SELECT id FROM metodos_pago WHERE LOWER(nombre) = LOWER(%s) AND id != %s AND estado = 1",
                (value, exclude_id)) is not None
        return self.fetch_one("transalca",
            "SELECT id FROM metodos_pago WHERE LOWER(nombre) = LOWER(%s) AND estado = 1",
            (value,)) is not None

    def get_by_name(self, name):
        value = (name or '').strip()
        if not value:
            return None
        return self.fetch_one("transalca", "SELECT * FROM metodos_pago WHERE LOWER(nombre) = LOWER(%s)", (value,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO metodos_pago (nombre, datos, permite_credito) VALUES (%s,%s,%s)",
            (data['nombre'].strip(), data['datos'].strip(), int(data.get('permite_credito') or 0)))

    def update_method(self, method_id, data):
        return self.update("transalca",
            "UPDATE metodos_pago SET nombre=%s, datos=%s, permite_credito=%s WHERE id=%s",
            (data['nombre'].strip(), data['datos'].strip(), int(data.get('permite_credito') or 0), method_id))

    def soft_delete(self, method_id):
        return self.update("transalca",
            "UPDATE metodos_pago SET estado=0 WHERE id=%s", (method_id,))
