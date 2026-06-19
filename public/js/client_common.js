
let currentUser = null;
let clientNotificationsReady = false;
let clientKnownNotificationIds = new Set();

function showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast-custom ${type}`;
    const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
    const colors = { success: 'var(--success)', error: 'var(--danger)', warning: 'var(--warning)', info: 'var(--info)' };
    const text = typeof normalizeSystemMessage === 'function' ? normalizeSystemMessage(message) : String(message || '');
    const safe = typeof escapeHtml === 'function' ? escapeHtml(text) : text;
    toast.innerHTML = `<i class="bi ${icons[type] || icons.info}" style="color:${colors[type]};font-size:1.3rem;"></i><span style="flex:1;font-weight:500;font-size:0.85rem;">${safe}</span><button type="button" class="toast-close close-toast" aria-label="Cerrar"><i class="bi bi-x"></i></button>`;
    toast.querySelector('.toast-close')?.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        dismissToast(toast);
    });
    container.appendChild(toast);
    setTimeout(() => {
        if (typeof dismissToast === 'function') dismissToast(toast);
        else toast.remove();
    }, 5000);
}

async function checkSession() {
    try {
        const res = await fetch('/auth/session', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success') {
            currentUser = data.user;
            updateNavForUser();
            updateCartBadge();
            return true;
        }
        updateNavForGuest();
        return false;
    } catch (e) {
        updateNavForGuest();
        return false;
    }
}

function updateNavForUser() {
    if (!currentUser) return;
    const photo = document.getElementById('clientNavPhoto');
    const hasCustomPhoto = !!currentUser.foto && currentUser.foto !== 'default.png';
    if (photo) {
        photo.src = `/public/assets/profile_pics/${currentUser.foto || 'default.png'}`;
        photo.style.display = hasCustomPhoto ? '' : 'none';
    }
    document.querySelectorAll('.client-profile-fallback').forEach(el => {
        el.style.display = hasCustomPhoto ? 'none' : '';
    });
    document.querySelectorAll('.auth-required').forEach(el => el.style.display = '');
    document.querySelectorAll('.guest-only').forEach(el => el.style.display = 'none');
    const adminBtn = document.getElementById('navAdminBtn');
    if (adminBtn) {
        adminBtn.style.display = (['empleado', 'admin', 'vendedor', 'mecanico', 'soporte'].includes(currentUser.tipo)) ? '' : 'none';
    }
    document.querySelectorAll('.client-only-qr').forEach(el => {
        el.style.display = (currentUser.tipo === 'cliente') ? '' : 'none';
    });
}

function updateNavForGuest() {
    clientNotificationsReady = false;
    clientKnownNotificationIds.clear();
    document.querySelectorAll('.auth-required').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.guest-only').forEach(el => el.style.display = '');
}

function applyAuthVisibility() {
    if (currentUser) updateNavForUser();
    else updateNavForGuest();
}

async function updateCartBadge() {
    if (!currentUser) return;
    try {
        const res = await fetch('/api/orders/cart/count', { credentials: 'same-origin' });
        const data = await res.json();
        const badge = document.getElementById('cartBadge');
        if (badge) {
            badge.textContent = data.count || 0;
            badge.style.display = data.count > 0 ? '' : 'none';
        }
    } catch (e) {  }
}

async function addToCart(itemId, tipo = 'producto', cantidad = 1) {
    if (!currentUser) {
        showToast('Debe iniciar sesion para agregar al carrito.', 'warning');
        setTimeout(() => window.location.href = '/auth/login', 1500);
        return;
    }
    try {
        const res = await fetch('/api/orders/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ item_id: itemId, tipo, cantidad })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Producto agregado al carrito correctamente.', 'success');
            updateCartBadge();
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Error de conexion', 'error');
    }
}

function normalizeProductText(value) {
    return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
}

function hasExplicitProductImage(product) {
    const image = String(product?.imagen || '').trim();
    return !!image && image !== 'default_product.png' && image !== 'no-image.png';
}

function getProductDefaultImageName(product = {}) {
    const text = normalizeProductText([
        product.categoria_nombre,
        product.categoria,
        product.tipo,
        product.nombre,
        product.descripcion,
        product.marca_nombre,
        product.marca
    ].filter(Boolean).join(' '));

    const rules = [
        { image: 'product-default-battery.png', terms: ['bateria', 'battery', 'amp', 'duracell', 'moura'] },
        { image: 'product-default-lubricant.png', terms: ['lubricante', 'aceite', 'oil', '10w', '15w', '20w', '5w', 'sintetico', 'valvoline', 'mobil'] },
        { image: 'product-default-filter.png', terms: ['filtro', 'filter'] },
        { image: 'product-default-tire.png', terms: ['caucho', 'llanta', 'neumatico', 'rin', 'r13', 'r14', 'r15', 'r16', 'r17', 'r18', 'r19', 'pirelli', 'bridgestone', 'goodyear'] }
    ];

    const match = rules.find(rule => rule.terms.some(term => text.includes(term)));
    return match ? match.image : 'product-default-parts.png';
}

function getProductImageName(product = {}) {
    if (hasExplicitProductImage(product)) {
        return String(product.imagen).trim();
    }
    const catImg = String(product.categoria_imagen || product.imagen_categoria || '').trim();
    if (catImg && catImg !== 'product-default-parts.png' && catImg !== 'no-image.png' && catImg !== 'default_product.png') {
        return catImg;
    }
    return getProductDefaultImageName(product);
}

function getProductImageSrc(product = {}) {
    const name = getProductImageName(product);
    if (hasExplicitProductImage(product)) {
        return `/public/assets/product_imgs/${encodeURIComponent(name)}`;
    }
    return `/public/assets/images/${encodeURIComponent(name)}`;
}

function buildProductImageHtml(product = {}, altText = '') {
    const imageName = getProductImageName(product);
    const src = getProductImageSrc(product);
    const isDefault = !hasExplicitProductImage(product) && !(product.categoria_imagen || product.imagen_categoria);
    const fallback = '/public/assets/images/product-default-parts.png';
    const classes = isDefault ? ' class="product-default-image"' : '';
    return `<img src="${src}" alt="${escapeHtml(altText || product.nombre || 'Producto')}"${classes} data-product-fallback="${fallback}" onerror="handleProductImageError(this)">`;
}

function handleProductImageError(img) {
    if (!img) return;
    const fallback = img.dataset.productFallback || '/public/assets/images/product-default-parts.png';
    if (img.src.indexOf(fallback) === -1 && img.dataset.fallbackApplied !== '1') {
        img.dataset.fallbackApplied = '1';
        img.classList.add('product-default-image');
        img.src = fallback;
        return;
    }
    if (img.parentElement) {
        img.parentElement.innerHTML = '<div class="no-image"><i class="bi bi-image"></i><span>Sin imagen</span></div>';
    }
}

function formatCurrency(amount) {
    return parseFloat(amount || 0).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function installClientListSearches(root = document) {
    const scope = root instanceof Element ? root : document;
    scope.querySelectorAll('table').forEach((table, index) => {
        if (table.dataset.clientAutoSearchReady === '1' || table.closest('.modal')) return;
        const card = table.closest('.card') || table.parentElement;
        if (!card || card.querySelector('.auto-table-search-wrap')) return;
        const manualSearch = card.querySelector('input[id*="search" i], input[name*="search" i], [data-table-search]') || card.previousElementSibling?.querySelector?.('input[id*="search" i], input[name*="search" i], [data-table-search]');
        if (manualSearch) {
            table.dataset.clientAutoSearchReady = '1';
            return;
        }
        const wrap = document.createElement('div');
        wrap.className = 'auto-table-search-wrap d-flex justify-content-end mb-3';
        const input = document.createElement('input');
        input.type = 'search';
        input.className = 'form-control auto-table-search';
        input.placeholder = 'Buscar...';
        input.setAttribute('aria-label', 'Buscar en la lista');
        input.dataset.tableSearch = `client-auto-${index}`;
        wrap.appendChild(input);
        card.parentNode.insertBefore(wrap, card);
        input.addEventListener('input', () => {
            const term = input.value.trim().toLowerCase();
            table.querySelectorAll('tbody tr').forEach(row => {
                row.style.display = !term || row.textContent.toLowerCase().includes(term) ? '' : 'none';
            });
        });
        table.dataset.clientAutoSearchReady = '1';
    });
}

function normalizeActionButtons(root = document) {
    const scope = root instanceof Element ? root : document;
    scope.querySelectorAll('button.btn, a.btn').forEach(btn => {
        const text = (btn.textContent || '').trim().toLowerCase();
        const title = (btn.getAttribute('title') || '').trim().toLowerCase();
        const label = `${text} ${title}`;
        let action = '';
        if (label.includes('registrar')) action = 'register';
        else if (label.includes('modificar') || label.includes('editar')) action = 'edit';
        else if (label.includes('eliminar')) action = 'delete';
        if (!action) return;
        btn.classList.remove('btn-orange', 'btn-outline-orange', 'btn-warning', 'btn-outline-warning', 'btn-danger', 'btn-outline-danger', 'btn-success', 'btn-outline-success');
        const icon = btn.querySelector('i.bi');
        if (action === 'register') {
            btn.classList.add('btn-success');
            if (icon) icon.className = 'bi bi-plus-circle me-1';
        } else if (action === 'edit') {
            btn.classList.add('btn-warning');
            if (icon) icon.className = 'bi bi-pencil-square';
        } else if (action === 'delete') {
            btn.classList.add('btn-danger');
            if (icon) icon.className = 'bi bi-trash';
        }
    });
}

const CLIENT_SELECT_TAMPER_MESSAGE = 'El valor seleccionado no es válido o fue modificado. Recargue la página e intente nuevamente.';

function clientSelectFeedback(select) {
    let feedback = select.parentNode ? select.parentNode.querySelector('.invalid-feedback') : null;
    if (!feedback && select.parentNode) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        select.parentNode.appendChild(feedback);
    }
    return feedback;
}

function validateClientSelect(select) {
    if (!select || select.tagName !== 'SELECT' || select.disabled) return true;
    const allowed = Array.from(select.options || []).map(opt => opt.value);
    const required = select.required || select.dataset.required === 'true';
    const value = (select.value || '').trim();
    const feedback = clientSelectFeedback(select);
    let message = '';
    if (!value) {
        if (required) message = 'Debe seleccionar una opción.';
    } else if (!allowed.includes(value)) {
        message = CLIENT_SELECT_TAMPER_MESSAGE;
    }
    if (message) {
        select.classList.add('is-invalid');
        select.classList.remove('is-valid');
        if (feedback) { feedback.textContent = message; feedback.style.display = 'block'; }
        return false;
    }
    select.classList.remove('is-invalid');
    if (value) select.classList.add('is-valid');
    if (feedback) { feedback.textContent = ''; feedback.style.display = 'none'; }
    return true;
}

function updateClientFormSubmitState(form) {
    if (!form) return;
    const invalid = !!form.querySelector('.is-invalid');
    form.querySelectorAll('button[type="submit"], .btn-success, [data-client-submit]').forEach(btn => {
        if (!btn.dataset.loading) btn.disabled = invalid;
    });
}

function bindClientSelectGuards() {
    if (document.body.dataset.clientSelectGuardsBound === '1') return;
    document.body.dataset.clientSelectGuardsBound = '1';
    document.addEventListener('change', event => {
        const select = event.target && event.target.closest ? event.target.closest('select') : null;
        if (!select) return;
        validateClientSelect(select);
        updateClientFormSubmitState(select.closest('form'));
    });
}

const CLIENT_RECORD_TAMPER_MESSAGE = 'El registro seleccionado no es válido. Recargue la página e intente nuevamente.';
const _clientActionOriginalOnclick = new WeakMap();

function snapshotActionButtons(root = document) {
    const scope = root instanceof Element ? root : document;
    const seal = el => {
        if (el && el.nodeType === 1 && el.hasAttribute('onclick') && !_clientActionOriginalOnclick.has(el)) {
            _clientActionOriginalOnclick.set(el, el.getAttribute('onclick'));
        }
    };
    seal(scope);
    scope.querySelectorAll('[onclick]').forEach(seal);
}

function isActionButtonTampered(el) {
    if (!el || !_clientActionOriginalOnclick.has(el)) return false;
    return el.getAttribute('onclick') !== _clientActionOriginalOnclick.get(el);
}

document.addEventListener('click', e => {
    const el = e.target.closest('[onclick]');
    if (el && isActionButtonTampered(el)) {
        e.preventDefault();
        e.stopImmediatePropagation();
        showToast(CLIENT_RECORD_TAMPER_MESSAGE, 'error');
    }
}, true);

document.addEventListener('DOMContentLoaded', () => {
    document.title = 'Transalca Group | La mejor calidad';
    checkSession().then(loggedIn => {
        if (loggedIn) loadClientNotifications();
    });
    loadExchangeRatesCached().then(() => hydrateDualPrices());
    installClientListSearches();
    normalizeActionButtons();
    snapshotActionButtons();
    bindClientSelectGuards();
    updateCurrencyMenuLabel();
    const observer = new MutationObserver((mutations) => {
        applyAuthVisibility();
        const hasNewPrices = mutations.some(m => Array.from(m.addedNodes).some(n => n.nodeType === 1 && (n.hasAttribute('data-usd-price') || n.querySelector('[data-usd-price]'))));
        const hasRatesBar = mutations.some(m => Array.from(m.addedNodes).some(n => n.nodeType === 1 && (n.id === 'rateBcvClient' || n.querySelector?.('#rateBcvClient'))));
        if (hasNewPrices || hasRatesBar) {
            hydrateDualPrices();
        }
        if (mutations.some(m => Array.from(m.addedNodes).some(n => n.nodeType === 1 && (n.matches?.('table') || n.querySelector?.('table'))))) {
            installClientListSearches();
        }
        if (mutations.some(m => Array.from(m.addedNodes).some(n => n.nodeType === 1 && (n.matches?.('button.btn, a.btn') || n.querySelector?.('button.btn, a.btn'))))) {
            normalizeActionButtons();
        }
        if (mutations.some(m => Array.from(m.addedNodes).some(n => n.nodeType === 1 && (n.hasAttribute?.('onclick') || n.querySelector?.('[onclick]'))))) {
            snapshotActionButtons();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

async function loadClientNotifications() {
    try {
        const res = await fetch('/api/notifications/', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status !== 'success') return;
        const list = data.data || [];
        const newPaymentAlerts = list.filter(n => !n.leida && n.tipo === 'pago' && !clientKnownNotificationIds.has(String(n.id)));
        if (clientNotificationsReady && newPaymentAlerts.length) {
            const alert = newPaymentAlerts[0];
            showToast(alert.titulo || alert.mensaje || 'Actualizacion de pago recibida.', alert.prioridad === 'alta' ? 'warning' : 'info');
        }
        clientKnownNotificationIds = new Set(list.map(n => String(n.id)));
        clientNotificationsReady = true;
        const unread = list.filter(n => !n.leida).length;
        const badge = document.getElementById('clientNotifBadge');
        if (badge) { badge.textContent = unread; badge.style.display = unread > 0 ? '' : 'none'; }
        const container = document.getElementById('clientNotifList');
        if (!container) return;
        if (list.length === 0) { container.innerHTML = '<div class="text-center text-muted py-3" style="font-size:0.8rem;">Sin notificaciones</div>'; return; }
        container.innerHTML = list.slice(0, 8).map(n => {
            const bg = n.leida ? '' : 'background:rgba(0,0,0,0.03);';
            const title = escapeHtml(n.titulo || n.mensaje || 'Notificacion');
            const message = escapeHtml(n.mensaje ? String(n.mensaje).substring(0, 80) : '');
            const icon = n.tipo === 'pago' ? 'bi-credit-card' : n.tipo === 'ticket' ? 'bi-life-preserver' : 'bi-bell';
            return `<div class="px-3 py-2 border-bottom d-flex gap-2" style="font-size:0.8rem;cursor:pointer;${bg}" data-client-notification-id="${Number(n.id) || 0}">
                <i class="bi ${icon}" style="color:#ea580c;"></i>
                <div>
                    <div style="font-weight:${n.leida?'400':'600'};">${title}</div>
                    <div class="text-muted" style="font-size:0.7rem;">${message}</div>
                </div>
            </div>`;
        }).join('');
    } catch(e) {}
}

async function markReadClient(id) {
    try { await fetch(`/api/notifications/${id}/read`, { method: 'PUT', credentials: 'same-origin' }); loadClientNotifications(); } catch(e) {}
}

async function markAllReadClient() {
    try { await fetch('/api/notifications/read-all', { method: 'PUT', credentials: 'same-origin' }); loadClientNotifications(); } catch(e) {}
}

setInterval(() => { if (currentUser) loadClientNotifications(); }, 30000);

document.addEventListener('click', async (e) => {
    const closeToast = e.target.closest('.close-toast, .toast-close');
    if (closeToast) {
        e.preventDefault();
        e.stopPropagation();
        dismissToast(closeToast.closest('.toast-custom'));
        return;
    }
    const protectedLink = e.target.closest('a[href="/client/cart"], a[href="/client/my_orders"], a[href="/client/my_loyalty"], a[href="/client/profile"], a[href="/scanner"]');
    if (protectedLink && !currentUser) {
        e.preventDefault();
        showToast('Debe iniciar sesion para continuar.', 'warning');
        const next = protectedLink.getAttribute('href') || '/client/home';
        setTimeout(() => window.location.href = `/auth/login?next=${encodeURIComponent(next)}`, 900);
        return;
    }
    const currencyToggle = e.target.closest('[data-currency-toggle]');
    if (currencyToggle) {
        e.preventDefault();
        toggleCurrency();
        return;
    }
    const markAllClientNotifications = e.target.closest('[data-client-notifications-read-all]');
    if (markAllClientNotifications) {
        e.preventDefault();
        markAllReadClient();
        return;
    }
    const clientNotification = e.target.closest('[data-client-notification-id]');
    if (clientNotification) {
        e.preventDefault();
        const id = Number(clientNotification.dataset.clientNotificationId || 0);
        if (id) markReadClient(id);
        return;
    }
    const logoutTarget = e.target.closest('#clientLogout');
    if (logoutTarget) {
        e.preventDefault();
        await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
        window.location.href = '/client/home';
    }
}, true);

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function normalizeSystemMessage(message) {
    const text = String(message || '').trim();
    if (!text) return 'Operacion procesada.';
    const lower = text.charAt(0).toUpperCase() + text.slice(1);
    return lower.endsWith('.') || lower.endsWith('?') || lower.endsWith('!') ? lower : `${lower}.`;
}

function dismissToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 300);
}

function getSelectedCurrency() {
    const currency = (localStorage.getItem('transalca_currency') || 'USD').toUpperCase();
    return currency === 'VES' ? 'VES' : 'USD';
}

async function setSelectedCurrency(currency) {
    const nextCurrency = currency === 'VES' ? 'VES' : 'USD';
    localStorage.setItem('transalca_currency', nextCurrency);
    updateCurrencyMenuLabel();
    hydrateDualPrices();
    if (nextCurrency === 'VES') await loadExchangeRatesCached(true);
    hydrateDualPrices();
    updateCurrencyMenuLabel();
    if (nextCurrency === 'VES' && !convertUsdToBs(1)) {
        showToast('No se pudo calcular el precio en Bs. Verifique las tasas BCV y USDT.', 'warning');
    }
}

function toggleCurrency() {
    setSelectedCurrency(getSelectedCurrency() === 'USD' ? 'VES' : 'USD');
}

function updateCurrencyMenuLabel() {
    const currency = getSelectedCurrency();
    document.querySelectorAll('[data-currency-toggle-label]').forEach(el => {
        el.textContent = currency === 'USD' ? 'Ver precios en bolivares' : 'Ver precios en dolares';
    });
}

function formatUsdBs(amount) {
    const usd = parseFloat(amount || 0);
    if (getSelectedCurrency() === 'VES') {
        const bs = convertUsdToBs(usd);
        return bs ? `Bs. ${formatCurrency(bs)}` : `$${formatCurrency(usd)}`;
    }
    return `$${formatCurrency(usd)}`;
}

function convertUsdToBs(amount) {
    const rates = window.TransalcaRates || {};
    const bcv = parseFloat(rates.bcv || 0);
    const usdt = parseFloat(rates.usdt || 0);
    if (!bcv || !usdt) return 0;
    const precioDolar = (parseFloat(amount || 0) * usdt) / bcv;
    return precioDolar * bcv;
}

async function loadExchangeRatesCached(force = false) {
    const key = 'transalca_rates_cache_v1';
    const now = Date.now();
    try {
        const cached = JSON.parse(localStorage.getItem(key) || 'null');
        const expiresAt = Date.parse(cached?.expires_at || '');
        if (!force && cached && Number.isFinite(expiresAt) && expiresAt > now) {
            window.TransalcaRates = cached.data;
            return cached.data;
        }
    } catch (e) {}
    try {
        const res = await fetch('/api/rates/', { credentials: 'same-origin' });
        const json = await res.json();
        const data = normalizeRatePayload(json);
        window.TransalcaRates = data;
        localStorage.setItem(key, JSON.stringify({ data, expires_at: new Date(now + 300000).toISOString() }));
        return data;
    } catch (e) {
        window.TransalcaRates = window.TransalcaRates || { bcv: 0, usdt: 0 };
        return window.TransalcaRates;
    }
}

function normalizeRatePayload(json) {
    return {
        bcv: parseFloat(json?.data?.bcv?.usd || json?.data?.bcv?.monto || 0),
        usdt: parseFloat(json?.data?.binance?.usdt_ves || json?.data?.usdt?.monto || 0)
    };
}

function updateClientRatesBar() {
    const bcvEl = document.getElementById('rateBcvClient');
    if (!bcvEl) return;
    const bcv = parseFloat(window.TransalcaRates?.bcv || 0);
    bcvEl.textContent = bcv > 0 ? bcv.toFixed(2) : 'N/D';
}

function hydrateDualPrices(root = document) {
    root.querySelectorAll('[data-usd-price]').forEach(el => {
        if (el.hasAttribute('data-no-hydrate') || el.closest('[data-no-hydrate]')) return;
        el.textContent = formatUsdBs(el.dataset.usdPrice);
    });
    updateClientRatesBar();
    updateCurrencyMenuLabel();
}

function setButtonLoading(button, loading, text) {
    const btn = typeof button === 'string' ? document.querySelector(button) : button;
    if (!btn) return;
    if (loading) {
        btn.dataset.originalHtml = btn.dataset.originalHtml || btn.innerHTML;
        btn.dataset.loading = '1';
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${escapeHtml(text || 'Procesando...')}`;
    } else {
        btn.disabled = false;
        if (btn.dataset.originalHtml) btn.innerHTML = btn.dataset.originalHtml;
        delete btn.dataset.originalHtml;
        delete btn.dataset.loading;
    }
}

