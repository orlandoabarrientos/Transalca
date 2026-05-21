let currentCedula = null;
let pendingVehicleCarnetFile = null;

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="clients"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    loadClients();
    loadStats();

    $('#searchInput').on('input', debounce(loadClients, 300));
    $('#filterEstado').on('change', loadClients);
    $('#btnVehicleCarnet').on('click', () => $('#vCarnetFile').trigger('click'));
    $('#vCarnetFile').on('change', function () {
        pendingVehicleCarnetFile = this.files && this.files[0] ? this.files[0] : null;
        $('#vCarnetFileName').text(pendingVehicleCarnetFile ? pendingVehicleCarnetFile.name : 'No seleccionado');
        if (pendingVehicleCarnetFile) scanVehicleTitleAndFillAdmin(pendingVehicleCarnetFile);
    });
    Validator.setRules('clientForm', {
        fCedulaPrefijo: { required: true, custom: v => ['V', 'E', 'J', 'G', 'P'].includes(v), customMsg: 'El valor seleccionado no es válido. Recargue la página e inténtelo nuevamente.' },
        fCedula: { required: true, pattern: /^\d{7,8}$/, requiredMsg: 'Cédula requerida', patternMsg: 'La cédula debe tener 7 u 8 dígitos' },
        fNombre: { required: true, pattern: /^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$/u, requiredMsg: 'Nombre requerido', patternMsg: 'Solo letras y espacios' },
        fApellido: { required: true, pattern: /^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$/u, requiredMsg: 'Apellido requerido', patternMsg: 'Solo letras y espacios' },
        fTelefono: { required: true, pattern: /^04\d{9}$/, requiredMsg: 'Teléfono requerido', patternMsg: 'Debe tener 11 dígitos y comenzar por 04' },
        fEmail: { email: true }
    });
    Validator.setRules('vehicleForm', {
        vMarca: { required: true, minLength: 2, requiredMsg: 'Marca requerida' },
        vModelo: { required: true, minLength: 1, requiredMsg: 'Modelo requerido' },
        vKm: { min: 0, minMsg: 'El kilometraje no puede ser negativo' }
    });
    Validator.setupRealtime('clientForm');
    Validator.setupRealtime('vehicleForm');
    $('#fCedula').on('input', debounce(validateUniqueClientCedula, 350));
    $('#fCedulaPrefijo').on('change', debounce(validateUniqueClientCedula, 350));
    $('#fEmail').on('input', debounce(validateUniqueClientEmail, 350));
});

function debounce(fn, ms) {
    let t; return function (...a) { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), ms); };
}

function loadStats() {
    $.get('/api/clients/stats', function (r) {
        if (r.status === 'success') {
            $('#totalClients').text(r.data.total);
            $('#activeClients').text(r.data.activos);
        }
    });
}

function loadClients() {
    const q = $('#searchInput').val();
    const estado = $('#filterEstado').val();
    let url = '/api/clients/?';
    if (q) url += `q=${encodeURIComponent(q)}&`;
    if (estado !== '') url += `estado=${estado}&`;

    $.get(url, function (r) {
        const tbody = $('#clientsTableBody');
        tbody.empty();
        if (!r.data || r.data.length === 0) {
            tbody.html('<tr><td colspan="7" class="text-center py-4 text-muted">No se encontraron clientes</td></tr>');
            return;
        }
        r.data.forEach(c => {
            const estado = c.estado ? '<span class="badge bg-success">Activo</span>' : '<span class="badge bg-secondary">Inactivo</span>';
            tbody.append(`
                <tr style="cursor:pointer" onclick="showDetail('${c.cedula}')">
                    <td><strong>${c.cedula}</strong></td>
                    <td>${c.nombre} ${c.apellido}</td>
                    <td>${c.telefono || '<span class="text-muted">—</span>'}</td>
                    <td>${c.email || '<span class="text-muted">—</span>'}</td>
                    <td><span class="badge bg-info">${c.vehiculos_count || 0}</span></td>
                    <td>${estado}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="event.stopPropagation(); editClient('${c.cedula}')" title="Modificar Cliente"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-warning" onclick="event.stopPropagation(); toggleClient('${c.cedula}')" title="Eliminar Cliente"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>
            `);
        });
    });
}

