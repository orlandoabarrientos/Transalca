$(document).ready(function () {
    const page = window.location.pathname.split('/').pop();
    
    const params = new URLSearchParams(window.location.search);
    const nextVal = params.get('next');
    if (nextVal) {
        if (page === 'login') {
            const regLink = document.querySelector('a[href="/auth/register"]');
            if (regLink) regLink.href = `/auth/register?next=${encodeURIComponent(nextVal)}`;
        } else if (page === 'register') {
            const logLink = document.querySelector('a[href="/auth/login"]');
            if (logLink) logLink.href = `/auth/login?next=${encodeURIComponent(nextVal)}`;
        }
    }

    if (page === 'login') setupLogin();
    else if (page === 'register') setupRegister();
    else if (page === 'recover') setupRecover();
    else if (page === 'reset') setupReset();
});

function setupLogin() {
    Validator.setRules('loginForm', {
        loginEmail: { required: true, email: true, requiredMsg: 'El correo es requerido' },
        loginPassword: { required: true, requiredMsg: 'La contrasena es requerida' }
    });
    Validator.setupRealtime('loginForm');

    document.getElementById('loginForm')?.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!Validator.validate('loginForm')) return;
        const nextTarget = new URLSearchParams(window.location.search).get('next') || '';
        const data = {
            email: document.getElementById('loginEmail').value,
            password: document.getElementById('loginPassword').value,
            next: nextTarget
        };
        try {
            const res = await apiCall('/auth/do_login', 'POST', data);
            if (res.status === 'error') {
                if (res.errors) Validator.showServerErrors('loginForm', res.errors);
                showToast(res.message, 'error');
                return;
            }
            showToast('Bienvenido.', 'success');
            const safeRedirect = (res.redirect && res.redirect.startsWith('/') && !res.redirect.startsWith('//')) ? res.redirect : '/client/home';
            setTimeout(() => window.location.href = safeRedirect, 500);
        } catch (e) {}
    });
}

function setupRegister() {
    const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$/;
    const PHONE_REGEX = /^04\d{9}$/;
    Validator.setRules('registerForm', {
        regNombre: { required: true, pattern: /^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$/u, requiredMsg: 'Nombre requerido', patternMsg: 'Solo letras y espacios' },
        regApellido: { required: true, pattern: /^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$/u, requiredMsg: 'Apellido requerido', patternMsg: 'Solo letras y espacios' },
        regCedulaPrefijo: { required: true, custom: v => ['V', 'E', 'J', 'G', 'P'].includes(v), customMsg: 'El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente.' },
        regCedula: { required: true, pattern: /^\d{7,8}$/, requiredMsg: 'Cedula requerida', patternMsg: 'La cedula debe tener 7 u 8 digitos' },
        regTelefono: { required: true, pattern: PHONE_REGEX, requiredMsg: 'Telefono requerido', patternMsg: 'Debe tener 11 digitos y comenzar por 04' },
        regEmail: { required: true, email: true, requiredMsg: 'Correo requerido' },
        regPassword: { required: true, pattern: PASSWORD_REGEX, requiredMsg: 'Contrasena requerida', patternMsg: 'Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero, 1 especial' },
        regConfirmPassword: { required: true, match: 'regPassword', requiredMsg: 'Confirme la contrasena', matchMsg: 'Las contrasenas no coinciden' }
    });
    Validator.setupRealtime('registerForm');
    updatePasswordStrength('regPassword', 'passwordStrengthBar');

    const toggleReg = document.getElementById('toggleRegPassword');
    if (toggleReg) {
        toggleReg.addEventListener('click', function () {
            const input = document.getElementById('regPassword');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    }

    const toggleRegConfirm = document.getElementById('toggleRegConfirmPassword');
    if (toggleRegConfirm) {
        toggleRegConfirm.addEventListener('click', function () {
            const input = document.getElementById('regConfirmPassword');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    }

    document.getElementById('regCedula')?.addEventListener('input', debounceAuthUnique(() => validateRegisterUnique('cedula'), 350));
    document.getElementById('regCedulaPrefijo')?.addEventListener('change', debounceAuthUnique(() => validateRegisterUnique('cedula'), 350));
    document.getElementById('regEmail')?.addEventListener('input', debounceAuthUnique(() => validateRegisterUnique('email'), 350));

    document.getElementById('registerForm')?.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!Validator.validate('registerForm')) return;
        const data = {
            nombre: document.getElementById('regNombre').value,
            apellido: document.getElementById('regApellido').value,
            cedula_prefijo: document.getElementById('regCedulaPrefijo').value,
            cedula: buildDocumentValue('regCedulaPrefijo', 'regCedula'),
            telefono: document.getElementById('regTelefono').value,
            direccion: document.getElementById('regDireccion')?.value || '',
            email: document.getElementById('regEmail').value,
            password: document.getElementById('regPassword').value,
            confirm_password: document.getElementById('regConfirmPassword').value
        };
        try {
            const res = await apiCall('/auth/do_register', 'POST', data);
            if (res.status === 'error') {
                if (res.errors) Validator.showServerErrors('registerForm', res.errors);
                showToast(res.message, 'error');
                return;
            }
            showToast(res.message, 'success');
            const nextVal = new URLSearchParams(window.location.search).get('next');
            const loginUrl = nextVal ? `/auth/login?next=${encodeURIComponent(nextVal)}` : '/auth/login';
            setTimeout(() => window.location.href = loginUrl, 1500);
        } catch (e) {}
    });
}

function debounceAuthUnique(fn, ms) {
    let timer;
    return function () {
        clearTimeout(timer);
        timer = setTimeout(fn, ms);
    };
}

async function validateRegisterUnique(field) {
    const map = { cedula: 'regCedula', email: 'regEmail' };
    const input = document.getElementById(map[field]);
    if (!input) return true;
    if (!input.value.trim()) {
        clearFieldError(input);
        updateFormSubmitState('registerForm');
        return true;
    }
    if (!Validator.validateField('registerForm', map[field])) {
        updateFormSubmitState('registerForm');
        return false;
    }
    try {
        const value = field === 'cedula' ? buildDocumentValue('regCedulaPrefijo', 'regCedula') : input.value;
        const cedula = buildDocumentValue('regCedulaPrefijo', 'regCedula');
        const res = await fetch('/auth/check-unique', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ field, value, cedula })
        });
        const data = await res.json();
        if (data.status === 'success' && data.exists) {
            const msg = field === 'cedula' ? 'Esta cedula ya esta registrada.' : 'Este correo ya esta registrado.';
            setFieldError(input, msg);
            updateFormSubmitState('registerForm');
            return false;
        }
        if (data.status === 'success') {
            clearFieldError(input);
        }
        updateFormSubmitState('registerForm');
    } catch (e) {}
    return true;
}

