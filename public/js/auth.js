$(document).ready(function () {
    const page = window.location.pathname.split('/').pop();
    if (page === 'login') setupLogin();
    else if (page === 'register') setupRegister();
    else if (page === 'recover') setupRecover();
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
            cedula_numero: document.getElementById('regCedula').value,
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
            setTimeout(() => window.location.href = '/auth/login', 1500);
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
    if (!input || !input.value.trim()) return true;
    if (!Validator.validateField('registerForm', map[field])) return false;
    try {
        const value = field === 'cedula' ? buildDocumentValue('regCedulaPrefijo', 'regCedula') : input.value;
        const res = await fetch(`/auth/check-unique?field=${field}&value=${encodeURIComponent(value)}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status === 'success' && data.exists) {
            const msg = field === 'cedula' ? 'Esta cedula ya esta registrada.' : 'Este correo ya esta registrado.';
            Validator.showServerErrors('registerForm', { [map[field]]: msg });
            return false;
        }
    } catch (e) {}
    return true;
}

function setupRecover() {
    Validator.setRules('recoverForm', {
        recoverEmail: { required: true, email: true, requiredMsg: 'Ingrese su correo' }
    });
    Validator.setupRealtime('recoverForm');

    document.getElementById('recoverForm')?.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!Validator.validate('recoverForm')) return;
        try {
            const res = await apiCall('/auth/do_recover', 'POST', { email: document.getElementById('recoverEmail').value });
            if (res.status === 'error') {
                if (res.errors) Validator.showServerErrors('recoverForm', res.errors);
                showToast(res.message, 'error');
                return;
            }
            showToast(res.message, 'success');
        } catch (e) {}
    });
}
