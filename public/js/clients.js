let currentCedula = null;
let pendingVehicleCarnetFile = null;

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html');
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
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="event.stopPropagation(); editClient('${c.cedula}')" title="Editar"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-warning" onclick="event.stopPropagation(); toggleClient('${c.cedula}')" title="Cambiar estado"><i class="bi bi-toggle-on"></i></button>
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
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="editVehicle(${v.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteVehicle(${v.id})" title="Eliminar"><i class="bi bi-trash"></i></button>
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
                ohtml += `<tr><td>#${o.id}</td><td>$${formatCurrency(o.total)}</td><td>${estadoBadge(o.estado)}</td><td>${formatDate(o.created_at || o.fecha)}</td></tr>`;
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
    $('#clientModalTitle').text('Nuevo Cliente');
    $('#clientForm')[0].reset();
    $('#editCedula').val('');
    $('#fCedula').prop('disabled', false);
    new bootstrap.Modal('#clientModal').show();
}

function editClient(cedula) {
    $.get(`/api/clients/${cedula}`, function (r) {
        if (r.status !== 'success') return;
        const c = r.data;
        $('#clientModalTitle').text('Editar Cliente');
        $('#editCedula').val(cedula);
        $('#fCedula').val(cedula).prop('disabled', true);
        $('#fNombre').val(c.nombre);
        $('#fApellido').val(c.apellido);
        $('#fTelefono').val(c.telefono);
        $('#fEmail').val(c.email);
        $('#fDireccion').val(c.direccion);
        new bootstrap.Modal('#clientModal').show();
    });
}

function saveClient() {
    const cedula = $('#editCedula').val();
    const data = {
        cedula: $('#fCedula').val(),
        nombre: $('#fNombre').val(),
        apellido: $('#fApellido').val(),
        telefono: $('#fTelefono').val(),
        email: $('#fEmail').val(),
        direccion: $('#fDireccion').val()
    };
    if (!data.nombre || !data.apellido) { showToast('Nombre y apellido requeridos', 'error'); return; }
    if (!data.telefono || data.telefono.length < 7) { showToast('Teléfono requerido (min 7 caracteres)', 'error'); return; }

    const url = cedula ? `/api/clients/${cedula}` : '/api/clients/';
    const method = cedula ? 'PUT' : 'POST';
    if (!cedula && !data.cedula) { showToast('Cédula requerida', 'error'); return; }

    $.ajax({ url, type: method, contentType: 'application/json', data: JSON.stringify(data),
        success: function (r) {
            showToast(r.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('clientModal'))?.hide();
            loadClients();
            loadStats();
            if (cedula && currentCedula === cedula) showDetail(cedula);
        },
        error: function (x) { showToast(x.responseJSON?.message || 'Error', 'error'); }
    });
}

function toggleClient(cedula) {
    if (!confirm('¿Cambiar estado del cliente?')) return;
    $.ajax({ url: `/api/clients/${cedula}/toggle`, type: 'PUT',
        success: function (r) { showToast(r.message, 'success'); loadClients(); loadStats(); },
        error: function (x) { showToast(x.responseJSON?.message || 'Error', 'error'); }
    });
}

function showVehicleModal(vehicleData) {
    if (!currentCedula) return;
    $('#vehicleForm')[0].reset();
    pendingVehicleCarnetFile = null;
    $('#vCarnetFile').val('');
    $('#vCarnetFileName').text('No seleccionado');
    if (vehicleData) {
        $('#vehicleModalTitle').text('Editar Vehículo');
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
        $('#vehicleModalTitle').text('Agregar Vehículo');
        $('#editVehicleId').val('');
    }
    new bootstrap.Modal('#vehicleModal').show();
}

function editVehicle(vid) {
    if (!currentCedula) return;
    $.get(`/api/vehicles/${vid}`, function (r) {
        if (r.status === 'success') showVehicleModal(r.data);
    });
}

function deleteVehicle(vid) {
    if (!currentCedula) return;
    if (!confirm('¿Eliminar este vehículo?')) return;
    $.ajax({ url: `/api/clients/${currentCedula}/vehicles/${vid}`, type: 'DELETE',
        success: function (r) {
            showToast(r.message, 'success');
            showDetail(currentCedula);
        },
        error: function (x) { showToast(x.responseJSON?.message || 'Error', 'error'); }
    });
}

function saveVehicle() {
    if (!currentCedula) return;
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
    if (!data.marca || !data.modelo) { showToast('Marca y modelo requeridos', 'error'); return; }
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
            showToast((r.message || 'Vehiculo guardado') + carnetWarning, 'success');
            pendingVehicleCarnetFile = null;
            $('#vCarnetFile').val('');
            $('#vCarnetFileName').text('No seleccionado');
            bootstrap.Modal.getInstance(document.getElementById('vehicleModal'))?.hide();
            showDetail(currentCedula);
        },
        error: function (x) { showToast(x.responseJSON?.message || 'Error', 'error'); }
    });
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
                resolve({ ok: false, message: x.responseJSON?.message || 'No se pudo subir el titulo' });
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
                showToast(r.message || 'No se pudo leer el documento automaticamente', 'warning');
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
            showToast('Datos del documento cargados automaticamente', 'success');
        },
        error: function (x) {
            showToast(x.responseJSON?.message || 'No se pudo procesar el documento automaticamente', 'warning');
        }
    });
}
