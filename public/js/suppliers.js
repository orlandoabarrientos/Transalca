$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="suppliers"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('supplierForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'Nombre requerido', minLengthMsg: 'Minimo 3 caracteres' },
        rif: { required: true, pattern: /^[JGVEP]-\d{8}-\d$/, requiredMsg: 'RIF requerido', patternMsg: 'Formato: J-12345678-9' },
        email: { email: true },
        telefono: { minLength: 7, minLengthMsg: 'Minimo 7 caracteres' }
    });
    Validator.setupRealtime('supplierForm');
});

function loadData() {
    apiCall('/api/suppliers/').then(res => {
        const tbody = document.getElementById('supplierBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(s => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><strong>${s.nombre}</strong></td>
                <td>${s.rif}</td>
                <td>${s.telefono || '-'}</td>
                <td>${s.email || '-'}</td>
                <td>${statusBadge(s.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${escape(s.rif)}')" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${s.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado('${escape(s.rif)}')" title="${s.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${s.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-truck"></i><p>No hay proveedores registrados</p></div></td></tr>';
        }
    });
}

function openModal(rif = null) {
    Validator.clearForm('supplierForm');
    document.getElementById('supplierOldRif').value = rif ? unescape(rif) : '';
    document.getElementById('modalTitle').textContent = rif ? 'Editar Proveedor' : 'Nuevo Proveedor';
    new bootstrap.Modal(document.getElementById('supplierModal')).show();
}

function editData(rif) {
    rif = unescape(rif);
    apiCall(`/api/suppliers/${encodeURIComponent(rif)}`).then(res => {
        const s = res.data;
        document.getElementById('supplierOldRif').value = s.rif;
        document.getElementById('nombre').value = s.nombre;
        document.getElementById('rif').value = s.rif || '';
        document.getElementById('telefono').value = s.telefono || '';
        document.getElementById('email').value = s.email || '';
        document.getElementById('direccion').value = s.direccion || '';
        document.getElementById('modalTitle').textContent = 'Editar Proveedor';
        new bootstrap.Modal(document.getElementById('supplierModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('supplierForm')) return showToast('Corrija los errores','warning');
    const oldRif = document.getElementById('supplierOldRif').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        rif: document.getElementById('rif').value,
        telefono: document.getElementById('telefono').value,
        email: document.getElementById('email').value,
        direccion: document.getElementById('direccion').value
    };
    if (oldRif) {
        data.old_rif = oldRif;
        apiCall('/api/suppliers/update', 'PUT', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('supplierForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('supplierModal')).hide();
            showToast(res.message); loadData();
        });
    } else {
        apiCall('/api/suppliers/', 'POST', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('supplierForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('supplierModal')).hide();
            showToast(res.message); loadData();
        });
    }
}

function toggleEstado(rif) {
    rif = unescape(rif);
    confirmAction('¿Cambiar estado de este proveedor?', () => {
        apiCall('/api/suppliers/toggle', 'PUT', { rif }).then(res => { showToast(res.message); loadData(); });
    });
}
