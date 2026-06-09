$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="dashboard"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadDashboard();
});

async function loadDashboard() {
    try {
        const res = await apiCall('/api/reports/dashboard');
        if (res.data) {
            document.getElementById('totalProducts').textContent = res.data.total_products || 0;
            document.getElementById('totalOrders').textContent = res.data.total_orders || 0;
            document.getElementById('totalClients').textContent = res.data.total_clients || 0;
            document.getElementById('pendingPayments').textContent = res.data.pending_payments || 0;
        }
    } catch(e) {}

    try {
        const res = await apiCall('/api/reports/recent-orders?limit=5');
        const tbody = document.getElementById('recentOrders');
        if (res.data?.length) {
            tbody.innerHTML = '';
            res.data.forEach(o => {
                const st = String(o.estado || '').toLowerCase();
                const badge = ['aprobado', 'aprobada', 'pagado', 'pagada', 'verificado', 'verificada', 'entregado', 'entregada'].includes(st) ? 'badge-active' : st === 'pendiente' ? 'badge-pending' : 'badge-inactive';
                tbody.innerHTML += `<tr><td>#${o.id}</td><td>${o.cliente_nombre || 'N/A'}</td><td data-usd-price="${o.total}">${formatUsdBs(o.total)}</td><td><span class="badge-status ${badge}">${o.estado}</span></td><td>${formatDate(o.fecha)}</td></tr>`;
            });
        }
    } catch(e) {}

    try {
        const res = await apiCall('/api/sucursales/active');
        const list = document.getElementById('branchList');
        if (res.data?.length) {
            list.innerHTML = '';
            res.data.forEach(s => {
                list.innerHTML += `<div class="d-flex align-items-center gap-2 mb-2 p-2 rounded" style="background:var(--primary-soft);">
                    <i class="bi bi-geo-alt-fill" style="color:var(--primary);"></i>
                    <div><strong style="font-size:0.85rem;">${s.nombre}</strong><br><small class="text-muted">${s.direccion || ''}</small></div>
                </div>`;
            });
        } else {
            list.innerHTML = '<p class="text-muted text-center mb-0">No hay sucursales activas</p>';
        }
    } catch(e) {}
}
