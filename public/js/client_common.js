
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

document.addEventListener('DOMContentLoaded', () => {
    checkSession().then(loggedIn => {
        if (loggedIn) loadClientNotifications();
    });
    const observer = new MutationObserver(() => applyAuthVisibility());
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
    const protectedLink = e.target.closest('a[href="/client/cart"], a[href="/client/my_orders"], a[href="/client/my_loyalty"], a[href="/client/profile"], a[href="/scanner"]');
    if (protectedLink && !currentUser) {
        e.preventDefault();
        showToast('Debe iniciar sesion para continuar.', 'warning');
        const next = protectedLink.getAttribute('href') || '/client/home';
        setTimeout(() => window.location.href = `/auth/login?next=${encodeURIComponent(next)}`, 900);
        return;
    }
    const logoutTarget = e.target.closest('#clientLogout');
    if (logoutTarget) {
        e.preventDefault();
        await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
        window.location.href = '/client/home';
    }
});
