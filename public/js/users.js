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
        nombre: { required: true, minLength: 2, maxLength: 30, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El nombre es obligatorio', patternMsg: 'El nombre solo puede contener letras', maxLengthMsg: 'El nombre no puede superar los 30 caracteres.' },
        apellido: { required: true, minLength: 2, maxLength: 30, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El apellido es obligatorio', patternMsg: 'El apellido solo puede contener letras', maxLengthMsg: 'El apellido no puede superar los 30 caracteres.' },
        cedula_prefijo: { required: true, custom: v => ['V', 'E', 'J', 'G', 'P'].includes(v), customMsg: 'El valor seleccionado no es válido. Recargue la página e inténtelo nuevamente.' },
        cedula: { required: true, pattern: /^\d{7,8}$/, maxLength: 8, requiredMsg: 'La cédula es obligatoria.', patternMsg: 'La cédula debe tener 7 u 8 dígitos.', maxLengthMsg: 'La cédula no puede superar los 8 caracteres.' },
        email: { required: true, email: true, maxLength: 50, requiredMsg: 'El correo es obligatorio', maxLengthMsg: 'El correo no puede superar los 50 caracteres.' },
        telefono: { pattern: /^$|^04\d{9}$/, maxLength: 11, patternMsg: 'Debe tener 11 dígitos y comenzar por 04', maxLengthMsg: 'El teléfono no puede superar los 11 caracteres.' },
        direccion: { maxLength: 40, maxLengthMsg: 'La dirección no puede superar los 40 caracteres.' },
        tipo: { required: true, custom: v => ['cliente', 'empleado'].includes(v), customMsg: 'El valor seleccionado no es válido. Recargue la página e inténtelo nuevamente' },
        rol_id: { required: true, requiredMsg: 'El rol es obligatorio' }
    });
    setPasswordRules(true);
    Validator.setupRealtime('userForm');
    document.getElementById('cedula')?.addEventListener('input', () => validateUniqueUser('cedula'));
    document.getElementById('cedula_prefijo')?.addEventListener('change', () => validateUniqueUser('cedula'));
    document.getElementById('email')?.addEventListener('input', () => validateUniqueUser('email'));
    $('#tipo').on('change', filterRolesByTipo);
});


function setPasswordRules(creating) {
    if (creating) {
        Validator.rules.userForm.password = { required: true, pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$/, requiredMsg: 'La contraseña es obligatoria', patternMsg: 'Mínimo 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial (@$!%*?&#.)' };
        Validator.rules.userForm.confirm_password = { required: true, match: 'password', requiredMsg: 'Confirme la contraseña', matchMsg: 'Las contraseñas no coinciden' };
    } else {
        delete Validator.rules.userForm.password;
        delete Validator.rules.userForm.confirm_password;
    }
}

let paginator = null;

function loadData() {
    const tipo = document.getElementById('filterTipo')?.value || '';
    const url = tipo ? `/api/users/?tipo=${tipo}` : '/api/users/';
    apiCall(url).then(res => {
        if (!paginator) {
            paginator = new TablePaginator('userBody', {
                allData: res.data || [],
                itemName: 'usuarios',
                renderRow: (u) => {
                    const tipoBadge = u.tipo === 'empleado' ? '<span class="badge-status badge-info">Empleado</span>' : '<span class="badge-status badge-pending">Cliente</span>';
                    return `<tr class="fade-in-up">
                        <td class="col-id">${u.id}</td>
                        <td><strong>${escapeHtml(`${u.nombre || ''} ${u.apellido || ''}`.trim())}</strong></td>
                        <td>${escapeHtml(u.cedula || '-')}</td>
                        <td>${escapeHtml(u.email || '-')}</td>
                        <td>${tipoBadge}</td>
                        <td>${escapeHtml(u.roles || '-')}</td>
                        <td>
                            <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${u.id})" title="Modificar Usuario"><i class="bi bi-pencil"></i></button>
                            <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado(${u.id})" title="Eliminar Usuario"><i class="bi bi-trash"></i></button>
                        </td>
                    </tr>`;
                },
                onEmpty: () => '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-people"></i><p>No hay usuarios registrados</p></div></td></tr>'
            });
        } else {
            paginator.updateData(res.data || []);
        }
    });
}

let allRoles = [];

async function loadRoles() {
    try {
        const res = await apiCall('/api/roles/');
        allRoles = (res.data || []).filter(r => Number(r.estado) === 1);
        filterRolesByTipo();
    } catch(e) {}
}

