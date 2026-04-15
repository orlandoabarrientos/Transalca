import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from model.connection import Connection


class ScannerModel(Connection):
    def __init__(self):
        super().__init__()

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
        self.update("transalca", "UPDATE qr_codes SET contenido = %s WHERE id = %s",
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
                'message': 'La utilidad de este QR ya fue cumplida',
                'utility': utility,
                'content': content
            }

        if expires_at and now > expires_at:
            content['estado'] = 'expirada'
            content['expired_at'] = now.isoformat(timespec='seconds')
            self._save_content(qr['id'], content)
            return {
                'active': False,
                'message': 'La utilidad de este QR ya expiro',
                'utility': utility,
                'content': content
            }

        if assigned_at and not expires_at and now > assigned_at + timedelta(minutes=10):
            content['estado'] = 'expirada'
            content['expired_at'] = now.isoformat(timespec='seconds')
            self._save_content(qr['id'], content)
            return {
                'active': False,
                'message': 'La utilidad de este QR ya expiro',
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

    def get_active_qr_by_id(self, qr_id):
        return self.fetch_one("transalca", "SELECT * FROM qr_codes WHERE id = %s AND estado = 1", (qr_id,))

    def resolve_qr_from_raw(self, raw_text):
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

        qr = self.get_active_qr_by_id(qr_id)
        if not qr:
            return None, 'QR no encontrado o inactivo'

        return qr, None

    def _get_client_profile(self, cliente_cedula):
        profile = self.fetch_one("mantenimiento",
            "SELECT cedula, nombre, apellido, email, telefono FROM usuarios WHERE cedula = %s", (cliente_cedula,))
        if profile:
            return profile
        return self.fetch_one("transalca",
            "SELECT cedula, nombre, apellido, email FROM usuarios WHERE cedula = %s", (cliente_cedula,))

    def get_order_full(self, order_id):
        order = self.fetch_one("transalca", "SELECT * FROM ordenes_venta WHERE id = %s", (order_id,))
        if not order:
            return None

        order['detalles'] = self.fetch_all("transalca",
            "SELECT d.*, CASE WHEN d.tipo = 'producto' THEN p.nombre ELSE s.nombre END as item_nombre FROM detalle_orden_venta d LEFT JOIN productos p ON d.producto_codigo = p.codigo LEFT JOIN servicios s ON d.servicio_id = s.id WHERE d.orden_id = %s",
            (order_id,))
        order['cliente'] = self._get_client_profile(order['cliente_cedula'])
        return order

    def get_latest_order_full(self, cliente_cedula):
        order = self.fetch_one("transalca",
            "SELECT * FROM ordenes_venta WHERE cliente_cedula = %s ORDER BY fecha DESC, id DESC LIMIT 1",
            (cliente_cedula,))
        if not order:
            return None
        return self.get_order_full(order['id'])

    def ensure_invoice_qr(self, order_id):
        order = self.fetch_one("transalca", "SELECT id, cliente_cedula FROM ordenes_venta WHERE id = %s", (order_id,))
        if not order:
            return None

        existing = self.fetch_one("transalca",
            "SELECT * FROM qr_codes WHERE referencia_id = %s AND utilidad = 'factura' AND estado = 1 ORDER BY id DESC LIMIT 1",
            (order_id,))
        if existing:
            return existing

        payload = json.dumps({"kind": "factura", "orden_id": order_id})

        try:
            qr_id = self.insert("transalca",
                "INSERT INTO qr_codes (usuario_cedula, tipo, contenido, utilidad, referencia_id) VALUES (%s, 'pago', %s, 'factura', %s)",
                (order['cliente_cedula'], payload, order_id))
        except Exception:
            return self.fetch_one("transalca",
                "SELECT * FROM qr_codes WHERE referencia_id = %s AND utilidad = 'factura' AND estado = 1 ORDER BY id DESC LIMIT 1",
                (order_id,))

        return self.get_active_qr_by_id(qr_id)

    def get_active_promotions(self):
        return self.fetch_all("transalca",
            "SELECT id, nombre, puntos_requeridos, recompensa FROM promociones WHERE estado = 1 AND (fecha_fin IS NULL OR fecha_fin >= CURDATE()) ORDER BY nombre")

    def get_table_qrs(self):
        rows = self.fetch_all("transalca",
            "SELECT q.*, p.nombre as promocion_nombre FROM qr_codes q LEFT JOIN promociones p ON q.referencia_id = p.id WHERE q.estado = 1 AND q.utilidad LIKE 'mesa:%%' ORDER BY q.created_at DESC")

        for row in rows:
            content = self._parse_content(row.get('contenido'))
            row['codigo_mesa'] = self._mesa_codigo(row)
            row['accion'] = content.get('accion', 'sin_accion')
            row['promocion_id'] = row.get('referencia_id') or content.get('promocion_id')

        return rows

    def create_table_qr(self, usuario_cedula, codigo_mesa):
        code = re.sub(r'[^A-Za-z0-9_-]', '', (codigo_mesa or '').upper())
        if len(code) < 2:
            raise ValueError('Codigo de mesa invalido')

        utilidad = f"mesa:{code}"
        existing = self.fetch_one("transalca",
            "SELECT id FROM qr_codes WHERE utilidad = %s AND estado = 1 ORDER BY id DESC LIMIT 1",
            (utilidad,))
        if existing:
            return {'id': existing['id'], 'created': False}

        content = json.dumps({"kind": "mesa", "accion": "sin_accion", "promocion_id": None})
        qr_id = self.insert("transalca",
            "INSERT INTO qr_codes (usuario_cedula, tipo, contenido, utilidad) VALUES (%s, 'info', %s, %s)",
            (usuario_cedula, content, utilidad))

        return {'id': qr_id, 'created': True}

    def set_table_qr_action(self, qr_id, accion, promocion_id=None):
        qr = self.get_active_qr_by_id(qr_id)
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
                "SELECT id FROM promociones WHERE id = %s AND estado = 1", (promo_id,))
            if not promo:
                raise ValueError('Promocion no encontrada o inactiva')

        content = self._parse_content(qr.get('contenido'))
        content['kind'] = 'mesa'
        content['accion'] = action
        content['promocion_id'] = promo_id

        self.update("transalca",
            "UPDATE qr_codes SET contenido = %s, referencia_id = %s WHERE id = %s",
            (json.dumps(content), promo_id, qr_id))

        return self.get_active_qr_by_id(qr_id)

    def assign_card_to_client(self, cliente_cedula, promocion_id):
        promo = self.fetch_one("transalca",
            "SELECT id, nombre, puntos_requeridos, recompensa FROM promociones WHERE id = %s AND estado = 1",
            (promocion_id,))
        if not promo:
            return None

        card = self.fetch_one("transalca",
            "SELECT id FROM tarjeta_fidelidad WHERE cliente_cedula = %s AND promocion_id = %s AND canjeada = 0 ORDER BY id DESC LIMIT 1",
            (cliente_cedula, promocion_id))

        if card:
            card_id = card['id']
        else:
            card_id = self.insert("transalca",
                "INSERT INTO tarjeta_fidelidad (cliente_cedula, promocion_id) VALUES (%s, %s)",
                (cliente_cedula, promocion_id))

        return self.fetch_one("transalca",
            "SELECT tf.*, p.nombre as promo_nombre, p.puntos_requeridos, p.recompensa FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id WHERE tf.id = %s",
            (card_id,))

    def process_scan_for_employee(self, qr):
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

            order = self.get_order_full(order_id)
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
                "SELECT id, nombre, puntos_requeridos, recompensa FROM promociones WHERE id = %s AND estado = 1",
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

    def process_scan_for_client(self, qr, cliente_cedula):
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
                card = self.assign_card_to_client(cliente_cedula, promo_id)
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
                latest_order = self.get_latest_order_full(cliente_cedula)
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

        if utility in ('validar_pago', 'factura', 'pago') or content.get('kind') == 'factura':
            order_id = state.get('reference_id') or qr.get('referencia_id') or content.get('orden_id')
            order = self.get_order_full(order_id) if order_id else None
            if not order:
                return {'mode': 'factura_invalida', 'message': 'Factura no encontrada'}
            if order.get('cliente_cedula') != cliente_cedula:
                return {'mode': 'factura_restringida', 'message': 'Esta factura pertenece a otro cliente'}
            return {'mode': 'factura_cliente', 'message': 'Factura cargada', 'order': order}

        if utility == 'promocion' or qr.get('tipo') == 'promocion':
            promo_id = state.get('reference_id') or qr.get('referencia_id') or content.get('promocion_id')
            if promo_id:
                card = self.assign_card_to_client(cliente_cedula, promo_id)
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
