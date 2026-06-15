let assignmentModal;
let mechanicModal;
let mechanicsCache = [];
let ordersCache = [];

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="service_mechanics"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');

    assignmentModal = new bootstrap.Modal(document.getElementById('assignmentModal'));
    mechanicModal = new bootstrap.Modal(document.getElementById('mechanicAssignModal'));

    Validator.setRules('assignmentForm', {
        servicio_id: { required: true, requiredMsg: 'Debe seleccionar un servicio' },
        cliente_cedula: { required: true, requiredMsg: 'Debe seleccionar un cliente' },
        vehiculo_placa: { required: true, requiredMsg: 'Debe seleccionar un vehículo' },
        estado: { required: true, requiredMsg: 'Debe seleccionar un estado' },
        observaciones: {
            maxLength: 255,
            maxLengthMsg: 'Las observaciones no pueden superar los 255 caracteres.',
            pattern: /^$|^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s.,-]+$/,
            patternMsg: 'Las observaciones solo pueden contener letras, números, espacios, puntos, comas y guiones.',
            custom: () => {
                const el = document.getElementById('observaciones');
                return !el || !el.value || el.value.trim().length > 0;
            },
            customMsg: 'Las observaciones no pueden contener solo espacios en blanco.'
        }
    });
    Validator.setupRealtime('assignmentForm');

    Validator.setRules('mechanicAssignForm', {
        assignment_mechanic_cedula: { required: true, requiredMsg: 'Debe seleccionar un mecánico' },
        assignment_mechanic_commission: {
            required: true,
            requiredMsg: 'El porcentaje de comisión es obligatorio',
            custom: v => {
                const n = parseFloat(v);
                return !isNaN(n) && n > 0 && n <= 100;
            },
            customMsg: 'El porcentaje debe ser mayor a 0 y máximo 100'
        }
    });
    Validator.setupRealtime('mechanicAssignForm');

    $('#orden_venta_id').change(function() {
        const orderId = $(this).val();
        if (orderId) {
            const order = ordersCache.find(o => o.id == orderId);
            if (order) {
                document.getElementById('cliente_cedula').value = order.cliente_cedula || '';
                onClienteChange();
            }
        }
    });

    initializeCatalogs().then(() => loadAssignments());
});

let clientsCache = [];

async function loadClients() {
    try {
        const res = await apiCall('/api/clients/?tipo_cliente=all');
        clientsCache = res.data || [];
        const select = document.getElementById('cliente_cedula');
        if (!select) return;
        select.innerHTML = '<option value="">Seleccione cliente...</option>';
        clientsCache.forEach(c => {
            select.innerHTML += `<option value="${c.cedula}">${escapeHtml(c.nombre)} ${escapeHtml(c.apellido)} (${c.cedula})</option>`;
        });
    } catch (e) {}
}

async function loadVehiclesForClient(clienteCedula) {
    const select = document.getElementById('vehiculo_placa');
    if (!select) return;
    select.innerHTML = '<option value="">Cargando vehículos...</option>';
    if (!clienteCedula) {
        select.innerHTML = '<option value="">Seleccione un cliente primero</option>';
        return;
    }
    try {
        const res = await apiCall(`/api/vehicles/?cliente=${encodeURIComponent(clienteCedula)}`);
        const vehicles = res.data || [];
        select.innerHTML = '<option value="">Seleccione vehículo...</option>';
        vehicles.forEach(v => {
            select.innerHTML += `<option value="${v.placa}">${escapeHtml(v.marca)} ${escapeHtml(v.modelo)} - ${escapeHtml(v.placa)}</option>`;
        });
    } catch (e) {
        select.innerHTML = '<option value="">Error al cargar vehículos</option>';
    }
}

function onClienteChange() {
    const clientCedula = document.getElementById('cliente_cedula').value;
    loadVehiclesForClient(clientCedula);
}

async function initializeCatalogs() {
    await Promise.all([loadServices(), loadMechanics(), loadOrders(), loadClients()]);
}

