$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="qr"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('qrForm', { tipo: { required: true }, contenido: { required: true, minLength: 3, requiredMsg: 'Contenido requerido' } });
    Validator.setupRealtime('qrForm');
});

function loadData() {
    apiCall('/api/qr/').then(res => {
        const tbody = document.getElementById('qrBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(q => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${q.id}</td>
                <td><span class="badge-status badge-info">${q.tipo}</span></td>
                <td>${(q.contenido||'').substring(0,50)}${(q.contenido||'').length>50?'...':''}</td>
                <td>${q.usuario_nombre||'N/A'}</td>
                <td>${formatDate(q.created_at)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-info btn-sm" onclick="viewQRImage(${q.id})" title="Ver Codigo QR"><i class="bi bi-qr-code-scan"></i></button>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${q.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="deleteQR(${q.id})" title="Desactivar"><i class="bi bi-pause-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-qr-code"></i><p>Sin codigos QR</p></div></td></tr>';
    });
}

function openModal() { Validator.clearForm('qrForm'); document.getElementById('qrId').value = ''; document.getElementById('modalTitle').textContent = 'Nuevo QR'; new bootstrap.Modal(document.getElementById('qrModal')).show(); }

function editData(id) {
    apiCall(`/api/qr/${id}`).then(res => { const q = res.data; document.getElementById('qrId').value = q.id; document.getElementById('tipo').value = q.tipo; document.getElementById('contenido').value = q.contenido||''; document.getElementById('utilidad').value = q.utilidad||''; document.getElementById('modalTitle').textContent = 'Editar QR'; new bootstrap.Modal(document.getElementById('qrModal')).show(); });
}

function saveData() {
    if (!Validator.validate('qrForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('qrId').value;
    const data = { tipo: document.getElementById('tipo').value, contenido: document.getElementById('contenido').value, utilidad: document.getElementById('utilidad').value };
    apiCall(id ? `/api/qr/${id}` : '/api/qr/', id ? 'PUT' : 'POST', data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('qrForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('qrModal')).hide(); showToast(res.message); loadData();
    });
}

function deleteQR(id) { confirmAction('¿Desactivar QR?', () => { apiCall(`/api/qr/${id}`, 'DELETE').then(res => { showToast(res.message); loadData(); }); }); }

function viewQRImage(id) {
    const preview = document.getElementById('qrImagePreview');
    preview.src = `/api/qr/${id}/image?t=${new Date().getTime()}`;
    new bootstrap.Modal(document.getElementById('viewQrModal')).show();
}
