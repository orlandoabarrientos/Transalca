from model.connection import Connection


class PaymentModel(Connection):
    def __init__(self):
        super().__init__()

    def get_pending(self):
        comprobantes = self.fetch_all("transalca",
            "SELECT cp.*, ov.total, ov.fecha as orden_fecha FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id WHERE cp.estado = 'pendiente' ORDER BY cp.fecha DESC")
        for comp in comprobantes:
            order = self.fetch_one("transalca", "SELECT cliente_id FROM ordenes_venta WHERE id = %s", (comp['orden_venta_id'],))
            if order:
                client = self.fetch_one("mantenimiento",
                    "SELECT nombre, apellido, email, telefono FROM usuarios WHERE id = %s", (order['cliente_id'],))
                if client:
                    comp['cliente_nombre'] = f"{client['nombre']} {client['apellido']}"
                    comp['cliente_email'] = client['email']
        return comprobantes

    def get_all(self, estado=None):
        if estado:
            comprobantes = self.fetch_all("transalca",
                "SELECT cp.*, ov.total, ov.fecha as orden_fecha FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id WHERE cp.estado = %s ORDER BY cp.fecha DESC",
                (estado,))
        else:
            comprobantes = self.fetch_all("transalca",
                "SELECT cp.*, ov.total, ov.fecha as orden_fecha FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id ORDER BY cp.fecha DESC")
        for comp in comprobantes:
            order = self.fetch_one("transalca", "SELECT cliente_id FROM ordenes_venta WHERE id = %s", (comp['orden_venta_id'],))
            if order:
                client = self.fetch_one("mantenimiento",
                    "SELECT nombre, apellido, email FROM usuarios WHERE id = %s", (order['cliente_id'],))
                if client:
                    comp['cliente_nombre'] = f"{client['nombre']} {client['apellido']}"
                    comp['cliente_email'] = client['email']
            reviewer = None
            if comp['revisado_por']:
                reviewer = self.fetch_one("mantenimiento",
                    "SELECT nombre, apellido FROM usuarios WHERE id = %s", (comp['revisado_por'],))
            comp['revisado_por_nombre'] = f"{reviewer['nombre']} {reviewer['apellido']}" if reviewer else 'N/A'
        return comprobantes

    def approve(self, comprobante_id, revisado_por):
        comp = self.fetch_one("transalca", "SELECT * FROM comprobantes_pago WHERE id = %s", (comprobante_id,))
        if not comp:
            return False
        self.update("transalca",
            "UPDATE comprobantes_pago SET estado = 'aprobado', revisado_por = %s WHERE id = %s",
            (revisado_por, comprobante_id))
        self.update("transalca",
            "UPDATE ordenes_venta SET estado = 'aprobada' WHERE id = %s", (comp['orden_venta_id'],))
        return True

    def reject(self, comprobante_id, revisado_por, observaciones=''):
        comp = self.fetch_one("transalca", "SELECT * FROM comprobantes_pago WHERE id = %s", (comprobante_id,))
        if not comp:
            return False
        self.update("transalca",
            "UPDATE comprobantes_pago SET estado = 'rechazado', revisado_por = %s, observaciones = %s WHERE id = %s",
            (revisado_por, observaciones, comprobante_id))
        self.update("transalca",
            "UPDATE ordenes_venta SET estado = 'rechazada' WHERE id = %s", (comp['orden_venta_id'],))
        return True

    def get_by_id(self, comprobante_id):
        comp = self.fetch_one("transalca",
            "SELECT cp.*, ov.total, ov.fecha as orden_fecha, ov.cliente_id FROM comprobantes_pago cp INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id WHERE cp.id = %s",
            (comprobante_id,))
        if comp:
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, email, telefono, cedula FROM usuarios WHERE id = %s", (comp['cliente_id'],))
            if client:
                comp.update(client)
            comp['detalles'] = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_id = p.id LEFT JOIN servicios s ON d.servicio_id = s.id WHERE d.orden_id = %s",
                (comp['orden_venta_id'],))
        return comp

    def get_order_info_for_email(self, orden_venta_id):
        order = self.fetch_one("transalca", "SELECT * FROM ordenes_venta WHERE id = %s", (orden_venta_id,))
        if order:
            client = self.fetch_one("mantenimiento",
                "SELECT * FROM usuarios WHERE id = %s", (order['cliente_id'],))
            details = self.fetch_all("transalca",
                "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_id = p.id LEFT JOIN servicios s ON d.servicio_id = s.id WHERE d.orden_id = %s",
                (orden_venta_id,))
            return {"order": order, "client": client, "details": details}
        return None
