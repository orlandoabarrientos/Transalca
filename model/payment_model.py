from model.connection import Connection
from model.order_model import OrderModel, DETAIL_UNION


class PaymentModel(Connection):
    def __init__(self):
        super().__init__()

    def _base_select(self):
        return (
            "SELECT cp.*, cp.id_comprobante_pago AS id, cp.fecha_comprobante AS fecha, ov.total_orden_venta AS total, ov.fecha_orden_venta as orden_fecha, mp.nombre_metodo_pago AS metodo_pago "
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
        comprobantes = self.fetch_all("transalca",
            self._base_select() + "WHERE cp.estado = 'pendiente' ORDER BY cp.fecha_comprobante DESC")
        return self._attach_client(comprobantes)

    def _get_all(self, estado=None):
        if estado:
            comprobantes = self.fetch_all("transalca",
                self._base_select() + "WHERE cp.estado = %s ORDER BY cp.fecha_comprobante DESC",
                (estado,))
        else:
            comprobantes = self.fetch_all("transalca",
                self._base_select() + "ORDER BY cp.fecha_comprobante DESC")
        return self._attach_client(comprobantes)

    def _approve(self, comprobante_id, revisado_por_cedula=None):
        comp = self.fetch_one("transalca", "SELECT cp.*, cp.id_comprobante_pago AS id FROM comprobantes_pago cp WHERE cp.id_comprobante_pago = %s", (comprobante_id,))
        if not comp:
            return False
        self.update("transalca",
            "UPDATE comprobantes_pago SET estado = 'verificado' WHERE id_comprobante_pago = %s",
            (comprobante_id,))
        self.update("transalca",
            "UPDATE ordenes_venta SET estado = 'aprobada' WHERE id_orden_venta = %s", (comp['orden_venta_id'],))
        self.update("transalca",
            "UPDATE solicitudes_validacion sv "
            "INNER JOIN comprobantes_pago cp ON cp.id_comprobante_pago = sv.comprobante_pago_id "
            "SET sv.estado_validacion = 'aprobada' "
            "WHERE sv.estado_validacion = 'pendiente' AND cp.orden_venta_id = %s",
            (comp['orden_venta_id'],))
        # El servicio queda registrado/activado solo despues de validar el pago.
        OrderModel().ejecutar("activate_services_for_order", comp['orden_venta_id'])
        return True

    def _reject(self, comprobante_id, revisado_por_cedula=None, observaciones=''):
        comp = self.fetch_one("transalca", "SELECT cp.*, cp.id_comprobante_pago AS id FROM comprobantes_pago cp WHERE cp.id_comprobante_pago = %s", (comprobante_id,))
        if not comp:
            return False
        self.update("transalca",
            "UPDATE comprobantes_pago SET estado = 'rechazado', observaciones = %s WHERE id_comprobante_pago = %s",
            (observaciones, comprobante_id))
        self.update("transalca",
            "UPDATE ordenes_venta SET estado = 'rechazada' WHERE id_orden_venta = %s", (comp['orden_venta_id'],))
        self.update("transalca",
            "UPDATE solicitudes_validacion sv "
            "INNER JOIN comprobantes_pago cp ON cp.id_comprobante_pago = sv.comprobante_pago_id "
            "SET sv.estado_validacion = 'rechazada' "
            "WHERE sv.estado_validacion = 'pendiente' AND cp.orden_venta_id = %s",
            (comp['orden_venta_id'],))
        return True

    def _get_by_id(self, comprobante_id):
        comp = self.fetch_one("transalca",
            "SELECT cp.*, cp.id_comprobante_pago AS id, cp.fecha_comprobante AS fecha, ov.total_orden_venta AS total, ov.fecha_orden_venta as orden_fecha, ov.cliente_cedula, mp.nombre_metodo_pago AS metodo_pago "
            "FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id_orden_venta "
            "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id WHERE cp.id_comprobante_pago = %s",
            (comprobante_id,))
        if comp:
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono, cedula FROM usuarios WHERE cedula = %s", (comp['cliente_cedula'],))
            if client:
                comp.update(client)
            comp['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre_producto ELSE s.nombre_servicio END as item_nombre "
                "FROM " + DETAIL_UNION + " "
                "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
                "LEFT JOIN servicios s ON d.servicio_id = s.id_servicio WHERE d.orden_id = %s",
                (comp['orden_venta_id'],))
        return comp

    def _get_order_info_for_email(self, orden_venta_id):
        order = self.fetch_one("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE ov.id_orden_venta = %s", (orden_venta_id,))
        if order:
            client = self.fetch_one("mantenimiento",
                "SELECT * FROM usuarios WHERE cedula = %s", (order['cliente_cedula'],))
            details = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre_producto ELSE s.nombre_servicio END as item_nombre "
                "FROM " + DETAIL_UNION + " "
                "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
                "LEFT JOIN servicios s ON d.servicio_id = s.id_servicio WHERE d.orden_id = %s",
                (orden_venta_id,))
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
