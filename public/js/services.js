$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="services"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadSucursales('sucursal_id', false).then(() => enhanceSearchableSelects(document.getElementById('serviceModal')));
    Validator.setRules('serviceForm', {
        nombre: { required: true, minLength: 3, maxLength: 50, requiredMsg: 'El nombre es obligatorio', minLengthMsg: 'Mínimo 3 caracteres', maxLengthMsg: 'El nombre del servicio no puede superar los 50 caracteres.' },
        descripcion: { maxLength: 150, maxLengthMsg: 'La descripción no puede superar los 150 caracteres.' },
        precio: { required: true, min: 0.01, requiredMsg: 'El precio es obligatorio', minMsg: 'Debe ser mayor a 0' },
        duracion_estimada: { required: true, min: 1, requiredMsg: 'La duración es obligatoria', minMsg: 'Debe ser mayor a 0' },
        tipo: { required: true, requiredMsg: 'Seleccione un tipo de servicio' },
        sucursal_id: { required: true, requiredMsg: 'Seleccione al menos una sucursal' }
    });
    Validator.setupRealtime('serviceForm');

    let checkTimeout = null;
    const nameInput = document.getElementById('nombre');
    if (nameInput) {
        nameInput.addEventListener('input', () => {
            clearTimeout(checkTimeout);
            const val = nameInput.value.trim();
            const exclude = document.getElementById('serviceId').value.trim();
            if (val.length < 3) return;
            checkTimeout = setTimeout(() => {
                fetch(`/api/services/check-unique?value=${encodeURIComponent(val)}&exclude=${encodeURIComponent(exclude)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'success' && !data.unique) {
                            nameInput.dataset.externalError = 'El servicio ya existe';
                            setFieldError(nameInput, 'El servicio ya existe');
                        } else {
                            delete nameInput.dataset.externalError;
                            if (nameInput.classList.contains('is-invalid') && getFieldFeedback(nameInput).textContent === 'El servicio ya existe') {
                                clearFieldError(nameInput);
                                nameInput.classList.add('is-valid');
                            }
                        }
                        updateFormSubmitState('serviceForm');
                    });
            }, 350);
        });
    }
});

let paginator = null;

function loadData() {
    apiCall('/api/services/').then(res => {
        if (!paginator) {
            paginator = new TablePaginator('serviceBody', {
                allData: res.data || [],
                itemName: 'servicios',
                renderRow: (s) => `<tr class="fade-in-up">
                    <td class="col-id">${s.id}</td>
                    <td><strong>${escapeHtml(s.nombre)}</strong></td>
                    <td><span class="badge-status badge-info">${escapeHtml(s.tipo || 'general')}</span></td>
                    <td>${escapeHtml(s.sucursal_nombre || 'Todas')}</td>
                    <td class="fw-bold" style="color:var(--primary);" data-usd-price="${s.precio}">${formatUsdBs(s.precio)}</td>
                    <td>${s.duracion_estimada || '-'} min</td>
                    <td>
                        <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${s.id})" title="Modificar Servicio"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado(${s.id})" title="Eliminar Servicio"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`,
                onEmpty: () => '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-wrench-adjustable"></i><p>No hay servicios registrados</p></div></td></tr>'
            });
        } else {
            paginator.updateData(res.data || []);
        }
    });
}

function openModal(id = null) {
    Validator.clearForm('serviceForm');
    document.getElementById('serviceId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Modificar Servicio' : 'Registrar Servicio';
    new bootstrap.Modal(document.getElementById('serviceModal')).show();
    Validator.initTracking('serviceForm');
}

function editData(id) {
    apiCall(`/api/services/${id}`).then(res => {
        const s = res.data;
        Validator.clearForm('serviceForm');
        document.getElementById('serviceId').value = s.id;
        document.getElementById('nombre').value = s.nombre;
        document.getElementById('descripcion').value = s.descripcion || '';
        document.getElementById('tipo').value = s.tipo || 'general';
        document.getElementById('precio').value = s.precio;
        document.getElementById('duracion_estimada').value = s.duracion_estimada || 60;
        const sucSel = document.getElementById('sucursal_id');
        if(sucSel) {
            const ids = String(s.sucursal_ids || '').split(',').filter(Boolean);
            Array.from(sucSel.options).forEach(opt => { opt.selected = ids.includes(opt.value); });
            if (window.jQuery?.fn?.select2) window.jQuery(sucSel).trigger('change.select2');
        }
        document.getElementById('modalTitle').textContent = 'Modificar Servicio';
        new bootstrap.Modal(document.getElementById('serviceModal')).show();
        Validator.initTracking('serviceForm');
    });
}

function saveData() {
    if (!Validator.validate('serviceForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('serviceId').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        tipo: document.getElementById('tipo').value,
        precio: parseFloat(document.getElementById('precio').value),
        duracion_estimada: parseInt(document.getElementById('duracion_estimada').value) || 60,
        sucursal_ids: Array.from(document.getElementById('sucursal_id')?.selectedOptions || []).map(o => o.value)
    };
    const url = id ? `/api/services/${id}` : '/api/services/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('serviceForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('serviceModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Estás seguro de que deseas eliminar este servicio?', () => {
        apiCall(`/api/services/${id}`, 'DELETE').then(res => { showToast(res.message); loadData(); });
    });
}
