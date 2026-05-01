const PHONE_REGEX_PROFILE = /^[0-9+\-\s()]{7,20}$/;
const ALLOWED_FUEL_TYPES = ['gasolina', 'gasoil', 'otro'];

const clientProfileState = {
    cedula: '',
    profilePhotoFilename: 'default.png',
    vehicles: [],
    vehicleModal: null,
    editingVehicleId: null,
    pendingCarnetFile: null
};

$(document).ready(function () {
    $('#navbarContainer').load('/components/client_navbar.html', () => checkSession());
    $('#footerContainer').load('/components/client_footer.html');
    bindProfileEvents();
    loadProfile();
    loadVehicles();
});

function bindProfileEvents() {
    $('#btnChangePhoto').on('click', () => $('#photoInput').trigger('click'));
    $('#photoInput').on('change', onProfilePhotoSelected);
    $('#profileForm').on('submit', onSaveProfile);
    $('#passwordForm').on('submit', onChangePassword);
    $('#btnAddVehicle').on('click', () => openVehicleModal());
    $('#btnSaveVehicle').on('click', saveVehicleFromProfile);
    $('#btnVehicleCarnet').on('click', () => $('#vCarnetFile').trigger('click'));
    $('#vCarnetFile').on('change', onCarnetFileSelected);
}

async function loadProfile() {
    try {
        const res = await fetch('/api/profile/', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.status !== 'success' || !data.data) {
            showToast(data.message || 'No se pudo cargar el perfil', 'error');
            return;
        }
        const p = data.data;
        clientProfileState.cedula = p.cedula || '';
        $('#fNombre').val(p.nombre || '');
        $('#fApellido').val(p.apellido || '');
        $('#fTelefono').val(p.telefono || '');
        $('#fDireccion').val(p.direccion || '');
        $('#profileName').text(`${p.nombre || ''} ${p.apellido || ''}`.trim());
        $('#profileEmail').text(p.email || '');
        setProfilePhoto(p.foto_perfil || 'default.png');
    } catch (e) {
        showToast('Error al cargar el perfil', 'error');
    }
}

function setProfilePhoto(filename) {
    const safeName = filename || 'default.png';
    clientProfileState.profilePhotoFilename = safeName;
    const src = `/public/assets/profile_pics/${safeName}`;
    $('#profilePhoto').attr('src', src);
    $('#clientNavPhoto').attr('src', src);
    $('#navUserPhoto').attr('src', src);
}

async function onSaveProfile(event) {
    event.preventDefault();
    const telefono = ($('#fTelefono').val() || '').trim();
    if (!PHONE_REGEX_PROFILE.test(telefono)) {
        showToast('Telefono invalido', 'error');
        return;
    }
    const payload = {
        nombre: ($('#fNombre').val() || '').trim(),
        apellido: ($('#fApellido').val() || '').trim(),
        telefono,
        direccion: ($('#fDireccion').val() || '').trim()
    };
    try {
        const res = await fetch('/api/profile/', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudo actualizar el perfil', 'error');
            return;
        }
        $('#profileName').text(`${payload.nombre} ${payload.apellido}`.trim());
        showToast(data.message || 'Perfil actualizado', 'success');
    } catch (e) {
        showToast('Error al actualizar el perfil', 'error');
    }
}

async function onChangePassword(event) {
    event.preventDefault();
    const oldPassword = ($('#fOldPass').val() || '').trim();
    const newPassword = ($('#fNewPass').val() || '').trim();
    const confirmPassword = ($('#fConfirmPass').val() || '').trim();
    if (!oldPassword || !newPassword || !confirmPassword) {
        showToast('Complete los campos de contrasena', 'error');
        return;
    }
    if (newPassword !== confirmPassword) {
        showToast('Las contrasenas no coinciden', 'error');
        return;
    }
    const payload = {
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
    };
    try {
        const res = await fetch('/api/profile/password', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudo cambiar la contrasena', 'error');
            return;
        }
        $('#passwordForm')[0].reset();
        showToast(data.message || 'Contrasena actualizada', 'success');
    } catch (e) {
        showToast('Error al cambiar la contrasena', 'error');
    }
}

