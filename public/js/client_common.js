
const CLIENT_SESSION_CACHE_KEY = 'transalca_client_session_cache_v1';
const CLIENT_CART_COUNT_CACHE_KEY = 'transalca_client_cart_count_v1';

let currentUser = (() => {
    try {
        return JSON.parse(sessionStorage.getItem(CLIENT_SESSION_CACHE_KEY) || 'null');
    } catch (e) {
        return null;
    }
})();
let clientNotificationsReady = false;
let clientKnownNotificationIds = new Set();

function buildClientNavbarHtml() {
    let cachedBcv = '--';
    try {
        const ratesCache = JSON.parse(localStorage.getItem('transalca_rates_cache_v1') || 'null');
        const bcvVal = parseFloat(ratesCache?.data?.bcv || 0);
        if (bcvVal > 0) cachedBcv = bcvVal.toFixed(2);
    } catch (e) { }
    let cachedCart = 0;
    try {
        cachedCart = parseInt(sessionStorage.getItem(CLIENT_CART_COUNT_CACHE_KEY) || '0', 10) || 0;
    } catch (e) { }
    const currency = (localStorage.getItem('transalca_currency') || 'USD').toUpperCase() === 'VES' ? 'VES' : 'USD';
    const toggleLabel = currency === 'USD' ? 'Ver precios en bolivares' : 'Ver precios en dolares';
    const path = window.location.pathname;

    return `<nav class="client-navbar-wrap">
    <div class="client-topbar">
        <div class="container d-flex flex-wrap justify-content-between align-items-center gap-2">
            <span><i class="bi bi-shield-check me-1"></i>Compra segura en repuestos, cauchos y servicios</span>
            <span class="d-none d-md-inline-flex align-items-center gap-3">
                <span><i class="bi bi-truck me-1"></i>Atencion por sucursal</span>
                <span><i class="bi bi-headset me-1"></i>Soporte especializado</span>
            </span>
        </div>
    </div>
    <div class="navbar navbar-expand-lg client-navbar">
        <div class="container">
            <a href="/client/home" class="client-brand">
                <img src="/public/img/transalca-logo.png" alt="Transalca Group" class="client-brand-logo">
                <div>
                    <strong>Transalca Group</strong>
                    <small>Repuestos, cauchos y servicios</small>
                </div>
            </a>

            <div class="client-actions d-flex align-items-center gap-2 order-lg-3">
                <div class="d-flex align-items-center" id="ratesBar">
                    <span class="client-rate-pill" title="Tasa oficial BCV">
                        <i class="bi bi-bank me-1"></i><span class="rate-label-text">BCV: </span><span id="rateBcvClient">${cachedBcv}</span> Bs
                    </span>
                </div>
                <a href="/client/cart" class="btn btn-sm auth-required position-relative client-icon-btn client-cart-btn"
                    style="display:none;" title="Carrito" aria-label="Carrito">
                    <i class="bi bi-cart3"></i>
                    <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
                        id="cartBadge" style="${cachedCart > 0 ? '' : 'display:none;'}">${cachedCart}</span>
                </a>
                <div class="dropdown auth-required client-notifications" style="display:none;">
                    <button class="btn btn-sm position-relative client-icon-btn" data-bs-toggle="dropdown" title="Notificaciones">
                        <i class="bi bi-bell"></i>
                        <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" id="clientNotifBadge" style="display:none;font-size:0.6rem;">0</span>
                    </button>
                    <div class="dropdown-menu dropdown-menu-end p-0" style="width:320px;max-height:360px;overflow-y:auto;">
                        <div class="d-flex justify-content-between align-items-center px-3 py-2 border-bottom">
                            <strong style="font-size:0.85rem;">Notificaciones</strong>
                            <button class="btn btn-sm btn-link text-decoration-none p-0" data-client-notifications-read-all style="font-size:0.75rem;">Marcar todas</button>
                        </div>
                        <div id="clientNotifList"><div class="text-center text-muted py-3" style="font-size:0.8rem;">Sin notificaciones</div></div>
                    </div>
                </div>
                <a href="/admin/dashboard" class="btn btn-sm btn-dark client-icon-btn" id="navAdminBtn" style="display:none;"
                    title="Panel de Administracion"><i class="bi bi-shield-lock-fill"></i></a>
                <div class="dropdown auth-required" style="display:none;">
                    <button class="btn btn-sm client-profile-btn" data-bs-toggle="dropdown" aria-expanded="false">
                        <span class="client-profile-fallback" aria-hidden="true"><i class="bi bi-person-circle"></i></span>
                        <img src="/public/assets/profile_pics/default.png" alt="Perfil" id="clientNavPhoto"
                            class="client-profile-photo">
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="/client/profile"><i class="bi bi-person-circle me-2"></i>Mi
                                Perfil</a></li>
                        <li><a class="dropdown-item" href="/client/my_orders"><i class="bi bi-bag-check me-2"></i>Mis
                                Pedidos</a></li>
                        <li><a class="dropdown-item" href="/client/my_loyalty"><i class="bi bi-gift me-2"></i>Mi
                                Fidelizacion</a></li>
                        <li><a class="dropdown-item" href="/client/help"><i class="bi bi-headset me-2"></i>Ayuda</a></li>
                        <li><a class="dropdown-item" href="/scanner"><i class="bi bi-upc-scan me-2"></i>Escaner</a></li>
                        <li><a class="dropdown-item" href="#" data-currency-toggle><i class="bi bi-currency-exchange me-2"></i><span data-currency-toggle-label>${toggleLabel}</span></a></li>
                        <li>
                            <hr class="dropdown-divider">
                        </li>
                        <li><a class="dropdown-item" href="#" id="clientLogout"><i
                                    class="bi bi-box-arrow-left me-2"></i>Cerrar Sesion</a></li>
                    </ul>
                </div>
                <a href="/auth/login" class="btn btn-sm guest-only client-login-btn" title="Iniciar Sesion"><i
                        class="bi bi-person-fill me-1"></i>Entrar</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
                    data-bs-target="#clientNavCollapse" aria-controls="clientNavCollapse" aria-expanded="false"
                    aria-label="Abrir menu">
                    <i class="bi bi-list"></i>
                </button>
            </div>

            <div class="collapse navbar-collapse order-lg-2" id="clientNavCollapse">
                <ul class="navbar-nav mx-lg-auto client-nav-links">
                    <li class="nav-item"><a class="nav-link${path === '/client/home' ? ' active' : ''}" href="/client/home"><i
                                class="bi bi-house-door me-1"></i>Inicio</a></li>
                    <li class="nav-item"><a class="nav-link${path === '/client/catalog' ? ' active' : ''}" href="/client/catalog"><i
                                class="bi bi-grid-3x3-gap-fill me-1"></i>Catalogo</a></li>
                    <li class="nav-item auth-required" style="display:none;"><a class="nav-link${path === '/client/my_orders' ? ' active' : ''}"
                            href="/client/my_orders"><i class="bi bi-bag-check me-1"></i>Pedidos</a></li>
                    <li class="nav-item auth-required" style="display:none;"><a class="nav-link${path === '/client/my_loyalty' ? ' active' : ''}"
                            href="/client/my_loyalty"><i class="bi bi-gift me-1"></i>Fidelizacion</a></li>
                    <li class="nav-item"><a class="nav-link${path === '/client/help' ? ' active' : ''}" href="/client/help"><i class="bi bi-headset me-1"></i>Ayuda</a></li>
                    <li class="nav-item auth-required" style="display:none;"><a class="nav-link${path === '/scanner' ? ' active' : ''}" href="/scanner"><i
                                class="bi bi-upc-scan me-1"></i>Escaner</a></li>
                </ul>
            </div>
        </div>
    </div>
</nav>`;
}

