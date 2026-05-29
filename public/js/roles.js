const MODULES = [];
const MODULE_LABELS = {
    usuarios: 'G. Usuarios',
    roles: 'G. Roles',
    productos: 'G. Productos',
    categorias: 'G. Categorías',
    marcas: 'G. Marcas',
    proveedores: 'G. Proveedores',
    mecanicos: 'G. Mecánicos',
    stock: 'G. Stock de producto',
    servicios: 'G. Servicios',
    empresas: 'G. Empresa',
    creditos: 'G. Crédito',
    metodos_pago: 'G. Métodos de Pago',
    promociones: 'G. Promociones',
    ordenes: 'R. Orden de Venta',
    pagos: 'G. Pagos',
    bitacora: 'G. Bitácora',
    reportes: 'Reportes',
    respaldos: 'G. Respaldos',
    qr: 'G. Códigos QR',
    sucursales: 'G. Sucursales',
    vehiculos: 'G. Vehículos',
    comisiones: 'G. Comisiones',
    tickets: 'G. Tickets Soporte',
    notificaciones: 'Notificaciones',
    mantenimiento: 'G. Mantenimiento',
    tasas_avanzadas: 'G. Tasa de Cambio',
    cotizaciones: 'G. Cotizaciones',
    filtros: 'G. Filtros',
    combustible: 'G. Combustible'
};

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="roles"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    loadData();
    loadModules();
    Validator.setRules('roleForm', {
        nombre: {
            required: true,
            minLength: 3,
            pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/,
            requiredMsg: 'El nombre es obligatorio',
            patternMsg: 'El nombre solo puede contener letras'
        }
    });
    Validator.setupRealtime('roleForm');
});

function loadData() {
    apiCall('/api/roles/').then(res => {
        const tbody = document.getElementById('roleBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(r => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${r.id}</td>
                <td><strong>${escapeHtml(r.nombre)}</strong></td>
                <td>${escapeHtml(r.descripcion || '-')}</td>
                <td>${statusBadge(r.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${r.id})" title="Modificar rol"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-outline-danger" onclick="toggleEstado(${r.id})" title="Eliminar rol"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-shield-lock"></i><p>Sin roles</p></div></td></tr>';
    });
}

async function loadModules() {
    try {
        const res = await apiCall('/api/roles/modules');
        MODULES.length = 0;
        (res.data || []).forEach(m => MODULES.push(m));
    } catch(e) {}
}

function renderPermissions(permisos = []) {
    const tbody = document.getElementById('permissionsBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    MODULES.forEach(mod => {
        const p = permisos.find(x => x.modulo === mod) || {};
        tbody.innerHTML += `<tr>
            <td class="fw-bold">${escapeHtml(MODULE_LABELS[mod] || mod)}</td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="crear" ${p.crear ? 'checked' : ''}></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="leer" ${p.leer ? 'checked' : ''}></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="actualizar" ${p.actualizar ? 'checked' : ''}></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="eliminar" ${p.eliminar ? 'checked' : ''}></td>
        </tr>`;
    });
}

function openModal() {
    Validator.clearForm('roleForm');
    document.getElementById('roleId').value = '';
    document.getElementById('modalTitle').textContent = 'Registrar rol';
    renderPermissions();
    new bootstrap.Modal(document.getElementById('roleModal')).show();
    Validator.initTracking('roleForm');
}

function editData(id) {
    apiCall(`/api/roles/${id}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const r = res.data || {};
        Validator.clearForm('roleForm');
        document.getElementById('roleId').value = r.id;
        document.getElementById('nombre').value = r.nombre || '';
        document.getElementById('descripcion').value = r.descripcion || '';
        renderPermissions(r.permisos || []);
        document.getElementById('modalTitle').textContent = 'Modificar rol';
        new bootstrap.Modal(document.getElementById('roleModal')).show();
        Validator.initTracking('roleForm');
    });
}

function collectPermissions() {
    const perms = [];
    MODULES.forEach(mod => {
        const crear = document.querySelector(`.perm-check[data-mod="${mod}"][data-perm="crear"]`)?.checked ? 1 : 0;
        const leer = document.querySelector(`.perm-check[data-mod="${mod}"][data-perm="leer"]`)?.checked ? 1 : 0;
        const actualizar = document.querySelector(`.perm-check[data-mod="${mod}"][data-perm="actualizar"]`)?.checked ? 1 : 0;
        const eliminar = document.querySelector(`.perm-check[data-mod="${mod}"][data-perm="eliminar"]`)?.checked ? 1 : 0;
        if (crear || leer || actualizar || eliminar) {
            perms.push({ modulo: mod, crear, leer, actualizar, eliminar });
        }
    });
    return perms;
}

function saveData() {
    if (!Validator.validate('roleForm')) return showToast('Corrija los errores', 'warning');
    const id = document.getElementById('roleId').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        permisos: collectPermissions()
    };
    const url = id ? `/api/roles/${id}` : '/api/roles/';
    const method = id ? 'PUT' : 'POST';
    const saveBtn = document.querySelector('#roleModal .btn-orange');
    setButtonLoading(saveBtn, true, 'Guardando...');
    apiCall(url, method, data).then(res => {
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') {
            Validator.showServerErrors('roleForm', res.errors);
            return showToast(res.message, 'error');
        }
        bootstrap.Modal.getInstance(document.getElementById('roleModal')).hide();
        showToast(res.message, 'success');
        loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Estás seguro de que deseas eliminar este rol?', () => {
        apiCall(`/api/roles/${id}`, 'DELETE').then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message, 'success');
            loadData();
        });
    });
}

function escapeHtml(text) {
    return String(text ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
