let currentReport = 'sales';
let paginator = null;

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { 
        document.querySelector('[data-page="reports"]')?.classList.add('active'); 
    });
    $('#navbarContainer').load('/components/admin_navbar.html');

    const today = new Date();
    const lastMonth = new Date();
    lastMonth.setDate(today.getDate() - 30);
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
    document.getElementById('startDate').value = lastMonth.toISOString().split('T')[0];

    loadFilterOptions();
    switchReport('sales', document.querySelector('.report-tab[data-report="sales"]'));

    $('#filterForm').on('change', 'select', function () {
        loadReportData();
    });
});

const reportDescriptions = {
    sales: "Muestra las órdenes de venta registradas en el sistema, permitiendo filtrar por fechas, estados, métodos de pago y tipo de cliente (natural/jurídica).",
    top_products: "Presenta los productos más vendidos en el sistema (únicamente de órdenes aprobadas o completadas) ordenados por unidades vendidas o ingresos, permitiendo filtrar por fechas, categoría, marca, sucursal, ordenamiento y límite de ranking.",
    payments: "Detalla el flujo de pagos realizados por los clientes, permitiendo filtrar por fechas, moneda (USD/VES), tipo de cliente, método de pago y estado de verificación.",
    inventory: "Presenta el Kardex de stock e inventario, permitiendo filtrar por fechas, categoría, marca, sucursal y nivel de stock (alerta de mínimo, agotado o disponible).",
    mechanics: "Evalúa el desempeño de los mecánicos según los servicios asignados, completados, tasa de efectividad e ingresos generados, con filtro por mecánico específico y estado.",
    bitacora: "Exhibe la bitácora de auditoría del sistema con las acciones críticas realizadas por los usuarios, permitiendo filtrar por módulo, fecha y tipo de acción realizada."
};

function loadFilterOptions() {
    // Categorías
    apiCall('/api/categories/').then(res => {
        if (res && res.data && Array.isArray(res.data)) {
            const catSelect = document.getElementById('categoryFilter');
            if (catSelect) {
                catSelect.innerHTML = '<option value="">Todas</option>';
                res.data.forEach(c => {
                    const name = c.nombre_categoria || c.nombre;
                    if (name) catSelect.innerHTML += `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`;
                });
                if (window.scheduleDomEnhancements) scheduleDomEnhancements();
            }
        }
    }).catch(console.error);

    // Marcas
    apiCall('/api/brands/').then(res => {
        if (res && res.data && Array.isArray(res.data)) {
            const brandSelect = document.getElementById('brandFilter');
            if (brandSelect) {
                brandSelect.innerHTML = '<option value="">Todas</option>';
                res.data.forEach(b => {
                    const name = b.nombre_marca || b.nombre;
                    if (name) brandSelect.innerHTML += `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`;
                });
                if (window.scheduleDomEnhancements) scheduleDomEnhancements();
            }
        }
    }).catch(console.error);

    // Sucursales
    apiCall('/api/sucursales/active').then(res => {
        if (!res || !res.data || !Array.isArray(res.data) || res.data.length === 0) {
            return apiCall('/api/sucursales/');
        }
        return res;
    }).then(res => {
        if (res && res.data && Array.isArray(res.data)) {
            const sucSelect = document.getElementById('sucursalFilter');
            if (sucSelect) {
                const currentVal = sucSelect.value;
                sucSelect.innerHTML = '<option value="">Todas</option>';
                res.data.forEach(s => {
                    const id = s.id_sucursal ?? s.id;
                    const name = s.nombre_sucursal ?? s.nombre;
                    if (name && id !== undefined && id !== null) {
                        const opt = document.createElement('option');
                        opt.value = String(id);
                        opt.textContent = name;
                        sucSelect.appendChild(opt);
                    }
                });
                if (currentVal) sucSelect.value = currentVal;
                if (window.scheduleDomEnhancements) scheduleDomEnhancements();
            }
        }
    }).catch(console.error);

    // Métodos de Pago
    apiCall('/api/payment-methods/active').then(res => {
        if (!res || !res.data || !Array.isArray(res.data)) {
            return apiCall('/api/payment-methods/');
        }
        return res;
    }).then(res => {
        if (res && res.data && Array.isArray(res.data)) {
            const pmSelect = document.getElementById('paymentMethodFilter');
            if (pmSelect) {
                pmSelect.innerHTML = '<option value="">Todos</option>';
                res.data.forEach(m => {
                    const id = m.id_metodo_pago || m.id;
                    const name = m.nombre_metodo_pago || m.nombre;
                    if (name) pmSelect.innerHTML += `<option value="${id}">${escapeHtml(name)}</option>`;
                });
                if (window.scheduleDomEnhancements) scheduleDomEnhancements();
            }
        }
    }).catch(console.error);

    // Mecánicos
    apiCall('/api/mechanics/').then(res => {
        if (res && res.data && Array.isArray(res.data)) {
            const mecSelect = document.getElementById('mechanicFilter');
            if (mecSelect) {
                mecSelect.innerHTML = '<option value="">Todos</option>';
                res.data.forEach(m => {
                    const ced = m.cedula_mecanico || m.cedula;
                    const nom = `${m.nombre_mecanico || m.nombre || ''} ${m.apellido_mecanico || m.apellido || ''}`.trim();
                    if (ced) mecSelect.innerHTML += `<option value="${escapeHtml(ced)}">${escapeHtml(nom || ced)}</option>`;
                });
                if (window.scheduleDomEnhancements) scheduleDomEnhancements();
            }
        }
    }).catch(console.error);
}

