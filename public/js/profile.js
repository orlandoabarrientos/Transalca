$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="profile"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadProfile();
    updatePasswordStrength('new_password', 'passwordStrengthBar');
    Validator.setRules('profileForm', { nombre: { required: true, minLength: 2 }, apellido: { required: true, minLength: 2 } });
    Validator.setRules('passwordForm', {
        old_password: { required: true, requiredMsg: 'Ingrese contrasena actual' },
        new_password: { required: true, pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$/, patternMsg: 'Min 8, 1 may, 1 min, 1 num, 1 esp' },
        confirm_password: { required: true, match: 'new_password', matchMsg: 'No coinciden' }
    });
    Validator.setupRealtime('profileForm');
    Validator.setupRealtime('passwordForm');
});

async function loadProfile() {
    try {
        const res = await apiCall('/api/profile/');
        if (res.data) {
            const u = res.data;
            document.getElementById('nombre').value = u.nombre||'';
            document.getElementById('apellido').value = u.apellido||'';
            document.getElementById('telefono').value = u.telefono||'';
            document.getElementById('direccion').value = u.direccion||'';
            document.getElementById('profileName').textContent = `${u.nombre} ${u.apellido}`;
            document.getElementById('profileEmail').textContent = u.email;
            if (u.foto_perfil) document.getElementById('profilePhoto').src = `/public/assets/profile_pics/${u.foto_perfil}`;
        }
    } catch(e) {}
}

function saveProfile() {
    if (!Validator.validate('profileForm')) return showToast('Corrija errores','warning');
    const data = { nombre: document.getElementById('nombre').value, apellido: document.getElementById('apellido').value, telefono: document.getElementById('telefono').value, direccion: document.getElementById('direccion').value };
    apiCall('/api/profile/', 'PUT', data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('profileForm', res.errors); return showToast(res.message, 'error'); }
        showToast('Perfil actualizado'); loadProfile();
    });
}

function changePassword() {
    if (!Validator.validate('passwordForm')) return showToast('Corrija errores','warning');
    const data = { old_password: document.getElementById('old_password').value, new_password: document.getElementById('new_password').value, confirm_password: document.getElementById('confirm_password').value };
    apiCall('/api/profile/password', 'PUT', data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('passwordForm', res.errors); return showToast(res.message, 'error'); }
        showToast('Contrasena actualizada');
        document.getElementById('old_password').value = '';
        document.getElementById('new_password').value = '';
        document.getElementById('confirm_password').value = '';
    });
}

function uploadPhoto() {
    const input = document.getElementById('photoInput');
    if (!input.files[0]) return;
    const fd = new FormData();
    fd.append('photo', input.files[0]);
    fetch('/api/profile/photo', { method: 'POST', body: fd, credentials: 'same-origin' }).then(r => r.json()).then(res => {
        if (res.status === 'success') { showToast('Foto actualizada'); loadProfile(); }
        else showToast(res.message, 'error');
    });
}
