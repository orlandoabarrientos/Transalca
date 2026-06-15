let currentReport = 'sales';

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="reports"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');

    const today = new Date();
    const lastMonth = new Date();
    lastMonth.setDate(today.getDate() - 30);
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
    document.getElementById('startDate').value = lastMonth.toISOString().split('T')[0];

    switchReport('sales', document.querySelector('.report-tab[data-report="sales"]'));
});

const reportDescriptions = {
    sales: "Muestra las órdenes de venta registradas en el sistema, permitiendo filtrar por fechas y estados (pendiente, aprobada, completada, cancelada) para evaluar el volumen de facturación.",
    payments: "Detalla el flujo de pagos realizados por los clientes, incluyendo número de referencia, monto, moneda, método de pago y estado de verificación (pendiente, aprobado, rechazado).",
    inventory: "Presenta el Kardex de stock con las entradas y salidas de inventario por producto, indicando la cantidad, motivo del movimiento, tipo de transacción y fecha.",
    mechanics: "Evalúa el desempeño de los mecánicos de la empresa según los servicios asignados, completados, tasa de efectividad e ingresos totales generados en dólares.",
    bitacora: "Exhibe la bitácora de auditoría del sistema con las acciones críticas realizadas por los usuarios (creación, modificación, eliminación), indicando módulo, fecha, usuario e IP."
};

function switchReport(type, el) {
    currentReport = type;
    document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
    if (el) el.classList.add('active');

    const descEl = document.getElementById('reportDescription');
    if (descEl) {
        descEl.textContent = reportDescriptions[type] || 'Seleccione un reporte para ver su descripción.';
    }

    const statusContainer = document.getElementById('statusFilterContainer');
    const statusSelect = document.getElementById('status');
    statusSelect.innerHTML = '<option value="">Todos</option>';

    if (type === 'sales') {
        statusContainer.style.display = 'block';
        $('#statusFilterContainer label').text('Estado');
        ['pendiente', 'aprobada', 'completada', 'cancelada'].forEach(s => statusSelect.innerHTML += `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)}</option>`);
    } else if (type === 'payments') {
        statusContainer.style.display = 'block';
        $('#statusFilterContainer label').text('Estado');
        ['pendiente', 'aprobado', 'rechazado'].forEach(s => statusSelect.innerHTML += `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)}</option>`);
    } else if (type === 'bitacora') {
        statusContainer.style.display = 'block';
        $('#statusFilterContainer label').text('Modulo');
        [['AUTH', 'AUTH'], ['USUARIOS', 'USUARIOS'], ['PRODUCTOS', 'PRODUCTOS'], ['INVENTARIO', 'GESTIONAR STOCK DE PRODUCTOS'], ['VENTAS', 'VENTAS'], ['SERVICIOS', 'SERVICIOS']].forEach(s => statusSelect.innerHTML += `<option value="${s[0]}">${s[1]}</option>`);
    } else {
        statusContainer.style.display = 'none';
        $('#statusFilterContainer label').text('Estado');
    }

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
    const status = document.getElementById('status').value;

    let url = `/api/reports/query?type=${currentReport}`;
    if (sDate) url += `&start_date=${sDate}`;
    if (eDate) url += `&end_date=${eDate}`;
    if (status && document.getElementById('statusFilterContainer').style.display !== 'none') url += `&status=${status}`;

    apiCall(url).then(res => {
        if (!res.data) return;
        renderTable(currentReport, res.data);
    });
}

let paginator = null;