function switchReport(type, el) {
    currentReport = type;
    document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
    if (el) el.classList.add('active');

    const descEl = document.getElementById('reportDescription');
    if (descEl) {
        descEl.textContent = reportDescriptions[type] || 'Seleccione un reporte para ver su descripción.';
    }

    const startContainer = document.getElementById('startDateContainer');
    const endContainer = document.getElementById('endDateContainer');
    const catContainer = document.getElementById('categoryFilterContainer');
    const brandContainer = document.getElementById('brandFilterContainer');
    const statusContainer = document.getElementById('statusFilterContainer');
    const statusLabel = document.getElementById('statusLabel');
    const statusSelect = document.getElementById('status');
    const pmContainer = document.getElementById('paymentMethodFilterContainer');
    const clientTypeContainer = document.getElementById('clientTypeFilterContainer');
    const monedaContainer = document.getElementById('monedaFilterContainer');
    const stockStatusContainer = document.getElementById('stockStatusFilterContainer');
    const mechanicContainer = document.getElementById('mechanicFilterContainer');
    const sucursalContainer = document.getElementById('sucursalFilterContainer');
    const limitContainer = document.getElementById('limitFilterContainer');
    const orderByContainer = document.getElementById('orderByFilterContainer');
    const accionContainer = document.getElementById('accionFilterContainer');
    const searchContainer = document.getElementById('searchFilterContainer');
    const searchInput = document.getElementById('searchFilter');
    const btnContainer = document.getElementById('filterBtnContainer');

    statusSelect.innerHTML = '<option value="">Todos</option>';
    if (accionContainer) accionContainer.style.display = 'none';
    if (sucursalContainer) sucursalContainer.style.display = 'none';

    if (type === 'top_products') {
        startContainer.className = 'col-md-2';
        endContainer.className = 'col-md-2';
        catContainer.style.display = 'block';
        catContainer.className = 'col-md-2';
        brandContainer.style.display = 'block';
        brandContainer.className = 'col-md-2';
        if (sucursalContainer) {
            sucursalContainer.style.display = 'block';
            sucursalContainer.className = 'col-md-2';
        }
        limitContainer.style.display = 'block';
        limitContainer.className = 'col-md-2';
        orderByContainer.style.display = 'block';
        orderByContainer.className = 'col-md-2';
        btnContainer.className = 'col-md-2';
        searchContainer.style.display = 'none';
        stockStatusContainer.style.display = 'none';
        statusContainer.style.display = 'none';
        pmContainer.style.display = 'none';
        clientTypeContainer.style.display = 'none';
        monedaContainer.style.display = 'none';
        mechanicContainer.style.display = 'none';
    } else if (type === 'sales') {
        startContainer.className = 'col-md-2';
        endContainer.className = 'col-md-2';
        catContainer.style.display = 'none';
        brandContainer.style.display = 'none';
        stockStatusContainer.style.display = 'none';
        orderByContainer.style.display = 'none';
        limitContainer.style.display = 'none';
        statusContainer.style.display = 'block';
        statusContainer.className = 'col-md-2';
        statusLabel.textContent = 'Estado';
        ['pendiente', 'aprobada', 'completada', 'cancelada'].forEach(s => {
            statusSelect.innerHTML += `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)}</option>`;
        });
        pmContainer.style.display = 'block';
        pmContainer.className = 'col-md-2';
        clientTypeContainer.style.display = 'block';
        clientTypeContainer.className = 'col-md-2';
        if (sucursalContainer) {
            sucursalContainer.style.display = 'none';
        }
        searchContainer.style.display = 'none';
        monedaContainer.style.display = 'none';
        mechanicContainer.style.display = 'none';
        btnContainer.className = 'col-md-2';
    } else if (type === 'payments') {
        startContainer.className = 'col-md-2';
        endContainer.className = 'col-md-2';
        catContainer.style.display = 'none';
        brandContainer.style.display = 'none';
        stockStatusContainer.style.display = 'none';
        orderByContainer.style.display = 'none';
        limitContainer.style.display = 'none';
        statusContainer.style.display = 'block';
        statusContainer.className = 'col-md-2';
        statusLabel.textContent = 'Estado';
        ['pendiente', 'verificado', 'rechazado'].forEach(s => {
            statusSelect.innerHTML += `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)}</option>`;
        });
        pmContainer.style.display = 'block';
        pmContainer.className = 'col-md-2';
        monedaContainer.style.display = 'block';
        monedaContainer.className = 'col-md-2';
        clientTypeContainer.style.display = 'block';
        clientTypeContainer.className = 'col-md-2';
        searchContainer.style.display = 'none';
        mechanicContainer.style.display = 'none';
        btnContainer.className = 'col-md-2';
    } else if (type === 'inventory') {
        startContainer.className = 'col-md-2';
        endContainer.className = 'col-md-2';
        catContainer.style.display = 'block';
        catContainer.className = 'col-md-2';
        brandContainer.style.display = 'block';
        brandContainer.className = 'col-md-2';
        if (sucursalContainer) {
            sucursalContainer.style.display = 'block';
            sucursalContainer.className = 'col-md-2';
        }
        stockStatusContainer.style.display = 'block';
        stockStatusContainer.className = 'col-md-2';
        searchContainer.style.display = 'none';
        statusContainer.style.display = 'none';
        pmContainer.style.display = 'none';
        clientTypeContainer.style.display = 'none';
        monedaContainer.style.display = 'none';
        limitContainer.style.display = 'none';
        orderByContainer.style.display = 'none';
        mechanicContainer.style.display = 'none';
        btnContainer.className = 'col-md-2';
    } else if (type === 'mechanics') {
        startContainer.className = 'col-md-3';
        endContainer.className = 'col-md-3';
        mechanicContainer.style.display = 'block';
        mechanicContainer.className = 'col-md-2';
        statusContainer.style.display = 'block';
        statusContainer.className = 'col-md-2';
        statusLabel.textContent = 'Estado Servicio';
        ['asignado', 'en proceso', 'completado'].forEach(s => {
            statusSelect.innerHTML += `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)}</option>`;
        });
        catContainer.style.display = 'none';
        brandContainer.style.display = 'none';
        pmContainer.style.display = 'none';
        clientTypeContainer.style.display = 'none';
        monedaContainer.style.display = 'none';
        stockStatusContainer.style.display = 'none';
        limitContainer.style.display = 'none';
        orderByContainer.style.display = 'none';
        searchContainer.style.display = 'none';
        btnContainer.className = 'col-md-2';
    } else if (type === 'bitacora') {
        startContainer.className = 'col-md-2';
        endContainer.className = 'col-md-2';
        statusContainer.style.display = 'block';
        statusContainer.className = 'col-md-3';
        statusLabel.textContent = 'Módulo';
        const bitacoraModulos = [
            ['AUTH', 'AUTH (Autenticación)'],
            ['CATEGORIAS', 'CATEGORÍAS'],
            ['CLIENTES', 'CLIENTES'],
            ['COMISIONES', 'COMISIONES'],
            ['CREDITO', 'CRÉDITO'],
            ['EMPRESAS', 'EMPRESAS'],
            ['ESCANER', 'ESCÁNER'],
            ['INVENTARIO', 'INVENTARIO / STOCK'],
            ['MARCAS', 'MARCAS'],
            ['MECANICOS', 'MECÁNICOS'],
            ['METODOS_PAGO', 'MÉTODOS DE PAGO'],
            ['ORDENES', 'ÓRDENES DE VENTA'],
            ['ORDEN_COMPRA', 'ÓRDENES DE COMPRA'],
            ['PAGOS', 'PAGOS'],
            ['PRODUCTOS', 'PRODUCTOS'],
            ['PROMOCIONES', 'PROMOCIONES'],
            ['PROVEEDORES', 'PROVEEDORES'],
            ['QR', 'CÓDIGOS QR'],
            ['RESPALDOS', 'RESPALDOS'],
            ['ROLES', 'ROLES Y PERMISOS'],
            ['SERVICIOS', 'SERVICIOS'],
            ['SERVICIO_MECANICO', 'SERVICIO MECÁNICO'],
            ['TASAS_CAMBIO', 'TASAS DE CAMBIO'],
            ['TICKETS', 'TICKETS DE SOPORTE'],
            ['USUARIOS', 'USUARIOS'],
            ['VEHICULOS', 'VEHÍCULOS']
        ];
        bitacoraModulos.forEach(s => {
            statusSelect.innerHTML += `<option value="${s[0]}">${s[1]}</option>`;
        });
        if (accionContainer) {
            accionContainer.style.display = 'block';
            accionContainer.className = 'col-md-3';
        }
        searchContainer.style.display = 'none';
        catContainer.style.display = 'none';
        brandContainer.style.display = 'none';
        pmContainer.style.display = 'none';
        clientTypeContainer.style.display = 'none';
        monedaContainer.style.display = 'none';
        stockStatusContainer.style.display = 'none';
        limitContainer.style.display = 'none';
        orderByContainer.style.display = 'none';
        mechanicContainer.style.display = 'none';
        btnContainer.className = 'col-md-2';
    }

    if (window.scheduleDomEnhancements) scheduleDomEnhancements();

    document.getElementById('reportHead').innerHTML = '';
    document.getElementById('reportBody').innerHTML = '<tr><td class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></td></tr>';
    
    if (paginator) {
        if (paginator.controlsEl) paginator.controlsEl.innerHTML = '';
        if (paginator.infoEl) paginator.infoEl.textContent = '';
        paginator = null;
    }

    loadReportData();
}