function showDetail(cedula) {
    currentCedula = cedula;
    $.get(`/api/clients/${cedula}`, function (r) {
        if (r.status !== 'success') return;
        const c = r.data;
        $('#detCedula').text(c.cedula);
        $('#detNombre').text(`${c.nombre} ${c.apellido}`);
        $('#detTelefono').text(c.telefono || '—');
        $('#detEmail').text(c.email || '—');
        $('#detDireccion').text(c.direccion || '—');

        let vhtml = '';
        if (c.vehiculos && c.vehiculos.length > 0) {
            vhtml = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Placa</th><th>Marca</th><th>Modelo</th><th>Año</th><th>Km</th><th>Combustible</th><th>Acciones</th></tr></thead><tbody>';
            c.vehiculos.forEach(v => {
                vhtml += `<tr>
                    <td><strong>${v.placa || '—'}</strong></td>
                    <td>${v.marca}</td><td>${v.modelo}</td>
                    <td>${v.anio || '—'}</td>
                    <td>${(v.kilometraje_actual || 0).toLocaleString()}</td>
                    <td>${v.tipo_combustible || '—'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="editVehicle(${v.id})" title="Modificar Vehículo"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteVehicle(${v.id})" title="Eliminar Vehículo"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`;
            });
            vhtml += '</tbody></table></div>';
        } else {
            vhtml = '<p class="text-muted text-center py-3">Sin vehículos registrados</p>';
        }
        $('#vehiclesList').html(vhtml);

        let shtml = '';
        if (c.servicios && c.servicios.length > 0) {
            shtml = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Fecha</th><th>Vehículo</th><th>Descripción</th><th>Km</th></tr></thead><tbody>';
            c.servicios.forEach(s => {
                shtml += `<tr><td>${formatDate(s.fecha)}</td><td>${s.placa || ''} ${s.marca} ${s.modelo}</td><td>${s.descripcion || '—'}</td><td>${s.kilometraje || '—'}</td></tr>`;
            });
            shtml += '</tbody></table></div>';
        } else {
            shtml = '<p class="text-muted text-center py-3">Sin servicios registrados</p>';
        }
        $('#servicesList').html(shtml);

        let thtml = '';
        if (c.tickets && c.tickets.length > 0) {
            thtml = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>ID</th><th>Asunto</th><th>Estado</th><th>Prioridad</th><th>Fecha</th></tr></thead><tbody>';
            c.tickets.forEach(t => {
                thtml += `<tr><td>#${t.id}</td><td>${t.asunto}</td><td>${estadoBadge(t.estado)}</td><td>${estadoBadge(t.prioridad)}</td><td>${formatDate(t.created_at)}</td></tr>`;
            });
            thtml += '</tbody></table></div>';
        } else {
            thtml = '<p class="text-muted text-center py-3">Sin tickets</p>';
        }
        $('#ticketsList').html(thtml);

        let ohtml = '';
        if (c.ordenes && c.ordenes.length > 0) {
            ohtml = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>ID</th><th>Total</th><th>Estado</th><th>Fecha</th></tr></thead><tbody>';
            c.ordenes.forEach(o => {
                ohtml += `<tr><td>#${o.id}</td><td data-usd-price="${o.total}">${formatUsdBs(o.total)}</td><td>${estadoBadge(o.estado)}</td><td>${formatDate(o.created_at || o.fecha)}</td></tr>`;
            });
            ohtml += '</tbody></table></div>';
        } else {
            ohtml = '<p class="text-muted text-center py-3">Sin órdenes</p>';
        }
        $('#ordersList').html(ohtml);

        let nhtml = '';
        if (c.notificaciones && c.notificaciones.length > 0) {
            nhtml = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Tipo</th><th>Título</th><th>Mensaje</th><th>Estado</th><th>Fecha</th></tr></thead><tbody>';
            c.notificaciones.forEach(n => {
                const readBadge = n.leida ? '<span class="badge bg-secondary">Leída</span>' : '<span class="badge bg-warning">No leída</span>';
                nhtml += `<tr><td>${estadoBadge(n.tipo)}</td><td><strong>${n.titulo || ''}</strong></td><td>${(n.mensaje || '').substring(0, 80)}</td><td>${readBadge}</td><td>${formatDate(n.created_at)}</td></tr>`;
            });
            nhtml += '</tbody></table></div>';
        } else {
            nhtml = '<p class="text-muted text-center py-3">Sin notificaciones</p>';
        }
        $('#notificationsList').html(nhtml);

        let bhtml = '';
        if (c.bitacora && c.bitacora.length > 0) {
            bhtml = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Fecha</th><th>Vehículo</th><th>Tipo</th><th>Descripción</th><th>Km</th></tr></thead><tbody>';
            c.bitacora.forEach(b => {
                bhtml += `<tr><td>${formatDate(b.fecha)}</td><td>${b.placa || ''} ${b.marca} ${b.modelo}</td><td>${estadoBadge(b.tipo_registro || '')}</td><td>${b.descripcion || '—'}</td><td>${b.kilometraje || '—'}</td></tr>`;
            });
            bhtml += '</tbody></table></div>';
        } else {
            bhtml = '<p class="text-muted text-center py-3">Sin registros en bitácora</p>';
        }
        $('#bitacoraList').html(bhtml);

        $('#detailPanel').slideDown(200);
        $('html,body').animate({ scrollTop: $('#detailPanel').offset().top - 80 }, 300);
    });
}

