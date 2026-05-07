let mechanicCedulaTimer = null;

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="mechanics"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('mechanicForm', {
        nombre: { required: true, minLength: 2, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El nombre es obligatorio', patternMsg: 'El nombre solo puede contener letras' },
        apellido: { required: true, minLength: 2, pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/, requiredMsg: 'El apellido es obligatorio', patternMsg: 'El apellido solo puede contener letras' },
        cedula_prefijo: { required: true, custom: v => ['V', 'E', 'J', 'G', 'P'].includes(v), customMsg: 'El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente.' },
        cedula: { required: true, pattern: /^\d{7,8}$/, requiredMsg: 'La cedula es obligatoria.', patternMsg: 'La cedula debe tener 7 u 8 digitos.' },
        telefono: { pattern: /^$|^04\d{9}$/, patternMsg: 'Debe tener 11 digitos y comenzar por 04' }
    });
    Validator.setupRealtime('mechanicForm');
    document.getElementById('cedula')?.addEventListener('input', validateUniqueMechanicCedula);
    document.getElementById('cedula_prefijo')?.addEventListener('change', validateUniqueMechanicCedula);
});

function loadData() {
    apiCall('/api/mechanics/').then(res => {
        const tbody = document.getElementById('mechanicBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(m => {
            tbody.innerHTML += `<tr class="fade-in-up">
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
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${encodeURIComponent(m.cedula)}')" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${m.estado ? 'btn-warning' : 'btn-success'}" onclick="deleteData('${encodeURIComponent(m.cedula)}')" title="${m.estado ? 'Eliminar' : 'Reactivar'}"><i class="bi bi-${m.estado ? 'trash' : 'arrow-clockwise'}"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-person-badge"></i><p>No hay mecanicos registrados</p></div></td></tr>';
    });
}

async function openModal(cedula = null) {
    Validator.clearForm('mechanicForm');
    document.getElementById('mechanicOldCedula').value = cedula ? decodeURIComponent(cedula) : '';
    setDocumentFields('cedula_prefijo', 'cedula', cedula ? decodeURIComponent(cedula) : '', 'V');
    document.getElementById('modalTitle').textContent = cedula ? 'Editar Mecanico' : 'Nuevo Mecanico';
    new bootstrap.Modal(document.getElementById('mechanicModal')).show();
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
        document.getElementById('modalTitle').textContent = 'Editar Mecanico';
        new bootstrap.Modal(document.getElementById('mechanicModal')).show();
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
    formData.append('cedula_numero', document.getElementById('cedula').value);
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

function deleteData(cedula) {
    cedula = decodeURIComponent(cedula);
    confirmAction('Cambiar estado de este mecanico?', () => {
        apiCall('/api/mechanics/delete', 'DELETE', { cedula }).then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadData();
        });
    }, { confirmText: 'Aceptar' });
}

function validateUniqueMechanicCedula() {
    clearTimeout(mechanicCedulaTimer);
    mechanicCedulaTimer = setTimeout(async () => {
        const input = document.getElementById('cedula');
        const oldCedula = document.getElementById('mechanicOldCedula')?.value || '';
        const value = (input?.value || '').trim();
        if (!value || !Validator.validateField('mechanicForm', 'cedula')) return;
        const queryValue = buildDocumentValue('cedula_prefijo', 'cedula');
        const res = await apiCall(`/api/mechanics/check-unique?value=${encodeURIComponent(queryValue)}&exclude=${encodeURIComponent(oldCedula)}`);
        if (res.status === 'success' && res.exists) {
            input.classList.add('is-invalid');
            const feedback = input.parentNode.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.textContent = 'Esta cedula ya esta registrada.';
                feedback.style.display = 'block';
            }
            updateFormSubmitState('mechanicForm');
        }
    }, 350);
}
