import smtplib
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.config import MAIL_PASSWORD, MAIL_PORT, MAIL_SERVER, MAIL_USERNAME
from model.connection import Connection
from model.notification_model import NotificationModel


class CreditModel(Connection):
    def __init__(self):
        super().__init__()
        self.notifications = NotificationModel()

    def _today(self):
        return (datetime.utcnow() - timedelta(hours=4)).date()

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

    def _credit_users(self):
        return self.fetch_all("mantenimiento",
            "SELECT DISTINCT u.id FROM usuarios u "
            "INNER JOIN usuario_rol ur ON ur.usuario_id = u.id "
            "INNER JOIN permisos p ON p.rol_id = ur.rol_id "
            "WHERE u.estado = 1 AND p.modulo = 'creditos' AND p.leer = 1")

    def _notify_credit_users(self, title, message, priority='alta'):
        notifications = []
        for user in self._credit_users():
            notifications.append({
                'usuario_id': user['id'],
                'tipo': 'credito',
                'titulo': title,
                'mensaje': message,
                'prioridad': priority
            })
        if notifications:
            self.notifications.create_bulk(notifications)

    def _send_expired_email(self, to_email, company_name, order_id, due_date):
        if not to_email or not MAIL_USERNAME or not MAIL_PASSWORD:
            return False
        subject = f"Crédito vencido orden #{order_id}"
        plain = (
            f"Estimado cliente, el crédito de {company_name} asociado a la orden #{order_id} "
            f"venció el {due_date.strftime('%d/%m/%Y')}. Por favor comuníquese con Transalca C.A."
        )
        html = (
            "<div style='font-family:Arial,sans-serif;color:#1f2937'>"
            "<h2 style='color:#e95d0f'>Crédito vencido</h2>"
            f"<p>Estimado cliente, el crédito de <strong>{company_name}</strong> asociado a la "
            f"orden <strong>#{order_id}</strong> venció el <strong>{due_date.strftime('%d/%m/%Y')}</strong>.</p>"
            "<p>Por favor comuníquese con Transalca C.A. para regularizar el pago.</p>"
            "</div>"
        )
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = MAIL_USERNAME
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(plain, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
            with smtplib.SMTP(MAIL_SERVER, int(MAIL_PORT), timeout=10) as server:
                server.starttls()
                server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.sendmail(MAIL_USERNAME, [to_email], msg.as_string())
            return True
        except Exception:
            return False

    def sync_credit_statuses(self):
        rows = self.fetch_all("transalca",
            "SELECT ov.id, ov.credito_estado, ov.fecha_vencimiento_credito, "
            "COALESCE(ov.monto_deuda, ov.total, 0) AS monto_deuda, "
            "COALESCE(ov.credito_notificacion_7d, 0) AS credito_notificacion_7d, "
            "COALESCE(ov.credito_notificacion_2d, 0) AS credito_notificacion_2d, "
            "COALESCE(ov.credito_notificacion_vencido, 0) AS credito_notificacion_vencido, "
            "c.email, e.razon_social, e.rif "
            "FROM ordenes_venta ov "
            "INNER JOIN clientes c ON c.cedula = ov.cliente_cedula "
            "INNER JOIN empresas e ON e.cliente_cedula = c.cedula "
            "WHERE ov.tipo_pago = 'credito' "
            "AND COALESCE(ov.credito_estado, '') NOT IN ('pagado', 'anulado', 'sin_credito') "
            "AND COALESCE(ov.monto_deuda, ov.total, 0) > 0")
        today = self._today()
        for row in rows:
            due_date = self._as_date(row.get('fecha_vencimiento_credito'))
            if not due_date:
                continue
            days_left = (due_date - today).days
            company = row.get('razon_social') or row.get('rif') or 'Empresa'
            if days_left <= 0:
                if row.get('credito_estado') != 'vencido':
                    self.update("transalca",
                        "UPDATE ordenes_venta SET credito_estado = 'vencido' WHERE id = %s AND tipo_pago = 'credito'",
                        (row['id'],))
                if not int(row.get('credito_notificacion_vencido') or 0):
                    self._notify_credit_users(
                        "Crédito vencido",
                        f"El crédito de {company} para la orden #{row['id']} venció.",
                        'alta'
                    )
                    self._send_expired_email(row.get('email'), company, row['id'], due_date)
                    self.update("transalca",
                        "UPDATE ordenes_venta SET credito_notificacion_vencido = 1 WHERE id = %s",
                        (row['id'],))
                continue
            if days_left <= 2 and not int(row.get('credito_notificacion_2d') or 0):
                self._notify_credit_users(
                    "Crédito por vencer",
                    f"El crédito de {company} para la orden #{row['id']} vence en {days_left} días.",
                    'alta'
                )
                self.update("transalca",
                    "UPDATE ordenes_venta SET credito_notificacion_2d = 1 WHERE id = %s",
                    (row['id'],))
            if days_left <= 7 and not int(row.get('credito_notificacion_7d') or 0):
                self._notify_credit_users(
                    "Crédito por vencer",
                    f"El crédito de {company} para la orden #{row['id']} vence en {days_left} días.",
                    'media'
                )
                self.update("transalca",
                    "UPDATE ordenes_venta SET credito_notificacion_7d = 1 WHERE id = %s",
                    (row['id'],))

    def get_all(self, search=None, estado=None):
        self.sync_credit_statuses()
        sql = (
            "SELECT ov.*, COALESCE(ov.monto_deuda, ov.total, 0) AS monto_deuda, "
            "c.nombre, c.email, c.telefono, e.rif, e.razon_social, e.nombre_comercial, "
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
            if estado == 'activo':
                sql += " AND ov.credito_estado IN ('activo','pendiente','aprobado')"
            else:
                sql += " AND ov.credito_estado = %s"
                params.append(estado)
        sql += " ORDER BY ov.fecha DESC"
        return self.fetch_all("transalca", sql, tuple(params))

    def get_stats(self):
        self.sync_credit_statuses()
        row = self.fetch_one("transalca",
            "SELECT COUNT(*) total, "
            "SUM(CASE WHEN credito_estado IN ('pendiente','aprobado','activo') THEN 1 ELSE 0 END) pendientes, "
            "SUM(CASE WHEN credito_estado='pagado' THEN 1 ELSE 0 END) pagados, "
            "SUM(CASE WHEN credito_estado='vencido' THEN 1 ELSE 0 END) vencidos, "
            "COALESCE(SUM(CASE WHEN credito_estado NOT IN ('pagado','anulado') "
            "THEN COALESCE(monto_deuda,total,0) ELSE 0 END),0) saldo "
            "FROM ordenes_venta WHERE tipo_pago='credito'")
        if not row:
            return {'total': 0, 'pendientes': 0, 'pagados': 0, 'vencidos': 0, 'saldo': 0}
        return {
            'total': row.get('total') or 0,
            'pendientes': row.get('pendientes') or 0,
            'pagados': row.get('pagados') or 0,
            'vencidos': row.get('vencidos') or 0,
            'saldo': row.get('saldo') or 0,
        }

    def update_status(self, order_id, estado):
        if estado == 'pagado':
            return self.mark_paid(order_id)
        if estado == 'anulado':
            return self.update("transalca",
                "UPDATE ordenes_venta SET credito_estado='anulado', monto_deuda=0 WHERE id=%s AND tipo_pago='credito'",
                (order_id,))
        return self.update("transalca",
            "UPDATE ordenes_venta SET credito_estado=%s WHERE id=%s AND tipo_pago='credito'",
            (estado, order_id))

    def get_by_order(self, order_id):
        return self.fetch_one("transalca",
            "SELECT id, total, COALESCE(monto_deuda, total, 0) AS monto_deuda, credito_estado "
            "FROM ordenes_venta WHERE id=%s AND tipo_pago='credito'",
            (order_id,))

    def update_dates(self, order_id, fecha_inicio, fecha_fin):
        return self.update("transalca",
            "UPDATE ordenes_venta SET fecha_inicio_credito=%s, fecha_vencimiento_credito=%s, "
            "credito_estado=CASE WHEN credito_estado IN ('pagado','anulado') THEN credito_estado ELSE 'activo' END, "
            "credito_notificacion_7d=0, credito_notificacion_2d=0, credito_notificacion_vencido=0 "
            "WHERE id=%s AND tipo_pago='credito'",
            (fecha_inicio, fecha_fin, order_id))

    def mark_paid(self, order_id):
        return self.update("transalca",
            "UPDATE ordenes_venta SET credito_estado='pagado', monto_deuda=0, fecha_pago_credito=NOW() "
            "WHERE id=%s AND tipo_pago='credito'",
            (order_id,))

    def register_payment(self, order_id, amount):
        amount = self._as_money(amount)
        if amount <= 0:
            return {'ok': False, 'message': 'El monto del abono debe ser mayor a cero.'}
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, total, COALESCE(monto_deuda, total, 0) AS monto_deuda, credito_estado "
                "FROM ordenes_venta WHERE id=%s AND tipo_pago='credito' FOR UPDATE",
                (order_id,)
            )
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return {'ok': False, 'status_code': 404, 'message': 'Crédito no encontrado.'}
            if row.get('credito_estado') == 'pagado':
                conn.rollback()
                return {'ok': False, 'message': 'Este crédito ya está pagado.'}
            debt = self._as_money(row.get('monto_deuda'))
            if debt <= 0:
                cursor.execute(
                    "UPDATE ordenes_venta SET credito_estado='pagado', monto_deuda=0, fecha_pago_credito=NOW() WHERE id=%s",
                    (order_id,)
                )
                conn.commit()
                return {'ok': True, 'monto_deuda': Decimal("0.00"), 'pagado': True}
            if amount > debt:
                conn.rollback()
                return {'ok': False, 'message': 'El abono no puede ser mayor a la deuda.'}
            new_debt = (debt - amount).quantize(Decimal("0.01"))
            if new_debt == 0:
                cursor.execute(
                    "UPDATE ordenes_venta SET monto_deuda=0, credito_estado='pagado', fecha_pago_credito=NOW() WHERE id=%s",
                    (order_id,)
                )
            else:
                cursor.execute(
                    "UPDATE ordenes_venta SET monto_deuda=%s WHERE id=%s",
                    (new_debt, order_id)
                )
            conn.commit()
            return {'ok': True, 'monto_deuda': new_debt, 'pagado': new_debt == 0}
        except Exception:
            conn.rollback()
            raise
