from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from model.connection import Connection


class PurchaseOrderModel(Connection):
    def __init__(self):
        super().__init__()

    def _as_date(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()

    def _as_money(self, value):
        try:
            return Decimal(str(value or 0)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    def get_all(self, search=None, estado=None):
        sql = (
            "SELECT oc.*, p.nombre AS proveedor_nombre, s.nombre AS sucursal_nombre "
            "FROM ordenes_compra oc "
            "INNER JOIN proveedores p ON p.rif = oc.proveedor_rif "
            "INNER JOIN sucursales s ON s.id = oc.sucursal_id"
        )
        params = []
        where_clauses = []
        if search:
            q = f"%{search}%"
            where_clauses.append("(p.rif LIKE %s OR p.nombre LIKE %s OR oc.id LIKE %s)")
            params.extend([q, q, q])
        if estado:
            where_clauses.append("oc.estado = %s")
            params.append(estado)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " ORDER BY oc.fecha DESC"
        return self.fetch_all("transalca", sql, tuple(params))

    def get_stats(self):
        row = self.fetch_one("transalca",
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN estado='pendiente' THEN 1 ELSE 0 END) AS pendientes, "
            "SUM(CASE WHEN estado='comprado' THEN 1 ELSE 0 END) AS comprados, "
            "COALESCE(SUM(total), 0) AS total_invertido "
            "FROM ordenes_compra")
        if not row:
            return {'total': 0, 'pendientes': 0, 'comprados': 0, 'total_invertido': 0}
        return {
            'total': row.get('total') or 0,
            'pendientes': row.get('pendientes') or 0,
            'comprados': row.get('comprados') or 0,
            'total_invertido': row.get('total_invertido') or 0
        }

    def get_by_id(self, order_id):
        order = self.fetch_one("transalca",
            "SELECT oc.*, p.nombre AS proveedor_nombre, p.telefono AS proveedor_telefono, "
            "p.email AS proveedor_email, p.direccion AS proveedor_direccion, "
            "s.nombre AS sucursal_nombre, s.direccion AS sucursal_direccion "
            "FROM ordenes_compra oc "
            "INNER JOIN proveedores p ON p.rif = oc.proveedor_rif "
            "INNER JOIN sucursales s ON s.id = oc.sucursal_id "
            "WHERE oc.id = %s", (order_id,))
        if order:
            order['detalles'] = self.fetch_all("transalca",
                "SELECT doc.*, prod.nombre AS producto_nombre "
                "FROM detalle_orden_compra doc "
                "INNER JOIN productos prod ON prod.codigo = doc.producto_codigo "
                "WHERE doc.orden_compra_id = %s", (order_id,))
        return order

    def create(self, data):

        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()


            cursor.execute("SELECT id FROM sucursales WHERE id = %s AND estado = 1", (data['sucursal_id'],))
            if not cursor.fetchone():
                conn.rollback()
                return {'ok': False, 'message': 'La sucursal destino no existe o esta inactiva.'}

            cursor.execute("SELECT rif FROM proveedores WHERE rif = %s AND estado = 1", (data['proveedor_rif'],))
            if not cursor.fetchone():
                conn.rollback()
                return {'ok': False, 'message': 'El proveedor no existe o esta inactivo.'}


            total = Decimal("0.00")
            cursor.execute(
                "INSERT INTO ordenes_compra (proveedor_rif, sucursal_id, total, estado, observaciones) "
                "VALUES (%s, %s, %s, 'pendiente', %s)",
                (data['proveedor_rif'], data['sucursal_id'], total, data.get('observaciones', ''))
            )
            order_id = cursor.lastrowid


            for item in data.get('items', []):
                prod_code = item['producto_codigo']
                qty = int(item['cantidad'])
                price = self._as_money(item['precio_unitario'])
                subtotal = (qty * price).quantize(Decimal("0.01"))
                total += subtotal


                cursor.execute("SELECT codigo FROM productos WHERE codigo = %s AND estado = 1", (prod_code,))
                if not cursor.fetchone():
                    conn.rollback()
                    return {'ok': False, 'message': f'El producto con codigo {prod_code} no existe o esta inactivo.'}

                cursor.execute(
                    "INSERT INTO detalle_orden_compra (orden_compra_id, producto_codigo, cantidad, precio_unitario, subtotal) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (order_id, prod_code, qty, price, subtotal)
                )


            cursor.execute(
                "UPDATE ordenes_compra SET total = %s WHERE id = %s",
                (total, order_id)
            )

            conn.commit()
            return {'ok': True, 'id': order_id, 'message': 'Orden de compra registrada correctamente.'}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'message': f'Error al registrar la orden: {str(e)}'}

    def mark_as_bought(self, order_id):
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()


            cursor.execute(
                "SELECT id, sucursal_id, estado FROM ordenes_compra WHERE id = %s FOR UPDATE",
                (order_id,)
            )
            order = cursor.fetchone()
            if not order:
                conn.rollback()
                return {'ok': False, 'message': 'Orden de compra no encontrada.'}
            if order['estado'] == 'comprado':
                conn.rollback()
                return {'ok': False, 'message': 'Esta orden de compra ya ha sido procesada como comprada.'}


            cursor.execute(
                "SELECT producto_codigo, cantidad FROM detalle_orden_compra WHERE orden_compra_id = %s",
                (order_id,)
            )
            details = cursor.fetchall()

            sucursal_id = order['sucursal_id']
            for item in details:
                prod_code = item['producto_codigo']
                qty = item['cantidad']


                cursor.execute(
                    "SELECT stock FROM stock WHERE producto_codigo = %s AND sucursal_id = %s FOR UPDATE",
                    (prod_code, sucursal_id)
                )
                stock_row = cursor.fetchone()
                if stock_row:
                    new_stock = stock_row['stock'] + qty
                    cursor.execute(
                        "UPDATE stock SET stock = %s WHERE producto_codigo = %s AND sucursal_id = %s",
                        (new_stock, prod_code, sucursal_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO stock (producto_codigo, sucursal_id, stock) VALUES (%s, %s, %s)",
                        (prod_code, sucursal_id, qty)
                    )


            cursor.execute(
                "UPDATE ordenes_compra SET estado = 'comprado' WHERE id = %s",
                (order_id,)
            )

            conn.commit()
            return {'ok': True, 'message': 'Orden de compra marcada como comprada. Stock actualizado.'}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'message': f'Error al procesar la compra: {str(e)}'}
