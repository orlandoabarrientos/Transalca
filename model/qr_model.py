from model.connection import Connection
import json


class QRModel(Connection):
    def __init__(self):
        super().__init__()

    def create_qr(self, data):
        return self.insert("transalca",
            "INSERT INTO qr_codes (usuario_cedula, tipo, contenido, utilidad) VALUES (%s, %s, %s, %s)",
            (data['usuario_cedula'], data.get('tipo', 'info'), data.get('contenido', ''), data.get('utilidad', '')))

    def get_user_qrs(self, usuario_cedula):
        return self.fetch_all("transalca",
            "SELECT * FROM qr_codes WHERE usuario_cedula = %s AND estado = 1 ORDER BY created_at DESC",
            (usuario_cedula,))

    def get_by_id(self, qr_id):
        return self.fetch_one("transalca", "SELECT * FROM qr_codes WHERE id = %s", (qr_id,))

    def update_qr(self, qr_id, data):
        return self.update("transalca",
            "UPDATE qr_codes SET tipo = %s, contenido = %s, utilidad = %s WHERE id = %s",
            (data.get('tipo', 'info'), data.get('contenido', ''), data.get('utilidad', ''), qr_id))

    def delete_qr(self, qr_id):
        return self.update("transalca",
            "UPDATE qr_codes SET estado = 0 WHERE id = %s", (qr_id,))

    def soft_delete(self, qr_id):
        return self.delete_qr(qr_id)

    def get_qr_data(self, qr_id):
        qr = self.get_by_id(qr_id)
        if not qr:
            return None
        user = self.fetch_one("mantenimiento",
            "SELECT nombre, apellido, cedula, email, telefono FROM usuarios WHERE cedula = %s", (qr['usuario_cedula'],))
        result = {"qr": qr, "usuario": user}
        if qr['tipo'] == 'promocion':
            try:
                content = json.loads(qr['contenido'])
                card = self.fetch_one("transalca",
                    "SELECT tf.*, p.nombre as promo_nombre, p.puntos_requeridos, p.recompensa FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id WHERE tf.id = %s",
                    (content.get('tarjeta_id'),))
                result['tarjeta'] = card
            except (json.JSONDecodeError, TypeError):
                pass
        elif qr['tipo'] == 'servicio':
            try:
                content = json.loads(qr['contenido'])
                order = self.fetch_one("transalca", "SELECT * FROM ordenes_venta WHERE id = %s", (content.get('orden_id'),))
                if order:
                    order['detalles'] = self.fetch_all("transalca",
                        "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_codigo = p.codigo LEFT JOIN servicios s ON d.servicio_id = s.id WHERE d.orden_id = %s",
                        (order['id'],))
                result['orden'] = order
            except (json.JSONDecodeError, TypeError):
                pass
        return result

    def get_all_qrs(self):
        qrs = self.fetch_all("transalca", "SELECT * FROM qr_codes WHERE estado = 1 ORDER BY created_at DESC")
        for qr in qrs:
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (qr['usuario_cedula'],))
            qr['usuario_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'N/A'
        return qrs
