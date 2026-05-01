from model.connection import Connection


class VehicleLogModel(Connection):
    """Bitácora del vehículo — historial completo de servicios y mantenimiento."""
    def __init__(self):
        super().__init__()

    def get_by_vehicle(self, vid, limit=50):
        return self.fetch_all("transalca",
            "SELECT bv.*, m.nombre as mecanico_nombre, m.apellido as mecanico_apellido, "
            "s.nombre as servicio_nombre "
            "FROM bitacora_vehiculo bv "
            "LEFT JOIN mecanicos m ON bv.mecanico_cedula = m.cedula "
            "LEFT JOIN servicios s ON bv.servicio_id = s.id "
            "WHERE bv.vehiculo_id=%s ORDER BY bv.fecha DESC LIMIT %s", (vid, limit))

    def get_by_cliente(self, cliente_cedula, limit=100):
        return self.fetch_all("transalca",
            "SELECT bv.*, v.placa, v.marca, v.modelo, "
            "m.nombre as mecanico_nombre, m.apellido as mecanico_apellido "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_id = v.id "
            "LEFT JOIN mecanicos m ON bv.mecanico_cedula = m.cedula "
            "WHERE bv.cliente_cedula=%s ORDER BY bv.fecha DESC LIMIT %s",
            (cliente_cedula, limit))

    def get_by_id(self, lid):
        return self.fetch_one("transalca",
            "SELECT bv.*, v.placa, v.marca, v.modelo, "
            "m.nombre as mecanico_nombre, m.apellido as mecanico_apellido, "
            "s.nombre as servicio_nombre, c.nombre as cliente_nombre, c.apellido as cliente_apellido "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_id = v.id "
            "INNER JOIN clientes c ON bv.cliente_cedula = c.cedula "
            "LEFT JOIN mecanicos m ON bv.mecanico_cedula = m.cedula "
            "LEFT JOIN servicios s ON bv.servicio_id = s.id "
            "WHERE bv.id=%s", (lid,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO bitacora_vehiculo (vehiculo_id, cliente_cedula, orden_venta_id, "
            "servicio_id, mecanico_cedula, tipo_registro, descripcion, kilometraje, "
            "aceite_usado, filtros_usados, refrigerante_usado, cauchos_info, "
            "precio_servicio, precio_productos, proximo_mantenimiento, modo_registro, observaciones) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (data['vehiculo_id'], data['cliente_cedula'],
             data.get('orden_venta_id'), data.get('servicio_id'),
             data.get('mecanico_cedula'),
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
            "WHERE vehiculo_id=%s AND aceite_usado IS NOT NULL AND aceite_usado != ''", (vid,))
        return result['total'] if result else 0

    def get_service_count(self, vid, tipo_servicio=None):
        sql = "SELECT COUNT(*) as total FROM bitacora_vehiculo WHERE vehiculo_id=%s"
        params = [vid]
        if tipo_servicio:
            sql += " AND descripcion LIKE %s"
            params.append(f"%{tipo_servicio}%")
        result = self.fetch_one("transalca", sql, tuple(params))
        return result['total'] if result else 0
