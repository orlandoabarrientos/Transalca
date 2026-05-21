$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="orders_sales"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    $('#salesOrderSearch').on('input', filterSalesOrders);
    loadSalesOrders();
});

function loadSalesOrders() {
    apiCall('/api/inventory/sales-orders').then(res => {
        const tbody = document.getElementById('salesOrderBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(o => {
            const stateLower = String(o.estado || '').toLowerCase();
            const badge = ['aprobada', 'aprobado', 'entregada', 'entregado', 'verificado', 'pagado', 'activo'].includes(stateLower) ? 'badge-active' : ['pendiente', 'procesando', 'enviada'].includes(stateLower) ? 'badge-pending' : 'badge-inactive';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${o.id}</td>
                <td><strong>${escapeHtml(o.cliente_nombre || 'N/A')}</strong></td>
                <td>${escapeHtml(o.sucursal_nombre || 'N/A')}</td>
                <td class="fw-bold" style="color:var(--primary);" data-usd-price="${o.total}">${formatUsdBs(o.total)}</td>
                <td>${escapeHtml(o.metodo_pago || '-')}</td>
                <td><span class="badge-status ${badge}">${escapeHtml(o.estado || '-')}</span></td>
                <td>${formatDate(o.fecha)}</td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-cart"></i><p>Sin órdenes de venta registradas</p></div></td></tr>';
    });
}

function filterSalesOrders() {
    const term = String(document.getElementById('salesOrderSearch')?.value || '').trim().toLowerCase();
    document.querySelectorAll('#salesOrderBody tr').forEach(row => {
        if (row.querySelector('.empty-state')) return;
        row.style.display = !term || row.textContent.toLowerCase().includes(term) ? '' : 'none';
    });
}

function exportSalesOrders(format) {
    const safeFormat = format === 'excel' ? 'excel' : 'pdf';
    window.open(`/api/reports/export?type=sales&format=${safeFormat}`, '_blank');
}
