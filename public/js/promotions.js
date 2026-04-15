$(document).ready(function () {
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
    document.getElementById('imagen_tarjeta')?.addEventListener('change', onPromoImageSelected);
});

function loadPromos() {
    apiCall('/api/promotions/').then(res => {
        const tbody = document.getElementById('promoBody');
        if (!tbody) return;
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
        const container = document.getElementById('cardsBody');
        if (!container) return;
        container.innerHTML = '';
        (res.data || []).forEach(c => {
            const progreso = `${c.puntos_acumulados || 0}/${c.puntos_requeridos || 0}`;
            const cardImg = c.imagen_tarjeta ? `/public/assets/images/${c.imagen_tarjeta}` : '/public/assets/images/default_card.png';
            container.innerHTML += `<div class="promo-fidelity-card fade-in-up">
                <div class="promo-fidelity-head">
                    <strong>${escapeHtml(c.promo_nombre || 'Promocion')}</strong>
                    <span class="badge-status ${c.canjeada ? 'badge-active' : 'badge-pending'}">${c.canjeada ? 'Canjeada' : 'Activa'}</span>
                </div>
                <img src="${cardImg}" class="promo-fidelity-img" alt="Tarjeta" onerror="this.src='/public/assets/images/default_card.png'">
                <div class="promo-fidelity-body">
                    <div class="mb-1"><strong>Cliente:</strong> ${escapeHtml(c.cliente_nombre || 'N/A')}</div>
                    <div class="mb-1"><strong>Cedula:</strong> ${escapeHtml(c.cliente_cedula_display || c.cliente_cedula || '-')}</div>
                    <div class="mb-1"><strong>Tipo:</strong> ${escapeHtml(c.tipo || '-')}</div>
                    <div class="mb-1"><strong>Puntos:</strong> ${progreso}</div>
                    <div class="mb-1"><strong>Recompensa:</strong> ${escapeHtml(c.recompensa || '-')}</div>
                    <div class="mb-2 text-muted">${escapeHtml(c.promo_descripcion || '')}</div>
                    ${!c.canjeada ? `<button class="btn btn-sm btn-outline-orange" onclick="addPoint(${c.id})"><i class="bi bi-plus-circle me-1"></i>+1 Punto</button>` : ''}
                </div>
            </div>`;
        });
        if (!res.data?.length) container.innerHTML = '<div class="text-center py-5 w-100"><div class="empty-state"><i class="bi bi-credit-card"></i><p>Sin tarjetas</p></div></div>';
    });
}

function openModal() {
    Validator.clearForm('promoForm');
    document.getElementById('promoId').value = '';
    document.getElementById('modalTitle').textContent = 'Nueva Promocion';
    document.getElementById('nombre').value = '';
    document.getElementById('descripcion').value = '';
    document.getElementById('tipo').value = 'puntos';
    document.getElementById('puntos_requeridos').value = 5;
    document.getElementById('recompensa').value = '';
    document.getElementById('fecha_inicio').value = '';
    document.getElementById('fecha_fin').value = '';
    document.getElementById('imagen_tarjeta').value = '';
    setPromoPreview('');
    new bootstrap.Modal(document.getElementById('promoModal')).show();
}

function editData(id) {
    apiCall(`/api/promotions/${id}`).then(res => {
        const p = res.data;
        document.getElementById('promoId').value = p.id;
        document.getElementById('nombre').value = p.nombre;
        document.getElementById('descripcion').value = p.descripcion || '';
        document.getElementById('tipo').value = p.tipo;
        document.getElementById('puntos_requeridos').value = p.puntos_requeridos;
        document.getElementById('recompensa').value = p.recompensa || '';
        document.getElementById('fecha_inicio').value = normalizeDateInput(p.fecha_inicio);
        document.getElementById('fecha_fin').value = normalizeDateInput(p.fecha_fin);
        document.getElementById('imagen_tarjeta').value = '';
        setPromoPreview(p.imagen_tarjeta ? `/public/assets/images/${p.imagen_tarjeta}` : '');
        document.getElementById('modalTitle').textContent = 'Editar Promocion';
        new bootstrap.Modal(document.getElementById('promoModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('promoForm')) return showToast('Corrija los errores', 'warning');
    const id = document.getElementById('promoId').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        tipo: document.getElementById('tipo').value,
        puntos_requeridos: parseInt(document.getElementById('puntos_requeridos').value),
        recompensa: document.getElementById('recompensa').value,
        fecha_inicio: document.getElementById('fecha_inicio').value || null,
        fecha_fin: document.getElementById('fecha_fin').value || null
    };
    const url = id ? `/api/promotions/${id}` : '/api/promotions/';
    apiCall(url, id ? 'PUT' : 'POST', data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('promoForm', res.errors); return showToast(res.message, 'error'); }
        const promoId = id || res.id;
        uploadPromoImageIfNeeded(promoId).then(() => {
            bootstrap.Modal.getInstance(document.getElementById('promoModal')).hide();
            showToast(res.message);
            loadPromos();
            loadCards();
        });
    });
}

function deletePromo(id) { confirmAction('¿Desactivar promocion?', () => { apiCall(`/api/promotions/${id}`, 'DELETE').then(res => { showToast(res.message); loadPromos(); }); }); }

function addPoint(cardId) { apiCall(`/api/promotions/cards/${cardId}/add-point`, 'POST', { descripcion: 'Punto manual' }).then(res => { if (res.status === 'error') return showToast(res.message, 'error'); showToast('Punto agregado'); loadCards(); }); }

function onPromoImageSelected(e) {
    const file = e?.target?.files?.[0];
    if (!file) {
        setPromoPreview('');
        return;
    }
    const reader = new FileReader();
    reader.onload = function (evt) {
        setPromoPreview(evt?.target?.result || '');
    };
    reader.readAsDataURL(file);
}

function setPromoPreview(src) {
    const img = document.getElementById('promoImagePreview');
    if (!img) return;
    if (!src) {
        img.style.display = 'none';
        img.src = '';
        return;
    }
    img.src = src;
    img.style.display = '';
}

function uploadPromoImageIfNeeded(promoId) {
    const fileInput = document.getElementById('imagen_tarjeta');
    const file = fileInput?.files?.[0];
    if (!file || !promoId) return Promise.resolve();

    const formData = new FormData();
    formData.append('image', file);

    return fetch(`/api/promotions/${promoId}/image`, {
        method: 'POST',
        credentials: 'same-origin',
        body: formData
    }).then(r => r.json()).then(data => {
        if (data.status === 'error') {
            showToast(data.message || 'No se pudo subir la imagen', 'warning');
        }
    }).catch(() => {
        showToast('No se pudo subir la imagen', 'warning');
    });
}

function normalizeDateInput(value) {
    if (!value) return '';
    const txt = String(value);
    if (txt.length >= 10) return txt.substring(0, 10);
    return '';
}

function escapeHtml(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
