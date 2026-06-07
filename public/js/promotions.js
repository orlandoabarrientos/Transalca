$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="promotions"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadPromos();
    loadCards();
    Validator.setRules('promoForm', {
        nombre: { required: true, minLength: 3, maxLength: 50, requiredMsg: 'El nombre es obligatorio', minLengthMsg: 'El nombre debe tener al menos 3 caracteres', maxLengthMsg: 'El nombre no puede superar los 50 caracteres.' },
        recompensa: { maxLength: 100, maxLengthMsg: 'La recompensa no puede superar los 100 caracteres.' },
        tipo: { required: true, requiredMsg: 'El tipo de promoción es obligatorio' },
        puntos_requeridos: { required: true, min: 1, requiredMsg: 'Los puntos son obligatorios', minMsg: 'Los puntos deben ser mayores a 0' },
        fecha_inicio: {
            custom: v => {
                if (!v) return true;
                return /^\d{4}-\d{2}-\d{2}$/.test(v);
            },
            customMsg: 'Fecha de inicio inválida'
        },
        fecha_fin: {
            custom: v => {
                if (!v) return true;
                if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
                const start = $('#fecha_inicio').val();
                if (!start) return true;
                return v >= start;
            },
            customMsg: 'La fecha de fin no puede ser anterior a la fecha de inicio'
        }
    });
    Validator.setupRealtime('promoForm');
    $('#fecha_inicio').on('change input', () => {
        Validator.validateField('promoForm', 'fecha_fin');
    });
    bindModalValidationReset();
    document.getElementById('imagen_tarjeta')?.addEventListener('change', onPromoImageSelected);

    let checkTimeout = null;
    const nameInput = document.getElementById('nombre');
    if (nameInput) {
        nameInput.addEventListener('input', () => {
            clearTimeout(checkTimeout);
            const val = nameInput.value.trim();
            const exclude = document.getElementById('promoId').value.trim();
            if (val.length < 3) return;
            checkTimeout = setTimeout(() => {
                fetch(`/api/promotions/check-unique?value=${encodeURIComponent(val)}&exclude=${encodeURIComponent(exclude)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'success' && !data.unique) {
                            nameInput.dataset.externalError = 'La promoción ya existe';
                            setFieldError(nameInput, 'La promoción ya existe');
                        } else {
                            delete nameInput.dataset.externalError;
                            if (nameInput.classList.contains('is-invalid') && getFieldFeedback(nameInput).textContent === 'La promoción ya existe') {
                                clearFieldError(nameInput);
                                nameInput.classList.add('is-valid');
                            }
                        }
                        updateFormSubmitState('promoForm');
                    });
            }, 350);
        });
    }
});

let promoPaginator = null;
let cardsPaginator = null;

function loadPromos() {
    apiCall('/api/promotions/').then(res => {
        if (!promoPaginator) {
            promoPaginator = new TablePaginator('promoBody', {
                allData: res.data || [],
                itemName: 'promociones',
                renderRow: (p) => `<tr class="fade-in-up">
                    <td class="col-id">${escapeHtml(p.id)}</td>
                    <td><strong>${escapeHtml(p.nombre)}</strong></td>
                    <td><span class="badge-status badge-info">${escapeHtml(p.tipo)}</span></td>
                    <td>${escapeHtml(p.puntos_requeridos)}</td>
                    <td>${escapeHtml(p.recompensa || '-')}</td>
                    <td>
                        <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${Number(p.id)})" title="Modificar Promoción"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-icon btn-sm btn-warning" onclick="deletePromo(${Number(p.id)})" title="Eliminar Promoción"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`,
                onEmpty: () => '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-gift"></i><p>No hay promociones registradas</p></div></td></tr>'
            });
        } else {
            promoPaginator.updateData(res.data || []);
        }
    });
}

function loadCards() {
    apiCall('/api/promotions/cards').then(res => {
        if (!res.data?.length) {
            const container = document.getElementById('cardsBody');
            if (container) loadPromotionCardTemplates(container);
            return;
        }
        if (!cardsPaginator) {
            cardsPaginator = new TablePaginator('cardsBody', {
                allData: res.data || [],
                itemName: 'tarjetas',
                renderRow: (c) => {
                    const accumulated = c.puntos_acumulados || 0;
                    const required = c.puntos_requeridos || 0;

                    let slotsHtml = '<div class="punch-card-grid">';
                    for (let i = 1; i <= required; i++) {
                        const isReward = (i === required);
                        const isFilled = (i <= accumulated);

                        let slotClass = 'punch-slot';
                        if (isReward) slotClass += ' reward-slot';
                        if (isFilled) slotClass += ' filled';

                        let slotContent = '';
                        if (isReward) {
                            slotContent = isFilled ? '<i class="bi bi-gift-fill"></i>' : '<i class="bi bi-gift"></i>';
                        } else {
                            slotContent = i;
                        }

                        slotsHtml += `<div class="${slotClass}">${slotContent}</div>`;
                    }
                    slotsHtml += '</div>';

                    const bg = getCardBackground(c.imagen_tarjeta);
                    const cardNum = formatCardNumber(c.id);
                    const statusClass = c.canjeada ? 'redeemed-badge' : 'active-badge';
                    const statusText = c.canjeada ? 'Canjeada' : 'Activa';
                    const completedAlertHtml = buildCompletedPromoAlert(c, accumulated, required);

                    return `<div class="loyalty-card-wrapper fade-in-up">
                        <div class="fidelity-card-physical" style="background: ${bg};">
                            <div class="card-meta-row">
                                <span class="card-brand-logo">TRANSALCA</span>
                                <span class="card-status-badge ${statusClass}">${statusText}</span>
                            </div>
                            <div class="card-meta-row mt-2">
                                <div class="card-chip-gold"></div>
                                <i class="bi bi-wifi card-contactless"></i>
                            </div>
                            <div class="card-number-display">${cardNum}</div>
                            <div class="card-holder-row">
                                <div>
                                    <div class="card-holder-name">${escapeHtml(c.cliente_nombre || 'N/A')}</div>
                                    <div class="card-holder-cedula">C.I. ${escapeHtml(c.cliente_cedula_display || c.cliente_cedula || '-')}</div>
                                </div>
                            </div>
                        </div>

                        <div class="card-stamps-panel">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <strong class="text-orange fs-6" style="font-weight:700;">${escapeHtml(c.promo_nombre || 'Promoción')}</strong>
                                <span class="small text-muted" style="font-weight:600;">${accumulated} / ${required} Puntos</span>
                            </div>
                            <p class="small text-muted mb-2">${escapeHtml(c.promo_descripcion || '')}</p>
                            <div class="small mb-2"><strong class="text-orange">Recompensa:</strong> ${escapeHtml(c.recompensa || '-')}</div>
                            ${completedAlertHtml}
                            ${slotsHtml}
                            ${!c.canjeada ? `<button class="btn btn-sm btn-outline-orange w-100 mt-2" onclick="addPoint(${Number(c.id)})"><i class="bi bi-plus-circle me-1"></i>Registrar punto</button>` : ''}
                        </div>
                    </div>`;
                },
                onEmpty: () => '<div class="text-center py-5 w-100"><div class="empty-state"><i class="bi bi-credit-card"></i><p>No hay tarjetas registradas</p></div></div>'
            });
        } else {
            cardsPaginator.updateData(res.data || []);
        }
    });
}

function loadPromotionCardTemplates(container) {
    apiCall('/api/promotions/active').then(res => {
        const promos = res.data || [];
        container.innerHTML = '';
        promos.forEach(p => {
            const required = p.puntos_requeridos || 5;
            let slotsHtml = '<div class="punch-card-grid">';
            for (let i = 1; i <= required; i++) {
                const isReward = (i === required);
                let slotClass = 'punch-slot';
                if (isReward) slotClass += ' reward-slot';
                slotsHtml += `<div class="${slotClass}">${isReward ? '<i class="bi bi-gift"></i>' : i}</div>`;
            }
            slotsHtml += '</div>';

            const bg = getCardBackground(p.imagen_tarjeta);
            const cardNum = formatCardNumber(0);

            container.innerHTML += `<div class="loyalty-card-wrapper fade-in-up">
                <div class="fidelity-card-physical" style="background: ${bg};">
                    <div class="card-meta-row">
                        <span class="card-brand-logo">TRANSALCA</span>
                        <span class="card-status-badge template-badge">Plantilla</span>
                    </div>
                    <div class="card-meta-row mt-2">
                        <div class="card-chip-gold"></div>
                        <i class="bi bi-wifi card-contactless"></i>
                    </div>
                    <div class="card-number-display">${cardNum}</div>
                    <div class="card-holder-row">
                        <div>
                            <div class="card-holder-name">CLIENTE DE PRUEBA</div>
                            <div class="card-holder-cedula">C.I. V-00000000</div>
                        </div>
                    </div>
                </div>

                <div class="card-stamps-panel">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong class="text-orange fs-6" style="font-weight:700;">${escapeHtml(p.nombre || 'Promoción')}</strong>
                        <span class="small text-muted" style="font-weight:600;">0 / ${required} Puntos</span>
                    </div>
                    <p class="small text-muted mb-2">${escapeHtml(p.descripcion || '')}</p>
                    <div class="small mb-2"><strong class="text-orange">Recompensa:</strong> ${escapeHtml(p.recompensa || '-')}</div>
                    ${slotsHtml}
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
    document.getElementById('modalTitle').textContent = 'Registrar Promoción';
    document.getElementById('nombre').value = '';
    document.getElementById('descripcion').value = '';
    document.getElementById('tipo').value = '';
    document.getElementById('puntos_requeridos').value = 5;
    document.getElementById('recompensa').value = '';
    document.getElementById('fecha_inicio').value = '';
    document.getElementById('fecha_fin').value = '';
    document.getElementById('imagen_tarjeta').value = '';
    setPromoPreview('');
    new bootstrap.Modal(document.getElementById('promoModal')).show();
    Validator.initTracking('promoForm');
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
        document.getElementById('modalTitle').textContent = 'Modificar Promoción';
        new bootstrap.Modal(document.getElementById('promoModal')).show();
        Validator.initTracking('promoForm');
    });
}

function saveData() {
    if (!Validator.validate('promoForm')) {
        updateFormSubmitState('promoForm');
        return showToast('Corrija los errores del formulario', 'warning');
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
            showToast(message || 'No se pudo subir la imagen', 'error');
        });
    }).finally(() => {
        setButtonLoading(button, false);
    });
}

function deletePromo(id) {
    confirmAction('¿Estás seguro de que deseas eliminar esta promoción?', () => {
        apiCall(`/api/promotions/${id}`, 'DELETE').then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message, 'success');
            loadPromos();
            loadCards();
        });
    });
}

function addPoint(cardId) {
    apiCall(`/api/promotions/cards/${cardId}/add-point`, 'POST', { descripcion: 'Punto registrado' }).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        showToast(res.message || 'Punto registrado correctamente', 'success');
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
        return showToast('El archivo debe ser una imagen png, jpg, jpeg o webp', 'warning');
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
            return Promise.reject(data.message || 'No se pudo subir la imagen');
        }
        return data;
    }).catch(() => {
        return Promise.reject('No se pudo subir la imagen');
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
