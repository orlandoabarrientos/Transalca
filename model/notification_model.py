from model.connection import Connection

NOTIF_BY_USER_AND_CLIENT_SQL = (
    "SELECT n.*, n.id_notificacion AS id, n.tipo_notificacion AS tipo, n.titulo_notificacion AS titulo, "
    "n.mensaje_notificacion AS mensaje, n.prioridad_notificacion AS prioridad "
    "FROM notificaciones n WHERE n.usuario_id = %s OR n.cliente_cedula = %s "
    "ORDER BY n.created_at DESC LIMIT %s"
)
NOTIF_BY_USER_SQL = (
    "SELECT n.*, n.id_notificacion AS id, n.tipo_notificacion AS tipo, n.titulo_notificacion AS titulo, "
    "n.mensaje_notificacion AS mensaje, n.prioridad_notificacion AS prioridad "
    "FROM notificaciones n WHERE n.usuario_id = %s ORDER BY n.created_at DESC LIMIT %s"
)
NOTIF_BY_CLIENT_SQL = (
    "SELECT n.*, n.id_notificacion AS id, n.tipo_notificacion AS tipo, n.titulo_notificacion AS titulo, "
    "n.mensaje_notificacion AS mensaje, n.prioridad_notificacion AS prioridad "
    "FROM notificaciones n WHERE n.cliente_cedula = %s ORDER BY n.created_at DESC LIMIT %s"
)
NOTIF_UNREAD_BY_USER_AND_CLIENT_SQL = (
    "SELECT n.*, n.id_notificacion AS id, n.tipo_notificacion AS tipo, n.titulo_notificacion AS titulo, "
    "n.mensaje_notificacion AS mensaje, n.prioridad_notificacion AS prioridad "
    "FROM notificaciones n WHERE (n.usuario_id = %s OR n.cliente_cedula = %s) AND n.leida = 0 "
    "ORDER BY n.created_at DESC"
)
NOTIF_UNREAD_BY_USER_SQL = (
    "SELECT n.*, n.id_notificacion AS id, n.tipo_notificacion AS tipo, n.titulo_notificacion AS titulo, "
    "n.mensaje_notificacion AS mensaje, n.prioridad_notificacion AS prioridad "
    "FROM notificaciones n WHERE n.usuario_id = %s AND n.leida = 0 ORDER BY n.created_at DESC"
)