async function loadOrders() {
    try {
        const res = await apiCall('/api/inventory/sales-orders');
        ordersCache = res.data || [];
        const orderSelect = document.getElementById('orden_venta_id');
        if (!orderSelect) return;
        orderSelect.innerHTML = '<option value="">Sin orden</option>';
        ordersCache.forEach(order => {
            orderSelect.innerHTML += `<option value="${order.id}">#${order.id} - ${escapeHtml(order.cliente_nombre || 'Cliente')} - ${formatDate(order.fecha)}</option>`;
        });
    } catch (e) { }
}

async function loadServices() {
    try {
        const res = await apiCall('/api/services/active');
        const serviceSelect = document.getElementById('servicio_id');
        serviceSelect.innerHTML = '<option value="">Seleccione servicio</option>';
        (res.data || []).forEach(item => {
            serviceSelect.innerHTML += `<option value="${item.id}">${item.nombre}${item.sucursal_nombre ? ` - ${item.sucursal_nombre}` : ''}</option>`;
        });
    } catch (e) { }
}

async function loadMechanics() {
    try {
        const res = await apiCall('/api/mechanics/');
        mechanicsCache = (res.data || []).filter(m => Number(m.estado) === 1);
        const baseOptions = '<option value="">Sin asignar por ahora</option>';
        const allOptions = mechanicsCache.map(m => `<option value="${m.cedula}">${m.nombre} ${m.apellido} (${m.cedula})</option>`).join('');
        document.getElementById('mecanico_cedula').innerHTML = baseOptions + allOptions;
        document.getElementById('assignment_mechanic_cedula').innerHTML = '<option value="">Seleccione mecánico</option>' + allOptions;
    } catch (e) { }
}

let paginator = null;

async function loadAssignments() {
    try {
        const res = await apiCall('/api/service-mechanics/');
        const assignments = res.data || [];
        
        let noAssigned = 0;
        assignments.forEach(a => {
            const hasMechanic = !!(a.mecanico_cedula || '').trim();
            if (!hasMechanic) noAssigned += 1;
        });

        if (!paginator) {
            paginator = new TablePaginator('assignmentBody', {
                allData: assignments,
                itemName: 'servicios mecánicos',
                renderRow: (a) => {
                    const hasMechanic = !!(a.mecanico_cedula || '').trim();
                    const mechanicHtml = hasMechanic
                        ? `<div><strong>${escapeHtml(a.mecanico_nombre || a.mecanico_cedula)}</strong><br><small class="text-muted">${escapeHtml(a.mecanico_cedula)}</small></div>`
                        : '<span class="badge-status badge-pending">Sin asignar</span>';

                    return `<tr class="fade-in-up">
                        <td class="col-id">${a.id}</td>
                        <td><strong>${escapeHtml(a.servicio_nombre || '-')}</strong></td>
                        <td>${a.orden_venta_id || '-'}</td>
                        <td>${mechanicHtml}</td>
                        <td>${statusSelect(a.id, a.estado)}</td>
                        <td>${formatDate(a.fecha)}</td>
                        <td>${escapeHtml(a.observaciones || '-')}</td>
                        <td>
                            ${!hasMechanic ? `<button class="btn btn-icon btn-outline-orange btn-sm" title="Asignar Mecánico" onclick="openMechanicModal(${a.id})"><i class="bi bi-person-plus"></i></button>` : ''}
                            <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editAssignment(${a.id})" title="Modificar"><i class="bi bi-pencil"></i></button>
                            <button class="btn btn-icon btn-sm btn-warning" onclick="deleteAssignment(${a.id})" title="Eliminar"><i class="bi bi-trash"></i></button>
                        </td>
                    </tr>`;
                },
                onEmpty: () => '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-tools"></i><p>No hay registros de servicio mecánico</p></div></td></tr>'
            });
        } else {
            paginator.updateData(assignments);
        }

        document.getElementById('statTotal').textContent = assignments.length;
        document.getElementById('statNoAssigned').textContent = noAssigned;
    } catch (e) { }
}


