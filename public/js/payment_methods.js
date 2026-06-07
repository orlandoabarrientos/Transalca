let paymentMethodsCache = [];

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="payment_methods"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    Validator.setRules('paymentMethodForm', {
        nombre: { required: true, minLength: 3, maxLength: 50, requiredMsg: 'El nombre es obligatorio', minLengthMsg: 'El nombre debe tener al menos 3 caracteres', maxLengthMsg: 'El nombre no puede superar los 50 caracteres.' },
        datos_pago: { required: true, minLength: 3, maxLength: 80, requiredMsg: 'Los datos son obligatorios', minLengthMsg: 'Los datos deben tener al menos 3 caracteres', maxLengthMsg: 'Los datos no pueden superar los 80 caracteres.' }
    });
    Validator.setupRealtime('paymentMethodForm');
    let checkTimeout = null;
    const nameInput = document.getElementById('nombre');
    if (nameInput) {
        nameInput.addEventListener('input', () => {
            clearTimeout(checkTimeout);
            const val = nameInput.value.trim();
            const exclude = document.getElementById('paymentMethodId').value;
            if (val.length < 3) return;
            checkTimeout = setTimeout(() => {
                fetch(`/api/payment-methods/check-unique?value=${encodeURIComponent(val)}&exclude=${encodeURIComponent(exclude)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'success' && !data.unique) {
                            nameInput.dataset.externalError = 'Este método de pago ya está registrado.';
                            setFieldError(nameInput, 'Este método de pago ya está registrado.');
                        } else {
                            delete nameInput.dataset.externalError;
                            if (nameInput.classList.contains('is-invalid')) clearFieldError(nameInput);
                        }
                        updateFormSubmitState('paymentMethodForm');
                    });
            }, 350);
    }
    loadPaymentMethods();
});
let paginator = null;

function loadPaymentMethods() {
    apiCall('/api/payment-methods/').then(res => {
        paymentMethodsCache = res.data || [];
        if (!paginator) {
            paginator = new TablePaginator('paymentMethodBody', {
                allData: paymentMethodsCache,
                itemName: 'métodos de pago',
                searchSelector: '#paymentMethodSearch',
                renderRow: (item) => `<tr>
                    <td><strong>${escapeHtml(item.nombre)}</strong></td>
                    <td style="white-space: pre-line;">${escapeHtml(item.datos_pago || '')}</td>
                    <td>${item.permite_credito ? '<span class="badge bg-success">Sí</span>' : '<span class="badge bg-secondary">No</span>'}</td>
                    <td><span class="badge bg-info">${(item.moneda || 'usd').toUpperCase()}</span></td>
                    <td>
                        <button class="btn btn-icon btn-sm btn-warning" onclick="editPaymentMethod(${item.id})" title="Modificar método de pago"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-icon btn-sm btn-danger" onclick="deletePaymentMethod(${item.id})" title="Eliminar método de pago"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`,
                onEmpty: () => '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-wallet2"></i><p>No hay métodos de pago registrados</p></div></td></tr>'
            });
        } else {
            paginator.updateData(paymentMethodsCache);
        }
    });
}

function openPaymentMethodModal() {
    Validator.clearForm('paymentMethodForm');
    document.getElementById('paymentMethodId').value = '';
    document.getElementById('permite_credito').checked = false;
    document.getElementById('moneda').value = 'usd';
    document.getElementById('datos_pago').value = '';
    document.getElementById('paymentMethodModalTitle').textContent = 'Registrar Método de Pago';
    document.getElementById('btnSavePaymentMethod').innerHTML = '<i class="bi bi-check-circle me-1"></i>Guardar';
    new bootstrap.Modal(document.getElementById('paymentMethodModal')).show();
    Validator.initTracking('paymentMethodForm');
}

function editPaymentMethod(id) {
    apiCall(`/api/payment-methods/${id}`).then(res => {
        const item = res.data;
        Validator.clearForm('paymentMethodForm');
        document.getElementById('paymentMethodId').value = item.id;
        document.getElementById('nombre').value = item.nombre || '';
        document.getElementById('datos_pago').value = item.datos_pago || '';
        document.getElementById('permite_credito').checked = !!item.permite_credito;
        document.getElementById('moneda').value = item.moneda || 'usd';
        document.getElementById('paymentMethodModalTitle').textContent = 'Modificar Método de Pago';
        document.getElementById('btnSavePaymentMethod').innerHTML = '<i class="bi bi-check-circle me-1"></i>Guardar';
        new bootstrap.Modal(document.getElementById('paymentMethodModal')).show();
        Validator.initTracking('paymentMethodForm');
    });
}

function savePaymentMethod() {
    if (!Validator.validate('paymentMethodForm')) return showToast('Corrija los errores', 'warning');
    const id = document.getElementById('paymentMethodId').value;
    const data = {
        nombre: document.getElementById('nombre').value,
        datos_pago: document.getElementById('datos_pago').value,
        permite_credito: document.getElementById('permite_credito').checked ? 1 : 0,
        moneda: document.getElementById('moneda').value
    };
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/payment-methods/${id}` : '/api/payment-methods/';
    apiCall(url, method, data).then(res => {
        if (res.status === 'error') {
            Validator.showServerErrors('paymentMethodForm', res.errors);
            return showToast(res.message, 'error');
        }
        bootstrap.Modal.getInstance(document.getElementById('paymentMethodModal')).hide();
        showToast(res.message);
        loadPaymentMethods();
    });
}

function deletePaymentMethod(id) {
    confirmAction('¿Estás seguro de que deseas eliminar este método de pago?', () => {
        apiCall(`/api/payment-methods/${id}`, 'DELETE').then(res => {
            showToast(res.message, res.status === 'success' ? 'success' : 'error');
            loadPaymentMethods();
        });
    });
}
