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
            maxLength: 30,
            pattern: /^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$/,
            requiredMsg: 'El nombre es obligatorio',
            patternMsg: 'El nombre solo puede contener letras',
            maxLengthMsg: 'El nombre del cargo no puede superar los 30 caracteres.'
        },
        descripcion: {
            maxLength: 150,
            maxLengthMsg: 'La descripción no puede superar los 150 caracteres.'
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
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${r.id})" title="Modificar rol"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-outline-danger" onclick="toggleEstado(${r.id})" title="Eliminar rol"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4"><div class="empty-state"><i class="bi bi-shield-lock"></i><p>Sin roles</p></div></td></tr>';
    });
}

async function loadModules() {
    try {
        const res = await apiCall('/api/roles/modules');
        MODULES.length = 0;
        (res.data || []).forEach(m => MODULES.push(m));
    } catch(e) {}
}

let permissionsState = {};
let currentPermissionsPage = 1;
const permissionsPerPage = 5;

function initPermissionsState(permisos = []) {
    permissionsState = {};
    MODULES.forEach(mod => {
        permissionsState[mod] = { crear: 0, leer: 0, actualizar: 0, eliminar: 0 };
    });
    permisos.forEach(p => {
        if (permissionsState[p.modulo]) {
            permissionsState[p.modulo] = {
                crear: p.crear ? 1 : 0,
                leer: p.leer ? 1 : 0,
                actualizar: p.actualizar ? 1 : 0,
                eliminar: p.eliminar ? 1 : 0
            };
        }
    });
}

function renderPermissionsPage(page = 1) {
    currentPermissionsPage = page;
    const tbody = document.getElementById('permissionsBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const start = (page - 1) * permissionsPerPage;
    const end = start + permissionsPerPage;
    const pageModules = MODULES.slice(start, end);
    
    pageModules.forEach(mod => {
        const p = permissionsState[mod] || { crear: 0, leer: 0, actualizar: 0, eliminar: 0 };
        tbody.innerHTML += `<tr>
            <td class="fw-bold">${escapeHtml(MODULE_LABELS[mod] || mod)}</td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="crear" ${p.crear ? 'checked' : ''} onchange="updatePermissionState('${escapeHtml(mod)}', 'crear', this.checked)"></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="leer" ${p.leer ? 'checked' : ''} onchange="updatePermissionState('${escapeHtml(mod)}', 'leer', this.checked)"></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="actualizar" ${p.actualizar ? 'checked' : ''} onchange="updatePermissionState('${escapeHtml(mod)}', 'actualizar', this.checked)"></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${escapeHtml(mod)}" data-perm="eliminar" ${p.eliminar ? 'checked' : ''} onchange="updatePermissionState('${escapeHtml(mod)}', 'eliminar', this.checked)"></td>
        </tr>`;
    });
    
    renderPermissionsPagination(MODULES.length, page);
}

function updatePermissionState(mod, perm, checked) {
    if (!permissionsState[mod]) {
        permissionsState[mod] = { crear: 0, leer: 0, actualizar: 0, eliminar: 0 };
    }
    permissionsState[mod][perm] = checked ? 1 : 0;
    updateFormSubmitState('roleForm');
}

function renderPermissionsPagination(total, page) {
    const info = document.getElementById('permissionsPageInfo');
    const controls = document.getElementById('permissionsPagination');
    const pages = Math.ceil(total / permissionsPerPage);
    
    if (info) {
        const start = total ? (page - 1) * permissionsPerPage + 1 : 0;
        const end = Math.min(page * permissionsPerPage, total);
        info.textContent = `Mostrando ${start} a ${end} de ${total} módulos`;
    }
    if (!controls) return;
    controls.innerHTML = '';
    if (pages <= 1) return;
    
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page > 1}) renderPermissionsPage(${page - 1})"><i class="bi bi-chevron-left"></i></a>`;
    controls.appendChild(prevLi);
    
    for (let i = 1; i <= pages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${page === i ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); renderPermissionsPage(${i})">${i}</a>`;
        controls.appendChild(li);
    }
    
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${page === pages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page < pages}) renderPermissionsPage(${page + 1})"><i class="bi bi-chevron-right"></i></a>`;
    controls.appendChild(nextLi);
}

function openModal() {
    Validator.clearForm('roleForm');
    document.getElementById('roleId').value = '';
    document.getElementById('modalTitle').textContent = 'Registrar rol';
    initPermissionsState();
    renderPermissionsPage(1);
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
        initPermissionsState(r.permisos || []);
        renderPermissionsPage(1);
        document.getElementById('modalTitle').textContent = 'Modificar rol';
        new bootstrap.Modal(document.getElementById('roleModal')).show();
        Validator.initTracking('roleForm');
    });
}

function collectPermissions() {
    const perms = [];
    Object.keys(permissionsState).forEach(mod => {
        const p = permissionsState[mod];
        if (p.crear || p.leer || p.actualizar || p.eliminar) {
            perms.push({ modulo: mod, crear: p.crear, leer: p.leer, actualizar: p.actualizar, eliminar: p.eliminar });
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
    const saveBtn = document.querySelector('#roleModal .btn-success');
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
