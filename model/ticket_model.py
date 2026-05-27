from model.connection import Connection


class TicketModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self, estado=None, prioridad=None):
        sql = ("SELECT t.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido, "
               "v.placa as vehiculo_placa, v.marca as vehiculo_marca, v.modelo as vehiculo_modelo, "
               "m.nombre as asignado_nombre, m.apellido as asignado_apellido "
               "FROM tickets_soporte t "
               "INNER JOIN clientes c ON t.cliente_cedula = c.cedula "
               "LEFT JOIN vehiculos v ON t.vehiculo_placa = v.placa "
               "LEFT JOIN mecanicos m ON t.asignado_a = m.cedula "
               "WHERE 1=1")
        params = []
        if estado:
            sql += " AND t.estado = %s"
            params.append(estado)
        if prioridad:
            sql += " AND t.prioridad = %s"
            params.append(prioridad)
        sql += " ORDER BY t.created_at DESC"
        return self.fetch_all("transalca", sql, tuple(params) if params else None)

    def get_by_id(self, ticket_id):
        ticket = self.fetch_one("transalca",
            "SELECT t.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido, "
            "c.telefono as cliente_telefono, c.email as cliente_email, "
            "v.placa as vehiculo_placa, v.marca as vehiculo_marca, v.modelo as vehiculo_modelo, "
            "m.nombre as asignado_nombre, m.apellido as asignado_apellido "
            "FROM tickets_soporte t "
            "INNER JOIN clientes c ON t.cliente_cedula = c.cedula "
            "LEFT JOIN vehiculos v ON t.vehiculo_placa = v.placa "
            "LEFT JOIN mecanicos m ON t.asignado_a = m.cedula "
            "WHERE t.id = %s", (ticket_id,))
        if ticket:
            ticket['respuestas'] = self.get_responses(ticket_id)
        return ticket

    def get_by_cliente(self, cliente_cedula):
        return self.fetch_all("transalca",
            "SELECT t.*, v.placa as vehiculo_placa, v.marca as vehiculo_marca "
            "FROM tickets_soporte t "
            "LEFT JOIN vehiculos v ON t.vehiculo_placa = v.placa "
            "WHERE t.cliente_cedula = %s ORDER BY t.created_at DESC",
            (cliente_cedula,))

    def create(self, data):
        vehiculo_placa = None
        if data.get('vehiculo_id'):
            vehicle = self.fetch_one("transalca", "SELECT placa FROM vehiculos WHERE id=%s", (data.get('vehiculo_id'),))
            vehiculo_placa = vehicle['placa'] if vehicle else None
        return self.insert("transalca",
            "INSERT INTO tickets_soporte (cliente_cedula, vehiculo_placa, asunto, "
            "descripcion, prioridad) VALUES (%s, %s, %s, %s, %s)",
            (data['cliente_cedula'].strip(),
             vehiculo_placa,
             data['asunto'].strip(),
             (data.get('descripcion') or '').strip(),
             data.get('prioridad', 'media')))

    def update_status(self, ticket_id, estado):
        return self.update("transalca",
            "UPDATE tickets_soporte SET estado = %s WHERE id = %s",
            (estado, ticket_id))

    def assign_to(self, ticket_id, mecanico_cedula):
        return self.update("transalca",
            "UPDATE tickets_soporte SET asignado_a = %s, estado = 'en_revision' "
            "WHERE id = %s", (mecanico_cedula, ticket_id))

    def add_response(self, data):
        return self.insert("transalca",
            "INSERT INTO ticket_respuestas (ticket_id, autor_id, autor_tipo, "
            "mensaje, adjunto_url) VALUES (%s, %s, %s, %s, %s)",
            (data['ticket_id'], data['autor_id'], data['autor_tipo'],
             data['mensaje'].strip(), data.get('adjunto_url')))

    def get_responses(self, ticket_id):
        responses = self.fetch_all("transalca",
            "SELECT * FROM ticket_respuestas WHERE ticket_id = %s "
            "ORDER BY created_at ASC", (ticket_id,))
        for r in responses:
            if r['autor_tipo'] in ('admin', 'soporte'):
                user = self.fetch_one("mantenimiento",
                    "SELECT nombre, apellido FROM usuarios WHERE id = %s",
                    (r['autor_id'],))
            else:
                user = self.fetch_one("mantenimiento",
                    "SELECT nombre, apellido FROM usuarios WHERE id = %s",
                    (r['autor_id'],))
            r['autor_nombre'] = f"{user['nombre']} {user['apellido']}" if user else 'Sistema'
        return responses

    def count_by_estado(self):
        return self.fetch_all("transalca",
            "SELECT estado, COUNT(*) as total FROM tickets_soporte "
            "GROUP BY estado")

    def count_open_by_cliente(self, cliente_cedula):
        result = self.fetch_one("transalca",
            "SELECT COUNT(*) as total FROM tickets_soporte "
            "WHERE cliente_cedula = %s AND estado NOT IN ('resuelto','cerrado')",
            (cliente_cedula,))
        return result['total'] if result else 0
