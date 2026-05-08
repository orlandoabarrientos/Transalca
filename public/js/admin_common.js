
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

function splitDocumentValue(value, defaultPrefix = 'V') {
    const raw = String(value || '').toUpperCase().replace(/\./g, '').trim();
    const compact = raw.replace(/[^A-Z0-9]/g, '');
    if (!compact) return { prefix: defaultPrefix, number: '' };
    if (/^[A-Z]/.test(compact)) {
        return { prefix: compact[0], number: compact.slice(1) };
    }
    return { prefix: defaultPrefix, number: compact.replace(/\D/g, '') };
}

function splitRifValue(value, defaultPrefix = 'J') {
    const doc = splitDocumentValue(value, defaultPrefix);
    return { prefix: doc.prefix, number: doc.number.replace(/\D/g, '').slice(0, 9) };
}

function setDocumentFields(prefixId, numberId, value, defaultPrefix = 'V') {
    const doc = splitDocumentValue(value, defaultPrefix);
    const prefix = document.getElementById(prefixId);
    const number = document.getElementById(numberId);
    if (prefix) prefix.value = doc.prefix || defaultPrefix;
    if (number) number.value = doc.number || '';
}

function setRifFields(prefixId, numberId, value, defaultPrefix = 'J') {
    const doc = splitRifValue(value, defaultPrefix);
    const prefix = document.getElementById(prefixId);
    const number = document.getElementById(numberId);
    if (prefix) prefix.value = doc.prefix || defaultPrefix;
    if (number) number.value = doc.number || '';
}

function buildDocumentValue(prefixId, numberId) {
    const prefix = (document.getElementById(prefixId)?.value || '').trim().toUpperCase();
    const number = (document.getElementById(numberId)?.value || '').replace(/\D/g, '');
    return prefix && number ? `${prefix}-${number}` : '';
}

function buildRifValue(prefixId, numberId) {
    const prefix = (document.getElementById(prefixId)?.value || '').trim().toUpperCase();
    const number = (document.getElementById(numberId)?.value || '').replace(/\D/g, '');
    return prefix && number.length === 9 ? `${prefix}-${number.slice(0, 8)}-${number.slice(8)}` : '';
}

function cssEscapeValue(value) {
    if (typeof CSS !== 'undefined' && CSS.escape) return CSS.escape(String(value));
    return String(value).replace(/["\\]/g, '\\$&');
}

function getFieldFeedback(el) {
    let feedback = el?.nextElementSibling;
    while (feedback && !feedback.classList.contains('invalid-feedback')) {
        feedback = feedback.nextElementSibling;
    }
    if (!feedback && el?.parentNode) {
        feedback = el.parentNode.querySelector('.invalid-feedback');
    }
    if (!feedback && el?.parentNode) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        el.parentNode.appendChild(feedback);
    }
    return feedback;
}

function setFieldError(el, message) {
    if (!el) return;
    el.classList.add('is-invalid');
    el.classList.remove('is-valid');
    const feedback = getFieldFeedback(el);
    if (feedback) {
        feedback.textContent = message || '';
        feedback.style.display = 'block';
    }
}

function clearFieldError(el) {
    if (!el) return;
    el.classList.remove('is-invalid');
    const feedback = getFieldFeedback(el);
    if (feedback) {
        feedback.textContent = '';
        feedback.style.display = 'none';
        feedback.style.color = '';
    }
}

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
    toast.innerHTML = `<i class="bi ${icons[type] || icons.info}" style="color:${colors[type]};font-size:1.3rem;"></i><span style="flex:1;font-weight:500;font-size:0.85rem;">${escapeHtml(normalizeSystemMessage(message))}</span><i class="bi bi-x close-toast" style="cursor:pointer;color:var(--text-muted);font-size:1.1rem;" onclick="this.parentElement.remove()"></i>`;
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
            const el = document.getElementById(field) || document.querySelector(`#${formId} [name="${cssEscapeValue(field)}"]`);
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
                setFieldError(el, error);
            } else if (value) {
                el.classList.add('is-valid');
                el.classList.remove('is-invalid');
                clearFieldError(el);
            }
        }
        return isValid;
    },

    showServerErrors(formId, errors) {
        if (!errors) return;
        for (const [field, msg] of Object.entries(errors)) {
            const el = document.getElementById(field) || document.querySelector(`#${formId} [name="${cssEscapeValue(field)}"]`);
            if (!el) continue;
            setFieldError(el, msg);
        }
        updateFormSubmitState(formId);
    },

    clearForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            form.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
                el.classList.remove('is-invalid', 'is-valid');
            });
            form.querySelectorAll('.invalid-feedback').forEach(el => el.style.display = 'none');
            form.querySelectorAll('.invalid-feedback').forEach(el => el.textContent = '');
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
            setFieldError(el, error);
            return false;
        } else if (value) {
            el.classList.add('is-valid');
            el.classList.remove('is-invalid');
            clearFieldError(el);
        } else {
            el.classList.remove('is-invalid', 'is-valid');
            clearFieldError(el);
        }
        return true;
    },

    setupRealtime(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        form.querySelectorAll('input, select, textarea').forEach(el => {
            const handler = () => {
                if (el.id) {
                    Validator.validateField(formId, el.id);
                } else {
                    el.classList.remove('is-invalid');
                    const fb = el.parentNode.querySelector('.invalid-feedback');
                    if (fb) {
                        fb.style.display = 'none';
                        fb.textContent = '';
                    }
                }
                updateFormSubmitState(formId);
            };
            el.addEventListener('input', handler);
            el.addEventListener('change', handler);
        });
        form.addEventListener('reset', () => setTimeout(() => {
            Validator.clearForm(formId);
            updateFormSubmitState(formId);
        }, 0));
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
            return json && typeof json === 'object'
                ? json
                : { status: 'error', message: 'Error en la solicitud.' };
        }
        return json;
    } catch (e) {
        return { status: 'error', message: e.message || 'Error de conexion.' };
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

function updateFormSubmitState(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    const modal = form.closest('.modal-content') || form;
    const hasErrors = !!form.querySelector('.is-invalid');
    modal.querySelectorAll('button[type="submit"], button[onclick*="save"], button[onclick*="Save"], #btnSaveVehicle').forEach(btn => {
        if (!btn.dataset.loading) btn.disabled = hasErrors;
    });
}

function bindModalValidationReset() {
    document.querySelectorAll('.modal').forEach(modal => {
        if (modal.dataset.validationResetBound) return;
        modal.dataset.validationResetBound = '1';
        modal.addEventListener('hidden.bs.modal', () => {
            modal.querySelectorAll('form').forEach(form => Validator.clearForm(form.id));
        });
    });
}

function enhanceSearchableSelects(root = document) {
    root.querySelectorAll('select.form-select:not([data-no-search])').forEach(select => {
        if (select.dataset.searchEnhanced === '1') return;
        if (select.closest('.input-group')) return;
        if ((select.options?.length || 0) < 7) return;
        select.dataset.searchEnhanced = '1';
        const input = document.createElement('input');
        input.type = 'search';
        input.className = 'form-control form-control-sm select-search-input mb-1';
        input.placeholder = 'Buscar...';
        input.autocomplete = 'off';
        select.parentNode.insertBefore(input, select);
        const resetOptions = () => {
            Array.from(select.options).forEach(option => {
                option.hidden = false;
            });
        };
        input.addEventListener('input', () => {
            const q = input.value.trim().toLowerCase();
            Array.from(select.options).forEach(option => {
                option.hidden = q && !option.textContent.toLowerCase().includes(q);
            });
        });
        input.addEventListener('blur', () => {
            if (!input.value.trim()) resetOptions();
        });
        select.addEventListener('change', () => {
            clearFieldError(select);
            if (!input.value.trim()) resetOptions();
        });
        const modal = select.closest('.modal');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                input.value = '';
                resetOptions();
            });
        }
    });
}