function statusSelect(id, current) {
    const options = [
        ['sin_asignar', 'Sin asignar'],
        ['asignado', 'Asignado'],
        ['en_proceso', 'En proceso'],
        ['completado', 'Completado'],
        ['cancelado', 'Cancelado']
    ];

    const html = options.map(([value, label]) => `<option value="${value}" ${value === current ? 'selected' : ''}>${label}</option>`).join('');
    return `<select class="form-select form-select-sm" onchange="updateAssignmentStatus(${id}, this.value)">${html}</select>`;
}

function openAssignmentModal() {
    Validator.clearForm('assignmentForm');
    $('#assignmentId').val('');
    $('#assignmentModalTitle').text('Registrar Servicio Mecánico');
    $('#servicio_id').val('').trigger('change');
    $('#mecanico_cedula').val('').trigger('change');
    $('#orden_venta_id').val('');
    $('#observaciones').val('');
    $('#cliente_cedula').val('').trigger('change');
    $('#vehiculo_placa').val('').trigger('change');
    $('#estado').val('sin_asignar').trigger('change');
    $('#porcentaje_comision').val('');

    onClienteChange();

    assignmentModal.show();
    Validator.initTracking('assignmentForm');
}

async function saveAssignment() {
    if (!Validator.validate('assignmentForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }

    const idInput = document.getElementById('assignmentId');
    const id = idInput ? idInput.value : '';

    const data = {
        servicio_id: parseInt(document.getElementById('servicio_id').value, 10),
        mecanico_cedula: document.getElementById('mecanico_cedula').value || null,
        orden_venta_id: document.getElementById('orden_venta_id').value ? parseInt(document.getElementById('orden_venta_id').value, 10) : null,
        observaciones: document.getElementById('observaciones').value || '',
        cliente_cedula: document.getElementById('cliente_cedula').value || null,
        vehiculo_placa: document.getElementById('vehiculo_placa').value || null,
        estado: document.getElementById('estado').value || 'sin_asignar',
        porcentaje_comision: document.getElementById('porcentaje_comision').value || null
    };
    const saveBtn = document.querySelector('#assignmentModal .btn-orange');

    try {
        setButtonLoading(saveBtn, true, 'Guardando...');
        const url = id ? `/api/service-mechanics/${id}` : '/api/service-mechanics/';
        const method = id ? 'PUT' : 'POST';
        const res = await apiCall(url, method, data);
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') {
            Validator.showServerErrors('assignmentForm', res.errors);
            return showToast(res.message, 'error');
        }
        assignmentModal.hide();
        showToast(res.message || 'Servicio mecánico registrado correctamente', 'success');
        loadAssignments();
    } catch (e) { }
}

function editAssignment(id) {
    apiCall(`/api/service-mechanics/${id}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const a = res.data;
        Validator.clearForm('assignmentForm');

        $('#assignmentId').val(a.id);
        $('#orden_venta_id').val(a.orden_venta_id || '');
        $('#observaciones').val(a.observaciones || '');
        $('#estado').val(a.estado || 'sin_asignar').trigger('change');
        $('#porcentaje_comision').val(a.porcentaje_comision || '');


        const serviceSelect = document.getElementById('servicio_id');
        if (serviceSelect && a.servicio_id && !Array.from(serviceSelect.options).some(opt => opt.value == a.servicio_id)) {
            const opt = document.createElement('option');
            opt.value = a.servicio_id;
            opt.textContent = `${a.servicio_nombre || 'Servicio inactivo'} (Inactivo)`;
            serviceSelect.appendChild(opt);
        }
        $('#servicio_id').val(a.servicio_id || '').trigger('change');


        const mechanicSelect = document.getElementById('mecanico_cedula');
        if (mechanicSelect && a.mecanico_cedula && !Array.from(mechanicSelect.options).some(opt => opt.value == a.mecanico_cedula)) {
            const opt = document.createElement('option');
            opt.value = a.mecanico_cedula;
            opt.textContent = `${a.mecanico_nombre || a.mecanico_cedula} (Inactivo)`;
            mechanicSelect.appendChild(opt);
        }
        $('#mecanico_cedula').val(a.mecanico_cedula || '').trigger('change');


        const clientSelect = document.getElementById('cliente_cedula');
        if (clientSelect && a.cliente_cedula && !Array.from(clientSelect.options).some(opt => opt.value == a.cliente_cedula)) {
            const opt = document.createElement('option');
            opt.value = a.cliente_cedula;
            const name = a.cliente_nombre ? `${a.cliente_nombre} ${a.cliente_apellido || ''}` : (a.cliente_cedula === 'V-00000000' ? 'Cliente General' : 'Cliente Inactivo');
            opt.textContent = `${name} (${a.cliente_cedula})` + (a.cliente_cedula === 'V-00000000' ? '' : ' (Inactivo)');
            clientSelect.appendChild(opt);
        }
        $('#cliente_cedula').val(a.cliente_cedula || '').trigger('change');

        loadVehiclesForClient(a.cliente_cedula).then(() => {
            const vehicleSelect = document.getElementById('vehiculo_placa');
            if (vehicleSelect && a.vehiculo_placa && !Array.from(vehicleSelect.options).some(opt => opt.value == a.vehiculo_placa)) {
                const opt = document.createElement('option');
                opt.value = a.vehiculo_placa;
                const brand = a.vehiculo_marca || '';
                const modelName = a.vehiculo_modelo || '';
                opt.textContent = `${brand} ${modelName} - ${a.vehiculo_placa} (Inactivo)`;
                vehicleSelect.appendChild(opt);
            }
            $('#vehiculo_placa').val(a.vehiculo_placa || '').trigger('change');
        });

        $('#assignmentModalTitle').text('Modificar Servicio Mecánico');
        assignmentModal.show();
        Validator.initTracking('assignmentForm');
    });
}

function deleteAssignment(id) {
    confirmAction('¿Estás seguro de que deseas eliminar este registro de servicio mecánico?', () => {
        apiCall(`/api/service-mechanics/${id}`, 'DELETE').then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadAssignments();
        });
    });
}

function openMechanicModal(assignmentId) {
    Validator.clearForm('mechanicAssignForm');
    document.getElementById('assignmentIdForMechanic').value = assignmentId;
    $('#assignment_mechanic_cedula').val('').trigger('change');
    document.getElementById('assignment_mechanic_commission').value = '';
    mechanicModal.show();
    Validator.initTracking('mechanicAssignForm');
}

async function saveMechanicAssignment(confirmar) {
    if (!Validator.validate('mechanicAssignForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }

    const assignmentId = document.getElementById('assignmentIdForMechanic').value;
    const mecanicoCedula = document.getElementById('assignment_mechanic_cedula').value;

    if (!assignmentId || !mecanicoCedula) {
        showToast('Seleccione un mecánico', 'warning');
        return;
    }

    try {
        const saveBtn = document.querySelector('#mechanicAssignModal .btn-orange');
        setButtonLoading(saveBtn, true, 'Asignando...');
        const payload = {
            mecanico_cedula: mecanicoCedula,
            porcentaje_comision: document.getElementById('assignment_mechanic_commission').value,
            confirmar: !!confirmar
        };
        const res = await apiCall(`/api/service-mechanics/${assignmentId}/mechanic`, 'PUT', payload);
        setButtonLoading(saveBtn, false);
        if (res.status === 'confirm') {
            confirmAction(res.message, () => saveMechanicAssignment(true));
            return;
        }
        if (res.status === 'error') {
            Validator.showServerErrors('mechanicAssignForm', res.errors);
            return showToast(res.message, 'error');
        }
        mechanicModal.hide();
        showToast(res.message || 'Mecánico asignado correctamente', 'success');
        loadAssignments();
    } catch (e) { }
}

async function updateAssignmentStatus(assignmentId, estado) {
    try {
        const res = await apiCall(`/api/service-mechanics/${assignmentId}/status`, 'PUT', { estado });
        if (res.status === 'error') {
            const detalles = res.errors ? Object.values(res.errors).join(' ') : '';
            showToast(detalles || res.message, 'error');
            loadAssignments();
            return;
        }
        showToast(res.message || 'Estado actualizado', 'success');
    } catch (e) {
        loadAssignments();
    }
}

function escapeHtml(text) {
    return String(text ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
