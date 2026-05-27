from model.connection import Connection


class FuelModel(Connection):
    def __init__(self):
        super().__init__()

    def get_by_vehicle(self, vid):
        return self.fetch_all("transalca",
            "SELECT * FROM consumo_combustible WHERE vehiculo_placa=(SELECT placa FROM vehiculos WHERE id=%s) "
            "ORDER BY fecha DESC, id DESC", (vid,))

    def get_latest(self, vid):
        return self.fetch_one("transalca",
            "SELECT * FROM consumo_combustible WHERE vehiculo_placa=(SELECT placa FROM vehiculos WHERE id=%s) "
            "ORDER BY fecha DESC, id DESC LIMIT 1", (vid,))

    def get_by_id(self, rid):
        return self.fetch_one("transalca",
            "SELECT cc.*, v.id as vehiculo_id FROM consumo_combustible cc "
            "INNER JOIN vehiculos v ON cc.vehiculo_placa = v.placa WHERE cc.id=%s", (rid,))

    def create(self, data):
        vehicle = self.fetch_one("transalca", "SELECT placa FROM vehiculos WHERE id=%s", (data['vehiculo_id'],))
        if not vehicle:
            return None
        return self.insert("transalca",
            "INSERT INTO consumo_combustible (vehiculo_placa, modo, consumo_estimado_lkm, "
            "fuente_dato, km_recorridos, litros_consumidos, precio_litro, fecha, observaciones) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (vehicle['placa'], data.get('modo', 'manual'),
             data.get('consumo_estimado_lkm') or None,
             (data.get('fuente_dato') or '').strip(),
             data.get('km_recorridos') or None,
             data.get('litros_consumidos') or None,
             data.get('precio_litro') or None,
             data.get('fecha') or None,
             (data.get('observaciones') or '').strip()))

    def get_average_consumption(self, vid):
        result = self.fetch_one("transalca",
            "SELECT AVG(consumo_estimado_lkm) as promedio "
            "FROM consumo_combustible WHERE vehiculo_placa=(SELECT placa FROM vehiculos WHERE id=%s) "
            "AND consumo_estimado_lkm IS NOT NULL AND consumo_estimado_lkm > 0", (vid,))
        return float(result['promedio']) if result and result['promedio'] else None

    def delete_record(self, rid):
        return self.delete("transalca",
            "DELETE FROM consumo_combustible WHERE id=%s", (rid,))