function buildClientFooterHtml() {
    return `<footer class="client-footer">
    <div class="container">
        <div class="row g-4 align-items-start">
            <div class="col-lg-4">
                <a href="/client/home" class="client-footer-brand">
                    <img src="/public/img/transalca-logo.png" alt="Transalca Group" class="client-footer-logo">
                    <div>
                        <strong>Transalca Group</strong>
                        <small>Tienda automotriz y servicios</small>
                    </div>
                </a>
                <p class="client-footer-text mb-0">Calidad, confianza y respaldo tecnico para mantener tu vehiculo
                    siempre en movimiento.</p>
            </div>
            <div class="col-6 col-lg-2">
                <h6 class="client-footer-title">Navegacion</h6>
                <a href="/client/home">Inicio</a>
                <a href="/client/catalog">Catalogo</a>
                <a href="/client/cart" class="auth-required">Carrito</a>
                <a href="/client/my_orders" class="auth-required">Mis pedidos</a>
            </div>
            <div class="col-6 col-lg-3">
                <h6 class="client-footer-title">Programa cliente</h6>
                <a href="/client/my_loyalty" class="auth-required">Fidelizacion</a>
                <a href="/client/profile" class="auth-required">Mi perfil</a>
                <a href="/scanner" class="auth-required">Escaner</a>
                <a href="/auth/login" class="guest-only">Iniciar sesion</a>
            </div>
            <div class="col-lg-3">
                <h6 class="client-footer-title">Contacto</h6>
                <p class="client-footer-text mb-1"><i class="bi bi-telephone me-2"></i>+58 412-000-0000</p>
                <p class="client-footer-text mb-1"><i class="bi bi-envelope me-2"></i>atencion@transalca.com</p>
                <p class="client-footer-text mb-3"><i class="bi bi-geo-alt me-2"></i>Venezuela</p>
                <a href="/client/catalog" class="btn btn-sm btn-orange"><i class="bi bi-cart-plus me-1"></i>Comprar
                    ahora</a>
            </div>
        </div>
        <div class="client-footer-bottom">
            <span>Copyright 2026 Transalca Group. Todos los derechos reservados.</span>
            <div class="client-footer-social">
                <a href="#" aria-label="Instagram"><i class="bi bi-instagram"></i></a>
                <a href="#" aria-label="Facebook"><i class="bi bi-facebook"></i></a>
                <a href="#" aria-label="WhatsApp"><i class="bi bi-whatsapp"></i></a>
            </div>
        </div>
    </div>
</footer>`;
}

