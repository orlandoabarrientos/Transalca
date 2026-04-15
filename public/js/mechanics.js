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
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${escape(m.cedula)}')" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${m.estado ? 'btn-warning' : 'btn-success'}" onclick="deleteData('${escape(m.cedula)}')" title="Desactivar"><i class="bi bi-${m.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-person-badge"></i><p>No hay mecanicos registrados</p></div></td></tr>';
    });
}

async function openModal(cedula = null) {
    Validator.clearForm('mechanicForm');
    document.getElementById('mechanicOldCedula').value = cedula ? unescape(cedula) : '';
    document.getElementById('modalTitle').textContent = cedula ? 'Editar Mecanico' : 'Nuevo Mecanico';
    new bootstrap.Modal(document.getElementById('mechanicModal')).show();
}

function editData(cedula) {
    cedula = unescape(cedula);
    apiCall(`/api/mechanics/${encodeURIComponent(cedula)}`).then(res => {
        const m = res.data;
        document.getElementById('mechanicOldCedula').value = m.cedula;
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
    const oldCedula = document.getElementById('mechanicOldCedula').value;
    
    const formData = new FormData();
    formData.append('nombre', document.getElementById('nombre').value);
    formData.append('apellido', document.getElementById('apellido').value);
    formData.append('cedula', document.getElementById('cedula').value);
    formData.append('telefono', document.getElementById('telefono').value);
    formData.append('especialidad', document.getElementById('especialidad').value);
    
    const fileInput = document.getElementById('foto_perfil');
    if (fileInput && fileInput.files.length > 0) {
        formData.append('foto_perfil', fileInput.files[0]);
    }

    if (oldCedula) {
        formData.append('old_cedula', oldCedula);
        apiCall('/api/mechanics/update', 'PUT', formData).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('mechanicForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('mechanicModal')).hide();
            showToast(res.message); loadData();
        });
    } else {
        apiCall('/api/mechanics/', 'POST', formData).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('mechanicForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('mechanicModal')).hide();
            showToast(res.message); loadData();
        });
    }
}

function deleteData(cedula) {
    cedula = unescape(cedula);
    confirmAction('¿Desactivar este mecánico?', () => {
        apiCall('/api/mechanics/delete', 'DELETE', { cedula }).then(res => { showToast(res.message); loadData(); });
    });
}
