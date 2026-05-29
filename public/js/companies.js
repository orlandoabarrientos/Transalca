let currentCompanyRif = null;

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="companies"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    loadCompanies();
    loadCompanyStats();
    $('#searchInput').on('input', debounce(loadCompanies, 300));
    $('#filterEstado').on('change', loadCompanies);
    Validator.setRules('companyForm', {
        fRifPrefijo: { required: true, custom: v => ['J', 'G', 'V', 'E', 'P'].includes(v), customMsg: 'El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente.' },
        fRif: { required: true, pattern: /^\d{9}$/, requiredMsg: 'RIF requerido', patternMsg: 'El RIF debe tener 9 digitos' },
        fRazonSocial: { required: true, minLength: 2, maxLength: 200, requiredMsg: 'Razon social requerida' },
        fTelefono: { required: true, pattern: /^04\d{9}$/, requiredMsg: 'Telefono requerido', patternMsg: 'Debe tener 11 digitos y comenzar por 04' },
        fEmail: { email: true },
        fRepresentanteTelefono: { pattern: /^$|^04\d{9}$/, patternMsg: 'Debe tener 11 digitos y comenzar por 04' },
        fRepresentanteEmail: { email: true },
        fLimiteCredito: { min: 0, minMsg: 'El límite no puede ser negativo' },
        fDiasCredito: { min: 0, minMsg: 'Los días no pueden ser negativos' }
    });
    Validator.setRules('fleetForm', {
        vMarca: { required: true, minLength: 2, requiredMsg: 'Marca requerida' },
        vModelo: { required: true, minLength: 1, requiredMsg: 'Modelo requerido' },
        vPlaca: { required: true, minLength: 5, requiredMsg: 'Placa requerida' },
        vKm: { min: 0, minMsg: 'El kilometraje no puede ser negativo' }
    });
    Validator.setupRealtime('companyForm');
    Validator.setupRealtime('fleetForm');
    $('#fRif, #fRifPrefijo').on('input change', debounce(validateUniqueCompanyRif, 350));
    $('#fEmail').on('input', debounce(validateUniqueCompanyEmail, 350));
});

function debounce(fn, ms) {
    let t; return function (...a) { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), ms); };
}

function buildCompanyRif() {
    const prefix = ($('#fRifPrefijo').val() || 'J').toUpperCase();
    const number = ($('#fRif').val() || '').replace(/\D/g, '');
    return prefix && number.length === 9 ? `${prefix}-${number.slice(0, 8)}-${number.slice(8)}` : '';
}

function setCompanyRif(value) {
    const doc = splitRifValue(value, 'J');
    $('#fRifPrefijo').val(doc.prefix || 'J');
    $('#fRif').val(doc.number || '');
}

function loadCompanyStats() {
    $.get('/api/companies/stats', function (r) {
        if (r.status === 'success') {
            $('#totalCompanies').text(r.data.total);
            $('#activeCompanies').text(r.data.activos);
        }
    });
}

function loadCompanies() {
    const q = $('#searchInput').val();
    const estado = $('#filterEstado').val();
    let url = '/api/companies/?';
    if (q) url += `q=${encodeURIComponent(q)}&`;
    if (estado !== '') url += `estado=${estado}&`;
    $.get(url, function (r) {
        const tbody = $('#companiesTableBody');
        tbody.empty();
        if (!r.data || !r.data.length) {
            tbody.html('<tr><td colspan="8" class="text-center py-4 text-muted">No se encontraron empresas</td></tr>');
            return;
        }
        r.data.forEach(c => {
            const estado = c.estado ? '<span class="badge bg-success">Activo</span>' : '<span class="badge bg-secondary">Inactivo</span>';
            const credito = companyCreditBadge(c.estado_credito);
            const vencimiento = c.credito_vencimiento ? `<small class="d-block text-muted">Fin: ${formatCompanyDate(c.credito_vencimiento)}</small>` : '';
            tbody.append(`
                <tr style="cursor:pointer" onclick="showCompanyDetail('${encodeURIComponent(c.rif)}')">
                    <td><strong>${escapeHtml(c.rif || '')}</strong></td>
                    <td>${escapeHtml(c.razon_social || c.nombre || '')}</td>
                    <td>${escapeHtml(c.telefono || '')}</td>
                    <td>${escapeHtml(c.email || '')}</td>
                    <td><span class="badge bg-info">${c.flota_count || 0}</span></td>
                    <td>${credito}${vencimiento}</td>
                    <td>${estado}</td>
                    <td>
                        <button class="btn btn-sm btn-warning me-1" onclick="event.stopPropagation(); editCompany('${encodeURIComponent(c.rif)}')" title="Modificar Empresa"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteCompany('${encodeURIComponent(c.rif)}')" title="Eliminar Empresa"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>
            `);
        });
        hydrateDualPrices();
    });
}

