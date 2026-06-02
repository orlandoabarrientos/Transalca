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
            "e.representante_nombre, e.representante_cedula_prefijo, e.representante_cedula, e.representante_telefono, "
            "e.representante_email, e.sector, e.limite_credito, e.dias_credito, "
            f"{self._credit_status_sql()} AS estado_credito, "
            "(SELECT MIN(ov.fecha_vencimiento_credito) FROM ordenes_venta ov WHERE ov.cliente_cedula = c.cedula "
            "AND ov.tipo_pago='credito' AND COALESCE(ov.credito_estado,'') NOT IN ('pagado','anulado','sin_credito') "
            "AND COALESCE(ov.monto_deuda, ov.total, 0) > 0) AS credito_vencimiento, "
            "(SELECT COUNT(*) FROM vehiculos v WHERE v.cliente_cedula = c.cedula AND v.estado = 1) as flota_count "
            "FROM clientes c INNER JOIN empresas e ON e.cliente_cedula = c.cedula "
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
            "e.representante_nombre, e.representante_cedula_prefijo, e.representante_cedula, e.representante_telefono, "
            "e.representante_email, e.sector, e.limite_credito, e.dias_credito, "
            f"{self._credit_status_sql()} AS estado_credito, "
            "(SELECT MIN(ov.fecha_vencimiento_credito) FROM ordenes_venta ov WHERE ov.cliente_cedula = c.cedula "
            "AND ov.tipo_pago='credito' AND COALESCE(ov.credito_estado,'') NOT IN ('pagado','anulado','sin_credito') "
            "AND COALESCE(ov.monto_deuda, ov.total, 0) > 0) AS credito_vencimiento "
            "FROM clientes c INNER JOIN empresas e ON e.cliente_cedula = c.cedula "
            "WHERE e.rif = %s OR c.cedula = %s", (rif, rif))

    def create(self, data):
        rif = data['rif']
        existing = self.get_by_rif(rif)
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            if existing:
                cursor.execute(
                    "UPDATE clientes SET cedula_prefijo=%s, tipo_cliente='empresa', nombre=%s, apellido='Empresa', "
                    "telefono=%s, email=%s, direccion=%s, estado=1 WHERE cedula=%s",
                    (data.get('rif_prefijo'), data['razon_social'], data.get('telefono', ''),
                     data.get('email', ''), data.get('direccion', ''), rif)
                )
                cursor.execute(
                    "UPDATE empresas SET rif_prefijo=%s, razon_social=%s, nombre_comercial=%s, "
                    "representante_nombre=%s, representante_cedula_prefijo=%s, representante_cedula=%s, representante_telefono=%s, "
                    "representante_email=%s, sector=%s, limite_credito=%s, dias_credito=%s WHERE cliente_cedula=%s",
                    (data.get('rif_prefijo'), data['razon_social'], data.get('nombre_comercial', ''),
                     data.get('representante_nombre', ''), data.get('representante_cedula_prefijo'), data.get('representante_cedula'),
                     data.get('representante_telefono', ''), data.get('representante_email', ''),
                     data.get('sector', ''), data.get('limite_credito') or 0,
                     data.get('dias_credito') or 0, rif)
                )
                conn.commit()
                return {'rif': rif, 'reactivated': not bool(existing.get('estado'))}
            cursor.execute(
                "INSERT INTO clientes (cedula, cedula_prefijo, tipo_cliente, nombre, apellido, telefono, email, direccion, origen_registro, estado) "
                "VALUES (%s,%s,'empresa',%s,'Empresa',%s,%s,%s,'admin',1)",
                (rif, data.get('rif_prefijo'), data['razon_social'], data.get('telefono', ''),
                 data.get('email', ''), data.get('direccion', ''))
            )
            cursor.execute(
                "INSERT INTO empresas (cliente_cedula, rif, rif_prefijo, razon_social, nombre_comercial, "
                "representante_nombre, representante_cedula_prefijo, representante_cedula, representante_telefono, representante_email, "
                "sector, limite_credito, dias_credito) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (rif, rif, data.get('rif_prefijo'), data['razon_social'], data.get('nombre_comercial', ''),
                 data.get('representante_nombre', ''), data.get('representante_cedula_prefijo'), data.get('representante_cedula'),
                 data.get('representante_telefono', ''), data.get('representante_email', ''),
                 data.get('sector', ''), data.get('limite_credito') or 0, data.get('dias_credito') or 0)
            )
            conn.commit()
            return {'rif': rif, 'reactivated': False}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update_company(self, rif, data):
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clientes SET nombre=%s, apellido='Empresa', telefono=%s, email=%s, direccion=%s WHERE cedula=%s AND tipo_cliente='empresa'",
                (data['razon_social'], data.get('telefono', ''), data.get('email', ''), data.get('direccion', ''), rif)
            )
            cursor.execute(
                "UPDATE empresas SET razon_social=%s, nombre_comercial=%s, representante_nombre=%s, "
                "representante_cedula_prefijo=%s, representante_cedula=%s, representante_telefono=%s, representante_email=%s, sector=%s, "
                "limite_credito=%s, dias_credito=%s WHERE cliente_cedula=%s",
                (data['razon_social'], data.get('nombre_comercial', ''), data.get('representante_nombre', ''),
                 data.get('representante_cedula_prefijo'), data.get('representante_cedula'), data.get('representante_telefono', ''),
                 data.get('representante_email', ''), data.get('sector', ''),
                 data.get('limite_credito') or 0, data.get('dias_credito') or 0, rif)
            )
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def soft_delete(self, rif):
        return self.update("transalca", "UPDATE clientes SET estado=0 WHERE cedula=%s AND tipo_cliente='empresa'", (rif,))

    def get_stats(self):
        total = self.fetch_one("transalca", "SELECT COUNT(*) total FROM clientes WHERE tipo_cliente='empresa'")
        active = self.fetch_one("transalca", "SELECT COUNT(*) total FROM clientes WHERE tipo_cliente='empresa' AND estado=1")
        return {'total': total['total'] if total else 0, 'activos': active['total'] if active else 0}

    def get_fleet(self, rif):
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa as id FROM vehiculos v WHERE v.cliente_cedula=%s AND v.estado=1 ORDER BY v.created_at DESC",
            (rif,))

    def get_orders(self, rif):
        return self.fetch_all("transalca",
            "SELECT ov.*, mp.nombre AS metodo_pago, mp.nombre AS metodo_pago_nombre "
            "FROM ordenes_venta ov LEFT JOIN metodos_pago mp ON mp.id = ov.metodo_pago_id "
            "WHERE ov.cliente_cedula=%s ORDER BY ov.id DESC LIMIT 50",
            (rif,))