function formatUsdBs(amount) {
    const usd = parseFloat(amount || 0);
    const bs = convertUsdToBs(usd);
    const usdText = `$${formatCurrency(usd)}`;
    if (!bs) return usdText;
    return `${usdText} / Bs. ${formatCurrency(bs)}`;
}

function convertUsdToBs(amount) {
    const rates = window.TransalcaRates || {};
    const bcv = parseFloat(rates.bcv || 0);
    const usdt = parseFloat(rates.usdt || 0);
    if (!bcv || !usdt) return 0;
    return (parseFloat(amount || 0) * usdt) / bcv;
}

async function loadExchangeRatesCached() {
    const key = 'transalca_rates_cache_v1';
    const now = Date.now();
    try {
        const cached = JSON.parse(localStorage.getItem(key) || 'null');
        if (cached && cached.expires > now) {
            window.TransalcaRates = cached.data;
            return cached.data;
        }
    } catch (e) {}
    try {
        const res = await fetch('/api/rates/', { credentials: 'same-origin' });
        const json = await res.json();
        const data = {
            bcv: parseFloat(json?.data?.bcv?.usd || 0),
            usdt: parseFloat(json?.data?.binance?.usdt_ves || 0)
        };
        window.TransalcaRates = data;
        localStorage.setItem(key, JSON.stringify({ data, expires: now + 300000 }));
        return data;
    } catch (e) {
        window.TransalcaRates = window.TransalcaRates || { bcv: 0, usdt: 0 };
        return window.TransalcaRates;
    }
}

function hydrateDualPrices(root = document) {
    root.querySelectorAll('[data-usd-price]').forEach(el => {
        el.textContent = formatUsdBs(el.dataset.usdPrice);
    });
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
    bindModalValidationReset();
    enhanceSearchableSelects();
    loadExchangeRatesCached().then(() => hydrateDualPrices());
    const observer = new MutationObserver(() => {
        bindModalValidationReset();
        enhanceSearchableSelects();
        hydrateDualPrices();
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

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
                    dashboard: 'Dashboard', clients: 'Clientes', products: 'Productos', categories: 'Categorias',
                    brands: 'Marcas', suppliers: 'Proveedores', inventory: 'Gestionar Stock de Productos',
                    services: 'Servicios', service_mechanics: 'Servicio Mecanico', mechanics: 'Mecanicos', orders: 'Ordenes de Venta',
                    tickets: 'Tickets de Soporte',
                    payments: 'Comprobacion de Pagos', promotions: 'Promociones',
                    users: 'Usuarios', roles: 'Roles y Permisos', qr: 'Codigos QR',
                    reports: 'Reportes', report_stats: 'Estadisticas', tasas: 'Tasa de Cambio',
                    bitacora: 'Bitacora', backup: 'Respaldos',
                    profile: 'Mi Perfil', sucursales: 'Sucursales', guide: 'Guia'
                };
                titleEl.textContent = titles[page] || 'Panel de Administracion';
            }
        }
    } catch (e) { }
}
