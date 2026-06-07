let mechanicCedulaTimer = null;

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="mechanics"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('mechanicForm', {
        nombre: { required: true, minLength: 2, maxLength: 30, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El nombre es obligatorio', patternMsg: 'El nombre solo puede contener letras', maxLengthMsg: 'El nombre no puede superar los 30 caracteres.' },
        apellido: { required: true, minLength: 2, maxLength: 30, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El apellido es obligatorio', patternMsg: 'El apellido solo puede contener letras', maxLengthMsg: 'El apellido no puede superar los 30 caracteres.' },
        cedula_prefijo: { required: true, custom: v => ['V', 'E', 'J', 'G', 'P'].includes(v), customMsg: 'El valor seleccionado no es válido. Recargue la página e inténtelo nuevamente.' },
        cedula: { required: true, pattern: /^\d{7,8}$/, maxLength: 8, requiredMsg: 'La cédula es obligatoria.', patternMsg: 'La cédula debe tener 7 u 8 dígitos.', maxLengthMsg: 'La cédula no puede superar los 8 caracteres.' },
        telefono: { pattern: /^$|^04\d{9}$/, maxLength: 11, patternMsg: 'Debe tener 11 dígitos y comenzar por 04', maxLengthMsg: 'El teléfono no puede superar los 11 caracteres.' },
        especialidad: { maxLength: 50, maxLengthMsg: 'La especialidad no puede superar los 50 caracteres.' }
    });
    Validator.setupRealtime('mechanicForm');
    document.getElementById('cedula')?.addEventListener('input', validateUniqueMechanicCedula);
    document.getElementById('cedula_prefijo')?.addEventListener('change', validateUniqueMechanicCedula);
});

let paginator = null;

function loadData() {
    apiCall('/api/mechanics/').then(res => {
        if (!paginator) {
            paginator = new TablePaginator('mechanicBody', {
                allData: res.data || [],
                itemName: 'mecánicos',
                renderRow: (m) => {
                    const actionBtn = m.total_servicios > 0 
                        ? `<button class="btn btn-icon btn-sm btn-outline-danger" onclick="deleteData('${encodeURIComponent(m.cedula)}', true)" title="Desactivar Mecánico"><i class="bi bi-slash-circle"></i></button>`
                        : `<button class="btn btn-icon btn-sm btn-warning" onclick="deleteData('${encodeURIComponent(m.cedula)}', false)" title="Eliminar Mecánico"><i class="bi bi-trash"></i></button>`;
                    return `<tr class="fade-in-up">
                        <td>
                            <div class="d-flex align-items-center gap-4 py-2">
                                <img src="/public/assets/profile_pics/${escapeHtml(m.foto_perfil || 'default.png')}" style="width: 96px; height: 120px;" class="rounded shadow-sm object-fit-cover border">
                                <div>
                                    <h6 class="mb-0 fw-bold">${escapeHtml(`${m.nombre || ''} ${m.apellido || ''}`.trim())}</h6>
                                    <small class="text-muted"><i class="bi bi-person-badge me-1"></i>${escapeHtml(m.cedula || '-')}</small>
                                </div>
                            </div>
                        </td>
                        <td>${escapeHtml(m.especialidad || '-')}</td>
                        <td>${escapeHtml(m.telefono || '-')}</td>
                        <td>${statusBadge(m.estado)}</td>
                        <td>
                            <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${encodeURIComponent(m.cedula)}')" title="Modificar Mecánico"><i class="bi bi-pencil"></i></button>
                            ${actionBtn}
                        </td>
                    </tr>`;
                },
                onEmpty: () => '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-person-badge"></i><p>No hay mecánicos registrados</p></div></td></tr>'
            });
        } else {
            paginator.updateData(res.data || []);
        }
    });
}

function openModal(cedula = null) {
    Validator.clearForm('mechanicForm');
    document.getElementById('mechanicOldCedula').value = cedula ? decodeURIComponent(cedula) : '';
    setDocumentFields('cedula_prefijo', 'cedula', cedula ? decodeURIComponent(cedula) : '', 'V');
    document.getElementById('modalTitle').textContent = cedula ? 'Modificar Mecánico' : 'Registrar Mecánico';
    new bootstrap.Modal(document.getElementById('mechanicModal')).show();
    Validator.initTracking('mechanicForm');
}

