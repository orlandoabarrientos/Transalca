$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="credit"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    $('#filterEstado').on('change', loadCredits);
    Validator.setRules('creditDatesForm', {
        creditStartDate: { required: true, requiredMsg: 'Fecha de inicio requerida' },
        creditEndDate: { required: true, requiredMsg: 'Fecha de fin requerida' }
    });
    Validator.setRules('creditPaymentForm', {
        creditPaymentAmount: {
            required: true,
            requiredMsg: 'El monto del abono es obligatorio',
            min: 0.01,
            minMsg: 'El monto del abono debe ser mayor a cero'
        }
    });
    Validator.setRules('registerCreditForm', {
        creditCompanySelect: { required: true, requiredMsg: 'Debe seleccionar una empresa' },
        creditTotalAmount: {
            required: true,
            requiredMsg: 'El monto es obligatorio',
            min: 0.01,
            minMsg: 'El monto debe ser mayor a cero'
        },
        registerCreditStartDate: { required: true, requiredMsg: 'Fecha de inicio requerida' },
        registerCreditEndDate: { required: true, requiredMsg: 'Fecha de fin requerida' },
        creditObservaciones: { maxLength: 300, maxLengthMsg: 'Las observaciones no pueden superar los 300 caracteres.' }
    });
    Validator.setupRealtime('creditDatesForm');
    Validator.setupRealtime('creditPaymentForm');
    Validator.setupRealtime('registerCreditForm');

    const totalInput = document.getElementById('creditTotalAmount');
    if (totalInput) {
        totalInput.addEventListener('input', function () {
            let val = totalInput.value;
            val = val.replace(/[^0-9.]/g, '');
            const parts = val.split('.');
            if (parts.length > 2) {
                val = parts[0] + '.' + parts.slice(1).join('');
            }
            if (parts.length > 1 && parts[1].length > 2) {
                val = parts[0] + '.' + parts[1].slice(0, 2);
            }
            if (totalInput.value !== val) {
                totalInput.value = val;
            }

            const num = parseFloat(val);
            if (!val) {
                setFieldError(totalInput, 'El monto es obligatorio');
            } else if (isNaN(num) || num <= 0) {
                setFieldError(totalInput, 'El monto debe ser mayor a cero');
            } else if (num > 1000000) {
                setFieldError(totalInput, 'El monto supera el límite máximo permitido ($1,000,000)');
            } else {
                clearFieldError(totalInput);
                totalInput.classList.add('is-valid');
                totalInput.classList.remove('is-invalid');
            }
            updateFormSubmitState('registerCreditForm');
        });
    }

    const paymentInput = document.getElementById('creditPaymentAmount');
    if (paymentInput) {
        paymentInput.addEventListener('input', function () {
            let val = paymentInput.value;
            val = val.replace(/[^0-9.]/g, '');
            const parts = val.split('.');
            if (parts.length > 2) {
                val = parts[0] + '.' + parts.slice(1).join('');
            }
            if (parts.length > 1 && parts[1].length > 2) {
                val = parts[0] + '.' + parts[1].slice(0, 2);
            }
            if (paymentInput.value !== val) {
                paymentInput.value = val;
            }

            const num = parseFloat(val);
            const debt = parseFloat(document.getElementById('creditPaymentDebt').value || 0);
            if (!val) {
                setFieldError(paymentInput, 'El monto del abono es obligatorio');
            } else if (isNaN(num) || num <= 0) {
                setFieldError(paymentInput, 'El monto del abono debe ser mayor a cero');
            } else if (num > debt) {
                setFieldError(paymentInput, 'El abono no puede ser mayor a la deuda');
            } else {
                clearFieldError(paymentInput);
                paymentInput.classList.add('is-valid');
                paymentInput.classList.remove('is-invalid');
            }
            updateFormSubmitState('creditPaymentForm');
        });
    }

    $(document).on('change', '#creditCompanySelect, #registerCreditStartDate', function() {
        const selected = $('#creditCompanySelect option:selected');
        const dias = parseInt(selected.data('dias') || 0);
        const startDateVal = $('#registerCreditStartDate').val();
        if (startDateVal && dias > 0) {
            const start = new Date(`${startDateVal}T00:00:00`);
            start.setDate(start.getDate() + dias);
            $('#registerCreditEndDate').val(start.toISOString().slice(0, 10));
        }
    });

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

