from model.connection import Connection
class InventoryModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, p.precio, p.categoria as categoria_nombre, s.nombre as sucursal_nombre FROM stock i INNER JOIN productos p ON i.producto_codigo = p.codigo LEFT JOIN sucursales s ON i.sucursal_id = s.id ORDER BY p.nombre")

    def get_by_sucursal(self, sucursal_id):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, p.precio, p.categoria as categoria_nombre, s.nombre as sucursal_nombre FROM stock i INNER JOIN productos p ON i.producto_codigo = p.codigo LEFT JOIN sucursales s ON i.sucursal_id = s.id WHERE i.sucursal_id = %s ORDER BY p.nombre", (sucursal_id,))

    def get_paginated(self, page, per_page, sucursal_id=None, q=None):
        where = []
        params = []
        if sucursal_id:
            where.append("i.sucursal_id = %s")
            params.append(sucursal_id)
        if q:
            like = f"%{q}%"
            where.append("(p.nombre LIKE %s OR p.codigo LIKE %s OR p.categoria LIKE %s OR s.nombre LIKE %s)")
            params.extend([like, like, like, like])

        from_sql = (
            "FROM stock i INNER JOIN productos p ON i.producto_codigo = p.codigo "
            "LEFT JOIN sucursales s ON i.sucursal_id = s.id"
        )
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""
        total_row = self.fetch_one("transalca", f"SELECT COUNT(*) as total {from_sql}{where_sql}", tuple(params))
        total = total_row['total'] if total_row else 0
        pages = (total + per_page - 1) // per_page if total else 0
        if pages and page > pages:
            page = pages
        offset = (page - 1) * per_page
        data = self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, p.precio, p.categoria as categoria_nombre, s.nombre as sucursal_nombre "
            f"{from_sql}{where_sql} ORDER BY p.nombre LIMIT %s OFFSET %s",
            tuple(params + [per_page, offset]))
        return {
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

    def get_low_stock(self):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, s.nombre as sucursal_nombre FROM stock i INNER JOIN productos p ON i.producto_codigo = p.codigo LEFT JOIN sucursales s ON i.sucursal_id = s.id WHERE i.stock <= i.stock_minimo ORDER BY i.stock ASC")

    def update_stock(self, producto_codigo, stock, sucursal_id=None):
        if sucursal_id:
            existing = self.fetch_one("transalca",
                "SELECT producto_codigo FROM stock WHERE producto_codigo = %s AND sucursal_id = %s",
                (producto_codigo, sucursal_id))
            if existing:
                return self.update("transalca",
                    "UPDATE stock SET stock = %s WHERE producto_codigo = %s AND sucursal_id = %s",
                    (stock, producto_codigo, sucursal_id))
            else:
                return self.insert("transalca",
                    "INSERT INTO stock (producto_codigo, sucursal_id, stock) VALUES (%s, %s, %s)",
                    (producto_codigo, sucursal_id, stock))
        return self.update("transalca",
            "UPDATE stock SET stock = %s WHERE producto_codigo = %s", (stock, producto_codigo))

    def update_min_stock(self, producto_codigo, stock_minimo, sucursal_id=None):
        if sucursal_id:
            return self.update("transalca",
                "UPDATE stock SET stock_minimo = %s WHERE producto_codigo = %s AND sucursal_id = %s",
                (stock_minimo, producto_codigo, sucursal_id))
        return self.update("transalca",
            "UPDATE stock SET stock_minimo = %s WHERE producto_codigo = %s",
            (stock_minimo, producto_codigo))

    def get_sales_orders(self):
        orders = self.fetch_all("transalca",
            "SELECT ov.*, mp.nombre AS metodo_pago, mp.nombre AS metodo_pago_nombre, s.nombre as sucursal_nombre "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id = ov.metodo_pago_id "
            "LEFT JOIN sucursales s ON ov.sucursal_id = s.id ORDER BY ov.fecha DESC")
        for order in orders:
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}" if client else 'N/A'
        return orders

    def get_sales_order_detail(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT ov.*, mp.nombre AS metodo_pago, mp.nombre AS metodo_pago_nombre, s.nombre as sucursal_nombre "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id = ov.metodo_pago_id "
            "LEFT JOIN sucursales s ON ov.sucursal_id = s.id WHERE ov.id = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE sv.nombre END as item_nombre "
                "FROM ((SELECT id, orden_id, producto_codigo, 0 AS servicio_id, 'producto' AS tipo, cantidad, precio_unitario, subtotal FROM detalle_orden_venta_productos) "
                "UNION ALL "
                "(SELECT id, orden_id, 'SIN_PRODUCTO' AS producto_codigo, servicio_id, 'servicio' AS tipo, cantidad, precio_unitario, subtotal FROM detalle_orden_venta_servicios)) d "
                "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
                "LEFT JOIN servicios sv ON d.servicio_id = sv.id WHERE d.orden_id = %s",
                (order_id,))
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            if client:
                order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}"
                order['cliente_email'] = client['email']
                order['cliente_telefono'] = client['telefono']
        return order
