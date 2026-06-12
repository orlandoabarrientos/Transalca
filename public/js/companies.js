let currentCompanyRif = null;
let currentCompanyRepresentatives = [];

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="companies"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    loadCompanies();
    loadCompanyStats();
    $('#filterEstado').on('change', loadCompanies);
    Validator.setRules('companyForm', {
        fRifPrefijo: { required: true, custom: v => ['J', 'G', 'V', 'E', 'P'].includes(v), customMsg: 'El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente.' },
        fRif: { required: true, pattern: /^\d{9}$/, maxLength: 9, requiredMsg: 'RIF requerido', patternMsg: 'El RIF debe tener 9 digitos', maxLengthMsg: 'El RIF no puede superar los 9 caracteres.' },
        fRazonSocial: { required: true, minLength: 2, maxLength: 60, requiredMsg: 'Razon social requerida', maxLengthMsg: 'La razón social no puede superar los 60 caracteres.' },
        fNombreComercial: { maxLength: 100, maxLengthMsg: 'El nombre comercial no puede superar los 100 caracteres.' },
        fSector: { maxLength: 50, maxLengthMsg: 'El sector no puede superar los 50 caracteres.' },
        fTelefono: { required: true, pattern: /^04\d{9}$/, maxLength: 11, requiredMsg: 'Telefono requerido', patternMsg: 'Debe tener 11 digitos y comenzar por 04', maxLengthMsg: 'El teléfono no puede superar los 11 caracteres.' },
        fEmail: { email: true, maxLength: 50, maxLengthMsg: 'El correo no puede superar los 50 caracteres.' },
        fDireccion: { maxLength: 40, maxLengthMsg: 'La dirección no puede superar los 40 caracteres.' },
        fLimiteCredito: { min: 0, minMsg: 'El límite no puede ser negativo' },
        fDiasCredito: { min: 0, minMsg: 'Los días no pueden ser negativos' }
    });
    Validator.setRules('fleetForm', {
        vMarca: { required: true, minLength: 2, maxLength: 30, requiredMsg: 'Marca requerida', maxLengthMsg: 'La marca no puede superar los 30 caracteres.' },
        vModelo: { required: true, minLength: 1, maxLength: 30, requiredMsg: 'Modelo requerido', maxLengthMsg: 'El modelo no puede superar los 30 caracteres.' },
        vAnio: {
            custom: v => {
                if (!v) return true;
                const yr = parseInt(v);
                const maxYear = new Date().getFullYear() + 1;
                return yr >= 1940 && yr <= maxYear;
            },
            customMsg: `El año del vehículo debe estar entre 1940 y ${new Date().getFullYear() + 1}`
        },
        vPlaca: { required: true, minLength: 5, maxLength: 10, requiredMsg: 'Placa requerida', maxLengthMsg: 'La placa no puede superar los 10 caracteres.' },
        vColor: { maxLength: 20, maxLengthMsg: 'El color no puede superar los 20 caracteres.' },
        vTipo: { maxLength: 30, maxLengthMsg: 'El tipo de vehículo no puede superar los 30 caracteres.' },
        vKm: { min: 0, minMsg: 'El kilometraje no puede ser negativo' },
        vRepresentante: {
            custom: v => {
                const vid = $('#editVehicleId').val();
                if (vid) return true;
                return !!v;
            },
            customMsg: 'Seleccione el representante que gestiona el registro'
        }
    });
    Validator.setRules('representativeForm', {
        repCedulaNumero: { required: true, pattern: /^\d{7,8}$/, maxLength: 8, requiredMsg: 'Cedula requerida', patternMsg: 'Debe tener 7 o 8 digitos', maxLengthMsg: 'La cedula no puede superar los 8 caracteres.' },
        repNombre: { required: true, minLength: 2, maxLength: 50, requiredMsg: 'Nombre requerido', maxLengthMsg: 'El nombre no puede superar los 50 caracteres.' },
        repApellido: { maxLength: 50, maxLengthMsg: 'El apellido no puede superar los 50 caracteres.' },
        repTelefono: { required: true, pattern: /^04\d{9}$/, maxLength: 11, requiredMsg: 'Telefono requerido', patternMsg: 'Debe comenzar por 04 con 11 digitos', maxLengthMsg: 'El telefono no puede superar los 11 caracteres.' },
        repEmail: { email: true, maxLength: 50, maxLengthMsg: 'El correo no puede superar los 50 caracteres.' }
    });
    Validator.setupRealtime('companyForm');
    Validator.setupRealtime('fleetForm');
    Validator.setupRealtime('representativeForm');
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

let paginator = null;

