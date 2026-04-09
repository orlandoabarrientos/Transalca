$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="promotions"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadPromos();
    loadCards();
    Validator.setRules('promoForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'Nombre requerido' },
        tipo: { required: true, requiredMsg: 'Seleccione tipo' },
        puntos_requeridos: { required: true, min: 1, requiredMsg: 'Puntos requeridos', minMsg: 'Minimo 1' }
    });
    Validator.setupRealtime('promoForm');
});

function loadPromos() {
    apiCall('/api/promotions/').then(res => {
        const tbody = document.getElementById('promoBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${p.id}</td>
                <td><strong>${p.nombre}</strong></td>
                <td><span class="badge-status badge-info">${p.tipo}</span></td>
                <td>${p.puntos_requeridos}</td>
                <td>${p.recompensa || '-'}</td>
                <td>${statusBadge(p.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${p.id})"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="deletePromo(${p.id})"><i class="bi bi-pause-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-gift"></i><p>Sin promociones</p></div></td></tr>';
    });
}

function loadCards() {
    apiCall('/api/promotions/cards').then(res => {
        const tbody = document.getElementById('cardsBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(c => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${c.id}</td>
                <td>${c.cliente_nombre || 'N/A'}</td>
                <td>${c.promo_nombre || 'N/A'}</td>
                <td>${c.puntos_acumulados}/${c.puntos_requeridos}</td>
                <td>${c.canjeada ? '<span class="badge-status badge-active">Si</span>' : '<span class="badge-status badge-pending">No</span>'}</td>
                <td>${!c.canjeada ? `<button class="btn btn-sm btn-outline-orange" onclick="addPoint(${c.id})"><i class="bi bi-plus-circle me-1"></i>+1 Punto</button>` : ''}</td>
            </tr>`;
        });
        if (!res.data?.length) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-credit-card"></i><p>Sin tarjetas</p></div></td></tr>';
    });
}

function openModal() { Validator.clearForm('promoForm'); document.getElementById('promoId').value = ''; document.getElementById('modalTitle').textContent = 'Nueva Promocion'; new bootstrap.Modal(document.getElementById('promoModal')).show(); }

function editData(id) {
    apiCall(`/api/promotions/${id}`).then(res => {
        const p = res.data;
        document.getElementById('promoId').value = p.id;
        document.getElementById('nombre').value = p.nombre;
        document.getElementById('descripcion').value = p.descripcion || '';
        document.getElementById('tipo').value = p.tipo;
        document.getElementById('puntos_requeridos').value = p.puntos_requeridos;
        document.getElementById('recompensa').value = p.recompensa || '';
        document.getElementById('modalTitle').textContent = 'Editar Promocion';
        new bootstrap.Modal(document.getElementById('promoModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('promoForm')) return showToast('Corrija los errores','warning');
    const id = document.getElementById('promoId').value;
    const data = { nombre: document.getElementById('nombre').value, descripcion: document.getElementById('descripcion').value, tipo: document.getElementById('tipo').value, puntos_requeridos: parseInt(document.getElementById('puntos_requeridos').value), recompensa: document.getElementById('recompensa').value };
    const url = id ? `/api/promotions/${id}` : '/api/promotions/';
    apiCall(url, id ? 'PUT' : 'POST', data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('promoForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('promoModal')).hide();
        showToast(res.message); loadPromos();
    });
}

function deletePromo(id) { confirmAction('¿Desactivar promocion?', () => { apiCall(`/api/promotions/${id}`, 'DELETE').then(res => { showToast(res.message); loadPromos(); }); }); }

function addPoint(cardId) { apiCall(`/api/promotions/cards/${cardId}/add-point`, 'POST', { descripcion: 'Punto manual' }).then(res => { if (res.status === 'error') return showToast(res.message, 'error'); showToast('Punto agregado'); loadCards(); }); }