function loadReportData() {
    const sDate = document.getElementById('startDate').value;
    const eDate = document.getElementById('endDate').value;
    const category = document.getElementById('categoryFilter').value;
    const brand = document.getElementById('brandFilter').value;
    const status = document.getElementById('status').value;
    const paymentMethod = document.getElementById('paymentMethodFilter').value;
    const clientType = document.getElementById('clientTypeFilter').value;
    const moneda = document.getElementById('monedaFilter').value;
    const stockStatus = document.getElementById('stockStatusFilter').value;
    const mechanicCedula = document.getElementById('mechanicFilter').value;
    const sucursalId = (document.getElementById('sucursalFilter')?.value || $('#sucursalFilter').val() || '').trim();
    const limit = document.getElementById('limitFilter').value;
    const orderBy = document.getElementById('orderByFilter').value;
    const accionTipo = document.getElementById('accionFilter')?.value;
    const search = document.getElementById('searchFilter').value;

    let url = `/api/reports/query?type=${currentReport}`;
    if (sDate) url += `&start_date=${encodeURIComponent(sDate)}`;
    if (eDate) url += `&end_date=${encodeURIComponent(eDate)}`;
    if (category && document.getElementById('categoryFilterContainer').style.display !== 'none') url += `&category=${encodeURIComponent(category)}`;
    if (brand && document.getElementById('brandFilterContainer').style.display !== 'none') url += `&brand=${encodeURIComponent(brand)}`;
    if (status && document.getElementById('statusFilterContainer').style.display !== 'none') url += `&status=${encodeURIComponent(status)}`;
    if (paymentMethod && document.getElementById('paymentMethodFilterContainer').style.display !== 'none') url += `&payment_method=${encodeURIComponent(paymentMethod)}`;
    if (clientType && document.getElementById('clientTypeFilterContainer').style.display !== 'none') url += `&client_type=${encodeURIComponent(clientType)}`;
    if (moneda && document.getElementById('monedaFilterContainer').style.display !== 'none') url += `&moneda=${encodeURIComponent(moneda)}`;
    if (stockStatus && document.getElementById('stockStatusFilterContainer').style.display !== 'none') url += `&stock_status=${encodeURIComponent(stockStatus)}`;
    if (mechanicCedula && document.getElementById('mechanicFilterContainer').style.display !== 'none') url += `&mechanic_cedula=${encodeURIComponent(mechanicCedula)}`;
    if (sucursalId && sucursalId !== '' && document.getElementById('sucursalFilterContainer') && document.getElementById('sucursalFilterContainer').style.display !== 'none') url += `&sucursal_id=${encodeURIComponent(sucursalId)}`;
    if (limit && document.getElementById('limitFilterContainer').style.display !== 'none') url += `&limit=${encodeURIComponent(limit)}`;
    if (orderBy && document.getElementById('orderByFilterContainer').style.display !== 'none') url += `&order_by=${encodeURIComponent(orderBy)}`;
    if (accionTipo && document.getElementById('accionFilterContainer') && document.getElementById('accionFilterContainer').style.display !== 'none') url += `&accion_tipo=${encodeURIComponent(accionTipo)}`;
    if (search && document.getElementById('searchFilterContainer').style.display !== 'none') url += `&search=${encodeURIComponent(search)}`;

    apiCall(url).then(res => {
        if (!res || res.status === 'error' || !res.data) {
            renderTable(currentReport, []);
            return;
        }
        renderTable(currentReport, res.data);
    }).catch(err => {
        console.error('Error cargando datos de reporte:', err);
        renderTable(currentReport, []);
    });
}