function loadCompanies() {
    const estado = $('#filterEstado').val();
    let url = '/api/companies/?';
    if (estado !== '') url += `estado=${estado}&`;
    $.get(url, function (r) {
        if (!paginator) {
            paginator = new TablePaginator('companiesTableBody', {
                allData: r.data || [],
                itemName: 'empresas',
                searchSelector: '#searchInput',
                renderRow: (c) => {
                    const credito = companyCreditBadge(c.estado_credito);
                    const vencimiento = c.credito_vencimiento ? `<small class="d-block text-muted">Fin: ${formatCompanyDate(c.credito_vencimiento)}</small>` : '';
                    return `
                        <tr style="cursor:pointer" onclick="showCompanyDetail('${encodeURIComponent(c.rif)}')">
                            <td><strong>${escapeHtml(c.rif || '')}</strong></td>
                            <td>${escapeHtml(c.razon_social || c.nombre || '')}</td>
                            <td>${escapeHtml(c.telefono || '')}</td>
                            <td>${escapeHtml(c.email || '')}</td>
                            <td><span class="badge bg-info">${c.flota_count || 0}</span></td>
                            <td>${credito}${vencimiento}</td>
                            <td>
                                <button class="btn btn-sm btn-warning me-1" onclick="event.stopPropagation(); editCompany('${encodeURIComponent(c.rif)}')" title="Modificar Empresa"><i class="bi bi-pencil-square"></i></button>
                                <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteCompany('${encodeURIComponent(c.rif)}')" title="Eliminar Empresa"><i class="bi bi-trash"></i></button>
                            </td>
                        </tr>
                    `;
                },
                onEmpty: () => '<tr><td colspan="7" class="text-center py-4 text-muted">No se encontraron empresas</td></tr>'
            });
        } else {
            paginator.updateData(r.data || []);
        }
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
        telefono: $('#fTelefono').val(),
        email: $('#fEmail').val(),
        direccion: $('#fDireccion').val(),
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
        $('#fSector').val(c.sector);
        $('#fTelefono').val(c.telefono);
        $('#fEmail').val(c.email);
        $('#fDireccion').val(c.direccion);
        $('#fLimiteCredito').val(c.limite_credito || 0);
        $('#fDiasCredito').val(c.dias_credito || 0);
        new bootstrap.Modal('#companyModal').show();
        Validator.initTracking('companyForm');
    });
}

function deleteCompany(rif) {
    rif = decodeURIComponent(rif);
    confirmAction('¿Estás seguro de que deseas eliminar esta empresa?', () => {
        $.ajax({
            url: `/api/companies/${encodeURIComponent(rif)}/toggle`,
            type: 'PUT',
            success: r => { showToast(r.message, 'success'); loadCompanies(); loadCompanyStats(); hideCompanyDetail(); },
            error: x => showToast(x.responseJSON?.message || 'No se pudo eliminar la empresa', 'error')
        });
    });
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
        currentCompanyRepresentatives = c.representantes || [];
        renderRepresentatives(currentCompanyRepresentatives);
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
        $('#vRepresentanteWrapper').hide();
        $('#vRepresentante').prop('required', false).val('');
    } else {
        $('#fleetModalTitle').text('Registrar vehiculo de flota');
        $('#editVehicleId').val('');
        $('#vCombustible').val('gasolina');
        $('#vRepresentanteWrapper').show();
        $('#vRepresentante').prop('required', true);
        
        const activeReps = currentCompanyRepresentatives.filter(r => r.estado === 1);
        let repHtml = '<option value="">Seleccione un representante...</option>';
        if (activeReps.length === 0) {
            repHtml = '<option value="">Debe registrar al menos un representante activo primero...</option>';
        } else {
            activeReps.forEach(r => {
                const fullname = `${r.nombre} ${r.apellido || ''}`.trim();
                repHtml += `<option value="${escapeHtml(r.cedula)}">${escapeHtml(fullname)} (${escapeHtml(r.cargo)})</option>`;
            });
        }
        $('#vRepresentante').html(repHtml);
    }
    if (window.jQuery?.fn?.select2) window.jQuery('#vCombustible').trigger('change');
    new bootstrap.Modal('#fleetModal').show();
    Validator.initTracking('fleetForm');
}

function fleetPayload() {
    const payload = {
        marca: $('#vMarca').val(),
        modelo: $('#vModelo').val(),
        anio: parseInt($('#vAnio').val()) || null,
        placa: $('#vPlaca').val(),
        color: $('#vColor').val(),
        tipo_vehiculo: $('#vTipo').val(),
        tipo_combustible: $('#vCombustible').val(),
        kilometraje_actual: parseInt($('#vKm').val()) || 0
    };
    const vid = $('#editVehicleId').val();
    if (!vid) {
        payload.representante_cedula = $('#vRepresentante').val();
    }
    return payload;
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
    confirmAction('¿Estás seguro de que deseas eliminar este vehículo?', () => {
        $.ajax({
            url: `/api/clients/${encodeURIComponent(currentCompanyRif)}/vehicles/${encodeURIComponent(vid)}`,
            type: 'DELETE',
            success: r => { showToast(r.message, 'success'); showCompanyDetail(currentCompanyRif); },
            error: x => showToast(x.responseJSON?.message || 'No se pudo eliminar el vehículo', 'error')
        });
    });
}

async function validateUniqueCompanyRif() {
    const input = document.getElementById('fRif');
    if (!input || input.disabled || !input.value.trim()) return true;
    if (!Validator.validateField('companyForm', 'fRif')) return false;
    try {
        const exclude = $('#editRif').val();
        const value = buildCompanyRif();
        const res = await fetch('/api/companies/check-unique', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ field: 'rif', value, exclude })
        });
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
        const res = await fetch('/api/companies/check-unique', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ field: 'email', value: input.value.trim(), exclude })
        });
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

