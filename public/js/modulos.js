$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="modulos"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    loadData();
    Validator.setRules('moduloForm', {
        titulo: {
            required: true,
            minLength: 2,
            maxLength: 150,
            requiredMsg: 'El nombre del módulo es obligatorio',
            minLengthMsg: 'Debe tener al menos 2 caracteres',
            maxLengthMsg: 'No puede superar los 150 caracteres.'
        },
        nombre: {
            required: true,
            pattern: /^[a-z][a-z0-9_]{1,99}$/,
            requiredMsg: 'La clave es obligatoria',
            patternMsg: 'Solo minúsculas, números y guion bajo (ej: ordenes_compra).'
        },
        descripcion: {
            maxLength: 255,
            pattern: /^$|^[^<>]+$/,
            maxLengthMsg: 'No puede superar los 255 caracteres.',
            patternMsg: 'Contiene caracteres no permitidos.'
        },
        ruta: {
            required: true,
            pattern: /^\/[A-Za-z0-9_\-\/]*$/,
            requiredMsg: 'La ruta es obligatoria',
            patternMsg: 'La ruta debe iniciar con / y ser interna (ej: /admin/ejemplo).'
        },
        grupo: { required: true, requiredMsg: 'El grupo es obligatorio' },
        orden: { required: true, requiredMsg: 'El orden es obligatorio' }
    });
    Validator.setupRealtime('moduloForm');

    let checkTimeout = null;
    bindUniqueCheck('nombre', 'nombre', 'Ya existe un módulo con esa clave');
    bindUniqueCheck('ruta', 'ruta', 'Ya existe un módulo con esa ruta');

    function bindUniqueCheck(inputId, field, message) {
        const input = document.getElementById(inputId);
        if (!input) return;
        input.addEventListener('input', () => {
            clearTimeout(checkTimeout);
            const val = input.value.trim();
            const exclude = document.getElementById('moduloId').value.trim();
            if (!val) return;
            checkTimeout = setTimeout(() => {
                fetch(`/api/modulos/check-unique?field=${field}&value=${encodeURIComponent(val)}&exclude=${encodeURIComponent(exclude)}`, { credentials: 'same-origin' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'success' && !data.unique) {
                            input.dataset.externalError = message;
                            setFieldError(input, message);
                        } else {
                            delete input.dataset.externalError;
                            if (input.classList.contains('is-invalid') && getFieldFeedback(input).textContent === message) {
                                clearFieldError(input);
                            }
                        }
                        updateFormSubmitState('moduloForm');
                    });
            }, 350);
        });
    }
});

let paginator = null;

function loadData() {
    apiCall('/api/modulos/').then(res => {
        const data = res.data || [];
        if (!paginator) {
            paginator = new TablePaginator('moduloBody', {
                allData: data,
                itemName: 'módulos',
                searchSelector: '#searchModulo',
                filterSelectors: [
                    { selector: '#filterGrupo', filterFn: (item, val) => item.grupo === val }
                ],
                renderRow: (m) => `<tr class="fade-in-up">
                    <td><i class="${escapeHtml(m.icono || 'bi bi-app')} me-2" style="color:var(--primary);"></i><strong>${escapeHtml(m.titulo)}</strong></td>
                    <td><code>${escapeHtml(m.nombre)}</code></td>
                    <td>${escapeHtml(m.ruta || '-')}</td>
                    <td>${escapeHtml(m.grupo)}</td>
                    <td>${m.orden}</td>
                    <td>${m.en_sidebar ? '<span class="badge-status badge-active">Sí</span>' : '<span class="badge-status badge-inactive">No</span>'}</td>
                    <td>
                        <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${m.id})" title="Modificar Módulo"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado(${m.id})" title="Eliminar Módulo"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`,
                onEmpty: () => '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-grid-3x3-gap"></i><p>No hay módulos registrados</p></div></td></tr>'
            });
        } else {
            paginator.updateData(data);
        }
    });
}

function openModal() {
    Validator.clearForm('moduloForm');
    document.getElementById('moduloId').value = '';
    document.getElementById('en_sidebar').value = '1';
    document.getElementById('publico').value = '0';
    document.getElementById('estado').value = '1';
    document.getElementById('orden').value = '0';
    document.getElementById('icono').value = 'bi bi-app';
    document.getElementById('modalTitle').textContent = 'Registrar Módulo';
    new bootstrap.Modal(document.getElementById('moduloModal')).show();
    Validator.initTracking('moduloForm');
}

function editData(id) {
    apiCall(`/api/modulos/${id}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const m = res.data;
        document.getElementById('moduloId').value = m.id;
        document.getElementById('titulo').value = m.titulo || '';
        document.getElementById('nombre').value = m.nombre || '';
        document.getElementById('descripcion').value = m.descripcion || '';
        document.getElementById('ruta').value = m.ruta || '';
        document.getElementById('icono').value = m.icono || 'bi bi-app';
        document.getElementById('grupo').value = m.grupo || 'Gestión';
        document.getElementById('orden').value = m.orden ?? 0;
        document.getElementById('en_sidebar').value = String(m.en_sidebar ?? 1);
        document.getElementById('publico').value = String(m.publico ?? 0);
        document.getElementById('estado').value = String(m.estado ?? 1);
        document.getElementById('modalTitle').textContent = 'Modificar Módulo';
        new bootstrap.Modal(document.getElementById('moduloModal')).show();
        Validator.initTracking('moduloForm');
    });
}

function collectData() {
    return {
        nombre: document.getElementById('nombre').value,
        titulo: document.getElementById('titulo').value,
        descripcion: document.getElementById('descripcion').value,
        ruta: document.getElementById('ruta').value,
        icono: document.getElementById('icono').value,
        grupo: document.getElementById('grupo').value,
        orden: document.getElementById('orden').value,
        en_sidebar: document.getElementById('en_sidebar').value,
        publico: document.getElementById('publico').value,
        estado: document.getElementById('estado').value
    };
}

function saveData() {
    if (!Validator.validate('moduloForm')) return showToast('Corrija los errores del formulario', 'warning');
    const id = document.getElementById('moduloId').value;
    const data = collectData();
    const url = id ? `/api/modulos/${id}` : '/api/modulos/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('moduloForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('moduloModal')).hide();
        showToast(res.message); loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Estás seguro de que deseas eliminar este módulo?', () => {
        apiCall(`/api/modulos/${id}`, 'DELETE').then(res => { showToast(res.message); loadData(); });
    });
}
