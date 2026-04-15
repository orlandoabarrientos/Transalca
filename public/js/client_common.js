
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
    toast.innerHTML = `<i class="bi ${icons[type] || icons.info}" style="color:${colors[type]};font-size:1.3rem;"></i><span style="flex:1;font-weight:500;font-size:0.85rem;">${message}</span><i class="bi bi-x" style="cursor:pointer;color:var(--text-muted);" onclick="this.parentElement.remove()"></i>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 4000);
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
        adminBtn.style.display = (currentUser.tipo === 'empleado' || currentUser.tipo === 'admin') ? '' : 'none';
    }
    document.querySelectorAll('.client-only-qr').forEach(el => {
        el.style.display = (currentUser.tipo === 'cliente') ? '' : 'none';
    });
}

function updateNavForGuest() {
    document.querySelectorAll('.auth-required').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.guest-only').forEach(el => el.style.display = '');
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
        showToast('Debe iniciar sesion para agregar al carrito', 'warning');
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
            showToast('Agregado al carrito', 'success');
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
    checkSession();
});

document.body.addEventListener('click', async (e) => {
    const logoutTarget = e.target.closest('#clientLogout');
    if (logoutTarget) {
        e.preventDefault();
        await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
        window.location.href = '/client/home';
    }
});
