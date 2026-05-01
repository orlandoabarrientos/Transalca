const CONSTANTS = {
    ESTADOS_COMPROBANTE: ['pendiente', 'verificado', 'rechazado'],
    ESTADOS_ORDEN_COMPRA: ['pendiente', 'recibida', 'cancelada'],
    ESTADOS_ORDEN_VENTA: ['pendiente', 'procesando', 'aprobada', 'enviada', 'entregada', 'cancelada'],
    ESTADOS_SERVICIO_MECANICO: ['pendiente', 'en_proceso', 'completado', 'cancelado'],
    ESTADOS_TICKET: ['abierto', 'en_revision', 'espera_cliente', 'resuelto', 'cerrado'],
    TIPOS_COMBUSTIBLE: ['gasolina', 'gasoil', 'otro'],
    TIPOS_FILTRO: ['aceite', 'aire', 'gasolina', 'gasoil', 'otro'],
    TIPOS_PROMOCION: ['porcentaje', 'monto_fijo', '2x1', 'puntos_extra'],
    TIPOS_QR: ['producto', 'servicio', 'enlace'],
    PRIORIDADES_TICKET: ['baja', 'media', 'alta', 'critica'],
    ESTADOS_COMISION: ['pendiente', 'pagado', 'anulado'],
    ESTADOS_MANTENIMIENTO: ['pendiente', 'proximo', 'vencido', 'completado']
};

function buildSelectOptions(arr, selected) {
    return arr.map(v => `<option value="${v}" ${v === selected ? 'selected' : ''}>${v.charAt(0).toUpperCase() + v.slice(1).replace(/_/g, ' ')}</option>`).join('');
}

function isValidConstant(name, value) {
    return Array.isArray(CONSTANTS[name]) && CONSTANTS[name].includes(value);
}

function showAlteredSelect(message) {
    showToast(message || 'Select alterado: valor no permitido', 'error');
}

function estadoBadge(estado) {
    const colors = {
        pendiente: 'warning', procesando: 'info', aprobada: 'success', aprobado: 'success',
        enviada: 'primary', entregada: 'success', cancelada: 'danger', cancelado: 'danger',
        verificado: 'success', rechazado: 'danger', en_proceso: 'info', completado: 'success',
        abierto: 'primary', en_revision: 'info', espera_cliente: 'warning', resuelto: 'success',
        cerrado: 'secondary', pagado: 'success', anulado: 'danger', vencido: 'danger',
        proximo: 'warning', activo: 'success', inactivo: 'secondary',
        baja: 'secondary', media: 'info', alta: 'warning', critica: 'danger',
        mantenimiento: 'info', aceite: 'primary', filtro: 'secondary', refrigerante: 'info',
        caucho: 'dark', combustible: 'warning', ticket: 'primary', promocion: 'success', sistema: 'secondary'
    };
    const color = colors[estado] || 'secondary';
    const label = (estado || '').replace(/_/g, ' ');
    return `<span class="badge bg-${color}">${label.charAt(0).toUpperCase() + label.slice(1)}</span>`;
}
