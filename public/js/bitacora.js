$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="bitacora"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
});

function loadData() {
    apiCall('/api/bitacora/').then(res => {
        renderLogs(res.data);
    });
}

function renderLogs(data) {
    const tbody = document.getElementById('bitBody');
    if(!tbody) return;
    tbody.innerHTML = '';
    (data || []).forEach(b => {
        const actionColor = b.accion === 'CREAR' ? 'var(--success)' : b.accion === 'ELIMINAR' ? 'var(--danger)' : 'var(--info)';
        tbody.innerHTML += `<tr class="fade-in-up">
            <td>${formatDate(b.fecha)}</td>
            <td>${b.usuario_nombre || b.usuario_id || 'N/A'}</td>
            <td><span style="color:${actionColor};font-weight:700;">${b.accion}</span></td>
            <td><span class="badge-status badge-info">${b.modulo}</span></td>
            <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;">${b.detalle || '-'}</td>
            <td><code>${b.ip || '-'}</code></td>
        </tr>`;
    });
    if (!data?.length) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-journal-text"></i><p>Sin registros</p></div></td></tr>';
}

function searchLogs() {
    const q = document.getElementById('searchBit')?.value || '';
    if (q.length < 2) return loadData();
    apiCall(`/api/bitacora/search?q=${encodeURIComponent(q)}`).then(res => renderLogs(res.data));
}

function filterByDate() {
    const start = document.getElementById('dateStart')?.value;
    const end = document.getElementById('dateEnd')?.value;
    if (!start || !end) return showToast('Seleccione ambas fechas', 'warning');
    apiCall(`/api/bitacora/filter?start=${start}&end=${end}`).then(res => renderLogs(res.data));
}
