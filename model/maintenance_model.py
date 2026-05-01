from model.connection import Connection
from datetime import datetime, timedelta


class MaintenanceModel(Connection):
    def __init__(self):
        super().__init__()

    def get_rules(self, active_only=True):
        if active_only:
            return self.fetch_all("transalca",
                "SELECT * FROM reglas_mantenimiento WHERE activo=1 ORDER BY nombre")
        return self.fetch_all("transalca",
            "SELECT * FROM reglas_mantenimiento ORDER BY nombre")

    def get_rule_by_id(self, rid):
        return self.fetch_one("transalca",
            "SELECT * FROM reglas_mantenimiento WHERE id=%s", (rid,))

    def create_rule(self, data):
        return self.insert("transalca",
            "INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, "
            "intervalo_dias, intervalo_servicios, tipo_combustible, tipo_vehiculo, descripcion) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (data['nombre'].strip(), data['tipo_servicio'].strip(),
             data.get('intervalo_km') or None, data.get('intervalo_dias') or None,
             data.get('intervalo_servicios') or None,
             data.get('tipo_combustible', 'todos'),
             (data.get('tipo_vehiculo') or '').strip(),
             (data.get('descripcion') or '').strip()))

    def update_rule(self, rid, data):
        return self.update("transalca",
            "UPDATE reglas_mantenimiento SET nombre=%s, tipo_servicio=%s, intervalo_km=%s, "
            "intervalo_dias=%s, intervalo_servicios=%s, tipo_combustible=%s, "
            "tipo_vehiculo=%s, descripcion=%s WHERE id=%s",
            (data['nombre'].strip(), data['tipo_servicio'].strip(),
             data.get('intervalo_km') or None, data.get('intervalo_dias') or None,
             data.get('intervalo_servicios') or None,
             data.get('tipo_combustible', 'todos'),
             (data.get('tipo_vehiculo') or '').strip(),
             (data.get('descripcion') or '').strip(), rid))

    def toggle_rule(self, rid):
        return self.update("transalca",
            "UPDATE reglas_mantenimiento SET activo = NOT activo WHERE id=%s", (rid,))

    def get_by_vehicle(self, vid):
        return self.fetch_all("transalca",
            "SELECT mp.*, r.nombre as regla_nombre FROM mantenimientos_programados mp "
            "LEFT JOIN reglas_mantenimiento r ON mp.regla_id = r.id "
            "WHERE mp.vehiculo_id=%s ORDER BY mp.estado ASC, mp.fecha_proxima ASC", (vid,))

    def get_scheduled_by_id(self, mid):
        return self.fetch_one("transalca",
            "SELECT mp.*, v.cliente_cedula FROM mantenimientos_programados mp "
            "INNER JOIN vehiculos v ON mp.vehiculo_id = v.id WHERE mp.id=%s", (mid,))

    def get_pending(self, vid=None):
        sql = ("SELECT mp.*, r.nombre as regla_nombre, v.placa, v.marca, v.modelo, "
               "c.nombre as cliente_nombre, c.apellido as cliente_apellido "
               "FROM mantenimientos_programados mp "
               "LEFT JOIN reglas_mantenimiento r ON mp.regla_id = r.id "
               "INNER JOIN vehiculos v ON mp.vehiculo_id = v.id "
               "INNER JOIN clientes c ON v.cliente_cedula = c.cedula "
               "WHERE mp.estado IN ('pendiente','proximo','vencido')")
        params = []
        if vid:
            sql += " AND mp.vehiculo_id = %s"
            params.append(vid)
        sql += " ORDER BY mp.estado DESC, mp.fecha_proxima ASC"
        return self.fetch_all("transalca", sql, tuple(params) if params else None)

    def create_scheduled(self, data):
        return self.insert("transalca",
            "INSERT INTO mantenimientos_programados (vehiculo_id, regla_id, "
            "tipo_mantenimiento, modo, km_proximo, fecha_proxima, registrado_por, observaciones) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (data['vehiculo_id'], data.get('regla_id'),
             data['tipo_mantenimiento'].strip(), data.get('modo', 'manual'),
             data.get('km_proximo') or None, data.get('fecha_proxima') or None,
             data.get('registrado_por'), (data.get('observaciones') or '').strip()))

    def complete_maintenance(self, mid, km_realizado=None):
        return self.update("transalca",
            "UPDATE mantenimientos_programados SET estado='completado', "
            "km_realizado=%s, fecha_realizado=CURDATE() WHERE id=%s",
            (km_realizado, mid))

    def calculate_for_vehicle(self, vid):
        vehicle = self.fetch_one("transalca",
            "SELECT * FROM vehiculos WHERE id=%s", (vid,))
        if not vehicle:
            return []

        rules = self.get_rules(active_only=True)
        created = []

        for rule in rules:
            if rule['tipo_combustible'] != 'todos':
                if rule['tipo_combustible'] != vehicle.get('tipo_combustible'):
                    continue

            existing = self.fetch_one("transalca",
                "SELECT id FROM mantenimientos_programados "
                "WHERE vehiculo_id=%s AND regla_id=%s AND estado IN ('pendiente','proximo')",
                (vid, rule['id']))
            if existing:
                continue

            km_proximo = None
            fecha_proxima = None

            if rule.get('intervalo_km') and vehicle.get('kilometraje_actual'):
                km_proximo = vehicle['kilometraje_actual'] + rule['intervalo_km']

            if rule.get('intervalo_dias'):
                base_date = vehicle.get('fecha_ultimo_servicio') or datetime.now().date()
                if hasattr(base_date, 'date'):
                    base_date = base_date
                fecha_proxima = (datetime.combine(base_date, datetime.min.time())
                                + timedelta(days=rule['intervalo_dias'])).date()

            mid = self.create_scheduled({
                'vehiculo_id': vid,
                'regla_id': rule['id'],
                'tipo_mantenimiento': rule['nombre'],
                'modo': 'automatico',
                'km_proximo': km_proximo,
                'fecha_proxima': fecha_proxima.isoformat() if fecha_proxima else None,
                'registrado_por': 'sistema'
            })
            created.append(mid)

        return created

    def check_overdue(self):
        today = datetime.now().date().isoformat()
        self.update("transalca",
            "UPDATE mantenimientos_programados SET estado='vencido' "
            "WHERE estado IN ('pendiente','proximo') "
            "AND fecha_proxima IS NOT NULL AND fecha_proxima < %s", (today,))

        vehicles = self.fetch_all("transalca",
            "SELECT mp.id, mp.km_proximo, v.kilometraje_actual "
            "FROM mantenimientos_programados mp "
            "INNER JOIN vehiculos v ON mp.vehiculo_id = v.id "
            "WHERE mp.estado IN ('pendiente','proximo') AND mp.km_proximo IS NOT NULL")
        for v in vehicles:
            if v['kilometraje_actual'] and v['km_proximo']:
                if v['kilometraje_actual'] >= v['km_proximo']:
                    self.update("transalca",
                        "UPDATE mantenimientos_programados SET estado='vencido' WHERE id=%s",
                        (v['id'],))