function filterRolesByTipo() {
    const sel = document.getElementById('rol_id');
    const tipo = document.getElementById('tipo')?.value;
    if (!sel || !allRoles.length) return;
    
    const currentVal = $(sel).val();
    sel.innerHTML = '<option value="">Seleccione un rol...</option>';
    
    let filtered = [];
    if (tipo === 'cliente') {
        filtered = allRoles.filter(r => r.nombre.toLowerCase() === 'cliente');
    } else {
        filtered = allRoles.filter(r => r.nombre.toLowerCase() !== 'cliente');
    }
    
    filtered.forEach(r => {
        sel.innerHTML += `<option value="${r.id}">${escapeHtml(r.nombre)}</option>`;
    });
    
    if (currentVal && filtered.some(r => r.id.toString() === currentVal.toString())) {
        $(sel).val(currentVal).trigger('change.select2');
    } else if (filtered.length > 0) {
        $(sel).val(filtered[0].id).trigger('change.select2');
    } else {
        $(sel).val('').trigger('change.select2');
    }
}

function openModal(id = null) {
    Validator.clearForm('userForm');
    document.getElementById('userId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Modificar Usuario' : 'Registrar Usuario';
    setDocumentFields('cedula_prefijo', 'cedula', '', 'V');
    document.getElementById('passwordRow').style.display = id ? 'none' : '';
    setPasswordRules(!id);
    new bootstrap.Modal(document.getElementById('userModal')).show();
    Validator.initTracking('userForm');
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
        $('#cedula_prefijo').trigger('change');
        document.getElementById('email').value = u.email || '';
        document.getElementById('telefono').value = u.telefono || '';
        document.getElementById('direccion').value = u.direccion || '';
        $('#tipo').val(u.tipo || 'empleado').trigger('change');
        if (u.roles?.length) {
            $('#rol_id').val(u.roles[0].id).trigger('change');
        } else {
            $('#rol_id').val('').trigger('change');
        }
        document.getElementById('passwordRow').style.display = 'none';
        setPasswordRules(false);
        document.getElementById('modalTitle').textContent = 'Modificar Usuario';
        new bootstrap.Modal(document.getElementById('userModal')).show();
        Validator.initTracking('userForm');
    });
}

function saveData() {
    const id = document.getElementById('userId').value;
    setPasswordRules(!id);
    if (!Validator.validate('userForm')) return showToast('Corrija los errores', 'warning');
    const data = {
        nombre: document.getElementById('nombre').value,
        apellido: document.getElementById('apellido').value,
        cedula_prefijo: document.getElementById('cedula_prefijo').value,
        cedula: buildDocumentValue('cedula_prefijo', 'cedula'),
        email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value,
        direccion: document.getElementById('direccion').value,
        tipo: document.getElementById('tipo').value,
        rol_id: document.getElementById('rol_id').value || null
    };
    if (!id) {
        data.password = document.getElementById('password').value;
        data.confirm_password = document.getElementById('confirm_password').value;
    }
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
    confirmAction('¿Estás seguro de que deseas eliminar este usuario?', () => {
        apiCall(`/api/users/${id}/status`, 'PUT', { estado: 0 }).then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadData();
        });
    });
}

function validateUniqueUser(field) {
    clearTimeout(userUniqueTimers[field]);
    userUniqueTimers[field] = setTimeout(async () => {
        const input = document.getElementById(field);
        const id = document.getElementById('userId')?.value || '';
        const value = (input?.value || '').trim();
        if (!input) return;
        if (!value) {
            delete input.dataset.externalError;
            clearFieldError(input);
            updateFormSubmitState('userForm');
            return;
        }
        if (!Validator.validateField('userForm', field)) {
            delete input.dataset.externalError;
            updateFormSubmitState('userForm');
            return;
        }
        const cedulaValue = buildDocumentValue('cedula_prefijo', 'cedula');
        const queryValue = field === 'cedula' ? cedulaValue : value;
        const res = await apiCall('/api/users/check-unique', 'POST', {
            field,
            value: queryValue,
            exclude: id,
            cedula: cedulaValue
        });
        if (res.status === 'success' && res.exists) {
            const errorMsg = field === 'email' ? 'Este correo ya está registrado.' : 'Esta cédula ya está registrada.';
            input.dataset.externalError = errorMsg;
            setFieldError(input, errorMsg);
        } else if (res.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('userForm');
    }, 350);
}
