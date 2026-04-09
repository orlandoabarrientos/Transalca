from model.connection import Connection


class InventoryModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, p.precio, c.nombre as categoria_nombre, s.nombre as sucursal_nombre FROM inventario i INNER JOIN productos p ON i.producto_id = p.id LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN sucursales s ON i.sucursal_id = s.id ORDER BY p.nombre")

    def get_by_sucursal(self, sucursal_id):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, p.precio, c.nombre as categoria_nombre, s.nombre as sucursal_nombre FROM inventario i INNER JOIN productos p ON i.producto_id = p.id LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN sucursales s ON i.sucursal_id = s.id WHERE i.sucursal_id = %s ORDER BY p.nombre", (sucursal_id,))

    def get_low_stock(self):
        return self.fetch_all("transalca",
            "SELECT i.*, p.nombre as producto_nombre, p.codigo, s.nombre as sucursal_nombre FROM inventario i INNER JOIN productos p ON i.producto_id = p.id LEFT JOIN sucursales s ON i.sucursal_id = s.id WHERE i.stock <= i.stock_minimo ORDER BY i.stock ASC")

    def update_stock(self, producto_id, stock, sucursal_id=None):
        if sucursal_id:
            existing = self.fetch_one("transalca", "SELECT id FROM inventario WHERE producto_id = %s AND sucursal_id = %s", (producto_id, sucursal_id))
            if existing:
                return self.update("transalca", "UPDATE inventario SET stock = %s WHERE producto_id = %s AND sucursal_id = %s", (stock, producto_id, sucursal_id))
            else:
                return self.insert("transalca", "INSERT INTO inventario (producto_id, sucursal_id, stock) VALUES (%s, %s, %s)", (producto_id, sucursal_id, stock))
        return self.update("transalca", "UPDATE inventario SET stock = %s WHERE producto_id = %s", (stock, producto_id))

    def update_min_stock(self, producto_id, stock_minimo):
        return self.update("transalca", "UPDATE inventario SET stock_minimo = %s WHERE producto_id = %s", (stock_minimo, producto_id))

    def create_purchase_order(self, data, details):
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ordenes_compra (proveedor_id, usuario_id, sucursal_id, total, observaciones) VALUES (%s, %s, %s, %s, %s)",
                (data['proveedor_id'], data['usuario_id'], data.get('sucursal_id'), data['total'], data.get('observaciones', '')))
            order_id = cursor.lastrowid
            for item in details:
                subtotal = int(item['cantidad']) * float(item['precio_unitario'])
                cursor.execute(
                    "INSERT INTO detalle_orden_compra (orden_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (order_id, item['producto_id'], item['cantidad'], item['precio_unitario'], subtotal))
            cursor.execute("UPDATE ordenes_compra SET total = (SELECT SUM(subtotal) FROM detalle_orden_compra WHERE orden_id = %s) WHERE id = %s", (order_id, order_id))
            conn.commit()
            return order_id
        except Exception:
            conn.rollback()
            return None

    def get_purchase_orders(self):
        orders = self.fetch_all("transalca",
            "SELECT oc.*, p.nombre as proveedor_nombre, s.nombre as sucursal_nombre FROM ordenes_compra oc INNER JOIN proveedores p ON oc.proveedor_id = p.id LEFT JOIN sucursales s ON oc.sucursal_id = s.id ORDER BY oc.fecha DESC")
        for order in orders:
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE id = %s", (order['usuario_id'],))
            order['usuario_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'N/A'
        return orders

    def get_purchase_order_detail(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT oc.*, p.nombre as proveedor_nombre, s.nombre as sucursal_nombre FROM ordenes_compra oc INNER JOIN proveedores p ON oc.proveedor_id = p.id LEFT JOIN sucursales s ON oc.sucursal_id = s.id WHERE oc.id = %s",
            (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, p.nombre as producto_nombre, p.codigo FROM detalle_orden_compra d INNER JOIN productos p ON d.producto_id = p.id WHERE d.orden_id = %s",
                (order_id,))
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE id = %s", (order['usuario_id'],))
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
                "SELECT nombre, apellido FROM usuarios WHERE id = %s", (order['cliente_id'],))
            order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}" if client else 'N/A'
        return orders

    def get_sales_order_detail(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT ov.*, s.nombre as sucursal_nombre FROM ordenes_venta ov LEFT JOIN sucursales s ON ov.sucursal_id = s.id WHERE ov.id = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE sv.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_id = p.id LEFT JOIN servicios sv ON d.servicio_id = sv.id WHERE d.orden_id = %s",
                (order_id,))
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono FROM usuarios WHERE id = %s", (order['cliente_id'],))
            if client:
                order['cliente_nombre'] = f"{client['nombre']} {client['apellido']}"
                order['cliente_email'] = client['email']
                order['cliente_telefono'] = client['telefono']
        return order
