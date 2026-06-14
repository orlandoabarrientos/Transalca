import json
import logging
from model.connection import Connection
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def caracas_now():
    return datetime.utcnow() - timedelta(hours=4)


DETAIL_UNION = (
    "((SELECT id_detalle_orden_venta_producto AS id, orden_id, producto_codigo, 0 AS servicio_id, 'producto' AS tipo, "
    "cantidad_detalle_orden_venta_producto AS cantidad, precio_unitario_producto AS precio_unitario, "
    "cantidad_detalle_orden_venta_producto * precio_unitario_producto AS subtotal FROM detalle_orden_venta_productos) "
    "UNION ALL "
    "(SELECT id_detalle_orden_venta_servicio AS id, orden_id, 'SIN_PRODUCTO' AS producto_codigo, servicio_id, 'servicio' AS tipo, "
    "cantidad_detalle_orden_venta_servicio AS cantidad, precio_unitario_servicio AS precio_unitario, "
    "cantidad_detalle_orden_venta_servicio * precio_unitario_servicio AS subtotal FROM detalle_orden_venta_servicios)) d"
)

ORDEN_ALIAS = "ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total"


class OrderModel(Connection):
    def __init__(self):
        super().__init__()

    def _ensure_client_exists(self, cliente_cedula):
        existing = self.fetch_one("transalca",
            "SELECT id_cliente FROM cliente WHERE identificador_cliente = %s", (cliente_cedula,))
        if existing:
            return True

        user = self.fetch_one("mantenimiento",
            "SELECT id, cedula, nombre, apellido, telefono, email, direccion FROM usuarios WHERE cedula = %s",
            (cliente_cedula,))

        if not user:
            return False

        nombre = (str(user.get('nombre') or 'Cliente').strip() + ' ' + str(user.get('apellido') or '').strip()).strip()
        cliente_id = self.insert("transalca",
            "INSERT INTO cliente (nombre_cliente, correo_cliente, identificador_cliente, telefono_cliente, direccion_cliente, tipo_cliente, estado) "
            "VALUES (%s, %s, %s, %s, %s, 'natural', 1)",
            (nombre, user.get('email', ''), user['cedula'], user.get('telefono', ''), user.get('direccion', '')))
        self.insert("transalca",
            "INSERT INTO cliente_natural (id_cliente, usuario_id, origen_registro) VALUES (%s, %s, 'cliente')",
            (cliente_id, user['id']))
        return True

    def _supports_qr_order_relation(self):
        column = self.fetch_one("transalca", "SHOW COLUMNS FROM qr_codes LIKE 'orden_venta_id'")
        return bool(column)

    def _get_current_rate(self, tipo='bcv'):
        return self.fetch_one("transalca",
            "SELECT id_tasa_cambio AS id, monto, tipo_tasa_cambio, fecha_tasa_cambio FROM tasas_cambio "
            "WHERE tipo_tasa_cambio = %s ORDER BY fecha_tasa_cambio DESC, id_tasa_cambio DESC LIMIT 1", (tipo,))

    def _get_cart(self, cliente_cedula):
        items = self.fetch_all("transalca",
            "SELECT c.*, c.id_carrito_compra AS id, CASE WHEN c.tipo_carrito = 0 THEN 'producto' ELSE 'servicio' END as tipo, c.cantidad_carrito as cantidad, "
            "CASE WHEN c.tipo_carrito = 0 THEN p.nombre_producto ELSE s.nombre_servicio END as item_nombre, "
            "CASE WHEN c.tipo_carrito = 0 THEN p.precio_producto ELSE s.precio_servicio END as precio, "
            "CASE WHEN c.tipo_carrito = 0 THEN "
            "  CASE WHEN p.imagen_producto IS NOT NULL AND p.imagen_producto != 'default_product.png' AND p.imagen_producto != '' THEN CONCAT('product_imgs/', p.imagen_producto) "
            "  ELSE CONCAT('images/', COALESCE(NULLIF(cat.imagen_categoria, ''), 'product-default-parts.png')) "
            "  END "
            "ELSE 'images/default_service.png' "
            "END as imagen_path "
            "FROM carrito_compra c "
            "LEFT JOIN productos p ON c.producto_codigo = p.codigo "
            "LEFT JOIN categorias cat ON p.categoria = cat.nombre_categoria "
            "LEFT JOIN servicios s ON c.servicio_id = s.id_servicio "
            "WHERE c.cliente_cedula = %s",
            (cliente_cedula,))
        return items

    def _get_active_payment_methods(self):
        try:
            return self.fetch_all("transalca",
                "SELECT id_metodo_pago AS id, nombre_metodo_pago AS nombre, permite_credito, moneda, datos_metodo_pago AS datos_pago "
                "FROM metodos_pago WHERE estado = 1 ORDER BY nombre_metodo_pago")
        except Exception:
            return [{'id': 0, 'nombre': n, 'permite_credito': 0, 'moneda': 'usd', 'datos_pago': ''} for n in ('transferencia', 'pago_movil', 'efectivo', 'zelle', 'binance', 'tarjeta')]

    def _get_payment_method(self, value):
        value = (value or '').strip()
        if not value:
            return None
        try:
            if value.isdigit():
                return self.fetch_one("transalca",
                    "SELECT id_metodo_pago AS id, nombre_metodo_pago AS nombre, permite_credito, moneda FROM metodos_pago WHERE id_metodo_pago = %s AND estado = 1 LIMIT 1",
                    (int(value),))
            return self.fetch_one("transalca",
                "SELECT id_metodo_pago AS id, nombre_metodo_pago AS nombre, permite_credito, moneda FROM metodos_pago WHERE nombre_metodo_pago = %s AND estado = 1 LIMIT 1", (value,))
        except Exception:
            if value in {'transferencia', 'pago_movil', 'efectivo', 'zelle', 'binance', 'tarjeta'}:
                return {'id': None, 'nombre': value, 'permite_credito': 0}
            return None

    def _is_valid_payment_method(self, value):
        return self._get_payment_method(value) is not None

    def _add_to_cart(self, cliente_cedula, item_id, tipo='producto', cantidad=1):
        if not self._ensure_client_exists(cliente_cedula):
            raise Exception("Cliente no encontrado")

        if tipo == 'producto':
            product = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo = %s AND estado = 1", (item_id,))
            if not product:
                raise ValueError("Producto no disponible")
            existing = self.fetch_one("transalca",
                "SELECT id_carrito_compra AS id, cantidad_carrito AS cantidad FROM carrito_compra WHERE cliente_cedula = %s AND producto_codigo = %s AND tipo_carrito = 0",
                (cliente_cedula, item_id))
            if existing:
                return self.update("transalca",
                    "UPDATE carrito_compra SET cantidad_carrito = cantidad_carrito + %s WHERE id_carrito_compra = %s", (cantidad, existing['id']))
            return self.insert("transalca",
                "INSERT INTO carrito_compra (cliente_cedula, producto_codigo, servicio_id, tipo_carrito, cantidad_carrito) VALUES (%s, %s, %s, 0, %s)",
                (cliente_cedula, item_id, None, cantidad))
        else:
            service = self.fetch_one("transalca", "SELECT id_servicio FROM servicios WHERE id_servicio = %s AND estado = 1", (item_id,))
            if not service:
                raise ValueError("Servicio no disponible")
            existing = self.fetch_one("transalca",
                "SELECT id_carrito_compra AS id FROM carrito_compra WHERE cliente_cedula = %s AND servicio_id = %s AND tipo_carrito = 1",
                (cliente_cedula, item_id))
            if existing:
                return existing['id']
            return self.insert("transalca",
                "INSERT INTO carrito_compra (cliente_cedula, producto_codigo, servicio_id, tipo_carrito, cantidad_carrito) VALUES (%s, %s, %s, 1, 1)",
                (cliente_cedula, None, item_id))

    def _update_cart_quantity(self, cart_id, cantidad):
        if cantidad <= 0:
            return self.delete("transalca", "DELETE FROM carrito_compra WHERE id_carrito_compra = %s", (cart_id,))
        return self.update("transalca",
            "UPDATE carrito_compra SET cantidad_carrito = %s WHERE id_carrito_compra = %s", (cantidad, cart_id))

    def _cart_item_owner(self, cart_id):
        row = self.fetch_one("transalca", "SELECT cliente_cedula FROM carrito_compra WHERE id_carrito_compra = %s", (cart_id,))
        return row['cliente_cedula'] if row else None

    def _remove_from_cart(self, cart_id):
        return self.delete("transalca", "DELETE FROM carrito_compra WHERE id_carrito_compra = %s", (cart_id,))

    def _clear_cart(self, cliente_cedula):
        return self.delete("transalca", "DELETE FROM carrito_compra WHERE cliente_cedula = %s", (cliente_cedula,))

    def _create_sale_order(self, cliente_cedula, metodo_pago, comprobante_url='', sucursal_id=None):
        if not self._ensure_client_exists(cliente_cedula):
            return None

        cart_items = self._get_cart(cliente_cedula)
        if not cart_items:
            return None

        qr_has_order_relation = self._supports_qr_order_relation()

        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            payment_method = self._get_payment_method(metodo_pago)
            if not payment_method:
                raise ValueError("El metodo de pago no es valido.")
            client = self.fetch_one("transalca",
                "SELECT c.tipo_cliente, j.dias_credito FROM cliente c "
                "LEFT JOIN cliente_juridico j ON j.id_cliente = c.id_cliente WHERE c.identificador_cliente = %s",
                (cliente_cedula,))
            if int(payment_method.get('permite_credito') or 0) and (not client or client.get('tipo_cliente') != 'juridica'):
                raise ValueError("Las compras a credito solo estan disponibles para empresas.")
            metodo_id = payment_method.get('id')
            tipo_pago = 'credito' if int(payment_method.get('permite_credito') or 0) else 'contado'
            fecha_inicio_credito = None
            fecha_vencimiento = None
            if tipo_pago == 'credito':
                fecha_inicio_credito = caracas_now().date()
                fecha_vencimiento = fecha_inicio_credito + timedelta(days=int(client.get('dias_credito') or 0))
            moneda = (payment_method.get('moneda') or 'usd').lower()

            current_rate = self._get_current_rate('bcv')
            tasa_cambio_id = current_rate['id'] if current_rate else None
            tasa_factor = 1.0
            if moneda == 'bs':
                try:
                    from model.bcv_rate_model import get_bcv_rates
                    from model.binance_rate_model import get_usdt_rate_ves
                    bcv_rate = float(get_bcv_rates(verify=False).get('usd', 0))
                    usdt_rate = float(get_usdt_rate_ves())
                    if bcv_rate > 0 and usdt_rate > 0:
                        tasa_factor = usdt_rate / bcv_rate
                    else:
                        tasa_factor = 1.3200
                except Exception:
                    tasa_factor = 1.3200

            total = 0
            for item in cart_items:
                item_price = float(item['precio'])
                if moneda == 'bs':
                    item_price = round(item_price * tasa_factor, 2)
                total += item_price * item['cantidad']

            cursor.execute(
                "INSERT INTO ordenes_venta (cliente_cedula, sucursal_id, fecha_orden_venta, total_orden_venta, metodo_pago_id, tasa_cambio_id, tipo_pago) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (cliente_cedula, sucursal_id, caracas_now(), total, metodo_id, tasa_cambio_id, tipo_pago))
            order_id = cursor.lastrowid
            if tipo_pago == 'credito':
                cursor.execute(
                    "INSERT INTO creditos_orden_venta (orden_venta_id, fecha_inicio_credito, fecha_vencimiento_credito, estado_credito) "
                    "VALUES (%s, %s, %s, 'activo')",
                    (order_id, fecha_inicio_credito, fecha_vencimiento))
            for item in cart_items:
                item_price = float(item['precio'])
                if moneda == 'bs':
                    item_price = round(item_price * tasa_factor, 2)
                if item['tipo'] == 'producto':
                    cursor.execute(
                        "INSERT INTO detalle_orden_venta_productos (orden_id, producto_codigo, cantidad_detalle_orden_venta_producto, precio_unitario_producto) VALUES (%s, %s, %s, %s)",
                        (order_id, item['producto_codigo'], item['cantidad'], item_price))
                else:
                    cursor.execute(
                        "INSERT INTO detalle_orden_venta_servicios (orden_id, servicio_id, cantidad_detalle_orden_venta_servicio, precio_unitario_servicio) VALUES (%s, %s, 1, %s)",
                        (order_id, item['servicio_id'], item_price))
            if comprobante_url:
                cursor.execute(
                    "INSERT INTO comprobantes_pago (orden_venta_id, imagen_url) VALUES (%s, %s)",
                    (order_id, comprobante_url))

            try:
                qr_payload = json.dumps({"kind": "factura", "orden_id": order_id})
                if qr_has_order_relation:
                    cursor.execute(
                        "INSERT INTO qr_codes (usuario_cedula, tipo_qr_code, contenido, utilidad, referencia_qr_code, orden_venta_id) VALUES (%s, 1, %s, 'factura', %s, %s)",
                        (cliente_cedula, qr_payload, order_id, order_id))
                else:
                    cursor.execute(
                        "INSERT INTO qr_codes (usuario_cedula, tipo_qr_code, contenido, utilidad, referencia_qr_code) VALUES (%s, 1, %s, 'factura', %s)",
                        (cliente_cedula, qr_payload, order_id))
            except Exception:
                logger.warning("No se pudo crear el QR de factura para la orden %s.", order_id, exc_info=True)

            cursor.execute("DELETE FROM carrito_compra WHERE cliente_cedula = %s", (cliente_cedula,))
            conn.commit()
            return order_id
        except ValueError:
            conn.rollback()
            raise
        except Exception:
            conn.rollback()
            logger.exception("Error al crear la orden de venta")
            return None

    def _activate_services_for_order(self, order_id):
        """Crea los registros en servicio_mecanico cuando el pago de la orden fue validado."""
        try:
            order = self.fetch_one("transalca",
                "SELECT id_orden_venta, cliente_cedula FROM ordenes_venta WHERE id_orden_venta = %s", (order_id,))
            if not order:
                return 0
            services = self.fetch_all("transalca",
                "SELECT d.servicio_id FROM detalle_orden_venta_servicios d WHERE d.orden_id = %s", (order_id,))
            created = 0
            for svc in services:
                existing = self.fetch_one("transalca",
                    "SELECT id_servicio_mecanico FROM servicio_mecanico WHERE orden_venta_id = %s AND servicio_id = %s",
                    (order_id, svc['servicio_id']))
                if existing:
                    continue
                self.insert("transalca",
                    "INSERT INTO servicio_mecanico (servicio_id, mecanico_cedula, orden_venta_id, observaciones_servicio, cliente_cedula, estado_servicio) "
                    "VALUES (%s, NULL, %s, %s, %s, 'sin_asignar')",
                    (svc['servicio_id'], order_id, 'Pago validado - pendiente de asignacion de mecanico', order['cliente_cedula']))
                created += 1
            return created
        except Exception:
            logger.exception("No se pudieron activar los servicios de la orden %s", order_id)
            return 0

    def _get_client_orders(self, cliente_cedula):
        return self.fetch_all("transalca",
            "SELECT " + ORDEN_ALIAS + ", mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE ov.cliente_cedula = %s ORDER BY ov.fecha_orden_venta DESC", (cliente_cedula,))

    def _get_order_detail(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT " + ORDEN_ALIAS + ", mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda, "
            "t.monto AS tasa_monto, t.fecha_tasa_cambio AS tasa_fecha, t.tipo_tasa_cambio AS tasa_tipo "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "LEFT JOIN tasas_cambio t ON t.id_tasa_cambio = ov.tasa_cambio_id "
            "WHERE ov.id_orden_venta = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre_producto ELSE s.nombre_servicio END as item_nombre "
                "FROM " + DETAIL_UNION + " "
                "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
                "LEFT JOIN servicios s ON d.servicio_id = s.id_servicio WHERE d.orden_id = %s",
                (order_id,))
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono, cedula FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            if not client:
                client = self.fetch_one("transalca",
                    "SELECT nombre_cliente AS nombre, '' AS apellido, correo_cliente AS email, "
                    "telefono_cliente AS telefono, identificador_cliente AS cedula "
                    "FROM cliente WHERE identificador_cliente = %s", (order['cliente_cedula'],))
            if client:
                order.update(client)
            comprobante = self.fetch_one("transalca",
                "SELECT cp.*, cp.id_comprobante_pago AS id, cp.fecha_comprobante AS fecha FROM comprobantes_pago cp "
                "WHERE cp.orden_venta_id = %s ORDER BY cp.id_comprobante_pago DESC LIMIT 1", (order_id,))
            order['comprobante'] = comprobante
        return order

    def _get_cart_count(self, cliente_cedula):
        result = self.fetch_one("transalca",
            "SELECT COALESCE(SUM(cantidad_carrito), 0) as total FROM carrito_compra WHERE cliente_cedula = %s", (cliente_cedula,))
        return result['total'] if result else 0

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "ensure_client_exists": self._ensure_client_exists,
            "supports_qr_order_relation": self._supports_qr_order_relation,
            "get_current_rate": self._get_current_rate,
            "get_cart": self._get_cart,
            "get_active_payment_methods": self._get_active_payment_methods,
            "get_payment_method": self._get_payment_method,
            "is_valid_payment_method": self._is_valid_payment_method,
            "add_to_cart": self._add_to_cart,
            "update_cart_quantity": self._update_cart_quantity,
            "cart_item_owner": self._cart_item_owner,
            "remove_from_cart": self._remove_from_cart,
            "clear_cart": self._clear_cart,
            "create_sale_order": self._create_sale_order,
            "activate_services_for_order": self._activate_services_for_order,
            "get_client_orders": self._get_client_orders,
            "get_order_detail": self._get_order_detail,
            "get_cart_count": self._get_cart_count,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
