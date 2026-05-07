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
        servicio_id: { required: true, requiredMsg: 'Debe seleccionar un servicio' }
    });
    Validator.setupRealtime('assignmentForm');

    initializeCatalogs().then(() => loadAssignments());
});

async function initializeCatalogs() {
    await Promise.all([loadServices(), loadMechanics(), loadOrders()]);
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
        document.getElementById('assignment_mechanic_cedula').innerHTML = '<option value="">Seleccione mecanico</option>' + allOptions;
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
                    ${!hasMechanic ? `<button class="btn btn-icon btn-outline-orange btn-sm" title="Asignar mecanico" onclick="openMechanicModal(${a.id})"><i class="bi bi-person-plus"></i></button>` : ''}
                </td>
            </tr>`;
        });

        if (!assignments.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-tools"></i><p>No hay registros de servicio mecanico</p></div></td></tr>';
        }

        document.getElementById('statTotal').textContent = assignments.length;
        document.getElementById('statNoAssigned').textContent = noAssigned;
    } catch (e) { }
}

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
    document.getElementById('assignmentModalTitle').textContent = 'Nuevo Registro Servicio Mecanico';
    document.getElementById('orden_venta_id').value = '';
    assignmentModal.show();
}

async function saveAssignment() {
    if (!Validator.validate('assignmentForm')) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }

    const data = {
        servicio_id: parseInt(document.getElementById('servicio_id').value, 10),
        mecanico_cedula: document.getElementById('mecanico_cedula').value || null,
        orden_venta_id: document.getElementById('orden_venta_id').value ? parseInt(document.getElementById('orden_venta_id').value, 10) : null,
        observaciones: document.getElementById('observaciones').value || ''
    };
    const saveBtn = document.querySelector('#assignmentModal .btn-orange');

    try {
        setButtonLoading(saveBtn, true, 'Guardando...');
        const res = await apiCall('/api/service-mechanics/', 'POST', data);
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') {
            Validator.showServerErrors('assignmentForm', res.errors);
            return showToast(res.message, 'error');
        }
        assignmentModal.hide();
        showToast(res.message || 'Servicio mecanico registrado correctamente', 'success');
        loadAssignments();
    } catch (e) { }
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
        showToast('Seleccione un mecanico', 'warning');
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
        showToast(res.message || 'Mecanico asignado correctamente', 'success');
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
