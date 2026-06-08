let activeProducts = [];

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="purchase_orders"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    $('#filterEstado').on('change', loadOrders);

    Validator.setRules('createOrderForm', {
        proveedor_rif: { required: true, requiredMsg: 'Debe seleccionar un proveedor' },
        sucursal_id: { required: true, requiredMsg: 'Debe seleccionar una sucursal' },
        poObservaciones: { maxLength: 300, maxLengthMsg: 'Las observaciones no pueden superar los 300 caracteres.' }
    });
    Validator.setupRealtime('createOrderForm');


    loadStats();
    loadOrders();
    preloadProducts();
});

function debounce(fn, ms) {
    let t; return function (...a) { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), ms); };
}

function loadStats() {
    $.get('/api/purchase-orders/stats', function (r) {
        if (r.status !== 'success') return;
        $('#totalOrders').text(r.data.total || 0);
        $('#pendingOrders').text(r.data.pendientes || 0);
        $('#boughtOrders').text(r.data.comprados || 0);
        $('#totalInverted').attr('data-usd-price', r.data.total_invertido || 0).text(formatUsdBs(r.data.total_invertido || 0));
    });
}

let paginator = null;

function loadOrders() {
    const estado = $('#filterEstado').val();
    let url = '/api/purchase-orders/?';
    if (estado) url += `estado=${encodeURIComponent(estado)}&`;

    $.get(url, function (r) {
        if (!paginator) {
            paginator = new TablePaginator('ordersTableBody', {
                allData: r.data || [],
                itemName: 'órdenes de compra',
                searchSelector: '#searchInput',
                renderRow: (o) => {
                    const dateStr = formatDate(o.fecha);
                    const total = Number(o.total || 0);
                    const isBought = String(o.estado || '').toLowerCase() === 'comprado';
                    const statusBadge = isBought
                        ? '<span class="badge-status badge-active">Comprado</span>'
                        : '<span class="badge-status badge-pending">Pendiente</span>';

                    return `
                        <tr>
                            <td>#${o.id}</td>
                            <td>${escapeHtml(o.proveedor_nombre || '')}</td>
                            <td>${escapeHtml(o.proveedor_rif || '')}</td>
                            <td>${escapeHtml(o.sucursal_nombre || '')}</td>
                            <td data-usd-price="${total}">${formatUsdBs(total)}</td>
                            <td>${dateStr}</td>
                            <td>${statusBadge}</td>
                            <td>
                                <div class="d-flex gap-1 justify-content-start align-items-center">
                                    <button class="btn btn-sm btn-outline-orange" title="Ver detalle" onclick="viewOrderDetails(${o.id})"><i class="bi bi-eye"></i></button>
                                    <button class="btn btn-sm btn-success text-nowrap" title="Marcar como Comprado" onclick="markOrderAsBought(${o.id})" ${isBought ? 'disabled' : ''}><i class="bi bi-cart-check"></i> <span class="d-none d-xl-inline">Comprado</span></button>
                                    <button class="btn btn-sm btn-danger text-nowrap" title="Ver PDF" onclick="downloadOrderPdf(${o.id})"><i class="bi bi-file-earmark-pdf"></i> <span class="d-none d-xl-inline">PDF</span></button>
                                </div>
                            </td>
                        </tr>
                    `;
                },
                onEmpty: () => '<tr><td colspan="8" class="text-center py-4 text-muted">No hay órdenes de compra registradas.</td></tr>'
            });
        } else {
            paginator.updateData(r.data || []);
        }
    });
}

function preloadProducts() {
    $.get('/api/products/active', function (r) {
        if (r.status === 'success') {
            activeProducts = r.data || [];
        }
    });
}

