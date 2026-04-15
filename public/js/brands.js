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
                <td><strong>${b.nombre}</strong></td>
                <td>${b.descripcion || '-'}</td>
                <td>${b.total_productos || 0}</td>
                <td>${statusBadge(b.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${escape(b.nombre)}')" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${b.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado('${escape(b.nombre)}')" title="${b.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${b.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-award"></i><p>No hay marcas registradas</p></div></td></tr>';
        }
    });
}

function openModal(nombre = null) {
    Validator.clearForm('brandForm');
    document.getElementById('brandOldNombre').value = nombre ? unescape(nombre) : '';
    document.getElementById('modalTitle').textContent = nombre ? 'Editar Marca' : 'Nueva Marca';
    new bootstrap.Modal(document.getElementById('brandModal')).show();
}

function editData(nombre) {
    nombre = unescape(nombre);
    apiCall(`/api/brands/${encodeURIComponent(nombre)}`).then(res => {
        const b = res.data;
        document.getElementById('brandOldNombre').value = b.nombre;
        document.getElementById('nombre').value = b.nombre;
        document.getElementById('descripcion').value = b.descripcion || '';
        document.getElementById('modalTitle').textContent = 'Editar Marca';
        new bootstrap.Modal(document.getElementById('brandModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('brandForm')) return showToast('Corrija los errores','warning');
    const oldNombre = document.getElementById('brandOldNombre').value;
    const data = { nombre: document.getElementById('nombre').value, descripcion: document.getElementById('descripcion').value };
    if (oldNombre) {
        data.old_nombre = oldNombre;
        apiCall('/api/brands/update', 'PUT', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('brandForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('brandModal')).hide();
            showToast(res.message); loadData();
        });
    } else {
        apiCall('/api/brands/', 'POST', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('brandForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('brandModal')).hide();
            showToast(res.message); loadData();
        });
    }
}

function toggleEstado(nombre) {
    nombre = unescape(nombre);
    confirmAction('¿Cambiar estado de esta marca?', () => {
        apiCall('/api/brands/toggle', 'PUT', { nombre }).then(res => { showToast(res.message); loadData(); });
    });
}
