from model.connection import Connection
from datetime import datetime, timedelta


class ReportModel(Connection):
    def __init__(self):
        super().__init__()

    def _client_name(self, cedula):
        client = self.fetch_one(
            "transalca",
            "SELECT c.nombre, c.apellido, c.tipo_cliente, e.razon_social "
            "FROM clientes c LEFT JOIN empresas e ON e.rif = c.cedula "
            "WHERE c.cedula = %s",
            (cedula,))
        if not client:
            return 'N/A'
        if client.get('tipo_cliente') == 'empresa':
            return client.get('razon_social') or client.get('nombre') or 'N/A'
        return f"{client.get('nombre', '')} {client.get('apellido', '')}".strip() or 'N/A'

    def get_dashboard_stats(self):
        total_products = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM productos WHERE estado = 1")
        total_categories = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM categorias WHERE estado = 1")
        total_clients = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM clientes WHERE tipo_cliente = 'persona' AND estado = 1")
        total_employees = self.fetch_one("mantenimiento", "SELECT COUNT(*) as total FROM usuarios WHERE tipo IN ('admin','vendedor','mecanico','soporte','empleado') AND estado = 1")
        pending_payments = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM comprobantes_pago WHERE estado = 'pendiente'")
        total_sales = self.fetch_one("transalca", "SELECT COALESCE(SUM(total), 0) as total FROM ordenes_venta WHERE estado = 'aprobada'")
        total_orders = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM ordenes_venta WHERE estado != 'cancelada'")
        low_stock = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM stock WHERE stock <= stock_minimo")
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
        orders = self.fetch_all("transalca",
            "SELECT ov.*, mp.nombre AS metodo_pago, mp.nombre AS metodo_pago_nombre "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id = ov.metodo_pago_id "
            "ORDER BY ov.fecha DESC LIMIT %s", (limit,))
        for order in orders:
            order['cliente_nombre'] = self._client_name(order['cliente_cedula'])
            order['fecha'] = order['fecha'].isoformat() if hasattr(order['fecha'], 'isoformat') else order['fecha']
        return orders

    def get_sales_history(self, start_date=None, end_date=None, status=None):
        sql = (
            "SELECT ov.id, ov.cliente_cedula, ov.fecha, ov.total, ov.estado, "
            "c.nombre, c.apellido, c.tipo_cliente, e.razon_social "
            "FROM ordenes_venta ov "
            "LEFT JOIN clientes c ON ov.cliente_cedula = c.cedula "
            "LEFT JOIN empresas e ON e.rif = c.cedula "
            "WHERE 1=1"
        )
        params = []
        if start_date:
            sql += " AND DATE(ov.fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(ov.fecha) <= %s"
            params.append(end_date)
        if status:
            sql += " AND ov.estado = %s"
            params.append(status)
        sql += " ORDER BY ov.fecha DESC"

        orders = self.fetch_all("transalca", sql, tuple(params) if params else None)

        for order in orders:
            if order.get('tipo_cliente') == 'empresa':
                order['cliente'] = order.get('razon_social') or order.get('nombre') or 'N/A'
            else:
                order['cliente'] = f"{order.get('nombre', '')} {order.get('apellido', '')}".strip() or 'N/A'
            order['fecha'] = order['fecha'].isoformat() if hasattr(order['fecha'], 'isoformat') else order['fecha']
        return orders

    def get_payments_history(self, start_date=None, end_date=None, status=None):
        sql = (
            "SELECT cp.id, ov.cliente_cedula, cp.orden_venta_id as orden_id, CONCAT('IMG-', cp.id) as referencia, "
            "ov.total as monto, 'USD' as moneda, mp.nombre as metodo, cp.fecha, cp.estado, "
            "c.nombre, c.apellido, c.tipo_cliente, e.razon_social "
            "FROM comprobantes_pago cp "
            "INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id "
            "LEFT JOIN metodos_pago mp ON mp.id = ov.metodo_pago_id "
            "LEFT JOIN clientes c ON ov.cliente_cedula = c.cedula "
            "LEFT JOIN empresas e ON e.rif = c.cedula "
            "WHERE 1=1"
        )
        params = []
        if start_date:
            sql += " AND DATE(cp.fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(cp.fecha) <= %s"
            params.append(end_date)
        if status:
            sql += " AND cp.estado = %s"
            params.append(status)
        sql += " ORDER BY cp.fecha DESC"

        payments = self.fetch_all("transalca", sql, tuple(params) if params else None)
        for p in payments:
            if p.get('tipo_cliente') == 'empresa':
                p['cliente'] = p.get('razon_social') or p.get('nombre') or 'N/A'
            else:
                p['cliente'] = f"{p.get('nombre', '')} {p.get('apellido', '')}".strip() or 'N/A'
            p['fecha'] = p['fecha'].isoformat() if hasattr(p['fecha'], 'isoformat') else p['fecha']
        return payments

    def get_inventory_kardex(self, start_date=None, end_date=None):
        sql = "SELECT i.producto_codigo as id, i.producto_codigo, 'Stock actual' as tipo, i.stock as cantidad, 'Ajuste sistemico' as motivo, i.updated_at as fecha, p.nombre as producto, p.codigo FROM stock i INNER JOIN productos p ON i.producto_codigo = p.codigo WHERE 1=1"
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
        sql = (
            "SELECT sm.mecanico_cedula, sm.estado as asignacion_estado, sm.fecha, s.precio as subtotal, "
            "CONCAT(m.nombre, ' ', m.apellido) as mecanico_nombre "
            "FROM servicio_mecanico sm "
            "INNER JOIN servicios s ON sm.servicio_id = s.id "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula "
            "WHERE sm.mecanico_cedula IS NOT NULL"
        )
        params = []
        if start_date:
            sql += " AND DATE(sm.fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(sm.fecha) <= %s"
            params.append(end_date)

        records = self.fetch_all("transalca", sql, tuple(params) if params else None)

        mecanicos_stats = {}
        for r in records:
            mid = r['mecanico_cedula']
            if mid not in mecanicos_stats:
                mecanico_nombre = r.get('mecanico_nombre') or 'Desconocido'
                mecanicos_stats[mid] = {
                    "mecanico_nombre": mecanico_nombre,
                    "total_asignados": 0,
                    "total_completados": 0,
                    "ingreso_generado": 0.0
                }
            mecanicos_stats[mid]["total_asignados"] += 1
            if r['asignacion_estado'] == 'completado':
                mecanicos_stats[mid]["total_completados"] += 1
                mecanicos_stats[mid]["ingreso_generado"] += float(r['subtotal'])

        return list(mecanicos_stats.values())

    def get_bitacora_audit(self, start_date=None, end_date=None, modulo=None):
        sql = (
            "SELECT b.id, b.usuario_id, b.accion, b.modulo, b.descripcion, b.ip, b.fecha, "
            "u.email as usuario "
            "FROM bitacora b "
            "LEFT JOIN usuarios u ON b.usuario_id = u.id "
            "WHERE 1=1"
        )
        params = []
        if start_date:
            sql += " AND DATE(b.fecha) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(b.fecha) <= %s"
            params.append(end_date)
        if modulo:
            sql += " AND b.modulo = %s"
            params.append(modulo)
        sql += " ORDER BY b.fecha DESC LIMIT 500"

        logs = self.fetch_all("mantenimiento", sql, tuple(params) if params else None)
        for l in logs:
            l['usuario'] = l.get('usuario') or 'Sistema'
            l['fecha'] = l['fecha'].isoformat() if hasattr(l['fecha'], 'isoformat') else l['fecha']
        return logs
