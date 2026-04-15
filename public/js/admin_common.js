
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
    toast.innerHTML = `<i class="bi ${icons[type] || icons.info}" style="color:${colors[type]};font-size:1.3rem;"></i><span style="flex:1;font-weight:500;font-size:0.85rem;">${message}</span><i class="bi bi-x close-toast" style="cursor:pointer;color:var(--text-muted);font-size:1.1rem;" onclick="this.parentElement.remove()"></i>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; setTimeout(() => toast.remove(), 300); }, 4000);
}

const Validator = {
    rules: {},

    setRules(formId, rules) {
        this.rules[formId] = rules;
    },

    validate(formId) {
        const rules = this.rules[formId];
        if (!rules) return true;
        let isValid = true;
        document.querySelectorAll(`#${formId} .is-invalid`).forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll(`#${formId} .is-valid`).forEach(el => el.classList.remove('is-valid'));

        for (const [field, fieldRules] of Object.entries(rules)) {
            const el = document.getElementById(field);
            if (!el) continue;
            const value = el.value.trim();
            let error = '';

            if (fieldRules.required && !value) {
                error = fieldRules.requiredMsg || 'Este campo es requerido';
            } else if (fieldRules.minLength && value.length < fieldRules.minLength) {
                error = fieldRules.minLengthMsg || `Minimo ${fieldRules.minLength} caracteres`;
            } else if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
                error = fieldRules.maxLengthMsg || `Maximo ${fieldRules.maxLength} caracteres`;
            } else if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
                error = fieldRules.patternMsg || 'Formato invalido';
            } else if (fieldRules.min !== undefined && parseFloat(value) < fieldRules.min) {
                error = fieldRules.minMsg || `El valor minimo es ${fieldRules.min}`;
            } else if (fieldRules.email && value && !/^[^@]+@[^@]+\.[^@]+$/.test(value)) {
                error = 'Ingrese un correo valido';
            } else if (fieldRules.match) {
                const matchEl = document.getElementById(fieldRules.match);
                if (matchEl && value !== matchEl.value) {
                    error = fieldRules.matchMsg || 'Los campos no coinciden';
                }
            } else if (fieldRules.custom && !fieldRules.custom(value)) {
                error = fieldRules.customMsg || 'Valor invalido';
            }

            if (error) {
                isValid = false;
                el.classList.add('is-invalid');
                el.classList.remove('is-valid');
                let feedback = el.nextElementSibling;
                while (feedback && !feedback.classList.contains('invalid-feedback')) {
                    feedback = feedback.nextElementSibling;
                }
                if (!feedback) {
                    feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    el.parentNode.appendChild(feedback);
                }
                feedback.textContent = error;
                feedback.style.display = 'block';
            } else if (value) {
                el.classList.add('is-valid');
                el.classList.remove('is-invalid');
            }
        }
        return isValid;
    },

    showServerErrors(formId, errors) {
        if (!errors) return;
        for (const [field, msg] of Object.entries(errors)) {
            const el = document.getElementById(field);
            if (!el) continue;
            el.classList.add('is-invalid');
            let feedback = el.nextElementSibling;
            while (feedback && !feedback.classList.contains('invalid-feedback')) {
                feedback = feedback.nextElementSibling;
            }
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                el.parentNode.appendChild(feedback);
            }
            feedback.textContent = msg;
            feedback.style.display = 'block';
        }
    },

    clearForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            form.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
                el.classList.remove('is-invalid', 'is-valid');
            });
            form.querySelectorAll('.invalid-feedback').forEach(el => el.style.display = 'none');
        }
    },

    validateField(formId, field) {
        const rules = this.rules[formId];
        if (!rules || !rules[field]) return true;
        const fieldRules = rules[field];
        const el = document.getElementById(field);
        if (!el) return true;

        const value = el.value.trim();
        let error = '';

        if (fieldRules.required && !value) {
            error = fieldRules.requiredMsg || 'Este campo es requerido';
        } else if (fieldRules.minLength && value.length < fieldRules.minLength) {
            error = fieldRules.minLengthMsg || `Minimo ${fieldRules.minLength} caracteres`;
        } else if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
            error = fieldRules.maxLengthMsg || `Maximo ${fieldRules.maxLength} caracteres`;
        } else if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
            error = fieldRules.patternMsg || 'Formato invalido';
        } else if (fieldRules.min !== undefined && parseFloat(value) < fieldRules.min) {
            error = fieldRules.minMsg || `El valor minimo es ${fieldRules.min}`;
        } else if (fieldRules.email && value && !/^[^@]+@[^@]+\.[^@]+$/.test(value)) {
            error = 'Ingrese un correo valido';
        } else if (fieldRules.match) {
            const matchEl = document.getElementById(fieldRules.match);
            if (matchEl && value !== matchEl.value) {
                error = fieldRules.matchMsg || 'Los campos no coinciden';
            }
        } else if (fieldRules.custom && !fieldRules.custom(value)) {
            error = fieldRules.customMsg || 'Valor invalido';
        }

        if (error) {
            el.classList.add('is-invalid');
            el.classList.remove('is-valid');
            let feedback = el.nextElementSibling;
            while (feedback && !feedback.classList.contains('invalid-feedback')) {
                feedback = feedback.nextElementSibling;
            }
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                el.parentNode.appendChild(feedback);
            }
            feedback.textContent = error;
            feedback.style.display = 'block';
            return false;
        } else if (value) {
            el.classList.add('is-valid');
            el.classList.remove('is-invalid');
            const fb = el.parentNode.querySelector('.invalid-feedback');
            if (fb) fb.style.display = 'none';
        } else {
            el.classList.remove('is-invalid', 'is-valid');
        }
        return true;
    },

    setupRealtime(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        form.querySelectorAll('input, select, textarea').forEach(el => {
            if (el.id) {
                el.addEventListener('input', () => {
                    Validator.validateField(formId, el.id);
                });
            } else {
                el.addEventListener('input', () => {
                    el.classList.remove('is-invalid');
                    const fb = el.parentNode.querySelector('.invalid-feedback');
                    if (fb) fb.style.display = 'none';
                });
            }
        });
    }
};