function renderTable(type, data) {
    const head = document.getElementById('reportHead');
    const body = document.getElementById('reportBody');

    let hHtml = '<tr>';
    if (type === 'sales') {
        hHtml += '<th>ID</th><th>Cliente</th><th>Tipo</th><th>Método</th><th>Fecha</th><th>Total</th><th>Estado</th>';
    } else if (type === 'top_products') {
        hHtml += '<th>#</th><th>Código</th><th>Producto</th><th>Categoría</th><th>Marca</th><th>Cantidad Vendida</th><th>Total Recaudado</th><th>Órdenes</th>';
    } else if (type === 'payments') {
        hHtml += '<th>ID</th><th>Orden</th><th>Cliente</th><th>Referencia</th><th>Monto</th><th>Moneda</th><th>Método</th><th>Estado</th><th>Fecha</th>';
    } else if (type === 'inventory') {
        hHtml += '<th>ID</th><th>Producto</th><th>Código</th><th>Categoría</th><th>Marca</th><th>Tipo</th><th>Cantidad</th><th>Fecha</th>';
    } else if (type === 'mechanics') {
        hHtml += '<th>Mecánico</th><th>Servicios Asignados</th><th>Completados</th><th>Desempeño</th><th>Ingreso Generado</th>';
    } else if (type === 'bitacora') {
        hHtml += '<th>ID</th><th>Fecha</th><th>Usuario</th><th>Módulo</th><th>Acción</th><th>Descripción</th><th>IP</th>';
    }
    hHtml += '</tr>';
    head.innerHTML = hHtml;

    if (!data || data.length === 0) {
        body.innerHTML = '<tr><td colspan="12" class="text-center py-4 text-muted"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No hay registros para este periodo</td></tr>';
        if (paginator) {
            if (paginator.controlsEl) paginator.controlsEl.innerHTML = '';
            if (paginator.infoEl) paginator.infoEl.textContent = 'Mostrando 0 a 0 de 0 registros';
        }
        return;
    }

    if (!paginator) {
        paginator = new TablePaginator('reportBody', {
            allData: data,
            itemName: 'registros',
            renderRow: (d) => {
                if (currentReport === 'sales') {
                    const st = String(d.estado || '').toLowerCase();
                    const color = ['aprobada', 'aprobado', 'completada', 'completado', 'entregada', 'entregado', 'verificado', 'verificada', 'pagado', 'activo'].includes(st) ? 'active' : ['pendiente', 'procesando', 'enviada'].includes(st) ? 'pending' : 'inactive';
                    const tipoCli = d.tipo_cliente === 'juridica' ? 'Empresa' : 'Natural';
                    return `<tr><td>#${d.id}</td><td>${escapeHtml(d.cliente)}</td><td><small class="text-muted">${tipoCli}</small></td><td><small class="text-muted">${escapeHtml(d.metodo_pago || 'N/A')}</small></td><td>${formatDate(d.fecha)}</td><td data-usd-price="${d.total}">${formatUsdBs(d.total)}</td><td><span class="badge-status badge-${color}">${escapeHtml(d.estado)}</span></td></tr>`;
                } else if (currentReport === 'top_products') {
                    return `<tr><td><strong>${d.ranking}</strong></td><td><small class="text-muted">${escapeHtml(d.codigo)}</small></td><td><strong>${escapeHtml(d.nombre_producto)}</strong></td><td>${escapeHtml(d.categoria)}</td><td>${escapeHtml(d.marca)}</td><td>${d.total_vendido}</td><td data-usd-price="${d.total_recaudado}">${formatUsdBs(d.total_recaudado)}</td><td>${d.total_ordenes}</td></tr>`;
                } else if (currentReport === 'payments') {
                    const st = String(d.estado || '').toLowerCase();
                    const color = ['aprobado', 'aprobada', 'verificado', 'verificada', 'pagado', 'activo'].includes(st) ? 'active' : ['pendiente', 'procesando'].includes(st) ? 'pending' : 'inactive';
                    return `<tr><td>#${d.id}</td><td><a href="#">#${d.orden_id}</a></td><td>${escapeHtml(d.cliente)}</td><td>${escapeHtml(d.referencia)}</td><td>${escapeHtml(d.monto)}</td><td>${escapeHtml(d.moneda)}</td><td>${escapeHtml(d.metodo)}</td><td><span class="badge-status badge-${color}">${escapeHtml(d.estado)}</span></td><td>${formatDate(d.fecha)}</td></tr>`;
                } else if (currentReport === 'inventory') {
                    return `<tr><td>#${d.id}</td><td>${escapeHtml(d.producto)}</td><td><small class="text-muted">${escapeHtml(d.codigo)}</small></td><td>${escapeHtml(d.categoria || 'N/A')}</td><td>${escapeHtml(d.marca || 'N/A')}</td><td><span class="badge-status ${d.tipo === 'entrada' ? 'badge-active' : 'badge-inactive'}">${escapeHtml(d.tipo)}</span></td><td>${escapeHtml(d.cantidad)}</td><td>${formatDate(d.fecha)}</td></tr>`;
                } else if (currentReport === 'mechanics') {
                    const perf = d.total_asignados > 0 ? Math.round((d.total_completados / d.total_asignados) * 100) : 0;
                    const perfColor = perf > 80 ? 'success' : perf > 50 ? 'warning' : 'danger';
                    return `<tr><td><strong>${escapeHtml(d.mecanico_nombre)}</strong></td><td>${d.total_asignados}</td><td>${d.total_completados}</td><td><div class="progress" style="height:6px;width:80px;display:inline-flex;margin-right:8px;"><div class="progress-bar bg-${perfColor}" style="width:${perf}%;height:100%"></div></div><small>${perf}%</small></td><td>$${formatCurrency(d.ingreso_generado)}</td></tr>`;
                } else if (currentReport === 'bitacora') {
                    return `<tr><td>${d.id}</td><td>${formatDate(d.fecha)}</td><td>${escapeHtml(d.usuario)}</td><td><span class="badge-status badge-info">${escapeHtml(d.modulo)}</span></td><td><strong>${escapeHtml(d.accion)}</strong></td><td>${escapeHtml(d.descripcion)}</td><td><small class="text-muted">${escapeHtml(d.ip)}</small></td></tr>`;
                }
                return '';
            },
            onEmpty: () => '<tr><td colspan="12" class="text-center py-4 text-muted"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No hay registros para este periodo</td></tr>'
        });
    } else {
        paginator.updateData(data);
    }
}

