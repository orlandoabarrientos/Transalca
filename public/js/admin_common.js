
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
        const msg = (message || '').toLowerCase();
        if (msg.includes('ya existe') || msg.includes('ya registrado') || msg.includes('ya esta registrado') || msg.includes('ya está registrado') || msg.includes('ya registrada') || msg.includes('ya se encuentra')) {
            feedback.style.color = '#dc3545';
        } else {
            feedback.style.color = '#b0b0b0';
        }
    }
    syncSelect2ValidationState(el);
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
    syncSelect2ValidationState(el);
}

function syncSelect2ValidationState(el) {
    if (!el || el.tagName !== 'SELECT') return;
    const container = el.nextElementSibling;
    if (!container || !container.classList.contains('select2')) return;
    const selection = container.querySelector('.select2-selection');
    if (!selection) return;
    selection.classList.toggle('is-invalid', el.classList.contains('is-invalid'));
    selection.classList.toggle('is-valid', el.classList.contains('is-valid'));
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
    toast.innerHTML = `<i class="bi ${icons[type] || icons.info}" style="color:${colors[type]};font-size:1.3rem;"></i><span style="flex:1;font-weight:500;font-size:0.85rem;">${escapeHtml(normalizeSystemMessage(message))}</span><button type="button" class="toast-close close-toast" aria-label="Cerrar"><i class="bi bi-x"></i></button>`;
    toast.querySelector('.toast-close')?.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        dismissToast(toast);
    });
    container.appendChild(toast);
    setTimeout(() => dismissToast(toast), 5000);
}

function dismissToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 300);
}

function installSweetAlertDefaults() {
    if (!window.Swal || window.Swal.__transalcaDefaults) return;
    const originalFire = window.Swal.fire.bind(window.Swal);
    window.Swal.fire = function(options, ...args) {
        if (typeof options === 'object' && options) {
            if (!options.showCancelButton && !options.timer) {
                options = { timer: 5000, timerProgressBar: true, showConfirmButton: true, ...options };
            }
            const originalDidClose = options.didClose;
            options.didClose = function(...closeArgs) {
                if (typeof originalDidClose === 'function') {
                    originalDidClose.apply(this, closeArgs);
                }
                setTimeout(() => {
                    if (document.querySelector('.modal.show')) {
                        document.body.classList.add('modal-open');
                    }
                }, 100);
            };
        }
        return originalFire(options, ...args);
    };
    window.Swal.__transalcaDefaults = true;
}

const Validator = {
    rules: {},

    setRules(formId, rules) {
        this.rules[formId] = rules;
    },

    initTracking(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        setTimeout(() => {
            form._initialState = serializeForm(form);
            updateFormSubmitState(formId);
        }, 150);
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

            if (el.dataset.externalError) {
                error = el.dataset.externalError;
            } else if (fieldRules.required && !value) {
                error = fieldRules.requiredMsg || 'Este campo es requerido';
            } else if (fieldRules.minLength && value.length < fieldRules.minLength) {
                error = fieldRules.minLengthMsg || `Mínimo ${fieldRules.minLength} caracteres`;
            } else if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
                error = fieldRules.maxLengthMsg || `Máximo ${fieldRules.maxLength} caracteres`;
            } else if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
                error = fieldRules.patternMsg || 'Formato inválido';
            } else if (fieldRules.min !== undefined && parseFloat(value) < fieldRules.min) {
                error = fieldRules.minMsg || `El valor mínimo es ${fieldRules.min}`;
            } else if (fieldRules.email && value && !/^[^@]+@[^@]+\.[^@]+$/.test(value)) {
                error = 'Ingrese un correo válido';
            } else if (fieldRules.match) {
                const matchEl = document.getElementById(fieldRules.match);
                if (matchEl && value !== matchEl.value) {
                    error = fieldRules.matchMsg || 'Los campos no coinciden';
                }
            } else if (fieldRules.custom && !fieldRules.custom(value)) {
                error = fieldRules.customMsg || 'Valor inválido';
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
            if (form.dataset.validatorClearing === '1') return;
            form.dataset.validatorClearing = '1';
            form.reset();
            delete form._initialState;
            clearFormValidationState(form);
            setTimeout(() => {
                delete form.dataset.validatorClearing;
            }, 0);
        }
    },

    validateField(formId, field) {
        const rules = this.rules[formId];
        if (!rules || !rules[field]) return true;
        const fieldRules = rules[field];
        const el = document.querySelector(`#${formId} #${field}`) || document.getElementById(field) || document.querySelector(`#${formId} [name="${cssEscapeValue(field)}"]`);
        if (!el) return true;

        let value = '';
        if (el.tagName === 'SELECT' && el.multiple) {
            const selectedOptions = Array.from(el.selectedOptions).map(opt => opt.value).filter(val => val !== '');
            value = selectedOptions.join(',');
        } else {
            value = el.value.trim();
        }
        let error = '';

        if (el.dataset.externalError) {
            error = el.dataset.externalError;
        } else if (fieldRules.required && !value) {
            error = fieldRules.requiredMsg || 'Este campo es requerido';
        } else if (fieldRules.minLength && value.length < fieldRules.minLength) {
            error = fieldRules.minLengthMsg || `Mínimo ${fieldRules.minLength} caracteres`;
        } else if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
            error = fieldRules.maxLengthMsg || `Máximo ${fieldRules.maxLength} caracteres`;
        } else if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
            error = fieldRules.patternMsg || 'Formato inválido';
        } else if (fieldRules.min !== undefined && parseFloat(value) < fieldRules.min) {
            error = fieldRules.minMsg || `El valor mínimo es ${fieldRules.min}`;
        } else if (fieldRules.email && value && !/^[^@]+@[^@]+\.[^@]+$/.test(value)) {
            error = 'Ingrese un correo válido';
        } else if (fieldRules.match) {
            const matchEl = document.getElementById(fieldRules.match);
            if (matchEl && value !== matchEl.value) {
                error = fieldRules.matchMsg || 'Los campos no coinciden';
            }
        } else if (fieldRules.custom && !fieldRules.custom(value)) {
            error = fieldRules.customMsg || 'Valor inválido';
        }

        if (error) {
            setFieldError(el, error);
            return false;
        } else if (value) {
            el.classList.add('is-valid');
            el.classList.remove('is-invalid');
            clearFieldError(el);
            syncSelect2ValidationState(el);
        } else {
            el.classList.remove('is-invalid', 'is-valid');
            clearFieldError(el);
            syncSelect2ValidationState(el);
        }
        return true;
    },

    setupRealtime(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        if (form.dataset.validatorRealtimeBound === '1') return;
        form.dataset.validatorRealtimeBound = '1';
        
        const rules = this.rules[formId];
        if (rules) {
            for (const [field, fieldRules] of Object.entries(rules)) {
                if (fieldRules && fieldRules.maxLength) {
                    const el = document.getElementById(field) || document.querySelector(`#${formId} [name="${cssEscapeValue(field)}"]`);
                    if (el && !el.hasAttribute('maxlength')) {
                        el.setAttribute('maxlength', fieldRules.maxLength);
                    }
                }
            }
        }

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
                if (form._initialState) {
                    form._isDirty = serializeForm(form) !== form._initialState;
                } else {
                    form._isDirty = true;
                }
                updateFormSubmitState(formId);
            };
            el.addEventListener('input', () => {
                delete el.dataset.externalError;
                handler();
            });
            el.addEventListener('change', handler);
        });
        form.addEventListener('reset', () => setTimeout(() => {
            if (form.dataset.validatorClearing === '1') return;
            clearFormValidationState(form);
            delete form._initialState;
            updateFormSubmitState(formId);
        }, 0));
    }
};

