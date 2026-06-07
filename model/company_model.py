from model.connection import Connection


class CompanyModel(Connection):
    def __init__(self):
        super().__init__()

    def _credit_status_sql(self):
        return (
            "CASE "
            "WHEN EXISTS (SELECT 1 FROM ordenes_venta ov WHERE ov.cliente_cedula = c.cedula "
            "AND ov.tipo_pago = 'credito' AND COALESCE(ov.credito_estado,'') NOT IN ('pagado','anulado','sin_credito') "
            "AND COALESCE(ov.monto_deuda, ov.total, 0) > 0 "
            "AND (ov.credito_estado = 'vencido' OR (ov.fecha_vencimiento_credito IS NOT NULL AND ov.fecha_vencimiento_credito <= CURDATE()))) "
            "THEN 'deudora' "
            "WHEN EXISTS (SELECT 1 FROM ordenes_venta ov WHERE ov.cliente_cedula = c.cedula "
            "AND ov.tipo_pago = 'credito' AND COALESCE(ov.credito_estado,'') IN ('pendiente','aprobado','activo') "
            "AND COALESCE(ov.monto_deuda, ov.total, 0) > 0 "
            "AND (ov.fecha_vencimiento_credito IS NULL OR ov.fecha_vencimiento_credito > CURDATE())) "
            "THEN 'credito_activo' "
            "ELSE 'al_dia' END"
        )

    def get_all(self, search=None, estado=None):
        sql = (
            "SELECT c.*, e.rif, e.rif_prefijo, e.razon_social, e.nombre_comercial, "
            "e.sector, e.limite_credito, e.dias_credito, "
            f"{self._credit_status_sql()} AS estado_credito, "
            "(SELECT MIN(ov.fecha_vencimiento_credito) FROM ordenes_venta ov WHERE ov.cliente_cedula = c.cedula "
            "AND ov.tipo_pago='credito' AND COALESCE(ov.credito_estado,'') NOT IN ('pagado','anulado','sin_credito') "
            "AND COALESCE(ov.monto_deuda, ov.total, 0) > 0) AS credito_vencimiento, "
            "(SELECT COUNT(*) FROM cliente_vehiculo cv INNER JOIN vehiculos v ON cv.vehiculo_placa = v.placa WHERE cv.cliente_cedula = c.cedula AND cv.estado = 1 AND v.estado = 1) as flota_count "
            "FROM clientes c INNER JOIN empresas e ON e.rif = c.cedula "
            "WHERE c.tipo_cliente = 'empresa'"
        )
        params = []
        if search:
            q = f"%{search}%"
            sql += (
                " AND (e.rif LIKE %s OR e.razon_social LIKE %s OR e.nombre_comercial LIKE %s "
                "OR c.email LIKE %s OR c.telefono LIKE %s)"
            )
            params.extend([q, q, q, q, q])
        sql += " AND c.estado = %s"
        params.append(int(estado) if estado is not None else 1)
        sql += " ORDER BY c.created_at DESC"
        return self.fetch_all("transalca", sql, tuple(params))

    def get_by_rif(self, rif):
        return self.fetch_one("transalca",
            "SELECT c.*, e.rif, e.rif_prefijo, e.razon_social, e.nombre_comercial, "
            "e.sector, e.limite_credito, e.dias_credito, "
            f"{self._credit_status_sql()} AS estado_credito, "
            "(SELECT MIN(ov.fecha_vencimiento_credito) FROM ordenes_venta ov WHERE ov.cliente_cedula = c.cedula "
            "AND ov.tipo_pago='credito' AND COALESCE(ov.credito_estado,'') NOT IN ('pagado','anulado','sin_credito') "
            "AND COALESCE(ov.monto_deuda, ov.total, 0) > 0) AS credito_vencimiento "
            "FROM clientes c INNER JOIN empresas e ON e.rif = c.cedula "
            "WHERE e.rif = %s OR c.cedula = %s", (rif, rif))

    def create(self, data):
        rif = data['rif']
        existing = self.get_by_rif(rif)
        conn = self.con_transalca()
        conn.begin()
        try:
            if existing:
                self.update("transalca",
                    "UPDATE clientes SET cedula_prefijo=%s, tipo_cliente='empresa', nombre=%s, apellido='Empresa', "
                    "telefono=%s, email=%s, direccion=%s, estado=1 WHERE cedula=%s",
                    (data.get('rif_prefijo'), data['razon_social'], data.get('telefono', ''),
                     data.get('email', ''), data.get('direccion', ''), rif)
                )
                self.update("transalca",
                    "UPDATE empresas SET rif_prefijo=%s, razon_social=%s, nombre_comercial=%s, "
                    "sector=%s, limite_credito=%s, dias_credito=%s WHERE rif=%s",
                    (data.get('rif_prefijo'), data['razon_social'], data.get('nombre_comercial', ''),
                     data.get('sector'), data.get('limite_credito') or 0,
                     data.get('dias_credito') or 0, rif)
                )
            else:
                self.insert("transalca",
                    "INSERT INTO clientes (cedula, cedula_prefijo, tipo_cliente, nombre, apellido, telefono, email, direccion, origen_registro, estado) "
                    "VALUES (%s,%s,'empresa',%s,'Empresa',%s,%s,%s,'admin',1)",
                    (rif, data.get('rif_prefijo'), data['razon_social'], data.get('telefono', ''),
                     data.get('email', ''), data.get('direccion', ''))
                )
                self.insert("transalca",
                    "INSERT INTO empresas (rif, rif_prefijo, razon_social, nombre_comercial, "
                    "sector, limite_credito, dias_credito) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (rif, data.get('rif_prefijo'), data['razon_social'], data.get('nombre_comercial', ''),
                     data.get('sector'), data.get('limite_credito') or 0, data.get('dias_credito') or 0)
                )
            
            # Save or link representative if provided
            rep_cedula = data.get('representante_cedula')
            if rep_cedula:
                rep_existing = self.fetch_one("transalca", "SELECT cedula FROM clientes WHERE cedula = %s", (rep_cedula,))
                if not rep_existing:
                    self.insert("transalca",
                        "INSERT INTO clientes (cedula, cedula_prefijo, tipo_cliente, nombre, apellido, telefono, email, estado, origen_registro) "
                        "VALUES (%s, %s, 'persona', %s, '', %s, %s, 1, 'admin')",
                        (rep_cedula, data.get('representante_cedula_prefijo') or 'V', data.get('representante_nombre', ''),
                         data.get('representante_telefono') or '', data.get('representante_email') or ''))
                
                existing_rel = self.fetch_one("transalca", 
                    "SELECT id, estado FROM empresa_representante WHERE empresa_rif = %s AND representante_cedula = %s",
                    (rif, rep_cedula))
                if not existing_rel:
                    self.insert("transalca",
                        "INSERT INTO empresa_representante (empresa_rif, representante_cedula, cargo, estado) "
                        "VALUES (%s, %s, 'Representante legal', 1)",
                        (rif, rep_cedula))
                elif existing_rel['estado'] == 0:
                    self.update("transalca", "UPDATE empresa_representante SET estado = 1 WHERE id = %s", (existing_rel['id'],))
            
            conn.commit()
            return {'rif': rif, 'reactivated': not bool(existing.get('estado')) if existing else False}
        except Exception:
            conn.rollback()
            raise

    def update_company(self, rif, data):
        conn = self.con_transalca()
        conn.begin()
        try:
            self.update("transalca",
                "UPDATE clientes SET nombre=%s, apellido='Empresa', telefono=%s, email=%s, direccion=%s WHERE cedula=%s AND tipo_cliente='empresa'",
                (data['razon_social'], data.get('telefono', ''), data.get('email', ''), data.get('direccion', ''), rif)
            )
            res = self.update("transalca",
                "UPDATE empresas SET razon_social=%s, nombre_comercial=%s, sector=%s, "
                "limite_credito=%s, dias_credito=%s WHERE rif=%s",
                (data['razon_social'], data.get('nombre_comercial', ''), data.get('sector', ''),
                 data.get('limite_credito') or 0, data.get('dias_credito') or 0, rif)
            )
            
            # Save or link representative if provided
            rep_cedula = data.get('representante_cedula')
            if rep_cedula:
                rep_existing = self.fetch_one("transalca", "SELECT cedula FROM clientes WHERE cedula = %s", (rep_cedula,))
                if not rep_existing:
                    self.insert("transalca",
                        "INSERT INTO clientes (cedula, cedula_prefijo, tipo_cliente, nombre, apellido, telefono, email, estado, origen_registro) "
                        "VALUES (%s, %s, 'persona', %s, '', %s, %s, 1, 'admin')",
                        (rep_cedula, data.get('representante_cedula_prefijo') or 'V', data.get('representante_nombre', ''),
                         data.get('representante_telefono') or '', data.get('representante_email') or ''))
                
                existing_rel = self.fetch_one("transalca", 
                    "SELECT id, estado FROM empresa_representante WHERE empresa_rif = %s AND representante_cedula = %s",
                    (rif, rep_cedula))
                if not existing_rel:
                    self.insert("transalca",
                        "INSERT INTO empresa_representante (empresa_rif, representante_cedula, cargo, estado) "
                        "VALUES (%s, %s, 'Representante legal', 1)",
                        (rif, rep_cedula))
                elif existing_rel['estado'] == 0:
                    self.update("transalca", "UPDATE empresa_representante SET estado = 1 WHERE id = %s", (existing_rel['id'],))
                    
            conn.commit()
            return res
        except Exception:
            conn.rollback()
            raise

    def soft_delete(self, rif):
        return self.update("transalca", "UPDATE clientes SET estado=0 WHERE cedula=%s AND tipo_cliente='empresa'", (rif,))

    def get_stats(self):
        total = self.fetch_one("transalca", "SELECT COUNT(*) total FROM clientes WHERE tipo_cliente='empresa'")
        active = self.fetch_one("transalca", "SELECT COUNT(*) total FROM clientes WHERE tipo_cliente='empresa' AND estado=1")
        return {'total': total['total'] if total else 0, 'activos': active['total'] if active else 0}

    def get_fleet(self, rif):
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa as id "
            "FROM vehiculos v "
            "INNER JOIN cliente_vehiculo cv ON v.placa = cv.vehiculo_placa "
            "WHERE cv.cliente_cedula = %s AND cv.estado = 1 AND v.estado = 1 "
            "ORDER BY cv.created_at DESC",
            (rif,))

    def get_orders(self, rif):
        return self.fetch_all("transalca",
            "SELECT ov.*, mp.nombre AS metodo_pago, mp.nombre AS metodo_pago_nombre "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id = ov.metodo_pago_id "
            "WHERE ov.cliente_cedula=%s ORDER BY ov.id DESC LIMIT 50",
            (rif,))

    def get_representatives(self, rif):
        return self.fetch_all("transalca",
            "SELECT er.id, er.cargo, er.estado, c.cedula, c.cedula_prefijo, c.nombre, c.apellido, c.telefono, c.email "
            "FROM empresa_representante er "
            "INNER JOIN clientes c ON er.representante_cedula = c.cedula "
            "WHERE er.empresa_rif = %s ORDER BY er.created_at DESC", (rif,))

    def add_representative(self, company_rif, data):
        rep_cedula = data['cedula'].strip()
        conn = self.con_transalca()
        conn.begin()
        try:
            rep_existing = self.fetch_one("transalca", "SELECT cedula FROM clientes WHERE cedula = %s", (rep_cedula,))
            if not rep_existing:
                self.insert("transalca",
                    "INSERT INTO clientes (cedula, cedula_prefijo, tipo_cliente, nombre, apellido, telefono, email, estado, origen_registro) "
                    "VALUES (%s, %s, 'persona', %s, %s, %s, %s, 1, 'admin')",
                    (rep_cedula, data.get('cedula_prefijo') or 'V', data['nombre'].strip(), data.get('apellido', '').strip(),
                     data['telefono'].strip(), data.get('email', '').strip()))
            
            existing_rel = self.fetch_one("transalca", 
                "SELECT id, estado FROM empresa_representante WHERE empresa_rif = %s AND representante_cedula = %s",
                (company_rif, rep_cedula))
            if not existing_rel:
                self.insert("transalca",
                    "INSERT INTO empresa_representante (empresa_rif, representante_cedula, cargo, estado) "
                    "VALUES (%s, %s, %s, %s)",
                    (company_rif, rep_cedula, data.get('cargo', 'Otro'), int(data.get('estado', 1))))
            else:
                self.update("transalca",
                    "UPDATE empresa_representante SET cargo = %s, estado = %s WHERE id = %s",
                    (data.get('cargo', 'Otro'), int(data.get('estado', 1)), existing_rel['id']))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise

    def toggle_representative_relation(self, relation_id, estado):
        return self.update("transalca",
            "UPDATE empresa_representante SET estado = %s WHERE id = %s",
            (int(estado), relation_id))
