$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="brands"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('brandForm', {
        nombre: { required: true, minLength: 2, requiredMsg: 'El nombre de la marca es obligatorio', minLengthMsg: 'El nombre debe tener al menos 2 caracteres' }
    });
    Validator.setupRealtime('brandForm');

    // Debounced real-time uniqueness validation
    let checkTimeout = null;
    const nameInput = document.getElementById('nombre');
    if (nameInput) {
        nameInput.addEventListener('input', () => {
            clearTimeout(checkTimeout);
            const val = nameInput.value.trim();
            const exclude = document.getElementById('brandOldNombre').value.trim();
            if (val.length < 2) return;
            checkTimeout = setTimeout(() => {
                fetch(`/api/brands/check-unique?value=${encodeURIComponent(val)}&exclude=${encodeURIComponent(exclude)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'success' && !data.unique) {
                            nameInput.dataset.externalError = 'La marca ya existe';
                            setFieldError(nameInput, 'La marca ya existe');
                        } else {
                            delete nameInput.dataset.externalError;
                            if (nameInput.classList.contains('is-invalid') && getFieldFeedback(nameInput).textContent === 'La marca ya existe') {
                                clearFieldError(nameInput);
                                nameInput.classList.add('is-valid');
                            }
                        }
                        updateFormSubmitState('brandForm');
                    });
            }, 350);
        });
    }
});

function loadData() {
    apiCall('/api/brands/').then(res => {
        const tbody = document.getElementById('brandBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(b => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><strong>${escapeHtml(b.nombre)}</strong></td>
                <td>${escapeHtml(b.descripcion || '-')}</td>
                <td>${b.total_productos || 0}</td>
                <td>${statusBadge(b.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${escape(b.nombre)}')" title="Modificar Marca"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado('${escape(b.nombre)}')" title="Eliminar Marca"><i class="bi bi-trash"></i></button>
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
    document.getElementById('modalTitle').textContent = nombre ? 'Modificar Marca' : 'Registrar Marca';
    new bootstrap.Modal(document.getElementById('brandModal')).show();
    Validator.initTracking('brandForm');
}

function editData(nombre) {
    nombre = unescape(nombre);
    apiCall(`/api/brands/${encodeURIComponent(nombre)}`).then(res => {
        const b = res.data;
        document.getElementById('brandOldNombre').value = b.nombre;
        document.getElementById('nombre').value = b.nombre;
        document.getElementById('descripcion').value = b.descripcion || '';
        document.getElementById('modalTitle').textContent = 'Modificar Marca';
        new bootstrap.Modal(document.getElementById('brandModal')).show();
        Validator.initTracking('brandForm');
    });
}

function saveData() {
    if (!Validator.validate('brandForm')) return showToast('Corrija los errores', 'warning');
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
    confirmAction('¿Estás seguro de que deseas eliminar esta marca?', () => {
        apiCall('/api/brands/delete', 'DELETE', { nombre }).then(res => { showToast(res.message); loadData(); });
    });
}