function clearFormValidationState(form) {
    if (!form) return;
    form.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
        el.classList.remove('is-invalid', 'is-valid');
    });
    form.querySelectorAll('.invalid-feedback').forEach(el => {
        el.style.display = 'none';
        el.textContent = '';
    });
    if (window.jQuery && window.jQuery.fn?.select2) {
        form.querySelectorAll('select').forEach(select => {
            if (window.jQuery(select).hasClass('select2-hidden-accessible')) {
                window.jQuery(select).trigger('change.select2');
            }
            syncSelect2ValidationState(select);
        });
    }
}

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
        if (select.multiple) {
            select.innerHTML = '';
        } else {
            select.innerHTML = includeAll ? '<option value="">Todas las sucursales</option>' : '<option value="">Seleccione sucursal</option>';
        }
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

function serializeForm(form) {
    const data = {};
    form.querySelectorAll('input, select, textarea').forEach(el => {
        if (!el.id && !el.name) return;
        const key = el.id || el.name;
        if (el.type === 'checkbox' || el.type === 'radio') {
            data[key] = el.checked;
        } else {
            data[key] = el.value.trim();
        }
    });
    return JSON.stringify(data);
}

function formHasMissingRequired(formId, form) {
    const rules = Validator.rules[formId];
    if (!rules) return false;
    for (const [field, fieldRules] of Object.entries(rules)) {
        if (!fieldRules || !fieldRules.required) continue;
        const el = document.querySelector(`#${formId} #${cssEscapeValue(field)}`) || document.getElementById(field) || form.querySelector(`[name="${cssEscapeValue(field)}"]`);
        if (!el || el.disabled) continue;
        let value = '';
        if (el.tagName === 'SELECT' && el.multiple) {
            value = Array.from(el.selectedOptions).map(opt => opt.value).filter(val => val !== '').join(',');
        } else {
            value = (el.value || '').trim();
        }
        if (!value) return true;
    }
    return false;
}

function updateFormSubmitState(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    const modal = form.closest('.modal-content') || form;
    const hasErrors = !!form.querySelector('.is-invalid');
    const missingRequired = formHasMissingRequired(formId, form);
    const isDirty = form._initialState ? (serializeForm(form) !== form._initialState) : true;
    modal.querySelectorAll('button[type="submit"], button[onclick*="save"], button[onclick*="Save"], #btnSaveVehicle, #btnSavePromo, button[onclick*="change"], button[onclick*="Change"], #btnChangePassword, .btn-success').forEach(btn => {
        if (!btn.dataset.loading) {
            btn.disabled = hasErrors || missingRequired || (form._initialState ? !isDirty : false);
        }
    });
}

function inputNumericMode(input) {
    const key = `${input.id || ''} ${input.name || ''}`.toLowerCase();
    if (key.includes('search') || input.type === 'search' || input.classList.contains('auto-table-search') || input.classList.contains('table-search-input')) return '';
    if (input.dataset.numeric === 'decimal') return 'decimal';
    if (input.dataset.numeric === 'integer') return 'integer';
    if (input.type === 'number') {
        return ['precio', 'monto', 'tasa', 'unitario', 'total'].some(token => key.includes(token)) ? 'decimal' : 'integer';
    }
    if (key.includes('telefono') || key.includes('phone')) return 'phone';
    if (['cedula', 'rif', 'cantidad', 'duracion', 'kilometraje', 'anio', 'ano', 'puntos', 'stock'].some(token => key.includes(token))) return 'integer';
    return '';
}

