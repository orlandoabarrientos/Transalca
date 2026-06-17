$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="backup"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
});

let paginator = null;

function loadData() {
    apiCall('/api/backup/').then(res => {
        if (!paginator) {
            paginator = new TablePaginator('backupBody', {
                allData: res.data || [],
                itemName: 'respaldos',
                renderRow: (b) => `<tr class="fade-in-up">
                    <td><i class="bi bi-file-earmark-zip me-2" style="color:var(--primary);"></i><strong>${escapeHtml(b.filename)}</strong></td>
                    <td>${escapeHtml(b.size || '-')}</td>
                    <td>${escapeHtml(b.date || '-')}</td>
                    <td>
                        <a href="/api/backup/download/${escapeHtml(b.filename)}" class="btn btn-icon btn-outline-orange btn-sm" title="Descargar Respaldo"><i class="bi bi-download"></i></a>
                        <button class="btn btn-icon btn-sm btn-success" onclick="restoreBackup('${escapeHtml(b.filename)}')" title="Restaurar Respaldo"><i class="bi bi-arrow-counterclockwise"></i></button>
                        <button class="btn btn-icon btn-sm btn-danger" onclick="deleteBackup('${escapeHtml(b.filename)}')" title="Eliminar Respaldo"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`,
                onEmpty: () => '<tr><td colspan="4" class="text-center py-4"><div class="empty-state"><i class="bi bi-database"></i><p>Sin respaldos registrados</p></div></td></tr>'
            });
        } else {
            paginator.updateData(res.data || []);
        }
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
    confirmAction('¿Estás seguro de que deseas eliminar este respaldo?', () => {
        apiCall(`/api/backup/delete/${filename}`, 'DELETE').then(res => { showToast(res.message); loadData(); });
    });
}

function restoreBackup(filename) {
    confirmAction(
        'Restaurar este respaldo reemplazará los datos actuales de la base de datos. Se creará un respaldo de seguridad del estado actual antes de continuar. ¿Desea continuar?',
        () => {
            showToast('Restaurando respaldo...', 'info');
            apiCall('/api/backup/restore', 'POST', { filename }).then(res => {
                if (res.status === 'error') return showToast(res.message, 'error');
                showToast(res.message || 'Respaldo restaurado correctamente', 'success');
                loadData();
            });
        },
        { type: 'warning', confirmText: 'Restaurar', confirmColor: '#dc3545' }
    );
}

function importBackup() {
    const input = document.getElementById('restoreFileInput');
    const file = input.files && input.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('backup', file);
    showToast('Importando respaldo...', 'info');
    apiCall('/api/backup/upload', 'POST', formData).then(res => {
        input.value = '';
        if (res.status === 'error') return showToast(res.message, 'error');
        showToast(res.message || 'Respaldo importado correctamente', 'success');
        loadData();
    });
}
