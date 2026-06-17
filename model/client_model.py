from model.connection import Connection
from config.validation import (
    ValidationError,
    normalize_cedula,
    normalize_email,
    normalize_phone,
    optional_text,
    require_text,
)


CLIENTE_BASE = (
    "SELECT c.identificador_cliente AS cedula, c.nombre_cliente AS nombre, '' AS apellido, "
    "c.correo_cliente AS email, c.telefono_cliente AS telefono, c.direccion_cliente AS direccion, "
    "c.tipo_cliente, c.estado, c.id_cliente, c.created_at, c.updated_at, "
    "n.id_natural, n.usuario_id, n.origen_registro "
    "FROM cliente c LEFT JOIN cliente_natural n ON n.id_cliente = c.id_cliente"
)


class ClientModel(Connection):
    def __init__(self):
        super().__init__()
        self._cedula = None
        self._email = None
        self._telefono = None
        self._direccion = None

    @property
    def cedula(self):
        return self._cedula

    @cedula.setter
    def cedula(self, valor):
        if valor:
            valor = str(valor).strip()
        self._cedula = valor

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        if valor:
            valor = str(valor).strip()
        self._email = valor

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor:
            valor = str(valor).strip()
        self._telefono = valor

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._direccion = valor

    def _user_by_cedula(self, cedula):
        return self.fetch_one("mantenimiento",
            "SELECT id, nombre, apellido, cedula, email, telefono, direccion, tipo FROM usuarios WHERE cedula = %s",
            (cedula,))

    @staticmethod
    def _full_name(data):
        nombre = (data.get('nombre') or '').strip()
        apellido = (data.get('apellido') or '').strip()
        return (nombre + ' ' + apellido).strip() or nombre

    def _get_all(self, search=None, estado=None, tipo_cliente='persona'):
        sql = (
            CLIENTE_BASE.replace(
                "FROM cliente c",
                ", (SELECT COUNT(*) FROM cliente_vehiculo cv INNER JOIN vehiculos v ON cv.vehiculo_placa = v.placa_vehiculo "
                "WHERE cv.cliente_cedula = c.identificador_cliente AND cv.estado = 1 AND v.estado = 1) as vehiculos_count "
                "FROM cliente c")
            + " WHERE c.identificador_cliente != 'V-00000000'"
        )
        params = []
        if tipo_cliente:
            tipo = 'juridica' if tipo_cliente in ('empresa', 'juridica') else 'natural'
            sql += " AND c.tipo_cliente = %s"
            params.append(tipo)
        if search:
            sql += " AND (c.nombre_cliente LIKE %s OR c.identificador_cliente LIKE %s OR c.correo_cliente LIKE %s OR c.telefono_cliente LIKE %s)"
            q = f"%{search}%"
            params.extend([q, q, q, q])
        sql += " AND c.estado = %s"
        params.append(int(estado) if estado is not None else 1)
        sql += " ORDER BY c.created_at DESC"
        return self.fetch_all("transalca", sql, tuple(params) if params else None)

    def _get_by_cedula(self, cedula):
        return self.fetch_one("transalca",
            CLIENTE_BASE + " WHERE c.identificador_cliente = %s", (cedula,))

    def _get_cliente_id(self, cedula):
        row = self.fetch_one("transalca",
            "SELECT id_cliente FROM cliente WHERE identificador_cliente = %s", (cedula,))
        return row['id_cliente'] if row else None

    def _validate(self, data, require_cedula=True):
        errors = {}
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=100, person=True)
        clean['apellido'] = optional_text(errors, 'apellido', data.get('apellido'), 'El apellido', max_len=100, person=True)
        clean['telefono'] = normalize_phone(errors, data.get('telefono'))
        clean['email'] = normalize_email(errors, data.get('email'), required=False)
        clean['direccion'] = optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=40)
        if require_cedula:
            cedula, prefijo, _ = normalize_cedula(errors, data)
            clean['cedula'] = cedula
            clean['cedula_prefijo'] = prefijo
        if errors:
            raise ValidationError(errors)
        return clean

    def _create(self, data):
        clean = self._validate(data, require_cedula=True)
        data = {**data, **clean}
        self.cedula = data['cedula']
        cedula = self._cedula
        existing_client = self._get_by_cedula(cedula)
        if existing_client and existing_client.get('estado'):
            raise ValidationError({'cedula': 'Esta cedula ya esta registrada.'})
        if clean.get('email') and self.email_exists_globally(clean['email'], {"cliente_cedula": cedula, "usuario_cedula": cedula}):
            raise ValidationError({'email': 'Este correo ya esta registrado.'})
        user = self._user_by_cedula(cedula)
        if user and user.get('tipo') != 'cliente':
            raise ValueError('La cedula pertenece a un usuario interno')
        tipo = 'juridica' if data.get('tipo_cliente') in ('empresa', 'juridica') else 'natural'
        nombre_cliente = self._full_name(data)
        self.email = data.get('email') or ''
        self.telefono = data.get('telefono') or ''
        self.direccion = data.get('direccion') or ''
        email = self._email
        telefono = self._telefono
        direccion = self._direccion
        if existing_client:
            self.update("transalca",
                "UPDATE cliente SET nombre_cliente=%s, correo_cliente=%s, telefono_cliente=%s, direccion_cliente=%s, tipo_cliente=%s, estado=1 "
                "WHERE identificador_cliente=%s",
                (nombre_cliente, email, telefono, direccion, tipo, cedula))
            cliente_id = existing_client['id_cliente']
        else:
            cliente_id = self.insert("transalca",
                "INSERT INTO cliente (nombre_cliente, correo_cliente, identificador_cliente, telefono_cliente, direccion_cliente, tipo_cliente, estado) "
                "VALUES (%s, %s, %s, %s, %s, %s, 1)",
                (nombre_cliente, email, cedula, telefono, direccion, tipo))
        if tipo == 'natural':
            self.insert("transalca",
                "INSERT INTO cliente_natural (id_cliente, usuario_id, origen_registro) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE usuario_id = COALESCE(VALUES(usuario_id), usuario_id)",
                (cliente_id, user['id'] if user else None, data.get('origen_registro', 'admin')))
        else:
            self.insert("transalca",
                "INSERT INTO cliente_juridico (id_cliente, sector, limite_credito, dias_credito) VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE sector = VALUES(sector)",
                (cliente_id, data.get('sector'), data.get('limite_credito', 0), data.get('dias_credito', 0)))
        if user:
            self.update("mantenimiento",
                "UPDATE usuarios SET nombre=%s, apellido=%s, telefono=%s, email=%s, direccion=%s WHERE id=%s AND tipo='cliente'",
                ((data.get('nombre') or nombre_cliente).strip(), (data.get('apellido') or '').strip(),
                 telefono, email, direccion, user['id']))
        return {'cedula': cedula, 'reactivated': bool(existing_client and not existing_client.get('estado'))}

    def _update_client(self, cedula, data):
        clean = self._validate({**data, 'cedula': cedula}, require_cedula=True)
        if clean.get('email') and self.email_exists_globally(clean['email'], {"cliente_cedula": cedula, "usuario_cedula": cedula}):
            raise ValidationError({'email': 'Este correo ya esta registrado.'})
        data = {**data, **clean}
        self.email = data.get('email') or ''
        self.telefono = data.get('telefono') or ''
        self.direccion = data.get('direccion') or ''
        nombre_cliente = self._full_name(data)
        result = self.update("transalca",
            "UPDATE cliente SET nombre_cliente=%s, correo_cliente=%s, telefono_cliente=%s, direccion_cliente=%s "
            "WHERE identificador_cliente=%s",
            (nombre_cliente, self._email, self._telefono, self._direccion, cedula))
        client = self._get_by_cedula(cedula)
        if client and client.get('usuario_id'):
            self.update("mantenimiento",
                "UPDATE usuarios SET nombre=%s, apellido=%s, telefono=%s, email=%s, direccion=%s WHERE id=%s AND tipo='cliente'",
                ((data.get('nombre') or nombre_cliente).strip(), (data.get('apellido') or '').strip(),
                 self._telefono, self._email, self._direccion, client['usuario_id']))
        return result

    def _toggle_estado(self, cedula):
        self.update("transalca",
            "UPDATE cliente SET estado = 0 WHERE identificador_cliente=%s", (cedula,))
        client = self._get_by_cedula(cedula)
        return int(client.get('estado') or 0) if client else 0

    def _get_stats(self, tipo_cliente='persona'):
        if tipo_cliente:
            tipo = 'juridica' if tipo_cliente in ('empresa', 'juridica') else 'natural'
            params = (tipo,)
            total = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM cliente WHERE tipo_cliente = %s AND identificador_cliente != 'V-00000000'", params)
            activos = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM cliente WHERE tipo_cliente = %s AND identificador_cliente != 'V-00000000' AND estado=1", params)
        else:
            total = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM cliente WHERE identificador_cliente != 'V-00000000'")
            activos = self.fetch_one("transalca", "SELECT COUNT(*) as total FROM cliente WHERE identificador_cliente != 'V-00000000' AND estado=1")
        return {
            'total': total['total'] if total else 0,
            'activos': activos['total'] if activos else 0
        }

    def _get_vehicles(self, cedula):
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa_vehiculo as id, v.placa_vehiculo as placa, v.marca_vehiculo as marca, "
            "v.modelo_vehiculo as modelo, v.anio_vehiculo as anio, v.color_vehiculo as color, "
            "v.observaciones_vehiculo as observaciones, v.cauchos_vehiculo as cauchos_json "
            "FROM vehiculos v INNER JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa "
            "WHERE cv.cliente_cedula=%s AND cv.estado=1 AND v.estado=1 ORDER BY cv.created_at DESC",
            (cedula,))

    def _get_services(self, cedula):
        return self.fetch_all("transalca",
            "SELECT bv.*, bv.id_bitacora_vehiculo AS id, bv.fecha_bitacora as fecha, bv.descripcion_bitacora as descripcion, "
            "bv.observaciones_bitacora as observaciones, bv.cauchos_usados as cauchos_info, "
            "v.placa_vehiculo as placa, v.marca_vehiculo as marca, v.modelo_vehiculo as modelo "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa_vehiculo "
            "INNER JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa "
            "WHERE cv.cliente_cedula=%s AND cv.estado=1 AND v.estado=1 ORDER BY bv.fecha_bitacora DESC LIMIT 50",
            (cedula,))

    def _get_tickets(self, cedula):
        return self.fetch_all("transalca",
            "SELECT t.*, t.id_ticket_soporte AS id, t.prioridad_ticket AS prioridad, t.descripcion_ticket_soporte as descripcion FROM tickets_soporte t "
            "WHERE t.cliente_cedula=%s ORDER BY t.created_at DESC",
            (cedula,))

    def _get_orders(self, cedula):
        return self.fetch_all("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE ov.cliente_cedula=%s ORDER BY ov.id_orden_venta DESC LIMIT 50",
            (cedula,))

    def _get_notifications(self, cedula):
        return self.fetch_all("transalca",
            "SELECT nf.*, nf.id_notificacion AS id, nf.tipo_notificacion as tipo, nf.titulo_notificacion as titulo, "
            "nf.mensaje_notificacion as mensaje, nf.prioridad_notificacion as prioridad "
            "FROM notificaciones nf WHERE nf.cliente_cedula=%s OR nf.usuario_id IN "
            "(SELECT id FROM db_mantenimiento.usuarios WHERE cedula=%s) "
            "ORDER BY nf.created_at DESC LIMIT 50",
            (cedula, cedula))

    def _get_bitacora(self, cedula):
        return self.fetch_all("transalca",
            "SELECT bv.*, bv.id_bitacora_vehiculo AS id, bv.fecha_bitacora as fecha, bv.descripcion_bitacora as descripcion, "
            "bv.observaciones_bitacora as observaciones, bv.cauchos_usados as cauchos_info, "
            "v.placa_vehiculo as placa, v.marca_vehiculo as marca, v.modelo_vehiculo as modelo "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa_vehiculo "
            "INNER JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa "
            "WHERE cv.cliente_cedula=%s AND cv.estado=1 AND v.estado=1 ORDER BY bv.fecha_bitacora DESC LIMIT 100",
            (cedula,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "full_name": self._full_name,
            "get_all": self._get_all,
            "get_by_cedula": self._get_by_cedula,
            "get_cliente_id": self._get_cliente_id,
            "create": self._create,
            "update_client": self._update_client,
            "toggle_estado": self._toggle_estado,
            "get_stats": self._get_stats,
            "get_vehicles": self._get_vehicles,
            "get_services": self._get_services,
            "get_tickets": self._get_tickets,
            "get_orders": self._get_orders,
            "get_notifications": self._get_notifications,
            "get_bitacora": self._get_bitacora,
            "email_exists_globally": self.email_exists_globally,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
