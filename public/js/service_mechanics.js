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
        estado: { required: true, requiredMsg: 'Debe seleccionar un estado' },
        fecha: { required: true, requiredMsg: 'Debe seleccionar una fecha' }
    });
    Validator.setupRealtime('assignmentForm');

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

async function loadAssignments() {
    try {
        const res = await apiCall('/api/service-mechanics/');
        const assignments = res.data || [];
        const tbody = document.getElementById('assignmentBody');
        tbody.innerHTML = '';

        let noAssigned = 0;

        assignments.forEach(a => {
            const hasMechanic = !!(a.mecanico_cedula || '').trim();
            if (!hasMechanic) noAssigned += 1;

            const mechanicHtml = hasMechanic
                ? `<div><strong>${a.mecanico_nombre || a.mecanico_cedula}</strong><br><small class="text-muted">${a.mecanico_cedula}</small></div>`
                : '<span class="badge-status badge-pending">Sin asignar</span>';

            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${a.id}</td>
                <td><strong>${a.servicio_nombre || '-'}</strong></td>
                <td>${a.orden_venta_id || '-'}</td>
                <td>${mechanicHtml}</td>
                <td>${statusSelect(a.id, a.estado)}</td>
                <td>${formatDate(a.fecha)}</td>
                <td>${a.observaciones || '-'}</td>
                <td>
                    ${!hasMechanic ? `<button class="btn btn-icon btn-outline-orange btn-sm" title="Asignar Mecánico" onclick="openMechanicModal(${a.id})"><i class="bi bi-person-plus"></i></button>` : ''}
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editAssignment(${a.id})" title="Modificar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="deleteAssignment(${a.id})" title="Eliminar"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });

        if (!assignments.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-tools"></i><p>No hay registros de servicio mecánico</p></div></td></tr>';
        }

        document.getElementById('statTotal').textContent = assignments.length;
        document.getElementById('statNoAssigned').textContent = noAssigned;
    } catch (e) { }
}

// Para la bitácora
function statusSelect(id, current) {
    const options = [
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
    const idInput = document.getElementById('assignmentId');
    if (idInput) idInput.value = '';
    document.getElementById('assignmentModalTitle').textContent = 'Registrar Servicio Mecánico';
    document.getElementById('orden_venta_id').value = '';
    document.getElementById('mecanico_cedula').value = '';
    document.getElementById('observaciones').value = '';
    document.getElementById('cliente_cedula').value = '';
    document.getElementById('vehiculo_placa').value = '';
    document.getElementById('estado').value = 'asignado';

    const now = new Date();
    const tzoffset = now.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(Date.now() - tzoffset)).toISOString().slice(0, 16);
    document.getElementById('fecha').value = localISOTime;

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
        estado: document.getElementById('estado').value || 'asignado',
        fecha: document.getElementById('fecha').value || null
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
        
        const idInput = document.getElementById('assignmentId');
        if (idInput) idInput.value = a.id;
        
        document.getElementById('servicio_id').value = a.servicio_id || '';
        document.getElementById('mecanico_cedula').value = a.mecanico_cedula || '';
        document.getElementById('orden_venta_id').value = a.orden_venta_id || '';
        document.getElementById('observaciones').value = a.observaciones || '';
        document.getElementById('cliente_cedula').value = a.cliente_cedula || '';
        document.getElementById('estado').value = a.estado || 'asignado';

        if (a.fecha) {
            const cleanFecha = a.fecha.replace(' ', 'T');
            const date = new Date(cleanFecha);
            if (!isNaN(date.getTime())) {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                document.getElementById('fecha').value = `${year}-${month}-${day}T${hours}:${minutes}`;
            } else {
                const match = a.fecha.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/);
                if (match) {
                    document.getElementById('fecha').value = `${match[1]}T${match[2]}`;
                } else {
                    document.getElementById('fecha').value = '';
                }
            }
        } else {
            document.getElementById('fecha').value = '';
        }

        loadVehiclesForClient(a.cliente_cedula).then(() => {
            document.getElementById('vehiculo_placa').value = a.vehiculo_placa || '';
        });
        
        document.getElementById('assignmentModalTitle').textContent = 'Modificar Servicio Mecánico';
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
    document.getElementById('assignmentIdForMechanic').value = assignmentId;
    document.getElementById('assignment_mechanic_cedula').value = '';
    mechanicModal.show();
}

async function saveMechanicAssignment() {
    const assignmentId = document.getElementById('assignmentIdForMechanic').value;
    const mecanicoCedula = document.getElementById('assignment_mechanic_cedula').value;

    if (!assignmentId || !mecanicoCedula) {
        showToast('Seleccione un mecánico', 'warning');
        return;
    }

    try {
        const saveBtn = document.querySelector('#mechanicAssignModal .btn-orange');
        setButtonLoading(saveBtn, true, 'Asignando...');
        const res = await apiCall(`/api/service-mechanics/${assignmentId}/mechanic`, 'PUT', {
            mecanico_cedula: mecanicoCedula
        });
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') return showToast(res.message, 'error');
        mechanicModal.hide();
        showToast(res.message || 'Mecánico asignado correctamente', 'success');
        loadAssignments();
    } catch (e) { }
}

async function updateAssignmentStatus(assignmentId, estado) {
    try {
        const res = await apiCall(`/api/service-mechanics/${assignmentId}/status`, 'PUT', { estado });
        if (res.status === 'error') {
            showToast(res.message, 'error');
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
