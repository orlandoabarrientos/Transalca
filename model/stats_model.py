from model.connection import Connection
from datetime import datetime, timedelta

class StatsModel(Connection):
    def __init__(self):
        super().__init__()

    def get_revenue_timeline(self, days=30):
        start_date = datetime.now() - timedelta(days=days)
        sql = "SELECT DATE(fecha) as fecha_corta, COALESCE(SUM(total), 0) as total FROM ordenes_venta WHERE estado = 'aprobada' AND fecha >= %s GROUP BY DATE(fecha) ORDER BY fecha_corta ASC"
        records = self.fetch_all("transalca", sql, (start_date,))
        labels = [r['fecha_corta'].strftime('%Y-%m-%d') for r in records]
        data = [float(r['total']) for r in records]
        return {"labels": labels, "data": data}

    def get_top_performing_products(self, limit=5):
        sql = "SELECT p.nombre, SUM(d.cantidad) as total_vendido FROM detalle_orden_venta d INNER JOIN productos p ON d.producto_codigo = p.codigo WHERE d.tipo = 'producto' GROUP BY d.producto_codigo ORDER BY total_vendido DESC LIMIT %s"
        records = self.fetch_all("transalca", sql, (limit,))
        labels = [r['nombre'][:15] for r in records]
        data = [int(r['total_vendido']) for r in records]
        return {"labels": labels, "data": data}

    def get_order_status_distribution(self):
        sql = "SELECT estado, COUNT(*) as cantidad FROM ordenes_venta GROUP BY estado"
        records = self.fetch_all("transalca", sql)
        labels = [str(r['estado']).capitalize() for r in records]
        data = [int(r['cantidad']) for r in records]
        return {"labels": labels, "data": data}

    def get_payments_distribution(self):
        sql = "SELECT metodo_pago as metodo, COUNT(*) as cantidad FROM ordenes_venta WHERE metodo_pago IS NOT NULL GROUP BY metodo_pago"
        records = self.fetch_all("transalca", sql)
        labels = [str(r['metodo']).capitalize() for r in records]
        data = [int(r['cantidad']) for r in records]
        return {"labels": labels, "data": data}
