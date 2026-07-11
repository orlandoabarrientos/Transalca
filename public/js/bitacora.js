$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="bitacora"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
});

let paginator = null;

function actionColor(accion) {
    return accion === 'CREAR' ? 'var(--success)' : accion === 'ELIMINAR' ? 'var(--danger)' : 'var(--info)';
}

function userName(b) {
    return [b.nombre, b.apellido].filter(Boolean).join(' ') || 'N/A';
}

function loadData() {
    apiCall('/api/bitacora/').then(res => {
        setupPaginator(res.data);
    });
}

function setupPaginator(data) {
    if (!paginator) {
        paginator = new TablePaginator('bitBody', {
            allData: data || [],
            itemName: 'registros',
            searchSelector: '#searchBit',
            renderRow: (b) => {
                return `<tr class="fade-in-up">
                    <td>${formatDate(b.fecha)}</td>
                    <td>${escapeHtml(userName(b))}</td>
                    <td><span style="color:${actionColor(b.accion)};font-weight:700;">${escapeHtml(b.accion)}</span></td>
                    <td><span class="badge-status badge-info">${escapeHtml(b.modulo)}</span></td>
                    <td class="text-center"><button class="btn btn-icon btn-sm btn-outline-orange rounded-circle" onclick="verDetalle(${b.id})" title="Ver detalle"><i class="bi bi-eye"></i></button></td>
                    <td><code>${escapeHtml(b.ip || '-')}</code></td>
                </tr>`;
            },
            onEmpty: () => '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-journal-text"></i><p>Sin registros</p></div></td></tr>'
        });
    } else {
        paginator.updateData(data || []);
    }
}

function verDetalle(id) {
    const b = (paginator?.allData || []).find(x => x.id === id);
    if (!b) return;
    document.getElementById('bitDetalle').innerHTML =
        `<table class="table table-sm mb-0">
            <tr><th style="width:140px;">Fecha</th><td>${formatDate(b.fecha)}</td></tr>
            <tr><th>Usuario</th><td>${escapeHtml(userName(b))}</td></tr>
            <tr><th>Acción</th><td><span style="color:${actionColor(b.accion)};font-weight:700;">${escapeHtml(b.accion)}</span></td></tr>
            <tr><th>Módulo</th><td><span class="badge-status badge-info">${escapeHtml(b.modulo)}</span></td></tr>
            <tr><th>Descripción</th><td>${escapeHtml(b.descripcion || '-')}</td></tr>
            <tr><th>IP</th><td><code>${escapeHtml(b.ip || '-')}</code></td></tr>
        </table>`;
    document.getElementById('bitUsuarioHistorial').textContent = userName(b);
    loadUltimasAccionesUsuario(b);
    new bootstrap.Modal(document.getElementById('bitModal')).show();
}

function loadUltimasAccionesUsuario(b) {
    const cont = document.getElementById('bitUltimos');
    cont.innerHTML = '<div class="text-center text-muted py-3">Cargando...</div>';
    apiCall(`/api/bitacora/user/${encodeURIComponent(b.usuario_id)}?limit=10`).then(res => {
        const data = res.data || [];
        if (!data.length) {
            cont.innerHTML = '<div class="text-center text-muted py-3">Sin acciones registradas</div>';
            return;
        }
        cont.innerHTML = `<table class="table table-sm mb-0">
            <thead><tr><th>Fecha</th><th>Módulo</th><th>Acción</th><th>Descripción</th></tr></thead>
            <tbody>${data.map(c => `<tr${c.id === b.id ? ' class="table-active"' : ''}>
                <td class="text-nowrap"><small>${formatDate(c.fecha)}</small></td>
                <td><span class="badge-status badge-info">${escapeHtml(c.modulo || '-')}</span></td>
                <td><span style="color:${actionColor(c.accion)};font-weight:700;font-size:0.8rem;">${escapeHtml(c.accion)}</span></td>
                <td><small>${escapeHtml(c.descripcion || '-')}</small></td>
            </tr>`).join('')}</tbody>
        </table>`;
    }).catch(() => {
        cont.innerHTML = '<div class="text-center text-muted py-3">No se pudieron cargar las acciones</div>';
    });
}

function searchLogs() {
    const q = document.getElementById('searchBit')?.value || '';
    if (q.length < 2) return loadData();
    apiCall(`/api/bitacora/search?q=${encodeURIComponent(q)}`).then(res => setupPaginator(res.data));
}

function filterByDate() {
    const start = document.getElementById('dateStart')?.value;
    const end = document.getElementById('dateEnd')?.value;
    if (!start || !end) return showToast('Seleccione ambas fechas', 'warning');
    apiCall(`/api/bitacora/filter?start=${start}&end=${end}`).then(res => setupPaginator(res.data));
}
