from model.connection import Connection


class CommissionModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self, estado_pago=None):
        sql = ("SELECT cm.*, m.nombre as mecanico_nombre, m.apellido as mecanico_apellido, "
               "s.nombre as servicio_nombre "
               "FROM comisiones_mecanico cm "
               "INNER JOIN mecanicos m ON cm.mecanico_cedula = m.cedula "
               "INNER JOIN servicio_mecanico sm ON cm.servicio_mecanico_id = sm.id "
               "INNER JOIN servicios s ON sm.servicio_id = s.id WHERE 1=1")
        params = []
        if estado_pago:
            sql += " AND cm.estado_pago = %s"
            params.append(estado_pago)
        sql += " ORDER BY cm.fecha DESC"
        return self.fetch_all("transalca", sql, tuple(params) if params else None)

    def get_by_mecanico(self, mecanico_cedula, estado_pago=None):
        sql = ("SELECT cm.*, s.nombre as servicio_nombre "
               "FROM comisiones_mecanico cm "
               "INNER JOIN servicio_mecanico sm ON cm.servicio_mecanico_id = sm.id "
               "INNER JOIN servicios s ON sm.servicio_id = s.id "
               "WHERE cm.mecanico_cedula = %s")
        params = [mecanico_cedula]
        if estado_pago:
            sql += " AND cm.estado_pago = %s"
            params.append(estado_pago)
        sql += " ORDER BY cm.fecha DESC"
        return self.fetch_all("transalca", sql, tuple(params))

    def get_by_id(self, cid):
        return self.fetch_one("transalca",
            "SELECT cm.*, m.nombre as mecanico_nombre, m.apellido as mecanico_apellido, "
            "s.nombre as servicio_nombre FROM comisiones_mecanico cm "
            "INNER JOIN mecanicos m ON cm.mecanico_cedula = m.cedula "
            "INNER JOIN servicio_mecanico sm ON cm.servicio_mecanico_id = sm.id "
            "INNER JOIN servicios s ON sm.servicio_id = s.id WHERE cm.id = %s", (cid,))

    def create(self, data):
        precio = float(data['precio_servicio'])
        porcentaje = float(data.get('porcentaje_comision', 30.00))
        monto = round(precio * (porcentaje / 100), 2)
        return self.insert("transalca",
            "INSERT INTO comisiones_mecanico (mecanico_cedula, servicio_mecanico_id, "
            "orden_venta_id, precio_servicio, porcentaje_comision, monto_comision) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (data['mecanico_cedula'], data['servicio_mecanico_id'],
             data['orden_venta_id'], precio, porcentaje, monto))

    def create_from_service(self, servicio_mecanico_id):
        sm = self.fetch_one("transalca",
            "SELECT sm.*, s.precio FROM servicio_mecanico sm "
            "INNER JOIN servicios s ON sm.servicio_id = s.id WHERE sm.id = %s",
            (servicio_mecanico_id,))
        if not sm or not sm.get('mecanico_cedula') or not sm.get('orden_venta_id'):
            return None
        existing = self.fetch_one("transalca",
            "SELECT id FROM comisiones_mecanico WHERE servicio_mecanico_id = %s",
            (servicio_mecanico_id,))
        if existing:
            return existing['id']
        return self.create({
            'mecanico_cedula': sm['mecanico_cedula'],
            'servicio_mecanico_id': servicio_mecanico_id,
            'orden_venta_id': sm.get('orden_venta_id'),
            'precio_servicio': float(sm['precio'])
        })

    def mark_paid(self, cid):
        return self.update("transalca",
            "UPDATE comisiones_mecanico SET estado_pago='pagado', "
            "fecha_pago=CURDATE() WHERE id=%s", (cid,))

    def mark_cancelled(self, cid):
        return self.update("transalca",
            "UPDATE comisiones_mecanico SET estado_pago='anulado' WHERE id=%s", (cid,))

    def get_summary(self, mecanico_cedula):
        return self.fetch_one("transalca",
            "SELECT COUNT(*) as total_servicios, "
            "COALESCE(SUM(CASE WHEN estado_pago='pendiente' THEN monto_comision ELSE 0 END),0) as pendiente, "
            "COALESCE(SUM(CASE WHEN estado_pago='pagado' THEN monto_comision ELSE 0 END),0) as pagado, "
            "COALESCE(SUM(monto_comision),0) as total "
            "FROM comisiones_mecanico WHERE mecanico_cedula=%s", (mecanico_cedula,))
