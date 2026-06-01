let productCodigoTimer = null;

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="products"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadCombos();
    Validator.setRules('productForm', {
        codigo: { required: true, minLength: 2, requiredMsg: 'El código es obligatorio' },
        nombre: { 
            required: true, 
            minLength: 3, 
            maxLength: 50, 
            pattern: /^[A-Za-z0-9ñÑáéíóúÁÉÍÓÚ\s\-\.\#\:\,\_\/]+$/, 
            requiredMsg: 'El nombre es obligatorio', 
            minLengthMsg: 'Mínimo 3 caracteres',
            maxLengthMsg: 'Máximo 50 caracteres',
            patternMsg: 'El nombre contiene caracteres no válidos' 
        },
        descripcion: {
            maxLength: 250,
            maxLengthMsg: 'La descripción no puede superar los 250 caracteres'
        },
        precio: { required: true, min: 0.01, requiredMsg: 'El precio es obligatorio', minMsg: 'El precio debe ser mayor a 0' },
        categoria: { required: true, requiredMsg: 'Debe seleccionar una categoría' },
        marca: { required: true, requiredMsg: 'Debe seleccionar una marca' },
        proveedor_rif: { required: true, requiredMsg: 'Debe seleccionar un proveedor' }
    });
    Validator.setupRealtime('productForm');
    document.getElementById('codigo')?.addEventListener('input', validateUniqueProductCodigo);
});

