$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="orders"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadSalesOrders();
    loadPurchaseOrders();
});

function loadSalesOrders() {
    apiCall('/api/inventory/sales-orders').then(res => {
        const tbody = document.getElementById('salesOrderBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(o => {
            const badge = o.estado === 'aprobada' || o.estado === 'entregada' ? 'badge-active' : o.estado === 'pendiente' ? 'badge-pending' : 'badge-inactive';
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
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-cart"></i><p>Sin ordenes de venta</p></div></td></tr>';
    });
}

function loadPurchaseOrders() {
    apiCall('/api/inventory/purchase-orders').then(res => {
        const tbody = document.getElementById('purchaseOrderBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(o => {
            const badge = o.estado === 'recibida' ? 'badge-active' : o.estado === 'pendiente' ? 'badge-pending' : 'badge-inactive';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${o.id}</td>
                <td><strong>${escapeHtml(o.proveedor_nombre || o.proveedor_rif || 'N/A')}</strong></td>
                <td>${escapeHtml(o.usuario_nombre || '-')}</td>
                <td>${escapeHtml(o.sucursal_nombre || 'N/A')}</td>
                <td class="fw-bold" style="color:var(--primary);" data-usd-price="${o.total}">${formatUsdBs(o.total)}</td>
                <td><span class="badge-status ${badge}">${escapeHtml(o.estado || '-')}</span></td>
                <td>${formatDate(o.fecha)}</td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-box-arrow-in-down"></i><p>Sin ordenes de compra</p></div></td></tr>';
    });
}