function sanitizeNumericValue(value, mode) {
    let text = String(value || '');
    if (mode === 'phone' || mode === 'integer') return text.replace(/\D/g, '');
    if (mode === 'decimal') {
        text = text.replace(',', '.').replace(/[^0-9.]/g, '');
        const parts = text.split('.');
        return parts.length > 1 ? `${parts.shift()}.${parts.join('').slice(0, 2)}` : text;
    }
    return text;
}

function bindInputGuards() {
    if (document.body.dataset.inputGuardsBound === '1') return;
    document.body.dataset.inputGuardsBound = '1';
    document.body.addEventListener('beforeinput', event => {
        const input = event.target.closest?.('input');
        if (!input || event.inputType?.startsWith('delete')) return;
        const mode = inputNumericMode(input);
        if (!mode || event.data == null) return;
        const allowed = mode === 'decimal' ? /^[0-9.,]+$/ : /^\d+$/;
        if (!allowed.test(event.data)) event.preventDefault();
    });
    document.body.addEventListener('input', event => {
        const input = event.target.closest?.('input');
        if (!input) return;
        const mode = inputNumericMode(input);
        if (!mode) return;
        const clean = sanitizeNumericValue(input.value, mode);
        if (input.value !== clean) input.value = clean;
    });
}

function bindModalValidationReset() {
    document.querySelectorAll('.modal').forEach(modal => {
        if (modal.dataset.validationResetBound) return;
        modal.dataset.validationResetBound = '1';
        modal.addEventListener('shown.bs.modal', () => {
            enhanceSearchableSelects(modal);
        });
        modal.addEventListener('hidden.bs.modal', () => {
            modal.querySelectorAll('form').forEach(form => Validator.clearForm(form.id));
            cleanupUiLocks();
        });
    });
}

function cleanupUiLocks() {
    const hasShownModal = !!document.querySelector('.modal.show');
    if (!hasShownModal) {
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
    }
}

function bindReliableSidebarNavigation() {
    if (document.body.dataset.sidebarNavBound === '1') return;
    document.body.dataset.sidebarNavBound = '1';
    document.body.addEventListener('click', (e) => {
        const link = e.target.closest('#adminSidebar a.nav-link[href]');
        if (!link) return;
        const href = (link.getAttribute('href') || '').trim();
        if (!href || href === '#' || href.startsWith('javascript:')) return;
        e.preventDefault();
        if (window.innerWidth <= 768) {
            const sidebar = document.getElementById('adminSidebar');
            if (sidebar) sidebar.classList.remove('show');
        }
        window.location.assign(href);
    });
}

let select2AssetsPromise = null;
let domEnhancementTimer = null;
let domEnhancementRunning = false;
let adminNotificationsInterval = null;

function ensureSelect2Assets() {
    if (!window.jQuery) return Promise.resolve(false);
    if (window.jQuery?.fn?.select2) return Promise.resolve(true);
    if (select2AssetsPromise) return select2AssetsPromise;
    const cssId = 'transalca-select2-css';
    if (!document.getElementById(cssId)) {
        const link = document.createElement('link');
        link.id = cssId;
        link.rel = 'stylesheet';
        link.href = '/public/select2/select2.min.css';
        document.head.appendChild(link);
    }
    select2AssetsPromise = new Promise(resolve => {
        const scriptId = 'transalca-select2-js';
        const existing = document.getElementById(scriptId);
        const finalize = () => resolve(!!window.jQuery?.fn?.select2);
        if (existing) {
            if (window.jQuery?.fn?.select2) return finalize();
            existing.addEventListener('load', finalize, { once: true });
            existing.addEventListener('error', () => resolve(false), { once: true });
            return;
        }
        const script = document.createElement('script');
        script.id = scriptId;
        script.src = '/public/select2/select2.min.js';
        script.async = true;
        script.onload = finalize;
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
    });
    return select2AssetsPromise;
}

function enhanceSearchableSelects(root = document) {
    const scope = root instanceof Element ? root : document;
    const selects = Array.from(scope.querySelectorAll('select.form-select'));
    if (!selects.length) return;
    scope.querySelectorAll('.select-search-input').forEach(node => node.remove());
    ensureSelect2Assets().then(ready => {
        if (!ready || !window.jQuery) return;
        selects.forEach(select => {
            if (select.closest('.input-group')) return;
            if (select.hasAttribute('data-no-select2') || select.classList.contains('no-select2')) return;
            const $select = window.jQuery(select);
            const modal = select.closest('.modal');
            const modalId = modal?.id || '';
            const currentParent = select.dataset.select2Parent || '';
            const shouldRebuild = select.dataset.select2Ready === '1' && currentParent !== modalId;
            if (shouldRebuild && $select.hasClass('select2-hidden-accessible')) {
                $select.select2('destroy');
            }
            const optionsCount = String(select.options?.length || 0);
            if ($select.hasClass('select2-hidden-accessible') && select.dataset.select2OptionsCount !== optionsCount) {
                select.dataset.select2OptionsCount = optionsCount;
                $select.select2('destroy');
            }
            if (!$select.hasClass('select2-hidden-accessible')) {
                const firstEmptyOption = select.querySelector('option[value=""]');
                const config = {
                    width: select.style.width || '100%',
                    minimumResultsForSearch: select.hasAttribute('data-no-search') ? Infinity : 0
                };
                if (firstEmptyOption) {
                    config.placeholder = firstEmptyOption.textContent.trim();
                    config.allowClear = false;
                }
                if (modal) config.dropdownParent = window.jQuery(modal);
                $select.select2(config);
                select.dataset.select2Ready = '1';
                select.dataset.select2Parent = modalId;
                select.dataset.select2OptionsCount = optionsCount;
            }
            $select.off('.transalcaSelect2');
            $select.on('change.transalcaSelect2 select2:select.transalcaSelect2 select2:clear.transalcaSelect2', () => {
                if (select.form?.id && select.id) {
                    Validator.validateField(select.form.id, select.id);
                    updateFormSubmitState(select.form.id);
                } else {
                    clearFieldError(select);
                }
            });
            syncSelect2ValidationState(select);
        });
    });
}