function setupRecover() {
    Validator.setRules('recoverForm', {
        recoverEmail: { required: true, email: true, requiredMsg: 'Ingrese su correo' }
    });
    Validator.setupRealtime('recoverForm');

    const form = document.getElementById('recoverForm');
    const emailInput = document.getElementById('recoverEmail');
    const btnSubmit = document.getElementById('btnSubmitRecover') || form?.querySelector('button[type="submit"]');
    let countdownInterval = null;

    function formatCountdown(sec) {
        if (sec >= 3600) {
            const h = Math.floor(sec / 3600);
            const m = Math.floor((sec % 3600) / 60);
            const s = sec % 60;
            return `${h}h ${m < 10 ? '0' : ''}${m}m ${s < 10 ? '0' : ''}${s}s`;
        }
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
    }

    function getStorageKey(email) {
        const clean = (email || '').trim().toLowerCase();
        return `transalca_recover_until_${clean}`;
    }

    function getRemainingSeconds(email) {
        const key = getStorageKey(email);
        const stored = localStorage.getItem(key);
        if (!stored) return 0;
        const target = parseInt(stored, 10);
        const diff = target - Date.now();
        if (diff <= 0) {
            localStorage.removeItem(key);
            return 0;
        }
        return Math.ceil(diff / 1000);
    }

    function startTimer(seconds, email) {
        if (!btnSubmit) return;
        const key = getStorageKey(email);
        const targetTime = Date.now() + (seconds * 1000);
        localStorage.setItem(key, targetTime.toString());
        localStorage.setItem('transalca_recover_last_email', (email || '').trim().toLowerCase());

        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }

        btnSubmit.disabled = true;

        function tick() {
            const diff = targetTime - Date.now();
            if (diff <= 0) {
                if (countdownInterval) {
                    clearInterval(countdownInterval);
                    countdownInterval = null;
                }
                localStorage.removeItem(key);
                btnSubmit.disabled = false;
                btnSubmit.textContent = 'Volver a enviar';
                return;
            }
            const sec = Math.ceil(diff / 1000);
            btnSubmit.textContent = `Reenviar en ${formatCountdown(sec)}`;
        }

        tick();
        countdownInterval = setInterval(tick, 1000);
    }

    function syncCooldownForCurrentInput() {
        const email = emailInput ? emailInput.value.trim() : '';
        if (!email) {
            const lastEmail = localStorage.getItem('transalca_recover_last_email') || '';
            if (lastEmail && emailInput && !emailInput.value) {
                emailInput.value = lastEmail;
                const remaining = getRemainingSeconds(lastEmail);
                if (remaining > 0) {
                    startTimer(remaining, lastEmail);
                    return;
                } else if (btnSubmit) {
                    btnSubmit.disabled = false;
                    btnSubmit.textContent = 'Volver a enviar';
                    return;
                }
            }
            if (countdownInterval) {
                clearInterval(countdownInterval);
                countdownInterval = null;
            }
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.textContent = 'Enviar enlace de recuperacion';
            }
            return;
        }
        const remaining = getRemainingSeconds(email);
        if (remaining > 0) {
            startTimer(remaining, email);
        } else {
            if (countdownInterval) {
                clearInterval(countdownInterval);
                countdownInterval = null;
            }
            if (btnSubmit) {
                btnSubmit.disabled = false;
                const lastEmail = localStorage.getItem('transalca_recover_last_email') || '';
                const wasSent = lastEmail === email.toLowerCase();
                btnSubmit.textContent = wasSent ? 'Volver a enviar' : 'Enviar enlace de recuperacion';
            }
        }
    }

    syncCooldownForCurrentInput();

    emailInput?.addEventListener('input', function () {
        syncCooldownForCurrentInput();
    });

    form?.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (btnSubmit && btnSubmit.disabled) return;
        if (!Validator.validate('recoverForm')) return;

        const emailVal = emailInput ? emailInput.value.trim() : '';
        const prevText = btnSubmit ? btnSubmit.textContent : '';
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Enviando...';
        }

        try {
            const res = await apiCall('/auth/do_recover', 'POST', { email: emailVal });
            if (res.status === 'error') {
                if (res.errors) Validator.showServerErrors('recoverForm', res.errors);
                showToast(res.message, 'error');
                if (res.cooldown) {
                    startTimer(res.cooldown, emailVal);
                } else if (btnSubmit) {
                    btnSubmit.disabled = false;
                    btnSubmit.textContent = prevText;
                }
                return;
            }
            showToast(res.message, 'success');
            const cooldownSec = res.cooldown || 300;
            startTimer(cooldownSec, emailVal);
        } catch (err) {
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.textContent = prevText;
            }
            showToast('No se pudo completar la solicitud.', 'error');
        }
    });
}

