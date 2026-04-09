$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="services"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadSucursales('sucursal_id', true);
    Validator.setRules('serviceForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'Nombre requerido', minLengthMsg: 'Minimo 3 caracteres' },
        precio: { required: true, min: 0.01, requiredMsg: 'Precio requerido', minMsg: 'Debe ser mayor a 0' }
    });
    Validator.setupRealtime('serviceForm');
});

function loadData() {
    apiCall('/api/services/').then(res => {
        const tbody = document.getElementById('serviceBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(s => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${s.id}</td>
                <td><strong>${s.nombre}</strong></td>
                <td><span class="badge-status badge-info">${s.tipo || 'general'}</span></td>
                <td>${s.sucursal_nombre || 'Todas'}</td>
                <td class="fw-bold" style="color:var(--primary);">$${formatCurrency(s.precio)}</td>
                <td>${s.duracion_estimada || '-'} min</td>
                <td>${statusBadge(s.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${s.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${s.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado(${s.id})" title="${s.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${s.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-wrench-adjustable"></i><p>No hay servicios registrados</p></div></td></tr>';
        }
    });
}

function openModal(id = null) {
    Validator.clearForm('serviceForm');
    document.getElementById('serviceId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Editar Servicio' : 'Nuevo Servicio';
    new bootstrap.Modal(document.getElementById('serviceModal')).show();
}

function editData(id) {
    apiCall(`/api/services/${id}`).then(res => {
        const s = res.data;
        document.getElementById('serviceId').value = s.id;
        document.getElementById('nombre').value = s.nombre;
        document.getElementById('descripcion').value = s.descripcion || '';
        document.getElementById('tipo').value = s.tipo || 'general';
        document.getElementById('precio').value = s.precio;
        document.getElementById('duracion_estimada').value = s.duracion_estimada || 60;
        const sucSel = document.getElementById('sucursal_id');
        if(sucSel) sucSel.value = s.sucursal_id || '';
        document.getElementById('modalTitle').textContent = 'Editar Servicio';
        new bootstrap.Modal(document.getElementById('serviceModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('serviceForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('serviceId').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        tipo: document.getElementById('tipo').value,
        precio: parseFloat(document.getElementById('precio').value),
        duracion_estimada: parseInt(document.getElementById('duracion_estimada').value) || 60,
        sucursal_id: document.getElementById('sucursal_id')?.value || null
    };
    const url = id ? `/api/services/${id}` : '/api/services/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('serviceForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('serviceModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Cambiar estado de este servicio?', () => {
        apiCall(`/api/services/${id}/toggle`, 'PUT').then(res => { showToast(res.message); loadData(); });
    });
}