function showCreateOrderModal() {
    $('#createOrderForm')[0].reset();
    $('#poItemsBody').empty();
    $('#poTotalLabel').text('$0.00');


    $('#poSupplierSelect').html('<option value="">Cargando proveedores...</option>');
    $.get('/api/suppliers/active', function(r) {
        if (r.status === 'success') {
            let opts = '<option value="">Seleccione proveedor...</option>';
            (r.data || []).forEach(s => {
                opts += `<option value="${s.rif}">${escapeHtml(s.nombre)} (${escapeHtml(s.rif)})</option>`;
            });
            $('#poSupplierSelect').html(opts);
        } else {
            $('#poSupplierSelect').html('<option value="">Error al cargar proveedores</option>');
        }
    });


    $('#poSucursalSelect').html('<option value="">Cargando sucursales...</option>');
    $.get('/api/sucursales/active', function(r) {
        if (r.status === 'success') {
            let opts = '<option value="">Seleccione sucursal...</option>';
            (r.data || []).forEach(s => {
                opts += `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`;
            });
            $('#poSucursalSelect').html(opts);
        } else {
            $('#poSucursalSelect').html('<option value="">Error al cargar sucursales</option>');
        }
    });


    addProductRow();

    new bootstrap.Modal('#createOrderModal').show();
    Validator.initTracking('createOrderForm');
}

function addProductRow() {
    const tbody = $('#poItemsBody');
    const index = tbody.find('tr').length;

    let productOptions = '<option value="">Seleccione producto...</option>';
    activeProducts.forEach(p => {
        productOptions += `<option value="${p.codigo}" data-price="${p.precio || 0}">${escapeHtml(p.nombre)} (${escapeHtml(p.codigo)})</option>`;
    });

    const row = `
        <tr class="po-item-row" id="poRow_${index}">
            <td>
                <select class="form-select po-product-select" required onchange="handleProductChange(this)">
                    ${productOptions}
                </select>
            </td>
            <td>
                <input type="number" class="form-control po-qty-input" min="1" value="1" required oninput="calculateRowSubtotal(this)">
            </td>
            <td>
                <input type="number" class="form-control po-price-input" min="0" step="0.01" value="0.00" required oninput="calculateRowSubtotal(this)">
            </td>
            <td class="fw-bold po-subtotal-label">$0.00</td>
            <td>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeProductRow(this)"><i class="bi bi-trash"></i></button>
            </td>
        </tr>
    `;
    tbody.append(row);
}

function removeProductRow(btn) {
    if ($('#poItemsBody tr').length <= 1) {
        showToast('Debe incluir al menos un producto.', 'warning');
        return;
    }
    $(btn).closest('tr').remove();
    calculateGrandTotal();
}

function handleProductChange(select) {
    const selectedOpt = $(select).find('option:selected');
    const defaultPrice = Number(selectedOpt.data('price') || 0).toFixed(2);
    const row = $(select).closest('tr');
    row.find('.po-price-input').val(defaultPrice);
    calculateRowSubtotal(select);
}

function calculateRowSubtotal(el) {
    const row = $(el).closest('tr');
    const qty = parseInt(row.find('.po-qty-input').val() || 0);
    const price = parseFloat(row.find('.po-price-input').val() || 0);
    const subtotal = qty * price;
    row.find('.po-subtotal-label').text(`$${subtotal.toFixed(2)}`);
    calculateGrandTotal();
}

function calculateGrandTotal() {
    let grandTotal = 0;
    $('.po-item-row').each(function () {
        const qty = parseInt($(this).find('.po-qty-input').val() || 0);
        const price = parseFloat($(this).find('.po-price-input').val() || 0);
        grandTotal += qty * price;
    });
    $('#poTotalLabel').text(`$${grandTotal.toFixed(2)}`);
}

function savePurchaseOrder() {
    if (!Validator.validate('createOrderForm')) {
        showToast('Corrija los errores del formulario.', 'warning');
        return;
    }
    const supplier = $('#poSupplierSelect').val();
    const sucursal = $('#poSucursalSelect').val();

    const items = [];
    let isValid = true;

    $('.po-item-row').each(function () {
        const product = $(this).find('.po-product-select').val();
        const qty = parseInt($(this).find('.po-qty-input').val() || 0);
        const price = parseFloat($(this).find('.po-price-input').val() || 0);

        if (!product) {
            showToast('Seleccione un producto en cada fila.', 'warning');
            isValid = false;
            return false;
        }
        if (qty <= 0) {
            showToast('La cantidad debe ser mayor a cero.', 'warning');
            isValid = false;
            return false;
        }
        if (price < 0) {
            showToast('El precio no puede ser negativo.', 'warning');
            isValid = false;
            return false;
        }

        items.push({
            producto_codigo: product,
            cantidad: qty,
            precio_unitario: price
        });
    });

    if (!isValid) return;
    if (!items.length) {
        showToast('Debe agregar al menos un producto.', 'warning');
        return;
    }

    const btn = document.querySelector('#createOrderModal .btn-orange');
    setButtonLoading(btn, true, 'Registrando...');

    const payload = {
        proveedor_rif: supplier,
        sucursal_id: sucursal,
        observaciones: $('#poObservaciones').val(),
        items: items
    };

    apiCall('/api/purchase-orders/', 'POST', payload).then(r => {
        if (r.status === 'success') {
            showToast(r.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('createOrderModal'))?.hide();
            loadStats();
            loadOrders();
        } else {
            showToast(r.message || 'No se pudo registrar la orden de compra.', 'error');
        }
    }).finally(() => setButtonLoading(btn, false));
}

