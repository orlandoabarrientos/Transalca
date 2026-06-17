from model.connection import Connection
from model.order_model import DETAIL_UNION
from config.validation import SELECT_TAMPER_MESSAGE, ValidationError
import json
from datetime import datetime, timedelta

QR_TIPO_INT = {'info': 0, 'pago': 1, 'promocion': 2, 'servicio': 3}
TIPO_QR_LABEL_SQL = "CASE q.tipo_qr_code WHEN 1 THEN 'pago' WHEN 2 THEN 'promocion' WHEN 3 THEN 'servicio' ELSE 'info' END"


def qr_tipo_to_int(value):
    if isinstance(value, int):
        return value
    return QR_TIPO_INT.get((value or 'info').strip().lower(), 0)


QR_ALIAS = "q.*, q.id_qr_code AS id, " + TIPO_QR_LABEL_SQL + " AS tipo, q.referencia_qr_code AS referencia_id"


class QRModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self):
        rows = self.fetch_all("transalca", "SHOW COLUMNS FROM qr_codes")
        return {r['Field'] for r in rows}

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

    def _reference_id(self, data):
        referencia_id = data.get('referencia_id')
        if referencia_id in ('', None):
            return None
        try:
            return int(referencia_id)
        except Exception as exc:
            raise ValueError('Referencia invalida') from exc

    def _reference_fields(self, data):
        referencia_id = self._reference_id(data)
        utility_type = (data.get('utilidad_tipo') or data.get('utilidad') or '').strip().lower()
        tipo = (data.get('tipo') or 'info').strip().lower()
        fields = {
            'referencia_id': referencia_id,
            'promocion_id': None,
            'servicio_id': None,
            'orden_venta_id': None
        }
        if not referencia_id:
            return fields
        if utility_type == 'promocion' or tipo == 'promocion' or utility_type.startswith('mesa'):
            fields['promocion_id'] = referencia_id
        elif utility_type in ('factura', 'validar_pago', 'pago') or tipo == 'pago':
            fields['orden_venta_id'] = referencia_id
        elif utility_type == 'servicio' or tipo == 'servicio':
            fields['servicio_id'] = referencia_id
        return fields

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

        referencia_id = self._reference_id(data)
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

    def _validate(self, data):
        errors = {}
        tipo = (data.get('tipo') or '').strip().lower()
        if not tipo:
            errors['tipo'] = 'Seleccione un tipo de QR'
        elif tipo not in QR_TIPO_INT:
            errors['tipo'] = SELECT_TAMPER_MESSAGE
        utilidad_tipo = (data.get('utilidad_tipo') or '').strip().lower()
        if not utilidad_tipo:
            errors['utilidad_tipo'] = 'La utilidad es obligatoria'
        elif utilidad_tipo in ('promocion', 'mesa') and not str(data.get('referencia_id') or '').strip():
            errors['referencia_id'] = 'Seleccione una referencia para esta utilidad'
        if errors:
            raise ValidationError(errors)

    def _create_qr(self, data):
        self._validate(data)
        utilidad_tipo = (data.get('utilidad_tipo') or '').strip().lower()
        utilidad = utilidad_tipo or (data.get('utilidad') or '').strip()
        contenido = self._build_content(data)
        fields = self._reference_fields(data)
        columns = self._columns()
        column_map = {'referencia_id': 'referencia_qr_code', 'promocion_id': 'promocion_id',
                      'servicio_id': 'servicio_id', 'orden_venta_id': 'orden_venta_id'}
        extra = [k for k in column_map if column_map[k] in columns]
        names = ['usuario_cedula', 'tipo_qr_code', 'contenido', 'utilidad'] + [column_map[k] for k in extra]
        values = [data['usuario_cedula'], qr_tipo_to_int(data.get('tipo', 'info')), contenido, utilidad] + [fields[k] for k in extra]
        return self.insert("transalca",
            self.build_insert_sql("qr_codes", names, {"qr_codes"}, columns),
            tuple(values))

    def _get_user_qrs(self, usuario_cedula):
        return self.fetch_all("transalca",
            "SELECT " + QR_ALIAS + " FROM qr_codes q WHERE q.usuario_cedula = %s AND q.estado = 1 ORDER BY q.created_at DESC",
            (usuario_cedula,))

    def _get_by_id(self, qr_id):
        qr = self.fetch_one("transalca", "SELECT " + QR_ALIAS + " FROM qr_codes q WHERE q.id_qr_code = %s", (qr_id,))
        if qr:
            content = self._parse_content(qr.get('contenido'))
            qr['utilidad_estado'] = content.get('estado') or ('activa' if qr.get('utilidad') else 'sin_utilidad')
            qr['utilidad_asignada_at'] = content.get('assigned_at')
            qr['utilidad_expires_at'] = content.get('expires_at')
            qr['utilidad_referencia_id'] = content.get('referencia_id')
            if qr.get('utilidad'):
                qr['contenido_resumen'] = content.get('nota') or ''
            else:
                qr['contenido_resumen'] = qr.get('contenido') or ''
        return qr

    def _update_qr(self, qr_id, data):
        self._validate(data)
        existing = self._get_by_id(qr_id)
        contenido = self._build_content(data, existing.get('contenido') if existing else None)
        utilidad_tipo = (data.get('utilidad_tipo') or '').strip().lower()
        utilidad = utilidad_tipo or (data.get('utilidad') or '').strip()
        fields = self._reference_fields(data)
        columns = self._columns()
        column_map = {'referencia_id': 'referencia_qr_code', 'promocion_id': 'promocion_id',
                      'servicio_id': 'servicio_id', 'orden_venta_id': 'orden_venta_id'}
        extra = [k for k in column_map if column_map[k] in columns]
        update_columns = ['tipo_qr_code', 'contenido', 'utilidad'] + [column_map[k] for k in extra]
        values = [qr_tipo_to_int(data.get('tipo', 'info')), contenido, utilidad] + [fields[k] for k in extra] + [qr_id]
        return self.update("transalca",
            self.build_update_by_key_sql("qr_codes", update_columns, "id_qr_code", {"qr_codes"}, columns),
            tuple(values))

    def _delete_qr(self, qr_id):
        return self.update("transalca",
            "UPDATE qr_codes SET estado = 0 WHERE id_qr_code = %s", (qr_id,))

    def _soft_delete(self, qr_id):
        return self._delete_qr(qr_id)

    def _get_qr_data(self, qr_id):
        qr = self._get_by_id(qr_id)
        if not qr:
            return None
        user = self.fetch_one("mantenimiento",
            "SELECT nombre, apellido, cedula, email, telefono FROM usuarios WHERE cedula = %s", (qr['usuario_cedula'],))
        result = {"qr": qr, "usuario": user}
        if qr['tipo'] == 'promocion':
            try:
                content = json.loads(qr['contenido'])
                card = self.fetch_one("transalca",
                    "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.nombre_promocion as promo_nombre, p.puntos_requeridos, p.recompensa_promocion as recompensa "
                    "FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE tf.id_tarjeta_fidelidad = %s",
                    (content.get('tarjeta_id'),))
                result['tarjeta'] = card
            except (json.JSONDecodeError, TypeError):
                pass
        elif qr['tipo'] == 'servicio':
            try:
                content = json.loads(qr['contenido'])
                order = self.fetch_one("transalca",
                    "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
                    "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
                    "WHERE ov.id_orden_venta = %s", (content.get('orden_id'),))
                if order:
                    order['detalles'] = self.fetch_all("transalca",
                        "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre_producto ELSE s.nombre_servicio END as item_nombre "
                        "FROM " + DETAIL_UNION + " "
                        "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
                        "LEFT JOIN servicios s ON d.servicio_id = s.id_servicio WHERE d.orden_id = %s",
                        (order['id'],))
                result['orden'] = order
            except (json.JSONDecodeError, TypeError):
                pass
        return result

    def _get_all_qrs(self):
        qrs = self.fetch_all("transalca", "SELECT " + QR_ALIAS + " FROM qr_codes q WHERE q.estado = 1 ORDER BY q.created_at DESC")
        for qr in qrs:
            content = self._parse_content(qr.get('contenido'))
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE cedula = %s", (qr['usuario_cedula'],))
            qr['usuario_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'N/A'
            qr['utilidad_estado'] = content.get('estado') or ('activa' if qr.get('utilidad') else 'sin_utilidad')
            qr['utilidad_asignada_at'] = content.get('assigned_at')
            qr['utilidad_expires_at'] = content.get('expires_at')
            qr['utilidad_referencia_id'] = content.get('referencia_id')
            if qr.get('utilidad'):
                qr['contenido_resumen'] = content.get('nota') or ''
            else:
                qr['contenido_resumen'] = qr.get('contenido') or ''
        return qrs

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "validate": self._validate,
            "create_qr": self._create_qr,
            "get_user_qrs": self._get_user_qrs,
            "get_by_id": self._get_by_id,
            "update_qr": self._update_qr,
            "delete_qr": self._delete_qr,
            "soft_delete": self._soft_delete,
            "get_qr_data": self._get_qr_data,
            "get_all_qrs": self._get_all_qrs,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
