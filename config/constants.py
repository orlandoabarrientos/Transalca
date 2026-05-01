ESTADOS_COMPROBANTE = ['pendiente', 'verificado', 'rechazado']
ESTADOS_ORDEN_COMPRA = ['pendiente', 'recibida', 'cancelada']
ESTADOS_ORDEN_VENTA = ['pendiente', 'procesando', 'aprobada', 'enviada', 'entregada', 'cancelada']
ESTADOS_SERVICIO_MECANICO = ['pendiente', 'en_proceso', 'completado', 'cancelado']
ESTADOS_TICKET = ['abierto', 'en_revision', 'espera_cliente', 'resuelto', 'cerrado']
TIPOS_COMBUSTIBLE = ['gasolina', 'gasoil', 'otro']
TIPOS_FILTRO = ['aceite', 'aire', 'gasolina', 'gasoil', 'otro']
TIPOS_ITEM = ['producto', 'servicio']
TIPOS_MOVIMIENTO_PUNTOS = ['acumular', 'canjear', 'ajuste']
TIPOS_PROMOCION = ['porcentaje', 'monto_fijo', '2x1', 'puntos_extra']
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
ESTADOS_MANTENIMIENTO = ['pendiente', 'proximo', 'vencido', 'completado']
MODOS_MANTENIMIENTO = ['manual', 'automatico']
PHONE_REGEX = r'^[0-9+\-\s()]{7,20}$'


def validate_choice(value, valid_values, field_name='campo'):
    if value not in valid_values:
        raise ValueError(f"{field_name}: valor '{value}' no valido. Permitidos: {', '.join(valid_values)}")
    return value
