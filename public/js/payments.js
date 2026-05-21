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
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            const comprobante = p.imagen_url || p.comprobante_url || '';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${p.id}</td>
                <td>#${p.orden_venta_id}</td>
                <td>${comprobante ? `<a href="#" class="btn btn-sm btn-outline-orange" onclick="viewComp(${p.id})"><i class="bi bi-image me-1"></i>Ver</a>` : '-'}</td>
                <td>${escapeHtml(p.metodo_pago || '-')}</td>
                <td>${formatDate(p.fecha)}</td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="viewComp(${p.id})"><i class="bi bi-check-lg me-1"></i>Revisar pago</button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-credit-card"></i><p>Sin pagos pendientes</p></div></td></tr>';
    });
}

function loadAll() {
    apiCall('/api/payments/').then(res => {
        const tbody = document.getElementById('allBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            const stateLower = String(p.estado || '').toLowerCase();
            const badge = ['aprobado', 'aprobada', 'verificado', 'verificada', 'pagado', 'activo'].includes(stateLower) ? 'badge-active' : ['pendiente', 'procesando'].includes(stateLower) ? 'badge-pending' : 'badge-inactive';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${p.id}</td>
                <td>#${p.orden_venta_id}</td>
                <td>${escapeHtml(p.metodo_pago || '-')}</td>
                <td><span class="badge-status ${badge}">${escapeHtml(p.estado || '-')}</span></td>
                <td>${formatDate(p.fecha)}</td>
                <td>${escapeHtml(p.revisado_por_nombre || p.revisado_por || '-')}</td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-credit-card"></i><p>Sin pagos</p></div></td></tr>';
    });
}

function viewComp(id) {
    currentPaymentId = id;
    apiCall(`/api/payments/${id}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const p = res.data || {};
        const img = document.getElementById('compImg');
        const comprobante = p.imagen_url || p.comprobante_url || '';
        if (comprobante) {
            img.innerHTML = `<img src="/public/assets/comprobantes/${escapeHtml(comprobante)}" style="max-width:100%;border-radius:var(--radius);" alt="Comprobante" onerror="this.parentElement.innerHTML='<div class=&quot;empty-state&quot;><i class=&quot;bi bi-image&quot;></i><p>No se encontro el comprobante</p></div>'"><p class="mt-3 text-muted">Metodo: ${escapeHtml(p.metodo_pago || 'N/A')} | Fecha: ${formatDate(p.fecha)}</p>`;
        } else {
            img.innerHTML = '<div class="empty-state"><i class="bi bi-image"></i><p>Sin comprobante adjunto</p></div>';
        }
        new bootstrap.Modal(document.getElementById('compModal')).show();
    });
}

function approvePayment() {
    if (!currentPaymentId) return;
    confirmAction('¿Estás seguro de Aprobar este pago?', () => {
        setButtonLoading('#btnApprovePayment', true, 'Procesando...');
        apiCall(`/api/payments/${currentPaymentId}/approve`, 'POST').then(res => {
            setButtonLoading('#btnApprovePayment', false);
            if (res.status === 'error') return showToast(res.message, 'error');
            bootstrap.Modal.getInstance(document.getElementById('compModal')).hide();
            showToast(res.message || 'Pago verificado correctamente', 'success');
            loadPending();
            loadAll();
        });
    });
}

function rejectPayment() {
    if (!currentPaymentId) return;
    if (!window.Swal) {
        showToast('No se pudo abrir el formulario de rechazo', 'error');
        return;
    }
    const compModalEl = document.getElementById('compModal');
    const compModal = compModalEl ? bootstrap.Modal.getInstance(compModalEl) : null;
    compModal?._focustrap?.deactivate();
    Swal.fire({
        icon: 'warning',
        title: 'Motivo del rechazo.',
        input: 'textarea',
        inputPlaceholder: 'Explique el motivo.',
        didOpen: () => {
            const input = Swal.getInput();
            if (input) input.focus();
        },
        willClose: () => {
            compModal?._focustrap?.activate();
        },
        showCancelButton: true,
        confirmButtonText: 'Rechazar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#dc3545',
        inputValidator: value => {
            const text = String(value || '').trim();
            if (!text) return 'El motivo es obligatorio.';
            if (text.length > 255) return 'El motivo no puede superar 255 caracteres.';
            if (/[<>]|script|onerror|onclick/i.test(text)) return 'El motivo contiene caracteres no permitidos.';
            return null;
        }
    }).then(result => {
        if (!result.isConfirmed) return;
        setButtonLoading('#btnRejectPayment', true, 'Procesando...');
        apiCall(`/api/payments/${currentPaymentId}/reject`, 'POST', { observaciones: result.value }).then(res => {
            setButtonLoading('#btnRejectPayment', false);
            if (res.status === 'error') return showToast(res.message, 'error');
            bootstrap.Modal.getInstance(document.getElementById('compModal')).hide();
            showToast(res.message || 'Pago rechazado correctamente', 'warning');
            loadPending();
            loadAll();
        });
    });
}
