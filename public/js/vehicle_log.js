$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="vehicle_log"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadRegistros();
    loadPredicciones();
});

const PRIORIDAD_BADGE = {
    critica: 'badge-prioridad-critica',
    alta: 'badge-prioridad-alta',
    media: 'badge-prioridad-media',
    baja: 'badge-prioridad-baja'
};

function clearFiltros() {
    ['filtroCliente', 'filtroVehiculo', 'filtroDesde', 'filtroHasta'].forEach(id => { document.getElementById(id).value = ''; });
    loadRegistros();
}

async function loadRegistros() {
    const params = new URLSearchParams();
    const cliente = document.getElementById('filtroCliente').value.trim();
    const vehiculo = document.getElementById('filtroVehiculo').value.trim();
    const desde = document.getElementById('filtroDesde').value;
    const hasta = document.getElementById('filtroHasta').value;
    if (cliente) params.set('cliente', cliente);
    if (vehiculo) params.set('vehiculo', vehiculo);
    if (desde) params.set('fecha_desde', desde);
    if (hasta) params.set('fecha_hasta', hasta);
    try {
        const res = await apiCall('/api/vehicle-log/admin?' + params.toString());
        const data = res.data || [];
        document.getElementById('statRegistros').textContent = data.length;
        const body = document.getElementById('registrosBody');
        if (!data.length) {
            body.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-journal-x"></i><p>Sin registros de bitacora</p></div></td></tr>';
            return;
        }
        body.innerHTML = data.map(r => `<tr class="fade-in-up">
            <td>${formatDate(r.fecha)}</td>
            <td class="fw-bold">${escapeHtml(r.placa || r.vehiculo_placa || '')}<br><small class="text-muted">${escapeHtml((r.marca || '') + ' ' + (r.modelo || ''))}</small></td>
            <td>${escapeHtml(r.cliente_nombre || '-')}</td>
            <td>${escapeHtml(r.servicio_nombre || r.descripcion || '-')}</td>
            <td><small>${escapeHtml(r.productos_usados || '-')}</small></td>
            <td><small>${escapeHtml(r.cauchos_usados || r.cauchos_info || '-')}</small></td>
            <td>${r.kilometraje ? Number(r.kilometraje).toLocaleString() : '-'}</td>
            <td><button class="btn btn-icon btn-sm btn-outline-orange" onclick="verRegistro(${r.id})" title="Ver detalle"><i class="bi bi-eye"></i></button></td>
        </tr>`).join('');
        window.__registros = data;
    } catch (e) {
        showToast('No se pudieron cargar los registros de bitacora', 'error');
    }
}

function verRegistro(id) {
    const r = (window.__registros || []).find(x => x.id === id);
    if (!r) return;
    const rows = [
        ['Fecha', formatDate(r.fecha)],
        ['Vehiculo', `${r.placa || r.vehiculo_placa || ''} - ${(r.marca || '')} ${(r.modelo || '')}`],
        ['Cliente', r.cliente_nombre || '-'],
        ['Servicio', r.servicio_nombre || '-'],
        ['Descripcion', r.descripcion || '-'],
        ['Kilometraje', r.kilometraje || '-'],
        ['Aceite usado', r.aceite_usado || '-'],
        ['Filtros usados', r.filtros_usados || '-'],
        ['Refrigerante usado', r.refrigerante_usado || '-'],
        ['Productos usados', r.productos_usados || '-'],
        ['Cauchos usados', r.cauchos_usados || r.cauchos_info || '-'],
        ['Proximo mantenimiento', r.proximo_mantenimiento || '-'],
        ['Observaciones', r.observaciones || '-']
    ];
    document.getElementById('registroDetalle').innerHTML =
        '<table class="table table-sm mb-0">' +
        rows.map(([k, v]) => `<tr><th style="width:220px;">${k}</th><td>${escapeHtml(String(v))}</td></tr>`).join('') +
        '</table>';
    new bootstrap.Modal(document.getElementById('registroModal')).show();
}

async function loadPredicciones() {
    const params = new URLSearchParams();
    const cliente = document.getElementById('predCliente').value.trim();
    const vehiculo = document.getElementById('predVehiculo').value.trim();
    const estado = document.getElementById('predEstado').value;
    const prioridad = document.getElementById('predPrioridad').value;
    if (cliente) params.set('cliente', cliente);
    if (vehiculo) params.set('vehiculo', vehiculo);
    if (estado) params.set('estado', estado);
    if (prioridad) params.set('prioridad', prioridad);
    try {
        const res = await apiCall('/api/vehicle-log/predictions?' + params.toString());
        const data = res.data || [];
        const activas = data.filter(p => p.estado !== 'atendida');
        document.getElementById('statPredicciones').textContent = activas.length;
        document.getElementById('statProximas').textContent = activas.filter(p => p.dias_restantes >= 0 && p.dias_restantes <= 14).length;
        document.getElementById('statVencidas').textContent = activas.filter(p => p.dias_restantes < 0).length;
        const body = document.getElementById('prediccionesBody');
        if (!data.length) {
            body.innerHTML = '<tr><td colspan="10" class="text-center py-4"><div class="empty-state"><i class="bi bi-magic"></i><p>Sin predicciones. Use "Actualizar bitacora y predicciones".</p></div></td></tr>';
            return;
        }
        body.innerHTML = data.map(p => {
            const dias = Number(p.dias_restantes);
            const diasTxt = dias < 0 ? `<span class="text-danger fw-bold">${Math.abs(dias)} dias vencida</span>` : `${dias} dias`;
            return `<tr class="fade-in-up">
                <td class="fw-bold">${escapeHtml(p.vehiculo_placa)}<br><small class="text-muted">${escapeHtml((p.marca || '') + ' ' + (p.modelo || ''))}</small></td>
                <td>${escapeHtml(p.cliente_nombre || '-')}</td>
                <td>${escapeHtml(p.tipo_label || p.tipo_prediccion)}</td>
                <td><small>${escapeHtml(p.referencia_detalle || '-')}</small></td>
                <td>${formatDate(p.fecha_estimada)}</td>
                <td>${diasTxt}</td>
                <td><span class="badge ${PRIORIDAD_BADGE[p.prioridad] || ''}">${escapeHtml(p.prioridad)}</span></td>
                <td>${escapeHtml(p.estado)}</td>
                <td><small class="text-muted">${escapeHtml(p.base_calculo || '-')}</small></td>
                <td>${p.estado !== 'atendida' ? `<button class="btn btn-icon btn-sm btn-outline-success" onclick="atenderPrediccion(${p.id})" title="Marcar como atendida"><i class="bi bi-check2-circle"></i></button>` : ''}</td>
            </tr>`;
        }).join('');
    } catch (e) {
        showToast('No se pudieron cargar las predicciones', 'error');
    }
}

async function atenderPrediccion(id) {
    try {
        await apiCall(`/api/vehicle-log/predictions/${id}/attend`, 'PUT');
        showToast('Prediccion marcada como atendida', 'success');
        loadPredicciones();
    } catch (e) {
        showToast('No se pudo actualizar la prediccion', 'error');
    }
}

async function runCycle() {
    try {
        const res = await apiCall('/api/vehicle-log/run-cycle', 'POST');
        const d = res.data || {};
        showToast(`Bitacora actualizada: ${d.sincronizados || 0} servicios sincronizados, ${d.predicciones || 0} predicciones, ${d.notificaciones || 0} notificaciones`, 'success');
        loadRegistros();
        loadPredicciones();
    } catch (e) {
        showToast('No se pudo ejecutar el ciclo automatico', 'error');
    }
}
