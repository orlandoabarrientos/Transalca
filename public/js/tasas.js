$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="tasas"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('tasaForm', {
        fecha: { required: true, requiredMsg: 'Fecha requerida' },
        monto: { required: true, min: 0.01, requiredMsg: 'Monto requerido', minMsg: 'Debe ser mayor a 0' },
        fuente: { required: true, minLength: 2, maxLength: 30, requiredMsg: 'Fuente requerida', minLengthMsg: 'Mínimo 2 caracteres', maxLengthMsg: 'La fuente no puede superar los 30 caracteres.' }
    });
    Validator.setupRealtime('tasaForm');
});

let paginator = null;

function loadData() {
    apiCall('/api/tasas/').then(res => {
        const data = res.data || [];
        if (!paginator) {
            paginator = new TablePaginator('tasaBody', {
                allData: data,
                itemName: 'tasas',
                renderRow: (t) => `<tr class="fade-in-up">
                    <td class="col-id">${t.id}</td>
                    <td>${formatDate(t.fecha)}</td>
                    <td class="fw-bold" style="color:var(--primary);">${parseFloat(t.monto).toFixed(2)} Bs</td>
                    <td>${escapeHtml(t.fuente)}</td>
                    <td>
                        <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${t.id}, '${t.fecha}', ${t.monto}, '${escapeHtml(t.fuente)}')" title="Modificar Tasa"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-icon btn-sm btn-outline-danger" onclick="deleteData(${t.id})" title="Eliminar Tasa"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`,
                onEmpty: () => '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-currency-dollar"></i><p>No hay tasas registradas</p></div></td></tr>'
            });
        } else {
            paginator.updateData(data);
        }
        if (data.length > 0) {
            document.getElementById('statLatest').textContent = parseFloat(data[0].monto).toFixed(2);
            document.getElementById('statDate').textContent = formatDate(data[0].fecha);
            document.getElementById('statFuente').textContent = data[0].fuente;
        }
    });
}

function openModal(id = null) {
    Validator.clearForm('tasaForm');
    document.getElementById('tasaId').value = id || '';
    document.getElementById('modalTitle').textContent = id ? 'Modificar Tasa' : 'Registrar Tasa';
    if (!id) {
        document.getElementById('fecha').value = new Date().toISOString().split('T')[0];
    }
    new bootstrap.Modal(document.getElementById('tasaModal')).show();
    Validator.initTracking('tasaForm');
}

function formatIsoDate(dateStr) {
    if (!dateStr) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
    if (/^\d{4}-\d{2}-\d{2}T/.test(dateStr)) return dateStr.split('T')[0];
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    const year = d.getUTCFullYear();
    const month = String(d.getUTCMonth() + 1).padStart(2, '0');
    const day = String(d.getUTCDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function editData(id, fecha, monto, fuente) {
    Validator.clearForm('tasaForm');
    document.getElementById('tasaId').value = id;
    document.getElementById('fecha').value = formatIsoDate(fecha);
    document.getElementById('monto').value = monto;
    document.getElementById('fuente').value = fuente;
    document.getElementById('modalTitle').textContent = 'Modificar Tasa';
    new bootstrap.Modal(document.getElementById('tasaModal')).show();
    Validator.initTracking('tasaForm');
}

function saveData() {
    if (!Validator.validate('tasaForm')) return showToast('Corrija los errores', 'warning');
    const id = document.getElementById('tasaId').value;
    const data = {
        fecha: document.getElementById('fecha').value,
        monto: parseFloat(document.getElementById('monto').value),
        fuente: document.getElementById('fuente').value
    };
    const url = id ? `/api/tasas/${id}` : '/api/tasas/';
    const method = id ? 'PUT' : 'POST';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('tasaForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('tasaModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function deleteData(id) {
    confirmAction('¿Estás seguro de que deseas eliminar esta tasa?', () => {
        apiCall(`/api/tasas/${id}`, 'DELETE').then(res => { showToast(res.message); loadData(); });
    });
}

function syncScraping() {
    showToast('Sincronizando con BCV...', 'info');
    apiCall('/api/tasas/sync-scraping', 'POST').then(res => {
        showToast(res.message, res.status === 'success' ? 'success' : 'error');
        loadData();
    });
}