function setupReset() {
    const params = new URLSearchParams(window.location.search);
    const token = (params.get('token') || '').trim();
    const tokenInput = document.getElementById('resetToken');
    if (tokenInput && token) {
        tokenInput.value = token;
    }
    if (!token) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'error',
                title: 'Token no encontrado',
                text: 'El enlace de recuperacion es invalido o no contiene un token valido.',
                confirmButtonColor: '#E67E22'
            }).then(() => {
                window.location.href = '/auth/login';
            });
        } else {
            showToast('El enlace de recuperacion es invalido.', 'error');
            setTimeout(() => window.location.href = '/auth/login', 1500);
        }
        return;
    }

    const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$/;

    const toggleReset = document.getElementById('toggleResetPassword');
    if (toggleReset) {
        toggleReset.addEventListener('click', function () {
            const input = document.getElementById('resetPassword');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    }

    const toggleConfirm = document.getElementById('toggleResetConfirmPassword');
    if (toggleConfirm) {
        toggleConfirm.addEventListener('click', function () {
            const input = document.getElementById('resetConfirmPassword');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    }

    Validator.setRules('resetForm', {
        resetPassword: {
            required: true,
            pattern: PASSWORD_REGEX,
            requiredMsg: 'La contrasena es obligatoria',
            patternMsg: 'Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero, 1 especial'
        },
        resetConfirmPassword: {
            required: true,
            match: 'resetPassword',
            requiredMsg: 'Confirme su contrasena',
            matchMsg: 'Las contrasenas no coinciden'
        }
    });
    Validator.setupRealtime('resetForm');

    document.getElementById('resetForm')?.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!Validator.validate('resetForm')) return;
        const password = document.getElementById('resetPassword').value;
        const confirm_password = document.getElementById('resetConfirmPassword').value;
        try {
            const res = await apiCall('/auth/do_reset', 'POST', {
                token: token,
                password: password,
                confirm_password: confirm_password
            });
            if (res.status === 'error') {
                if (res.errors) Validator.showServerErrors('resetForm', res.errors);
                showToast(res.message, 'error');
                return;
            }
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'success',
                    title: 'Contrasena modificada',
                    text: res.message || 'Su contrasena ha sido actualizada con exito. Ahora puede iniciar sesion.',
                    confirmButtonColor: '#E67E22'
                }).then(() => {
                    window.location.href = '/auth/login';
                });
            } else {
                showToast(res.message || 'Contrasena modificada correctamente.', 'success');
                setTimeout(() => window.location.href = '/auth/login', 1500);
            }
        } catch (err) {
            showToast('No se pudo completar la solicitud.', 'error');
        }
    });
}
