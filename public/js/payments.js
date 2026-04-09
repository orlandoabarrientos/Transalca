let currentPaymentId = null;

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="payments"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadPending();
    loadAll();
});

function loadPending() {
    apiCall('/api/payments/pending').then(res => {
        const tbody = document.getElementById('pendingBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${p.id}</td>
                <td>#${p.orden_venta_id}</td>
                <td>${p.comprobante_url ? `<a href="#" class="btn btn-sm btn-outline-orange" onclick="viewComp(${p.id})"><i class="bi bi-image me-1"></i>Ver</a>` : '-'}</td>
                <td>${p.metodo_pago || '-'}</td>
                <td>${formatDate(p.fecha)}</td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="viewComp(${p.id})"><i class="bi bi-check-lg me-1"></i>Revisar</button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-credit-card"></i><p>Sin pagos pendientes</p></div></td></tr>';
    });
}

function loadAll() {
    apiCall('/api/payments/').then(res => {
        const tbody = document.getElementById('allBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            const badge = p.estado === 'aprobado' ? 'badge-active' : p.estado === 'pendiente' ? 'badge-pending' : 'badge-inactive';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${p.id}</td><td>#${p.orden_venta_id}</td><td>${p.metodo_pago || '-'}</td>
                <td><span class="badge-status ${badge}">${p.estado}</span></td>
                <td>${formatDate(p.fecha)}</td><td>${p.revisado_por || '-'}</td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-credit-card"></i><p>Sin pagos</p></div></td></tr>';
    });
}

function viewComp(id) {
    currentPaymentId = id;
    apiCall(`/api/payments/${id}`).then(res => {
        const p = res.data;
        const img = document.getElementById('compImg');
        if (p.comprobante_url) {
            img.innerHTML = `<img src="/public/assets/comprobantes/${p.comprobante_url}" style="max-width:100%;border-radius:var(--radius);" alt="Comprobante"><p class="mt-3 text-muted">Metodo: ${p.metodo_pago || 'N/A'} | Fecha: ${formatDate(p.fecha)}</p>`;
        } else {
            img.innerHTML = '<div class="empty-state"><i class="bi bi-image"></i><p>Sin comprobante adjunto</p></div>';
        }
        new bootstrap.Modal(document.getElementById('compModal')).show();
    });
}

function approvePayment() {
    if (!currentPaymentId) return;
    confirmAction('¿Aprobar este pago?', () => {
        apiCall(`/api/payments/${currentPaymentId}/approve`, 'POST').then(res => {
            bootstrap.Modal.getInstance(document.getElementById('compModal')).hide();
            showToast('Pago aprobado', 'success'); loadPending(); loadAll();
        });
    });
}

function rejectPayment() {
    if (!currentPaymentId) return;
    const obs = prompt('Motivo del rechazo:');
    if (obs !== null) {
        apiCall(`/api/payments/${currentPaymentId}/reject`, 'POST', { observaciones: obs }).then(res => {
            bootstrap.Modal.getInstance(document.getElementById('compModal')).hide();
            showToast('Pago rechazado', 'warning'); loadPending(); loadAll();
        });
    }
}
