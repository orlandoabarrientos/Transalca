const MODULES = [];

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="roles"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadModules();
    Validator.setRules('roleForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'Nombre requerido' }
    });
    Validator.setupRealtime('roleForm');
});

function loadData() {
    apiCall('/api/roles/').then(res => {
        const tbody = document.getElementById('roleBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(r => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${r.id}</td>
                <td><strong>${r.nombre}</strong></td>
                <td>${r.descripcion || '-'}</td>
                <td>${statusBadge(r.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${r.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${r.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado(${r.id})" title="${r.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${r.estado ? 'pause' : 'play'}-fill"></i></button>
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
        (res.data||[]).forEach(m => MODULES.push(m));
    } catch(e) {}
}

function renderPermissions(permisos = []) {
    const tbody = document.getElementById('permissionsBody');
    if(!tbody) return;
    tbody.innerHTML = '';
    MODULES.forEach(mod => {
        const p = permisos.find(x => x.modulo === mod) || {};
        tbody.innerHTML += `<tr>
            <td class="fw-bold text-capitalize">${mod}</td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${mod}" data-perm="crear" ${p.crear ? 'checked' : ''}></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${mod}" data-perm="leer" ${p.leer ? 'checked' : ''}></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${mod}" data-perm="actualizar" ${p.actualizar ? 'checked' : ''}></td>
            <td><input type="checkbox" class="form-check-input perm-check" data-mod="${mod}" data-perm="eliminar" ${p.eliminar ? 'checked' : ''}></td>
        </tr>`;
    });
}

function openModal() {
    Validator.clearForm('roleForm');
    document.getElementById('roleId').value = '';
    document.getElementById('modalTitle').textContent = 'Nuevo Rol';
    renderPermissions();
    new bootstrap.Modal(document.getElementById('roleModal')).show();
}

function editData(id) {
    apiCall(`/api/roles/${id}`).then(res => {
        const r = res.data;
        document.getElementById('roleId').value = r.id;
        document.getElementById('nombre').value = r.nombre;
        document.getElementById('descripcion').value = r.descripcion || '';
        renderPermissions(r.permisos || []);
        document.getElementById('modalTitle').textContent = 'Editar Rol';
        new bootstrap.Modal(document.getElementById('roleModal')).show();
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
    if (!Validator.validate('roleForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('roleId').value;
    const data = { nombre: document.getElementById('nombre').value, descripcion: document.getElementById('descripcion').value, permisos: collectPermissions() };
    const url = id ? `/api/roles/${id}` : '/api/roles/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('roleForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('roleModal')).hide();
        showToast(res.message); loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Cambiar estado del rol?', () => {
        apiCall(`/api/roles/${id}`, 'DELETE').then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message); loadData();
        });
    });
}
