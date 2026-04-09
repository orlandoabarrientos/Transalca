$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="suppliers"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('supplierForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'Nombre requerido', minLengthMsg: 'Minimo 3 caracteres' },
        rif: { required: true, pattern: /^[JGVEP]-\d{8}-\d$/, requiredMsg: 'RIF requerido', patternMsg: 'Formato: J-12345678-9' },
        email: { email: true },
        telefono: { minLength: 7, minLengthMsg: 'Minimo 7 caracteres' }
    });
    Validator.setupRealtime('supplierForm');
});

function loadData() {
    apiCall('/api/suppliers/').then(res => {
        const tbody = document.getElementById('supplierBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(s => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${s.id}</td>
                <td><strong>${s.nombre}</strong></td>
                <td>${s.rif || '-'}</td>
                <td>${s.telefono || '-'}</td>
                <td>${s.email || '-'}</td>
                <td>${statusBadge(s.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${s.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${s.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado(${s.id})" title="${s.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${s.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-truck"></i><p>No hay proveedores registrados</p></div></td></tr>';
        }
    });
}

function openModal(id = null) {
    Validator.clearForm('supplierForm');
    document.getElementById('supplierId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Editar Proveedor' : 'Nuevo Proveedor';
    new bootstrap.Modal(document.getElementById('supplierModal')).show();
}

function editData(id) {
    apiCall(`/api/suppliers/${id}`).then(res => {
        const s = res.data;
        document.getElementById('supplierId').value = s.id;
        document.getElementById('nombre').value = s.nombre;
        document.getElementById('rif').value = s.rif || '';
        document.getElementById('telefono').value = s.telefono || '';
        document.getElementById('email').value = s.email || '';
        document.getElementById('direccion').value = s.direccion || '';
        document.getElementById('modalTitle').textContent = 'Editar Proveedor';
        new bootstrap.Modal(document.getElementById('supplierModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('supplierForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('supplierId').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        rif: document.getElementById('rif').value,
        telefono: document.getElementById('telefono').value,
        email: document.getElementById('email').value,
        direccion: document.getElementById('direccion').value
    };
    const url = id ? `/api/suppliers/${id}` : '/api/suppliers/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('supplierForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('supplierModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Cambiar estado de este proveedor?', () => {
        apiCall(`/api/suppliers/${id}/toggle`, 'PUT').then(res => { showToast(res.message); loadData(); });
    });
}
