from model.connection import Connection


class InventoryModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, p.precio, p.categoria as categoria_nombre, s.nombre as sucursal_nombre FROM inventario i INNER JOIN productos p ON i.producto_codigo = p.codigo LEFT JOIN sucursales s ON i.sucursal_id = s.id ORDER BY p.nombre")

    def get_by_sucursal(self, sucursal_id):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, p.precio, p.categoria as categoria_nombre, s.nombre as sucursal_nombre FROM inventario i INNER JOIN productos p ON i.producto_codigo = p.codigo LEFT JOIN sucursales s ON i.sucursal_id = s.id WHERE i.sucursal_id = %s ORDER BY p.nombre", (sucursal_id,))

    def get_low_stock(self):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, s.nombre as sucursal_nombre FROM inventario i INNER JOIN productos p ON i.producto_codigo = p.codigo LEFT JOIN sucursales s ON i.sucursal_id = s.id WHERE i.stock <= i.stock_minimo ORDER BY i.stock ASC")

    def update_stock(self, producto_codigo, stock, sucursal_id=None):
        if sucursal_id:
            existing = self.fetch_one("transalca",
                "SELECT producto_codigo FROM inventario WHERE producto_codigo = %s AND sucursal_id = %s",
                (producto_codigo, sucursal_id))
            if existing:
                return self.update("transalca",
                    "UPDATE inventario SET stock = %s WHERE producto_codigo = %s AND sucursal_id = %s",
                    (stock, producto_codigo, sucursal_id))
            else:
                return self.insert("transalca",
                    "INSERT INTO inventario (producto_codigo, sucursal_id, stock) VALUES (%s, %s, %s)",
                    (producto_codigo, sucursal_id, stock))
        # Without sucursal_id, update all entries for this product
        return self.update("transalca",
            "UPDATE inventario SET stock = %s WHERE producto_codigo = %s", (stock, producto_codigo))

    def update_min_stock(self, producto_codigo, stock_minimo, sucursal_id=None):
        if sucursal_id:
            return self.update("transalca",
                "UPDATE inventario SET stock_minimo = %s WHERE producto_codigo = %s AND sucursal_id = %s",
                (stock_minimo, producto_codigo, sucursal_id))
        return self.update("transalca",
            "UPDATE inventario SET stock_minimo = %s WHERE producto_codigo = %s",
            (stock_minimo, producto_codigo))

    def create_purchase_order(self, data, details):
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ordenes_compra (proveedor_rif, usuario_cedula, sucursal_id, total, observaciones) VALUES (%s, %s, %s, %s, %s)",
                (data['proveedor_rif'], data['usuario_cedula'], data.get('sucursal_id'),
                 data['total'], data.get('observaciones', '')))
            order_id = cursor.lastrowid
            for item in details:
                subtotal = int(item['cantidad']) * float(item['precio_unitario'])
                cursor.execute(
                    "INSERT INTO detalle_orden_compra (orden_id, producto_codigo, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (order_id, item['producto_codigo'], item['cantidad'], item['precio_unitario'], subtotal))
            cursor.execute(
                "UPDATE ordenes_compra SET total = (SELECT SUM(subtotal) FROM detalle_orden_compra WHERE orden_id = %s) WHERE id = %s",
                (order_id, order_id))
            conn.commit()
            return order_id
        except Exception:
            conn.rollback()
            return None

    def get_purchase_orders(self):
        orders = self.fetch_all("transalca",
            "SELECT oc.*, p.nombre as proveedor_nombre, s.nombre as sucursal_nombre FROM ordenes_compra oc INNER JOIN proveedores p ON oc.proveedor_rif = p.rif LEFT JOIN sucursales s ON oc.sucursal_id = s.id ORDER BY oc.fecha DESC")
        for order in orders:
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (order['usuario_cedula'],))
            order['usuario_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'N/A'
        return orders

    def get_purchase_order_detail(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT oc.*, p.nombre as proveedor_nombre, s.nombre as sucursal_nombre FROM ordenes_compra oc INNER JOIN proveedores p ON oc.proveedor_rif = p.rif LEFT JOIN sucursales s ON oc.sucursal_id = s.id WHERE oc.id = %s",
            (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, p.nombre as producto_nombre, p.codigo FROM detalle_orden_compra d INNER JOIN productos p ON d.producto_codigo = p.codigo WHERE d.orden_id = %s",
                (order_id,))
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (order['usuario_cedula'],))
            order['usuario_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'N/A'
        return order

    def update_purchase_order_status(self, order_id, estado):
        return self.update("transalca",
            "UPDATE ordenes_compra SET estado = %s WHERE id = %s", (estado, order_id))

    def get_sales_orders(self):
        orders = self.fetch_all("transalca",
            "SELECT ov.*, s.nombre as sucursal_nombre FROM ordenes_venta ov LEFT JOIN sucursales s ON ov.sucursal_id = s.id ORDER BY ov.fecha DESC")
        for order in orders:
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}" if client else 'N/A'
        return orders

    def get_sales_order_detail(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT ov.*, s.nombre as sucursal_nombre FROM ordenes_venta ov LEFT JOIN sucursales s ON ov.sucursal_id = s.id WHERE ov.id = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE sv.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_codigo = p.codigo LEFT JOIN servicios sv ON d.servicio_id = sv.id WHERE d.orden_id = %s",
                (order_id,))
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            if client:
                order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}"
                order['cliente_email'] = client['email']
                order['cliente_telefono'] = client['telefono']
        return order