class TablePaginator {
    constructor(element, options) {
        this.element = typeof element === 'string' ? document.getElementById(element) : element;
        if (!this.element) return;
        this.isTable = this.element.tagName === 'TABLE';
        this.tbody = this.isTable ? this.element.querySelector('tbody') : this.element;
        this.allData = options.allData || [];
        this.perPage = options.perPage || 30;
        this.currentPage = 1;
        this.renderRow = options.renderRow;
        this.onEmpty = options.onEmpty || (() => {
            return this.isTable 
                ? '<tr><td colspan="20" class="text-center py-4 text-muted">No se encontraron registros</td></tr>'
                : '<div class="p-3 text-muted text-center">No se encontraron registros</div>';
        });
        this.searchSelector = options.searchSelector;
        this.filterSelectors = options.filterSelectors || [];
        this.itemName = options.itemName || 'registros';
        
        this.initDom();
        this.initEvents();
        this.apply();
    }
    
    initDom() {
        const card = this.element.closest('.card') || this.element.parentElement;
        let pInfo = card.nextElementSibling && card.nextElementSibling.classList.contains('pagination-info-wrap') 
            ? card.nextElementSibling 
            : null;
        if (!pInfo) {
            pInfo = document.createElement('div');
            pInfo.className = 'd-flex justify-content-between align-items-center px-2 mb-4 pagination-info-wrap';
            pInfo.innerHTML = `
                <div class="d-flex align-items-center gap-3">
                    <div class="text-muted small paginator-info">Mostrando 0 a 0 de 0 registros</div>
                    <div class="d-flex align-items-center gap-1">
                        <span class="text-muted small" style="white-space: nowrap; font-size: 0.8rem;">Mostrar:</span>
                        <select class="form-select form-select-sm paginator-limit-select" style="width: auto; font-size: 0.75rem; padding: 0.2rem 1.6rem 0.2rem 0.4rem; height: 1.8rem; border-color: rgba(233, 93, 15, 0.2); border-radius: 4px;">
                            <option value="10">10</option>
                            <option value="20">20</option>
                            <option value="30">30</option>
                        </select>
                    </div>
                </div>
                <nav aria-label="Navegación">
                    <ul class="pagination pagination-sm mb-0 animate-fade-in paginator-controls">
                    </ul>
                </nav>
            `;
            card.parentNode.insertBefore(pInfo, card.nextSibling);
        }
        this.infoEl = pInfo.querySelector('.paginator-info');
        this.controlsEl = pInfo.querySelector('.paginator-controls');
        this.limitSelect = pInfo.querySelector('.paginator-limit-select');
    }
    
