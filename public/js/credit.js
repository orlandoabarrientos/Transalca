$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="credit"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    $('#searchInput').on('input', debounce(loadCredits, 300));
    $('#filterEstado').on('change', loadCredits);
    Validator.setRules('creditDatesForm', {
        creditStartDate: { required: true, requiredMsg: 'Fecha de inicio requerida' },
        creditEndDate: { required: true, requiredMsg: 'Fecha de fin requerida' }
    });
    Validator.setupRealtime('creditDatesForm');
    loadCreditStats();
    loadCredits();
});

function debounce(fn, ms) {
    let t; return function (...a) { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), ms); };
}

function loadCreditStats() {
    $.get('/api/credit/stats', function (r) {
        if (r.status !== 'success') return;
        $('#totalCredits').text(r.data.total || 0);
        $('#pendingCredits').text(r.data.pendientes || 0);
        $('#paidCredits').text(r.data.pagados || 0);
        $('#expiredCredits').text(r.data.vencidos || 0);
        $('#creditBalance').attr('data-usd-price', r.data.saldo || 0).text(formatUsdBs(r.data.saldo || 0));
    });
}

function loadCredits() {
    const tbody = $('#creditTableBody');
    tbody.html('<tr><td colspan="10" class="text-center py-4"><div class="spinner-border text-warning" role="status"></div></td></tr>');
    const q = $('#searchInput').val();
    const estado = $('#filterEstado').val();
    let url = '/api/credit/?';
    if (q) url += `q=${encodeURIComponent(q)}&`;
    if (estado) url += `estado=${encodeURIComponent(estado)}&`;
    $.get(url, function (r) {
        tbody.empty();
        if (r.status !== 'success') {
            tbody.html('<tr><td colspan="10" class="text-center py-4 text-danger">No se pudieron cargar los creditos.</td></tr>');
            return;
        }
        if (!r.data || !r.data.length) {
            tbody.html('<tr><td colspan="10" class="text-center py-4 text-muted">No hay creditos registrados.</td></tr>');
            return;
        }
        r.data.forEach(o => {
            const startDate = dateOnly(o.fecha_inicio_credito || o.fecha);
            const endDate = dateOnly(o.fecha_vencimiento_credito || '');
            const days = daysUntil(endDate);
            tbody.append(`
                <tr>
                    <td>#${o.id}</td>
                    <td>${escapeHtml(o.razon_social || o.nombre || '')}</td>
                    <td>${escapeHtml(o.rif || '')}</td>
                    <td data-usd-price="${o.total || 0}">${formatUsdBs(o.total || 0)}</td>
                    <td>${escapeHtml(o.metodo_pago_nombre || o.metodo_pago || '')}</td>
                    <td>${startDate ? formatCreditDate(startDate) : 'N/A'}</td>
                    <td>${endDate ? formatCreditDate(endDate) : 'N/A'}</td>
                    <td>${renderDaysLeft(days)}</td>
                    <td>${creditStatusBadge(o.credito_estado || 'activo')}</td>
                    <td>
                        <button class="btn btn-sm btn-warning me-1" title="Modificar credito" onclick="showCreditDatesModal(${o.id}, '${startDate || ''}', '${endDate || ''}')"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-sm btn-success" title="Pagado" onclick="markCreditPaid(${o.id})" ${o.credito_estado === 'pagado' ? 'disabled' : ''}><i class="bi bi-check2-circle"></i> Pagado</button>
                    </td>
                </tr>
            `);
        });
        hydrateDualPrices();
        enhanceSearchableSelects();
    });
}

function dateOnly(value) {
    if (!value) return '';
    return String(value).slice(0, 10);
}

function formatCreditDate(value) {
    const [y, m, d] = String(value || '').split('-');
    return y && m && d ? `${d}/${m}/${y}` : 'N/A';
}

function daysUntil(dateValue) {
    if (!dateValue) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const end = new Date(`${dateValue}T00:00:00`);
    if (Number.isNaN(end.getTime())) return null;
    return Math.ceil((end - today) / 86400000);
}

function renderDaysLeft(days) {
    if (days === null) return '<span class="text-muted">N/A</span>';
    if (days <= 0) return '<span class="badge-status badge-inactive">Vencido</span>';
    if (days <= 2) return `<span class="badge-status badge-pending">${days} dias</span>`;
    return `<span class="badge-status badge-info">${days} dias</span>`;
}

function creditStatusBadge(status) {
    const normalized = String(status || '').toLowerCase();
    const labels = {
        activo: 'Credito activo',
        pendiente: 'Credito activo',
        aprobado: 'Credito activo',
        pagado: 'Al dia',
        vencido: 'Deudora',
        anulado: 'Anulado'
    };
    if (['activo', 'pendiente', 'aprobado'].includes(normalized)) {
        return '<span class="badge-status badge-pending">Credito activo</span>';
    }
    if (normalized === 'pagado') return '<span class="badge-status badge-active">Al dia</span>';
    if (normalized === 'vencido') return '<span class="badge-status badge-inactive">Deudora</span>';
    return statusBadge(labels[normalized] || status || 'Sin credito');
}

function updateCreditStatus(id, estado) {
    apiCall(`/api/credit/${id}/status`, 'PUT', { estado }).then(r => {
        if (r.status === 'success') {
            showToast(r.message, 'success');
            loadCreditStats();
            loadCredits();
            return;
        }
        showToast(r.message || 'No se pudo modificar el credito', 'error');
    });
}

function showCreditDatesModal(id, startDate, endDate) {
    Validator.clearForm('creditDatesForm');
    $('#creditOrderId').val(id);
    $('#creditStartDate').val(startDate || new Date().toISOString().slice(0, 10));
    $('#creditEndDate').val(endDate || '');
    new bootstrap.Modal('#creditDatesModal').show();
    Validator.initTracking('creditDatesForm');
}

function saveCreditDates() {
    if (!Validator.validate('creditDatesForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const start = $('#creditStartDate').val();
    const end = $('#creditEndDate').val();
    if (end < start) {
        setFieldError(document.getElementById('creditEndDate'), 'La fecha fin no puede ser menor a la fecha inicio.');
        return;
    }
    const id = $('#creditOrderId').val();
    const btn = document.querySelector('#creditDatesModal .btn-warning');
    setButtonLoading(btn, true, 'Modificando...');
    apiCall(`/api/credit/${id}/dates`, 'PUT', { fecha_inicio: start, fecha_fin: end }).then(r => {
        if (r.status === 'success') {
            showToast(r.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('creditDatesModal'))?.hide();
            loadCreditStats();
            loadCredits();
            return;
        }
        if (r.errors) Validator.showServerErrors('creditDatesForm', r.errors);
        showToast(r.message || 'No se pudo modificar el credito', 'error');
    }).finally(() => setButtonLoading(btn, false));
}

function markCreditPaid(id) {
    confirmAction('Estas seguro de marcar este credito como pagado?', () => {
        apiCall(`/api/credit/${id}/paid`, 'PUT').then(r => {
            if (r.status === 'success') {
                showToast(r.message, 'success');
                loadCreditStats();
                loadCredits();
                return;
            }
            showToast(r.message || 'No se pudo marcar el credito como pagado', 'error');
        });
    }, { type: 'question', confirmText: 'Pagado', confirmColor: '#16a34a' });
}
