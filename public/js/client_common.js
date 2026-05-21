
let currentUser = null;

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
    if (photo) photo.src = `/public/assets/profile_pics/${currentUser.foto || 'default.png'}`;
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

document.addEventListener('DOMContentLoaded', () => {
    checkSession().then(loggedIn => {
        if (loggedIn) loadClientNotifications();
    });
    loadExchangeRatesCached().then(() => hydrateDualPrices());
    installClientListSearches();
    updateCurrencyMenuLabel();
    const observer = new MutationObserver((mutations) => {
        applyAuthVisibility();
        const hasNewPrices = mutations.some(m => Array.from(m.addedNodes).some(n => n.nodeType === 1 && (n.hasAttribute('data-usd-price') || n.querySelector('[data-usd-price]'))));
        if (hasNewPrices) {
            hydrateDualPrices();
        }
        if (mutations.some(m => Array.from(m.addedNodes).some(n => n.nodeType === 1 && (n.matches?.('table') || n.querySelector?.('table'))))) {
            installClientListSearches();
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
        const unread = list.filter(n => !n.leida).length;
        const badge = document.getElementById('clientNotifBadge');
        if (badge) { badge.textContent = unread; badge.style.display = unread > 0 ? '' : 'none'; }
        const container = document.getElementById('clientNotifList');
        if (!container) return;
        if (list.length === 0) { container.innerHTML = '<div class="text-center text-muted py-3" style="font-size:0.8rem;">Sin notificaciones</div>'; return; }
        container.innerHTML = list.slice(0, 8).map(n => {
            const bg = n.leida ? '' : 'background:rgba(0,0,0,0.03);';
            return `<div class="px-3 py-2 border-bottom" style="font-size:0.8rem;cursor:pointer;${bg}" onclick="markReadClient(${n.id})"><div style="font-weight:${n.leida?'400':'600'};">${n.titulo || n.mensaje}</div><div class="text-muted" style="font-size:0.7rem;">${n.mensaje ? n.mensaje.substring(0,60) : ''}</div></div>`;
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

document.body.addEventListener('click', async (e) => {
    const closeToast = e.target.closest('.close-toast, .toast-close');
    if (closeToast) {
        e.preventDefault();
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
    const logoutTarget = e.target.closest('#clientLogout');
    if (logoutTarget) {
        e.preventDefault();
        await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
        window.location.href = '/client/home';
    }
});

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
    if (!toast) return;
    toast.classList.add('removing');
    const remove = () => toast.remove();
    toast.addEventListener('transitionend', remove, { once: true });
    setTimeout(remove, 250);
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
        el.textContent = currency === 'USD' ? 'Ver precios en bolívares' : 'Ver precios en dólares';
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
    return (parseFloat(amount || 0) * usdt) / bcv;
}

async function loadExchangeRatesCached(force = false) {
    const key = 'transalca_rates_cache_v1';
    const now = Date.now();
    try {
        const cached = JSON.parse(localStorage.getItem(key) || 'null');
        if (!force && cached && cached.expires > now) {
            window.TransalcaRates = cached.data;
            return cached.data;
        }
    } catch (e) {}
    try {
        const res = await fetch('/api/rates/', { credentials: 'same-origin' });
        const json = await res.json();
        const data = normalizeRatePayload(json);
        window.TransalcaRates = data;
        localStorage.setItem(key, JSON.stringify({ data, expires: now + 300000 }));
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

function hydrateDualPrices(root = document) {
    root.querySelectorAll('[data-usd-price]').forEach(el => {
        el.textContent = formatUsdBs(el.dataset.usdPrice);
    });
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