    initEvents() {
        let searchInput = null;
        if (this.searchSelector) {
            searchInput = document.querySelector(this.searchSelector);
        } else {
            const card = this.element.closest('.card') || this.element.parentElement;
            searchInput = card.previousElementSibling?.querySelector?.('input[type="search"], input[id*="search" i], .auto-table-search') || 
                          card.querySelector('input[id*="search" i], input[name*="search" i], .table-search-input');
        }
        
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                this.currentPage = 1;
                this.apply();
            });
            this.searchInput = searchInput;
        }
        
        this.filterSelectors.forEach(f => {
            const el = document.querySelector(f.selector);
            if (el) {
                el.addEventListener('change', () => {
                    this.currentPage = 1;
                    this.apply();
                });
            }
        });

        if (this.limitSelect) {
            this.limitSelect.value = this.perPage;
            this.limitSelect.addEventListener('change', () => {
                this.perPage = parseInt(this.limitSelect.value) || 30;
                this.currentPage = 1;
                this.apply();
            });
        }
    }
    
    updateData(newData) {
        this.allData = newData || [];
        this.currentPage = 1;
        this.apply();
    }
    
    apply() {
        let filtered = [...this.allData];
        
        if (this.searchInput) {
            const q = this.searchInput.value.trim().toLowerCase();
            if (q) {
                filtered = filtered.filter(item => {
                    return Object.values(item).some(val => 
                        val !== null && val !== undefined && 
                        String(val).toLowerCase().includes(q)
                    );
                });
            }
        }
        
        this.filterSelectors.forEach(f => {
            const el = document.querySelector(f.selector);
            if (el && el.value !== '') {
                const val = el.value;
                filtered = filtered.filter(item => f.filterFn(item, val));
            }
        });
        
        const total = filtered.length;
        const pages = Math.ceil(total / this.perPage);
        if (this.currentPage > pages && pages > 0) {
            this.currentPage = pages;
        }
        
        const start = total ? (this.currentPage - 1) * this.perPage + 1 : 0;
        const end = Math.min(this.currentPage * this.perPage, total);
        
        if (this.infoEl) {
            this.infoEl.textContent = `Mostrando ${start} a ${end} de ${total} ${this.itemName}`;
        }
        
        if (!this.tbody) return;
        this.tbody.innerHTML = '';
        if (total === 0) {
            this.tbody.innerHTML = this.onEmpty();
            if (this.controlsEl) this.controlsEl.innerHTML = '';
            return;
        }
        
        const pageData = filtered.slice((this.currentPage - 1) * this.perPage, this.currentPage * this.perPage);
        pageData.forEach((item, index) => {
            const actualIndex = (this.currentPage - 1) * this.perPage + index;
            const trHtmlOrEl = this.renderRow(item, actualIndex);
            if (typeof trHtmlOrEl === 'string') {
                this.tbody.innerHTML += trHtmlOrEl;
            } else if (trHtmlOrEl instanceof HTMLElement) {
                this.tbody.appendChild(trHtmlOrEl);
            }
        });
        
        hydrateDualPrices(this.tbody);
        normalizeActionButtons(this.tbody);
        
        this.renderControls(total, pages);
    }
    
    renderControls(total, pages) {
        if (!this.controlsEl) return;
        this.controlsEl.innerHTML = '';
        if (pages <= 1) return;
        
        const page = this.currentPage;
        
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#"><i class="bi bi-chevron-left"></i></a>`;
        if (page > 1) {
            prevLi.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = page - 1;
                this.apply();
            });
        }
        this.controlsEl.appendChild(prevLi);
        
        const maxVisible = 5;
        let startPage = Math.max(1, page - Math.floor(maxVisible / 2));
        let endPage = startPage + maxVisible - 1;
        
        if (endPage > pages) {
            endPage = pages;
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        if (startPage > 1) {
            const firstLi = document.createElement('li');
            firstLi.className = 'page-item';
            firstLi.innerHTML = `<a class="page-link" href="#">1</a>`;
            firstLi.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = 1;
                this.apply();
            });
            this.controlsEl.appendChild(firstLi);
            
            if (startPage > 2) {
                const ellipsisLi = document.createElement('li');
                ellipsisLi.className = 'page-item disabled';
                ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
                this.controlsEl.appendChild(ellipsisLi);
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${page === i ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            li.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = i;
                this.apply();
            });
            this.controlsEl.appendChild(li);
        }
        
        if (endPage < pages) {
            if (endPage < pages - 1) {
                const ellipsisLi = document.createElement('li');
                ellipsisLi.className = 'page-item disabled';
                ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
                this.controlsEl.appendChild(ellipsisLi);
            }
            const lastLi = document.createElement('li');
            lastLi.className = 'page-item';
            lastLi.innerHTML = `<a class="page-link" href="#">${pages}</a>`;
            lastLi.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = pages;
                this.apply();
            });
            this.controlsEl.appendChild(lastLi);
        }
        
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${page === pages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#"><i class="bi bi-chevron-right"></i></a>`;
        if (page < pages) {
            nextLi.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = page + 1;
                this.apply();
            });
        }
        this.controlsEl.appendChild(nextLi);
    }
}

function installListSearches(root = document) {
    const scope = root instanceof Element ? root : document;
    const tables = Array.from(scope.querySelectorAll('.content-area table'));
    tables.forEach((table, index) => {
        if (table.dataset.autoSearchReady === '1' || table.dataset.noAutoSearch === '1' || table.closest('.modal')) return;
        const contentArea = table.closest('.content-area');
        const card = table.closest('.card') || table.parentElement;
        if (!contentArea || !card || card.querySelector('.auto-table-search-wrap')) return;
        const manualSearch = card.querySelector('input[id*="search" i], input[name*="search" i], .table-search-input, [data-table-search]') || card.previousElementSibling?.querySelector?.('input[id*="search" i], input[name*="search" i], .table-search-input, [data-table-search]');
        if (manualSearch) {
            table.dataset.autoSearchReady = '1';
            return;
        }
        const wrap = document.createElement('div');
        wrap.className = 'auto-table-search-wrap d-flex justify-content-end mb-3';
        const input = document.createElement('input');
        input.type = 'search';
        input.className = 'form-control auto-table-search';
        input.placeholder = 'Buscar...';
        input.setAttribute('aria-label', 'Buscar en la lista');
        input.dataset.tableSearch = `auto-${index}`;
        wrap.appendChild(input);
        card.parentNode.insertBefore(wrap, card);
        input.addEventListener('input', () => {
            if (table.paginator) {
                table.paginator.currentPage = 1;
                table.paginator.apply();
                return;
            }
            const term = input.value.trim().toLowerCase();
            table.querySelectorAll('tbody tr').forEach(row => {
                if (row.querySelector('.empty-state')) return;
                row.style.display = !term || row.textContent.toLowerCase().includes(term) ? '' : 'none';
            });
        });
        table.dataset.autoSearchReady = '1';
    });
}

function isNoisyMutationNode(node) {
    if (!node || node.nodeType !== 1) return false;
    return !!node.closest?.('.select2-container, .select2-dropdown, .toast-container, .dropdown-menu');
}

function mutationNeedsEnhancement(mutation) {
    if (isNoisyMutationNode(mutation.target)) return false;
    if (mutation.target?.matches?.('select.form-select')) return true;
    if (mutation.target?.closest?.('select.form-select')) return true;
    for (const node of mutation.addedNodes || []) {
        if (node.nodeType !== 1 || isNoisyMutationNode(node)) continue;
        if (node.matches?.('select.form-select, .modal, table, button.btn, a.btn, [data-usd-price], [data-currency-toggle-label]')) return true;
        if (node.querySelector?.('select.form-select, .modal, table, button.btn, a.btn, [data-usd-price], [data-currency-toggle-label]')) return true;
    }
    return false;
}