function companyCreditBadge(value) {
    const status = String(value || 'al_dia').toLowerCase();
    if (status === 'deudora') return '<span class="badge-status badge-inactive">Deudora</span>';
    if (status === 'credito_activo') return '<span class="badge-status badge-pending">Crédito activo</span>';
    return '<span class="badge-status badge-active">Al día</span>';
}

function formatCompanyDate(value) {
    const date = String(value || '').slice(0, 10);
    const [y, m, d] = date.split('-');
    return y && m && d ? `${d}/${m}/${y}` : '-';
}

function showCreateCompanyModal() {
    $('#companyModalTitle').text('Registrar Empresa');
    Validator.clearForm('companyForm');
    $('#editRif').val('');
    $('#fRifPrefijo').val('J').prop('disabled', false);
    $('#fRif').prop('disabled', false);
    new bootstrap.Modal('#companyModal').show();
    Validator.initTracking('companyForm');
}

function companyPayload(includeRif = true) {
    const data = {
        razon_social: $('#fRazonSocial').val(),
        nombre_comercial: $('#fNombreComercial').val(),
        telefono: $('#fTelefono').val(),
        email: $('#fEmail').val(),
        direccion: $('#fDireccion').val(),
        representante_nombre: $('#fRepresentante').val(),
        representante_cedula: $('#fRepresentanteCedula').val(),
        representante_telefono: $('#fRepresentanteTelefono').val(),
        representante_email: $('#fRepresentanteEmail').val(),
        sector: $('#fSector').val(),
        limite_credito: $('#fLimiteCredito').val() || 0,
        dias_credito: $('#fDiasCredito').val() || 0
    };
    if (includeRif) {
        data.rif_prefijo = $('#fRifPrefijo').val();
        data.rif = buildCompanyRif();
    }
    return data;
}

