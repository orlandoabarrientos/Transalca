$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="users"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadRoles();
    updatePasswordStrength('password', 'passwordStrengthBar');
    Validator.setRules('userForm', {
        nombre: { required: true, minLength: 2, requiredMsg: 'Nombre requerido' },
        apellido: { required: true, minLength: 2, requiredMsg: 'Apellido requerido' },
        cedula: { required: true, minLength: 5, requiredMsg: 'Cedula requerida' },
        email: { required: true, email: true, requiredMsg: 'Email requerido' }
    });
    Validator.setupRealtime('userForm');
});

function loadData() {
    const tipo = document.getElementById('filterTipo')?.value || '';
    const url = tipo ? `/api/users/?tipo=${tipo}` : '/api/users/';
    apiCall(url).then(res => {
        const tbody = document.getElementById('userBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(u => {
            const tipoBadge = u.tipo === 'empleado' ? '<span class="badge-status badge-info">Empleado</span>' : '<span class="badge-status badge-pending">Cliente</span>';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${u.id}</td>
                <td><strong>${u.nombre} ${u.apellido}</strong></td>
                <td>${u.cedula || '-'}</td>
                <td>${u.email}</td>
                <td>${tipoBadge}</td>
                <td>${u.roles || '-'}</td>
                <td>${statusBadge(u.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${u.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${u.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado(${u.id}, ${u.estado})" title="${u.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${u.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-people"></i><p>No hay usuarios</p></div></td></tr>';
    });
}

async function loadRoles() {
    try {
        const res = await apiCall('/api/roles/');
        const sel = document.getElementById('rol_id');
        if (sel) {
            sel.innerHTML = '<option value="">Sin rol</option>';
            (res.data||[]).forEach(r => sel.innerHTML += `<option value="${r.id}">${r.nombre}</option>`);
        }
    } catch(e) {}
}

function openModal(id = null) {
    Validator.clearForm('userForm');
    document.getElementById('userId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Editar Usuario' : 'Nuevo Usuario';
    document.getElementById('passwordRow').style.display = id ? 'none' : '';
    new bootstrap.Modal(document.getElementById('userModal')).show();
}

function editData(id) {
    apiCall(`/api/users/${id}`).then(res => {
        const u = res.data;
        document.getElementById('userId').value = u.id;
        document.getElementById('nombre').value = u.nombre;
        document.getElementById('apellido').value = u.apellido;
        document.getElementById('cedula').value = u.cedula || '';
        document.getElementById('email').value = u.email;
        document.getElementById('telefono').value = u.telefono || '';
        document.getElementById('direccion').value = u.direccion || '';
        document.getElementById('tipo').value = u.tipo;
        if (u.roles?.length) document.getElementById('rol_id').value = u.roles[0].id;
        document.getElementById('passwordRow').style.display = 'none';
        document.getElementById('modalTitle').textContent = 'Editar Usuario';
        new bootstrap.Modal(document.getElementById('userModal')).show();
    });
}

function saveData() {
    const id = document.getElementById('userId').value;
    if (!id) {
        const passRules = Validator.rules['userForm'];
        passRules.password = { required: true, pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$/, requiredMsg: 'Contrasena requerida', patternMsg: 'Min 8, 1 may, 1 min, 1 num, 1 especial' };
    } else {
        delete Validator.rules['userForm']?.password;
    }
    if (!Validator.validate('userForm')) return showToast('Corrija los errores','warning');
    const data = {
        nombre: document.getElementById('nombre').value, apellido: document.getElementById('apellido').value,
        cedula: document.getElementById('cedula').value, email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value, direccion: document.getElementById('direccion').value,
        tipo: document.getElementById('tipo').value, rol_id: document.getElementById('rol_id').value || null
    };
    if (!id) data.password = document.getElementById('password').value;
    const url = id ? `/api/users/${id}` : '/api/users/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('userForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
        showToast(res.message); loadData();
    });
}

function toggleEstado(id, estado) {
    confirmAction(estado ? '¿Desactivar usuario?' : '¿Activar usuario?', () => {
        apiCall(`/api/users/${id}/status`, 'PUT', { estado: estado ? 0 : 1 }).then(res => { showToast(res.message); loadData(); });
    });
}
