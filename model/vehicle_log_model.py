import json
import logging
import threading
from datetime import date, datetime, timedelta

from model.connection import Connection
from model.notification_model import NotificationModel

logger = logging.getLogger(__name__)

BITACORA_SELECT = (
    "bv.*, bv.id_bitacora_vehiculo AS id, bv.fecha_bitacora AS fecha, bv.descripcion_bitacora AS descripcion, "
    "bv.observaciones_bitacora AS observaciones, bv.cauchos_usados AS cauchos_info"
)

# Mapa categoria de producto -> tipo de prediccion y clave de vida util en configuracion.
CATEGORIA_PREDICCION = {
    'cauchos': ('cauchos', 'vida_util_cauchos_meses', 24),
    'lubricantes': ('aceite', 'vida_util_aceite_meses', 6),
    'filtros': ('filtros', 'vida_util_filtros_meses', 6),
    'baterias': ('bateria', 'vida_util_bateria_meses', 24),
    'frenos': ('frenos', 'vida_util_frenos_meses', 18),
}

TIPO_LABEL = {
    'cauchos': 'Reemplazo de cauchos',
    'aceite': 'Cambio de aceite',
    'filtros': 'Cambio de filtros',
    'bateria': 'Reemplazo de bateria',
    'frenos': 'Revision/cambio de frenos',
    'refrigerante': 'Cambio de refrigerante',
    'servicio_general': 'Servicio general',
}


