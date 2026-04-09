$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="mechanics"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('mechanicForm', {
        nombre: { required: true, requiredMsg: 'El nombre es obligatorio', minLength: 2 },
        apellido: { required: true, requiredMsg: 'El apellido es obligatorio', minLength: 2 },
        cedula: { required: true, requiredMsg: 'La cédula es obligatoria' }
    });
    Validator.setupRealtime('mechanicForm');
});

function loadData() {
    apiCall('/api/mechanics/').then(res => {
        const tbody = document.getElementById('mechanicBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(m => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${m.id}</td>
                <td>
                    <div class="d-flex align-items-center gap-4 py-2">
                        <img src="/public/assets/profile_pics/${m.foto_perfil || 'default.png'}" style="width: 150px; height: 195px;" class="rounded shadow-sm object-fit-cover border">
                        <div>
                            <h6 class="mb-0 fw-bold">${m.nombre || ''} ${m.apellido || ''}</h6>
                            <small class="text-muted"><i class="bi bi-person-badge me-1"></i>${m.cedula || '-'}</small>
                        </div>
                    </div>
                </td>
                <td>${m.especialidad || '-'}</td>
                <td>${m.telefono || '-'}</td>
                <td>${statusBadge(m.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${m.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${m.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado(${m.id})" title="${m.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${m.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-person-badge"></i><p>No hay mecanicos registrados</p></div></td></tr>';
    });
}

async function openModal(id = null) {
    Validator.clearForm('mechanicForm');
    document.getElementById('mechanicId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Editar Mecanico' : 'Nuevo Mecanico';
    new bootstrap.Modal(document.getElementById('mechanicModal')).show();
}

function editData(id) {
    apiCall(`/api/mechanics/${id}`).then(res => {
        const m = res.data;
        document.getElementById('mechanicId').value = m.id;
        document.getElementById('nombre').value = m.nombre || '';
        document.getElementById('apellido').value = m.apellido || '';
        document.getElementById('cedula').value = m.cedula || '';
        document.getElementById('telefono').value = m.telefono || '';
        document.getElementById('especialidad').value = m.especialidad || '';
        document.getElementById('modalTitle').textContent = 'Editar Mecanico';
        new bootstrap.Modal(document.getElementById('mechanicModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('mechanicForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('mechanicId').value;
    
    const formData = new FormData();
    formData.append('nombre', document.getElementById('nombre').value);
    formData.append('apellido', document.getElementById('apellido').value);
    formData.append('cedula', document.getElementById('cedula').value);
    formData.append('telefono', document.getElementById('telefono').value);
    formData.append('especialidad', document.getElementById('especialidad').value);
    
    const fileInput = document.getElementById('foto_perfil');
    if (fileInput.files.length > 0) {
        formData.append('foto_perfil', fileInput.files[0]);
    }

    const url = id ? `/api/mechanics/${id}` : '/api/mechanics/';
    const method = id ? 'PUT' : 'POST';
    
    apiCall(url, method, formData).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('mechanicForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('mechanicModal')).hide();
        showToast(res.message); loadData();
    });
}

function toggleEstado(id) {
    confirmAction('¿Cambiar estado?', () => {
        apiCall(`/api/mechanics/${id}/toggle`, 'PUT').then(res => { showToast(res.message); loadData(); });
    });
}
