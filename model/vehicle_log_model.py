from model.connection import Connection


class VehicleLogModel(Connection):
    def __init__(self):
        super().__init__()

    def _vehicle_plate(self, vid):
        placa = (str(vid or '').strip().upper())
        if not placa:
            return None
        vehicle = self.fetch_one("transalca", "SELECT placa FROM vehiculos WHERE placa=%s", (placa,))
        return vehicle['placa'] if vehicle else None

    def _service_mechanic_id(self, data):
        smid = data.get('servicio_mecanico_id')
        if smid:
            return smid
        orden_venta_id = data.get('orden_venta_id') or None
        servicio_id = data.get('servicio_id') or None
        mecanico_cedula = data.get('mecanico_cedula') or None
        if not any((orden_venta_id, servicio_id, mecanico_cedula)):
            return None
        row = self.fetch_one(
            "transalca",
            "SELECT id FROM servicio_mecanico WHERE "
            "(%s IS NULL OR orden_venta_id=%s) AND "
            "(%s IS NULL OR servicio_id=%s) AND "
            "(%s IS NULL OR mecanico_cedula=%s) "
            "ORDER BY fecha DESC LIMIT 1",
            (orden_venta_id, orden_venta_id, servicio_id, servicio_id, mecanico_cedula, mecanico_cedula)
        )
        return row['id'] if row else None

    def get_by_vehicle(self, vid, limit=50):
        return self.fetch_all("transalca",
            "SELECT bv.*, m.nombre as mecanico_nombre, m.apellido as mecanico_apellido, "
            "s.nombre as servicio_nombre "
            "FROM bitacora_vehiculo bv "
            "LEFT JOIN servicio_mecanico sm ON bv.servicio_mecanico_id = sm.id "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula "
            "LEFT JOIN servicios s ON sm.servicio_id = s.id "
            "WHERE bv.vehiculo_placa=%s "
            "ORDER BY bv.fecha DESC LIMIT %s", (self._vehicle_plate(vid), limit))

    def get_by_cliente(self, cliente_cedula, limit=100):
        return self.fetch_all("transalca",
            "SELECT bv.*, v.placa, v.marca, v.modelo, "
            "m.nombre as mecanico_nombre, m.apellido as mecanico_apellido "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa "
            "LEFT JOIN servicio_mecanico sm ON bv.servicio_mecanico_id = sm.id "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula "
            "WHERE v.cliente_cedula=%s ORDER BY bv.fecha DESC LIMIT %s",
            (cliente_cedula, limit))

    def get_by_id(self, lid):
        return self.fetch_one("transalca",
            "SELECT bv.*, v.placa, v.marca, v.modelo, "
            "m.nombre as mecanico_nombre, m.apellido as mecanico_apellido, "
            "s.nombre as servicio_nombre, c.cedula as cliente_cedula, c.nombre as cliente_nombre, c.apellido as cliente_apellido "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa "
            "INNER JOIN clientes c ON v.cliente_cedula = c.cedula "
            "LEFT JOIN servicio_mecanico sm ON bv.servicio_mecanico_id = sm.id "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula "
            "LEFT JOIN servicios s ON sm.servicio_id = s.id "
            "WHERE bv.id=%s", (lid,))

    def create(self, data):
        placa = self._vehicle_plate(data['vehiculo_id'])
        if not placa:
            return None
        servicio_mecanico_id = self._service_mechanic_id(data)
        return self.insert("transalca",
            "INSERT INTO bitacora_vehiculo (vehiculo_placa, servicio_mecanico_id, tipo_registro, descripcion, kilometraje, "
            "aceite_usado, filtros_usados, refrigerante_usado, cauchos_info, "
            "precio_servicio, precio_productos, proximo_mantenimiento, modo_registro, observaciones) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (placa, servicio_mecanico_id,
             data.get('tipo_registro', 'servicio'),
             (data.get('descripcion') or '').strip(),
             data.get('kilometraje') or None,
             (data.get('aceite_usado') or '').strip(),
             (data.get('filtros_usados') or '').strip(),
             (data.get('refrigerante_usado') or '').strip(),
             (data.get('cauchos_info') or '').strip(),
             float(data.get('precio_servicio', 0)),
             float(data.get('precio_productos', 0)),
             (data.get('proximo_mantenimiento') or '').strip(),
             data.get('modo_registro', 'manual'),
             (data.get('observaciones') or '').strip()))

    def count_oil_changes(self, vid):
        result = self.fetch_one("transalca",
            "SELECT COUNT(*) as total FROM bitacora_vehiculo "
            "WHERE vehiculo_placa=%s "
            "AND aceite_usado IS NOT NULL AND aceite_usado != ''", (self._vehicle_plate(vid),))
        return result['total'] if result else 0

    def get_service_count(self, vid, tipo_servicio=None):
        sql = "SELECT COUNT(*) as total FROM bitacora_vehiculo WHERE vehiculo_placa=%s"
        params = [self._vehicle_plate(vid)]
        if tipo_servicio:
            sql += " AND descripcion LIKE %s"
            params.append(f"%{tipo_servicio}%")
        result = self.fetch_one("transalca", sql, tuple(params))
        return result['total'] if result else 0
