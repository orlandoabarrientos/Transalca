let userUniqueTimers = {};

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="users"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadRoles();
    updatePasswordStrength('password', 'passwordStrengthBar');
    Validator.setRules('userForm', {
        nombre: { required: true, minLength: 2, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El nombre es obligatorio', patternMsg: 'El nombre solo puede contener letras' },
        apellido: { required: true, minLength: 2, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El apellido es obligatorio', patternMsg: 'El apellido solo puede contener letras' },
        cedula_prefijo: { required: true, custom: v => ['V', 'E', 'J', 'G', 'P'].includes(v), customMsg: 'El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente.' },
        cedula: { required: true, pattern: /^\d{7,8}$/, requiredMsg: 'La cedula es obligatoria.', patternMsg: 'La cedula debe tener 7 u 8 digitos.' },
        email: { required: true, email: true, requiredMsg: 'El correo es obligatorio' },
        telefono: { pattern: /^$|^04\d{9}$/, patternMsg: 'Debe tener 11 digitos y comenzar por 04' },
        tipo: { required: true, custom: v => ['cliente', 'empleado'].includes(v), customMsg: 'El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente' }
    });
    Validator.setupRealtime('userForm');
    document.getElementById('cedula')?.addEventListener('input', () => validateUniqueUser('cedula'));
    document.getElementById('cedula_prefijo')?.addEventListener('change', () => validateUniqueUser('cedula'));
    document.getElementById('email')?.addEventListener('input', () => validateUniqueUser('email'));
});

function loadData() {
    const tipo = document.getElementById('filterTipo')?.value || '';
    const url = tipo ? `/api/users/?tipo=${tipo}` : '/api/users/';
    apiCall(url).then(res => {
        const tbody = document.getElementById('userBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(u => {
            const tipoBadge = u.tipo === 'empleado' ? '<span class="badge-status badge-info">Empleado</span>' : '<span class="badge-status badge-pending">Cliente</span>';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${u.id}</td>
                <td><strong>${escapeHtml(`${u.nombre || ''} ${u.apellido || ''}`.trim())}</strong></td>
                <td>${escapeHtml(u.cedula || '-')}</td>
                <td>${escapeHtml(u.email || '-')}</td>
                <td>${tipoBadge}</td>
                <td>${escapeHtml(u.roles || '-')}</td>
                <td>${statusBadge(u.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${u.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado(${u.id})" title="Eliminar"><i class="bi bi-trash"></i></button>
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
            (res.data || []).filter(r => Number(r.estado) === 1).forEach(r => sel.innerHTML += `<option value="${r.id}">${escapeHtml(r.nombre)}</option>`);
        }
    } catch(e) {}
}

function openModal(id = null) {
    Validator.clearForm('userForm');
    document.getElementById('userId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Editar Usuario' : 'Nuevo Usuario';
    setDocumentFields('cedula_prefijo', 'cedula', '', 'V');
    document.getElementById('passwordRow').style.display = id ? 'none' : '';
    new bootstrap.Modal(document.getElementById('userModal')).show();
}

function editData(id) {
    apiCall(`/api/users/${id}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const u = res.data || {};
        Validator.clearForm('userForm');
        document.getElementById('userId').value = u.id;
        document.getElementById('nombre').value = u.nombre || '';
        document.getElementById('apellido').value = u.apellido || '';
        setDocumentFields('cedula_prefijo', 'cedula', u.cedula || '', 'V');
        document.getElementById('email').value = u.email || '';
        document.getElementById('telefono').value = u.telefono || '';
        document.getElementById('direccion').value = u.direccion || '';
        document.getElementById('tipo').value = u.tipo || 'empleado';
        if (u.roles?.length) document.getElementById('rol_id').value = u.roles[0].id;
        document.getElementById('passwordRow').style.display = 'none';
        document.getElementById('modalTitle').textContent = 'Editar Usuario';
        new bootstrap.Modal(document.getElementById('userModal')).show();
    });
}

function saveData() {
    const id = document.getElementById('userId').value;
    if (!id) {
        Validator.rules.userForm.password = { required: true, pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$/, requiredMsg: 'La contrasena es obligatoria', patternMsg: 'Minimo 8 caracteres, una mayuscula, una minuscula, un numero y un especial' };
    } else {
        delete Validator.rules.userForm.password;
    }
    if (!Validator.validate('userForm')) return showToast('Corrija los errores', 'warning');
    const data = {
        nombre: document.getElementById('nombre').value,
        apellido: document.getElementById('apellido').value,
        cedula_prefijo: document.getElementById('cedula_prefijo').value,
        cedula_numero: document.getElementById('cedula').value,
        cedula: buildDocumentValue('cedula_prefijo', 'cedula'),
        email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value,
        direccion: document.getElementById('direccion').value,
        tipo: document.getElementById('tipo').value,
        rol_id: document.getElementById('rol_id').value || null
    };
    if (!id) data.password = document.getElementById('password').value;
    const url = id ? `/api/users/${id}` : '/api/users/';
    const method = id ? 'PUT' : 'POST';
    const saveBtn = document.querySelector('#userModal .btn-orange');
    setButtonLoading(saveBtn, true, 'Guardando...');
    apiCall(url, method, data).then(res => {
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') {
            Validator.showServerErrors('userForm', res.errors);
            return showToast(res.message, 'error');
        }
        bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(id) {
    confirmAction('Eliminar este usuario?', () => {
        apiCall(`/api/users/${id}/status`, 'PUT', { estado: 0 }).then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadData();
        });
    }, { confirmText: 'Eliminar' });
}

function validateUniqueUser(field) {
    clearTimeout(userUniqueTimers[field]);
    userUniqueTimers[field] = setTimeout(async () => {
        const input = document.getElementById(field);
        const id = document.getElementById('userId')?.value || '';
        const value = (input?.value || '').trim();
        if (!input) return;
        if (!value) {
            clearFieldError(input);
            updateFormSubmitState('userForm');
            return;
        }
        if (!Validator.validateField('userForm', field)) {
            updateFormSubmitState('userForm');
            return;
        }
        const cedulaValue = buildDocumentValue('cedula_prefijo', 'cedula');
        const queryValue = field === 'cedula' ? cedulaValue : value;
        const res = await apiCall(`/api/users/check-unique?field=${field}&value=${encodeURIComponent(queryValue)}&exclude=${encodeURIComponent(id)}&cedula=${encodeURIComponent(cedulaValue)}`);
        if (res.status === 'success' && res.exists) {
            setFieldError(input, field === 'email' ? 'Este correo ya esta registrado.' : 'Esta cedula ya esta registrada.');
        } else if (res.status === 'success') {
            clearFieldError(input);
        }
        updateFormSubmitState('userForm');
    }, 350);
}
