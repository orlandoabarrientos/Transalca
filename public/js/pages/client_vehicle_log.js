const vlogState = {
    vehicles: [],
    logs: [],
    predictions: [],
    selectedPlate: null
};

$(document).ready(function () {
    $('#navbarContainer').load('/components/client_navbar.html', async () => {
        await initVehicleLogPage();
    });
    $('#footerContainer').load('/components/client_footer.html');
});

async function initVehicleLogPage() {
    const loggedIn = await checkSession();
    if (!loggedIn || !currentUser || currentUser.tipo !== 'cliente') {
        $('#vlogGuestBox').show();
        $('#vlogApp').hide();
        return;
    }
    $('#vlogGuestBox').hide();
    $('#vlogApp').show();
    await Promise.all([loadVlogData(), loadVlogPredictions()]);
    renderVehicleChips();
    renderHistorial();
    renderAlertas();
}

async function loadVlogData() {
    try {
        const res = await fetch(`/api/vehicle-log/client/${encodeURIComponent(currentUser.cedula)}`, { credentials: 'same-origin' });
        const data = await res.json();
        vlogState.logs = (data.status === 'success' && Array.isArray(data.data)) ? data.data : [];
        const plates = [...new Set(vlogState.logs.map(l => l.placa || l.vehiculo_placa))];
        vlogState.vehicles = plates;
    } catch (e) {
        vlogState.logs = [];
    }
    try {
        const res = await fetch('/api/vehicles/', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.data)) {
            data.data.forEach(v => {
                const placa = v.placa || v.id;
                if (placa && !vlogState.vehicles.includes(placa)) vlogState.vehicles.push(placa);
            });
        }
    } catch (e) { }
}

async function loadVlogPredictions() {
    try {
        const res = await fetch(`/api/vehicle-log/predictions/client/${encodeURIComponent(currentUser.cedula)}`, { credentials: 'same-origin' });
        const data = await res.json();
        vlogState.predictions = (data.status === 'success' && Array.isArray(data.data)) ? data.data : [];
    } catch (e) {
        vlogState.predictions = [];
    }
}

function renderVehicleChips() {
    const cont = document.getElementById('vehiculosChips');
    if (!vlogState.vehicles.length) {
        cont.innerHTML = '<div class="alert alert-info mb-0 w-100">No tiene vehiculos registrados. Registre su vehiculo en <a href="/client/profile">Mi Perfil</a>.</div>';
        return;
    }
    cont.innerHTML = ['<span class="badge bg-light text-dark border vehiculo-chip' + (vlogState.selectedPlate ? '' : ' active') + '" data-placa="">Todos</span>']
        .concat(vlogState.vehicles.map(p =>
            `<span class="badge bg-light text-dark border vehiculo-chip${vlogState.selectedPlate === p ? ' active' : ''}" data-placa="${p}"><i class="bi bi-car-front me-1"></i>${p}</span>`))
        .join('');
    cont.querySelectorAll('.vehiculo-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            vlogState.selectedPlate = chip.dataset.placa || null;
            renderVehicleChips();
            renderHistorial();
            renderAlertas();
        });
    });
}

function vlogEscape(t) {
    return String(t == null ? '' : t).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function vlogDate(d) {
    if (!d) return '-';
    try { return new Date(d).toLocaleDateString('es-VE', { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch (e) { return String(d).slice(0, 10); }
}

function renderHistorial() {
    const cont = document.getElementById('vlogHistorial');
    let logs = vlogState.logs;
    if (vlogState.selectedPlate) logs = logs.filter(l => (l.placa || l.vehiculo_placa) === vlogState.selectedPlate);
    if (!logs.length) {
        cont.innerHTML = '<p class="text-muted mb-0">Aun no hay registros de servicios para su vehiculo. Cuando se realice un servicio en Transalca, aparecera aqui automaticamente.</p>';
        return;
    }
    cont.innerHTML = logs.map(l => {
        const detalles = [];
        if (l.productos_usados) detalles.push(`<div><i class="bi bi-box-seam me-1 text-secondary"></i><strong>Productos:</strong> ${vlogEscape(l.productos_usados)}</div>`);
        if (l.cauchos_usados || l.cauchos_info) detalles.push(`<div><i class="bi bi-circle me-1 text-secondary"></i><strong>Cauchos:</strong> ${vlogEscape(l.cauchos_usados || l.cauchos_info)}</div>`);
        if (l.aceite_usado) detalles.push(`<div><i class="bi bi-droplet me-1 text-secondary"></i><strong>Aceite:</strong> ${vlogEscape(l.aceite_usado)}</div>`);
        if (l.filtros_usados) detalles.push(`<div><i class="bi bi-funnel me-1 text-secondary"></i><strong>Filtros:</strong> ${vlogEscape(l.filtros_usados)}</div>`);
        if (l.kilometraje) detalles.push(`<div><i class="bi bi-speedometer2 me-1 text-secondary"></i><strong>Kilometraje:</strong> ${Number(l.kilometraje).toLocaleString()} km</div>`);
        const mecanico = (l.mecanico_nombre || '').trim();
        return `<div class="vlog-entry">
            <div class="vlog-date">${vlogDate(l.fecha)} · <span class="fw-bold">${vlogEscape(l.placa || l.vehiculo_placa || '')}</span>${mecanico ? ' · Mecanico: ' + vlogEscape(mecanico + ' ' + (l.mecanico_apellido || '')) : ''}</div>
            <div class="fw-semibold">${vlogEscape(l.servicio_nombre || l.descripcion || 'Registro de servicio')}</div>
            <div class="vlog-detail">${detalles.join('') || '<span class="text-muted">Sin detalle de productos</span>'}</div>
        </div>`;
    }).join('');
}

function renderAlertas() {
    const cont = document.getElementById('vlogAlertas');
    let preds = vlogState.predictions;
    if (vlogState.selectedPlate) preds = preds.filter(p => p.vehiculo_placa === vlogState.selectedPlate);
    if (!preds.length) {
        cont.innerHTML = '<p class="text-muted mb-0">No hay recomendaciones pendientes. El sistema calculara los proximos mantenimientos a partir del historial de su vehiculo.</p>';
        return;
    }
    cont.innerHTML = preds.map(p => {
        const dias = Number(p.dias_restantes);
        const vencida = dias < 0;
        const cuando = vencida
            ? `<span class="text-danger fw-bold">Vencida hace ${Math.abs(dias)} dias</span>`
            : `En ${dias} dias (${vlogDate(p.fecha_estimada)})`;
        return `<div class="alerta-card card-custom mb-2 ${vlogEscape(p.prioridad)}">
            <div class="card-body py-2">
                <div class="d-flex justify-content-between align-items-start gap-2">
                    <div>
                        <div class="fw-semibold">${vlogEscape(p.tipo_label || p.tipo_prediccion)} <small class="text-muted">· ${vlogEscape(p.vehiculo_placa)}</small></div>
                        <div style="font-size:0.83rem;">${cuando}</div>
                        <div class="text-muted" style="font-size:0.78rem;">${vlogEscape(p.referencia_detalle || '')}</div>
                        <div style="font-size:0.8rem;" class="mt-1"><i class="bi bi-lightbulb me-1"></i>Recomendacion: agende su ${vlogEscape((p.tipo_label || '').toLowerCase() || 'mantenimiento')} en Transalca.</div>
                    </div>
                    <span class="badge text-bg-light border text-uppercase" style="font-size:0.68rem;">${vlogEscape(p.prioridad)}</span>
                </div>
            </div>
        </div>`;
    }).join('');
}
