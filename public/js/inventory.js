$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="inventory"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadSucursales('filterSucursal', true);
    loadSucursales('sucursal_id', false);
    loadCombos();
    loadStock();
    loadOrders();
    Validator.setRules('inventoryForm', {
        proveedor_rif: { required: true, requiredMsg: 'Seleccione un proveedor' },
        sucursal_id: { required: true, requiredMsg: 'Seleccione una sucursal' },
        producto_codigo: { required: true, requiredMsg: 'Seleccione un producto' },
        cantidad: { required: true, min: 1, requiredMsg: 'Cantidad requerida', minMsg: 'Minimo 1' }
    });
    Validator.setupRealtime('inventoryForm');
});

async function loadCombos() {
    try {
        const [suppliers, products] = await Promise.all([
            apiCall('/api/suppliers/active'),
            apiCall('/api/products/active')
        ]);
        const supSel = document.getElementById('proveedor_rif');
        if (supSel) {
            supSel.innerHTML = '<option value="">Seleccione proveedor</option>';
            (suppliers.data||[]).forEach(s => supSel.innerHTML += `<option value="${s.rif}">${s.nombre} (${s.rif || ''})</option>`);
        }
        const prodSel = document.getElementById('producto_codigo');
        if (prodSel) {
            prodSel.innerHTML = '<option value="">Seleccione producto</option>';
            (products.data||[]).forEach(p => prodSel.innerHTML += `<option value="${p.codigo}">${p.nombre} (${p.codigo})</option>`);
        }
    } catch(e) {}
}

function loadStock() {
    const sucursal = document.getElementById('filterSucursal')?.value || '';
    const url = sucursal ? `/api/inventory/?sucursal_id=${sucursal}` : '/api/inventory/';
    apiCall(url).then(res => {
        const tbody = document.getElementById('stockBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(s => {
            const isLow = s.stock <= (s.stock_minimo || 5);
            tbody.innerHTML += `<tr class="fade-in-up ${isLow ? 'table-warning' : ''}">
                <td><strong>${s.producto_nombre || ''}</strong></td>
                <td>${s.codigo || ''}</td>
                <td>${s.sucursal_nombre || 'N/A'}</td>
                <td class="fw-bold">${s.stock || 0}</td>
                <td>${s.stock_minimo || 5}</td>
                <td>${isLow ? '<span class="badge-status badge-pending"><i class="bi bi-exclamation-triangle me-1"></i>Bajo</span>' : '<span class="badge-status badge-active">OK</span>'}</td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-archive"></i><p>Sin datos de stock</p></div></td></tr>';
        }
    });
}

function loadOrders() {
    apiCall('/api/inventory/purchase-orders').then(res => {
        const tbody = document.getElementById('orderBody');
        if(!tbody) return;
        tbody.innerHTML = '';
        (res.data || []).forEach(o => {
            tbody.innerHTML += `<tr class="fade-in-up">
                <td>#${o.id}</td>
                <td>${o.proveedor_nombre || 'N/A'}</td>
                <td>${o.sucursal_nombre || 'N/A'}</td>
                <td>${o.usuario_nombre || 'N/A'}</td>
                <td>$${formatCurrency(o.total || 0)}</td>
                <td>${formatDate(o.fecha)}</td>
                <td>${statusBadge(o.estado)}</td>
            </tr>`;
        });
        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-archive"></i><p>Sin ordenes de compra</p></div></td></tr>';
        }
    });
}

function filterTable() {
    const q = document.getElementById('searchStock')?.value.toLowerCase() || '';
    document.querySelectorAll('#stockBody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

function openModal() {
    Validator.clearForm('inventoryForm');
    new bootstrap.Modal(document.getElementById('inventoryModal')).show();
}

function saveOrder() {
    if (!Validator.validate('inventoryForm')) return showToast('Corrija los errores','warning');
    const data = {
        proveedor_rif: document.getElementById('proveedor_rif').value,
        sucursal_id: document.getElementById('sucursal_id').value,
        detalles: [{
            producto_codigo: document.getElementById('producto_codigo').value,
            cantidad: parseInt(document.getElementById('cantidad').value),
            precio_unitario: parseFloat(document.getElementById('precio_unitario').value) || 0
        }],
        observaciones: document.getElementById('observaciones').value,
        total: parseInt(document.getElementById('cantidad').value) * (parseFloat(document.getElementById('precio_unitario').value) || 0)
    };
    apiCall('/api/inventory/purchase-orders', 'POST', data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('inventoryForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('inventoryModal')).hide();
        showToast(res.message);
        loadStock();
        loadOrders();
    });
}
