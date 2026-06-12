ESTADOS_COMPROBANTE = ['pendiente', 'verificado', 'rechazado']
ESTADOS_ORDEN_COMPRA = ['pendiente', 'recibida', 'cancelada']
ESTADOS_ORDEN_VENTA = ['pendiente', 'procesando', 'aprobada', 'enviada', 'entregada', 'cancelada']
ESTADOS_SERVICIO_MECANICO = ['sin_asignar', 'asignado', 'pendiente', 'en_proceso', 'completado', 'cancelado']
ESTADOS_TICKET = ['abierto', 'en_revision', 'espera_cliente', 'resuelto', 'cerrado']
TIPOS_COMBUSTIBLE = ['gasolina', 'gasoil', 'otro']
TIPOS_FILTRO = ['aceite', 'aire', 'gasolina', 'gasoil', 'otro']
TIPOS_ITEM = ['producto', 'servicio']
TIPOS_MOVIMIENTO_PUNTOS = ['acumular', 'canjear', 'ajuste']
TIPOS_PROMOCION = ['puntos', 'descuento', 'gratis', 'porcentaje', 'monto_fijo', '2x1', 'puntos_extra']
TIPOS_QR = ['producto', 'servicio', 'enlace']
PRIORIDADES_TICKET = ['baja', 'media', 'alta', 'critica']
PRIORIDADES_NOTIFICACION = ['baja', 'media', 'alta', 'critica']
PORCENTAJE_COMISION_DEFAULT = 30.0
ESTADOS_COMISION = ['pendiente', 'pagado', 'anulado']
TIPOS_NOTIFICACION = [
    'mantenimiento', 'aceite', 'filtro', 'refrigerante',
    'caucho', 'combustible', 'ticket', 'promocion', 'sistema'
]
TIPOS_REGISTRO_VEHICULO = ['servicio', 'producto', 'mantenimiento', 'observacion', 'combustible']
PHONE_REGEX = r'^04\d{9}$'
DOCUMENT_PREFIXES = ['V', 'E', 'J', 'G', 'P']
RIF_PREFIXES = ['J', 'G', 'V', 'E', 'P']


def validate_choice(value, valid_values, field_name='campo'):
    if value not in valid_values:
        raise ValueError("El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente.")
    return value
