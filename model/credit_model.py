from model.connection import Connection


class CreditModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self, search=None, estado=None):
        sql = (
            "SELECT ov.*, c.nombre, c.email, c.telefono, e.rif, e.razon_social, e.nombre_comercial, "
            "e.limite_credito, e.dias_credito, mp.nombre AS metodo_pago_nombre "
            "FROM ordenes_venta ov "
            "INNER JOIN clientes c ON c.cedula = ov.cliente_cedula "
            "INNER JOIN empresas e ON e.cliente_cedula = c.cedula "
            "LEFT JOIN metodos_pago mp ON mp.id = ov.metodo_pago_id "
            "WHERE c.tipo_cliente = 'empresa' AND ov.tipo_pago = 'credito'"
        )
        params = []
        if search:
            q = f"%{search}%"
            sql += " AND (e.rif LIKE %s OR e.razon_social LIKE %s OR ov.id LIKE %s)"
            params.extend([q, q, q])
        if estado:
            sql += " AND ov.credito_estado = %s"
            params.append(estado)
        sql += " ORDER BY ov.fecha DESC"
        return self.fetch_all("transalca", sql, tuple(params))

    def get_stats(self):
        row = self.fetch_one("transalca",
            "SELECT COUNT(*) total, "
            "SUM(CASE WHEN credito_estado='pendiente' THEN 1 ELSE 0 END) pendientes, "
            "SUM(CASE WHEN credito_estado='pagado' THEN 1 ELSE 0 END) pagados, "
            "COALESCE(SUM(CASE WHEN credito_estado!='pagado' THEN total ELSE 0 END),0) saldo "
            "FROM ordenes_venta WHERE tipo_pago='credito'")
        if not row:
            return {'total': 0, 'pendientes': 0, 'pagados': 0, 'saldo': 0}
        return {
            'total': row.get('total') or 0,
            'pendientes': row.get('pendientes') or 0,
            'pagados': row.get('pagados') or 0,
            'saldo': row.get('saldo') or 0,
        }

    def update_status(self, order_id, estado):
        return self.update("transalca",
            "UPDATE ordenes_venta SET credito_estado=%s WHERE id=%s AND tipo_pago='credito'",
            (estado, order_id))