function runDomEnhancements(root = document) {
    if (domEnhancementRunning) return;
    domEnhancementRunning = true;
    try {
        bindModalValidationReset();
        bindReliableSidebarNavigation();
        bindInputGuards();
        enhanceSearchableSelects(root);
        installListSearches(root);
        hydrateDualPrices(root);
        normalizeActionButtons(root);
        applyAdminDocumentTitle();
        initAdminNavbar();


        const sidebar = document.getElementById('adminSidebar');
        if (sidebar && !sidebar.dataset.scrollRestored) {
            sidebar.dataset.scrollRestored = '1';
            const scrollTop = sessionStorage.getItem('adminSidebarScrollTop');
            if (scrollTop !== null) {
                sidebar.scrollTop = parseInt(scrollTop);
            }
            sidebar.addEventListener('scroll', () => {
                sessionStorage.setItem('adminSidebarScrollTop', sidebar.scrollTop);
            });
        }
    } finally {
        domEnhancementRunning = false;
    }
}

function scheduleDomEnhancements(root = document) {
    clearTimeout(domEnhancementTimer);
    domEnhancementTimer = setTimeout(() => runDomEnhancements(root), 120);
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

function hydrateDualPrices(root = document) {
    root.querySelectorAll('[data-usd-price]').forEach(el => {
        el.textContent = formatUsdBs(el.dataset.usdPrice);
    });
    updateCurrencyMenuLabel();
}

function formatCurrency(amount) {
    return parseFloat(amount || 0).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('es-VE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function statusBadge(estado) {
    const raw = String(estado ?? '').trim();
    const normalized = raw.toLowerCase();
    const label = raw || 'Inactivo';
    if (['al dia', 'al día'].includes(normalized)) {
        return '<span class="badge-status badge-active">Al día</span>';
    }
    if (estado === 1 || estado === true || ['activo', 'activa'].includes(normalized)) {
        return '<span class="badge-status badge-active">Activo</span>';
    }
    if (['aprobado', 'aprobada', 'pagado', 'pagada', 'verificado', 'verificada', 'completado', 'completada', 'entregado', 'entregada', 'recibido', 'recibida'].includes(normalized)) {
        return `<span class="badge-status badge-active">${escapeHtml(label)}</span>`;
    }
    if (['pendiente', 'procesando', 'enviado', 'enviada', 'abierto', 'abierta', 'media'].includes(normalized)) {
        return `<span class="badge-status badge-pending">${escapeHtml(label)}</span>`;
    }
    if (['credito_activo', 'credito activo', 'crédito activo'].includes(normalized)) {
        return '<span class="badge-status badge-pending">Crédito activo</span>';
    }
    if (['deudora', 'vencido', 'vencida'].includes(normalized)) {
        return `<span class="badge-status badge-inactive">${escapeHtml(label)}</span>`;
    }
    return `<span class="badge-status badge-inactive">${escapeHtml(label)}</span>`;
}

function getAdminModuleTitle() {
    const page = window.location.pathname.split('/').pop();
    const titles = {
        dashboard: 'Dashboard',
        clients: 'Gestionar Clientes',
        companies: 'Gestionar Empresas',
        products: 'Gestionar Productos',
        categories: 'Gestionar Categorías',
        brands: 'Gestionar Marcas',
        suppliers: 'Gestionar Proveedores',
        inventory: 'Gestionar Stock de producto',
        services: 'Gestionar Servicios',
        service_mechanics: 'Gestionar Servicio Mecánico',
        mechanics: 'Gestionar Mecánicos',
        orders_sales: 'Reporte Orden de Venta',
        credit: 'Gestionar Crédito',
        tickets: 'Gestionar Tickets de Soporte',
        payments: 'Gestionar Pagos',
        payment_methods: 'Gestionar Métodos de Pago',
        promotions: 'Gestionar Promociones',
        users: 'Gestionar Usuarios',
        roles: 'Gestionar Roles y Permisos',
        qr: 'Gestionar Códigos QR',
        reports: 'Reportes',
        report_stats: 'Reportes Estadísticos',
        tasas: 'Gestionar Tasa de Cambio',
        bitacora: 'Gestionar Bitácora',
        backup: 'Gestionar Respaldos',
        profile: 'Gestionar Mi Perfil',
        sucursales: 'Gestionar Sucursales',
        guide: 'Guía'
    };
    return titles[page] || 'Panel de Administración';
}

function applyAdminDocumentTitle() {
    const title = getAdminModuleTitle();
    document.title = `Transalca Admin | ${title}`;
    const titleEl = document.getElementById('pageTitle');
    if (titleEl) titleEl.textContent = title;
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

document.addEventListener('DOMContentLoaded', () => {
    installSweetAlertDefaults();
    cleanupUiLocks();
    applyAdminDocumentTitle();
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
    runDomEnhancements();
    loadExchangeRatesCached().then(() => hydrateDualPrices());
    const observer = new MutationObserver(mutations => {
        if (mutations.some(mutationNeedsEnhancement)) {
            scheduleDomEnhancements();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setInterval(cleanupUiLocks, 5000);
    if (document.getElementById('sidebarContainer')) {
        startAdminValidationPolling();
    }
});

document.addEventListener('click', async (e) => {
    const closeToast = e.target.closest('.close-toast, .toast-close');
    if (closeToast) {
        e.preventDefault();
        e.stopPropagation();
        dismissToast(closeToast.closest('.toast-custom'));
        return;
    }
    const currencyToggle = e.target.closest('[data-currency-toggle]');
    if (currencyToggle) {
        e.preventDefault();
        toggleCurrency();
        return;
    }
    const adminNotificationsReadAll = e.target.closest('[data-admin-notifications-read-all]');
    if (adminNotificationsReadAll) {
        e.preventDefault();
        markAllRead();
        return;
    }
    const adminNotification = e.target.closest('[data-admin-notification-id]');
    if (adminNotification) {
        e.preventDefault();
        const id = Number(adminNotification.dataset.adminNotificationId || 0);
        if (id) markRead(id);
        return;
    }
    const logoutTarget = e.target.closest('#btnLogout, #navLogout');
    if (logoutTarget) {
        e.preventDefault();
        await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
        window.location.href = '/auth/login';
    }
}, true);

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
            applyAdminDocumentTitle();
        }
    } catch (e) { }
}

function initAdminNavbar() {
    const notifList = document.getElementById('notifList');
    if (!notifList) return;
    const navbar = notifList.closest('nav');
    if (navbar?.dataset.adminNavbarReady === '1') return;
    if (navbar) navbar.dataset.adminNavbarReady = '1';
    loadNavSession();
    loadAdminRates();
    loadNotifications();
    if (!adminNotificationsInterval) {
        adminNotificationsInterval = setInterval(() => {
            if (document.getElementById('notifList')) loadNotifications();
        }, 30000);
    }
}

async function loadAdminRates() {
    try {
        const res = await fetch('/api/rates/', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && data.data) {
            const bcv = data.data.bcv?.usd || 0;
            const bcvEl = document.getElementById('rateBcvAdmin');
            if (bcvEl) bcvEl.textContent = bcv > 0 ? bcv.toFixed(2) : 'N/D';
        }
    } catch (e) { }
}

async function loadNotifications() {
    try {
        const res = await fetch('/api/notifications/', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status !== 'success') return;
        const list = data.data || [];
        const unread = list.filter(n => !n.leida).length;
        const badge = document.getElementById('notifBadge');
        if (badge) {
            badge.textContent = unread;
            badge.style.display = unread > 0 ? '' : 'none';
        }
        const container = document.getElementById('notifList');
        if (!container) return;
        if (list.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-3" style="font-size:0.8rem;">Sin notificaciones</div>';
            return;
        }
        container.innerHTML = list.slice(0, 8).map(n => {
            const icons = { mantenimiento:'bi-wrench', aceite:'bi-droplet', ticket:'bi-ticket', promocion:'bi-gift', sistema:'bi-gear', combustible:'bi-fuel-pump', filtro:'bi-filter', refrigerante:'bi-snow', caucho:'bi-circle' };
            const icon = icons[n.tipo] || 'bi-bell';
            const bg = n.leida ? '' : 'background:rgba(var(--bs-primary-rgb),0.05);';
            const title = escapeHtml(n.titulo || n.mensaje || 'Notificacion');
            const message = escapeHtml(n.mensaje ? String(n.mensaje).substring(0, 60) : '');
            const created = escapeHtml(n.created_at || '');
            return `<div class="px-3 py-2 border-bottom" style="font-size:0.8rem;cursor:pointer;${bg}" data-admin-notification-id="${Number(n.id) || 0}"><div class="d-flex gap-2"><i class="bi ${icon}" style="color:var(--primary);font-size:0.95rem;margin-top:2px;"></i><div><div style="font-weight:${n.leida?'400':'600'};">${title}</div><div class="text-muted" style="font-size:0.7rem;">${message}</div><div class="text-muted" style="font-size:0.65rem;">${created}</div></div></div></div>`;
        }).join('');
    } catch (e) { }
}

async function markRead(id) {
    try {
        await fetch(`/api/notifications/${id}/read`, { method: 'PUT', credentials: 'same-origin' });
        loadNotifications();
    } catch (e) { }
}

async function markAllRead() {
    try {
        await fetch('/api/notifications/read-all', { method: 'PUT', credentials: 'same-origin' });
        loadNotifications();
    } catch (e) { }
}

const shownValidationRequestIds = new Set();

function getShownValidationRequestIds() {
    return shownValidationRequestIds;
}

function markValidationRequestIdAsShown(id) {
    shownValidationRequestIds.add(id);
}

function markValidationAlertSeen(id) {
    fetch('/api/scanner/alerta-vista', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ solicitud_id: id })
    }).catch(() => { });
}

