import json
from model.connection import Connection


class OrderModel(Connection):
    def __init__(self):
        super().__init__()

    def ensure_client_exists(self, cliente_cedula):
        existing = self.fetch_one("transalca",
            "SELECT cedula FROM clientes WHERE cedula = %s", (cliente_cedula,))
        if existing:
            return True

        user = self.fetch_one("mantenimiento",
            "SELECT cedula, nombre, apellido, telefono, email, direccion FROM usuarios WHERE cedula = %s",
            (cliente_cedula,))

        if not user:
            user = self.fetch_one("transalca",
                "SELECT cedula, nombre, apellido, email FROM usuarios WHERE cedula = %s",
                (cliente_cedula,))

        if not user:
            return False

        self.insert("transalca",
            "INSERT INTO clientes (cedula, nombre, apellido, telefono, email, direccion) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE nombre = VALUES(nombre), apellido = VALUES(apellido), telefono = VALUES(telefono), email = VALUES(email), direccion = VALUES(direccion)",
            (
                user['cedula'],
                user.get('nombre', 'Cliente'),
                user.get('apellido', 'Transalca'),
                user.get('telefono', ''),
                user.get('email', ''),
                user.get('direccion', '')
            ))
        return True

    def supports_unassigned_service_records(self):
        column = self.fetch_one("transalca", "SHOW COLUMNS FROM servicio_mecanico LIKE 'mecanico_cedula'")
        if not column:
            return False
        if column.get('Null') == 'YES':
            return True
        try:
            self.update("transalca", "ALTER TABLE servicio_mecanico MODIFY mecanico_cedula VARCHAR(20) NULL")
        except Exception:
            return False
        column = self.fetch_one("transalca", "SHOW COLUMNS FROM servicio_mecanico LIKE 'mecanico_cedula'")
        return bool(column and column.get('Null') == 'YES')

    def get_cart(self, cliente_cedula):
        items = self.fetch_all("transalca",
            "SELECT c.*, CASE WHEN c.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre, CASE WHEN c.tipo = 'producto' THEN p.precio ELSE s.precio END as precio, CASE WHEN c.tipo = 'producto' THEN p.imagen ELSE 'default_service.png' END as imagen FROM carrito c LEFT JOIN productos p ON c.producto_codigo = p.codigo LEFT JOIN servicios s ON c.servicio_id = s.id WHERE c.cliente_cedula = %s",
            (cliente_cedula,))
        return items

    def add_to_cart(self, cliente_cedula, item_id, tipo='producto', cantidad=1):
        if not self.ensure_client_exists(cliente_cedula):
            raise Exception("Cliente no encontrado")

        if tipo == 'producto':
            existing = self.fetch_one("transalca",
                "SELECT id, cantidad FROM carrito WHERE cliente_cedula = %s AND producto_codigo = %s AND tipo = 'producto'",
                (cliente_cedula, item_id))
            if existing:
                return self.update("transalca",
                    "UPDATE carrito SET cantidad = cantidad + %s WHERE id = %s", (cantidad, existing['id']))
            return self.insert("transalca",
                "INSERT INTO carrito (cliente_cedula, producto_codigo, tipo, cantidad) VALUES (%s, %s, 'producto', %s)",
                (cliente_cedula, item_id, cantidad))
        else:
            existing = self.fetch_one("transalca",
                "SELECT id FROM carrito WHERE cliente_cedula = %s AND servicio_id = %s AND tipo = 'servicio'",
                (cliente_cedula, item_id))
            if existing:
                return existing['id']
            return self.insert("transalca",
                "INSERT INTO carrito (cliente_cedula, servicio_id, tipo, cantidad) VALUES (%s, %s, 'servicio', 1)",
                (cliente_cedula, item_id))

    def update_cart_quantity(self, cart_id, cantidad):
        if cantidad <= 0:
            return self.delete("transalca", "DELETE FROM carrito WHERE id = %s", (cart_id,))
        return self.update("transalca",
            "UPDATE carrito SET cantidad = %s WHERE id = %s", (cantidad, cart_id))

    def remove_from_cart(self, cart_id):
        return self.delete("transalca", "DELETE FROM carrito WHERE id = %s", (cart_id,))

    def clear_cart(self, cliente_cedula):
        return self.delete("transalca", "DELETE FROM carrito WHERE cliente_cedula = %s", (cliente_cedula,))

    def create_sale_order(self, cliente_cedula, metodo_pago, comprobante_url='', sucursal_id=None):
        if not self.ensure_client_exists(cliente_cedula):
            return None

        cart_items = self.get_cart(cliente_cedula)
        if not cart_items:
            return None

        allow_unassigned_services = True
        if any(item['tipo'] == 'servicio' for item in cart_items):
            allow_unassigned_services = self.supports_unassigned_service_records()

        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            total = sum(item['precio'] * item['cantidad'] for item in cart_items)
            cursor.execute(
                "INSERT INTO ordenes_venta (cliente_cedula, sucursal_id, total, metodo_pago, comprobante_url) VALUES (%s, %s, %s, %s, %s)",
                (cliente_cedula, sucursal_id, total, metodo_pago, comprobante_url))
            order_id = cursor.lastrowid
            for item in cart_items:
                if item['tipo'] == 'producto':
                    subtotal = item['precio'] * item['cantidad']
                    cursor.execute(
                        "INSERT INTO detalle_orden_venta (orden_id, producto_codigo, tipo, cantidad, precio_unitario, subtotal) VALUES (%s, %s, 'producto', %s, %s, %s)",
                        (order_id, item['producto_codigo'], item['cantidad'], item['precio'], subtotal))
                else:
                    cursor.execute(
                        "INSERT INTO detalle_orden_venta (orden_id, servicio_id, tipo, cantidad, precio_unitario, subtotal) VALUES (%s, %s, 'servicio', 1, %s, %s)",
                        (order_id, item['servicio_id'], item['precio'], item['precio']))
                    if allow_unassigned_services:
                        cursor.execute(
                            "INSERT INTO servicio_mecanico (servicio_id, mecanico_cedula, orden_venta_id, observaciones) VALUES (%s, %s, %s, %s)",
                            (item['servicio_id'], None, order_id, 'Pendiente de asignacion de mecanico'))
            if comprobante_url:
                cursor.execute(
                    "INSERT INTO comprobantes_pago (orden_venta_id, imagen_url) VALUES (%s, %s)",
                    (order_id, comprobante_url))

            try:
                qr_payload = json.dumps({"kind": "factura", "orden_id": order_id})
                cursor.execute(
                    "INSERT INTO qr_codes (usuario_cedula, tipo, contenido, utilidad, referencia_id) VALUES (%s, 'pago', %s, 'factura', %s)",
                    (cliente_cedula, qr_payload, order_id))
            except Exception:
                pass

            cursor.execute("DELETE FROM carrito WHERE cliente_cedula = %s", (cliente_cedula,))
            conn.commit()
            return order_id
        except Exception:
            conn.rollback()
            return None

    def get_client_orders(self, cliente_cedula):
        return self.fetch_all("transalca",
            "SELECT * FROM ordenes_venta WHERE cliente_cedula = %s ORDER BY fecha DESC", (cliente_cedula,))

    def get_order_detail(self, order_id):
        order = self.fetch_one("transalca", "SELECT * FROM ordenes_venta WHERE id = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_codigo = p.codigo LEFT JOIN servicios s ON d.servicio_id = s.id WHERE d.orden_id = %s",
                (order_id,))
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono, cedula FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            if client:
                order.update(client)
            comprobante = self.fetch_one("transalca",
                "SELECT * FROM comprobantes_pago WHERE orden_venta_id = %s ORDER BY id DESC LIMIT 1", (order_id,))
            order['comprobante'] = comprobante
        return order

    def get_cart_count(self, cliente_cedula):
        result = self.fetch_one("transalca",
            "SELECT COALESCE(SUM(cantidad), 0) as total FROM carrito WHERE cliente_cedula = %s", (cliente_cedula,))
        return result['total'] if result else 0