function editData(cedula) {
    cedula = decodeURIComponent(cedula);
    apiCall(`/api/mechanics/${encodeURIComponent(cedula)}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const m = res.data || {};
        Validator.clearForm('mechanicForm');
        document.getElementById('mechanicOldCedula').value = m.cedula || '';
        document.getElementById('nombre').value = m.nombre || '';
        document.getElementById('apellido').value = m.apellido || '';
        setDocumentFields('cedula_prefijo', 'cedula', m.cedula || '', 'V');
        document.getElementById('telefono').value = m.telefono || '';
        document.getElementById('especialidad').value = m.especialidad || '';
        document.getElementById('modalTitle').textContent = 'Modificar Mecánico';
        new bootstrap.Modal(document.getElementById('mechanicModal')).show();
        Validator.initTracking('mechanicForm');
    });
}

function saveData() {
    if (!Validator.validate('mechanicForm')) return showToast('Corrija los errores', 'warning');
    const oldCedula = document.getElementById('mechanicOldCedula').value;
    const saveBtn = document.querySelector('#mechanicModal .btn-orange');
    const formData = new FormData();
    formData.append('nombre', document.getElementById('nombre').value);
    formData.append('apellido', document.getElementById('apellido').value);
    formData.append('cedula_prefijo', document.getElementById('cedula_prefijo').value);
    formData.append('cedula', buildDocumentValue('cedula_prefijo', 'cedula'));
    formData.append('telefono', document.getElementById('telefono').value);
    formData.append('especialidad', document.getElementById('especialidad').value);
    const fileInput = document.getElementById('foto_perfil');
    if (fileInput && fileInput.files.length > 0) {
        formData.append('foto_perfil', fileInput.files[0]);
    }
    const url = oldCedula ? '/api/mechanics/update' : '/api/mechanics/';
    const method = oldCedula ? 'PUT' : 'POST';
    if (oldCedula) formData.append('old_cedula', oldCedula);
    setButtonLoading(saveBtn, true, 'Guardando...');
    apiCall(url, method, formData).then(res => {
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') {
            Validator.showServerErrors('mechanicForm', res.errors);
            return showToast(res.message, 'error');
        }
        bootstrap.Modal.getInstance(document.getElementById('mechanicModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function deleteData(cedula, deactivateOnly = false) {
    cedula = decodeURIComponent(cedula);
    const msg = deactivateOnly 
        ? '¿Estás seguro de que deseas desactivar este mecánico?' 
        : '¿Estás seguro de que deseas eliminar este mecánico?';
    confirmAction(msg, () => {
        apiCall('/api/mechanics/delete', 'DELETE', { cedula }).then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadData();
        });
    });
}

function validateUniqueMechanicCedula() {
    clearTimeout(mechanicCedulaTimer);
    mechanicCedulaTimer = setTimeout(async () => {
        const input = document.getElementById('cedula');
        const oldCedula = document.getElementById('mechanicOldCedula')?.value || '';
        const value = (input?.value || '').trim();
        if (!input) return;
        if (!value) {
            delete input.dataset.externalError;
            clearFieldError(input);
            updateFormSubmitState('mechanicForm');
            return;
        }
        if (!Validator.validateField('mechanicForm', 'cedula')) {
            delete input.dataset.externalError;
            updateFormSubmitState('mechanicForm');
            return;
        }
        const queryValue = buildDocumentValue('cedula_prefijo', 'cedula');
        const res = await apiCall(`/api/mechanics/check-unique?value=${encodeURIComponent(queryValue)}&exclude=${encodeURIComponent(oldCedula)}`);
        if (res.status === 'success' && res.exists) {
            input.dataset.externalError = 'Esta cédula ya está registrada';
            setFieldError(input, 'Esta cédula ya está registrada');
        } else if (res.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('mechanicForm');
    }, 350);
}

function escapeHtml(text) {
    return String(text ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