function onProfilePhotoSelected() {
    const file = this.files && this.files[0] ? this.files[0] : null;
    if (!file) {
        return;
    }
    const previousFile = clientProfileState.profilePhotoFilename;
    const reader = new FileReader();
    reader.onload = ev => $('#profilePhoto').attr('src', ev.target.result);
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append('photo', file);

    fetch('/api/profile/photo', {
        method: 'POST',
        credentials: 'same-origin',
        body: formData
    }).then(async res => {
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            throw new Error(data.message || 'Error al subir foto');
        }
        const filename = data.filename || previousFile || 'default.png';
        setProfilePhoto(filename);
        const cacheBust = `?t=${Date.now()}`;
        const src = `/public/assets/profile_pics/${filename}${cacheBust}`;
        $('#profilePhoto').attr('src', src);
        $('#clientNavPhoto').attr('src', src);
        $('#navUserPhoto').attr('src', src);
        showToast(data.message || 'Foto actualizada', 'success');
    }).catch(err => {
        setProfilePhoto(previousFile || 'default.png');
        showToast(err.message || 'No se pudo subir la foto', 'error');
    }).finally(() => {
        $('#photoInput').val('');
    });
}

async function loadVehicles() {
    try {
        const res = await fetch('/api/vehicles/', { credentials: 'same-origin' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudieron cargar los vehiculos', 'error');
            return;
        }
        clientProfileState.vehicles = Array.isArray(data.data) ? data.data : [];
        renderVehiclesTable();
    } catch (e) {
        showToast('Error al cargar vehiculos', 'error');
    }
}

function renderVehiclesTable() {
    const tbody = $('#vehiclesProfileBody');
    tbody.empty();
    if (clientProfileState.vehicles.length === 0) {
        tbody.html('<tr><td colspan="7" class="text-center text-muted py-3">Sin vehiculos registrados</td></tr>');
        return;
    }
    clientProfileState.vehicles.forEach(v => {
        const carnetCell = v.imagen_carnet
            ? `<a href="/public/assets/images/${v.imagen_carnet}" target="_blank" rel="noopener">Ver</a>`
            : '<span class="text-muted">No</span>';
        tbody.append(`
            <tr>
                <td><strong>${escapeHtml(v.placa || '-')}</strong></td>
                <td>${escapeHtml(v.marca || '-')}</td>
                <td>${escapeHtml(v.modelo || '-')}</td>
                <td>${escapeHtml(v.anio || '-')}</td>
                <td>${Number(v.kilometraje_actual || 0).toLocaleString()}</td>
                <td>${carnetCell}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editVehicleFromProfile(${v.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteVehicleFromProfile(${v.id})" title="Eliminar"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `);
    });
}

function openVehicleModal(vehicle = null) {
    clientProfileState.editingVehicleId = vehicle ? vehicle.id : null;
    clientProfileState.pendingCarnetFile = null;
    $('#vehicleForm')[0].reset();
    $('#vCarnetFile').val('');
    $('#vCarnetFileName').text('No seleccionado');
    $('#vCarnetPreview').hide().attr('src', '');
    $('#vCombustibleError').addClass('d-none');
    $('#vCombustible').removeClass('is-invalid');

    if (vehicle) {
        $('#vehicleModalTitle').text('Editar Vehiculo');
        $('#editVehicleId').val(vehicle.id);
        $('#vMarca').val(vehicle.marca || '');
        $('#vModelo').val(vehicle.modelo || '');
        $('#vAnio').val(vehicle.anio || '');
        $('#vPlaca').val(vehicle.placa || '');
        $('#vColor').val(vehicle.color || '');
        $('#vTipo').val(vehicle.tipo_vehiculo || '');
        $('#vCombustible').val(vehicle.tipo_combustible || 'gasolina');
        $('#vKm').val(vehicle.kilometraje_actual || 0);
    } else {
        $('#vehicleModalTitle').text('Agregar Vehiculo');
        $('#editVehicleId').val('');
        $('#vCombustible').val('gasolina');
        $('#vKm').val(0);
    }

    if (!clientProfileState.vehicleModal) {
        clientProfileState.vehicleModal = new bootstrap.Modal('#vehicleModal');
    }
    clientProfileState.vehicleModal.show();
}

function editVehicleFromProfile(vehicleId) {
    const vehicle = clientProfileState.vehicles.find(v => Number(v.id) === Number(vehicleId));
    if (!vehicle) {
        return;
    }
    openVehicleModal(vehicle);
}

async function deleteVehicleFromProfile(vehicleId) {
    if (!confirm('Desea eliminar este vehiculo?')) {
        return;
    }
    try {
        const res = await fetch(`/api/vehicles/${vehicleId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudo eliminar el vehiculo', 'error');
            return;
        }
        showToast(data.message || 'Vehiculo eliminado', 'success');
        await loadVehicles();
    } catch (e) {
        showToast('Error al eliminar vehiculo', 'error');
    }
}

function onCarnetFileSelected() {
    const file = this.files && this.files[0] ? this.files[0] : null;
    clientProfileState.pendingCarnetFile = file || null;
    if (!file) {
        $('#vCarnetFileName').text('No seleccionado');
        $('#vCarnetPreview').hide().attr('src', '');
        return;
    }
    $('#vCarnetFileName').text(file.name);
    const reader = new FileReader();
    reader.onload = ev => {
        $('#vCarnetPreview').attr('src', ev.target.result).show();
    };
    reader.readAsDataURL(file);
    scanVehicleTitleAndFill(file);
}

function getVehicleFormPayload() {
    const payload = {
        cliente_cedula: clientProfileState.cedula,
        marca: ($('#vMarca').val() || '').trim(),
        modelo: ($('#vModelo').val() || '').trim(),
        anio: parseInt($('#vAnio').val(), 10) || null,
        placa: ($('#vPlaca').val() || '').trim(),
        color: ($('#vColor').val() || '').trim(),
        tipo_vehiculo: ($('#vTipo').val() || '').trim(),
        tipo_combustible: ($('#vCombustible').val() || '').trim(),
        kilometraje_actual: parseInt($('#vKm').val(), 10) || 0
    };
    return payload;
}

function validateVehiclePayload(payload) {
    if (!payload.marca || !payload.modelo) {
        showToast('Marca y modelo son requeridos', 'error');
        return false;
    }
    if (!ALLOWED_FUEL_TYPES.includes(payload.tipo_combustible)) {
        $('#vCombustible').addClass('is-invalid');
        $('#vCombustibleError').removeClass('d-none');
        showToast('Combustible alterado: valor no permitido', 'error');
        return false;
    }
    $('#vCombustible').removeClass('is-invalid');
    $('#vCombustibleError').addClass('d-none');
    return true;
}

async function saveVehicleFromProfile() {
    if (!clientProfileState.cedula) {
        showToast('No se pudo identificar el cliente', 'error');
        return;
    }
    const payload = getVehicleFormPayload();
    if (!validateVehiclePayload(payload)) {
        return;
    }

    const vehicleId = clientProfileState.editingVehicleId;
    const url = vehicleId ? `/api/vehicles/${vehicleId}` : '/api/vehicles/';
    const method = vehicleId ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudo guardar el vehiculo', 'error');
            return;
        }

        const savedVehicleId = vehicleId || data.id;
        let carnetMessage = '';
        if (clientProfileState.pendingCarnetFile && savedVehicleId) {
            const carnetResult = await uploadVehicleCarnet(savedVehicleId, clientProfileState.pendingCarnetFile);
            if (!carnetResult.ok) {
                carnetMessage = ` (${carnetResult.message})`;
            }
        }

        showToast((data.message || 'Vehiculo guardado') + carnetMessage, 'success');
        clientProfileState.vehicleModal.hide();
        await loadVehicles();
    } catch (e) {
        showToast('Error al guardar vehiculo', 'error');
    }
}

async function uploadVehicleCarnet(vehicleId, file) {
    const formData = new FormData();
    formData.append('imagen', file);
    try {
        const res = await fetch(`/api/vehicles/${vehicleId}/carnet`, {
            method: 'POST',
            credentials: 'same-origin',
            body: formData
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            return { ok: false, message: data.message || 'No se pudo subir el titulo' };
        }
        return { ok: true };
    } catch (e) {
        return { ok: false, message: 'No se pudo subir el titulo' };
    }
}

async function scanVehicleTitleAndFill(file) {
    const formData = new FormData();
    formData.append('imagen', file);
    try {
        const res = await fetch('/api/vehicles/scan-title', {
            method: 'POST',
            credentials: 'same-origin',
            body: formData
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success' || !data.data) {
            showToast(data.message || 'No se pudo leer el documento automaticamente', 'warning');
            return;
        }
        applyScannedVehicleData(data.data);
        showToast('Datos del documento cargados automaticamente', 'success');
    } catch (e) {
        showToast('No se pudo procesar el documento automaticamente', 'warning');
    }
}

function applyScannedVehicleData(parsed) {
    if (parsed.marca) $('#vMarca').val(parsed.marca);
    if (parsed.modelo) $('#vModelo').val(parsed.modelo);
    if (parsed.anio) $('#vAnio').val(parsed.anio);
    if (parsed.placa) $('#vPlaca').val(parsed.placa);
    if (parsed.color) $('#vColor').val(parsed.color);
    if (parsed.tipo_vehiculo) $('#vTipo').val(parsed.tipo_vehiculo);
    if (parsed.tipo_combustible && ALLOWED_FUEL_TYPES.includes(parsed.tipo_combustible)) {
        $('#vCombustible').val(parsed.tipo_combustible);
    }
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
