$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="backup"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
});

function loadData() {
    apiCall('/api/backup/').then(res => {
        const tbody = document.getElementById('backupBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(b => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><i class="bi bi-file-earmark-zip me-2" style="color:var(--primary);"></i><strong>${b.filename}</strong></td>
                <td>${b.size || '-'}</td>
                <td>${b.date || '-'}</td>
                <td>
                    <a href="/api/backup/download/${b.filename}" class="btn btn-icon btn-outline-orange btn-sm" title="Descargar"><i class="bi bi-download"></i></a>
                    <button class="btn btn-icon btn-sm btn-danger" onclick="deleteBackup('${b.filename}')" title="Eliminar"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4"><div class="empty-state"><i class="bi bi-database"></i><p>Sin respaldos</p></div></td></tr>';
    });
}

function createBackup() {
    showToast('Creando respaldo...', 'info');
    apiCall('/api/backup/create', 'POST').then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        showToast('Respaldo creado exitosamente'); loadData();
    });
}

function deleteBackup(filename) {
    confirmAction('¿Eliminar este respaldo?', () => {
        apiCall(`/api/backup/delete/${filename}`, 'DELETE').then(res => { showToast(res.message); loadData(); });
    });
}
