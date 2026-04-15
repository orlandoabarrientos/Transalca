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

function switchReport(type, el) {
    currentReport = type;
    document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
    if (el) el.classList.add('active');

    const statusContainer = document.getElementById('statusFilterContainer');
    const statusSelect = document.getElementById('status');
    statusSelect.innerHTML = '<option value="">Todos</option>';

    if (type === 'sales') {
        statusContainer.style.display = 'block';
        ['pendiente', 'aprobada', 'completada', 'cancelada'].forEach(s => statusSelect.innerHTML += `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)}</option>`);
    } else if (type === 'payments') {
        statusContainer.style.display = 'block';
        ['pendiente', 'aprobado', 'rechazado'].forEach(s => statusSelect.innerHTML += `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)}</option>`);
    } else if (type === 'bitacora') {
        statusContainer.style.display = 'block';
        $('#statusFilterContainer label').text('Modulo');
        [['AUTH', 'AUTH'], ['USUARIOS', 'USUARIOS'], ['PRODUCTOS', 'PRODUCTOS'], ['INVENTARIO', 'GESTIONAR STOCK DE PRODUCTOS'], ['VENTAS', 'VENTAS'], ['SERVICIOS', 'SERVICIOS']].forEach(s => statusSelect.innerHTML += `<option value="${s[0]}">${s[1]}</option>`);
    } else {
        statusContainer.style.display = 'none';
        $('#statusFilterContainer label').text('Estado');
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

function renderTable(type, data) {
    const head = document.getElementById('reportHead');
    const body = document.getElementById('reportBody');

    if (data.length === 0) {
        head.innerHTML = '';
        body.innerHTML = '<tr><td class="text-center py-4 text-muted"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No hay registros para este periodo</td></tr>';
        return;
    }

    let hHtml = '<tr>';
    let bHtml = '';

    if (type === 'sales') {
        hHtml += '<th>ID</th><th>Cliente</th><th>Fecha</th><th>Total</th><th>Estado</th>';
        data.forEach(d => bHtml += `<tr><td>#${d.id}</td><td>${d.cliente}</td><td>${formatDate(d.fecha)}</td><td>$${formatCurrency(d.total)}</td><td><span class="badge-status badge-${d.estado === 'aprobada' ? 'active' : d.estado === 'pendiente' ? 'pending' : 'inactive'}">${d.estado}</span></td></tr>`);
    } else if (type === 'payments') {
        hHtml += '<th>ID</th><th>Orden</th><th>Cliente</th><th>Referencia</th><th>Monto</th><th>Método</th><th>Estado</th><th>Fecha</th>';
        data.forEach(d => bHtml += `<tr><td>#${d.id}</td><td><a href="#">#${d.orden_id}</a></td><td>${d.cliente}</td><td>${d.referencia}</td><td>${d.monto} ${d.moneda}</td><td>${d.metodo}</td><td><span class="badge-status badge-${d.estado === 'aprobado' ? 'active' : d.estado === 'pendiente' ? 'pending' : 'inactive'}">${d.estado}</span></td><td>${formatDate(d.fecha)}</td></tr>`);
    } else if (type === 'inventory') {
        hHtml += '<th>ID</th><th>Producto</th><th>Código</th><th>Motivo</th><th>Tipo</th><th>Cantidad</th><th>Fecha</th>';
        data.forEach(d => bHtml += `<tr><td>#${d.id}</td><td>${d.producto}</td><td><small class="text-muted">${d.codigo}</small></td><td>${d.motivo}</td><td><span class="badge-status ${d.tipo === 'entrada' ? 'badge-active' : 'badge-inactive'}">${d.tipo}</span></td><td>${d.cantidad}</td><td>${formatDate(d.fecha)}</td></tr>`);
    } else if (type === 'mechanics') {
        hHtml += '<th>Mecánico</th><th>Servicios Asignados</th><th>Completados</th><th>Performance</th><th>Ingreso Generado</th>';
        data.forEach(d => {
            const perf = d.total_asignados > 0 ? Math.round((d.total_completados / d.total_asignados) * 100) : 0;
            const perfColor = perf > 80 ? 'success' : perf > 50 ? 'warning' : 'danger';
            bHtml += `<tr><td><strong>${d.mecanico_nombre}</strong></td><td>${d.total_asignados}</td><td>${d.total_completados}</td><td><div class="progress" style="height:6px;width:80px;display:inline-flex;align-items:center;margin-right:8px;"><div class="progress-bar bg-${perfColor}" style="width:${perf}%"></div></div><small>${perf}%</small></td><td>$${formatCurrency(d.ingreso_generado)}</td></tr>`;
        });
    } else if (type === 'bitacora') {
        hHtml += '<th>ID</th><th>Fecha</th><th>Usuario</th><th>Módulo</th><th>Acción</th><th>Descripción</th><th>IP</th>';
        data.forEach(d => bHtml += `<tr><td>${d.id}</td><td>${formatDate(d.fecha)}</td><td>${d.usuario}</td><td><span class="badge-status badge-info">${d.modulo}</span></td><td><strong>${d.accion}</strong></td><td>${d.descripcion}</td><td><small class="text-muted">${d.ip}</small></td></tr>`);
    }
    hHtml += '</tr>';

    head.innerHTML = hHtml;
    body.innerHTML = bHtml;
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
