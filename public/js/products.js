$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="products"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadCombos();
    Validator.setRules('productForm', {
        codigo: { required: true, minLength: 2, requiredMsg: 'Codigo requerido' },
        nombre: { required: true, minLength: 3, requiredMsg: 'Nombre requerido', minLengthMsg: 'Minimo 3 caracteres' },
        precio: { required: true, min: 0.01, requiredMsg: 'Precio requerido', minMsg: 'El precio debe ser mayor a 0' }
    });
    Validator.setupRealtime('productForm');
});

function loadData() {
    apiCall('/api/products/').then(res => {
        const tbody = document.getElementById('productBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(p => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td><strong>${p.nombre}</strong><br><small class="text-muted">${p.codigo}</small></td>
                <td>${p.categoria_nombre || '-'}</td>
                <td>${p.marca_nombre || '-'}</td>
                <td>${p.sucursal_nombre || 'Todas'}</td>
                <td class="fw-bold" style="color:var(--primary);">$${formatCurrency(p.precio)}</td>
                <td>${p.stock !== undefined ? p.stock : '-'}</td>
                <td>${statusBadge(p.estado)}</td>
                <td>
                    <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${escape(p.codigo)}')" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-icon btn-sm ${p.estado ? 'btn-warning' : 'btn-success'}" onclick="toggleEstado('${escape(p.codigo)}')" title="${p.estado ? 'Desactivar' : 'Activar'}"><i class="bi bi-${p.estado ? 'pause' : 'play'}-fill"></i></button>
                </td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="empty-state"><i class="bi bi-box-seam"></i><p>No hay productos registrados</p></div></td></tr>';
        }
    });
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
            catSel.innerHTML = '<option value="">Sin categoria</option>';
            (cats.data||[]).forEach(c => catSel.innerHTML += `<option value="${c.nombre}">${c.nombre}</option>`);
        }
        if (brandSel) {
            brandSel.innerHTML = '<option value="">Sin marca</option>';
            (brands.data||[]).forEach(b => brandSel.innerHTML += `<option value="${b.nombre}">${b.nombre}</option>`);
        }
        await loadSucursales('sucursal_id', true);
    } catch(e) {}
}

function openModal(codigo = null) {
    Validator.clearForm('productForm');
    document.getElementById('productOldCodigo').value = codigo ? unescape(codigo) : '';
    document.getElementById('modalTitle').textContent = codigo ? 'Editar Producto' : 'Nuevo Producto';
    new bootstrap.Modal(document.getElementById('productModal')).show();
}

function editData(codigo) {
    codigo = unescape(codigo);
    apiCall(`/api/products/detail/${encodeURIComponent(codigo)}`).then(res => {
        const p = res.data;
        document.getElementById('productOldCodigo').value = p.codigo;
        document.getElementById('codigo').value = p.codigo;
        document.getElementById('nombre').value = p.nombre;
        document.getElementById('descripcion').value = p.descripcion || '';
        document.getElementById('precio').value = p.precio;
        const catSel = document.getElementById('categoria');
        if (catSel) catSel.value = p.categoria || '';
        const brandSel = document.getElementById('marca');
        if (brandSel) brandSel.value = p.marca || '';
        const sucSel = document.getElementById('sucursal_id');
        if(sucSel) sucSel.value = p.sucursal_id || '';
        document.getElementById('modalTitle').textContent = 'Editar Producto';
        new bootstrap.Modal(document.getElementById('productModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('productForm')) return showToast('Corrija los errores','warning');
    const oldCodigo = document.getElementById('productOldCodigo').value;
    const data = {
        codigo: document.getElementById('codigo').value,
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        precio: parseFloat(document.getElementById('precio').value),
        categoria: document.getElementById('categoria')?.value || null,
        marca: document.getElementById('marca')?.value || null,
        sucursal_id: document.getElementById('sucursal_id')?.value || null
    };
    if (oldCodigo) {
        data.old_codigo = oldCodigo;
        apiCall('/api/products/update', 'PUT', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('productForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
            showToast(res.message); loadData();
        });
    } else {
        apiCall('/api/products/', 'POST', data).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('productForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
            showToast(res.message); loadData();
        });
    }
}

function toggleEstado(codigo) {
    codigo = unescape(codigo);
    confirmAction('¿Cambiar estado del producto?', () => {
        apiCall('/api/products/toggle', 'PUT', { codigo }).then(res => { showToast(res.message); loadData(); });
    });
}