function loadData() {
    apiCall('/api/products/').then(res => {
        const tbody = document.getElementById('productBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><strong>${escapeHtml(p.nombre)}</strong><br><small class="text-muted">${escapeHtml(p.codigo)}</small></td>
                <td>${escapeHtml(p.categoria_nombre || '-')}</td>
                <td>${escapeHtml(p.marca_nombre || '-')}</td>
                <td>${escapeHtml(p.proveedor_nombre || '-')}</td>
                <td>${escapeHtml(p.sucursal_nombre || 'Todas')}</td>
                <td class="fw-bold" style="color:var(--primary);" data-usd-price="${p.precio}">${formatUsdBs(p.precio)}</td>
                <td>${p.stock !== undefined ? p.stock : '-'}</td>
                <td>${statusBadge(p.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${encodeURIComponent(p.codigo)}')" title="Modificar Producto"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado('${encodeURIComponent(p.codigo)}')" title="Eliminar Producto"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4"><div class="empty-state"><i class="bi bi-box"></i><p>No hay productos registrados</p></div></td></tr>';
        }
    });
}

async function loadCombos() {
    try {
        const [cats, brands, suppliers] = await Promise.all([
            apiCall('/api/categories/active'),
            apiCall('/api/brands/active'),
            apiCall('/api/suppliers/active')
        ]);
        const catSel = document.getElementById('categoria');
        const brandSel = document.getElementById('marca');
        const supplierSel = document.getElementById('proveedor_rif');
        if (catSel) {
            catSel.innerHTML = '<option value="">Seleccione categoría...</option>';
            (cats.data || []).forEach(c => catSel.innerHTML += `<option value="${escapeHtml(c.nombre)}">${escapeHtml(c.nombre)}</option>`);
        }
        if (brandSel) {
            brandSel.innerHTML = '<option value="">Seleccione marca...</option>';
            (brands.data || []).forEach(b => brandSel.innerHTML += `<option value="${escapeHtml(b.nombre)}">${escapeHtml(b.nombre)}</option>`);
        }
        if (supplierSel) {
            supplierSel.innerHTML = '<option value="">Seleccione proveedor...</option>';
            (suppliers.data || []).forEach(s => supplierSel.innerHTML += `<option value="${escapeHtml(s.rif)}">${escapeHtml(s.nombre)} (${escapeHtml(s.rif)})</option>`);
        }
    } catch(e) {}
}

function openModal(codigo = null) {
    Validator.clearForm('productForm');
    document.getElementById('productOldCodigo').value = codigo ? decodeURIComponent(codigo) : '';
    document.getElementById('modalTitle').textContent = codigo ? 'Modificar Producto' : 'Registrar Producto';
    new bootstrap.Modal(document.getElementById('productModal')).show();
    Validator.initTracking('productForm');
}

function editData(codigo) {
    codigo = decodeURIComponent(codigo);
    apiCall(`/api/products/detail/${encodeURIComponent(codigo)}`).then(res => {
        if (res.status === 'error') return showToast(res.message, 'error');
        const p = res.data || {};
        Validator.clearForm('productForm');
        document.getElementById('productOldCodigo').value = p.codigo;
        document.getElementById('codigo').value = p.codigo || '';
        document.getElementById('nombre').value = p.nombre || '';
        document.getElementById('descripcion').value = p.descripcion || '';
        document.getElementById('precio').value = p.precio || '';
        const catSel = document.getElementById('categoria');
        if (catSel) catSel.value = p.categoria || '';
        const brandSel = document.getElementById('marca');
        if (brandSel) brandSel.value = p.marca || '';
        const supplierSel = document.getElementById('proveedor_rif');
        if (supplierSel) supplierSel.value = p.proveedor_rif || '';
        document.getElementById('modalTitle').textContent = 'Modificar Producto';
        new bootstrap.Modal(document.getElementById('productModal')).show();
        Validator.initTracking('productForm');
    });
}

function saveData() {
    if (!Validator.validate('productForm')) return showToast('Corrija los errores', 'warning');
    const oldCodigo = document.getElementById('productOldCodigo').value;
    const data = {
        codigo: document.getElementById('codigo').value,
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        precio: document.getElementById('precio').value,
        categoria: document.getElementById('categoria')?.value || null,
        marca: document.getElementById('marca')?.value || null,
        proveedor_rif: document.getElementById('proveedor_rif')?.value || null
    };
    const saveBtn = document.querySelector('#productModal .btn-orange');
    const url = oldCodigo ? '/api/products/update' : '/api/products/';
    const method = oldCodigo ? 'PUT' : 'POST';
    if (oldCodigo) data.old_codigo = oldCodigo;
    setButtonLoading(saveBtn, true, 'Guardando...');
    apiCall(url, method, data).then(res => {
        setButtonLoading(saveBtn, false);
        if (res.status === 'error') {
            Validator.showServerErrors('productForm', res.errors);
            return showToast(res.message, 'error');
        }
        bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
        showToast(res.message);
        loadData();
    });
}

function toggleEstado(codigo) {
    codigo = decodeURIComponent(codigo);
    confirmAction('¿Estás seguro de que deseas eliminar este producto?', () => {
        apiCall('/api/products/toggle', 'PUT', { codigo }).then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadData();
        });
    });
}

function validateUniqueProductCodigo() {
    clearTimeout(productCodigoTimer);
    productCodigoTimer = setTimeout(async () => {
        const input = document.getElementById('codigo');
        const oldCodigo = document.getElementById('productOldCodigo')?.value || '';
        const value = (input?.value || '').trim();
        if (!input) return;
        if (!value) {
            delete input.dataset.externalError;
            clearFieldError(input);
            updateFormSubmitState('productForm');
            return;
        }
        if (!Validator.validateField('productForm', 'codigo')) {
            delete input.dataset.externalError;
            updateFormSubmitState('productForm');
            return;
        }
        const res = await apiCall(`/api/products/check-unique?value=${encodeURIComponent(value)}&exclude=${encodeURIComponent(oldCodigo)}`);
        if (res.status === 'success' && res.exists) {
            input.dataset.externalError = 'Este código ya está registrado';
            setFieldError(input, 'Este código ya está registrado');
        } else if (res.status === 'success') {
            delete input.dataset.externalError;
            clearFieldError(input);
        }
        updateFormSubmitState('productForm');
    }, 350);
}