function openExportModal() {
    new bootstrap.Modal(document.getElementById('exportModal')).show();
}

function triggerDownload(format) {
    const sDate = document.getElementById('startDate').value;
    const eDate = document.getElementById('endDate').value;
    const category = document.getElementById('categoryFilter').value;
    const brand = document.getElementById('brandFilter').value;
    const status = document.getElementById('status').value;
    const paymentMethod = document.getElementById('paymentMethodFilter').value;
    const clientType = document.getElementById('clientTypeFilter').value;
    const moneda = document.getElementById('monedaFilter').value;
    const stockStatus = document.getElementById('stockStatusFilter').value;
    const mechanicCedula = document.getElementById('mechanicFilter').value;
    const sucursalId = (document.getElementById('sucursalFilter')?.value || $('#sucursalFilter').val() || '').trim();
    const limit = document.getElementById('limitFilter').value;
    const orderBy = document.getElementById('orderByFilter').value;
    const accionTipo = document.getElementById('accionFilter')?.value;
    const search = document.getElementById('searchFilter').value;

    let url = `/api/reports/export?type=${currentReport}&format=${format}`;
    if (sDate) url += `&start_date=${encodeURIComponent(sDate)}`;
    if (eDate) url += `&end_date=${encodeURIComponent(eDate)}`;
    if (category && document.getElementById('categoryFilterContainer').style.display !== 'none') url += `&category=${encodeURIComponent(category)}`;
    if (brand && document.getElementById('brandFilterContainer').style.display !== 'none') url += `&brand=${encodeURIComponent(brand)}`;
    if (status && document.getElementById('statusFilterContainer').style.display !== 'none') url += `&status=${encodeURIComponent(status)}`;
    if (paymentMethod && document.getElementById('paymentMethodFilterContainer').style.display !== 'none') url += `&payment_method=${encodeURIComponent(paymentMethod)}`;
    if (clientType && document.getElementById('clientTypeFilterContainer').style.display !== 'none') url += `&client_type=${encodeURIComponent(clientType)}`;
    if (moneda && document.getElementById('monedaFilterContainer').style.display !== 'none') url += `&moneda=${encodeURIComponent(moneda)}`;
    if (stockStatus && document.getElementById('stockStatusFilterContainer').style.display !== 'none') url += `&stock_status=${encodeURIComponent(stockStatus)}`;
    if (mechanicCedula && document.getElementById('mechanicFilterContainer').style.display !== 'none') url += `&mechanic_cedula=${encodeURIComponent(mechanicCedula)}`;
    if (sucursalId && sucursalId !== '' && document.getElementById('sucursalFilterContainer') && document.getElementById('sucursalFilterContainer').style.display !== 'none') url += `&sucursal_id=${encodeURIComponent(sucursalId)}`;
    if (limit && document.getElementById('limitFilterContainer').style.display !== 'none') url += `&limit=${encodeURIComponent(limit)}`;
    if (orderBy && document.getElementById('orderByFilterContainer').style.display !== 'none') url += `&order_by=${encodeURIComponent(orderBy)}`;
    if (accionTipo && document.getElementById('accionFilterContainer') && document.getElementById('accionFilterContainer').style.display !== 'none') url += `&accion_tipo=${encodeURIComponent(accionTipo)}`;
    if (search && document.getElementById('searchFilterContainer').style.display !== 'none') url += `&search=${encodeURIComponent(search)}`;

    window.open(url, '_blank');
    bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
}
