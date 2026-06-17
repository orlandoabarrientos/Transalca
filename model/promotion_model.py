import re
from model.connection import Connection
from config.constants import TIPOS_PROMOCION
from config.validation import (
    ValidationError,
    normalize_int,
    optional_text,
    require_text,
    validate_choice,
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class PromotionModel(Connection):
    def __init__(self):
        super().__init__()
        self._nombre = None
        self._descripcion = None
        self._recompensa = None
        self._fecha_inicio = None
        self._fecha_fin = None

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

    @property
    def descripcion(self):
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._descripcion = valor

    @property
    def recompensa(self):
        return self._recompensa

    @recompensa.setter
    def recompensa(self, valor):
        if valor:
            valor = str(valor).strip()
        self._recompensa = valor

    @property
    def fecha_inicio(self):
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, valor):
        if valor:
            valor = str(valor).strip()
        self._fecha_inicio = valor

    @property
    def fecha_fin(self):
        return self._fecha_fin

    @fecha_fin.setter
    def fecha_fin(self, valor):
        if valor:
            valor = str(valor).strip()
        self._fecha_fin = valor

    def _format_promo_dates(self, p):
        if not p:
            return p
        if isinstance(p, list):
            for item in p:
                self._format_promo_dates(item)
            return p
        p['fecha_inicio'] = p['fecha_inicio'].isoformat() if hasattr(p.get('fecha_inicio'), 'isoformat') else p.get('fecha_inicio')
        p['fecha_fin'] = p['fecha_fin'].isoformat() if hasattr(p.get('fecha_fin'), 'isoformat') else p.get('fecha_fin')
        return p

    def _get_all(self):
        return self._format_promo_dates(self.fetch_all("transalca", "SELECT pr.*, pr.id_promocion AS id, pr.nombre_promocion AS nombre, pr.descripcion_promocion AS descripcion, pr.tipo_promocion AS tipo, pr.recompensa_promocion AS recompensa, pr.fecha_inicio_promocion AS fecha_inicio, pr.fecha_fin_promocion AS fecha_fin FROM promociones pr WHERE pr.estado = 1 ORDER BY pr.id_promocion DESC"))

    def _get_active(self):
        return self._format_promo_dates(self.fetch_all("transalca",
            "SELECT pr.*, pr.id_promocion AS id, pr.nombre_promocion AS nombre, pr.descripcion_promocion AS descripcion, pr.tipo_promocion AS tipo, pr.recompensa_promocion AS recompensa, pr.fecha_inicio_promocion AS fecha_inicio, pr.fecha_fin_promocion AS fecha_fin FROM promociones pr WHERE pr.estado = 1 AND (pr.fecha_fin_promocion IS NULL OR pr.fecha_fin_promocion >= CURDATE()) ORDER BY pr.nombre_promocion"))

    def _get_by_id(self, promo_id):
        return self._format_promo_dates(self.fetch_one("transalca", "SELECT pr.*, pr.id_promocion AS id, pr.nombre_promocion AS nombre, pr.descripcion_promocion AS descripcion, pr.tipo_promocion AS tipo, pr.recompensa_promocion AS recompensa, pr.fecha_inicio_promocion AS fecha_inicio, pr.fecha_fin_promocion AS fecha_fin FROM promociones pr WHERE pr.id_promocion = %s", (promo_id,)))

    def _validate(self, data):
        errors = {}
        clean = {
            'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=150, allow_serial=False),
            'descripcion': optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=500, allow_serial=True),
            'tipo': validate_choice(errors, 'tipo', data.get('tipo'), TIPOS_PROMOCION),
            'puntos_requeridos': normalize_int(errors, 'puntos_requeridos', data.get('puntos_requeridos') or 1, 'Los puntos', min_value=1, max_value=999999),
            'recompensa': optional_text(errors, 'recompensa', data.get('recompensa'), 'La recompensa', max_len=200, allow_serial=True),
            'fecha_inicio': data.get('fecha_inicio') or None,
            'fecha_fin': data.get('fecha_fin') or None,
        }
        for field in ('fecha_inicio', 'fecha_fin'):
            if clean[field] and not DATE_RE.match(str(clean[field])):
                errors[field] = 'La fecha debe tener formato valido.'
        if clean['fecha_inicio'] and clean['fecha_fin'] and clean['fecha_fin'] < clean['fecha_inicio']:
            errors['fecha_fin'] = 'La fecha fin no puede ser menor que la fecha inicio.'
        if errors:
            raise ValidationError(errors)
        return clean

    def _apply_save(self, clean):
        self.nombre = clean['nombre']
        self.descripcion = clean.get('descripcion', '') or ''
        self.recompensa = clean.get('recompensa', '') or ''
        self.fecha_inicio = clean.get('fecha_inicio')
        self.fecha_fin = clean.get('fecha_fin')

    def _apply_update(self, promo_id, clean):
        self._apply_save(clean)
        return self.update("transalca",
            "UPDATE promociones SET nombre_promocion = %s, descripcion_promocion = %s, tipo_promocion = %s, puntos_requeridos = %s, recompensa_promocion = %s, fecha_inicio_promocion = %s, fecha_fin_promocion = %s WHERE id_promocion = %s",
            (self._nombre, self._descripcion, clean.get('tipo', 'puntos'),
             clean.get('puntos_requeridos', 3), self._recompensa,
             self._fecha_inicio, self._fecha_fin, promo_id))

    def _create(self, data):
        clean = self._validate(data)
        existing = self._get_by_nombre(clean['nombre'])
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'nombre': 'Ya existe una promocion con ese nombre.'})
            self._apply_update(existing['id'], clean)
            self._reactivar(existing['id'])
            return existing['id']
        self._apply_save(clean)
        return self.insert("transalca",
            "INSERT INTO promociones (nombre_promocion, descripcion_promocion, tipo_promocion, puntos_requeridos, recompensa_promocion, imagen_tarjeta, fecha_inicio_promocion, fecha_fin_promocion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (self._nombre, self._descripcion, clean.get('tipo', 'puntos'),
             clean.get('puntos_requeridos', 3), self._recompensa,
             'default_card.png',
             self._fecha_inicio, self._fecha_fin))

    def _update_promotion(self, promo_id, data):
        clean = self._validate(data)
        if self._nombre_exists(clean['nombre'], promo_id):
            raise ValidationError({'nombre': 'Ya existe una promocion con ese nombre.'})
        return self._apply_update(promo_id, clean)

    def _update_image(self, promo_id, filename):
        return self.update("transalca",
            "UPDATE promociones SET imagen_tarjeta = %s WHERE id_promocion = %s", (filename, promo_id))

    def _delete_promotion(self, promo_id):
        return self.update("transalca",
            "UPDATE promociones SET estado = 0 WHERE id_promocion = %s", (promo_id,))

    def _soft_delete(self, promo_id):
        promo = self._get_by_id(promo_id)
        if not promo:
            return None
        self.update("transalca", "UPDATE promociones SET estado = 0 WHERE id_promocion = %s", (promo_id,))
        return 0

    def _assign_card_to_client(self, cliente_cedula, promocion_id):
        client = self.fetch_one("transalca", "SELECT id_cliente FROM cliente WHERE identificador_cliente = %s", (cliente_cedula,))
        if not client:
            user = self.fetch_one("mantenimiento", "SELECT id, nombre, apellido, email, telefono, direccion FROM usuarios WHERE cedula = %s", (cliente_cedula,))
            if user:
                nombre = (str(user['nombre'] or '') + ' ' + str(user['apellido'] or '')).strip()
                cliente_id = self.insert("transalca",
                    "INSERT INTO cliente (nombre_cliente, correo_cliente, identificador_cliente, telefono_cliente, direccion_cliente, tipo_cliente) VALUES (%s, %s, %s, %s, %s, 'natural')",
                    (nombre, user['email'], cliente_cedula, user.get('telefono') or '', user.get('direccion') or ''))
                self.insert("transalca",
                    "INSERT INTO cliente_natural (id_cliente, usuario_id, origen_registro) VALUES (%s, %s, 'cliente')",
                    (cliente_id, user['id']))
            else:
                return None

        existing = self.fetch_one("transalca",
            "SELECT id_tarjeta_fidelidad AS id FROM tarjeta_fidelidad WHERE cliente_cedula = %s AND promocion_id = %s AND canjeada = 0",
            (cliente_cedula, promocion_id))
        if existing:
            return existing['id']
        return self.insert("transalca",
            "INSERT INTO tarjeta_fidelidad (cliente_cedula, promocion_id) VALUES (%s, %s)",
            (cliente_cedula, promocion_id))

    def _get_client_info(self, cedula):
        client = self.fetch_one("transalca",
            "SELECT nombre_cliente, identificador_cliente FROM cliente WHERE identificador_cliente = %s", (cedula,))
        if client:
            return {
                "cliente_nombre": client['nombre_cliente'].strip(),
                "cliente_cedula_display": client['identificador_cliente']
            }
        user = self.fetch_one("mantenimiento",
            "SELECT nombre, apellido, cedula FROM usuarios WHERE cedula = %s", (cedula,))
        if user:
            return {
                "cliente_nombre": f"{user['nombre']} {user['apellido']}".strip(),
                "cliente_cedula_display": user['cedula']
            }
        return {
            "cliente_nombre": "Cliente no encontrado",
            "cliente_cedula_display": cedula
        }

    def _loyalty_activity_filter(self, scanned_only):
        if not scanned_only:
            return ""
        return (
            " AND (tf.puntos_acumulados > 0 OR EXISTS ("
            "SELECT 1 FROM historial_puntos hp_scan WHERE hp_scan.tarjeta_id = tf.id_tarjeta_fidelidad"
            "))"
        )

    def _get_client_cards(self, cliente_cedula, scanned_only=False):
        if scanned_only:
            sql = (
                "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.nombre_promocion as promo_nombre, p.descripcion_promocion as promo_descripcion, p.puntos_requeridos, p.recompensa_promocion as recompensa, p.imagen_tarjeta, p.tipo_promocion as tipo, "
                "DATE_FORMAT(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), '%%Y-%%m-%%d') as fecha_aplicacion_promocion, "
                "DATE_FORMAT(DATE_ADD(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), INTERVAL 1 MONTH), '%%Y-%%m-%%d') as fecha_vencimiento_promocion "
                "FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE tf.cliente_cedula = %s "
                "AND (tf.puntos_acumulados > 0 OR EXISTS (SELECT 1 FROM historial_puntos hp_scan WHERE hp_scan.tarjeta_id = tf.id_tarjeta_fidelidad)) ORDER BY tf.fecha_creacion DESC"
            )
        else:
            sql = (
                "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.nombre_promocion as promo_nombre, p.descripcion_promocion as promo_descripcion, p.puntos_requeridos, p.recompensa_promocion as recompensa, p.imagen_tarjeta, p.tipo_promocion as tipo, "
                "DATE_FORMAT(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), '%%Y-%%m-%%d') as fecha_aplicacion_promocion, "
                "DATE_FORMAT(DATE_ADD(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), INTERVAL 1 MONTH), '%%Y-%%m-%%d') as fecha_vencimiento_promocion "
                "FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE tf.cliente_cedula = %s ORDER BY tf.fecha_creacion DESC"
            )
        cards = self.fetch_all("transalca", sql, (cliente_cedula,))
        for card in cards:
            info = self._get_client_info(card['cliente_cedula'])
            card.update(info)
        return cards

    def _add_point(self, tarjeta_id, descripcion=''):
        card = self.fetch_one("transalca",
            "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.puntos_requeridos FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE tf.id_tarjeta_fidelidad = %s",
            (tarjeta_id,))
        if not card or card['canjeada']:
            return None
        new_points = card['puntos_acumulados'] + 1
        canjeada = 1 if new_points >= card['puntos_requeridos'] else 0
        self.update("transalca",
            "UPDATE tarjeta_fidelidad SET puntos_acumulados = %s, canjeada = %s WHERE id_tarjeta_fidelidad = %s",
            (new_points, canjeada, tarjeta_id))
        self.insert("transalca",
            "INSERT INTO historial_puntos (tarjeta_id, puntos, tipo_historial_punto, descripcion_historial_punto) VALUES (%s, 1, 'suma', %s)",
            (tarjeta_id, descripcion))
        return {"puntos_acumulados": new_points, "canjeada": canjeada}

    def _get_card_history(self, tarjeta_id):
        return self.fetch_all("transalca",
            "SELECT hp.*, hp.id_historial_punto AS id, hp.tipo_historial_punto AS tipo, hp.descripcion_historial_punto AS descripcion, hp.fecha_historial_punto AS fecha FROM historial_puntos hp WHERE hp.tarjeta_id = %s ORDER BY hp.fecha_historial_punto DESC",
            (tarjeta_id,))

    def _get_all_cards(self, scanned_only=False):
        if scanned_only:
            sql = (
                "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.nombre_promocion as promo_nombre, p.descripcion_promocion as promo_descripcion, p.puntos_requeridos, p.recompensa_promocion as recompensa, p.imagen_tarjeta, p.tipo_promocion as tipo, "
                "DATE_FORMAT(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), '%%Y-%%m-%%d') as fecha_aplicacion_promocion, "
                "DATE_FORMAT(DATE_ADD(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), INTERVAL 1 MONTH), '%%Y-%%m-%%d') as fecha_vencimiento_promocion "
                "FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE 1 = 1 "
                "AND (tf.puntos_acumulados > 0 OR EXISTS (SELECT 1 FROM historial_puntos hp_scan WHERE hp_scan.tarjeta_id = tf.id_tarjeta_fidelidad)) ORDER BY tf.fecha_creacion DESC"
            )
        else:
            sql = (
                "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.nombre_promocion as promo_nombre, p.descripcion_promocion as promo_descripcion, p.puntos_requeridos, p.recompensa_promocion as recompensa, p.imagen_tarjeta, p.tipo_promocion as tipo, "
                "DATE_FORMAT(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), '%%Y-%%m-%%d') as fecha_aplicacion_promocion, "
                "DATE_FORMAT(DATE_ADD(COALESCE((SELECT MAX(hp.fecha_historial_punto) FROM historial_puntos hp WHERE hp.tarjeta_id = tf.id_tarjeta_fidelidad), tf.fecha_creacion), INTERVAL 1 MONTH), '%%Y-%%m-%%d') as fecha_vencimiento_promocion "
                "FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE 1 = 1 ORDER BY tf.fecha_creacion DESC"
            )
        cards = self.fetch_all("transalca", sql)
        for card in cards:
            info = self._get_client_info(card['cliente_cedula'])
            card.update(info)
        return cards

    def _get_card_by_id(self, card_id):
        card = self.fetch_one("transalca",
            "SELECT tf.*, tf.id_tarjeta_fidelidad AS id, p.nombre_promocion as promo_nombre, p.descripcion_promocion as promo_descripcion, p.puntos_requeridos, p.recompensa_promocion as recompensa, p.imagen_tarjeta, p.tipo_promocion as tipo FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id_promocion WHERE tf.id_tarjeta_fidelidad = %s",
            (card_id,))
        if card:
            info = self._get_client_info(card['cliente_cedula'])
            card.update(info)
        return card

    def _nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            result = self.fetch_one("transalca", "SELECT id_promocion FROM promociones WHERE nombre_promocion = %s AND id_promocion != %s AND estado = 1", (nombre, exclude_id))
        else:
            result = self.fetch_one("transalca", "SELECT id_promocion FROM promociones WHERE nombre_promocion = %s AND estado = 1", (nombre,))
        return result is not None

    def _get_by_nombre(self, nombre):
        return self._format_promo_dates(self.fetch_one("transalca", "SELECT pr.*, pr.id_promocion AS id, pr.nombre_promocion AS nombre, pr.descripcion_promocion AS descripcion, pr.tipo_promocion AS tipo, pr.recompensa_promocion AS recompensa, pr.fecha_inicio_promocion AS fecha_inicio, pr.fecha_fin_promocion AS fecha_fin FROM promociones pr WHERE pr.nombre_promocion = %s", (nombre,)))

    def _reactivar(self, promo_id):
        return self.update("transalca", "UPDATE promociones SET estado = 1 WHERE id_promocion = %s", (promo_id,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_active": self._get_active,
            "get_by_id": self._get_by_id,
            "validate": self._validate,
            "create": self._create,
            "update_promotion": self._update_promotion,
            "update_image": self._update_image,
            "delete_promotion": self._delete_promotion,
            "soft_delete": self._soft_delete,
            "assign_card_to_client": self._assign_card_to_client,
            "get_client_cards": self._get_client_cards,
            "add_point": self._add_point,
            "get_card_history": self._get_card_history,
            "get_all_cards": self._get_all_cards,
            "get_card_by_id": self._get_card_by_id,
            "nombre_exists": self._nombre_exists,
            "get_by_nombre": self._get_by_nombre,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
