from model.connection import Connection


class PaymentMethodModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("mantenimiento",
            "SELECT mp.*, u.nombre as usuario_nombre, u.apellido as usuario_apellido "
            "FROM metodos_pago mp "
            "INNER JOIN usuarios u ON mp.usuario_id = u.id "
            "WHERE mp.estado = 1 ORDER BY mp.created_at DESC")

    def get_active(self):
        return self.fetch_all("mantenimiento",
            "SELECT id, nombre, datos FROM metodos_pago WHERE estado = 1 ORDER BY nombre")

    def get_by_id(self, method_id):
        return self.fetch_one("mantenimiento",
            "SELECT * FROM metodos_pago WHERE id = %s", (method_id,))

    def name_exists(self, nombre, exclude_id=None):
        value = (nombre or '').strip()
        if not value:
            return False
        if exclude_id:
            return self.fetch_one("mantenimiento",
                "SELECT id FROM metodos_pago WHERE LOWER(nombre) = LOWER(%s) AND id != %s AND estado = 1",
                (value, exclude_id)) is not None
        return self.fetch_one("mantenimiento",
            "SELECT id FROM metodos_pago WHERE LOWER(nombre) = LOWER(%s) AND estado = 1",
            (value,)) is not None

    def create(self, data):
        return self.insert("mantenimiento",
            "INSERT INTO metodos_pago (usuario_id, nombre, datos) VALUES (%s,%s,%s)",
            (data['usuario_id'], data['nombre'].strip(), data['datos'].strip()))

    def update_method(self, method_id, data):
        return self.update("mantenimiento",
            "UPDATE metodos_pago SET nombre=%s, datos=%s WHERE id=%s",
            (data['nombre'].strip(), data['datos'].strip(), method_id))

    def soft_delete(self, method_id):
        return self.update("mantenimiento",
            "UPDATE metodos_pago SET estado=0 WHERE id=%s", (method_id,))
