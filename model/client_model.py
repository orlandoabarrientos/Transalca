from model.connection import Connection


class ClientModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self, table):
        rows = self.fetch_all("transalca", f"SHOW COLUMNS FROM {table}")
        return {r['Field'] for r in rows}

    def _user_by_cedula(self, cedula):
        return self.fetch_one("mantenimiento",
            "SELECT id, nombre, apellido, cedula, email, telefono, direccion, tipo FROM usuarios WHERE cedula = %s",
            (cedula,))

    def get_all(self, search=None, estado=None, tipo_cliente='persona'):
        sql = (
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM vehiculos v WHERE v.cliente_cedula = c.cedula AND v.estado = 1) as vehiculos_count "
            "FROM clientes c WHERE 1=1"
        )
        params = []
        if tipo_cliente:
            sql += " AND COALESCE(c.tipo_cliente, 'persona') = %s"
            params.append(tipo_cliente)
        if search:
            sql += " AND (c.nombre LIKE %s OR c.apellido LIKE %s OR c.cedula LIKE %s OR c.email LIKE %s OR c.telefono LIKE %s)"
            q = f"%{search}%"
            params.extend([q, q, q, q, q])
        sql += " AND c.estado = %s"
        params.append(int(estado) if estado is not None else 1)
        sql += " ORDER BY c.created_at DESC"
        return self.fetch_all("transalca", sql, tuple(params) if params else None)

    def get_by_cedula(self, cedula):
        return self.fetch_one("transalca",
            "SELECT * FROM clientes WHERE cedula = %s", (cedula,))

    def create(self, data):
        columns = self._columns("clientes")
        cedula = data['cedula'].strip()
        existing_client = self.get_by_cedula(cedula)
        user = self._user_by_cedula(cedula)
        if user and user.get('tipo') != 'cliente':
            raise ValueError('La cedula pertenece a un usuario interno')
        values = {
            'cedula': cedula,
            'cedula_prefijo': data.get('cedula_prefijo'),
            'tipo_cliente': data.get('tipo_cliente', 'persona'),
            'nombre': data['nombre'].strip(),
            'apellido': data['apellido'].strip(),
            'telefono': data.get('telefono', '').strip(),
            'email': data.get('email', '').strip(),
            'direccion': data.get('direccion', '').strip(),
            'origen_registro': data.get('origen_registro', 'admin'),
            'estado': 1
        }
        if user:
            values['usuario_id'] = user['id']
        keys = [k for k in values if k in columns]
        if existing_client:
            set_parts = [f"{k}=%s" for k in keys if k != 'cedula']
            params = [values[k] for k in keys if k != 'cedula']
            params.append(cedula)
            self.update("transalca", f"UPDATE clientes SET {', '.join(set_parts)} WHERE cedula=%s", tuple(params))
            if user:
                self.update("mantenimiento",
                    "UPDATE usuarios SET nombre=%s, apellido=%s, telefono=%s, email=%s, direccion=%s WHERE id=%s AND tipo='cliente'",
                    (values['nombre'], values['apellido'], values['telefono'], values['email'], values['direccion'], user['id']))
            return {'cedula': cedula, 'reactivated': not bool(existing_client.get('estado'))}
        sql = f"INSERT INTO clientes ({', '.join(keys)}) VALUES ({', '.join(['%s'] * len(keys))})"
        self.insert("transalca", sql, tuple(values[k] for k in keys))
        if user:
            self.update("mantenimiento",
                "UPDATE usuarios SET nombre=%s, apellido=%s, telefono=%s, email=%s, direccion=%s WHERE id=%s AND tipo='cliente'",
                (values['nombre'], values['apellido'], values['telefono'], values['email'], values['direccion'], user['id']))
        return {'cedula': cedula, 'reactivated': False}

    def update_client(self, cedula, data):
        columns = self._columns("clientes")
        values = {
            'cedula_prefijo': data.get('cedula_prefijo'),
            'nombre': data['nombre'].strip(),
            'apellido': data['apellido'].strip(),
            'telefono': data.get('telefono', '').strip(),
            'email': data.get('email', '').strip(),
            'direccion': data.get('direccion', '').strip()
        }
        keys = [k for k in values if k in columns]
        params = [values[k] for k in keys]
        params.append(cedula)
        result = self.update("transalca",
            f"UPDATE clientes SET {', '.join([f'{k}=%s' for k in keys])} WHERE cedula=%s",
            tuple(params))
        client = self.get_by_cedula(cedula)
        if client and client.get('usuario_id'):
            self.update("mantenimiento",
                "UPDATE usuarios SET nombre=%s, apellido=%s, telefono=%s, email=%s, direccion=%s WHERE id=%s AND tipo='cliente'",
                (data['nombre'].strip(), data['apellido'].strip(),
                 data.get('telefono', '').strip(), data.get('email', '').strip(),
                 data.get('direccion', '').strip(), client['usuario_id']))
        return result

    def toggle_estado(self, cedula):
        self.update("transalca",
            "UPDATE clientes SET estado = 0 WHERE cedula=%s", (cedula,))
        client = self.get_by_cedula(cedula)
        return int(client.get('estado') or 0) if client else 0

    def get_stats(self, tipo_cliente='persona'):
        params = (tipo_cliente,) if tipo_cliente else None
        where = "WHERE COALESCE(tipo_cliente, 'persona') = %s" if tipo_cliente else ""
        total = self.fetch_one("transalca", f"SELECT COUNT(*) as total FROM clientes {where}", params)
        activos = self.fetch_one("transalca", f"SELECT COUNT(*) as total FROM clientes {where} AND estado=1" if tipo_cliente else "SELECT COUNT(*) as total FROM clientes WHERE estado=1", params)
        return {
            'total': total['total'] if total else 0,
            'activos': activos['total'] if activos else 0
        }

    def get_vehicles(self, cedula):
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa as id FROM vehiculos v WHERE cliente_cedula=%s AND estado=1 ORDER BY created_at DESC",
            (cedula,))

    def get_services(self, cedula):
        return self.fetch_all("transalca",
            "SELECT bv.*, v.placa, v.marca, v.modelo "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa "
            "WHERE v.cliente_cedula=%s ORDER BY bv.fecha DESC LIMIT 50",
            (cedula,))

    def get_tickets(self, cedula):
        return self.fetch_all("transalca",
            "SELECT * FROM tickets_soporte WHERE cliente_cedula=%s ORDER BY created_at DESC",
            (cedula,))

    def get_orders(self, cedula):
        return self.fetch_all("transalca",
            "SELECT * FROM ordenes_venta WHERE cliente_cedula=%s ORDER BY id DESC LIMIT 50",
            (cedula,))

    def get_notifications(self, cedula):
        return self.fetch_all("transalca",
            "SELECT * FROM notificaciones WHERE cliente_cedula=%s OR usuario_id IN "
            "(SELECT id FROM db_mantenimiento.usuarios WHERE cedula=%s) "
            "ORDER BY created_at DESC LIMIT 50",
            (cedula, cedula))

    def get_bitacora(self, cedula):
        return self.fetch_all("transalca",
            "SELECT bv.*, v.placa, v.marca, v.modelo "
            "FROM bitacora_vehiculo bv "
            "INNER JOIN vehiculos v ON bv.vehiculo_placa = v.placa "
            "WHERE v.cliente_cedula=%s ORDER BY bv.fecha DESC LIMIT 100",
            (cedula,))
