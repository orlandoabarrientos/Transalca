$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="inventory"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadSucursales('filterSucursal', true).then(() => {
        enhanceSearchableSelects();
    });
    loadStock();
});

function loadStock() {
    const tbody = document.getElementById('stockBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="spinner-border text-warning" role="status"></div></td></tr>';
    }
    const sucursal = document.getElementById('filterSucursal')?.value || '';
    const url = sucursal ? `/api/inventory/?sucursal_id=${encodeURIComponent(sucursal)}` : '/api/inventory/';
    apiCall(url).then(res => {
        if(!tbody) return;
        tbody.innerHTML = '';
        if (res.status === 'error') {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">No se pudo cargar el stock.</td></tr>';
            return;
        }
        (res.data || []).forEach(s => {
            const isLow = Number(s.stock || 0) <= Number(s.stock_minimo || 5);
            tbody.innerHTML += `<tr class="fade-in-up ${isLow ? 'table-warning' : ''}">
                <td><strong>${escapeHtml(s.producto_nombre || '')}</strong></td>
                <td>${escapeHtml(s.codigo || '')}</td>
                <td>${escapeHtml(s.sucursal_nombre || 'N/A')}</td>
                <td class="fw-bold">${Number(s.stock || 0)}</td>
                <td>${Number(s.stock_minimo || 5)}</td>
                <td>${isLow ? '<span class="badge-status badge-pending"><i class="bi bi-exclamation-triangle me-1"></i>Bajo</span>' : '<span class="badge-status badge-active">OK</span>'}</td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-archive"></i><p>Sin datos de stock</p></div></td></tr>';
        }
    });
}

function filterTable() {
    const q = document.getElementById('searchStock')?.value.toLowerCase() || '';
    document.querySelectorAll('#stockBody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}
