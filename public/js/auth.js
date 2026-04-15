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
            showToast('Bienvenido!', 'success');
            const safeRedirect = (res.redirect && res.redirect.startsWith('/') && !res.redirect.startsWith('//')) ? res.redirect : '/client/home';
            setTimeout(() => window.location.href = safeRedirect, 500);
        } catch (e) {
            showToast('Error al iniciar sesion', 'error');
        }
    });
}

function setupRegister() {
    const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$/;
    Validator.setRules('registerForm', {
        regNombre: { required: true, minLength: 2, requiredMsg: 'Nombre requerido' },
        regApellido: { required: true, minLength: 2, requiredMsg: 'Apellido requerido' },
        regCedula: { required: true, minLength: 5, requiredMsg: 'Cedula requerida', minLengthMsg: 'Minimo 5 caracteres' },
        regEmail: { required: true, email: true, requiredMsg: 'Correo requerido' },
        regPassword: { required: true, pattern: PASSWORD_REGEX, requiredMsg: 'Contrasena requerida', patternMsg: 'Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero, 1 especial' },
        regConfirmPassword: { required: true, match: 'regPassword', requiredMsg: 'Confirme la contrasena', matchMsg: 'Las contrasenas no coinciden' }
    });
    Validator.setupRealtime('registerForm');
    updatePasswordStrength('regPassword', 'passwordStrengthBar');

    document.getElementById('registerForm')?.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!Validator.validate('registerForm')) return;
        const data = {
            nombre: document.getElementById('regNombre').value,
            apellido: document.getElementById('regApellido').value,
            cedula: document.getElementById('regCedula').value,
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
        } catch (e) {
            showToast('Error al registrarse', 'error');
        }
    });
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
        } catch (e) {
            showToast('Error al enviar solicitud', 'error');
        }
    });
}