function checkPasswordStrength(password) {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[@$!%*?&#.]/.test(password)) score++;
    if (score <= 2) return 'weak';
    if (score <= 3) return 'medium';
    return 'strong';
}

function updatePasswordStrength(inputId, barId) {
    const input = document.getElementById(inputId);
    const bar = document.getElementById(barId);
    if (!input || !bar) return;
    input.addEventListener('input', () => {
        const strength = checkPasswordStrength(input.value);
        bar.className = `bar ${strength}`;
    });
}

async function apiCall(url, method = 'GET', data = null) {
    try {
        const opts = { method, credentials: 'same-origin' };
        if (data && method !== 'GET') {
            if (data instanceof FormData) {
                opts.body = data;
            } else {
                opts.headers = { 'Content-Type': 'application/json' };
                opts.body = JSON.stringify(data);
            }
        }
        const res = await fetch(url, opts);
        const json = await res.json();
        if (!res.ok) {
            if (json.errors) return json;
            throw new Error(json.message || 'Error en la solicitud');
        }
        return json;
    } catch (e) {
        showToast(e.message || 'Error de conexion', 'error');
        throw e;
    }
}

async function saveWithValidation(formId, url, method, successMsg, callback) {
    if (!Validator.validate(formId)) {
        showToast('Corrija los errores del formulario', 'warning');
        return;
    }
    const form = document.getElementById(formId);
    const data = {};
    form.querySelectorAll('input, select, textarea').forEach(el => {
        if (el.name) data[el.name] = el.type === 'number' ? parseFloat(el.value) || 0 : el.value;
    });
    try {
        const res = await apiCall(url, method, data);
        if (res.status === 'error') {
            if (res.errors) Validator.showServerErrors(formId, res.errors);
            showToast(res.message, 'error');
            return;
        }
        showToast(successMsg || res.message, 'success');
        if (callback) callback(res);
    } catch (e) { }
}

async function loadSucursales(selectId, includeAll = true) {
    try {
        const res = await apiCall('/api/sucursales/active');
        const select = document.getElementById(selectId);
        if (!select) return;
        select.innerHTML = includeAll ? '<option value="">Todas las sucursales</option>' : '<option value="">Seleccione sucursal</option>';
        (res.data || []).forEach(s => {
            select.innerHTML += `<option value="${s.id}">${s.nombre}</option>`;
        });
    } catch (e) { }
}

function confirmAction(message, callback) {
    if (confirm(message)) callback();
}

function formatCurrency(amount) {
    return parseFloat(amount || 0).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('es-VE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function statusBadge(estado) {
    if (estado === 1 || estado === true || estado === 'activo' || estado === 'aprobado') {
        return '<span class="badge-status badge-active">Activo</span>';
    } else if (estado === 'pendiente') {
        return '<span class="badge-status badge-pending">Pendiente</span>';
    }
    return '<span class="badge-status badge-inactive">Inactivo</span>';
}

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });
    const toggle = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('adminSidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => sidebar.classList.toggle('show'));
    }
});

// Event Delegation for dynamically loaded auth elements
document.body.addEventListener('click', async (e) => {
    const logoutTarget = e.target.closest('#btnLogout, #navLogout');
    if (logoutTarget) {
        e.preventDefault();
        await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
        window.location.href = '/auth/login';
    }
});

async function loadNavSession() {
    try {
        const res = await fetch('/auth/session', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success') {
            const u = data.user;
            const nameEl = document.getElementById('navUserName');
            if (nameEl) nameEl.textContent = `${u.nombre} ${u.apellido}`;
            const photoEl = document.getElementById('navUserPhoto');
            if (photoEl) photoEl.src = `/public/assets/profile_pics/${u.foto || 'default.png'}`;
            const titleEl = document.getElementById('pageTitle');
            if (titleEl) {
                const page = window.location.pathname.split('/').pop();
                const titles = {
                    dashboard: 'Dashboard', products: 'Productos', categories: 'Categorias',
                    brands: 'Marcas', suppliers: 'Proveedores', inventory: 'Gestionar Stock de Productos',
                    services: 'Servicios', service_mechanics: 'Servicio Mecanico', mechanics: 'Mecanicos', orders: 'Ordenes de Venta',
                    payments: 'Comprobacion de Pagos', promotions: 'Promociones',
                    users: 'Usuarios', roles: 'Roles y Permisos', qr: 'Codigos QR',
                    reports: 'Reportes', bitacora: 'Bitacora', backup: 'Respaldos',
                    profile: 'Mi Perfil', sucursales: 'Sucursales'
                };
                titleEl.textContent = titles[page] || 'Panel de Administracion';
            }
        }
    } catch (e) { }
}
