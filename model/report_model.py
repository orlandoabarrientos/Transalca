from model.connection import Connection
from datetime import datetime, timedelta


class ReportModel(Connection):
    def __init__(self):
        super().__init__()

    def get_dashboard_stats(self):
        total_products = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM productos WHERE estado = 1")
        total_categories = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM categorias WHERE estado = 1")
        total_clients = self.fetch_one("mantenimiento", "SELECT COUNT(*) as total FROM usuarios WHERE tipo = 'cliente' AND estado = 1")
        total_employees = self.fetch_one("mantenimiento", "SELECT COUNT(*) as total FROM usuarios WHERE tipo = 'empleado' AND estado = 1")
        pending_payments = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM comprobantes_pago WHERE estado = 'pendiente'")
        total_sales = self.fetch_one("transalca", "SELECT COALESCE(SUM(total), 0) as total FROM ordenes_venta WHERE estado = 'aprobada'")
        total_orders = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM ordenes_venta WHERE estado != 'cancelada'")
        low_stock = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM inventario WHERE stock <= stock_minimo")
        active_promos = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM promociones WHERE estado = 1")
        return {
            "total_products": total_products['total'] if total_products else 0,
            "total_categories": total_categories['total'] if total_categories else 0,
            "total_clients": total_clients['total'] if total_clients else 0,
            "total_employees": total_employees['total'] if total_employees else 0,
            "pending_payments": pending_payments['total'] if pending_payments else 0,
            "total_sales": float(total_sales['total']) if total_sales else 0,
            "total_orders": total_orders['total'] if total_orders else 0,
            "low_stock": low_stock['total'] if low_stock else 0,
            "active_promos": active_promos['total'] if active_promos else 0
        }

    def get_recent_orders(self, limit=10):
        orders = self.fetch_all("transalca", "SELECT * FROM ordenes_venta ORDER BY fecha DESC LIMIT %s", (limit,))
        for order in orders:
            client = self.fetch_one("mantenimiento", "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}" if client else 'N/A'
            order['fecha'] = order['fecha'].isoformat() if hasattr(order['fecha'], 'isoformat') else order['fecha']
        return orders

    def get_sales_history(self, start_date=None, end_date=None, status=None):
        sql = "SELECT id, cliente_cedula, fecha, total, estado FROM ordenes_venta WHERE 1=1"
        params = []
        if start_date:
            sql += " AND DATE(fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(fecha) <= %s"
            params.append(end_date)
        if status:
            sql += " AND estado = %s"
            params.append(status)
        sql += " ORDER BY fecha DESC"

        orders = self.fetch_all("transalca", sql, tuple(params) if params else None)

        for order in orders:
            client = self.fetch_one("mantenimiento", "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            order['cliente'] = f"{client['nombre']} {client['apellido']}" if client else 'N/A'
            order['fecha'] = order['fecha'].isoformat() if hasattr(order['fecha'], 'isoformat') else order['fecha']
        return orders

    def get_payments_history(self, start_date=None, end_date=None, status=None):
        sql = "SELECT c.id, o.cliente_cedula, c.orden_venta_id as orden_id, CONCAT('IMG-', c.id) as referencia, o.total as monto, 'USD' as moneda, o.metodo_pago as metodo, c.fecha, c.estado FROM comprobantes_pago c INNER JOIN ordenes_venta o ON c.orden_venta_id = o.id WHERE 1=1"
        params = []
        if start_date:
            sql += " AND DATE(c.fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(c.fecha) <= %s"
            params.append(end_date)
        if status:
            sql += " AND c.estado = %s"
            params.append(status)
        sql += " ORDER BY c.fecha DESC"

        payments = self.fetch_all("transalca", sql, tuple(params) if params else None)
        for p in payments:
            client = self.fetch_one("mantenimiento", "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (p['cliente_cedula'],))
            p['cliente'] = f"{client['nombre']} {client['apellido']}" if client else 'N/A'
            p['fecha'] = p['fecha'].isoformat() if hasattr(p['fecha'], 'isoformat') else p['fecha']
        return payments

    def get_inventory_kardex(self, start_date=None, end_date=None):
        sql = "SELECT i.producto_codigo, 'Inventario Actual' as tipo, i.stock as cantidad, 'Ajuste Sistemico' as motivo, i.updated_at as fecha, p.nombre as producto, p.codigo FROM inventario i INNER JOIN productos p ON i.producto_codigo = p.codigo WHERE 1=1"
        params = []
        if start_date:
            sql += " AND DATE(i.updated_at) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(i.updated_at) <= %s"
            params.append(end_date)
        sql += " ORDER BY i.updated_at DESC"

        moves = self.fetch_all("transalca", sql, tuple(params) if params else None)
        for m in moves:
            m['fecha'] = m['fecha'].isoformat() if hasattr(m['fecha'], 'isoformat') else m['fecha']
        return moves

    def get_mechanics_performance(self, start_date=None, end_date=None):
        sql = "SELECT s.mecanico_cedula, m.nombre as servicio_nombre, o.estado, o.fecha, d.cantidad, d.subtotal FROM detalle_orden_venta d INNER JOIN ordenes_venta o ON d.orden_id = o.id INNER JOIN servicios m ON d.servicio_id = m.id INNER JOIN servicio_mecanico s ON s.orden_venta_id = o.id AND s.servicio_id = m.id WHERE d.tipo = 'servicio'"
        params = []
        if start_date:
            sql += " AND DATE(o.fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(o.fecha) <= %s"
            params.append(end_date)

        records = self.fetch_all("transalca", sql, tuple(params) if params else None)

        mecanicos_stats = {}
        for r in records:
            mid = r['mecanico_cedula']
            if mid not in mecanicos_stats:
                mec = self.fetch_one("transalca", "SELECT nombre, apellido FROM mecanicos WHERE cedula = %s", (mid,))
                if mec:
                    mecanico_nombre = f"{mec['nombre']} {mec['apellido']}"
                else:
                    mecanico_nombre = 'Desconocido'

                mecanicos_stats[mid] = {
                    "mecanico_nombre": mecanico_nombre,
                    "total_asignados": 0,
                    "total_completados": 0,
                    "ingreso_generado": 0.0
                }
            mecanicos_stats[mid]["total_asignados"] += 1
            if r['estado'] == 'entregada':
                mecanicos_stats[mid]["total_completados"] += 1
            mecanicos_stats[mid]["ingreso_generado"] += float(r['subtotal'])

        return list(mecanicos_stats.values())

    def get_bitacora_audit(self, start_date=None, end_date=None, modulo=None):
        sql = "SELECT id, usuario_id, accion, modulo, descripcion, ip, fecha FROM bitacora WHERE 1=1"
        params = []
        if start_date:
            sql += " AND DATE(fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(fecha) <= %s"
            params.append(end_date)
        if modulo:
            sql += " AND modulo = %s"
            params.append(modulo)
        sql += " ORDER BY fecha DESC LIMIT 500"

        logs = self.fetch_all("mantenimiento", sql, tuple(params) if params else None)
        for l in logs:
            user = self.fetch_one("mantenimiento", "SELECT email FROM usuarios WHERE id = %s", (l['usuario_id'],))
            l['usuario'] = user['email'] if user else 'Sistema'
            l['fecha'] = l['fecha'].isoformat() if hasattr(l['fecha'], 'isoformat') else l['fecha']
        return logs