let paginator = null;

function loadCredits() {
    const estado = $('#filterEstado').val();
    let url = '/api/credit/?';
    if (estado) url += `estado=${encodeURIComponent(estado)}&`;
    $.get(url, function (r) {
        if (!paginator) {
            paginator = new TablePaginator('creditTableBody', {
                allData: r.data || [],
                itemName: 'créditos',
                searchSelector: '#searchInput',
                renderRow: (o) => {
                    const startDate = dateOnly(o.fecha_inicio_credito || o.fecha);
                    const endDate = dateOnly(o.fecha_vencimiento_credito || '');
                    const days = daysUntil(endDate);
                    const debt = Number(o.monto_deuda ?? o.total ?? 0);
                    const paid = String(o.credito_estado || '').toLowerCase() === 'pagado' || debt <= 0;
                    return `
                        <tr>
                            <td>#${o.id}</td>
                            <td>${escapeHtml(o.razon_social || o.nombre || '')}</td>
                            <td>${escapeHtml(o.rif || '')}</td>
                            <td data-usd-price="${o.total || 0}">${formatUsdBs(o.total || 0)}</td>
                            <td data-usd-price="${debt}">${formatUsdBs(debt)}</td>
                            <td>${escapeHtml(o.metodo_pago_nombre || o.metodo_pago || '')}</td>
                            <td>${startDate ? formatCreditDate(startDate) : 'N/A'}</td>
                            <td>${endDate ? formatCreditDate(endDate) : 'N/A'}</td>
                            <td>${renderDaysLeft(days)}</td>
                            <td>${creditStatusBadge(o.credito_estado || 'activo')}</td>
                            <td>
                                <button class="btn btn-sm btn-warning me-1" title="Modificar crédito" onclick="showCreditDatesModal(${o.id}, '${startDate || ''}', '${endDate || ''}')"><i class="bi bi-pencil-square"></i></button>
                                <button class="btn btn-sm btn-success me-1" title="Registrar abono" onclick="showCreditPaymentModal(${o.id}, ${debt})" ${paid ? 'disabled' : ''}><i class="bi bi-cash-coin"></i> Abonar</button>
                                <button class="btn btn-sm btn-success" title="Pagado" onclick="markCreditPaid(${o.id})" ${paid ? 'disabled' : ''}><i class="bi bi-check2-circle"></i> Pagado</button>
                            </td>
                        </tr>
                    `;
                },
                onEmpty: () => '<tr><td colspan="11" class="text-center py-4 text-muted">No hay créditos registrados.</td></tr>'
            });
        } else {
            paginator.updateData(r.data || []);
        }
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
    if (days <= 2) return `<span class="badge-status badge-pending">${days} días</span>`;
    return `<span class="badge-status badge-info">${days} días</span>`;
}

function creditStatusBadge(status) {
    const normalized = String(status || '').toLowerCase();
    const labels = {
        activo: 'Crédito activo',
        pendiente: 'Crédito activo',
        aprobado: 'Crédito activo',
        pagado: 'Al día',
        vencido: 'Deudora',
        anulado: 'Anulado'
    };
    if (['activo', 'pendiente', 'aprobado'].includes(normalized)) {
        return '<span class="badge-status badge-pending">Crédito activo</span>';
    }
    if (normalized === 'pagado') return '<span class="badge-status badge-active">Al día</span>';
    if (normalized === 'vencido') return '<span class="badge-status badge-inactive">Deudora</span>';
    return statusBadge(labels[normalized] || status || 'Sin crédito');
}

function updateCreditStatus(id, estado) {
    apiCall(`/api/credit/${id}/status`, 'PUT', { estado }).then(r => {
        if (r.status === 'success') {
            showToast(r.message, 'success');
            loadCreditStats();
            loadCredits();
            return;
        }
        showToast(r.message || 'No se pudo modificar el crédito', 'error');
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
    const btn = document.querySelector('#creditDatesModal .btn-orange') || document.querySelector('#creditDatesModal .btn-warning');
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
        showToast(r.message || 'No se pudo modificar el crédito', 'error');
    }).finally(() => setButtonLoading(btn, false));
}

function markCreditPaid(id) {
    confirmAction('¿Estás seguro de marcar este crédito como pagado?', () => {
        apiCall(`/api/credit/${id}/paid`, 'PUT').then(r => {
            if (r.status === 'success') {
                showToast(r.message, 'success');
                loadCreditStats();
                loadCredits();
                return;
            }
            showToast(r.message || 'No se pudo marcar el crédito como pagado', 'error');
        });
    }, { type: 'question', confirmText: 'Pagado', confirmColor: '#16a34a' });
}

function showCreditPaymentModal(id, debt) {
    Validator.clearForm('creditPaymentForm');
    $('#creditPaymentOrderId').val(id);
    $('#creditPaymentDebt').val(Number(debt || 0).toFixed(2));
    $('#creditPaymentDebtLabel').attr('data-usd-price', debt || 0).text(formatUsdBs(debt || 0));
    $('#creditPaymentAmount').val('').attr('max', Number(debt || 0).toFixed(2));
    new bootstrap.Modal('#creditPaymentModal').show();
    Validator.initTracking('creditPaymentForm');
    hydrateDualPrices();
}

function saveCreditPayment() {
    if (!Validator.validate('creditPaymentForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const id = $('#creditPaymentOrderId').val();
    const amount = Number($('#creditPaymentAmount').val() || 0);
    const debt = Number($('#creditPaymentDebt').val() || 0);
    if (amount > debt) {
        setFieldError(document.getElementById('creditPaymentAmount'), 'El abono no puede ser mayor a la deuda.');
        return;
    }
    const btn = document.querySelector('#creditPaymentModal .btn-orange') || document.querySelector('#creditPaymentModal .btn-success');
    setButtonLoading(btn, true, 'Registrando...');
    apiCall(`/api/credit/${id}/payment`, 'PUT', { monto: amount }).then(r => {
        if (r.status === 'success') {
            showToast(r.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('creditPaymentModal'))?.hide();
            loadCreditStats();
            loadCredits();
            return;
        }
        if (r.errors) Validator.showServerErrors('creditPaymentForm', r.errors);
        showToast(r.message || 'No se pudo registrar el abono.', 'error');
    }).finally(() => setButtonLoading(btn, false));
}

function showRegisterCreditModal() {
    Validator.clearForm('registerCreditForm');
    $('#creditCompanySelect').html('<option value="">Cargando empresas...</option>');
    $.get('/api/companies/', function(r) {
        if (r.status === 'success') {
            let options = '<option value="">Seleccione una empresa...</option>';
            (r.data || []).forEach(c => {
                options += `<option value="${c.cedula}" data-dias="${c.dias_credito || 0}">${escapeHtml(c.razon_social)} (${escapeHtml(c.rif)})</option>`;
            });
            $('#creditCompanySelect').html(options);
        } else {
            $('#creditCompanySelect').html('<option value="">Error al cargar empresas</option>');
        }
    });
    const todayStr = new Date().toISOString().slice(0, 10);
    $('#registerCreditStartDate').val(todayStr);
    $('#registerCreditEndDate').val('');
    $('#creditTotalAmount').val('');
    $('#creditObservaciones').val('');
    new bootstrap.Modal('#registerCreditModal').show();
    Validator.initTracking('registerCreditForm');
}

function saveNewCredit() {
    if (!Validator.validate('registerCreditForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const start = $('#registerCreditStartDate').val();
    const end = $('#registerCreditEndDate').val();
    if (end < start) {
        setFieldError(document.getElementById('registerCreditEndDate'), 'La fecha fin no puede ser menor a la fecha inicio.');
        return;
    }
    const btn = document.querySelector('#registerCreditModal .btn-orange');
    setButtonLoading(btn, true, 'Registrando...');
    const payload = {
        cliente_cedula: $('#creditCompanySelect').val(),
        total: $('#creditTotalAmount').val(),
        fecha_inicio: start,
        fecha_fin: end,
        observaciones: $('#creditObservaciones').val()
    };
    apiCall('/api/credit/', 'POST', payload).then(r => {
        if (r.status === 'success') {
            showToast(r.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('registerCreditModal'))?.hide();
            loadCreditStats();
            loadCredits();
            return;
        }
        if (r.errors) Validator.showServerErrors('registerCreditForm', r.errors);
        showToast(r.message || 'No se pudo registrar el crédito', 'error');
    }).finally(() => setButtonLoading(btn, false));
}
