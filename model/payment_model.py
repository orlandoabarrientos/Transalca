from model.connection import Connection
from model.order_model import OrderModel
from config.validation import ValidationError, optional_text

PAYMENT_PENDING_SQL = (
    "SELECT cp.*, cp.id_comprobante_pago AS id, DATE_FORMAT(cp.fecha_comprobante, '%%Y-%%m-%%dT%%H:%%i:%%s') AS fecha, ov.total_orden_venta AS total, ov.fecha_orden_venta as orden_fecha, mp.nombre_metodo_pago AS metodo_pago "
    "FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id_orden_venta "
    "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
    "WHERE cp.estado = 'pendiente' ORDER BY cp.fecha_comprobante DESC"
)
PAYMENT_ALL_SQL = (
    "SELECT cp.*, cp.id_comprobante_pago AS id, DATE_FORMAT(cp.fecha_comprobante, '%%Y-%%m-%%dT%%H:%%i:%%s') AS fecha, ov.total_orden_venta AS total, ov.fecha_orden_venta as orden_fecha, mp.nombre_metodo_pago AS metodo_pago "
    "FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id_orden_venta "
    "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
    "ORDER BY cp.fecha_comprobante DESC"
)
PAYMENT_BY_STATUS_SQL = (
    "SELECT cp.*, cp.id_comprobante_pago AS id, DATE_FORMAT(cp.fecha_comprobante, '%%Y-%%m-%%dT%%H:%%i:%%s') AS fecha, ov.total_orden_venta AS total, ov.fecha_orden_venta as orden_fecha, mp.nombre_metodo_pago AS metodo_pago "
    "FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id_orden_venta "
    "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
    "WHERE cp.estado = %s ORDER BY cp.fecha_comprobante DESC"
)
PAYMENT_DETAIL_ITEMS_SQL = (
    "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre_producto ELSE s.nombre_servicio END as item_nombre "
    "FROM ((SELECT id_detalle_orden_venta_producto AS id, orden_id, producto_codigo, 0 AS servicio_id, 'producto' AS tipo, "
    "cantidad_detalle_orden_venta_producto AS cantidad, precio_unitario_producto AS precio_unitario, "
    "cantidad_detalle_orden_venta_producto * precio_unitario_producto AS subtotal FROM detalle_orden_venta_productos) "
    "UNION ALL "
    "(SELECT id_detalle_orden_venta_servicio AS id, orden_id, 'SIN_PRODUCTO' AS producto_codigo, servicio_id, 'servicio' AS tipo, "
    "cantidad_detalle_orden_venta_servicio AS cantidad, precio_unitario_servicio AS precio_unitario, "
    "cantidad_detalle_orden_venta_servicio * precio_unitario_servicio AS subtotal FROM detalle_orden_venta_servicios)) d "
    "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
    "LEFT JOIN servicios s ON d.servicio_id = s.id_servicio WHERE d.orden_id = %s"
)


class PaymentModel(Connection):
    def __init__(self):
        super().__init__()

    def _base_select(self):
        return (
            "SELECT cp.*, cp.id_comprobante_pago AS id, DATE_FORMAT(cp.fecha_comprobante, '%%Y-%%m-%%dT%%H:%%i:%%s') AS fecha, ov.total_orden_venta AS total, ov.fecha_orden_venta as orden_fecha, mp.nombre_metodo_pago AS metodo_pago "
            "FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id_orden_venta "
            "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
        )

    def _attach_client(self, comprobantes, with_phone=True):
        for comp in comprobantes:
            order = self.fetch_one("transalca", "SELECT cliente_cedula FROM ordenes_venta WHERE id_orden_venta = %s", (comp['orden_venta_id'],))
            if order:
                client = self.fetch_one("mantenimiento",
                    "SELECT nombre, apellido, email, telefono FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
                if not client:
                    client = self.fetch_one("transalca",
                        "SELECT nombre_cliente AS nombre, '' AS apellido, correo_cliente AS email, telefono_cliente AS telefono "
                        "FROM cliente WHERE identificador_cliente = %s", (order['cliente_cedula'],))
                if client:
                    comp['cliente_nombre'] = f"{client['nombre']} {client['apellido']}".strip()
                    comp['cliente_email'] = client['email']
        return comprobantes

    def _get_pending(self):
        comprobantes = self.fetch_all("transalca", PAYMENT_PENDING_SQL)
        return self._attach_client(comprobantes)

    def _get_all(self, estado=None):
        if estado:
            comprobantes = self.fetch_all("transalca", PAYMENT_BY_STATUS_SQL, (estado,))
        else:
            comprobantes = self.fetch_all("transalca", PAYMENT_ALL_SQL)
        return self._attach_client(comprobantes)

    def _approve(self, comprobante_id, revisado_por_cedula=None):
        comp = self.fetch_one("transalca", "SELECT cp.*, cp.id_comprobante_pago AS id FROM comprobantes_pago cp WHERE cp.id_comprobante_pago = %s", (comprobante_id,))
        if not comp:
            return False
        self.update("transalca", "CALL sp_aprobar_pago(%s)", (comprobante_id,))
        OrderModel().ejecutar("activate_services_for_order", comp['orden_venta_id'])
        return True

    def _reject(self, comprobante_id, revisado_por_cedula=None, observaciones=''):
        errors = {}
        observaciones = optional_text(errors, 'observaciones', observaciones, 'El motivo', max_len=255, allow_serial=True)
        if not observaciones:
            errors['observaciones'] = 'El motivo es obligatorio.'
        if errors:
            raise ValidationError(errors)
        comp = self.fetch_one("transalca", "SELECT cp.*, cp.id_comprobante_pago AS id FROM comprobantes_pago cp WHERE cp.id_comprobante_pago = %s", (comprobante_id,))
        if not comp:
            return False
        self.update("transalca", "CALL sp_rechazar_pago(%s, %s)", (comprobante_id, observaciones))
        return True

    def _get_by_id(self, comprobante_id):
        comp = self.fetch_one("transalca",
            "SELECT cp.*, cp.id_comprobante_pago AS id, DATE_FORMAT(cp.fecha_comprobante, '%%Y-%%m-%%dT%%H:%%i:%%s') AS fecha, ov.total_orden_venta AS total, ov.fecha_orden_venta as orden_fecha, ov.cliente_cedula, mp.nombre_metodo_pago AS metodo_pago "
            "FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id_orden_venta "
            "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id WHERE cp.id_comprobante_pago = %s",
            (comprobante_id,))
        if comp:
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono, cedula FROM usuarios WHERE cedula = %s", (comp['cliente_cedula'],))
            if client:
                comp.update(client)
            comp['detalles'] = self.fetch_all("transalca", PAYMENT_DETAIL_ITEMS_SQL, (comp['orden_venta_id'],))
        return comp

    def _get_order_info_for_email(self, orden_venta_id):
        order = self.fetch_one("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE ov.id_orden_venta = %s", (orden_venta_id,))
        if order:
            client = self.fetch_one("mantenimiento",
                "SELECT * FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            details = self.fetch_all("transalca", PAYMENT_DETAIL_ITEMS_SQL, (orden_venta_id,))
            return {"order": order, "client": client, "details": details}
        return None

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_pending": self._get_pending,
            "get_all": self._get_all,
            "approve": self._approve,
            "reject": self._reject,
            "get_by_id": self._get_by_id,
            "get_order_info_for_email": self._get_order_info_for_email,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
