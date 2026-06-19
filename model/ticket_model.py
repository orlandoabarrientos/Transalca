from model.connection import Connection

TICKET_BASE_LIST_SQL = (
    "SELECT t.*, t.id_ticket_soporte AS id, t.prioridad_ticket AS prioridad, t.descripcion_ticket_soporte as descripcion, "
    "c.nombre_cliente as cliente_nombre, '' as cliente_apellido, "
    "v.placa_vehiculo as vehiculo_placa, v.marca_vehiculo as vehiculo_marca, v.modelo_vehiculo as vehiculo_modelo, "
    "p.nombre_producto as producto_nombre, s.nombre_servicio as servicio_nombre "
    "FROM tickets_soporte t "
    "INNER JOIN cliente c ON t.cliente_cedula = c.identificador_cliente "
    "LEFT JOIN vehiculos v ON t.referencia_tipo = 'vehiculo' AND t.referencia_id = v.placa_vehiculo "
    "LEFT JOIN productos p ON t.referencia_tipo = 'producto' AND t.referencia_id = p.codigo "
    "LEFT JOIN servicios s ON t.referencia_tipo = 'servicio' AND t.referencia_id = CAST(s.id_servicio AS CHAR) "
    "WHERE 1=1"
)
TICKET_BY_ID_SQL = (
    "SELECT t.*, t.id_ticket_soporte AS id, t.prioridad_ticket AS prioridad, t.descripcion_ticket_soporte as descripcion, "
    "c.nombre_cliente as cliente_nombre, '' as cliente_apellido, "
    "c.telefono_cliente as cliente_telefono, c.correo_cliente as cliente_email, "
    "v.placa_vehiculo as vehiculo_placa, v.marca_vehiculo as vehiculo_marca, v.modelo_vehiculo as vehiculo_modelo, "
    "p.nombre_producto as producto_nombre, s.nombre_servicio as servicio_nombre "
    "FROM tickets_soporte t "
    "INNER JOIN cliente c ON t.cliente_cedula = c.identificador_cliente "
    "LEFT JOIN vehiculos v ON t.referencia_tipo = 'vehiculo' AND t.referencia_id = v.placa_vehiculo "
    "LEFT JOIN productos p ON t.referencia_tipo = 'producto' AND t.referencia_id = p.codigo "
    "LEFT JOIN servicios s ON t.referencia_tipo = 'servicio' AND t.referencia_id = CAST(s.id_servicio AS CHAR) "
    "WHERE t.id_ticket_soporte = %s"
)
TICKET_BY_CLIENT_SQL = (
    "SELECT t.*, t.id_ticket_soporte AS id, t.prioridad_ticket AS prioridad, t.descripcion_ticket_soporte as descripcion, "
    "v.placa_vehiculo as vehiculo_placa, v.marca_vehiculo as vehiculo_marca, "
    "p.nombre_producto as producto_nombre, s.nombre_servicio as servicio_nombre "
    "FROM tickets_soporte t "
    "LEFT JOIN vehiculos v ON t.referencia_tipo = 'vehiculo' AND t.referencia_id = v.placa_vehiculo "
    "LEFT JOIN productos p ON t.referencia_tipo = 'producto' AND t.referencia_id = p.codigo "
    "LEFT JOIN servicios s ON t.referencia_tipo = 'servicio' AND t.referencia_id = CAST(s.id_servicio AS CHAR) "
    "WHERE t.cliente_cedula = %s ORDER BY t.created_at DESC"
)