function startAdminValidationPolling() {
    if (typeof Swal === 'undefined') {
        let link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/public/sweetalert2/sweetalert2.min.css';
        document.head.appendChild(link);

        let script = document.createElement('script');
        script.src = '/public/sweetalert2/sweetalert2.all.min.js';
        document.head.appendChild(script);
    }

    setInterval(pollPendingValidations, 10000);
    setTimeout(pollPendingValidations, 2500);
}

async function pollPendingValidations() {
    if (typeof Swal === 'undefined') return;
    try {
        const res = await fetch('/api/scanner/solicitudes-pendientes', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && data.data && data.data.length > 0) {
            const shownIds = getShownValidationRequestIds();
            const pending = data.data.find(r => !shownIds.has(r.id));
            if (pending) {
                showValidationAlert(pending);
            }
        }
    } catch (e) {
        console.error('Error polling validations:', e);
    }
}

function showValidationAlert(req) {
    markValidationRequestIdAsShown(req.id);

    const title = req.tipo === 'validar_pago' ? 'Solicitud de Validación de Pago' : 'Escaneo de Factura Pagada';
    let timerInterval;
    Swal.fire({
        title: title,
        html: `
            <p>Hay una solicitud pendiente de validación:</p>
            <div class="text-start border rounded p-2 bg-light small mb-3">
                <strong>Cliente:</strong> ${escapeHtml(req.cliente_nombre)}<br>
                <strong>Teléfono:</strong> ${escapeHtml(req.cliente_telefono || 'N/A')}<br>
                <strong>Pedido:</strong> #${req.orden_venta_id}<br>
                <strong>Monto Total:</strong> $${req.total.toFixed(2)} (${req.metodo_pago})<br>
                <strong>Tipo:</strong> ${req.tipo === 'validar_pago' ? 'Validar Pago' : 'Factura'}
            </div>
            <p class="text-muted small">Cerrando automáticamente en <b>180</b> segundos...</p>
        `,
        icon: 'info',
        showCancelButton: true,
        confirmButtonText: 'Ver Datos',
        cancelButtonText: 'No ver / Rechazar',
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#dc3545',
        timer: 180000,
        timerProgressBar: true,
        didOpen: () => {
            const content = Swal.getHtmlContainer();
            const b = content.querySelector('b');
            timerInterval = setInterval(() => {
                if (b) {
                    b.textContent = Math.ceil(Swal.getTimerLeft() / 1000);
                }
            }, 1000);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
        markValidationAlertSeen(req.id);
        if (result.isConfirmed) {
            openAdminValidationDetailsModal(req);
        }
    });
}

function openAdminValidationDetailsModal(req) {
    const orderCurrency = (req.moneda || 'usd').toLowerCase();
    const symbol = orderCurrency === 'bs' ? 'Bs. ' : '$';

    const detailsRows = (req.detalles || []).map(d => `
        <tr>
            <td style="padding:4px 8px; text-align:left;">${escapeHtml(d.item_nombre || '-')}</td>
            <td style="padding:4px 8px;">${d.cantidad || 0}</td>
            <td style="padding:4px 8px; text-align:right;">${symbol}${parseFloat(d.precio_unitario || 0).toFixed(2)}</td>
            <td style="padding:4px 8px; text-align:right;">${symbol}${parseFloat(d.subtotal || 0).toFixed(2)}</td>
        </tr>
    `).join('');

    let comprobanteHtml = '';
    if (req.comprobante_img) {
        comprobanteHtml = `
            <div class="mt-3 text-start">
                <strong>Comprobante de Pago:</strong><br>
                <img src="/public/assets/comprobantes/${escapeHtml(req.comprobante_img)}"
                     class="img-fluid rounded border mt-2"
                     style="max-height: 240px; width: 100%; object-fit: contain;"
                     alt="Comprobante">
            </div>
        `;
    }

    const isAlreadyApproved = ['aprobada', 'aprobado', 'verificado', 'verificada', 'pagado', 'pagada'].includes(String(req.estado_orden || '').toLowerCase());

    Swal.fire({
        title: `Detalle de Validación - Pedido #${req.orden_venta_id}`,
        width: '600px',
        html: `
            <div class="text-start" style="font-size: 0.85rem;">
                <div class="row g-2 mb-3">
                    <div class="col-6"><strong>Cliente:</strong> ${escapeHtml(req.cliente_nombre)}</div>
                    <div class="col-6"><strong>Cédula:</strong> ${escapeHtml(req.cliente_cedula)}</div>
                    <div class="col-6"><strong>Email:</strong> ${escapeHtml(req.cliente_email || '-')}</div>
                    <div class="col-6"><strong>Teléfono:</strong> ${escapeHtml(req.cliente_telefono || '-')}</div>
                    <div class="col-6"><strong>Método Pago:</strong> ${escapeHtml(req.metodo_pago)}</div>
                    <div class="col-6"><strong>Estado:</strong> ${escapeHtml(req.estado_orden)}</div>
                </div>

                <h6 class="fw-bold border-bottom pb-1">Productos / Servicios</h6>
                <table style="width:100%; font-size: 0.8rem; border-collapse: collapse;" class="table table-sm mb-3">
                    <thead>
                        <tr style="background:#f1f5f9;">
                            <th style="padding:4px 8px; text-align:left;">Item</th>
                            <th style="padding:4px 8px;">Cant</th>
                            <th style="padding:4px 8px; text-align:right;">Precio</th>
                            <th style="padding:4px 8px; text-align:right;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${detailsRows || '<tr><td colspan="4" class="text-center text-muted">Sin detalles</td></tr>'}
                    </tbody>
                </table>

                <div class="d-flex justify-content-between align-items-center">
                    <strong>Total del Pedido:</strong>
                    <span class="fs-5 fw-bold" style="color: #e95d0f;">${symbol}${parseFloat(req.total).toFixed(2)}</span>
                </div>

                ${comprobanteHtml}
            </div>
        `,
        showDenyButton: !isAlreadyApproved,
        showConfirmButton: !isAlreadyApproved,
        showCancelButton: true,
        confirmButtonText: '<i class="bi bi-check-lg me-1"></i>Validar',
        denyButtonText: '<i class="bi bi-x-lg me-1"></i>Rechazar',
        cancelButtonText: 'Cerrar',
        confirmButtonColor: '#28a745',
        denyButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d'
    }).then((result) => {
        if (!isAlreadyApproved) {
            if (result.isConfirmed) {
                respondToValidationRequest(req.id, 'aprobar');
            } else if (result.isDenied) {
                respondToValidationRequest(req.id, 'rechazar');
            }
        }
    });
}

async function respondToValidationRequest(reqId, responseType) {
    try {
        const res = await fetch('/api/scanner/responder-validacion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                solicitud_id: reqId,
                respuesta: responseType
            }),
            credentials: 'same-origin'
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(data.message, 'success');
            if (typeof loadData === 'function') loadData();
        } else {
            showToast(data.message || 'Error al guardar respuesta', 'error');
        }
    } catch (e) {
        showToast('Error de conexión', 'error');
    }
}
