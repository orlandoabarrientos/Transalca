
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
        if (typeof options === 'object' && options && !options.showCancelButton && !options.timer) {
            options = { timer: 5000, timerProgressBar: true, showConfirmButton: true, ...options };
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
        const el = document.getElementById(field);
        if (!el) return true;

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

function updateFormSubmitState(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    const modal = form.closest('.modal-content') || form;
    const hasErrors = !!form.querySelector('.is-invalid');
    const isDirty = form._initialState ? (serializeForm(form) !== form._initialState) : true;
    modal.querySelectorAll('button[type="submit"], button[onclick*="save"], button[onclick*="Save"], #btnSaveVehicle, #btnSavePromo').forEach(btn => {
        if (!btn.dataset.loading) {
            btn.disabled = hasErrors || (form._initialState ? !isDirty : false);
        }
    });
}

function inputNumericMode(input) {
    const key = `${input.id || ''} ${input.name || ''}`.toLowerCase();
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
            const $select = window.jQuery(select);
            const modal = select.closest('.modal');
            const modalId = modal?.id || '';
            const currentParent = select.dataset.select2Parent || '';
            const shouldRebuild = select.dataset.select2Ready === '1' && currentParent !== modalId;
            if (shouldRebuild && $select.hasClass('select2-hidden-accessible')) {
                $select.select2('destroy');
            }
            if (!$select.hasClass('select2-hidden-accessible')) {
                const firstEmptyOption = select.querySelector('option[value=""]');
                const config = {
                    width: select.style.width || '100%',
                    minimumResultsForSearch: select.hasAttribute('data-no-search') ? Infinity : 0
                };
                if (firstEmptyOption) config.placeholder = firstEmptyOption.textContent.trim();
                if (modal) config.dropdownParent = window.jQuery(modal);
                $select.select2(config);
                select.dataset.select2Ready = '1';
                select.dataset.select2Parent = modalId;
                select.dataset.select2OptionsCount = String(select.options?.length || 0);
            } else {
                const optionsCount = String(select.options?.length || 0);
                if (select.dataset.select2OptionsCount !== optionsCount) {
                    select.dataset.select2OptionsCount = optionsCount;
                    $select.trigger('change.select2');
                }
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

        // Restore and persist sidebar scroll
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
    if (estado === 1 || estado === true || ['activo', 'activa'].includes(normalized)) {
        return '<span class="badge-status badge-active">Activo</span>';
    }
    if (['aprobado', 'aprobada', 'pagado', 'pagada', 'verificado', 'verificada', 'completado', 'completada', 'entregado', 'entregada', 'recibido', 'recibida'].includes(normalized)) {
        return `<span class="badge-status badge-active">${escapeHtml(label)}</span>`;
    }
    if (['pendiente', 'procesando', 'enviado', 'enviada', 'abierto', 'abierta', 'media'].includes(normalized)) {
        return `<span class="badge-status badge-pending">${escapeHtml(label)}</span>`;
    }
    return `<span class="badge-status badge-inactive">${escapeHtml(label)}</span>`;
}

function getAdminModuleTitle() {
    const page = window.location.pathname.split('/').pop();
    const titles = {
        dashboard: 'Dashboard',
        clients: 'Gestionar Clientes',
        products: 'Gestionar Productos',
        categories: 'Gestionar Categorías',
        brands: 'Gestionar Marcas',
        suppliers: 'Gestionar Proveedores',
        inventory: 'Gestionar Stock de producto',
        services: 'Gestionar Servicios',
        service_mechanics: 'Gestionar Servicio Mecánico',
        mechanics: 'Gestionar Mecánicos',
        orders_sales: 'Reporte Orden de Venta',
        tickets: 'Gestionar Tickets de Soporte',
        payments: 'Gestionar Comprobantes de Pago',
        promotions: 'Gestionar Promociones',
        users: 'Gestionar Usuarios',
        roles: 'Gestionar Roles y Permisos',
        qr: 'Gestionar Códigos QR',
        reports: 'Reportes',
        report_stats: 'Reportes estadísticos',
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
