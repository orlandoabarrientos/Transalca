let productCodigoTimer = null;

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="products"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadCombos();
    loadSucursales('sucursal_id', false).then(() => enhanceSearchableSelects(document.getElementById('productModal')));
    Validator.setRules('productForm', {
        codigo: { required: true, minLength: 2, maxLength: 20, requiredMsg: 'El código es obligatorio', maxLengthMsg: 'El código no puede superar los 20 caracteres.' },
        nombre: { 
            required: true, 
            minLength: 3, 
            maxLength: 50, 
            pattern: /^[A-Za-z0-9ñÑáéíóúÁÉÍÓÚ\s\-\.\#\:\,\_\/]+$/, 
            requiredMsg: 'El nombre es obligatorio', 
            minLengthMsg: 'Mínimo 3 caracteres',
            maxLengthMsg: 'El nombre no puede superar los 50 caracteres.',
            patternMsg: 'El nombre contiene caracteres no válidos' 
        },
        descripcion: {
            maxLength: 150,
            maxLengthMsg: 'La descripción no puede superar los 150 caracteres.'
        },
        precio: { required: true, min: 0.01, requiredMsg: 'El precio es obligatorio', minMsg: 'El precio debe ser mayor a 0' },
        categoria: { required: true, requiredMsg: 'Debe seleccionar una categoría' },
        marca: { required: true, requiredMsg: 'Debe seleccionar una marca' },
        sucursal_id: { required: true, requiredMsg: 'Seleccione al menos una sucursal' }
    });
    Validator.setupRealtime('productForm');
    document.getElementById('codigo')?.addEventListener('input', validateUniqueProductCodigo);
});

let currentProductPage = 1;
const productsPerPage = 30;

function loadData(page = 1) {
    currentProductPage = page;
    apiCall(`/api/products/?page=${page}&per_page=${productsPerPage}`).then(res => {
        const tbody = document.getElementById('productBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><strong>${escapeHtml(p.nombre)}</strong><br><small class="text-muted">${escapeHtml(p.codigo)}</small></td>
                <td>${escapeHtml(p.categoria_nombre || '-')}</td>
                <td>${escapeHtml(p.marca_nombre || '-')}</td>
                <td>${escapeHtml(p.sucursal_nombre || 'Todas')}</td>
                <td class="fw-bold" style="color:var(--primary);" data-usd-price="${p.precio}">${formatUsdBs(p.precio)}</td>
                <td>${p.stock !== undefined ? p.stock : '-'}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${encodeURIComponent(p.codigo)}')" title="Modificar Producto"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado('${encodeURIComponent(p.codigo)}')" title="Eliminar Producto"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-box"></i><p>No hay productos registrados</p></div></td></tr>';
        }
        renderPagination(res.total || 0, res.page || 1, res.pages || 1);
    });
}

function renderPagination(total, page, pages) {
    const info = document.getElementById('paginationInfo');
    const controls = document.getElementById('paginationControls');
    if (info) {
        const start = total ? (page - 1) * productsPerPage + 1 : 0;
        const end = Math.min(page * productsPerPage, total);
        info.textContent = `Mostrando ${start} a ${end} de ${total} productos`;
    }
    if (!controls) return;
    controls.innerHTML = '';
    if (pages <= 1) return;
    
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page > 1}) loadData(${page - 1})"><i class="bi bi-chevron-left"></i></a>`;
    controls.appendChild(prevLi);
    
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
        firstLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); loadData(1)">1</a>`;
        controls.appendChild(firstLi);
        
        if (startPage > 2) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
            controls.appendChild(ellipsisLi);
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${page === i ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); loadData(${i})">${i}</a>`;
        controls.appendChild(li);
    }
    
    if (endPage < pages) {
        if (endPage < pages - 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
            controls.appendChild(ellipsisLi);
        }
        const lastLi = document.createElement('li');
        lastLi.className = 'page-item';
        lastLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); loadData(${pages})">${pages}</a>`;
        controls.appendChild(lastLi);
    }
    
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${page === pages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page < pages}) loadData(${page + 1})"><i class="bi bi-chevron-right"></i></a>`;
    controls.appendChild(nextLi);
}

async function loadCombos() {
    try {
        const [cats, brands] = await Promise.all([
            apiCall('/api/categories/active'),
            apiCall('/api/brands/active')
        ]);
        const catSel = document.getElementById('categoria');
        const brandSel = document.getElementById('marca');
        if (catSel) {
            catSel.innerHTML = '<option value="">Seleccione categoría...</option>';
            (cats.data || []).forEach(c => catSel.innerHTML += `<option value="${escapeHtml(c.nombre)}">${escapeHtml(c.nombre)}</option>`);
        }
        if (brandSel) {
            brandSel.innerHTML = '<option value="">Seleccione marca...</option>';
            (brands.data || []).forEach(b => brandSel.innerHTML += `<option value="${escapeHtml(b.nombre)}">${escapeHtml(b.nombre)}</option>`);
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
        const sucSel = document.getElementById('sucursal_id');
        if (sucSel) {
            const ids = String(p.sucursal_ids || '').split(',').filter(Boolean);
            Array.from(sucSel.options).forEach(opt => { opt.selected = ids.includes(opt.value); });
            if (window.jQuery?.fn?.select2) window.jQuery(sucSel).trigger('change.select2');
        }
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
        sucursal_ids: Array.from(document.getElementById('sucursal_id')?.selectedOptions || []).map(o => o.value)
    };
    const saveBtn = document.querySelector('#productModal .btn-success');
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
        loadData(currentProductPage);
    });
}

function toggleEstado(codigo) {
    codigo = decodeURIComponent(codigo);
    confirmAction('¿Estás seguro de que deseas eliminar este producto?', () => {
        apiCall('/api/products/toggle', 'PUT', { codigo }).then(res => {
            if (res.status === 'error') return showToast(res.message, 'error');
            showToast(res.message);
            loadData(currentProductPage);
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