class VehicleLogModel(Connection):
    def __init__(self):
        super().__init__()
        self.notifications = NotificationModel()

    # ------------------------- utilidades -------------------------

    def _vehicle_plate(self, vid):
        placa = (str(vid or '').strip().upper())
        if not placa:
            return None
        vehicle = self.fetch_one("transalca", "SELECT placa_vehiculo FROM vehiculos WHERE placa_vehiculo=%s", (placa,))
        return vehicle['placa_vehiculo'] if vehicle else None

    def _config_int(self, clave, default):
        row = self.fetch_one("transalca", "SELECT valor FROM configuracion WHERE clave=%s", (clave,))
        try:
            return int(row['valor']) if row else default
        except (TypeError, ValueError):
            return default

    def _as_date(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

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
            "SELECT id_servicio_mecanico AS id FROM servicio_mecanico WHERE "
            "(%s IS NULL OR orden_venta_id=%s) AND "
            "(%s IS NULL OR servicio_id=%s) AND "
            "(%s IS NULL OR mecanico_cedula=%s) "
            "ORDER BY fecha_servicio DESC LIMIT 1",
            (orden_venta_id, orden_venta_id, servicio_id, servicio_id, mecanico_cedula, mecanico_cedula)
        )
        return row['id'] if row else None

    # ------------------------- consultas -------------------------

    def _get_by_vehicle(self, vid, limit=50):
        return self.fetch_all("transalca",
            "SELECT " + BITACORA_SELECT + ", m.nombre_mecanico as mecanico_nombre, m.apellido_mecanico as mecanico_apellido, "
            "s.nombre_servicio as servicio_nombre "
            "FROM bitacora_vehiculo bv "
            "LEFT JOIN servicio_mecanico sm ON bv.servicio_mecanico_id = sm.id_servicio_mecanico "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
            "LEFT JOIN servicios s ON sm.servicio_id = s.id_servicio "
            "WHERE bv.vehiculo_placa=%s "
            "ORDER BY bv.fecha_bitacora DESC LIMIT %s", (self._vehicle_plate(vid), limit))

    def _get_by_cliente(self, cliente_cedula, limit=100):
        return self.fetch_all("transalca",
            "SELECT " + BITACORA_SELECT + ", v.placa_vehiculo AS placa, v.marca_vehiculo AS marca, v.modelo_vehiculo AS modelo, "
            "m.nombre_mecanico as mecanico_nombre, m.apellido_mecanico as mecanico_apellido "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa_vehiculo "
            "INNER JOIN cliente_vehiculo cv ON cv.vehiculo_placa = v.placa_vehiculo AND cv.estado = 1 "
            "LEFT JOIN servicio_mecanico sm ON bv.servicio_mecanico_id = sm.id_servicio_mecanico "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
            "WHERE cv.cliente_cedula=%s ORDER BY bv.fecha_bitacora DESC LIMIT %s",
            (cliente_cedula, limit))

    def _get_by_id(self, lid):
        return self.fetch_one("transalca",
            "SELECT " + BITACORA_SELECT + ", v.placa_vehiculo AS placa, v.marca_vehiculo AS marca, v.modelo_vehiculo AS modelo, "
            "m.nombre_mecanico as mecanico_nombre, m.apellido_mecanico as mecanico_apellido, "
            "s.nombre_servicio as servicio_nombre, c.identificador_cliente as cliente_cedula, "
            "c.nombre_cliente as cliente_nombre, '' as cliente_apellido "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa_vehiculo "
            "LEFT JOIN cliente_vehiculo cv ON cv.vehiculo_placa = v.placa_vehiculo AND cv.estado = 1 "
            "LEFT JOIN cliente c ON cv.cliente_cedula = c.identificador_cliente "
            "LEFT JOIN servicio_mecanico sm ON bv.servicio_mecanico_id = sm.id_servicio_mecanico "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
            "LEFT JOIN servicios s ON sm.servicio_id = s.id_servicio "
            "WHERE bv.id_bitacora_vehiculo=%s", (lid,))

    def _get_admin_listing(self, cliente=None, vehiculo=None, fecha_desde=None, fecha_hasta=None):
        sql = ("SELECT " + BITACORA_SELECT + ", v.placa_vehiculo AS placa, v.marca_vehiculo AS marca, "
               "v.modelo_vehiculo AS modelo, v.kilometraje_actual, "
               "COALESCE(GROUP_CONCAT(DISTINCT c.nombre_cliente SEPARATOR ', '), '-') AS cliente_nombre, "
               "COALESCE(GROUP_CONCAT(DISTINCT c.identificador_cliente SEPARATOR ','), '') AS cliente_cedula, "
               "s.nombre_servicio AS servicio_nombre "
               "FROM bitacora_vehiculo bv "
               "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa_vehiculo "
               "LEFT JOIN cliente_vehiculo cv ON cv.vehiculo_placa = v.placa_vehiculo AND cv.estado = 1 "
               "LEFT JOIN cliente c ON cv.cliente_cedula = c.identificador_cliente "
               "LEFT JOIN servicio_mecanico sm ON bv.servicio_mecanico_id = sm.id_servicio_mecanico "
               "LEFT JOIN servicios s ON sm.servicio_id = s.id_servicio "
               "WHERE 1=1")
        params = []
        if vehiculo:
            sql += " AND bv.vehiculo_placa LIKE %s"
            params.append(f"%{str(vehiculo).strip().upper()}%")
        if cliente:
            sql += (" AND EXISTS (SELECT 1 FROM cliente_vehiculo cv2 INNER JOIN cliente c2 ON c2.identificador_cliente = cv2.cliente_cedula "
                    "WHERE cv2.vehiculo_placa = bv.vehiculo_placa AND cv2.estado = 1 "
                    "AND (c2.identificador_cliente LIKE %s OR c2.nombre_cliente LIKE %s))")
            q = f"%{cliente}%"
            params.extend([q, q])
        if fecha_desde:
            sql += " AND DATE(bv.fecha_bitacora) >= %s"
            params.append(fecha_desde)
        if fecha_hasta:
            sql += " AND DATE(bv.fecha_bitacora) <= %s"
            params.append(fecha_hasta)
        sql += " GROUP BY bv.id_bitacora_vehiculo ORDER BY bv.fecha_bitacora DESC LIMIT 300"
        return self.fetch_all("transalca", sql, tuple(params) if params else None)

    def _create(self, data):
        placa = self._vehicle_plate(data['vehiculo_id'])
        if not placa:
            return None
        servicio_mecanico_id = self._service_mechanic_id(data)
        return self.insert("transalca",
            "INSERT INTO bitacora_vehiculo (vehiculo_placa, servicio_mecanico_id, descripcion_bitacora, kilometraje, "
            "aceite_usado, filtros_usados, refrigerante_usado, productos_usados, cauchos_usados, "
            "proximo_mantenimiento, observaciones_bitacora) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (placa, servicio_mecanico_id,
             (data.get('descripcion') or '').strip(),
             data.get('kilometraje') or None,
             (data.get('aceite_usado') or '').strip(),
             (data.get('filtros_usados') or '').strip(),
             (data.get('refrigerante_usado') or '').strip(),
             (data.get('productos_usados') or '').strip(),
             (data.get('cauchos_info') or data.get('cauchos_usados') or '').strip(),
             (data.get('proximo_mantenimiento') or '').strip(),
             (data.get('observaciones') or '').strip()))

    def _count_oil_changes(self, vid):
        result = self.fetch_one("transalca",
            "SELECT COUNT(*) as total FROM bitacora_vehiculo "
            "WHERE vehiculo_placa=%s "
            "AND aceite_usado IS NOT NULL AND aceite_usado != ''", (self._vehicle_plate(vid),))
        return result['total'] if result else 0

    def _get_service_count(self, vid, tipo_servicio=None):
        sql = "SELECT COUNT(*) as total FROM bitacora_vehiculo WHERE vehiculo_placa=%s"
        params = [self._vehicle_plate(vid)]
        if tipo_servicio:
            sql += " AND descripcion_bitacora LIKE %s"
            params.append(f"%{tipo_servicio}%")
        result = self.fetch_one("transalca", sql, tuple(params))
        return result['total'] if result else 0

    # --------------- sincronizacion automatica desde servicios ---------------

    def _sync_from_services(self):
        """Registra automaticamente en la bitacora los servicios completados,
        con los productos y cauchos usados en la orden asociada."""
        rows = self.fetch_all("transalca",
            "SELECT sm.id_servicio_mecanico AS id, sm.servicio_id, sm.orden_venta_id, sm.vehiculo_placa, sm.fecha_servicio, "
            "s.nombre_servicio "
            "FROM servicio_mecanico sm "
            "INNER JOIN servicios s ON s.id_servicio = sm.servicio_id "
            "WHERE sm.estado_servicio = 'completado' AND sm.vehiculo_placa IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM bitacora_vehiculo bv WHERE bv.servicio_mecanico_id = sm.id_servicio_mecanico)")
        created = 0
        for row in rows:
            productos = []
            cauchos = []
            if row.get('orden_venta_id'):
                detalles = self.fetch_all("transalca",
                    "SELECT p.nombre_producto, p.categoria, d.cantidad_detalle_orden_venta_producto AS cantidad "
                    "FROM detalle_orden_venta_productos d INNER JOIN productos p ON p.codigo = d.producto_codigo "
                    "WHERE d.orden_id = %s", (row['orden_venta_id'],))
                for det in detalles:
                    etiqueta = f"{det['nombre_producto']} x{det['cantidad']}"
                    productos.append(etiqueta)
                    if (det.get('categoria') or '').strip().lower() == 'cauchos':
                        cauchos.append(etiqueta)
            vehiculo = self.fetch_one("transalca",
                "SELECT kilometraje_actual FROM vehiculos WHERE placa_vehiculo = %s", (row['vehiculo_placa'],))
            self.insert("transalca",
                "INSERT INTO bitacora_vehiculo (vehiculo_placa, servicio_mecanico_id, descripcion_bitacora, kilometraje, "
                "productos_usados, cauchos_usados, fecha_bitacora) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (row['vehiculo_placa'], row['id'],
                 f"Servicio realizado: {row['nombre_servicio']}",
                 (vehiculo or {}).get('kilometraje_actual'),
                 '; '.join(productos), '; '.join(cauchos),
                 row.get('fecha_servicio') or datetime.now()))
            created += 1
        return created

    # ------------------------- predicciones -------------------------

    def _upsert_prediction(self, placa, tipo, fecha_base, fecha_estimada, referencia, base_calculo):
        today = date.today()
        dias = (fecha_estimada - today).days
        if dias < 0:
            prioridad, estado = 'critica', 'vencida'
        elif dias <= 14:
            prioridad, estado = 'alta', 'activa'
        elif dias <= 45:
            prioridad, estado = 'media', 'activa'
        else:
            prioridad, estado = 'baja', 'activa'
        existing = self.fetch_one("transalca",
            "SELECT id_bitacora_prediccion AS id, fecha_estimada, estado, notificado FROM bitacora_prediccion "
            "WHERE vehiculo_placa=%s AND tipo_prediccion=%s", (placa, tipo))
        if existing:
            if existing.get('estado') == 'atendida' and self._as_date(existing.get('fecha_estimada')) == fecha_estimada:
                return existing['id']
            reset_notif = self._as_date(existing.get('fecha_estimada')) != fecha_estimada
            self.update("transalca",
                "UPDATE bitacora_prediccion SET fecha_base=%s, fecha_estimada=%s, referencia_detalle=%s, "
                "base_calculo=%s, prioridad_prediccion=%s, estado=%s, notificado=CASE WHEN %s THEN 0 ELSE notificado END "
                "WHERE id_bitacora_prediccion=%s",
                (fecha_base, fecha_estimada, referencia, base_calculo, prioridad, estado,
                 1 if reset_notif else 0, existing['id']))
            return existing['id']
        return self.insert("transalca",
            "INSERT INTO bitacora_prediccion (vehiculo_placa, tipo_prediccion, referencia_detalle, fecha_base, "
            "fecha_estimada, base_calculo, prioridad_prediccion, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (placa, tipo, referencia, fecha_base, fecha_estimada, base_calculo, prioridad, estado))

    def _generate_predictions(self):
        """Calcula fechas estimadas de proximos mantenimientos por vehiculo segun el
        historial de la bitacora, el tipo/categoria de producto usado y la vida util configurada."""
        vehicles = self.fetch_all("transalca",
            "SELECT placa_vehiculo, kilometraje_actual, tipo_vehiculo FROM vehiculos WHERE estado = 1")
        generated = 0
        for v in vehicles:
            placa = v['placa_vehiculo']
            # 1) por categoria de producto usado en bitacora
            for categoria, (tipo, clave, default_meses) in CATEGORIA_PREDICCION.items():
                row = self.fetch_one("transalca",
                    "SELECT MAX(DATE(bv.fecha_bitacora)) AS ultima, "
                    "SUBSTRING_INDEX(GROUP_CONCAT(bv.productos_usados ORDER BY bv.fecha_bitacora DESC SEPARATOR '||'), '||', 1) AS detalle "
                    "FROM bitacora_vehiculo bv "
                    "WHERE bv.vehiculo_placa = %s AND ("
                    "  EXISTS (SELECT 1 FROM servicio_mecanico sm "
                    "          INNER JOIN detalle_orden_venta_productos d ON d.orden_id = sm.orden_venta_id "
                    "          INNER JOIN productos p ON p.codigo = d.producto_codigo "
                    "          WHERE sm.id_servicio_mecanico = bv.servicio_mecanico_id AND LOWER(p.categoria) = %s) "
                    "  OR (%s = 'cauchos' AND bv.cauchos_usados IS NOT NULL AND bv.cauchos_usados != '') "
                    "  OR (%s = 'lubricantes' AND bv.aceite_usado IS NOT NULL AND bv.aceite_usado != '') "
                    "  OR (%s = 'filtros' AND bv.filtros_usados IS NOT NULL AND bv.filtros_usados != '')"
                    ")",
                    (placa, categoria, categoria, categoria, categoria))
                ultima = self._as_date((row or {}).get('ultima'))
                if not ultima:
                    continue
                meses = self._config_int(clave, default_meses)
                fecha_estimada = ultima + timedelta(days=meses * 30)
                base = f"Ultimo registro {ultima.isoformat()} + {meses} meses de vida util estimada ({categoria})"
                if v.get('kilometraje_actual'):
                    base += f"; km actual {v['kilometraje_actual']}"
                self._upsert_prediction(placa, tipo, ultima, fecha_estimada,
                                        (row or {}).get('detalle') or TIPO_LABEL[tipo], base)
                generated += 1
            # 2) refrigerante
            row = self.fetch_one("transalca",
                "SELECT MAX(DATE(fecha_bitacora)) AS ultima FROM bitacora_vehiculo "
                "WHERE vehiculo_placa=%s AND refrigerante_usado IS NOT NULL AND refrigerante_usado != ''", (placa,))
            ultima = self._as_date((row or {}).get('ultima'))
            if ultima:
                meses = self._config_int('vida_util_refrigerante_meses', 24)
                self._upsert_prediction(placa, 'refrigerante', ultima, ultima + timedelta(days=meses * 30),
                                        TIPO_LABEL['refrigerante'],
                                        f"Ultimo registro {ultima.isoformat()} + {meses} meses de vida util estimada")
                generated += 1
            # 3) servicio general por frecuencia de servicios
            row = self.fetch_one("transalca",
                "SELECT MAX(DATE(fecha_bitacora)) AS ultima, COUNT(*) AS total FROM bitacora_vehiculo WHERE vehiculo_placa=%s", (placa,))
            ultima = self._as_date((row or {}).get('ultima'))
            if ultima:
                meses = self._config_int('vida_util_servicio_general_meses', 6)
                base = (f"Ultimo servicio {ultima.isoformat()} + {meses} meses; "
                        f"{(row or {}).get('total') or 0} servicios en historial")
                self._upsert_prediction(placa, 'servicio_general', ultima, ultima + timedelta(days=meses * 30),
                                        TIPO_LABEL['servicio_general'], base)
                generated += 1
        return generated

    def _get_predictions(self, vehiculo=None, cliente=None, estado=None, prioridad=None):
        sql = ("SELECT bp.*, bp.id_bitacora_prediccion AS id, bp.prioridad_prediccion AS prioridad, v.marca_vehiculo AS marca, v.modelo_vehiculo AS modelo, "
               "COALESCE(GROUP_CONCAT(DISTINCT c.nombre_cliente SEPARATOR ', '), '-') AS cliente_nombre, "
               "COALESCE(GROUP_CONCAT(DISTINCT c.identificador_cliente SEPARATOR ','), '') AS cliente_cedula, "
               "DATEDIFF(bp.fecha_estimada, CURDATE()) AS dias_restantes "
               "FROM bitacora_prediccion bp "
               "INNER JOIN vehiculos v ON v.placa_vehiculo = bp.vehiculo_placa "
               "LEFT JOIN cliente_vehiculo cv ON cv.vehiculo_placa = bp.vehiculo_placa AND cv.estado = 1 "
               "LEFT JOIN cliente c ON c.identificador_cliente = cv.cliente_cedula "
               "WHERE 1=1")
        params = []
        if vehiculo:
            sql += " AND bp.vehiculo_placa LIKE %s"
            params.append(f"%{str(vehiculo).strip().upper()}%")
        if cliente:
            sql += (" AND EXISTS (SELECT 1 FROM cliente_vehiculo cv2 INNER JOIN cliente c2 ON c2.identificador_cliente = cv2.cliente_cedula "
                    "WHERE cv2.vehiculo_placa = bp.vehiculo_placa AND cv2.estado = 1 "
                    "AND (c2.identificador_cliente LIKE %s OR c2.nombre_cliente LIKE %s))")
            q = f"%{cliente}%"
            params.extend([q, q])
        if estado:
            sql += " AND bp.estado = %s"
            params.append(estado)
        if prioridad:
            sql += " AND bp.prioridad_prediccion = %s"
            params.append(prioridad)
        sql += " GROUP BY bp.id_bitacora_prediccion ORDER BY bp.fecha_estimada ASC"
        rows = self.fetch_all("transalca", sql, tuple(params) if params else None)
        for r in rows:
            r['tipo_label'] = TIPO_LABEL.get(r.get('tipo_prediccion'), r.get('tipo_prediccion'))
        return rows

    def _get_predictions_by_client(self, cliente_cedula):
        rows = self.fetch_all("transalca",
            "SELECT bp.*, bp.id_bitacora_prediccion AS id, bp.prioridad_prediccion AS prioridad, v.marca_vehiculo AS marca, v.modelo_vehiculo AS modelo, "
            "DATEDIFF(bp.fecha_estimada, CURDATE()) AS dias_restantes "
            "FROM bitacora_prediccion bp "
            "INNER JOIN vehiculos v ON v.placa_vehiculo = bp.vehiculo_placa "
            "INNER JOIN cliente_vehiculo cv ON cv.vehiculo_placa = bp.vehiculo_placa AND cv.estado = 1 "
            "WHERE cv.cliente_cedula = %s AND bp.estado != 'atendida' "
            "ORDER BY bp.fecha_estimada ASC",
            (cliente_cedula,))
        for r in rows:
            r['tipo_label'] = TIPO_LABEL.get(r.get('tipo_prediccion'), r.get('tipo_prediccion'))
        return rows

    def _mark_prediction_attended(self, prediction_id):
        return self.update("transalca",
            "UPDATE bitacora_prediccion SET estado='atendida' WHERE id_bitacora_prediccion=%s", (prediction_id,))

    def _notify_due_predictions(self, dias_aviso=14):
        """Notifica al cliente y a los administradores las predicciones proximas o vencidas."""
        rows = self.fetch_all("transalca",
            "SELECT bp.*, bp.id_bitacora_prediccion AS id, v.marca_vehiculo, v.modelo_vehiculo, DATEDIFF(bp.fecha_estimada, CURDATE()) AS dias "
            "FROM bitacora_prediccion bp INNER JOIN vehiculos v ON v.placa_vehiculo = bp.vehiculo_placa "
            "WHERE bp.estado IN ('activa', 'vencida') AND bp.notificado = 0 "
            "AND DATEDIFF(bp.fecha_estimada, CURDATE()) <= %s", (dias_aviso,))
        sent = 0
        for r in rows:
            tipo_label = TIPO_LABEL.get(r.get('tipo_prediccion'), r.get('tipo_prediccion'))
            vehiculo_txt = f"{r['marca_vehiculo']} {r['modelo_vehiculo']} ({r['vehiculo_placa']})"
            dias = int(r.get('dias') or 0)
            fecha_txt = self._as_date(r['fecha_estimada']).strftime('%d/%m/%Y')
            if dias < 0:
                titulo = f"Mantenimiento vencido: {tipo_label}"
                detalle = f"vencio el {fecha_txt}"
                prioridad = 'critica'
            else:
                titulo = f"Mantenimiento proximo: {tipo_label}"
                detalle = f"estimado para el {fecha_txt}"
                prioridad = 'alta' if dias <= 7 else 'media'
            mensaje = (f"Vehiculo: {vehiculo_txt}. {tipo_label} ({r.get('referencia_detalle') or ''}) {detalle}. "
                       f"Recomendacion: agende el servicio en Transalca.")
            clientes = self.fetch_all("transalca",
                "SELECT cliente_cedula FROM cliente_vehiculo WHERE vehiculo_placa=%s AND estado=1",
                (r['vehiculo_placa'],))
            for cl in clientes:
                self.notifications.ejecutar("create_unique", {
                    'cliente_cedula': cl['cliente_cedula'],
                    'tipo': 'mantenimiento',
                    'titulo': titulo,
                    'mensaje': mensaje,
                    'prioridad': prioridad,
                    'referencia_id': r['id']
                }, hours=72)
            for admin in self.notifications.ejecutar("get_admin_users", 'vehiculos'):
                self.notifications.ejecutar("create_unique", {
                    'usuario_id': admin['id'],
                    'tipo': 'mantenimiento',
                    'titulo': titulo + f" [{r['vehiculo_placa']}]",
                    'mensaje': mensaje,
                    'prioridad': prioridad,
                    'referencia_id': r['id']
                }, hours=72)
            self.update("transalca",
                "UPDATE bitacora_prediccion SET notificado = 1 WHERE id_bitacora_prediccion = %s", (r['id'],))
            sent += 1
        return sent

    def _run_automatic_cycle(self):
        """Ciclo automatico: sincroniza servicios, recalcula predicciones y notifica."""
        result = {'sincronizados': 0, 'predicciones': 0, 'notificaciones': 0, 'stock_bajo': 0}
        try:
            result['sincronizados'] = self._sync_from_services()
            result['predicciones'] = self._generate_predictions()
            result['notificaciones'] = self._notify_due_predictions()
        except Exception:
            logger.exception("Error en ciclo automatico de bitacora")
        try:
            from model.inventory_model import InventoryModel
            result['stock_bajo'] = InventoryModel().ejecutar("check_low_stock_and_notify")
        except Exception:
            logger.exception("Error en chequeo de stock bajo")
        return result

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_by_vehicle": self._get_by_vehicle,
            "get_by_cliente": self._get_by_cliente,
            "get_by_id": self._get_by_id,
            "get_admin_listing": self._get_admin_listing,
            "create": self._create,
            "count_oil_changes": self._count_oil_changes,
            "get_service_count": self._get_service_count,
            "sync_from_services": self._sync_from_services,
            "generate_predictions": self._generate_predictions,
            "get_predictions": self._get_predictions,
            "get_predictions_by_client": self._get_predictions_by_client,
            "mark_prediction_attended": self._mark_prediction_attended,
            "notify_due_predictions": self._notify_due_predictions,
            "run_automatic_cycle": self._run_automatic_cycle,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)


class BitacoraScheduler:
    """Tarea programada que ejecuta el ciclo automatico de bitacora periodicamente."""

    def __init__(self, interval_seconds=3600):
        self._interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name='bitacora-auto', daemon=True)
            self._thread.start()
            return True

    def stop(self):
        self._stop_event.set()

    def _run_loop(self):
        # primera pasada poco despues de arrancar
        self._stop_event.wait(30)
        while not self._stop_event.is_set():
            try:
                VehicleLogModel().ejecutar("run_automatic_cycle")
            except Exception:
                logger.exception("Fallo el ciclo programado de bitacora")
            self._stop_event.wait(self._interval)


_scheduler = BitacoraScheduler()


def start_bitacora_scheduler():
    return _scheduler.start()
