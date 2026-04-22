from model.connection import Connection


class ServiceMechanicModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        assignments = self.fetch_all("transalca",
            "SELECT sm.*, s.nombre as servicio_nombre, s.precio, m.nombre as mecanico_nombre_base, m.apellido as mecanico_apellido_base FROM servicio_mecanico sm INNER JOIN servicios s ON sm.servicio_id = s.id LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula ORDER BY sm.fecha DESC")
        for a in assignments:
            nombre = (a.get('mecanico_nombre_base') or '').strip()
            apellido = (a.get('mecanico_apellido_base') or '').strip()
            full_name = f"{nombre} {apellido}".strip()
            a['mecanico_nombre'] = full_name if full_name else 'Sin asignar'
            a.pop('mecanico_nombre_base', None)
            a.pop('mecanico_apellido_base', None)
        return assignments

    def get_by_id(self, aid):
        return self.fetch_one("transalca",
            "SELECT sm.*, s.nombre as servicio_nombre FROM servicio_mecanico sm INNER JOIN servicios s ON sm.servicio_id = s.id WHERE sm.id = %s", (aid,))

    def _is_mechanic_nullable(self):
        column = self.fetch_one("transalca", "SHOW COLUMNS FROM servicio_mecanico LIKE 'mecanico_cedula'")
        if not column:
            return False
        return column.get('Null') == 'YES'

    def ensure_optional_mechanic_support(self):
        if self._is_mechanic_nullable():
            return True
        try:
            self.update("transalca", "ALTER TABLE servicio_mecanico MODIFY mecanico_cedula VARCHAR(20) NULL")
        except Exception:
            return self._is_mechanic_nullable()
        return self._is_mechanic_nullable()

    def assign(self, data):
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip() or None
        if mecanico_cedula is None:
            self.ensure_optional_mechanic_support()
            if not self._is_mechanic_nullable():
                raise Exception("La base de datos no permite registrar servicio sin mecanico")
        return self.insert("transalca",
            "INSERT INTO servicio_mecanico (servicio_id, mecanico_cedula, orden_venta_id, observaciones) VALUES (%s, %s, %s, %s)",
            (data['servicio_id'], mecanico_cedula, data.get('orden_venta_id') or None, data.get('observaciones', '').strip()))

    def update_mechanic(self, aid, mecanico_cedula):
        return self.update("transalca",
            "UPDATE servicio_mecanico SET mecanico_cedula = %s WHERE id = %s", (mecanico_cedula.strip(), aid))

    def update_status(self, aid, estado):
        return self.update("transalca",
            "UPDATE servicio_mecanico SET estado = %s WHERE id = %s", (estado, aid))

    def delete_assignment(self, aid):
        return self.delete("transalca", "DELETE FROM servicio_mecanico WHERE id = %s", (aid,))