function renderTable(type, data) {
    const head = document.getElementById('reportHead');

    if (data.length === 0) {
        head.innerHTML = '';
        document.getElementById('reportBody').innerHTML = '<tr><td class="text-center py-4 text-muted"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No hay registros para este periodo</td></tr>';
        if (paginator) {
            if (paginator.controlsEl) paginator.controlsEl.innerHTML = '';
            if (paginator.infoEl) paginator.infoEl.textContent = '';
        }
        return;
    }

    let hHtml = '<tr>';
    if (type === 'sales') {
        hHtml += '<th>ID</th><th>Cliente</th><th>Fecha</th><th>Total</th><th>Estado</th>';
    } else if (type === 'payments') {
        hHtml += '<th>ID</th><th>Orden</th><th>Cliente</th><th>Referencia</th><th>Monto</th><th>Método</th><th>Estado</th><th>Fecha</th>';
    } else if (type === 'inventory') {
        hHtml += '<th>ID</th><th>Producto</th><th>Código</th><th>Motivo</th><th>Tipo</th><th>Cantidad</th><th>Fecha</th>';
    } else if (type === 'mechanics') {
        hHtml += '<th>Mecánico</th><th>Servicios Asignados</th><th>Completados</th><th>Desempeño</th><th>Ingreso Generado</th>';
    } else if (type === 'bitacora') {
        hHtml += '<th>ID</th><th>Fecha</th><th>Usuario</th><th>Módulo</th><th>Acción</th><th>Descripción</th><th>IP</th>';
    }
    hHtml += '</tr>';
    head.innerHTML = hHtml;

    if (!paginator) {
        paginator = new TablePaginator('reportBody', {
            allData: data,
            itemName: 'registros',
            renderRow: (d) => {
                if (currentReport === 'sales') {
                    const st = String(d.estado || '').toLowerCase();
                    const color = ['aprobada', 'aprobado', 'completada', 'completado', 'entregada', 'entregado', 'verificado', 'verificada', 'pagado', 'activo'].includes(st) ? 'active' : ['pendiente', 'procesando', 'enviada'].includes(st) ? 'pending' : 'inactive';
                    return `<tr><td>#${d.id}</td><td>${escapeHtml(d.cliente)}</td><td>${formatDate(d.fecha)}</td><td data-usd-price="${d.total}">${formatUsdBs(d.total)}</td><td><span class="badge-status badge-${color}">${escapeHtml(d.estado)}</span></td></tr>`;
                } else if (currentReport === 'payments') {
                    const st = String(d.estado || '').toLowerCase();
                    const color = ['aprobado', 'aprobada', 'verificado', 'verificada', 'pagado', 'activo'].includes(st) ? 'active' : ['pendiente', 'procesando'].includes(st) ? 'pending' : 'inactive';
                    return `<tr><td>#${d.id}</td><td><a href="#">#${d.orden_id}</a></td><td>${escapeHtml(d.cliente)}</td><td>${escapeHtml(d.referencia)}</td><td>${escapeHtml(d.monto)} ${escapeHtml(d.moneda)}</td><td>${escapeHtml(d.metodo)}</td><td><span class="badge-status badge-${color}">${escapeHtml(d.estado)}</span></td><td>${formatDate(d.fecha)}</td></tr>`;
                } else if (currentReport === 'inventory') {
                    return `<tr><td>#${d.id}</td><td>${escapeHtml(d.producto)}</td><td><small class="text-muted">${escapeHtml(d.codigo)}</small></td><td>${escapeHtml(d.motivo)}</td><td><span class="badge-status ${d.tipo === 'entrada' ? 'badge-active' : 'badge-inactive'}">${escapeHtml(d.tipo)}</span></td><td>${escapeHtml(d.cantidad)}</td><td>${formatDate(d.fecha)}</td></tr>`;
                } else if (currentReport === 'mechanics') {
                    const perf = d.total_asignados > 0 ? Math.round((d.total_completados / d.total_asignados) * 100) : 0;
                    const perfColor = perf > 80 ? 'success' : perf > 50 ? 'warning' : 'danger';
                    return `<tr><td><strong>${escapeHtml(d.mecanico_nombre)}</strong></td><td>${d.total_asignados}</td><td>${d.total_completados}</td><td><div class="progress" style="height:6px;width:80px;display:inline-flex;margin-right:8px;"><div class="progress-bar bg-${perfColor}" style="width:${perf}%;height:100%"></div></div><small>${perf}%</small></td><td>$${formatCurrency(d.ingreso_generado)}</td></tr>`;
                } else if (currentReport === 'bitacora') {
                    return `<tr><td>${d.id}</td><td>${formatDate(d.fecha)}</td><td>${escapeHtml(d.usuario)}</td><td><span class="badge-status badge-info">${escapeHtml(d.modulo)}</span></td><td><strong>${escapeHtml(d.accion)}</strong></td><td>${escapeHtml(d.descripcion)}</td><td><small class="text-muted">${escapeHtml(d.ip)}</small></td></tr>`;
                }
                return '';
            },
            onEmpty: () => '<tr><td class="text-center py-4 text-muted"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No hay registros para este periodo</td></tr>'
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
    const status = document.getElementById('status').value;

    let url = `/api/reports/export?type=${currentReport}&format=${format}`;
    if (sDate) url += `&start_date=${sDate}`;
    if (eDate) url += `&end_date=${eDate}`;
    if (status && document.getElementById('statusFilterContainer').style.display !== 'none') url += `&status=${status}`;

    window.open(url, '_blank');
    bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
}
