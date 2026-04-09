$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="orders"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
});

function loadData() {
    apiCall('/api/reports/recent-orders?limit=50').then(res => {
        const tbody = document.getElementById('orderBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(o => {
            const badge = o.estado === 'aprobado' ? 'badge-active' : o.estado === 'pendiente' ? 'badge-pending' : 'badge-inactive';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${o.id}</td>
                <td><strong>${o.cliente_nombre || 'N/A'}</strong></td>
                <td>${o.sucursal_nombre || 'N/A'}</td>
                <td>${o.total_items || '-'}</td>
                <td class="fw-bold" style="color:var(--primary);">$${formatCurrency(o.total)}</td>
                <td>${o.metodo_pago || '-'}</td>
                <td><span class="badge-status ${badge}">${o.estado}</span></td>
                <td>${formatDate(o.fecha)}</td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-cart"></i><p>Sin ordenes</p></div></td></tr>';
    });
}
