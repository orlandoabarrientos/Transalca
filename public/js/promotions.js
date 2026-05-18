$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="promotions"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadPromos();
    loadCards();
    Validator.setRules('promoForm', {
        nombre: { required: true, minLength: 3, requiredMsg: 'El nombre es obligatorio.', minLengthMsg: 'El nombre debe tener al menos 3 caracteres.' },
        tipo: { required: true, allowed: ['puntos', 'descuento', 'gratis'], requiredMsg: 'Seleccione un tipo valido.' },
        puntos_requeridos: { required: true, min: 1, requiredMsg: 'Los puntos son obligatorios.', minMsg: 'Los puntos deben ser mayores a 0.' }
    });
    Validator.setupRealtime('promoForm');
    bindModalValidationReset();
    document.getElementById('imagen_tarjeta')?.addEventListener('change', onPromoImageSelected);
});

function loadPromos() {
    apiCall('/api/promotions/').then(res => {
        const tbody = document.getElementById('promoBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td class="col-id">${escapeHtml(p.id)}</td>
                <td><strong>${escapeHtml(p.nombre)}</strong></td>
                <td><span class="badge-status badge-info">${escapeHtml(p.tipo)}</span></td>
                <td>${escapeHtml(p.puntos_requeridos)}</td>
                <td>${escapeHtml(p.recompensa || '-')}</td>
                <td>${statusBadge(p.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${Number(p.id)})" title="Modificar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="deletePromo(${Number(p.id)})" title="Eliminar"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-gift"></i><p>No hay promociones registradas</p></div></td></tr>';
        }
    });
}

function loadCards() {
    apiCall('/api/promotions/cards').then(res => {
        const container = document.getElementById('cardsBody');
        if (!container) return;
        container.innerHTML = '';
        (res.data || []).forEach(c => {
            const progreso = `${c.puntos_acumulados || 0}/${c.puntos_requeridos || 0}`;
            const cardImg = c.imagen_tarjeta ? `/public/assets/images/${encodeURIComponent(c.imagen_tarjeta)}` : '/public/assets/images/default_card.png';
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
                    <div class="mb-1"><strong>Puntos:</strong> ${escapeHtml(progreso)}</div>
                    <div class="mb-1"><strong>Recompensa:</strong> ${escapeHtml(c.recompensa || '-')}</div>
                    <div class="mb-2 text-muted">${escapeHtml(c.promo_descripcion || '')}</div>
                    ${!c.canjeada ? `<button class="btn btn-sm btn-outline-orange" onclick="addPoint(${Number(c.id)})"><i class="bi bi-plus-circle me-1"></i>Registrar punto</button>` : ''}
                </div>
            </div>`;
        });
        if (!res.data?.length) {
            loadPromotionCardTemplates(container);
        }
    });
}

function loadPromotionCardTemplates(container) {
    apiCall('/api/promotions/active').then(res => {
        const promos = res.data || [];
        container.innerHTML = '';
        promos.forEach(p => {
            const cardImg = p.imagen_tarjeta ? `/public/assets/images/${encodeURIComponent(p.imagen_tarjeta)}` : '/public/assets/images/default_card.png';
            container.innerHTML += `<div class="promo-fidelity-card fade-in-up">
                <div class="promo-fidelity-head">
                    <strong>${escapeHtml(p.nombre || 'Promocion')}</strong>
                    <span class="badge-status badge-info">Plantilla</span>
                </div>
                <img src="${cardImg}" class="promo-fidelity-img" alt="Tarjeta" onerror="this.src='/public/assets/images/default_card.png'">
                <div class="promo-fidelity-body">
                    <div class="mb-1"><strong>Tipo:</strong> ${escapeHtml(p.tipo || '-')}</div>
                    <div class="mb-1"><strong>Puntos:</strong> ${escapeHtml(p.puntos_requeridos || 0)}</div>
                    <div class="mb-1"><strong>Recompensa:</strong> ${escapeHtml(p.recompensa || '-')}</div>
                    <div class="mb-2 text-muted">${escapeHtml(p.descripcion || '')}</div>
                </div>
            </div>`;
        });
        if (!promos.length) {
            container.innerHTML = '<div class="text-center py-5 w-100"><div class="empty-state"><i class="bi bi-credit-card"></i><p>No hay tarjetas registradas</p></div></div>';
        }
    });
}

function openModal() {
    Validator.clearForm('promoForm');
    document.getElementById('promoId').value = '';
    document.getElementById('modalTitle').textContent = 'Nueva promocion';
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
        if (res.status === 'error') return showToast(res.message, 'error');
        const p = res.data;
        Validator.clearForm('promoForm');
        document.getElementById('promoId').value = p.id;
        document.getElementById('nombre').value = p.nombre || '';
        document.getElementById('descripcion').value = p.descripcion || '';
        document.getElementById('tipo').value = p.tipo || 'puntos';
        document.getElementById('puntos_requeridos').value = p.puntos_requeridos || 1;
        document.getElementById('recompensa').value = p.recompensa || '';
        document.getElementById('fecha_inicio').value = normalizeDateInput(p.fecha_inicio);
        document.getElementById('fecha_fin').value = normalizeDateInput(p.fecha_fin);
        document.getElementById('imagen_tarjeta').value = '';
        setPromoPreview(p.imagen_tarjeta ? `/public/assets/images/${encodeURIComponent(p.imagen_tarjeta)}` : '');
        document.getElementById('modalTitle').textContent = 'Modificar promocion';
        new bootstrap.Modal(document.getElementById('promoModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('promoForm')) {
        updateFormSubmitState('promoForm');
        return showToast('Corrija los errores del formulario.', 'warning');
    }
    const id = document.getElementById('promoId').value;
    const button = document.getElementById('btnSavePromo');
    const data = {
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        tipo: document.getElementById('tipo').value,
        puntos_requeridos: document.getElementById('puntos_requeridos').value,
        recompensa: document.getElementById('recompensa').value,
        fecha_inicio: document.getElementById('fecha_inicio').value || null,
        fecha_fin: document.getElementById('fecha_fin').value || null
    };
    const url = id ? `/api/promotions/${id}` : '/api/promotions/';
    setButtonLoading(button, true, 'Guardando');
    apiCall(url, id ? 'PUT' : 'POST', data).then(res => {
        if (res.status === 'error') {
            Validator.showServerErrors('promoForm', res.errors);
            updateFormSubmitState('promoForm');
            return showToast(res.message, 'error');
        }
        const promoId = id || res.id;
        uploadPromoImageIfNeeded(promoId).then(() => {
            bootstrap.Modal.getInstance(document.getElementById('promoModal'))?.hide();
            showToast(res.message, 'success');
            loadPromos();
            loadCards();
        }).catch(message => {
            showToast(message || 'No se pudo subir la imagen.', 'error');
        });
    }).finally(() => {
        setButtonLoading(button, false);
    });
}

function deletePromo(id) {
    confirmAction('Eliminar esta promocion?', () => {
        apiCall(`/api/promotions/${id}`, 'DELETE').then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message, 'success');
            loadPromos();
            loadCards();
        });
    }, { confirmText: 'Eliminar' });
}

function addPoint(cardId) {
    apiCall(`/api/promotions/cards/${cardId}/add-point`, 'POST', { descripcion: 'Punto registrado' }).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        showToast(res.message || 'Punto registrado correctamente.', 'success');
        loadCards();
    });
}

function onPromoImageSelected(e) {
    const file = e?.target?.files?.[0];
    if (!file) {
        setPromoPreview('');
        return;
    }
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
        e.target.value = '';
        setPromoPreview('');
        return showToast('El archivo debe ser una imagen png, jpg, jpeg o webp.', 'warning');
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
            return Promise.reject(data.message || 'No se pudo subir la imagen.');
        }
        return data;
    }).catch(() => {
        return Promise.reject('No se pudo subir la imagen.');
    });
}

function normalizeDateInput(value) {
    if (!value) return '';
    const txt = String(value);
    if (txt.length >= 10) return txt.substring(0, 10);
    return '';
}

function escapeHtml(text) {
    return String(text ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
