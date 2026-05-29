$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="credit"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    $('#searchInput').on('input', debounce(loadCredits, 300));
    $('#filterEstado').on('change', loadCredits);
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
        $('#creditBalance').attr('data-usd-price', r.data.saldo || 0).text(formatUsdBs(r.data.saldo || 0));
    });
}

function loadCredits() {
    const tbody = $('#creditTableBody');
    tbody.html('<tr><td colspan="8" class="text-center py-4"><div class="spinner-border text-warning" role="status"></div></td></tr>');
    const q = $('#searchInput').val();
    const estado = $('#filterEstado').val();
    let url = '/api/credit/?';
    if (q) url += `q=${encodeURIComponent(q)}&`;
    if (estado) url += `estado=${encodeURIComponent(estado)}&`;
    $.get(url, function (r) {
        tbody.empty();
        if (r.status !== 'success') {
            tbody.html('<tr><td colspan="8" class="text-center py-4 text-danger">No se pudieron cargar los creditos.</td></tr>');
            return;
        }
        if (!r.data || !r.data.length) {
            tbody.html('<tr><td colspan="8" class="text-center py-4 text-muted">No hay creditos registrados.</td></tr>');
            return;
        }
        r.data.forEach(o => {
            tbody.append(`
                <tr>
                    <td>#${o.id}</td>
                    <td>${escapeHtml(o.razon_social || o.nombre || '')}</td>
                    <td>${escapeHtml(o.rif || '')}</td>
                    <td data-usd-price="${o.total || 0}">${formatUsdBs(o.total || 0)}</td>
                    <td>${escapeHtml(o.metodo_pago_nombre || o.metodo_pago || '')}</td>
                    <td>${statusBadge(o.credito_estado || 'pendiente')}</td>
                    <td>${formatDate(o.fecha_vencimiento_credito || o.fecha)}</td>
                    <td>
                        <select class="form-select form-select-sm d-inline-block" style="width:150px" onchange="updateCreditStatus(${o.id}, this.value)">
                            ${['pendiente','aprobado','pagado','vencido','anulado'].map(e => `<option value="${e}" ${e === (o.credito_estado || 'pendiente') ? 'selected' : ''}>${e}</option>`).join('')}
                        </select>
                    </td>
                </tr>
            `);
        });
        hydrateDualPrices();
        enhanceSearchableSelects();
    });
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