function renderRepresentatives(items) {
    if (!items.length) {
        $('#representativesList').html('<p class="text-muted text-center py-3">Sin representantes registrados</p>');
        return;
    }
    let html = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Cedula</th><th>Nombre Completo</th><th>Cargo</th><th>Telefono</th><th>Email</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>';
    items.forEach(r => {
        const badgeClass = r.estado ? 'bg-success' : 'bg-secondary';
        const badgeText = r.estado ? 'Activo' : 'Inactivo';
        const toggleIcon = r.estado ? 'bi-toggle-on text-success' : 'bi-toggle-off text-muted';
        const toggleTitle = r.estado ? 'Eliminar representante' : 'Activar representante';
        const fullname = `${r.nombre} ${r.apellido || ''}`.trim();
        html += `<tr>
            <td><strong>${escapeHtml(r.cedula || '')}</strong></td>
            <td>${escapeHtml(fullname)}</td>
            <td>${escapeHtml(r.cargo || '')}</td>
            <td>${escapeHtml(r.telefono || '')}</td>
            <td>${escapeHtml(r.email || '-')}</td>
            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-warning me-1" onclick="editRepresentative(${JSON.stringify(r).replace(/"/g, '&quot;')})" title="Modificar"><i class="bi bi-pencil-square"></i></button>
                <button class="btn btn-sm btn-outline-secondary" onclick="toggleRepresentative(${r.id}, ${r.estado ? 0 : 1})" title="${toggleTitle}"><i class="bi ${toggleIcon} fs-5"></i></button>
            </td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    $('#representativesList').html(html);
}

function showRepresentativeModal() {
    $('#representativeModalTitle').text('Registrar Representante');
    Validator.clearForm('representativeForm');
    $('#editRepId').val('');
    $('#repCedulaPrefijo').val('V').prop('disabled', false);
    $('#repCedulaNumero').val('').prop('disabled', false);
    $('#repNombre').val('');
    $('#repApellido').val('');
    $('#repTelefono').val('');
    $('#repEmail').val('');
    $('#repCargo').val('Representante legal');
    $('#repEstado').val('1');
    new bootstrap.Modal('#representativeModal').show();
    Validator.initTracking('representativeForm');
}

function editRepresentative(r) {
    $('#representativeModalTitle').text('Modificar Representante');
    Validator.clearForm('representativeForm');
    $('#editRepId').val(r.id);
    const doc = splitRifValue(r.cedula, 'V');
    $('#repCedulaPrefijo').val(doc.prefix || 'V').prop('disabled', true);
    $('#repCedulaNumero').val(doc.number || '').prop('disabled', true);
    $('#repNombre').val(r.nombre);
    $('#repApellido').val(r.apellido || '');
    $('#repTelefono').val(r.telefono || '');
    $('#repEmail').val(r.email || '');
    $('#repCargo').val(r.cargo || 'Otro');
    $('#repEstado').val(r.estado);
    new bootstrap.Modal('#representativeModal').show();
    Validator.initTracking('representativeForm');
}

function saveRepresentative() {
    if (!currentCompanyRif || !Validator.validate('representativeForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const data = {
        cedula_prefijo: $('#repCedulaPrefijo').val(),
        cedula_numero: $('#repCedulaNumero').val(),
        cedula: buildDocumentValue('repCedulaPrefijo', 'repCedulaNumero'),
        nombre: $('#repNombre').val(),
        apellido: $('#repApellido').val(),
        telefono: $('#repTelefono').val(),
        email: $('#repEmail').val(),
        cargo: $('#repCargo').val(),
        estado: parseInt($('#repEstado').val())
    };
    const url = `/api/companies/${encodeURIComponent(currentCompanyRif)}/representatives`;
    const btn = document.querySelector('#representativeModal .modal-footer .btn-success');
    setButtonLoading(btn, true, 'Guardando...');
    $.ajax({
        url, type: 'POST', contentType: 'application/json', data: JSON.stringify(data),
        success: function (r) {
            showToast(r.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('representativeModal'))?.hide();
            showCompanyDetail(currentCompanyRif);
        },
        error: function (x) {
            if (x.responseJSON?.errors) Validator.showServerErrors('representativeForm', x.responseJSON.errors);
            showToast(x.responseJSON?.message || 'No se pudo guardar el representante', 'error');
        },
        complete: function () { setButtonLoading(btn, false); }
    });
}

function toggleRepresentative(relationId, targetState) {
    if (!currentCompanyRif) return;
    const actionText = targetState ? 'activar' : 'eliminar';
    confirmAction(`¿Estás seguro de que deseas ${actionText} a este representante?`, () => {
        $.ajax({
            url: `/api/companies/representatives/${relationId}/toggle`,
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({ estado: targetState }),
            success: r => { showToast(r.message, 'success'); showCompanyDetail(currentCompanyRif); },
            error: x => showToast(x.responseJSON?.message || 'No se pudo cambiar el estado del representante', 'error')
        });
    });
}