class NotificationModel(Connection):
    def __init__(self):
        super().__init__()

    def _get_by_user(self, usuario_id, cedula=None, limit=50):
        if cedula:
            return self.fetch_all("transalca", NOTIF_BY_USER_AND_CLIENT_SQL, (usuario_id, cedula, limit))
        return self.fetch_all("transalca", NOTIF_BY_USER_SQL, (usuario_id, limit))

    def _get_by_cliente(self, cedula, limit=50):
        return self.fetch_all("transalca", NOTIF_BY_CLIENT_SQL, (cedula, limit))

    def _get_unread(self, usuario_id, cedula=None):
        if cedula:
            return self.fetch_all("transalca", NOTIF_UNREAD_BY_USER_AND_CLIENT_SQL, (usuario_id, cedula))
        return self.fetch_all("transalca", NOTIF_UNREAD_BY_USER_SQL, (usuario_id,))

    def _count_unread(self, usuario_id, cedula=None):
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

    def _create(self, data):
        if not data.get('usuario_id') and not data.get('cliente_cedula'):
            raise ValueError('Notificacion requiere usuario_id o cliente_cedula')
        return self.insert("transalca",
            "INSERT INTO notificaciones (usuario_id, cliente_cedula, tipo_notificacion, titulo_notificacion, mensaje_notificacion, prioridad_notificacion, referencia) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (data.get('usuario_id'), data.get('cliente_cedula'),
             data.get('tipo', 'sistema'), data.get('titulo', ''),
             data.get('mensaje', ''), data.get('prioridad', 'media'),
             data.get('referencia_id')))

    def _exists_recent(self, tipo, titulo, usuario_id=None, cliente_cedula=None, hours=24):
        """Evita notificaciones duplicadas dentro de una ventana de tiempo."""
        sql = ("SELECT id_notificacion FROM notificaciones WHERE tipo_notificacion = %s AND titulo_notificacion = %s "
               "AND created_at > NOW() - INTERVAL %s HOUR")
        params = [tipo, titulo, hours]
        if usuario_id:
            sql += " AND usuario_id = %s"
            params.append(usuario_id)
        if cliente_cedula:
            sql += " AND cliente_cedula = %s"
            params.append(cliente_cedula)
        return self.fetch_one("transalca", sql + " LIMIT 1", tuple(params)) is not None

    def _create_unique(self, data, hours=24):
        if self._exists_recent(data.get('tipo', 'sistema'), data.get('titulo', ''),
                              data.get('usuario_id'), data.get('cliente_cedula'), hours):
            return None
        return self._create(data)

    def _mark_read(self, notif_id, usuario_id, cedula=None):
        if cedula:
            return self.update("transalca",
                "UPDATE notificaciones SET leida = 1 WHERE id_notificacion = %s AND (usuario_id = %s OR cliente_cedula = %s)",
                (notif_id, usuario_id, cedula))
        return self.update("transalca",
            "UPDATE notificaciones SET leida = 1 WHERE id_notificacion = %s AND usuario_id = %s",
            (notif_id, usuario_id))

    def _mark_all_read(self, usuario_id, cedula=None):
        if cedula:
            return self.update("transalca",
                "UPDATE notificaciones SET leida = 1 WHERE (usuario_id = %s OR cliente_cedula = %s) AND leida = 0",
                (usuario_id, cedula))
        return self.update("transalca",
            "UPDATE notificaciones SET leida = 1 WHERE usuario_id = %s AND leida = 0",
            (usuario_id,))

    def _delete_notification(self, notif_id, usuario_id, cedula=None):
        if cedula:
            return self.delete("transalca",
                "DELETE FROM notificaciones WHERE id_notificacion = %s AND (usuario_id = %s OR cliente_cedula = %s)",
                (notif_id, usuario_id, cedula))
        return self.delete("transalca",
            "DELETE FROM notificaciones WHERE id_notificacion = %s AND usuario_id = %s",
            (notif_id, usuario_id))

    def _clean_old_read_notifications(self):
        return self.delete("transalca",
            "DELETE FROM notificaciones WHERE leida = 1 AND created_at < NOW() - INTERVAL 48 HOUR")

    def _create_bulk(self, notifications):
        for n in notifications:
            self._create(n)

    def _get_admin_users(self, modulo='notificaciones'):
        return self.fetch_all("mantenimiento",
            "SELECT DISTINCT u.id FROM usuarios u "
            "INNER JOIN usuario_rol ur ON ur.usuario_id = u.id "
            "INNER JOIN permisos p ON p.rol_id = ur.rol_id "
            "WHERE u.estado = 1 AND p.modulo = %s AND p.leer = 1", (modulo,))

    def _notify_stock_low(self, producto_codigo, producto_nombre, stock_actual, umbral, sucursal_nombre=None):
        """Notifica stock bajo a los usuarios administradores, sin duplicar en 24h."""
        lugar = f" en {sucursal_nombre}" if sucursal_nombre else ""
        titulo = f"Stock bajo: {producto_nombre}"
        mensaje = (f"El producto {producto_nombre} ({producto_codigo}) tiene stock bajo{lugar}: "
                   f"{stock_actual} unidades (umbral: {umbral}). Considere reponer inventario.")
        created = 0
        for user in self._get_admin_users('stock'):
            notif_id = self._create_unique({
                'usuario_id': user['id'],
                'tipo': 'sistema',
                'titulo': titulo,
                'mensaje': mensaje,
                'prioridad': 'alta'
            }, hours=24)
            if notif_id:
                created += 1
        return created

    def _notify_ticket_update(self, usuario_id, ticket_id, mensaje):
        return self._create({
            'usuario_id': usuario_id,
            'tipo': 'ticket',
            'titulo': f'Ticket #{ticket_id} actualizado',
            'mensaje': mensaje,
            'prioridad': 'media'
        })

    def _notify_promotion(self, usuario_id, promo_nombre):
        return self._create({
            'usuario_id': usuario_id,
            'tipo': 'promocion',
            'titulo': f'Nueva promocion: {promo_nombre}',
            'mensaje': f'Tienes una nueva promocion disponible: {promo_nombre}',
            'prioridad': 'baja'
        })

    def _notify_payment_status(self, cliente_cedula, orden_venta_id, approved, reason=''):
        if not cliente_cedula:
            return None
        if approved:
            return self._create({
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
        return self._create({
            'cliente_cedula': cliente_cedula,
            'tipo': 'pago',
            'titulo': f'Pago rechazado: pedido #{orden_venta_id}',
            'mensaje': message,
            'prioridad': 'alta'
        })

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_by_user": self._get_by_user,
            "get_by_cliente": self._get_by_cliente,
            "get_unread": self._get_unread,
            "count_unread": self._count_unread,
            "create": self._create,
            "exists_recent": self._exists_recent,
            "create_unique": self._create_unique,
            "mark_read": self._mark_read,
            "mark_all_read": self._mark_all_read,
            "delete_notification": self._delete_notification,
            "clean_old_read_notifications": self._clean_old_read_notifications,
            "create_bulk": self._create_bulk,
            "get_admin_users": self._get_admin_users,
            "notify_stock_low": self._notify_stock_low,
            "notify_ticket_update": self._notify_ticket_update,
            "notify_promotion": self._notify_promotion,
            "notify_payment_status": self._notify_payment_status,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
