from model.connection import Connection


class NotificationModel(Connection):
    def __init__(self):
        super().__init__()

    def get_by_user(self, usuario_id, cedula=None, limit=50):
        if cedula:
            return self.fetch_all("transalca",
                "SELECT * FROM notificaciones WHERE usuario_id = %s OR cliente_cedula = %s "
                "ORDER BY created_at DESC LIMIT %s", (usuario_id, cedula, limit))
        return self.fetch_all("transalca",
            "SELECT * FROM notificaciones WHERE usuario_id = %s "
            "ORDER BY created_at DESC LIMIT %s", (usuario_id, limit))

    def get_by_cliente(self, cedula, limit=50):
        return self.fetch_all("transalca",
            "SELECT * FROM notificaciones WHERE cliente_cedula = %s "
            "ORDER BY created_at DESC LIMIT %s", (cedula, limit))

    def get_unread(self, usuario_id, cedula=None):
        if cedula:
            return self.fetch_all("transalca",
                "SELECT * FROM notificaciones WHERE (usuario_id = %s OR cliente_cedula = %s) AND leida = 0 "
                "ORDER BY created_at DESC", (usuario_id, cedula))
        return self.fetch_all("transalca",
            "SELECT * FROM notificaciones WHERE usuario_id = %s AND leida = 0 "
            "ORDER BY created_at DESC", (usuario_id,))

    def count_unread(self, usuario_id, cedula=None):
        if cedula:
            result = self.fetch_one("transalca",
                "SELECT COUNT(*) as total FROM notificaciones "
                "WHERE (usuario_id = %s OR cliente_cedula = %s) AND leida = 0",
                (usuario_id, cedula))
            return result['total'] if result else 0
        result = self.fetch_one("transalca",
            "SELECT COUNT(*) as total FROM notificaciones "
            "WHERE usuario_id = %s AND leida = 0", (usuario_id,))
        return result['total'] if result else 0

    def create(self, data):
        if not data.get('usuario_id') and not data.get('cliente_cedula'):
            raise ValueError('Notificacion requiere usuario_id o cliente_cedula')
        return self.insert("transalca",
            "INSERT INTO notificaciones (usuario_id, cliente_cedula, tipo, titulo, mensaje, prioridad) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (data.get('usuario_id'), data.get('cliente_cedula'),
             data.get('tipo', 'sistema'), data.get('titulo', ''),
             data.get('mensaje', ''), data.get('prioridad', 'media')))

    def mark_read(self, notif_id, usuario_id, cedula=None):
        if cedula:
            return self.update("transalca",
                "UPDATE notificaciones SET leida = 1 WHERE id = %s AND (usuario_id = %s OR cliente_cedula = %s)",
                (notif_id, usuario_id, cedula))
        return self.update("transalca",
            "UPDATE notificaciones SET leida = 1 WHERE id = %s AND usuario_id = %s",
            (notif_id, usuario_id))

    def mark_all_read(self, usuario_id, cedula=None):
        if cedula:
            return self.update("transalca",
                "UPDATE notificaciones SET leida = 1 WHERE (usuario_id = %s OR cliente_cedula = %s) AND leida = 0",
                (usuario_id, cedula))
        return self.update("transalca",
            "UPDATE notificaciones SET leida = 1 WHERE usuario_id = %s AND leida = 0",
            (usuario_id,))

    def delete_notification(self, notif_id, usuario_id, cedula=None):
        if cedula:
            return self.delete("transalca",
                "DELETE FROM notificaciones WHERE id = %s AND (usuario_id = %s OR cliente_cedula = %s)",
                (notif_id, usuario_id, cedula))
        return self.delete("transalca",
            "DELETE FROM notificaciones WHERE id = %s AND usuario_id = %s",
            (notif_id, usuario_id))

    def clean_old_read_notifications(self):
        return self.delete("transalca",
            "DELETE FROM notificaciones WHERE leida = 1 AND created_at < NOW() - INTERVAL 48 HOUR")

    def create_bulk(self, notifications):
        for n in notifications:
            self.create(n)

    def notify_maintenance_due(self, usuario_id, vehiculo_info, tipo_mant):
        return self.create({
            'usuario_id': usuario_id,
            'tipo': 'mantenimiento',
            'titulo': f'Mantenimiento pendiente: {tipo_mant}',
            'mensaje': f'Su vehiculo {vehiculo_info} requiere {tipo_mant}.',
            'prioridad': 'alta'
        })

    def notify_ticket_update(self, usuario_id, ticket_id, mensaje):
        return self.create({
            'usuario_id': usuario_id,
            'tipo': 'ticket',
            'titulo': f'Ticket #{ticket_id} actualizado',
            'mensaje': mensaje,
            'prioridad': 'media'
        })

    def notify_promotion(self, usuario_id, promo_nombre):
        return self.create({
            'usuario_id': usuario_id,
            'tipo': 'promocion',
            'titulo': f'Nueva promocion: {promo_nombre}',
            'mensaje': f'Tienes una nueva promocion disponible: {promo_nombre}',
            'prioridad': 'baja'
        })

    def notify_payment_status(self, cliente_cedula, orden_venta_id, approved, reason=''):
        if not cliente_cedula:
            return None
        if approved:
            return self.create({
                'cliente_cedula': cliente_cedula,
                'tipo': 'pago',
                'titulo': f'Pago aprobado: pedido #{orden_venta_id}',
                'mensaje': f'Tu pago del pedido #{orden_venta_id} fue aprobado. Ya puedes revisar el estado y el QR de factura en Mis pedidos.',
                'prioridad': 'media'
            })
        clean_reason = (reason or '').strip()
        message = f'Tu pago del pedido #{orden_venta_id} fue rechazado.'
        if clean_reason:
            message += f' Motivo: {clean_reason}'
            if clean_reason[-1] not in '.?!':
                message += '.'
        message += ' Revisa el detalle del pedido y carga un comprobante valido si corresponde.'
        return self.create({
            'cliente_cedula': cliente_cedula,
            'tipo': 'pago',
            'titulo': f'Pago rechazado: pedido #{orden_venta_id}',
            'mensaje': message,
            'prioridad': 'alta'
        })
