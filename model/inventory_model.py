from model.connection import Connection
from model.notification_model import NotificationModel
from model.order_model import DETAIL_UNION

INV_SELECT = (
    "SELECT i.*, p.nombre_producto as producto_nombre, p.codigo, p.precio_producto AS precio, "
    "p.categoria as categoria_nombre, s.nombre_sucursal as sucursal_nombre, i.ubicacion_stock AS ubicacion "
    "FROM stock i INNER JOIN productos p ON i.producto_codigo = p.codigo "
    "LEFT JOIN sucursales s ON i.sucursal_id = s.id_sucursal"
)


class InventoryModel(Connection):
    def __init__(self):
        super().__init__()

    def _get_all(self):
        return self.fetch_all("transalca", INV_SELECT + " ORDER BY p.nombre_producto")

    def _get_by_sucursal(self, sucursal_id):
        return self.fetch_all("transalca",
            INV_SELECT + " WHERE i.sucursal_id = %s ORDER BY p.nombre_producto", (sucursal_id,))

    def _get_paginated(self, page, per_page, sucursal_id=None, q=None):
        where = []
        params = []
        if sucursal_id:
            where.append("i.sucursal_id = %s")
            params.append(sucursal_id)
        if q:
            like = f"%{q}%"
            where.append("(p.nombre_producto LIKE %s OR p.codigo LIKE %s OR p.categoria LIKE %s OR s.nombre_sucursal LIKE %s)")
            params.extend([like, like, like, like])

        from_sql = (
            "FROM stock i INNER JOIN productos p ON i.producto_codigo = p.codigo "
            "LEFT JOIN sucursales s ON i.sucursal_id = s.id_sucursal"
        )
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""
        total_row = self.fetch_one("transalca", f"SELECT COUNT(*) as total {from_sql}{where_sql}", tuple(params))
        total = total_row['total'] if total_row else 0
        pages = (total + per_page - 1) // per_page if total else 0
        if pages and page > pages:
            page = pages
        offset = (page - 1) * per_page
        data = self.fetch_all("transalca",
            "SELECT i.*, p.nombre_producto as producto_nombre, p.codigo, p.precio_producto AS precio, "
            "p.categoria as categoria_nombre, s.nombre_sucursal as sucursal_nombre, i.ubicacion_stock AS ubicacion "
            f"{from_sql}{where_sql} ORDER BY p.nombre_producto LIMIT %s OFFSET %s",
            tuple(params + [per_page, offset]))
        return {
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

    def _get_low_stock_threshold(self):
        row = self.fetch_one("transalca", "SELECT valor FROM configuracion WHERE clave = 'umbral_stock_bajo'")
        try:
            return int(row['valor']) if row else 5
        except (TypeError, ValueError):
            return 5

    def _get_low_stock(self, producto_codigo=None):
        umbral = self._get_low_stock_threshold()
        sql = INV_SELECT + " WHERE i.stock <= GREATEST(COALESCE(i.stock_minimo, 0), %s)"
        params = [umbral]
        if producto_codigo:
            sql += " AND i.producto_codigo = %s"
            params.append(producto_codigo)
        return self.fetch_all("transalca", sql + " ORDER BY i.stock ASC", tuple(params))

    def _check_low_stock_and_notify(self, producto_codigo=None):
        """Genera notificaciones de stock bajo (umbral configurable, sin duplicados en 24h)."""
        notifier = NotificationModel()
        created = 0
        for item in self._get_low_stock(producto_codigo):
            umbral = max(int(item.get('stock_minimo') or 0), self._get_low_stock_threshold())
            created += notifier.ejecutar("notify_stock_low", 
                item['codigo'], item.get('producto_nombre') or item['codigo'],
                int(item.get('stock') or 0), umbral, item.get('sucursal_nombre'))
        return created

    def _update_stock(self, producto_codigo, stock, sucursal_id=None):
        if sucursal_id:
            existing = self.fetch_one("transalca",
                "SELECT producto_codigo FROM stock WHERE producto_codigo = %s AND sucursal_id = %s",
                (producto_codigo, sucursal_id))
            if existing:
                result = self.update("transalca",
                    "UPDATE stock SET stock = %s WHERE producto_codigo = %s AND sucursal_id = %s",
                    (stock, producto_codigo, sucursal_id))
            else:
                result = self.insert("transalca",
                    "INSERT INTO stock (producto_codigo, sucursal_id, stock) VALUES (%s, %s, %s)",
                    (producto_codigo, sucursal_id, stock))
        else:
            result = self.update("transalca",
                "UPDATE stock SET stock = %s WHERE producto_codigo = %s", (stock, producto_codigo))
        try:
            self._check_low_stock_and_notify(producto_codigo)
        except Exception:
            pass
        return result

    def _update_min_stock(self, producto_codigo, stock_minimo, sucursal_id=None):
        if sucursal_id:
            return self.update("transalca",
                "UPDATE stock SET stock_minimo = %s WHERE producto_codigo = %s AND sucursal_id = %s",
                (stock_minimo, producto_codigo, sucursal_id))
        return self.update("transalca",
            "UPDATE stock SET stock_minimo = %s WHERE producto_codigo = %s",
            (stock_minimo, producto_codigo))

    def _client_name(self, cedula):
        client = self.fetch_one("mantenimiento",
            "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (cedula,))
        if client:
            return f"{client['nombre']} {client['apellido']}"
        row = self.fetch_one("transalca",
            "SELECT nombre_cliente FROM cliente WHERE identificador_cliente = %s", (cedula,))
        return row['nombre_cliente'] if row else 'N/A'

    def _get_sales_orders(self):
        orders = self.fetch_all("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, "
            "mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda, s.nombre_sucursal as sucursal_nombre "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "LEFT JOIN sucursales s ON ov.sucursal_id = s.id_sucursal ORDER BY ov.fecha_orden_venta DESC")
        for order in orders:
            order['cliente_nombre'] = self._client_name(order['cliente_cedula'])
        return orders

    def _get_sales_order_detail(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, "
            "mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda, s.nombre_sucursal as sucursal_nombre "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "LEFT JOIN sucursales s ON ov.sucursal_id = s.id_sucursal WHERE ov.id_orden_venta = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre_producto ELSE sv.nombre_servicio END as item_nombre "
                "FROM " + DETAIL_UNION + " "
                "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
                "LEFT JOIN servicios sv ON d.servicio_id = sv.id_servicio WHERE d.orden_id = %s",
                (order_id,))
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            if client:
                order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}"
                order['cliente_email'] = client['email']
                order['cliente_telefono'] = client['telefono']
        return order

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_sucursal": self._get_by_sucursal,
            "get_paginated": self._get_paginated,
            "get_low_stock_threshold": self._get_low_stock_threshold,
            "get_low_stock": self._get_low_stock,
            "check_low_stock_and_notify": self._check_low_stock_and_notify,
            "update_stock": self._update_stock,
            "update_min_stock": self._update_min_stock,
            "get_sales_orders": self._get_sales_orders,
            "get_sales_order_detail": self._get_sales_order_detail,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
