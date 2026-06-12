import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from model.connection import Connection


class ScannerModel(Connection):
    def __init__(self):
        super().__init__()

    def _qr_columns(self):
        rows = self.fetch_all("transalca", "SHOW COLUMNS FROM qr_codes")
        return {r['Field'] for r in rows}

    def _parse_content(self, content):
        if not content:
            return {}
        try:
            if isinstance(content, dict):
                return content
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _parse_datetime(self, value):
        if not value:
            return None
        try:
            text = str(value).replace('Z', '+00:00')
            return datetime.fromisoformat(text)
        except Exception:
            return None

    def _save_content(self, qr_id, content):
        self.update("transalca", "UPDATE qr_codes SET contenido = %s WHERE id_qr_code = %s",
            (json.dumps(content, ensure_ascii=False), qr_id))

    def _get_utility_state(self, qr):
        content = self._parse_content(qr.get('contenido'))
        utility = (content.get('utilidad') or qr.get('utilidad') or '').strip().lower()
        assigned_at = self._parse_datetime(content.get('assigned_at'))
        expires_at = self._parse_datetime(content.get('expires_at'))
        state = (content.get('estado') or '').strip().lower()
        now = datetime.now(expires_at.tzinfo) if expires_at and getattr(expires_at, 'tzinfo', None) else datetime.now()

        if not utility or utility in ('info', 'sin_utilidad', 'none'):
            return {
                'active': False,
                'message': 'Este QR no tiene nada todavia, habla con el administrador',
                'utility': utility,
                'content': content
            }

        if state in ('cumplida', 'cumplido', 'usado', 'used'):
            return {
                'active': False,
                'message': 'Este QR ya fue utilizado y no esta disponible.',
                'utility': utility,
                'content': content
            }

        if expires_at and now > expires_at:
            content['estado'] = 'expirada'
            content['expired_at'] = now.isoformat(timespec='seconds')
            self._save_content(qr['id'], content)
            return {
                'active': False,
                'message': 'Este QR ya no esta disponible (tiempo agotado).',
                'utility': utility,
                'content': content
            }

        if assigned_at and not expires_at and now > assigned_at + timedelta(minutes=10):
            content['estado'] = 'expirada'
            content['expired_at'] = now.isoformat(timespec='seconds')
            self._save_content(qr['id'], content)
            return {
                'active': False,
                'message': 'Este QR ya no esta disponible (tiempo agotado).',
                'utility': utility,
                'content': content
            }

        if content.get('estado') != 'activa':
            content['estado'] = 'activa'
            self._save_content(qr['id'], content)

        return {
            'active': True,
            'message': 'Utilidad activa',
            'utility': utility,
            'content': content,
            'assigned_at': content.get('assigned_at'),
            'expires_at': content.get('expires_at'),
            'reference_id': content.get('referencia_id')
        }

    def _mark_completed(self, qr):
        content = self._parse_content(qr.get('contenido'))
        content['estado'] = 'cumplida'
        content['fulfilled_at'] = datetime.now().isoformat(timespec='seconds')
        self._save_content(qr['id'], content)

    def _is_table_qr(self, qr):
        utilidad = (qr.get('utilidad') or '').strip().lower()
        return utilidad.startswith('mesa:')

    def _mesa_codigo(self, qr):
        utilidad = (qr.get('utilidad') or '').strip()
        if ':' not in utilidad:
            return ''
        return utilidad.split(':', 1)[1]

    def _get_active_qr_by_id(self, qr_id):
        return self.fetch_one("transalca", "SELECT q.*, q.tipo_qr_code AS tipo, q.referencia_qr_code AS referencia_id FROM qr_codes q WHERE q.id_qr_code = %s AND q.estado = 1", (qr_id,))

    def _resolve_qr_from_raw(self, raw_text):
        raw = (raw_text or '').strip()
        if not raw:
            return None, 'Debe indicar un codigo QR'

        qr_id = None

        if raw.isdigit():
            qr_id = int(raw)
        else:
            try:
                parsed = urlparse(raw)
                path = (parsed.path or '').lower()
                params = parse_qs(parsed.query or '')

                if '/scanner' in path and params.get('qr', [''])[0].isdigit():
                    qr_id = int(params['qr'][0])
                elif '/client/qr_scan' in path and params.get('id', [''])[0].isdigit():
                    qr_id = int(params['id'][0])
            except Exception:
                qr_id = None

            if qr_id is None:
                match_scanner = re.search(r'/scanner\?qr=(\d+)', raw, re.IGNORECASE)
                match_qr_scan = re.search(r'/client/qr_scan\?id=(\d+)', raw, re.IGNORECASE)
                if match_scanner:
                    qr_id = int(match_scanner.group(1))
                elif match_qr_scan:
                    qr_id = int(match_qr_scan.group(1))

        if qr_id is None:
            return None, 'El codigo escaneado no pertenece al sistema'

        qr = self._get_active_qr_by_id(qr_id)
        if not qr:
            return None, 'QR no encontrado o inactivo'

        return qr, None

    def _get_client_profile(self, cliente_cedula):
        profile = self.fetch_one("mantenimiento",
            "SELECT cedula, nombre, apellido, email, telefono FROM usuarios WHERE cedula = %s", (cliente_cedula,))
        if profile:
            return profile
        return self.fetch_one("transalca",
            "SELECT identificador_cliente AS cedula, nombre_cliente AS nombre, '' AS apellido, correo_cliente AS email, telefono_cliente AS telefono FROM cliente WHERE identificador_cliente = %s", (cliente_cedula,))

    def _get_order_full(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE ov.id_orden_venta = %s", (order_id,))
        if not order:
            return None

        order['detalles'] = self.fetch_all("transalca",
            "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre_producto ELSE s.nombre_servicio END as item_nombre "
            "FROM ((SELECT id_detalle_orden_venta_producto AS id, orden_id, producto_codigo, 0 AS servicio_id, 'producto' AS tipo, cantidad_detalle_orden_venta_producto AS cantidad, precio_unitario_producto AS precio_unitario, cantidad_detalle_orden_venta_producto * precio_unitario_producto AS subtotal FROM detalle_orden_venta_productos) "
            "UNION ALL "
            "(SELECT id_detalle_orden_venta_servicio AS id, orden_id, 'SIN_PRODUCTO' AS producto_codigo, servicio_id, 'servicio' AS tipo, cantidad_detalle_orden_venta_servicio AS cantidad, precio_unitario_servicio AS precio_unitario, cantidad_detalle_orden_venta_servicio * precio_unitario_servicio AS subtotal FROM detalle_orden_venta_servicios)) d "
            "LEFT JOIN productos p ON d.producto_codigo = p.codigo "
            "LEFT JOIN servicios s ON d.servicio_id = s.id_servicio WHERE d.orden_id = %s",
            (order_id,))
        order['cliente'] = self._get_client_profile(order['cliente_cedula'])
        return order

    def _get_latest_order_full(self, cliente_cedula):
        order = self.fetch_one("transalca",
            "SELECT id_orden_venta AS id FROM ordenes_venta WHERE cliente_cedula = %s ORDER BY fecha_orden_venta DESC, id_orden_venta DESC LIMIT 1",
            (cliente_cedula,))
        if not order:
            return None
        return self._get_order_full(order['id'])

    def _ensure_invoice_qr(self, order_id):
        order = self.fetch_one("transalca", "SELECT id_orden_venta AS id, cliente_cedula FROM ordenes_venta WHERE id_orden_venta = %s", (order_id,))
        if not order:
            return None

        columns = self._qr_columns()
        if "orden_venta_id" in columns:
            existing = self.fetch_one("transalca",
                "SELECT q.*, q.tipo_qr_code AS tipo, q.referencia_qr_code AS referencia_id FROM qr_codes q WHERE (q.orden_venta_id = %s OR q.referencia_qr_code = %s) AND q.utilidad = 'factura' AND q.estado = 1 ORDER BY q.id_qr_code DESC LIMIT 1",
                (order_id, order_id))
        else:
            existing = self.fetch_one("transalca",
                "SELECT q.*, q.tipo_qr_code AS tipo, q.referencia_qr_code AS referencia_id FROM qr_codes q WHERE q.referencia_qr_code = %s AND q.utilidad = 'factura' AND q.estado = 1 ORDER BY q.id_qr_code DESC LIMIT 1",
                (order_id,))
        if existing:
            return existing

        payload = json.dumps({"kind": "factura", "orden_id": order_id})

        try:
            if "orden_venta_id" in columns:
                qr_id = self.insert("transalca",
                    "INSERT INTO qr_codes (usuario_cedula, tipo_qr_code, contenido, utilidad, referencia_qr_code, orden_venta_id) VALUES (%s, 'pago', %s, 'factura', %s, %s)",
                    (order['cliente_cedula'], payload, order_id, order_id))
            else:
                qr_id = self.insert("transalca",
                    "INSERT INTO qr_codes (usuario_cedula, tipo_qr_code, contenido, utilidad, referencia_qr_code) VALUES (%s, 'pago', %s, 'factura', %s)",
                    (order['cliente_cedula'], payload, order_id))
        except Exception:
            if "orden_venta_id" in columns:
                return self.fetch_one("transalca",
                    "SELECT q.*, q.tipo_qr_code AS tipo, q.referencia_qr_code AS referencia_id FROM qr_codes q WHERE (q.orden_venta_id = %s OR q.referencia_qr_code = %s) AND q.utilidad = 'factura' AND q.estado = 1 ORDER BY q.id_qr_code DESC LIMIT 1",
                    (order_id, order_id))
            return self.fetch_one("transalca",
                "SELECT q.*, q.tipo_qr_code AS tipo, q.referencia_qr_code AS referencia_id FROM qr_codes q WHERE q.referencia_qr_code = %s AND q.utilidad = 'factura' AND q.estado = 1 ORDER BY q.id_qr_code DESC LIMIT 1",
                (order_id,))

        return self._get_active_qr_by_id(qr_id)

    def _get_active_promotions(self):
        return self.fetch_all("transalca",
            "SELECT id_promocion AS id, nombre_promocion AS nombre, puntos_requeridos, recompensa_promocion AS recompensa FROM promociones WHERE estado = 1 AND (fecha_fin_promocion IS NULL OR fecha_fin_promocion >= CURDATE()) ORDER BY nombre_promocion")

    def _get_table_qrs(self):
        if "promocion_id" in self._qr_columns():
            rows = self.fetch_all("transalca",
                "SELECT q.*, q.tipo_qr_code AS tipo, q.referencia_qr_code AS referencia_id, p.nombre_promocion as promocion_nombre FROM qr_codes q LEFT JOIN promociones p ON COALESCE(q.promocion_id, q.referencia_qr_code) = p.id_promocion WHERE q.estado = 1 AND q.utilidad LIKE 'mesa:%%' ORDER BY q.created_at DESC")
        else:
            rows = self.fetch_all("transalca",
                "SELECT q.*, q.tipo_qr_code AS tipo, q.referencia_qr_code AS referencia_id, p.nombre_promocion as promocion_nombre FROM qr_codes q LEFT JOIN promociones p ON q.referencia_qr_code = p.id_promocion WHERE q.estado = 1 AND q.utilidad LIKE 'mesa:%%' ORDER BY q.created_at DESC")

        for row in rows:
            content = self._parse_content(row.get('contenido'))
            row['codigo_mesa'] = self._mesa_codigo(row)
            row['accion'] = content.get('accion', 'sin_accion')
            row['promocion_id'] = row.get('referencia_id') or content.get('promocion_id')

        return rows

    def _create_table_qr(self, usuario_cedula, codigo_mesa):
        code = re.sub(r'[^A-Za-z0-9_-]', '', (codigo_mesa or '').upper())
        if len(code) < 2:
            raise ValueError('Codigo de mesa invalido')

        utilidad = f"mesa:{code}"
        existing = self.fetch_one("transalca",
            "SELECT id_qr_code AS id FROM qr_codes WHERE utilidad = %s AND estado = 1 ORDER BY id_qr_code DESC LIMIT 1",
            (utilidad,))
        if existing:
            return {'id': existing['id'], 'created': False}

        content = json.dumps({"kind": "mesa", "accion": "sin_accion", "promocion_id": None})
        qr_id = self.insert("transalca",
            "INSERT INTO qr_codes (usuario_cedula, tipo_qr_code, contenido, utilidad) VALUES (%s, 'info', %s, %s)",
            (usuario_cedula, content, utilidad))

        return {'id': qr_id, 'created': True}

    def _set_table_qr_action(self, qr_id, accion, promocion_id=None):
        qr = self._get_active_qr_by_id(qr_id)
        if not qr or not self._is_table_qr(qr):
            raise ValueError('QR de mesa no encontrado')

        action = (accion or '').strip().lower()
        allowed = {'sin_accion', 'promocion', 'validar_pago'}
        if action not in allowed:
            raise ValueError('Accion invalida')

        promo_id = None
        if action == 'promocion':
            try:
                promo_id = int(promocion_id)
            except Exception:
                raise ValueError('Debe seleccionar una promocion valida')

            promo = self.fetch_one("transalca",
                "SELECT id_promocion AS id FROM promociones WHERE id_promocion = %s AND estado = 1", (promo_id,))
            if not promo:
                raise ValueError('Promocion no encontrada o inactiva')

        content = self._parse_content(qr.get('contenido'))
        content['kind'] = 'mesa'
        content['accion'] = action
        content['promocion_id'] = promo_id

        if "promocion_id" in self._qr_columns():
            self.update("transalca",
                "UPDATE qr_codes SET contenido = %s, referencia_qr_code = %s, promocion_id = %s WHERE id_qr_code = %s",
                (json.dumps(content), promo_id, promo_id, qr_id))
        else:
            self.update("transalca",
                "UPDATE qr_codes SET contenido = %s, referencia_qr_code = %s WHERE id_qr_code = %s",
                (json.dumps(content), promo_id, qr_id))

        return self._get_active_qr_by_id(qr_id)

    def _assign_card_to_client(self, cliente_cedula, promocion_id):
        promo = self.fetch_one("transalca",
            "SELECT id_promocion AS id, nombre_promocion AS nombre, puntos_requeridos, recompensa_promocion AS recompensa FROM promociones WHERE id_promocion = %s AND estado = 1",
            (promocion_id,))
        if not promo:
            return None


        client = self.fetch_one("transalca", "SELECT id_cliente FROM cliente WHERE identificador_cliente = %s", (cliente_cedula,))
        if not client:
            user = self.fetch_one("mantenimiento", "SELECT id, nombre, apellido, email, telefono, direccion FROM usuarios WHERE cedula = %s", (cliente_cedula,))
            if user:
                nombre_completo = (str(user['nombre'] or '') + ' ' + str(user['apellido'] or '')).strip()
                cliente_id = self.insert("transalca",
                    "INSERT INTO cliente (nombre_cliente, correo_cliente, identificador_cliente, telefono_cliente, direccion_cliente, tipo_cliente) VALUES (%s, %s, %s, %s, %s, 'natural')",
                    (nombre_completo, user['email'], cliente_cedula, user.get('telefono') or '', user.get('direccion') or ''))
                self.insert("transalca",
                    "INSERT INTO cliente_natural (id_cliente, usuario_id, origen_registro) VALUES (%s, %s, 'cliente')",
                    (cliente_id, user['id']))

        card = self.fetch_one("transalca",
            "SELECT id_tarjeta_fidelidad AS id, puntos_acumulados FROM tarjeta_fidelidad WHERE cliente_cedula = %s AND promocion_id = %s AND canjeada = 0 ORDER BY id_tarjeta_fidelidad DESC LIMIT 1",
            (cliente_cedula, promocion_id))

        if card:
            card_id = card['id']
            new_points = min(card['puntos_acumulados'] + 1, promo['puntos_requeridos'])
            self.update("transalca",
                "UPDATE tarjeta_fidelidad SET puntos_acumulados = %s WHERE id_tarjeta_fidelidad = %s",
                (new_points, card_id))
            self.insert("transalca",
                "INSERT INTO historial_puntos (tarjeta_id, puntos, tipo_historial_punto, descripcion_historial_punto) VALUES (%s, 1, 'suma', 'Punto acumulado via escaneo QR')",
                (card_id,))
        else:
            card_id = self.insert("transalca",
                "INSERT INTO tarjeta_fidelidad (cliente_cedula, promocion_id, puntos_acumulados) VALUES (%s, %s, 1)",
                (cliente_cedula, promocion_id))
            self.insert("transalca",
                "INSERT INTO historial_puntos (tarjeta_id, puntos, tipo_historial_punto, descripcion_historial_punto) VALUES (%s, 1, 'suma', 'Registro de tarjeta y primer punto via escaneo QR')",
                (card_id,))

        return self.fetch_one("transalca",
            "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.nombre_promocion as promo_nombre, p.puntos_requeridos, p.recompensa_promocion as recompensa FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE tf.id_tarjeta_fidelidad = %s",
            (card_id,))

    def _process_scan_for_employee(self, qr):
        content = self._parse_content(qr.get('contenido'))
        state = self._get_utility_state(qr)

        if not state['active']:
            return {
                'mode': 'qr_sin_utilidad',
                'message': state['message'],
                'qr': {
                    'id': qr.get('id'),
                    'tipo': qr.get('tipo'),
                    'utilidad': qr.get('utilidad')
                }
            }

        utility = state['utility']
        content = state['content']

        if utility.startswith('mesa') or self._is_table_qr(qr):
            return {
                'mode': 'mesa_info',
                'message': 'QR de mesa detectado',
                'codigo_mesa': self._mesa_codigo(qr),
                'accion': content.get('accion', 'sin_accion'),
                'promocion_id': qr.get('referencia_id') or content.get('promocion_id')
            }

        if utility in ('validar_pago', 'factura', 'pago') or content.get('kind') == 'factura' or qr.get('tipo') == 'pago':
            order_id = state.get('reference_id') or qr.get('referencia_id') or content.get('orden_id')
            if not order_id:
                return {'mode': 'factura_invalida', 'message': 'Factura sin referencia valida'}

            order = self._get_order_full(order_id)
            if not order:
                return {'mode': 'factura_invalida', 'message': 'La factura no existe en el sistema'}

            self._mark_completed(qr)

            return {
                'mode': 'factura_validada',
                'message': 'Factura valida',
                'order': order
            }

        if utility == 'promocion':
            promo_id = state.get('reference_id') or qr.get('referencia_id') or content.get('promocion_id')
            promo = self.fetch_one("transalca",
                "SELECT id_promocion AS id, nombre_promocion AS nombre, puntos_requeridos, recompensa_promocion AS recompensa FROM promociones WHERE id_promocion = %s AND estado = 1",
                (promo_id,)) if promo_id else None
            return {
                'mode': 'promocion_info',
                'message': 'Promocion lista para aplicar',
                'promocion': promo
            }

        return {
            'mode': 'qr_info',
            'message': 'QR leido sin accion especial',
            'qr': {
                'id': qr.get('id'),
                'tipo': qr.get('tipo'),
                'utilidad': qr.get('utilidad')
            }
        }

    def _process_scan_for_client(self, qr, cliente_cedula):
        content = self._parse_content(qr.get('contenido'))
        state = self._get_utility_state(qr)

        if not state['active']:
            return {
                'mode': 'qr_sin_utilidad',
                'message': state['message'],
                'qr': {
                    'id': qr.get('id'),
                    'tipo': qr.get('tipo'),
                    'utilidad': qr.get('utilidad')
                }
            }

        utility = state['utility']
        content = state['content']

        if utility.startswith('mesa') or self._is_table_qr(qr):
            action = content.get('accion', 'sin_accion')
            if action == 'promocion':
                promo_id = state.get('reference_id') or qr.get('referencia_id') or content.get('promocion_id')
                card = self._assign_card_to_client(cliente_cedula, promo_id)
                if not card:
                    return {
                        'mode': 'mesa_sin_accion',
                        'message': 'La promocion asociada ya no esta disponible',
                        'codigo_mesa': self._mesa_codigo(qr)
                    }
                self._mark_completed(qr)
                return {
                    'mode': 'mesa_promocion_aplicada',
                    'message': 'Promocion registrada en su fidelizacion',
                    'codigo_mesa': self._mesa_codigo(qr),
                    'card': card
                }

            if action == 'validar_pago':
                latest_order = self._get_latest_order_full(cliente_cedula)
                return {
                    'mode': 'mesa_validar_pago',
                    'message': 'Datos de su ultima factura listos para validacion',
                    'codigo_mesa': self._mesa_codigo(qr),
                    'order': latest_order
                }

            return {
                'mode': 'mesa_sin_accion',
                'message': 'Este QR de mesa no tiene accion asignada',
                'codigo_mesa': self._mesa_codigo(qr)
            }

        if utility == 'validar_pago':
            order_id = state.get('reference_id') or qr.get('referencia_id') or content.get('orden_id')
            if not order_id:
                return {
                    'mode': 'validar_pago_redirect',
                    'message': 'Redirigiendo a sus pedidos para validación',
                    'qr_id': qr['id']
                }

        if utility in ('validar_pago', 'factura', 'pago') or content.get('kind') == 'factura':
            order_id = state.get('reference_id') or qr.get('referencia_id') or content.get('orden_id')
            order = self._get_order_full(order_id) if order_id else None
            if not order:
                return {'mode': 'factura_invalida', 'message': 'Factura no encontrada'}
            if order.get('cliente_cedula') != cliente_cedula:
                return {'mode': 'factura_restringida', 'message': 'Esta factura pertenece a otro cliente'}
            return {'mode': 'factura_cliente', 'message': 'Factura cargada', 'order': order}

        if utility == 'promocion' or qr.get('tipo') == 'promocion':
            promo_id = state.get('reference_id') or qr.get('referencia_id') or content.get('promocion_id')
            if promo_id:
                card = self._assign_card_to_client(cliente_cedula, promo_id)
                if card:
                    self._mark_completed(qr)
                    return {
                        'mode': 'promocion_directa_aplicada',
                        'message': 'Promocion aplicada en su fidelizacion',
                        'card': card
                    }

        return {
            'mode': 'qr_info',
            'message': 'QR leido sin accion especial',
            'qr': {
                'id': qr.get('id'),
                'tipo': qr.get('tipo'),
                'utilidad': qr.get('utilidad')
            }
        }

    def _get_order_basic(self, orden_id):
        return self.fetch_one("transalca", "SELECT ov.*, ov.id_orden_venta AS id FROM ordenes_venta ov WHERE ov.id_orden_venta = %s", (orden_id,))

    def _latest_comprobante(self, orden_id):
        return self.fetch_one("transalca",
            "SELECT id_comprobante_pago FROM comprobantes_pago WHERE orden_venta_id = %s ORDER BY id_comprobante_pago DESC LIMIT 1",
            (orden_id,))

    def _pending_validation_for_order(self, orden_id):
        return self.fetch_one("transalca",
            "SELECT sv.id_validacion AS id FROM solicitudes_validacion sv "
            "INNER JOIN comprobantes_pago cp ON cp.id_comprobante_pago = sv.comprobante_pago_id "
            "WHERE cp.orden_venta_id = %s AND sv.estado_validacion = 'pendiente'",
            (orden_id,))

    def _create_validation_request(self, tipo, comprobante_id):
        return self.insert("transalca",
            "INSERT INTO solicitudes_validacion (tipo, comprobante_pago_id, estado_validacion) VALUES (%s, %s, 'pendiente')",
            (tipo, comprobante_id))

    def _get_pending_validations(self):
        return self.fetch_all("transalca",
            "SELECT sv.*, sv.id_validacion AS id, sv.estado_validacion AS estado, cp.orden_venta_id, cp.imagen_url "
            "FROM solicitudes_validacion sv "
            "INNER JOIN comprobantes_pago cp ON cp.id_comprobante_pago = sv.comprobante_pago_id "
            "WHERE sv.estado_validacion = 'pendiente' AND sv.alerta_vista = 0 ORDER BY sv.created_at ASC")

    def _mark_alert_seen(self, solicitud_id):
        return self.update("transalca",
            "UPDATE solicitudes_validacion SET alerta_vista = 1 WHERE id_validacion = %s", (solicitud_id,))

    def _get_validation_by_id(self, solicitud_id):
        return self.fetch_one("transalca",
            "SELECT sv.*, sv.id_validacion AS id, sv.estado_validacion AS estado, cp.orden_venta_id "
            "FROM solicitudes_validacion sv "
            "INNER JOIN comprobantes_pago cp ON cp.id_comprobante_pago = sv.comprobante_pago_id "
            "WHERE sv.id_validacion = %s", (solicitud_id,))

    def _set_validation_status(self, solicitud_id, estado):
        return self.update("transalca", "UPDATE solicitudes_validacion SET estado_validacion = %s WHERE id_validacion = %s", (estado, solicitud_id))

    def _order_client_cedula(self, orden_id):
        return self.fetch_one("transalca", "SELECT cliente_cedula FROM ordenes_venta WHERE id_orden_venta = %s", (orden_id,))

    def _set_order_status(self, orden_id, estado):
        return self.update("transalca", "UPDATE ordenes_venta SET estado = %s WHERE id_orden_venta = %s", (estado, orden_id))

    def _set_comprobante_status(self, comprobante_id, estado):
        return self.update("transalca", "UPDATE comprobantes_pago SET estado = %s WHERE id_comprobante_pago = %s", (estado, comprobante_id))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_active_qr_by_id": self._get_active_qr_by_id,
            "resolve_qr_from_raw": self._resolve_qr_from_raw,
            "get_order_full": self._get_order_full,
            "get_latest_order_full": self._get_latest_order_full,
            "ensure_invoice_qr": self._ensure_invoice_qr,
            "get_active_promotions": self._get_active_promotions,
            "get_table_qrs": self._get_table_qrs,
            "create_table_qr": self._create_table_qr,
            "set_table_qr_action": self._set_table_qr_action,
            "assign_card_to_client": self._assign_card_to_client,
            "process_scan_for_employee": self._process_scan_for_employee,
            "process_scan_for_client": self._process_scan_for_client,
            "get_order_basic": self._get_order_basic,
            "latest_comprobante": self._latest_comprobante,
            "pending_validation_for_order": self._pending_validation_for_order,
            "create_validation_request": self._create_validation_request,
            "get_pending_validations": self._get_pending_validations,
            "mark_alert_seen": self._mark_alert_seen,
            "get_validation_by_id": self._get_validation_by_id,
            "set_validation_status": self._set_validation_status,
            "order_client_cedula": self._order_client_cedula,
            "set_order_status": self._set_order_status,
            "set_comprobante_status": self._set_comprobante_status,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
