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
    document.getElementById('product_imagen')?.addEventListener('change', onProductImageSelected);
    $('#productsPerPageSelect').on('change', function() {
        productsPerPage = parseInt($(this).val()) || 30;
        loadData(1);
    });
});

let currentProductPage = 1;
let productsPerPage = 30;

function loadData(page = 1) {
    currentProductPage = page;
    apiCall(`/api/products/?page=${page}&per_page=${productsPerPage}`).then(res => {
        const tbody = document.getElementById('productBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            const imgPath = p.imagen && p.imagen !== 'default_product.png' ? `/public/assets/product_imgs/${p.imagen}` : '/public/assets/images/no-image.png';
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>
                    <div class="d-flex align-items-center gap-3">
                        <img src="${imgPath}" onerror="this.src='/public/assets/images/no-image.png'" style="width: 40px; height: 40px; border-radius: 6px; object-fit: cover;" class="border shadow-sm">
                        <div>
                            <strong>${escapeHtml(p.nombre)}</strong><br>
                            <small class="text-muted">${escapeHtml(p.codigo)}</small>
                        </div>
                    </div>
                </td>
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
    const fileInput = document.getElementById('product_imagen');
    if (fileInput) fileInput.value = '';
    setProductPreview('');
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
        if (catSel) {
            catSel.value = p.categoria || '';
            if (window.jQuery?.fn?.select2) window.jQuery(catSel).trigger('change.select2');
        }
        const brandSel = document.getElementById('marca');
        if (brandSel) {
            brandSel.value = p.marca || '';
            if (window.jQuery?.fn?.select2) window.jQuery(brandSel).trigger('change.select2');
        }
        const sucSel = document.getElementById('sucursal_id');
        if (sucSel) {
            const ids = String(p.sucursal_ids || '').split(',').filter(Boolean);
            Array.from(sucSel.options).forEach(opt => { opt.selected = ids.includes(opt.value); });
            if (window.jQuery?.fn?.select2) window.jQuery(sucSel).trigger('change.select2');
        }
        const fileInput = document.getElementById('product_imagen');
        if (fileInput) fileInput.value = '';
        const imgPath = p.imagen && p.imagen !== 'default_product.png' ? `/public/assets/product_imgs/${p.imagen}` : '/public/assets/images/no-image.png';
        setProductPreview(imgPath);
        
        document.getElementById('modalTitle').textContent = 'Modificar Producto';
        new bootstrap.Modal(document.getElementById('productModal')).show();
        Validator.initTracking('productForm');
    });
}

function saveData() {
    if (!Validator.validate('productForm')) return showToast('Corrija los errores', 'warning');
    const oldCodigo = document.getElementById('productOldCodigo').value;
    const formData = new FormData();
    formData.append('codigo', document.getElementById('codigo').value);
    formData.append('nombre', document.getElementById('nombre').value);
    formData.append('descripcion', document.getElementById('descripcion').value);
    formData.append('precio', document.getElementById('precio').value);
    formData.append('categoria', document.getElementById('categoria')?.value || '');
    formData.append('marca', document.getElementById('marca')?.value || '');
    
    const selectedSucs = Array.from(document.getElementById('sucursal_id')?.selectedOptions || []).map(o => o.value);
    selectedSucs.forEach(id => formData.append('sucursal_ids', id));

    const fileInput = document.getElementById('product_imagen');
    if (fileInput && fileInput.files.length > 0) {
        formData.append('imagen', fileInput.files[0]);
    }
    if (oldCodigo) {
        formData.append('old_codigo', oldCodigo);
    }
    
    const saveBtn = document.querySelector('#productModal .btn-success');
    const url = oldCodigo ? '/api/products/update' : '/api/products/';
    const method = oldCodigo ? 'PUT' : 'POST';
    setButtonLoading(saveBtn, true, 'Guardando...');
    apiCall(url, method, formData).then(res => {
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

function onProductImageSelected(e) {
    const file = e?.target?.files?.[0];
    if (!file) {
        setProductPreview('');
        return;
    }
    if (!['image/png', 'image/jpeg', 'image/webp', 'image/jpg'].includes(file.type)) {
        e.target.value = '';
        setProductPreview('');
        return showToast('El archivo debe ser una imagen png, jpg, jpeg o webp', 'warning');
    }
    const reader = new FileReader();
    reader.onload = function (evt) {
        setProductPreview(evt?.target?.result || '');
    };
    reader.readAsDataURL(file);
}

function setProductPreview(src) {
    const img = document.getElementById('productImagePreview');
    if (!img) return;
    if (!src) {
        img.style.display = 'none';
        img.src = '';
        return;
    }
    img.src = src;
    img.style.display = '';
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
