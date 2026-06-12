from model.connection import Connection
from datetime import datetime, timedelta


class StatsModel(Connection):
    def __init__(self):
        super().__init__()

    def _get_revenue_timeline(self, days=30):
        start_date = datetime.now() - timedelta(days=days)
        sql = ("SELECT DATE(fecha_orden_venta) as fecha_corta, COALESCE(SUM(total_orden_venta), 0) as total "
               "FROM ordenes_venta WHERE estado = 'aprobada' AND fecha_orden_venta >= %s "
               "GROUP BY DATE(fecha_orden_venta) ORDER BY fecha_corta ASC")
        records = self.fetch_all("transalca", sql, (start_date,))
        labels = [r['fecha_corta'].strftime('%Y-%m-%d') for r in records]
        data = [float(r['total']) for r in records]
        return {"labels": labels, "data": data}

    def _get_top_performing_products(self, limit=5):
        sql = ("SELECT p.nombre_producto AS nombre, SUM(d.cantidad_detalle_orden_venta_producto) as total_vendido "
               "FROM detalle_orden_venta_productos d INNER JOIN productos p ON d.producto_codigo = p.codigo "
               "GROUP BY d.producto_codigo ORDER BY total_vendido DESC LIMIT %s")
        records = self.fetch_all("transalca", sql, (limit,))
        labels = [r['nombre'][:15] for r in records]
        data = [int(r['total_vendido']) for r in records]
        return {"labels": labels, "data": data}

    def _get_order_status_distribution(self):
        sql = "SELECT estado, COUNT(*) as cantidad FROM ordenes_venta GROUP BY estado"
        records = self.fetch_all("transalca", sql)
        labels = [str(r['estado']).capitalize() for r in records]
        data = [int(r['cantidad']) for r in records]
        return {"labels": labels, "data": data}

    def _get_payments_distribution(self):
        sql = (
            "SELECT mp.nombre_metodo_pago as metodo, COUNT(*) as cantidad "
            "FROM ordenes_venta ov INNER JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "GROUP BY mp.nombre_metodo_pago"
        )
        records = self.fetch_all("transalca", sql)
        labels = [str(r['metodo']).capitalize() for r in records]
        data = [int(r['cantidad']) for r in records]
        return {"labels": labels, "data": data}

    def _get_top_services(self, limit=5):
        """Reporte nuevo: servicios mas solicitados con ingreso generado, calculado por codigo."""
        sql = ("SELECT s.nombre_servicio AS nombre, COUNT(*) as total_solicitados, "
               "COALESCE(SUM(d.cantidad_detalle_orden_venta_servicio * d.precio_unitario_servicio), 0) as ingreso "
               "FROM detalle_orden_venta_servicios d INNER JOIN servicios s ON d.servicio_id = s.id_servicio "
               "GROUP BY d.servicio_id ORDER BY total_solicitados DESC, ingreso DESC LIMIT %s")
        records = self.fetch_all("transalca", sql, (limit,))
        labels = [r['nombre'][:20] for r in records]
        data = [int(r['total_solicitados']) for r in records]
        ingresos = [float(r['ingreso']) for r in records]
        return {"labels": labels, "data": data, "ingresos": ingresos}

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_revenue_timeline": self._get_revenue_timeline,
            "get_top_performing_products": self._get_top_performing_products,
            "get_order_status_distribution": self._get_order_status_distribution,
            "get_payments_distribution": self._get_payments_distribution,
            "get_top_services": self._get_top_services,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
