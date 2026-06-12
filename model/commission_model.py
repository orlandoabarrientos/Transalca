from config.constants import PORCENTAJE_COMISION_DEFAULT
from model.connection import Connection

MONTO_SQL = "ROUND(cm.precio_servicio_comision * (cm.porcentaje_comision / 100), 2) AS monto_comision"


class CommissionModel(Connection):
    def __init__(self):
        super().__init__()

    def _get_all(self):
        sql = ("SELECT cm.*, " + MONTO_SQL + ", sm.mecanico_cedula, sm.orden_venta_id, "
               "sm.fecha_servicio AS fecha, sm.estado_servicio, "
               "m.nombre_mecanico as mecanico_nombre, m.apellido_mecanico as mecanico_apellido, "
               "s.nombre_servicio as servicio_nombre "
               "FROM comisiones_mecanico cm "
               "INNER JOIN servicio_mecanico sm ON cm.servicio_mecanico_id = sm.id_servicio_mecanico "
               "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
               "INNER JOIN servicios s ON sm.servicio_id = s.id_servicio "
               "ORDER BY sm.fecha_servicio DESC")
        return self.fetch_all("transalca", sql)

    def _get_by_mecanico(self, mecanico_cedula):
        sql = ("SELECT cm.*, " + MONTO_SQL + ", sm.mecanico_cedula, sm.orden_venta_id, "
               "sm.fecha_servicio AS fecha, s.nombre_servicio as servicio_nombre "
               "FROM comisiones_mecanico cm "
               "INNER JOIN servicio_mecanico sm ON cm.servicio_mecanico_id = sm.id_servicio_mecanico "
               "INNER JOIN servicios s ON sm.servicio_id = s.id_servicio "
               "WHERE sm.mecanico_cedula = %s ORDER BY sm.fecha_servicio DESC")
        return self.fetch_all("transalca", sql, (mecanico_cedula,))

    def _get_by_id(self, cid):
        return self.fetch_one("transalca",
            "SELECT cm.*, " + MONTO_SQL + ", sm.mecanico_cedula, sm.orden_venta_id, "
            "sm.fecha_servicio AS fecha, "
            "m.nombre_mecanico as mecanico_nombre, m.apellido_mecanico as mecanico_apellido, "
            "s.nombre_servicio as servicio_nombre FROM comisiones_mecanico cm "
            "INNER JOIN servicio_mecanico sm ON cm.servicio_mecanico_id = sm.id_servicio_mecanico "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
            "INNER JOIN servicios s ON sm.servicio_id = s.id_servicio WHERE cm.servicio_mecanico_id = %s", (cid,))

    def _create(self, data):
        precio = float(data.get('precio_servicio_comision', data.get('precio_servicio')))
        porcentaje = float(data.get('porcentaje_comision') or PORCENTAJE_COMISION_DEFAULT)
        self.insert("transalca",
            "INSERT INTO comisiones_mecanico (servicio_mecanico_id, precio_servicio_comision, porcentaje_comision) "
            "VALUES (%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE precio_servicio_comision = VALUES(precio_servicio_comision), porcentaje_comision = VALUES(porcentaje_comision)",
            (data['servicio_mecanico_id'], precio, porcentaje))
        return data['servicio_mecanico_id']

    def _create_from_service(self, servicio_mecanico_id, porcentaje_comision=None):
        sm = self.fetch_one("transalca",
            "SELECT sm.*, sm.id_servicio_mecanico AS id, s.precio_servicio AS precio FROM servicio_mecanico sm "
            "INNER JOIN servicios s ON sm.servicio_id = s.id_servicio WHERE sm.id_servicio_mecanico = %s",
            (servicio_mecanico_id,))
        if not sm or not sm.get('mecanico_cedula'):
            return None
        existing = self.fetch_one("transalca",
            "SELECT servicio_mecanico_id, porcentaje_comision FROM comisiones_mecanico WHERE servicio_mecanico_id = %s",
            (servicio_mecanico_id,))
        if existing and porcentaje_comision is None:
            return existing['servicio_mecanico_id']
        return self._create({
            'servicio_mecanico_id': servicio_mecanico_id,
            'precio_servicio_comision': float(sm['precio']),
            'porcentaje_comision': porcentaje_comision
        })

    def _set_percentage(self, servicio_mecanico_id, porcentaje_comision):
        return self._create_from_service(servicio_mecanico_id, porcentaje_comision)

    def _get_summary(self, mecanico_cedula):
        return self.fetch_one("transalca",
            "SELECT COUNT(*) as total_servicios, "
            "COALESCE(SUM(ROUND(cm.precio_servicio_comision * (cm.porcentaje_comision / 100), 2)),0) as total "
            "FROM comisiones_mecanico cm INNER JOIN servicio_mecanico sm ON cm.servicio_mecanico_id = sm.id_servicio_mecanico "
            "WHERE sm.mecanico_cedula=%s", (mecanico_cedula,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_mecanico": self._get_by_mecanico,
            "get_by_id": self._get_by_id,
            "create": self._create,
            "create_from_service": self._create_from_service,
            "set_percentage": self._set_percentage,
            "get_summary": self._get_summary,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
