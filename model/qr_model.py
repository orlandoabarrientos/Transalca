from model.connection import Connection
import json
from datetime import datetime, timedelta


class QRModel(Connection):
    def __init__(self):
        super().__init__()

    def _parse_content(self, content):
        if not content:
            return {}
        if isinstance(content, dict):
            return content
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _build_content(self, data, existing_content=None):
        utility_type = (data.get('utilidad_tipo') or '').strip().lower()
        if not utility_type:
            return data.get('contenido', '')

        payload = self._parse_content(existing_content)
        if not payload:
            payload = {}

        ttl_minutos = data.get('ttl_minutos') or 10
        try:
            ttl_minutos = max(int(ttl_minutos), 1)
        except Exception:
            ttl_minutos = 10

        referencia_id = data.get('referencia_id')
        if referencia_id in ('', None):
            referencia_id = None
        else:
            try:
                referencia_id = int(referencia_id)
            except Exception as exc:
                raise ValueError('Referencia invalida') from exc

        now = datetime.now()
        payload.update({
            'kind': utility_type,
            'utilidad': utility_type,
            'referencia_id': referencia_id,
            'estado': 'activa',
            'assigned_at': now.isoformat(timespec='seconds'),
            'expires_at': (now + timedelta(minutes=ttl_minutos)).isoformat(timespec='seconds'),
            'fulfilled_at': None,
            'nota': (data.get('contenido') or '').strip()
        })
        return json.dumps(payload, ensure_ascii=False)

    def create_qr(self, data):
        utilidad_tipo = (data.get('utilidad_tipo') or '').strip().lower()
        utilidad = utilidad_tipo or (data.get('utilidad') or '').strip()
        contenido = self._build_content(data)
        return self.insert("transalca",
            "INSERT INTO qr_codes (usuario_cedula, tipo, contenido, utilidad) VALUES (%s, %s, %s, %s)",
            (data['usuario_cedula'], data.get('tipo', 'info'), contenido, utilidad))

    def get_user_qrs(self, usuario_cedula):
        return self.fetch_all("transalca",
            "SELECT * FROM qr_codes WHERE usuario_cedula = %s AND estado = 1 ORDER BY created_at DESC",
            (usuario_cedula,))

    def get_by_id(self, qr_id):
        qr = self.fetch_one("transalca", "SELECT * FROM qr_codes WHERE id = %s", (qr_id,))
        if qr:
            content = self._parse_content(qr.get('contenido'))
            qr['utilidad_estado'] = content.get('estado') or ('activa' if qr.get('utilidad') else 'sin_utilidad')
            qr['utilidad_asignada_at'] = content.get('assigned_at')
            qr['utilidad_expires_at'] = content.get('expires_at')
            qr['utilidad_referencia_id'] = content.get('referencia_id')
            qr['contenido_resumen'] = content.get('nota') or qr.get('contenido') or ''
        return qr

    def update_qr(self, qr_id, data):
        existing = self.get_by_id(qr_id)
        contenido = self._build_content(data, existing.get('contenido') if existing else None)
        utilidad_tipo = (data.get('utilidad_tipo') or '').strip().lower()
        utilidad = utilidad_tipo or (data.get('utilidad') or '').strip()
        return self.update("transalca",
            "UPDATE qr_codes SET tipo = %s, contenido = %s, utilidad = %s WHERE id = %s",
            (data.get('tipo', 'info'), contenido, utilidad, qr_id))

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
            content = self._parse_content(qr.get('contenido'))
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (qr['usuario_cedula'],))
            qr['usuario_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'N/A'
            qr['utilidad_estado'] = content.get('estado') or ('activa' if qr.get('utilidad') else 'sin_utilidad')
            qr['utilidad_asignada_at'] = content.get('assigned_at')
            qr['utilidad_expires_at'] = content.get('expires_at')
            qr['utilidad_referencia_id'] = content.get('referencia_id')
            qr['contenido_resumen'] = content.get('nota') or qr.get('contenido') or ''
        return qrs
