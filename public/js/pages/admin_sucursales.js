function debounce(fn, ms) {
    let t;
    return function (...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), ms);
    };
}

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="sucursales"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('sucursalForm', {
        nombre: { required: true, minLength: 3, maxLength: 30, requiredMsg: 'El nombre es requerido', minLengthMsg: 'Mínimo 3 caracteres', maxLengthMsg: 'El nombre no puede superar los 30 caracteres.' },
        telefono: { pattern: /^$|^04\d{9}$/, maxLength: 11, patternMsg: 'Debe tener 11 dígitos y comenzar por 04', maxLengthMsg: 'El teléfono no puede superar los 11 caracteres.' },
        email: { email: true, maxLength: 50, maxLengthMsg: 'El correo no puede superar los 50 caracteres.' },
        direccion: {
            maxLength: 40,
            maxLengthMsg: 'La dirección no puede superar los 40 caracteres.',
            pattern: /^$|^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s.,-]+$/,
            patternMsg: 'La dirección solo puede contener letras, números, espacios, puntos, comas y guiones.',
            custom: () => {
                const el = document.getElementById('direccion');
                return !el || !el.value || el.value.trim().length > 0;
            },
            customMsg: 'La dirección no puede contener solo espacios en blanco.'
        }
    });
    Validator.setupRealtime('sucursalForm');
    document.getElementById('nombre')?.addEventListener('input', debounce(validateUniqueSucursalNombre, 350));
    document.getElementById('email')?.addEventListener('input', debounce(validateUniqueSucursalEmail, 350));
});

let paginator = null;

function loadData() {
    apiCall('/api/sucursales/').then(res => {
        if (!paginator) {
            paginator = new TablePaginator('sucursalBody', {
                allData: res.data || [],
                itemName: 'sucursales',
                renderRow: (s) => `<tr class="fade-in-up">
                    <td class="col-id">${s.id}</td>
                    <td><strong>${escapeHtml(s.nombre)}</strong></td>
                    <td>${escapeHtml(s.direccion || '-')}</td>
                    <td>${escapeHtml(s.telefono || '-')}</td>
                    <td>${escapeHtml(s.email || '-')}</td>
                    <td>
                        <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${s.id})" title="Modificar Sucursal"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado(${s.id})" title="Eliminar Sucursal"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`,
                onEmpty: () => '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-building"></i><p>No hay sucursales registradas</p></div></td></tr>'
            });
        } else {
            paginator.updateData(res.data || []);
        }
    });
}

function openModal(id = null) {
    Validator.clearForm('sucursalForm');
    document.getElementById('sucursalId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Modificar Sucursal' : 'Registrar Sucursal';
    new bootstrap.Modal(document.getElementById('sucursalModal')).show();
    Validator.initTracking('sucursalForm');
}

function editData(id) {
    apiCall(`/api/sucursales/${id}`).then(res => {
        const s = res.data;
        Validator.clearForm('sucursalForm');
        document.getElementById('sucursalId').value = s.id;
        document.getElementById('nombre').value = s.nombre;
        document.getElementById('direccion').value = s.direccion || '';
        document.getElementById('telefono').value = s.telefono || '';
        document.getElementById('email').value = s.email || '';
        document.getElementById('modalTitle').textContent = 'Modificar Sucursal';
        new bootstrap.Modal(document.getElementById('sucursalModal')).show();
        Validator.initTracking('sucursalForm');
    });
}

function saveData() {
    if (!Validator.validate('sucursalForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('sucursalId').value;
    const data = { nombre: document.getElementById('nombre').value, direccion: document.getElementById('direccion').value, telefono: document.getElementById('telefono').value, email: document.getElementById('email').value };
    const url = id ? `/api/sucursales/${id}` : '/api/sucursales/';
    const method = id ? 'PUT' : 'POST';
    const saveBtn = document.querySelector('#sucursalModal .btn-success');
    setButtonLoading(saveBtn, true, 'Guardando...');
    apiCall(url, method, data).then(res => {
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') { Validator.showServerErrors('sucursalForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('sucursalModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Estás seguro de que deseas eliminar esta sucursal?', () => {
        apiCall(`/api/sucursales/${id}`, 'DELETE').then(res => { showToast(res.message); loadData(); });
    });
}

function validateUniqueSucursalNombre() {
    const input = document.getElementById('nombre');
    if (!input) return;
    const value = input.value.trim();
    if (!value) {
        delete input.dataset.externalError;
        clearFieldError(input);
        updateFormSubmitState('sucursalForm');
        return;
    }
    if (!Validator.validateField('sucursalForm', 'nombre')) {
        delete input.dataset.externalError;
        updateFormSubmitState('sucursalForm');
        return;
    }
    const id = document.getElementById('sucursalId')?.value || '';
    apiCall('/api/sucursales/check-unique', 'POST', { field: 'nombre', value, exclude: id }).then(res => {
        if (res.status === 'success' && res.exists) {
            input.dataset.externalError = 'Ya existe una sucursal con ese nombre.';
            setFieldError(input, 'Ya existe una sucursal con ese nombre.');
        } else if (res.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('sucursalForm');
    });
}

function validateUniqueSucursalEmail() {
    const input = document.getElementById('email');
    if (!input) return;
    const value = input.value.trim();
    if (!value) {
        delete input.dataset.externalError;
        clearFieldError(input);
        updateFormSubmitState('sucursalForm');
        return;
    }
    if (!Validator.validateField('sucursalForm', 'email')) {
        delete input.dataset.externalError;
        updateFormSubmitState('sucursalForm');
        return;
    }
    const id = document.getElementById('sucursalId')?.value || '';
    apiCall('/api/sucursales/check-unique', 'POST', { field: 'email', value, exclude: id }).then(res => {
        if (res.status === 'success' && res.exists) {
            input.dataset.externalError = 'Este correo ya está registrado.';
            setFieldError(input, 'Este correo ya está registrado.');
        } else if (res.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('sucursalForm');
    });
}
