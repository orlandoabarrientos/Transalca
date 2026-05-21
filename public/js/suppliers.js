let supplierRifTimer = null;
let supplierEmailTimer = null;

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="suppliers"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('supplierForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'El nombre es obligatorio', minLengthMsg: 'Mínimo 3 caracteres' },
        rif_prefijo: { required: true, custom: v => ['J', 'G', 'V', 'E', 'P'].includes(v), customMsg: 'El valor seleccionado no es válido. Recargue la página e inténtelo nuevamente.' },
        rif: { required: true, pattern: /^\d{9}$/, requiredMsg: 'El RIF es obligatorio.', patternMsg: 'El RIF debe tener 9 dígitos.' },
        email: { email: true },
        telefono: { pattern: /^$|^04\d{9}$/, patternMsg: 'Debe tener 11 dígitos y comenzar por 04' }
    });
    Validator.setupRealtime('supplierForm');
    document.getElementById('rif')?.addEventListener('input', validateUniqueSupplierRif);
    document.getElementById('rif_prefijo')?.addEventListener('change', validateUniqueSupplierRif);
    document.getElementById('email')?.addEventListener('input', validateUniqueSupplierEmail);
});

function loadData() {
    apiCall('/api/suppliers/').then(res => {
        const tbody = document.getElementById('supplierBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(s => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><strong>${escapeHtml(s.nombre)}</strong></td>
                <td>${escapeHtml(s.rif)}</td>
                <td>${escapeHtml(s.telefono || '-')}</td>
                <td>${escapeHtml(s.email || '-')}</td>
                <td>${statusBadge(s.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${encodeURIComponent(s.rif)}')" title="Modificar Proveedor"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado('${encodeURIComponent(s.rif)}')" title="Eliminar Proveedor"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-truck"></i><p>No hay proveedores registrados</p></div></td></tr>';
        }
    });
}

function validateUniqueSupplierEmail() {
    clearTimeout(supplierEmailTimer);
    supplierEmailTimer = setTimeout(async () => {
        const input = document.getElementById('email');
        const oldRif = document.getElementById('supplierOldRif')?.value || buildRifValue('rif_prefijo', 'rif');
        const value = (input?.value || '').trim();
        if (!input) return;
        if (!value) {
            delete input.dataset.externalError;
            clearFieldError(input);
            updateFormSubmitState('supplierForm');
            return;
        }
        if (!Validator.validateField('supplierForm', 'email')) {
            delete input.dataset.externalError;
            updateFormSubmitState('supplierForm');
            return;
        }
        const res = await apiCall(`/api/suppliers/check-unique?field=email&value=${encodeURIComponent(value)}&exclude=${encodeURIComponent(oldRif)}`);
        if (res.status === 'success' && res.exists) {
            input.dataset.externalError = 'Este correo ya está registrado.';
            setFieldError(input, 'Este correo ya está registrado.');
        } else if (res.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('supplierForm');
    }, 350);
}

function openModal(rif = null) {
    Validator.clearForm('supplierForm');
    document.getElementById('supplierOldRif').value = rif ? decodeURIComponent(rif) : '';
    setRifFields('rif_prefijo', 'rif', rif ? decodeURIComponent(rif) : '', 'J');
    document.getElementById('modalTitle').textContent = rif ? 'Modificar Proveedor' : 'Registrar Proveedor';
    new bootstrap.Modal(document.getElementById('supplierModal')).show();
    Validator.initTracking('supplierForm');
}

function editData(rif) {
    rif = decodeURIComponent(rif);
    apiCall(`/api/suppliers/${encodeURIComponent(rif)}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const s = res.data || {};
        Validator.clearForm('supplierForm');
        document.getElementById('supplierOldRif').value = s.rif;
        document.getElementById('nombre').value = s.nombre || '';
        setRifFields('rif_prefijo', 'rif', s.rif || '', 'J');
        document.getElementById('telefono').value = s.telefono || '';
        document.getElementById('email').value = s.email || '';
        document.getElementById('direccion').value = s.direccion || '';
        document.getElementById('modalTitle').textContent = 'Modificar Proveedor';
        new bootstrap.Modal(document.getElementById('supplierModal')).show();
        Validator.initTracking('supplierForm');
    });
}

function saveData() {
    if (!Validator.validate('supplierForm')) return showToast('Corrija los errores', 'warning');
    const oldRif = document.getElementById('supplierOldRif').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        rif_prefijo: document.getElementById('rif_prefijo').value,
        rif_numero: document.getElementById('rif').value,
        rif: buildRifValue('rif_prefijo', 'rif'),
        telefono: document.getElementById('telefono').value,
        email: document.getElementById('email').value,
        direccion: document.getElementById('direccion').value
    };
    const url = oldRif ? '/api/suppliers/update' : '/api/suppliers/';
    const method = oldRif ? 'PUT' : 'POST';
    if (oldRif) data.old_rif = oldRif;
    const saveBtn = document.querySelector('#supplierModal .btn-orange');
    setButtonLoading(saveBtn, true, 'Guardando...');
    apiCall(url, method, data).then(res => {
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') {
            Validator.showServerErrors('supplierForm', res.errors);
            return showToast(res.message, 'error');
        }
        bootstrap.Modal.getInstance(document.getElementById('supplierModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(rif) {
    rif = decodeURIComponent(rif);
    confirmAction('¿Estás seguro de que deseas eliminar este proveedor?', () => {
        apiCall('/api/suppliers/toggle', 'PUT', { rif }).then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadData();
        });
    });
}

function validateUniqueSupplierRif() {
    clearTimeout(supplierRifTimer);
    supplierRifTimer = setTimeout(async () => {
        const input = document.getElementById('rif');
        const oldRif = document.getElementById('supplierOldRif')?.value || '';
        const value = (input?.value || '').trim();
        if (!input) return;
        if (!value) {
            delete input.dataset.externalError;
            clearFieldError(input);
            updateFormSubmitState('supplierForm');
            return;
        }
        if (!Validator.validateField('supplierForm', 'rif')) {
            delete input.dataset.externalError;
            updateFormSubmitState('supplierForm');
            return;
        }
        const queryValue = buildRifValue('rif_prefijo', 'rif');
        const res = await apiCall(`/api/suppliers/check-unique?value=${encodeURIComponent(queryValue)}&exclude=${encodeURIComponent(oldRif)}`);
        if (res.status === 'success' && res.exists) {
            input.dataset.externalError = 'Este RIF ya está registrado.';
            setFieldError(input, 'Este RIF ya está registrado.');
        } else if (res.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('supplierForm');
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