function markOrderAsBought(id) {
    confirmAction('¿Está seguro de marcar esta orden como comprada? Esto sumará los productos comprados al stock de la sucursal.', () => {
        apiCall(`/api/purchase-orders/${id}/buy`, 'POST').then(r => {
            if (r.status === 'success') {
                showToast(r.message, 'success');
                loadStats();
                loadOrders();
            } else {
                showToast(r.message || 'No se pudo procesar la compra.', 'error');
            }
        });
    }, { type: 'question', confirmText: 'Comprar', confirmColor: '#16a34a' });
}

function downloadOrderPdf(id) {
    window.location.href = `/api/purchase-orders/${id}/pdf`;
}

function viewOrderDetails(id) {
    apiCall(`/api/purchase-orders/${id}`).then(r => {
        if (r.status !== 'success') {
            showToast(r.message || 'No se pudo cargar la orden.', 'error');
            return;
        }
        const o = r.data;
        const dateStr = formatDate(o.fecha);
        let itemsHtml = '';
        o.detalles.forEach(d => {
            itemsHtml += `
                <tr>
                    <td>${escapeHtml(d.producto_codigo)}</td>
                    <td>${escapeHtml(d.producto_nombre)}</td>
                    <td class="text-center">${d.cantidad}</td>
                    <td class="text-end">$${Number(d.precio_unitario).toFixed(2)}</td>
                    <td class="text-end fw-bold">$${Number(d.subtotal).toFixed(2)}</td>
                </tr>
            `;
        });

        const html = `
            <div class="row g-3 mb-3">
                <div class="col-6">
                    <p class="mb-1"><strong>Proveedor:</strong> ${escapeHtml(o.proveedor_nombre)}</p>
                    <p class="mb-1"><strong>RIF:</strong> ${escapeHtml(o.proveedor_rif)}</p>
                    <p class="mb-1"><strong>Teléfono:</strong> ${escapeHtml(o.proveedor_telefono || 'N/A')}</p>
                </div>
                <div class="col-6">
                    <p class="mb-1"><strong>Sucursal destino:</strong> ${escapeHtml(o.sucursal_nombre)}</p>
                    <p class="mb-1"><strong>Fecha:</strong> ${dateStr}</p>
                    <p class="mb-1"><strong>Estado:</strong> <span class="badge-status ${o.estado === 'comprado' ? 'badge-active' : 'badge-pending'}">${o.estado.upper()}</span></p>
                </div>
            </div>
            ${o.observaciones ? `<div class="alert alert-info mb-3"><strong>Observaciones:</strong><br>${escapeHtml(o.observaciones)}</div>` : ''}
            <table class="table table-bordered align-middle">
                <thead>
                    <tr class="table-light">
                        <th>Código</th>
                        <th>Producto</th>
                        <th class="text-center" style="width: 80px;">Cant.</th>
                        <th class="text-end" style="width: 120px;">Precio Unit.</th>
                        <th class="text-end" style="width: 120px;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    ${itemsHtml}
                    <tr class="table-light fw-bold">
                        <td colspan="4" class="text-end">TOTAL COMPRA:</td>
                        <td class="text-end text-orange">$${Number(o.total).toFixed(2)}</td>
                    </tr>
                </tbody>
            </table>
        `;
        $('#detailOrderContent').html(html);
        new bootstrap.Modal('#detailOrderModal').show();
    });
}
String.prototype.upper = function() {
    return this.toUpperCase();
}
