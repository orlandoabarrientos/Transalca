from model.connection import Connection
from datetime import datetime, timedelta


class ReportModel(Connection):
    def __init__(self):
        super().__init__()

    def _client_name(self, cedula):
        client = self.fetch_one(
            "transalca",
            "SELECT c.nombre_cliente AS nombre, '' AS apellido, c.tipo_cliente, c.nombre_cliente AS razon_social "
            "FROM cliente c "
            "WHERE c.identificador_cliente = %s",
            (cedula,))
        if not client:
            return 'N/A'
        if client.get('tipo_cliente') == 'juridica':
            return client.get('razon_social') or client.get('nombre') or 'N/A'
        return f"{client.get('nombre', '')} {client.get('apellido', '')}".strip() or 'N/A'

    def _get_dashboard_stats(self):
        total_products = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM productos WHERE estado = 1")
        total_categories = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM categorias WHERE estado = 1")
        total_clients = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM cliente WHERE tipo_cliente = 'natural' AND estado = 1")
        total_employees = self.fetch_one("mantenimiento", "SELECT COUNT(*) as total FROM usuarios WHERE tipo IN ('admin','vendedor','mecanico','soporte','empleado') AND estado = 1")
        pending_payments = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM comprobantes_pago WHERE estado = 'pendiente'")
        total_sales = self.fetch_one("transalca", "SELECT COALESCE(SUM(total_orden_venta), 0) as total FROM ordenes_venta WHERE estado = 'aprobada'")
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

    def _get_recent_orders(self, limit=10):
        orders = self.fetch_all("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "ORDER BY ov.id_orden_venta DESC LIMIT %s", (limit,))
        for order in orders:
            order['cliente_nombre'] = self._client_name(order['cliente_cedula'])
            order['fecha'] = order['fecha'].isoformat() if hasattr(order['fecha'], 'isoformat') else order['fecha']
        return orders

    def _get_sales_history(self, start_date=None, end_date=None, status=None, payment_method=None, client_type=None, min_amount=None, max_amount=None, search=None, sucursal_id=None):
        sql = (
            "SELECT ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, ov.estado, "
            "c.nombre_cliente AS nombre, '' AS apellido, c.tipo_cliente, c.nombre_cliente AS razon_social, "
            "mp.nombre_metodo_pago AS metodo_pago, mp.id_metodo_pago "
            "FROM ordenes_venta ov "
            "LEFT JOIN cliente c ON ov.cliente_cedula = c.identificador_cliente "
            "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE 1=1"
        )
        params = []
        if start_date:
            sql += " AND DATE(ov.fecha_orden_venta) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(ov.fecha_orden_venta) <= %s"
            params.append(end_date)
        if status:
            sql += " AND ov.estado = %s"
            params.append(status)
        if payment_method:
            sql += " AND ov.metodo_pago_id = %s"
            params.append(payment_method)
        if sucursal_id and str(sucursal_id).strip() not in ('', '0', 'null', 'undefined'):
            suc_val = str(sucursal_id).strip()
            sql += " AND (ov.sucursal_id = %s OR (ov.sucursal_id IS NULL AND EXISTS (SELECT 1 FROM detalle_orden_venta_productos dov INNER JOIN stock st ON st.producto_codigo = dov.producto_codigo WHERE dov.orden_id = ov.id_orden_venta AND st.sucursal_id = %s)))"
            params.extend([suc_val, suc_val])
        if client_type:
            sql += " AND c.tipo_cliente = %s"
            params.append(client_type)
        if min_amount is not None and str(min_amount).strip() != '':
            sql += " AND ov.total_orden_venta >= %s"
            params.append(float(min_amount))
        if max_amount is not None and str(max_amount).strip() != '':
            sql += " AND ov.total_orden_venta <= %s"
            params.append(float(max_amount))
        if search:
            sql += " AND (c.nombre_cliente LIKE %s OR ov.cliente_cedula LIKE %s OR CAST(ov.id_orden_venta AS CHAR) LIKE %s)"
            like_val = f"%{search.strip()}%"
            params.extend([like_val, like_val, like_val])
        sql += " ORDER BY ov.fecha_orden_venta DESC"

        orders = self.fetch_all("transalca", sql, tuple(params) if params else None)

        for order in orders:
            if order.get('tipo_cliente') == 'juridica':
                order['cliente'] = order.get('razon_social') or order.get('nombre') or 'N/A'
            else:
                order['cliente'] = f"{order.get('nombre', '')} {order.get('apellido', '')}".strip() or 'N/A'
            order['fecha'] = order['fecha'].isoformat() if hasattr(order['fecha'], 'isoformat') else order['fecha']
        return orders

    def _get_payments_history(self, start_date=None, end_date=None, status=None, payment_method=None, moneda=None, client_type=None, search=None):
        sql = "SELECT * FROM vw_reporte_pagos WHERE 1=1"
        params = []
        if start_date:
            sql += " AND DATE(fecha_ts) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(fecha_ts) <= %s"
            params.append(end_date)
        if status:
            sql += " AND estado = %s"
            params.append(status)
        if payment_method:
            sql += " AND metodo = %s"
            params.append(payment_method)
        if moneda:
            sql += " AND moneda = %s"
            params.append(moneda)
        if client_type:
            sql += " AND tipo_cliente = %s"
            params.append(client_type)
        if search:
            sql += " AND (referencia LIKE %s OR nombre LIKE %s OR apellido LIKE %s OR razon_social LIKE %s OR CAST(orden_id AS CHAR) LIKE %s)"
            like_val = f"%{search.strip()}%"
            params.extend([like_val, like_val, like_val, like_val, like_val])
        sql += " ORDER BY fecha_ts DESC"

        payments = self.fetch_all("transalca", sql, tuple(params) if params else None)
        for p in payments:
            if p.get('tipo_cliente') == 'juridica':
                p['cliente'] = p.get('razon_social') or p.get('nombre') or 'N/A'
            else:
                p['cliente'] = f"{p.get('nombre', '')} {p.get('apellido', '')}".strip() or 'N/A'
            p['fecha'] = p['fecha'].isoformat() if hasattr(p['fecha'], 'isoformat') else p['fecha']
        return payments

    def _get_inventory_kardex(self, start_date=None, end_date=None, category=None, brand=None, stock_status=None, search=None, sucursal_id=None):
        sql = (
            "SELECT i.producto_codigo as id, i.producto_codigo, 'Stock actual' as tipo, "
            "i.stock as cantidad, 'Ajuste sistemico' as motivo, i.updated_at as fecha, "
            "p.nombre_producto as producto, p.codigo, p.categoria, p.marca, i.stock_minimo "
            "FROM stock i "
            "INNER JOIN productos p ON i.producto_codigo = p.codigo "
            "WHERE 1=1"
        )
        params = []
        if start_date:
            sql += " AND DATE(i.updated_at) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(i.updated_at) <= %s"
            params.append(end_date)
        if sucursal_id and str(sucursal_id).strip() not in ('', '0', 'null', 'undefined'):
            sql += " AND i.sucursal_id = %s"
            params.append(str(sucursal_id).strip())
        if category:
            sql += " AND p.categoria = %s"
            params.append(category)
        if brand:
            sql += " AND p.marca = %s"
            params.append(brand)
        if stock_status == 'low_stock':
            sql += " AND i.stock <= i.stock_minimo AND i.stock > 0"
        elif stock_status == 'out_of_stock':
            sql += " AND i.stock = 0"
        elif stock_status == 'in_stock':
            sql += " AND i.stock > 0"
        if search:
            sql += " AND (p.nombre_producto LIKE %s OR p.codigo LIKE %s)"
            like_val = f"%{search.strip()}%"
            params.extend([like_val, like_val])
        sql += " ORDER BY i.updated_at DESC"

        moves = self.fetch_all("transalca", sql, tuple(params) if params else None)
        for m in moves:
            m['fecha'] = m['fecha'].isoformat() if hasattr(m['fecha'], 'isoformat') else m['fecha']
        return moves

    def _get_mechanics_performance(self, start_date=None, end_date=None, mechanic_cedula=None, status=None):
        sql = (
            "SELECT sm.mecanico_cedula, sm.estado_servicio as asignacion_estado, sm.fecha_servicio AS fecha, s.precio_servicio as subtotal, "
            "CONCAT(m.nombre_mecanico, ' ', m.apellido_mecanico) as mecanico_nombre "
            "FROM servicio_mecanico sm "
            "INNER JOIN servicios s ON sm.servicio_id = s.id_servicio "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
            "WHERE sm.mecanico_cedula IS NOT NULL"
        )
        params = []
        if start_date:
            sql += " AND DATE(sm.fecha_servicio) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(sm.fecha_servicio) <= %s"
            params.append(end_date)
        if mechanic_cedula:
            sql += " AND sm.mecanico_cedula = %s"
            params.append(mechanic_cedula)
        if status:
            sql += " AND sm.estado_servicio = %s"
            params.append(status)

        records = self.fetch_all("transalca", sql, tuple(params) if params else None)

        mecanicos_stats = {}
        for r in records:
            mid = r['mecanico_cedula']
            if mid not in mecanicos_stats:
                mecanico_nombre = r.get('mecanico_nombre') or 'Desconocido'
                mecanicos_stats[mid] = {
                    "mecanico_nombre": mecanico_nombre,
                    "mecanico_cedula": mid,
                    "total_asignados": 0,
                    "total_completados": 0,
                    "ingreso_generado": 0.0
                }
            mecanicos_stats[mid]["total_asignados"] += 1
            if r['asignacion_estado'] == 'completado':
                mecanicos_stats[mid]["total_completados"] += 1
                mecanicos_stats[mid]["ingreso_generado"] += float(r['subtotal'])

        return list(mecanicos_stats.values())

    def _get_bitacora_audit(self, start_date=None, end_date=None, modulo=None, accion_tipo=None, search=None):
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
        if accion_tipo:
            sql += " AND b.accion LIKE %s"
            params.append(f"%{accion_tipo.strip()}%")
        if search:
            sql += " AND (b.descripcion LIKE %s OR u.email LIKE %s OR b.ip LIKE %s)"
            like_val = f"%{search.strip()}%"
            params.extend([like_val, like_val, like_val])
        sql += " ORDER BY b.fecha DESC LIMIT 500"

        logs = self.fetch_all("mantenimiento", sql, tuple(params) if params else None)
        for l in logs:
            l['usuario'] = l.get('usuario') or 'Sistema'
            l['fecha'] = l['fecha'].isoformat() if hasattr(l['fecha'], 'isoformat') else l['fecha']
        return logs

    def _get_top_products_report(self, start_date=None, end_date=None, category=None, brand=None, status=None, limit=None, search=None, stock_status=None, order_by=None, sucursal_id=None):
        sql = (
            "SELECT "
            "p.codigo, "
            "p.nombre_producto, "
            "COALESCE(p.categoria, 'Sin categoría') as categoria, "
            "COALESCE(p.marca, 'Sin marca') as marca, "
            "COALESCE(p.precio_producto, 0) as precio_actual, "
            "COALESCE(SUM(d.cantidad_detalle_orden_venta_producto), 0) as total_vendido, "
            "COALESCE(SUM(d.cantidad_detalle_orden_venta_producto * d.precio_unitario_producto), 0) as total_recaudado, "
            "COUNT(DISTINCT ov.id_orden_venta) as total_ordenes "
            "FROM detalle_orden_venta_productos d "
            "INNER JOIN ordenes_venta ov ON d.orden_id = ov.id_orden_venta "
            "INNER JOIN productos p ON d.producto_codigo = p.codigo "
            "WHERE 1=1"
        )
        params = []
        if start_date:
            sql += " AND DATE(ov.fecha_orden_venta) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(ov.fecha_orden_venta) <= %s"
            params.append(end_date)
        if status:
            sql += " AND ov.estado = %s"
            params.append(status)
        else:
            sql += " AND ov.estado IN ('aprobada', 'completada')"
        if sucursal_id and str(sucursal_id).strip() not in ('', '0', 'null', 'undefined'):
            suc_val = str(sucursal_id).strip()
            sql += " AND (ov.sucursal_id = %s OR (ov.sucursal_id IS NULL AND EXISTS (SELECT 1 FROM stock st WHERE st.producto_codigo = p.codigo AND st.sucursal_id = %s)))"
            params.extend([suc_val, suc_val])
        if category:
            sql += " AND p.categoria = %s"
            params.append(category)
        if brand:
            sql += " AND p.marca = %s"
            params.append(brand)
        if search:
            sql += " AND (p.nombre_producto LIKE %s OR p.codigo LIKE %s)"
            like_val = f"%{search.strip()}%"
            params.extend([like_val, like_val])

        sql += " GROUP BY p.codigo, p.nombre_producto, p.categoria, p.marca, p.precio_producto "

        if order_by == 'revenue':
            sql += " ORDER BY total_recaudado DESC, total_vendido DESC"
        else:
            sql += " ORDER BY total_vendido DESC, total_recaudado DESC"

        if limit and str(limit).isdigit() and int(limit) > 0:
            sql += f" LIMIT {int(limit)}"

        records = self.fetch_all("transalca", sql, tuple(params) if params else None)
        for idx, r in enumerate(records, 1):
            r['ranking'] = idx
            r['total_vendido'] = int(r.get('total_vendido') or 0)
            r['total_recaudado'] = float(r.get('total_recaudado') or 0.0)
            r['total_ordenes'] = int(r.get('total_ordenes') or 0)
            r['precio_actual'] = float(r.get('precio_actual') or 0.0)
        return records

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_dashboard_stats": self._get_dashboard_stats,
            "get_recent_orders": self._get_recent_orders,
            "get_sales_history": self._get_sales_history,
            "get_payments_history": self._get_payments_history,
            "get_inventory_kardex": self._get_inventory_kardex,
            "get_mechanics_performance": self._get_mechanics_performance,
            "get_bitacora_audit": self._get_bitacora_audit,
            "get_top_products_report": self._get_top_products_report,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