function hydrateClientNavbarSync() {
    const container = document.getElementById('navbarContainer');
    if (!container) return null;
    if (!container.querySelector('.client-navbar-wrap')) {
        container.innerHTML = buildClientNavbarHtml();
    }
    applyAuthVisibility();
    return container;
}

function hydrateClientFooterSync() {
    const container = document.getElementById('footerContainer');
    if (!container) return null;
    if (!container.querySelector('.client-footer')) {
        container.innerHTML = buildClientFooterHtml();
    }
    applyAuthVisibility();
    return container;
}

function installClientComponentLoadInterceptor() {
    if (!window.jQuery || !window.jQuery.fn || window.jQuery.fn.__transalcaClientLoadWrapped) return;
    const origLoad = window.jQuery.fn.load;
    window.jQuery.fn.load = function(url, params, callback) {
        const cb = typeof params === 'function' ? params : callback;
        if (typeof url === 'string') {
            if (url.includes('client_navbar.html')) {
                hydrateClientNavbarSync();
                if (typeof cb === 'function') {
                    this.each(function() { cb.call(this, '', 'success', null); });
                }
                return this;
            }
            if (url.includes('client_footer.html')) {
                hydrateClientFooterSync();
                if (typeof cb === 'function') {
                    this.each(function() { cb.call(this, '', 'success', null); });
                }
                return this;
            }
        }
        return origLoad.apply(this, arguments);
    };
    window.jQuery.fn.__transalcaClientLoadWrapped = true;
}

installClientComponentLoadInterceptor();
hydrateClientNavbarSync();
hydrateClientFooterSync();

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

let checkSessionPromise = null;

async function checkSession(force = false) {
    if (!force && currentUser && currentUser._ts && (Date.now() - currentUser._ts < 60000)) {
        updateNavForUser();
        return true;
    }
    if (!force && checkSessionPromise) return checkSessionPromise;
    checkSessionPromise = (async () => {
        try {
            const res = await fetch('/auth/session', { credentials: 'same-origin' });
            const data = await res.json();
            if (data.status === 'success' && data.user) {
                currentUser = { ...data.user, _ts: Date.now() };
                try {
                    sessionStorage.setItem(CLIENT_SESSION_CACHE_KEY, JSON.stringify(currentUser));
                } catch (e) { }
                updateNavForUser();
                updateCartBadge();
                return true;
            }
            currentUser = null;
            try {
                sessionStorage.removeItem(CLIENT_SESSION_CACHE_KEY);
                sessionStorage.removeItem(CLIENT_CART_COUNT_CACHE_KEY);
            } catch (e) { }
            updateNavForGuest();
            return false;
        } catch (e) {
            if (!currentUser) updateNavForGuest();
            return !!currentUser;
        } finally {
            checkSessionPromise = null;
        }
    })();
    return checkSessionPromise;
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
        const count = data.count || 0;
        try {
            sessionStorage.setItem(CLIENT_CART_COUNT_CACHE_KEY, String(count));
        } catch (e) { }
        const badge = document.getElementById('cartBadge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? '' : 'none';
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
            btn.classList.add('btn-orange');
            if (icon) icon.className = 'bi bi-plus-lg me-2';
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
    installClientComponentLoadInterceptor();
    hydrateClientNavbarSync();
    hydrateClientFooterSync();
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
        try {
            sessionStorage.removeItem(CLIENT_SESSION_CACHE_KEY);
            sessionStorage.removeItem(CLIENT_CART_COUNT_CACHE_KEY);
            sessionStorage.removeItem('transalca_admin_sidebar_cache_v2');
            sessionStorage.removeItem('transalca_admin_session_cache_v2');
        } catch (err) { }
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
    const bcv = parseFloat(window.TransalcaRates?.bcv || 0);
    const bcvEl = document.getElementById('rateBcvClient');
    if (bcvEl) bcvEl.textContent = bcv > 0 ? bcv.toFixed(2) : 'N/D';
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