function hideDetail() {
    $('#detailPanel').slideUp(200);
    currentCedula = null;
}

function showCreateModal() {
    $('#clientModalTitle').text('Registrar Cliente');
    Validator.clearForm('clientForm');
    $('#editCedula').val('');
    $('#fCedulaPrefijo').val('V').prop('disabled', false);
    $('#fCedula').prop('disabled', false);
    new bootstrap.Modal('#clientModal').show();
    Validator.initTracking('clientForm');
}

function editClient(cedula) {
    $.get(`/api/clients/${cedula}`, function (r) {
        if (r.status !== 'success') return;
        const c = r.data;
        $('#clientModalTitle').text('Modificar Cliente');
        $('#editCedula').val(cedula);
        setDocumentFields('fCedulaPrefijo', 'fCedula', cedula);
        $('#fCedulaPrefijo').prop('disabled', true);
        $('#fCedula').prop('disabled', true);
        $('#fNombre').val(c.nombre);
        $('#fApellido').val(c.apellido);
        $('#fTelefono').val(c.telefono);
        $('#fEmail').val(c.email);
        $('#fDireccion').val(c.direccion);
        new bootstrap.Modal('#clientModal').show();
        Validator.initTracking('clientForm');
    });
}

function saveClient() {
    if (!Validator.validate('clientForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const cedula = $('#editCedula').val();
    const data = {
        cedula_prefijo: $('#fCedulaPrefijo').val(),
        cedula_numero: $('#fCedula').val(),
        cedula: buildDocumentValue('fCedulaPrefijo', 'fCedula'),
        nombre: $('#fNombre').val(),
        apellido: $('#fApellido').val(),
        telefono: $('#fTelefono').val(),
        email: $('#fEmail').val(),
        direccion: $('#fDireccion').val()
    };
    const url = cedula ? `/api/clients/${cedula}` : '/api/clients/';
    const method = cedula ? 'PUT' : 'POST';
    const btn = document.querySelector('#clientModal .modal-footer .btn-orange');
    setButtonLoading(btn, true, 'Guardando...');

    $.ajax({ url, type: method, contentType: 'application/json', data: JSON.stringify(data),
        success: function (r) {
            showToast(r.message, 'success');
            Validator.clearForm('clientForm');
            bootstrap.Modal.getInstance(document.getElementById('clientModal'))?.hide();
            loadClients();
            loadStats();
            if (cedula && currentCedula === cedula) showDetail(cedula);
        },
        error: function (x) {
            if (x.responseJSON?.errors) Validator.showServerErrors('clientForm', x.responseJSON.errors);
            showToast(x.responseJSON?.message || 'No se pudo guardar el cliente', 'error');
        },
        complete: function () { setButtonLoading(btn, false); }
    });
}

function toggleClient(cedula) {
    confirmAction('¿Estás seguro de que deseas eliminar este cliente?', () => {
        $.ajax({ url: `/api/clients/${cedula}/toggle`, type: 'PUT',
            success: function (r) { showToast(r.message, 'success'); loadClients(); loadStats(); },
            error: function (x) { showToast(x.responseJSON?.message || 'No se pudo eliminar el cliente', 'error'); }
        });
    });
}

function showVehicleModal(vehicleData) {
    if (!currentCedula) return;
    Validator.clearForm('vehicleForm');
    pendingVehicleCarnetFile = null;
    $('#vCarnetFile').val('');
    $('#vCarnetFileName').text('No seleccionado');
    if (vehicleData) {
        $('#vehicleModalTitle').text('Modificar Vehículo');
        $('#editVehicleId').val(vehicleData.id);
        $('#vMarca').val(vehicleData.marca);
        $('#vModelo').val(vehicleData.modelo);
        $('#vAnio').val(vehicleData.anio);
        $('#vPlaca').val(vehicleData.placa);
        $('#vColor').val(vehicleData.color);
        $('#vTipo').val(vehicleData.tipo_vehiculo);
        $('#vCombustible').val(vehicleData.tipo_combustible);
        $('#vKm').val(vehicleData.kilometraje_actual);
    } else {
        $('#vehicleModalTitle').text('Registrar Vehículo');
        $('#editVehicleId').val('');
    }
    new bootstrap.Modal('#vehicleModal').show();
    Validator.initTracking('vehicleForm');
}

function editVehicle(vid) {
    if (!currentCedula) return;
    $.get(`/api/vehicles/${vid}`, function (r) {
        if (r.status === 'success') showVehicleModal(r.data);
    });
}

function deleteVehicle(vid) {
    if (!currentCedula) return;
    confirmAction('¿Estás seguro de que deseas eliminar este vehículo?', () => {
        $.ajax({ url: `/api/clients/${currentCedula}/vehicles/${vid}`, type: 'DELETE',
            success: function (r) {
                showToast(r.message, 'success');
                showDetail(currentCedula);
            },
            error: function (x) { showToast(x.responseJSON?.message || 'No se pudo eliminar el vehículo', 'error'); }
        });
    });
}

function saveVehicle() {
    if (!currentCedula) return;
    if (!Validator.validate('vehicleForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const vid = $('#editVehicleId').val();
    const data = {
        marca: $('#vMarca').val(),
        modelo: $('#vModelo').val(),
        anio: parseInt($('#vAnio').val()) || null,
        placa: $('#vPlaca').val(),
        color: $('#vColor').val(),
        tipo_vehiculo: $('#vTipo').val(),
        tipo_combustible: $('#vCombustible').val(),
        kilometraje_actual: parseInt($('#vKm').val()) || 0
    };
    $('#vCombustible').removeClass('is-invalid');
    $('#vCombustibleFeedback').text('');
    if (!isValidConstant('TIPOS_COMBUSTIBLE', data.tipo_combustible)) {
        $('#vCombustible').addClass('is-invalid');
        $('#vCombustibleFeedback').text('Select alterado: valor no permitido');
        showAlteredSelect('Combustible alterado: valor no permitido');
        return;
    }

    const url = vid ? `/api/clients/${currentCedula}/vehicles/${vid}` : `/api/clients/${currentCedula}/vehicles`;
    const method = vid ? 'PUT' : 'POST';

    $.ajax({
        url,
        type: method,
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: async function (r) {
            const targetVehicleId = vid || r.id;
            let carnetWarning = '';
            if (pendingVehicleCarnetFile && targetVehicleId) {
                const carnetUpload = await uploadVehicleCarnet(targetVehicleId, pendingVehicleCarnetFile);
                if (!carnetUpload.ok) carnetWarning = ` (${carnetUpload.message})`;
            }
            showToast((r.message || 'Vehículo guardado correctamente') + carnetWarning, 'success');
            pendingVehicleCarnetFile = null;
            $('#vCarnetFile').val('');
            $('#vCarnetFileName').text('No seleccionado');
            bootstrap.Modal.getInstance(document.getElementById('vehicleModal'))?.hide();
            showDetail(currentCedula);
        },
        error: function (x) {
            if (x.responseJSON?.errors) Validator.showServerErrors('vehicleForm', x.responseJSON.errors);
            showToast(x.responseJSON?.message || 'No se pudo guardar el vehículo', 'error');
        }
    });
}

async function validateUniqueClientCedula() {
    const input = document.getElementById('fCedula');
    if (!input || input.disabled) return true;
    if (!input.value.trim()) {
        delete input.dataset.externalError;
        clearFieldError(input);
        updateFormSubmitState('clientForm');
        return true;
    }
    if (!Validator.validateField('clientForm', 'fCedula')) {
        delete input.dataset.externalError;
        updateFormSubmitState('clientForm');
        return false;
    }
    try {
        const exclude = document.getElementById('editCedula')?.value || '';
        const value = buildDocumentValue('fCedulaPrefijo', 'fCedula');
        const res = await fetch(`/api/clients/check-unique?field=cedula&value=${encodeURIComponent(value)}&exclude=${encodeURIComponent(exclude)}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && data.exists && data.active) {
            input.dataset.externalError = 'Esta cédula ya está registrada';
            setFieldError(input, 'Esta cédula ya está registrada');
            updateFormSubmitState('clientForm');
            return false;
        }
        if (data.status === 'success' && data.exists && !data.active) {
            delete input.dataset.externalError;
            clearFieldError(input);
            updateFormSubmitState('clientForm');
            return true;
        }
        delete input.dataset.externalError;
        clearFieldError(input);
        updateFormSubmitState('clientForm');
    } catch (e) {}
    return true;
}

async function validateUniqueClientEmail() {
    const input = document.getElementById('fEmail');
    if (!input) return true;
    const value = input.value.trim();
    if (!value) {
        delete input.dataset.externalError;
        clearFieldError(input);
        updateFormSubmitState('clientForm');
        return true;
    }
    if (!Validator.validateField('clientForm', 'fEmail')) {
        delete input.dataset.externalError;
        updateFormSubmitState('clientForm');
        return false;
    }
    try {
        const exclude = document.getElementById('editCedula')?.value || buildDocumentValue('fCedulaPrefijo', 'fCedula');
        const res = await fetch(`/api/clients/check-unique?field=email&value=${encodeURIComponent(value)}&exclude=${encodeURIComponent(exclude)}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && data.exists) {
            input.dataset.externalError = 'Este correo ya está registrado';
            setFieldError(input, 'Este correo ya está registrado');
            updateFormSubmitState('clientForm');
            return false;
        }
        if (data.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('clientForm');
    } catch (e) {}
    return true;
}

function uploadVehicleCarnet(vehicleId, file) {
    return new Promise(resolve => {
        const formData = new FormData();
        formData.append('imagen', file);
        $.ajax({
            url: `/api/vehicles/${vehicleId}/carnet`,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function () {
                resolve({ ok: true });
            },
            error: function (x) {
                resolve({ ok: false, message: x.responseJSON?.message || 'No se pudo subir el título' });
            }
        });
    });
}

function scanVehicleTitleAndFillAdmin(file) {
    const fd = new FormData();
    fd.append('imagen', file);
    $.ajax({
        url: '/api/vehicles/scan-title',
        type: 'POST',
        data: fd,
        processData: false,
        contentType: false,
        success: function (r) {
            if (r.status !== 'success' || !r.data) {
                showToast(r.message || 'No se pudo leer el documento automáticamente', 'warning');
                return;
            }
            const d = r.data;
            if (d.marca) $('#vMarca').val(d.marca);
            if (d.modelo) $('#vModelo').val(d.modelo);
            if (d.anio) $('#vAnio').val(d.anio);
            if (d.placa) $('#vPlaca').val(d.placa);
            if (d.color) $('#vColor').val(d.color);
            if (d.tipo_vehiculo) $('#vTipo').val(d.tipo_vehiculo);
            if (d.tipo_combustible && isValidConstant('TIPOS_COMBUSTIBLE', d.tipo_combustible)) {
                $('#vCombustible').val(d.tipo_combustible);
            }
            showToast('Datos del documento cargados automáticamente', 'success');
        },
        error: function (x) {
            showToast(x.responseJSON?.message || 'No se pudo procesar el documento automáticamente', 'warning');
        }
    });
}
