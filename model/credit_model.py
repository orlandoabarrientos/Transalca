import smtplib
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.config import MAIL_PASSWORD, MAIL_PORT, MAIL_SERVER, MAIL_USERNAME
from config.validation import ValidationError
from model.connection import Connection
from model.notification_model import NotificationModel

ALLOWED_STATUS = {'pendiente', 'aprobado', 'activo', 'pagado', 'vencido', 'anulado'}


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

    def _validate_date(self, value, field, errors):
        raw = value.strip() if isinstance(value, str) else value
        if not raw:
            errors[field] = "La fecha es obligatoria."
            return None
        try:
            return self._as_date(raw)
        except (ValueError, TypeError):
            errors[field] = "La fecha no es válida."
            return None

    def _validate_amount(self, value, field, errors, label):
        raw = str(value if value is not None else '').strip().replace(',', '.')
        if not raw:
            errors[field] = f"{label} es obligatorio."
            return None
        try:
            amount = Decimal(raw).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            errors[field] = f"{label} no es válido."
            return None
        if amount <= 0:
            errors[field] = f"{label} debe ser mayor a cero."
            return None
        return amount

    def _paid_amount(self, id_credito):
        row = self.fetch_one("transalca",
            "SELECT COALESCE(SUM(monto_pago), 0) AS pagado FROM pagos_credito "
            "WHERE id_credito=%s AND revertido=0", (id_credito,))
        return self._as_money(row.get('pagado') if row else 0)

    def _estado_por_saldo(self, saldo, fecha_fin):
        if self._as_money(saldo) <= 0:
            return 'pagado'
        end = self._as_date(fecha_fin)
        if end and end < self._today():
            return 'vencido'
        return 'activo'

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
            self.notifications.ejecutar("create_bulk", notifications)

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

    def _sync_credit_statuses(self):
        rows = self.fetch_all("transalca",
            "SELECT cr.id_credito, cr.orden_venta_id AS id, cr.estado_credito, cr.fecha_vencimiento_credito, "
            "(ov.total_orden_venta - COALESCE((SELECT SUM(pc.monto_pago) FROM pagos_credito pc WHERE pc.id_credito = cr.id_credito AND pc.revertido = 0), 0)) AS monto_deuda, "
            "COALESCE(cr.notificacion_7d, 0) AS notificacion_7d, "
            "COALESCE(cr.notificacion_2d, 0) AS notificacion_2d, "
            "COALESCE(cr.notificacion_vencido, 0) AS notificacion_vencido, "
            "c.correo_cliente AS email, c.nombre_cliente AS razon_social, c.identificador_cliente AS rif "
            "FROM creditos_orden_venta cr "
            "INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
            "INNER JOIN cliente c ON c.identificador_cliente = ov.cliente_cedula "
            "WHERE cr.estado_credito NOT IN ('pagado', 'anulado')")
        today = self._today()
        for row in rows:
            if self._as_money(row.get('monto_deuda')) <= 0:
                continue
            due_date = self._as_date(row.get('fecha_vencimiento_credito'))
            if not due_date:
                continue
            days_left = (due_date - today).days
            company = row.get('razon_social') or row.get('rif') or 'Empresa'
            if days_left <= 0:
                if row.get('estado_credito') != 'vencido':
                    self.update("transalca",
                        "UPDATE creditos_orden_venta SET estado_credito = 'vencido' WHERE id_credito = %s",
                        (row['id_credito'],))
                if not int(row.get('notificacion_vencido') or 0):
                    self._notify_credit_users(
                        "Crédito vencido",
                        f"El crédito de {company} para la orden #{row['id']} venció.",
                        'alta'
                    )
                    self._send_expired_email(row.get('email'), company, row['id'], due_date)
                    self.update("transalca",
                        "UPDATE creditos_orden_venta SET notificacion_vencido = 1 WHERE id_credito = %s",
                        (row['id_credito'],))
                continue
            if days_left <= 2 and not int(row.get('notificacion_2d') or 0):
                self._notify_credit_users(
                    "Crédito por vencer",
                    f"El crédito de {company} para la orden #{row['id']} vence en {days_left} días.",
                    'alta'
                )
                self.update("transalca",
                    "UPDATE creditos_orden_venta SET notificacion_2d = 1 WHERE id_credito = %s",
                    (row['id_credito'],))
            if days_left <= 7 and not int(row.get('notificacion_7d') or 0):
                self._notify_credit_users(
                    "Crédito por vencer",
                    f"El crédito de {company} para la orden #{row['id']} vence en {days_left} días.",
                    'media'
                )
                self.update("transalca",
                    "UPDATE creditos_orden_venta SET notificacion_7d = 1 WHERE id_credito = %s",
                    (row['id_credito'],))

    def _get_all(self, search=None, estado=None):
        self._sync_credit_statuses()
        sql = (
            "SELECT ov.id_orden_venta AS id, ov.cliente_cedula, DATE_FORMAT(ov.fecha_orden_venta, '%%Y-%%m-%%d') AS fecha, ov.total_orden_venta AS total, ov.estado AS estado_orden, "
            "ov.tipo_pago, mp.moneda, "
            "cr.id_credito, cr.estado_credito AS credito_estado, DATE_FORMAT(cr.fecha_inicio_credito, '%%Y-%%m-%%d') AS fecha_inicio_credito, "
            "DATE_FORMAT(cr.fecha_vencimiento_credito, '%%Y-%%m-%%d') AS fecha_vencimiento_credito, DATE_FORMAT(cr.fecha_pago_credito, '%%Y-%%m-%%dT%%H:%%i:%%s') AS fecha_pago_credito, "
            "(ov.total_orden_venta - COALESCE((SELECT SUM(pc.monto_pago) FROM pagos_credito pc WHERE pc.id_credito = cr.id_credito AND pc.revertido = 0), 0)) AS monto_deuda, "
            "c.nombre_cliente AS nombre, c.correo_cliente AS email, c.telefono_cliente AS telefono, "
            "c.identificador_cliente AS rif, c.nombre_cliente AS razon_social, "
            "j.limite_credito, j.dias_credito, mp.nombre_metodo_pago AS metodo_pago_nombre "
            "FROM creditos_orden_venta cr "
            "INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
            "INNER JOIN cliente c ON c.identificador_cliente = ov.cliente_cedula "
            "LEFT JOIN cliente_juridico j ON j.id_cliente = c.id_cliente "
            "LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id "
            "WHERE 1=1"
        )
        params = []
        if search:
            q = f"%{search}%"
            sql += " AND (c.identificador_cliente LIKE %s OR c.nombre_cliente LIKE %s OR ov.id_orden_venta LIKE %s)"
            params.extend([q, q, q])
        if estado:
            if estado == 'activo':
                sql += " AND cr.estado_credito IN ('activo','pendiente','aprobado')"
            else:
                sql += " AND cr.estado_credito = %s"
                params.append(estado)
        sql += " ORDER BY ov.fecha_orden_venta DESC"
        return self.fetch_all("transalca", sql, tuple(params))

    def _get_stats(self):
        self._sync_credit_statuses()
        row = self.fetch_one("transalca",
            "SELECT COUNT(*) total, "
            "SUM(CASE WHEN cr.estado_credito IN ('pendiente','aprobado','activo') THEN 1 ELSE 0 END) pendientes, "
            "SUM(CASE WHEN cr.estado_credito='pagado' THEN 1 ELSE 0 END) pagados, "
            "SUM(CASE WHEN cr.estado_credito='vencido' THEN 1 ELSE 0 END) vencidos, "
            "COALESCE(SUM(CASE WHEN cr.estado_credito NOT IN ('pagado','anulado') "
            "THEN (ov.total_orden_venta - COALESCE((SELECT SUM(pc.monto_pago) FROM pagos_credito pc WHERE pc.id_credito = cr.id_credito AND pc.revertido = 0), 0)) ELSE 0 END),0) saldo "
            "FROM creditos_orden_venta cr INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id")
        if not row:
            return {'total': 0, 'pendientes': 0, 'pagados': 0, 'vencidos': 0, 'saldo': 0}
        return {
            'total': row.get('total') or 0,
            'pendientes': row.get('pendientes') or 0,
            'pagados': row.get('pagados') or 0,
            'vencidos': row.get('vencidos') or 0,
            'saldo': row.get('saldo') or 0,
        }

    def _update_status(self, order_id, estado):
        estado = (estado or '').strip().lower()
        if estado not in ALLOWED_STATUS:
            raise ValidationError({'estado': "El estado seleccionado no es válido."})
        if estado == 'pagado':
            return self._mark_paid(order_id)
        return self.update("transalca",
            "UPDATE creditos_orden_venta SET estado_credito=%s WHERE orden_venta_id=%s",
            (estado, order_id))

    def _get_by_order(self, order_id):
        return self.fetch_one("transalca",
            "SELECT ov.id_orden_venta AS id, ov.total_orden_venta AS total, cr.id_credito, "
            "(ov.total_orden_venta - COALESCE((SELECT SUM(pc.monto_pago) FROM pagos_credito pc WHERE pc.id_credito = cr.id_credito AND pc.revertido = 0), 0)) AS monto_deuda, cr.estado_credito AS credito_estado, "
            "cr.fecha_inicio_credito, cr.fecha_vencimiento_credito, cr.fecha_pago_credito "
            "FROM creditos_orden_venta cr INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
            "WHERE ov.id_orden_venta=%s",
            (order_id,))

    def _get_payments(self, order_id):
        return self.fetch_all("transalca",
            "SELECT pc.id_pago_credito, pc.monto_pago, DATE_FORMAT(pc.fecha_pago, '%%Y-%%m-%%d') AS fecha_pago, "
            "pc.observaciones_pago, pc.revertido, pc.fecha_reversion "
            "FROM pagos_credito pc INNER JOIN creditos_orden_venta cr ON cr.id_credito = pc.id_credito "
            "WHERE cr.orden_venta_id = %s ORDER BY pc.fecha_pago DESC",
            (order_id,))

    def _update_credit(self, order_id, fecha_inicio, fecha_fin, total):
        credit = self._get_by_order(order_id)
        if not credit:
            return {'ok': False, 'status_code': 404, 'message': 'Crédito no encontrado.'}
        if credit.get('credito_estado') == 'anulado':
            return {'ok': False, 'message': 'El crédito está anulado y no permite nuevas operaciones.'}
        errors = {}
        start = self._validate_date(fecha_inicio, 'fecha_inicio', errors)
        end = self._validate_date(fecha_fin, 'fecha_fin', errors)
        if start and end and end < start:
            errors['fecha_fin'] = "La fecha fin no puede ser menor a la fecha inicio."
        amount = self._validate_amount(total, 'total', errors, "El monto")
        if errors:
            raise ValidationError(errors)
        pagado = self._paid_amount(credit['id_credito'])
        if amount < pagado:
            raise ValidationError({'total': "El monto no puede ser menor a los abonos registrados."})
        saldo = (amount - pagado).quantize(Decimal("0.01"))
        estado = self._estado_por_saldo(saldo, end)
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            self._set_session_variables(cursor)
            cursor.execute(
                "UPDATE ordenes_venta SET total_orden_venta=%s WHERE id_orden_venta=%s",
                (amount, order_id))
            if estado == 'pagado':
                cursor.execute(
                    "UPDATE creditos_orden_venta SET fecha_inicio_credito=%s, fecha_vencimiento_credito=%s, "
                    "estado_credito='pagado', fecha_pago_credito=COALESCE(fecha_pago_credito, NOW()), "
                    "notificacion_7d=0, notificacion_2d=0, notificacion_vencido=0 WHERE orden_venta_id=%s",
                    (start, end, order_id))
            else:
                cursor.execute(
                    "UPDATE creditos_orden_venta SET fecha_inicio_credito=%s, fecha_vencimiento_credito=%s, "
                    "estado_credito=%s, fecha_pago_credito=NULL, "
                    "notificacion_7d=0, notificacion_2d=0, notificacion_vencido=0 WHERE orden_venta_id=%s",
                    (start, end, estado, order_id))
            conn.commit()
            return {'ok': True, 'message': 'Crédito modificado correctamente.'}
        except Exception:
            conn.rollback()
            raise

    def _mark_paid(self, order_id):
        credit = self._get_by_order(order_id)
        if not credit:
            return {'ok': False, 'status_code': 404, 'message': 'Crédito no encontrado.'}
        if credit.get('credito_estado') == 'anulado':
            return {'ok': False, 'message': 'El crédito está anulado y no permite nuevas operaciones.'}
        remaining = self._as_money(credit.get('monto_deuda'))
        if remaining > 0:
            self.insert("transalca",
                "INSERT INTO pagos_credito (id_credito, monto_pago, observaciones_pago) VALUES (%s, %s, %s)",
                (credit['id_credito'], remaining, 'Pago total del credito'))
        self.update("transalca",
            "UPDATE creditos_orden_venta SET estado_credito='pagado', fecha_pago_credito=NOW() "
            "WHERE orden_venta_id=%s",
            (order_id,))
        return {'ok': True, 'message': 'Crédito pagado correctamente.'}

    def _revert_last_payment(self, order_id):
        credit = self._get_by_order(order_id)
        if not credit:
            return {'ok': False, 'status_code': 404, 'message': 'Crédito no encontrado.'}
        if credit.get('credito_estado') == 'anulado':
            return {'ok': False, 'message': 'El crédito está anulado y no permite nuevas operaciones.'}
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            self._set_session_variables(cursor)
            cursor.execute(
                "SELECT pc.id_pago_credito, pc.monto_pago, pc.fecha_pago FROM pagos_credito pc "
                "INNER JOIN creditos_orden_venta cr ON cr.id_credito = pc.id_credito "
                "INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
                "WHERE ov.id_orden_venta=%s AND pc.revertido=0 "
                "ORDER BY pc.fecha_pago DESC, pc.id_pago_credito DESC LIMIT 1 FOR UPDATE",
                (order_id,))
            pago = cursor.fetchone()
            if not pago:
                conn.rollback()
                return {'ok': False, 'message': 'No hay abonos para revertir.'}
            cursor.execute(
                "UPDATE pagos_credito SET revertido=1, fecha_reversion=NOW() WHERE id_pago_credito=%s",
                (pago['id_pago_credito'],))
            cursor.execute(
                "SELECT ov.total_orden_venta AS total, cr.id_credito, cr.fecha_vencimiento_credito, "
                "COALESCE((SELECT SUM(p.monto_pago) FROM pagos_credito p WHERE p.id_credito = cr.id_credito AND p.revertido=0), 0) AS pagado "
                "FROM creditos_orden_venta cr INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
                "WHERE ov.id_orden_venta=%s", (order_id,))
            row = cursor.fetchone()
            saldo = (self._as_money(row['total']) - self._as_money(row['pagado'])).quantize(Decimal("0.01"))
            estado = self._estado_por_saldo(saldo, row.get('fecha_vencimiento_credito'))
            cursor.execute(
                "UPDATE creditos_orden_venta SET estado_credito=%s, fecha_pago_credito=NULL, "
                "notificacion_7d=0, notificacion_2d=0, notificacion_vencido=0 WHERE orden_venta_id=%s",
                (estado, order_id))
            conn.commit()
            self._log_credito('MODIFICAR',
                f"Ultimo abono revertido orden: {order_id} por ${self._as_money(pago['monto_pago'])}")
            return {'ok': True, 'message': 'Último abono revertido correctamente.'}
        except Exception:
            conn.rollback()
            raise

    def _anular_credit(self, order_id):
        credit = self._get_by_order(order_id)
        if not credit:
            return {'ok': False, 'status_code': 404, 'message': 'Crédito no encontrado.'}
        estado = credit.get('credito_estado')
        if estado == 'anulado':
            return {'ok': False, 'message': 'El crédito ya está anulado.'}
        if estado == 'pagado':
            return {'ok': False, 'message': 'No se puede anular un crédito pagado. Primero debe revertir el último pago.'}
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            self._set_session_variables(cursor)
            cursor.execute(
                "UPDATE creditos_orden_venta SET estado_credito='anulado', "
                "notificacion_7d=0, notificacion_2d=0, notificacion_vencido=0 WHERE orden_venta_id=%s",
                (order_id,))
            conn.commit()
            self._log_credito('ANULAR', f"Credito anulado orden: {order_id}")
            return {'ok': True, 'message': 'Crédito anulado correctamente.'}
        except Exception:
            conn.rollback()
            raise

    def _log_credito(self, accion, descripcion):
        try:
            self.insert("mantenimiento",
                "INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip) "
                "VALUES (COALESCE(@current_usuario_id, 1), %s, 'CREDITO', %s, COALESCE(@current_ip, '127.0.0.1'))",
                (accion, descripcion))
        except Exception:
            pass

    def _create_credit_for_order(self, order_id, fecha_inicio=None, dias_credito=0):
        fecha_inicio = self._as_date(fecha_inicio) or self._today()
        fecha_fin = fecha_inicio + timedelta(days=int(dias_credito or 0))
        return self.insert("transalca",
            "INSERT INTO creditos_orden_venta (orden_venta_id, fecha_inicio_credito, fecha_vencimiento_credito, estado_credito) "
            "VALUES (%s, %s, %s, 'activo') "
            "ON DUPLICATE KEY UPDATE fecha_inicio_credito = VALUES(fecha_inicio_credito), "
            "fecha_vencimiento_credito = VALUES(fecha_vencimiento_credito)",
            (order_id, fecha_inicio, fecha_fin))

    def _create_credit(self, data):
        errors = {}
        cliente_cedula = (data.get('cliente_cedula') or '').strip()
        if not cliente_cedula:
            errors['cliente_cedula'] = "La empresa es obligatoria."
        total = self._validate_amount(data.get('total'), 'total', errors, "El monto")
        fecha_inicio = self._validate_date(data.get('fecha_inicio'), 'fecha_inicio', errors)
        fecha_fin = self._validate_date(data.get('fecha_fin'), 'fecha_fin', errors)
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            errors['fecha_fin'] = "La fecha fin no puede ser menor a la fecha inicio."
        if errors:
            raise ValidationError(errors)
        client = self.fetch_one("transalca",
            "SELECT c.identificador_cliente AS cedula, j.dias_credito FROM cliente c "
            "INNER JOIN cliente_juridico j ON j.id_cliente = c.id_cliente "
            "WHERE c.identificador_cliente = %s AND c.estado = 1",
            (cliente_cedula,))
        if not client:
            return {'ok': False, 'message': 'La empresa no existe o esta inactiva.'}
        try:
            order_id = self.insert("transalca",
                "INSERT INTO ordenes_venta (cliente_cedula, total_orden_venta, tipo_pago, tasa_cambio_id) "
                "VALUES (%s, %s, 'credito', "
                "(SELECT t.id_tasa_cambio FROM tasas_cambio t WHERE t.tipo_tasa_cambio='bcv' ORDER BY t.fecha_tasa_cambio DESC, t.id_tasa_cambio DESC LIMIT 1))",
                (cliente_cedula, total))
            self.insert("transalca",
                "INSERT INTO creditos_orden_venta (orden_venta_id, fecha_inicio_credito, fecha_vencimiento_credito, estado_credito) "
                "VALUES (%s, %s, %s, 'activo')",
                (order_id, fecha_inicio, fecha_fin))
            return {'ok': True, 'id': order_id, 'message': 'Crédito registrado correctamente.'}
        except Exception as e:
            return {'ok': False, 'message': f'Error al registrar el credito: {str(e)}'}

    def _register_payment(self, order_id, amount, observaciones=None):
        errors = {}
        amount = self._validate_amount(amount, 'monto', errors, "El monto del abono")
        if errors:
            raise ValidationError(errors)
        conn = self.con_transalca()
        try:
            conn.begin()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cr.id_credito, ov.total_orden_venta AS total, cr.estado_credito, "
                "(ov.total_orden_venta - COALESCE((SELECT SUM(pc.monto_pago) FROM pagos_credito pc WHERE pc.id_credito = cr.id_credito AND pc.revertido = 0), 0)) AS monto_deuda "
                "FROM creditos_orden_venta cr INNER JOIN ordenes_venta ov ON ov.id_orden_venta = cr.orden_venta_id "
                "WHERE ov.id_orden_venta=%s FOR UPDATE",
                (order_id,)
            )
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return {'ok': False, 'status_code': 404, 'message': 'Crédito no encontrado.'}
            if row.get('estado_credito') == 'anulado':
                conn.rollback()
                return {'ok': False, 'message': 'El crédito está anulado y no permite nuevas operaciones.'}
            if row.get('estado_credito') == 'pagado':
                conn.rollback()
                return {'ok': False, 'message': 'Este crédito ya está pagado.'}
            debt = self._as_money(row.get('monto_deuda'))
            if debt <= 0:
                cursor.execute(
                    "UPDATE creditos_orden_venta SET estado_credito='pagado', fecha_pago_credito=NOW() WHERE id_credito=%s",
                    (row['id_credito'],)
                )
                conn.commit()
                return {'ok': True, 'monto_deuda': Decimal("0.00"), 'pagado': True}
            if amount > debt:
                conn.rollback()
                return {'ok': False, 'message': 'El abono no puede ser mayor a la deuda.'}
            cursor.execute(
                "INSERT INTO pagos_credito (id_credito, monto_pago, observaciones_pago) VALUES (%s, %s, %s)",
                (row['id_credito'], amount, observaciones or 'Abono registrado')
            )
            new_debt = (debt - amount).quantize(Decimal("0.01"))
            if new_debt == 0:
                cursor.execute(
                    "UPDATE creditos_orden_venta SET estado_credito='pagado', fecha_pago_credito=NOW() WHERE id_credito=%s",
                    (row['id_credito'],)
                )
            conn.commit()
            return {'ok': True, 'monto_deuda': new_debt, 'pagado': new_debt == 0}
        except Exception:
            conn.rollback()
            raise

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "sync_credit_statuses": self._sync_credit_statuses,
            "get_all": self._get_all,
            "get_stats": self._get_stats,
            "update_status": self._update_status,
            "get_by_order": self._get_by_order,
            "get_payments": self._get_payments,
            "update_credit": self._update_credit,
            "mark_paid": self._mark_paid,
            "revert_last_payment": self._revert_last_payment,
            "anular_credit": self._anular_credit,
            "create_credit_for_order": self._create_credit_for_order,
            "create_credit": self._create_credit,
            "register_payment": self._register_payment,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
