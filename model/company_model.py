from model.connection import Connection


DEUDA_SQL = (
    "(ov.total_orden_venta - COALESCE((SELECT SUM(pc.monto_pago) FROM pagos_credito pc "
    "WHERE pc.id_credito = cr.id_credito), 0))"
)


class CompanyModel(Connection):
    def __init__(self):
        super().__init__()
        self._rif = None
        self._razon_social = None
        self._telefono = None
        self._email = None
        self._direccion = None
        self._limite_credito = None
        self._dias_credito = None

    @property
    def rif(self):
        return self._rif

    @rif.setter
    def rif(self, valor):
        if valor:
            valor = str(valor).strip()
        self._rif = valor

    @property
    def razon_social(self):
        return self._razon_social

    @razon_social.setter
    def razon_social(self, valor):
        if valor:
            valor = str(valor).strip()
        self._razon_social = valor

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor:
            valor = str(valor).strip()
        self._telefono = valor

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        if valor:
            valor = str(valor).strip()
        self._email = valor

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._direccion = valor

    @property
    def limite_credito(self):
        return self._limite_credito

    @limite_credito.setter
    def limite_credito(self, valor):
        self._limite_credito = float(valor or 0)

    @property
    def dias_credito(self):
        return self._dias_credito

    @dias_credito.setter
    def dias_credito(self, valor):
        self._dias_credito = int(valor or 0)

    def _credit_status_sql(self):
        return (
            "CASE "
            "WHEN EXISTS (SELECT 1 FROM creditos_orden_venta cr INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
            "WHERE ov.cliente_cedula = c.identificador_cliente "
            "AND cr.estado_credito NOT IN ('pagado','anulado') AND " + DEUDA_SQL + " > 0 "
            "AND (cr.estado_credito = 'vencido' OR (cr.fecha_vencimiento_credito IS NOT NULL AND cr.fecha_vencimiento_credito <= CURDATE()))) "
            "THEN 'deudora' "
            "WHEN EXISTS (SELECT 1 FROM creditos_orden_venta cr INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
            "WHERE ov.cliente_cedula = c.identificador_cliente "
            "AND cr.estado_credito IN ('pendiente','aprobado','activo') AND " + DEUDA_SQL + " > 0 "
            "AND (cr.fecha_vencimiento_credito IS NULL OR cr.fecha_vencimiento_credito > CURDATE())) "
            "THEN 'credito_activo' "
            "ELSE 'al_dia' END"
        )

    def _company_select(self):
        return "".join([
            "SELECT c.identificador_cliente AS cedula, c.identificador_cliente AS rif, NULL AS rif_prefijo, ",
            "c.nombre_cliente AS razon_social, c.nombre_cliente AS nombre, '' AS apellido, NULL AS nombre_comercial, ",
            "c.correo_cliente AS email, c.telefono_cliente AS telefono, c.direccion_cliente AS direccion, ",
            "c.tipo_cliente, c.estado, c.id_cliente, c.created_at, c.updated_at, ",
            "j.id_juridica, j.sector, j.limite_credito, j.dias_credito, ",
            self._credit_status_sql(), " AS estado_credito, ",
            "(SELECT MIN(cr.fecha_vencimiento_credito) FROM creditos_orden_venta cr INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id ",
            "WHERE ov.cliente_cedula = c.identificador_cliente ",
            "AND cr.estado_credito NOT IN ('pagado','anulado') AND " + DEUDA_SQL + " > 0) AS credito_vencimiento, ",
            "(SELECT COUNT(*) FROM cliente_vehiculo cv INNER JOIN vehiculos v ON cv.vehiculo_placa = v.placa_vehiculo ",
            "WHERE cv.cliente_cedula = c.identificador_cliente AND cv.estado = 1 AND v.estado = 1) as flota_count ",
            "FROM cliente c INNER JOIN cliente_juridico j ON j.id_cliente = c.id_cliente ",
            "WHERE c.tipo_cliente = 'juridica'",
        ])

    def _get_all(self, search=None, estado=None):
        sql = self._company_select()
        params = []
        if search:
            q = f"%{search}%"
            sql += " AND (c.identificador_cliente LIKE %s OR c.nombre_cliente LIKE %s OR c.correo_cliente LIKE %s OR c.telefono_cliente LIKE %s)"
            params.extend([q, q, q, q])
        sql += " AND c.estado = %s"
        params.append(int(estado) if estado is not None else 1)
        sql += " ORDER BY c.created_at DESC"
        return self.fetch_all("transalca", sql, tuple(params))

    def _get_by_rif(self, rif):
        sql = self._company_select() + " AND c.identificador_cliente = %s"
        return self.fetch_one("transalca", sql, (rif,))

    def _create(self, data):
        self.rif = data['rif']
        self.razon_social = data['razon_social']
        self.telefono = data.get('telefono', '')
        self.email = data.get('email', '')
        self.direccion = data.get('direccion', '')
        self.limite_credito = data.get('limite_credito')
        self.dias_credito = data.get('dias_credito')
        rif = self._rif
        existing = self._get_by_rif(rif)
        conn = self.con_transalca()
        conn.begin()
        try:
            if existing:
                self.update("transalca",
                    "UPDATE cliente SET nombre_cliente=%s, telefono_cliente=%s, correo_cliente=%s, direccion_cliente=%s, "
                    "tipo_cliente='juridica', estado=1 WHERE identificador_cliente=%s",
                    (self._razon_social, self._telefono, self._email, self._direccion, rif))
                self.update("transalca",
                    "UPDATE cliente_juridico SET sector=%s, limite_credito=%s, dias_credito=%s WHERE id_cliente=%s",
                    (data.get('sector'), self._limite_credito, self._dias_credito, existing['id_cliente']))
            else:
                cliente_id = self.insert("transalca",
                    "INSERT INTO cliente (nombre_cliente, correo_cliente, identificador_cliente, telefono_cliente, direccion_cliente, tipo_cliente, estado) "
                    "VALUES (%s, %s, %s, %s, %s, 'juridica', 1)",
                    (self._razon_social, self._email, rif, self._telefono, self._direccion))
                self.insert("transalca",
                    "INSERT INTO cliente_juridico (id_cliente, sector, limite_credito, dias_credito) VALUES (%s,%s,%s,%s)",
                    (cliente_id, data.get('sector'), self._limite_credito, self._dias_credito))
            conn.commit()
            return {'rif': rif, 'reactivated': not bool(existing.get('estado')) if existing else False}
        except Exception:
            conn.rollback()
            raise

    def _update_company(self, rif, data):
        self.razon_social = data['razon_social']
        self.telefono = data.get('telefono', '')
        self.email = data.get('email', '')
        self.direccion = data.get('direccion', '')
        self.limite_credito = data.get('limite_credito')
        self.dias_credito = data.get('dias_credito')
        conn = self.con_transalca()
        conn.begin()
        try:
            self.update("transalca",
                "UPDATE cliente SET nombre_cliente=%s, telefono_cliente=%s, correo_cliente=%s, direccion_cliente=%s "
                "WHERE identificador_cliente=%s AND tipo_cliente='juridica'",
                (self._razon_social, self._telefono, self._email, self._direccion, rif))
            res = self.update("transalca",
                "UPDATE cliente_juridico j INNER JOIN cliente c ON c.id_cliente = j.id_cliente "
                "SET j.sector=%s, j.limite_credito=%s, j.dias_credito=%s WHERE c.identificador_cliente=%s",
                (data.get('sector', ''), self._limite_credito, self._dias_credito, rif))
            conn.commit()
            return res
        except Exception:
            conn.rollback()
            raise

    def _soft_delete(self, rif):
        return self.update("transalca",
            "UPDATE cliente SET estado=0 WHERE identificador_cliente=%s AND tipo_cliente='juridica'", (rif,))

    def _get_stats(self):
        total = self.fetch_one("transalca", "SELECT COUNT(*) total FROM cliente WHERE tipo_cliente='juridica'")
        active = self.fetch_one("transalca", "SELECT COUNT(*) total FROM cliente WHERE tipo_cliente='juridica' AND estado=1")
        return {'total': total['total'] if total else 0, 'activos': active['total'] if active else 0}

    def _get_fleet(self, rif):
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa_vehiculo as id, v.placa_vehiculo as placa, v.marca_vehiculo as marca, "
            "v.modelo_vehiculo as modelo, v.anio_vehiculo as anio, v.color_vehiculo as color "
            "FROM vehiculos v "
            "INNER JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa "
            "WHERE cv.cliente_cedula = %s AND cv.estado = 1 AND v.estado = 1 "
            "ORDER BY cv.created_at DESC",
            (rif,))

    def _get_orders(self, rif):
        return self.fetch_all("transalca",
            "SELECT ov.*, ov.id_orden_venta AS id, ov.fecha_orden_venta AS fecha, ov.total_orden_venta AS total, mp.nombre_metodo_pago AS metodo_pago, mp.nombre_metodo_pago AS metodo_pago_nombre, mp.moneda "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE ov.cliente_cedula=%s ORDER BY ov.id_orden_venta DESC LIMIT 50",
            (rif,))

    def _get_representatives(self, rif):
        return self.fetch_all("transalca",
            "SELECT er.id_empresa_representante AS id, er.cargo, er.estado, r.cedula_representante AS cedula, NULL AS cedula_prefijo, "
            "r.nombre_representante AS nombre, '' AS apellido, r.telefono_representante AS telefono, r.email_representante AS email "
            "FROM empresa_representante er "
            "INNER JOIN representantes r ON er.representante_cedula = r.cedula_representante "
            "WHERE er.empresa_rif = %s ORDER BY er.created_at DESC", (rif,))

    def _add_representative(self, company_rif, data):
        rep_cedula = data['cedula'].strip()
        nombre = (data['nombre'].strip() + ' ' + (data.get('apellido') or '').strip()).strip()
        conn = self.con_transalca()
        conn.begin()
        try:
            self.insert("transalca",
                "INSERT INTO representantes (cedula_representante, nombre_representante, telefono_representante, email_representante) "
                "VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE nombre_representante = VALUES(nombre_representante), "
                "telefono_representante = VALUES(telefono_representante), email_representante = VALUES(email_representante), estado = 1",
                (rep_cedula, nombre, data['telefono'].strip(), data.get('email', '').strip()))

            existing_rel = self.fetch_one("transalca",
                "SELECT id_empresa_representante AS id, estado FROM empresa_representante WHERE empresa_rif = %s AND representante_cedula = %s",
                (company_rif, rep_cedula))
            if not existing_rel:
                self.insert("transalca",
                    "INSERT INTO empresa_representante (empresa_rif, representante_cedula, cargo, estado) "
                    "VALUES (%s, %s, %s, %s)",
                    (company_rif, rep_cedula, data.get('cargo', 'Otro'), int(data.get('estado', 1))))
            else:
                self.update("transalca",
                    "UPDATE empresa_representante SET cargo = %s, estado = %s WHERE id_empresa_representante = %s",
                    (data.get('cargo', 'Otro'), int(data.get('estado', 1)), existing_rel['id']))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise

    def _toggle_representative_relation(self, relation_id, estado):
        return self.update("transalca",
            "UPDATE empresa_representante SET estado = %s WHERE id_empresa_representante = %s",
            (int(estado), relation_id))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_rif": self._get_by_rif,
            "create": self._create,
            "update_company": self._update_company,
            "soft_delete": self._soft_delete,
            "get_stats": self._get_stats,
            "get_fleet": self._get_fleet,
            "get_orders": self._get_orders,
            "get_representatives": self._get_representatives,
            "add_representative": self._add_representative,
            "toggle_representative_relation": self._toggle_representative_relation,
            "email_exists_globally": self.email_exists_globally,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