class TicketModel(Connection):
    def __init__(self):
        super().__init__()
        self._cliente_cedula = None
        self._asunto = None
        self._descripcion = None
        self._prioridad = None

    @property
    def cliente_cedula(self):
        return self._cliente_cedula

    @cliente_cedula.setter
    def cliente_cedula(self, valor):
        if valor:
            valor = str(valor).strip()
        self._cliente_cedula = valor

    @property
    def asunto(self):
        return self._asunto

    @asunto.setter
    def asunto(self, valor):
        if valor:
            valor = str(valor).strip()
        self._asunto = valor

    @property
    def descripcion(self):
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._descripcion = valor

    @property
    def prioridad(self):
        return self._prioridad

    @prioridad.setter
    def prioridad(self, valor):
        if valor:
            valor = str(valor).strip()
        self._prioridad = valor

    def _get_all(self, estado=None, prioridad=None):
        sql = TICKET_BASE_LIST_SQL
        params = []
        if estado:
            sql += " AND t.estado = %s"
            params.append(estado)
        if prioridad:
            sql += " AND t.prioridad_ticket = %s"
            params.append(prioridad)
        sql += " ORDER BY t.created_at DESC"
        return self.fetch_all("transalca", sql, tuple(params) if params else None)

    def _get_by_id(self, ticket_id):
        ticket = self.fetch_one("transalca", TICKET_BY_ID_SQL, (ticket_id,))
        if ticket:
            ticket['respuestas'] = self._get_responses(ticket_id)
        return ticket

    def _get_by_cliente(self, cliente_cedula):
        return self.fetch_all("transalca", TICKET_BY_CLIENT_SQL, (cliente_cedula,))

    def _create(self, data):
        self.cliente_cedula = data['cliente_cedula']
        self.asunto = data['asunto']
        self.descripcion = data.get('descripcion') or ''
        self.prioridad = data.get('prioridad', 'media')
        referencia_tipo = (data.get('referencia_tipo') or 'general').strip().lower()
        referencia_id = None
        if data.get('vehiculo_placa') or data.get('vehiculo_id'):
            referencia_tipo = 'vehiculo'
            vehicle_key = data.get('vehiculo_placa') or data.get('vehiculo_id')
            vehicle = self.fetch_one("transalca", "SELECT placa_vehiculo FROM vehiculos WHERE placa_vehiculo=%s", (str(vehicle_key).strip().upper(),))
            referencia_id = vehicle['placa_vehiculo'] if vehicle else None
        elif referencia_tipo == 'producto' and data.get('referencia_id'):
            product = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo=%s AND estado=1", (data.get('referencia_id'),))
            referencia_id = product['codigo'] if product else None
        elif referencia_tipo == 'servicio' and data.get('referencia_id'):
            service = self.fetch_one("transalca", "SELECT id_servicio AS id FROM servicios WHERE id_servicio=%s AND estado=1", (data.get('referencia_id'),))
            referencia_id = str(service['id']) if service else None
        else:
            referencia_tipo = 'general'
        return self.insert("transalca",
            "INSERT INTO tickets_soporte (cliente_cedula, referencia_tipo, referencia_id, asunto, "
            "descripcion_ticket_soporte, prioridad_ticket) VALUES (%s, %s, %s, %s, %s, %s)",
            (self._cliente_cedula,
             referencia_tipo,
             referencia_id,
             self._asunto,
             self._descripcion,
             self._prioridad))

    def _update_status(self, ticket_id, estado):
        return self.update("transalca",
            "UPDATE tickets_soporte SET estado = %s WHERE id_ticket_soporte = %s",
            (estado, ticket_id))

    def _add_response(self, data):
        return self.insert("transalca",
            "INSERT INTO ticket_respuestas (ticket_id, autor_id, autor_tipo, "
            "mensaje_ticket_respuesta, adjunto_url) VALUES (%s, %s, %s, %s, %s)",
            (data['ticket_id'], data['autor_id'], data['autor_tipo'],
             data['mensaje'].strip(), data.get('adjunto_url')))

    def _get_responses(self, ticket_id):
        responses = self.fetch_all("transalca",
            "SELECT tr.*, tr.id_ticket_respuesta AS id, tr.mensaje_ticket_respuesta as mensaje FROM ticket_respuestas tr WHERE tr.ticket_id = %s "
            "ORDER BY tr.created_at ASC", (ticket_id,))
        for r in responses:
            user = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido FROM usuarios WHERE id = %s",
                (r['autor_id'],))
            r['autor_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'Sistema'
        return responses

    def _count_by_estado(self):
        return self.fetch_all("transalca",
            "SELECT estado, COUNT(*) as total FROM tickets_soporte "
            "GROUP BY estado")

    def _count_open_by_cliente(self, cliente_cedula):
        result = self.fetch_one("transalca",
            "SELECT COUNT(*) as total FROM tickets_soporte "
            "WHERE cliente_cedula = %s AND estado NOT IN ('resuelto','cerrado')",
            (cliente_cedula,))
        return result['total'] if result else 0

    def _user_id_by_cedula(self, cedula):
        return self.fetch_one("mantenimiento",
            "SELECT id FROM usuarios WHERE cedula=%s", (cedula,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_id": self._get_by_id,
            "get_by_cliente": self._get_by_cliente,
            "create": self._create,
            "update_status": self._update_status,
            "add_response": self._add_response,
            "get_responses": self._get_responses,
            "count_by_estado": self._count_by_estado,
            "count_open_by_cliente": self._count_open_by_cliente,
            "user_id_by_cedula": self._user_id_by_cedula,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
