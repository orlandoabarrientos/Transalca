$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="brands"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('brandForm', {
        nombre: { required: true, minLength: 2, requiredMsg: 'Nombre requerido', minLengthMsg: 'Minimo 2 caracteres' }
    });
    Validator.setupRealtime('brandForm');
});

function loadData() {
    apiCall('/api/brands/').then(res => {
        const tbody = document.getElementById('brandBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(b => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${b.id}</td>
                <td><strong>${b.nombre}</strong></td>
                <td>${b.descripcion || '-'}</td>
                <td>${b.total_productos || 0}</td>
                <td>${statusBadge(b.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${b.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${b.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado(${b.id})" title="${b.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${b.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-award"></i><p>No hay marcas registradas</p></div></td></tr>';
        }
    });
}

function openModal(id = null) {
    Validator.clearForm('brandForm');
    document.getElementById('brandId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Editar Marca' : 'Nueva Marca';
    new bootstrap.Modal(document.getElementById('brandModal')).show();
}

function editData(id) {
    apiCall(`/api/brands/${id}`).then(res => {
        const b = res.data;
        document.getElementById('brandId').value = b.id;
        document.getElementById('nombre').value = b.nombre;
        document.getElementById('descripcion').value = b.descripcion || '';
        document.getElementById('modalTitle').textContent = 'Editar Marca';
        new bootstrap.Modal(document.getElementById('brandModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('brandForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('brandId').value;
    const data = { nombre: document.getElementById('nombre').value, descripcion: document.getElementById('descripcion').value };
    const url = id ? `/api/brands/${id}` : '/api/brands/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('brandForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('brandModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Cambiar estado de esta marca?', () => {
        apiCall(`/api/brands/${id}/toggle`, 'PUT').then(res => { showToast(res.message); loadData(); });
    });
}
