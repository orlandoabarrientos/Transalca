from model.connection import Connection


class OrderModel(Connection):
    def __init__(self):
        super().__init__()

    def get_cart(self, cliente_id):
        items = self.fetch_all("transalca",
            "SELECT c.*, CASE WHEN c.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre, CASE WHEN c.tipo = 'producto' THEN p.precio ELSE s.precio END as precio, CASE WHEN c.tipo = 'producto' THEN p.imagen ELSE 'default_service.png' END as imagen FROM carrito c LEFT JOIN productos p ON c.producto_id = p.id LEFT JOIN servicios s ON c.servicio_id = s.id WHERE c.cliente_id = %s",
            (cliente_id,))
        return items

    def add_to_cart(self, cliente_id, item_id, tipo='producto', cantidad=1):
        if tipo == 'producto':
            existing = self.fetch_one("transalca",
                "SELECT id, cantidad FROM carrito WHERE cliente_id = %s AND producto_id = %s AND tipo = 'producto'",
                (cliente_id, item_id))
            if existing:
                return self.update("transalca",
                    "UPDATE carrito SET cantidad = cantidad + %s WHERE id = %s", (cantidad, existing['id']))
            return self.insert("transalca",
                "INSERT INTO carrito (cliente_id, producto_id, tipo, cantidad) VALUES (%s, %s, 'producto', %s)",
                (cliente_id, item_id, cantidad))
        else:
            existing = self.fetch_one("transalca",
                "SELECT id FROM carrito WHERE cliente_id = %s AND servicio_id = %s AND tipo = 'servicio'",
                (cliente_id, item_id))
            if existing:
                return existing['id']
            return self.insert("transalca",
                "INSERT INTO carrito (cliente_id, servicio_id, tipo, cantidad) VALUES (%s, %s, 'servicio', 1)",
                (cliente_id, item_id))

    def update_cart_quantity(self, cart_id, cantidad):
        if cantidad <= 0:
            return self.delete("transalca", "DELETE FROM carrito WHERE id = %s", (cart_id,))
        return self.update("transalca",
            "UPDATE carrito SET cantidad = %s WHERE id = %s", (cantidad, cart_id))

    def remove_from_cart(self, cart_id):
        return self.delete("transalca", "DELETE FROM carrito WHERE id = %s", (cart_id,))

    def clear_cart(self, cliente_id):
        return self.delete("transalca", "DELETE FROM carrito WHERE cliente_id = %s", (cliente_id,))

    def create_sale_order(self, cliente_id, metodo_pago, comprobante_url=''):
        cart_items = self.get_cart(cliente_id)
        if not cart_items:
            return None
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            total = sum(item['precio'] * item['cantidad'] for item in cart_items)
            cursor.execute(
                "INSERT INTO ordenes_venta (cliente_id, total, metodo_pago, comprobante_url) VALUES (%s, %s, %s, %s)",
                (cliente_id, total, metodo_pago, comprobante_url))
            order_id = cursor.lastrowid
            for item in cart_items:
                if item['tipo'] == 'producto':
                    subtotal = item['precio'] * item['cantidad']
                    cursor.execute(
                        "INSERT INTO detalle_orden_venta (orden_id, producto_id, tipo, cantidad, precio_unitario, subtotal) VALUES (%s, %s, 'producto', %s, %s, %s)",
                        (order_id, item['producto_id'], item['cantidad'], item['precio'], subtotal))
                else:
                    cursor.execute(
                        "INSERT INTO detalle_orden_venta (orden_id, servicio_id, tipo, cantidad, precio_unitario, subtotal) VALUES (%s, %s, 'servicio', 1, %s, %s)",
                        (order_id, item['servicio_id'], item['precio'], item['precio']))
            if comprobante_url:
                cursor.execute(
                    "INSERT INTO comprobantes_pago (orden_venta_id, imagen_url) VALUES (%s, %s)",
                    (order_id, comprobante_url))
            cursor.execute("DELETE FROM carrito WHERE cliente_id = %s", (cliente_id,))
            conn.commit()
            return order_id
        except Exception:
            conn.rollback()
            return None

    def get_client_orders(self, cliente_id):
        return self.fetch_all("transalca",
            "SELECT * FROM ordenes_venta WHERE cliente_id = %s ORDER BY fecha DESC", (cliente_id,))

    def get_order_detail(self, order_id):
        order = self.fetch_one("transalca", "SELECT * FROM ordenes_venta WHERE id = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_id = p.id LEFT JOIN servicios s ON d.servicio_id = s.id WHERE d.orden_id = %s",
                (order_id,))
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono, cedula FROM usuarios WHERE id = %s", (order['cliente_id'],))
            if client:
                order.update(client)
            comprobante = self.fetch_one("transalca",
                "SELECT * FROM comprobantes_pago WHERE orden_venta_id = %s ORDER BY id DESC LIMIT 1", (order_id,))
            order['comprobante'] = comprobante
        return order

    def get_cart_count(self, cliente_id):
        result = self.fetch_one("transalca",
            "SELECT COALESCE(SUM(cantidad), 0) as total FROM carrito WHERE cliente_id = %s", (cliente_id,))
        return result['total'] if result else 0
