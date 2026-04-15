$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="categories"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('categoryForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'Nombre requerido', minLengthMsg: 'Minimo 3 caracteres' }
    });
    Validator.setupRealtime('categoryForm');
});

function loadData() {
    apiCall('/api/categories/').then(res => {
        const tbody = document.getElementById('categoryBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(c => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><strong>${c.nombre}</strong></td>
                <td>${c.descripcion || '-'}</td>
                <td>${c.total_productos || 0}</td>
                <td>${statusBadge(c.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${escape(c.nombre)}')" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${c.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado('${escape(c.nombre)}')" title="${c.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${c.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-tags"></i><p>No hay categorias registradas</p></div></td></tr>';
        }
    });
}

function openModal(nombre = null) {
    Validator.clearForm('categoryForm');
    document.getElementById('categoryOldNombre').value = nombre ? unescape(nombre) : '';
    document.getElementById('modalTitle').textContent = nombre ? 'Editar Categoria' : 'Nueva Categoria';
    new bootstrap.Modal(document.getElementById('categoryModal')).show();
}

function editData(nombre) {
    nombre = unescape(nombre);
    apiCall(`/api/categories/${encodeURIComponent(nombre)}`).then(res => {
        const c = res.data;
        document.getElementById('categoryOldNombre').value = c.nombre;
        document.getElementById('nombre').value = c.nombre;
        document.getElementById('descripcion').value = c.descripcion || '';
        document.getElementById('modalTitle').textContent = 'Editar Categoria';
        new bootstrap.Modal(document.getElementById('categoryModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('categoryForm')) return showToast('Corrija los errores','warning');
    const oldNombre = document.getElementById('categoryOldNombre').value;
    const data = { nombre: document.getElementById('nombre').value, descripcion: document.getElementById('descripcion').value };
    if (oldNombre) {
        data.old_nombre = oldNombre;
        apiCall('/api/categories/update', 'PUT', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('categoryForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
            showToast(res.message); loadData();
        });
    } else {
        apiCall('/api/categories/', 'POST', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('categoryForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
            showToast(res.message); loadData();
        });
    }
}

function toggleEstado(nombre) {
    nombre = unescape(nombre);
    confirmAction('¿Cambiar estado de esta categoria?', () => {
        apiCall('/api/categories/toggle', 'PUT', { nombre }).then(res => { showToast(res.message); loadData(); });
    });
}