function confirmAction(message, callback, options = {}) {
    const text = normalizeSystemMessage(message || 'Confirme la accion.');
    if (window.Swal) {
        Swal.fire({
            icon: options.type || 'warning',
            title: text,
            showCancelButton: true,
            confirmButtonText: options.confirmText || 'Aceptar',
            cancelButtonText: options.cancelText || 'Cancelar',
            confirmButtonColor: options.confirmColor || '#e95d0f'
        }).then(result => {
            if (result.isConfirmed && typeof callback === 'function') callback();
            setTimeout(() => {
                if (document.querySelector('.modal.show')) {
                    document.body.classList.add('modal-open');
                }
            }, 100);
        });
        return;
    }
    let modalEl = document.getElementById('systemConfirmModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.className = 'modal fade';
        modalEl.id = 'systemConfirmModal';
        modalEl.tabIndex = -1;
        modalEl.innerHTML = `<div class="modal-dialog modal-sm modal-dialog-centered"><div class="modal-content">
            <div class="modal-header"><h5 class="modal-title">Confirmar accion</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <div class="modal-body"><p class="mb-0" id="systemConfirmText"></p></div>
            <div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button><button type="button" class="btn btn-orange" id="systemConfirmAccept">Aceptar</button></div>
        </div></div>`;
        document.body.appendChild(modalEl);
    }
    modalEl.querySelector('#systemConfirmText').textContent = text;
    const accept = modalEl.querySelector('#systemConfirmAccept');
    const cloned = accept.cloneNode(true);
    accept.parentNode.replaceChild(cloned, accept);
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    cloned.addEventListener('click', () => {
        modal.hide();
        if (typeof callback === 'function') callback();
    }, { once: true });
    modal.show();
}