function saveCompany() {
    if (!Validator.validate('companyForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const editRif = $('#editRif').val();
    const data = companyPayload(!editRif);
    const url = editRif ? `/api/companies/${encodeURIComponent(editRif)}` : '/api/companies/';
    const method = editRif ? 'PUT' : 'POST';
    const btn = document.querySelector('#companyModal .modal-footer .btn-success');
    setButtonLoading(btn, true, 'Guardando...');
    $.ajax({
        url, type: method, contentType: 'application/json', data: JSON.stringify(data),
        success: function (r) {
            showToast(r.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('companyModal'))?.hide();
            loadCompanies();
            loadCompanyStats();
            if (editRif && currentCompanyRif === editRif) showCompanyDetail(editRif);
        },
        error: function (x) {
            if (x.responseJSON?.errors) Validator.showServerErrors('companyForm', x.responseJSON.errors);
            showToast(x.responseJSON?.message || 'No se pudo guardar la empresa', 'error');
        },
        complete: function () { setButtonLoading(btn, false); }
    });
}

function editCompany(rif) {
    rif = decodeURIComponent(rif);
    $.get(`/api/companies/${encodeURIComponent(rif)}`, function (r) {
        if (r.status !== 'success') return;
        const c = r.data;
        $('#companyModalTitle').text('Modificar Empresa');
        $('#editRif').val(c.rif);
        setCompanyRif(c.rif);
        $('#fRifPrefijo').prop('disabled', true);
        $('#fRif').prop('disabled', true);
        $('#fRazonSocial').val(c.razon_social);
        $('#fNombreComercial').val(c.nombre_comercial);
        $('#fSector').val(c.sector);
        $('#fTelefono').val(c.telefono);
        $('#fEmail').val(c.email);
        $('#fDireccion').val(c.direccion);
        $('#fRepresentante').val(c.representante_nombre);
        $('#fRepresentanteCedula').val(c.representante_cedula);
        $('#fRepresentanteTelefono').val(c.representante_telefono);
        $('#fRepresentanteEmail').val(c.representante_email);
        $('#fLimiteCredito').val(c.limite_credito || 0);
        $('#fDiasCredito').val(c.dias_credito || 0);
        new bootstrap.Modal('#companyModal').show();
        Validator.initTracking('companyForm');
    });
}

function deleteCompany(rif) {
    rif = decodeURIComponent(rif);
    confirmAction('Estas seguro de que deseas eliminar esta empresa?', () => {
        $.ajax({
            url: `/api/companies/${encodeURIComponent(rif)}/toggle`,
            type: 'PUT',
            success: r => { showToast(r.message, 'success'); loadCompanies(); loadCompanyStats(); hideCompanyDetail(); },
            error: x => showToast(x.responseJSON?.message || 'No se pudo eliminar la empresa', 'error')
        });
    }, { confirmColor: '#dc3545' });
}

function showCompanyDetail(rif) {
    rif = decodeURIComponent(rif);
    currentCompanyRif = rif;
    $.get(`/api/companies/${encodeURIComponent(rif)}`, function (r) {
        if (r.status !== 'success') return;
        const c = r.data;
        $('#detRif').text(c.rif);
        $('#detRazon').text(c.razon_social);
        $('#detTelefono').text(c.telefono || '-');
        $('#detEmail').text(c.email || '-');
        $('#detDireccion').text(c.direccion || '-');
        renderFleet(c.flota || []);
        renderCompanyOrders(c.ordenes || []);
        $('#detailPanel').slideDown(200);
        $('html,body').animate({ scrollTop: $('#detailPanel').offset().top - 80 }, 300);
    });
}

function hideCompanyDetail() {
    $('#detailPanel').slideUp(200);
    currentCompanyRif = null;
}

function renderFleet(items) {
    if (!items.length) {
        $('#fleetList').html('<p class="text-muted text-center py-3">Sin vehículos registrados</p>');
        return;
    }
    let html = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Placa</th><th>Marca</th><th>Modelo</th><th>Ano</th><th>Km</th><th>Acciones</th></tr></thead><tbody>';
    items.forEach(v => {
        html += `<tr><td><strong>${escapeHtml(v.placa || '-')}</strong></td><td>${escapeHtml(v.marca || '')}</td><td>${escapeHtml(v.modelo || '')}</td><td>${escapeHtml(v.anio || '-')}</td><td>${Number(v.kilometraje_actual || 0).toLocaleString()}</td><td><button class="btn btn-sm btn-warning me-1" onclick="editFleetVehicle('${encodeURIComponent(v.placa || '')}')" title="Modificar vehiculo"><i class="bi bi-pencil-square"></i></button><button class="btn btn-sm btn-danger" onclick="deleteFleetVehicle('${encodeURIComponent(v.placa || '')}')" title="Eliminar vehiculo"><i class="bi bi-trash"></i></button></td></tr>`;
    });
    html += '</tbody></table></div>';
    $('#fleetList').html(html);
}

function renderCompanyOrders(items) {
    if (!items.length) {
        $('#ordersList').html('<p class="text-muted text-center py-3">Sin órdenes registradas</p>');
        return;
    }
    let html = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>ID</th><th>Total</th><th>Estado</th><th>Crédito</th><th>Fecha</th></tr></thead><tbody>';
    items.forEach(o => {
        html += `<tr><td>#${o.id}</td><td data-usd-price="${o.total || 0}">${formatUsdBs(o.total || 0)}</td><td>${statusBadge(o.estado)}</td><td>${statusBadge(o.credito_estado || o.tipo_pago || '')}</td><td>${formatDate(o.fecha)}</td></tr>`;
    });
    html += '</tbody></table></div>';
    $('#ordersList').html(html);
    hydrateDualPrices();
}

function showFleetModal(vehicle) {
    if (!currentCompanyRif) return;
    Validator.clearForm('fleetForm');
    if (vehicle) {
        $('#fleetModalTitle').text('Modificar vehiculo de flota');
        $('#editVehicleId').val(vehicle.placa || vehicle.id);
        $('#vMarca').val(vehicle.marca);
        $('#vModelo').val(vehicle.modelo);
        $('#vAnio').val(vehicle.anio);
        $('#vPlaca').val(vehicle.placa);
        $('#vColor').val(vehicle.color);
        $('#vTipo').val(vehicle.tipo_vehiculo);
        $('#vCombustible').val(vehicle.tipo_combustible || 'gasolina');
        $('#vKm').val(vehicle.kilometraje_actual || 0);
    } else {
        $('#fleetModalTitle').text('Registrar vehiculo de flota');
        $('#editVehicleId').val('');
        $('#vCombustible').val('gasolina');
    }
    new bootstrap.Modal('#fleetModal').show();
    Validator.initTracking('fleetForm');
}

function fleetPayload() {
    return {
        marca: $('#vMarca').val(),
        modelo: $('#vModelo').val(),
        anio: parseInt($('#vAnio').val()) || null,
        placa: $('#vPlaca').val(),
        color: $('#vColor').val(),
        tipo_vehiculo: $('#vTipo').val(),
        tipo_combustible: $('#vCombustible').val(),
        kilometraje_actual: parseInt($('#vKm').val()) || 0
    };
}

function saveFleetVehicle() {
    if (!currentCompanyRif || !Validator.validate('fleetForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const vid = $('#editVehicleId').val();
    const url = vid ? `/api/clients/${encodeURIComponent(currentCompanyRif)}/vehicles/${encodeURIComponent(vid)}` : `/api/clients/${encodeURIComponent(currentCompanyRif)}/vehicles`;
    const method = vid ? 'PUT' : 'POST';
    $.ajax({
        url, type: method, contentType: 'application/json', data: JSON.stringify(fleetPayload()),
        success: r => { showToast(r.message, 'success'); bootstrap.Modal.getInstance(document.getElementById('fleetModal'))?.hide(); showCompanyDetail(currentCompanyRif); },
        error: x => { if (x.responseJSON?.errors) Validator.showServerErrors('fleetForm', x.responseJSON.errors); showToast(x.responseJSON?.message || 'No se pudo guardar el vehiculo', 'error'); }
    });
}

function editFleetVehicle(vid) {
    vid = decodeURIComponent(vid);
    $.get(`/api/vehicles/${encodeURIComponent(vid)}`, r => {
        if (r.status === 'success') showFleetModal(r.data);
    });
}

function deleteFleetVehicle(vid) {
    vid = decodeURIComponent(vid);
    confirmAction('Estas seguro de que deseas eliminar este vehiculo?', () => {
        $.ajax({
            url: `/api/clients/${encodeURIComponent(currentCompanyRif)}/vehicles/${encodeURIComponent(vid)}`,
            type: 'DELETE',
            success: r => { showToast(r.message, 'success'); showCompanyDetail(currentCompanyRif); },
            error: x => showToast(x.responseJSON?.message || 'No se pudo eliminar el vehiculo', 'error')
        });
    }, { confirmColor: '#dc3545' });
}

async function validateUniqueCompanyRif() {
    const input = document.getElementById('fRif');
    if (!input || input.disabled || !input.value.trim()) return true;
    if (!Validator.validateField('companyForm', 'fRif')) return false;
    try {
        const exclude = $('#editRif').val();
        const value = buildCompanyRif();
        const res = await fetch(`/api/companies/check-unique?field=rif&value=${encodeURIComponent(value)}&exclude=${encodeURIComponent(exclude)}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && data.exists && data.active) {
            input.dataset.externalError = 'Este rif ya esta registrado';
            setFieldError(input, 'Este rif ya esta registrado');
            updateFormSubmitState('companyForm');
            return false;
        }
        delete input.dataset.externalError;
        clearFieldError(input);
        updateFormSubmitState('companyForm');
    } catch (e) {}
    return true;
}

async function validateUniqueCompanyEmail() {
    const input = document.getElementById('fEmail');
    if (!input || !input.value.trim()) return true;
    if (!Validator.validateField('companyForm', 'fEmail')) return false;
    try {
        const exclude = $('#editRif').val() || buildCompanyRif();
        const res = await fetch(`/api/companies/check-unique?field=email&value=${encodeURIComponent(input.value.trim())}&exclude=${encodeURIComponent(exclude)}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && data.exists) {
            input.dataset.externalError = 'Este correo ya esta registrado';
            setFieldError(input, 'Este correo ya esta registrado');
            updateFormSubmitState('companyForm');
            return false;
        }
        delete input.dataset.externalError;
        clearFieldError(input);
        updateFormSubmitState('companyForm');
    } catch (e) {}
    return true;
}
