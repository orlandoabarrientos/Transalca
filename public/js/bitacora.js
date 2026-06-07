$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="bitacora"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
});

let paginator = null;

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
                const actionColor = b.accion === 'CREAR' ? 'var(--success)' : b.accion === 'ELIMINAR' ? 'var(--danger)' : 'var(--info)';
                return `<tr class="fade-in-up">
                    <td>${formatDate(b.fecha)}</td>
                    <td>${escapeHtml(b.usuario_nombre || b.usuario_id || 'N/A')}</td>
                    <td><span style="color:${actionColor};font-weight:700;">${escapeHtml(b.accion)}</span></td>
                    <td><span class="badge-status badge-info">${escapeHtml(b.modulo)}</span></td>
                    <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(b.detalle || '-')}</td>
                    <td><code>${escapeHtml(b.ip || '-')}</code></td>
                </tr>`;
            },
            onEmpty: () => '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-journal-text"></i><p>Sin registros</p></div></td></tr>'
        });
    } else {
        paginator.updateData(data || []);
    }
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
