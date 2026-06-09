let charts = {};
let chartDataCache = {};
const chartCanvasIds = {
    revenue: 'revenueChart',
    status: 'statusChart',
    products: 'productsChart',
    payments: 'paymentsChart'
};
const chartTypes = ['line', 'bar', 'doughnut', 'pie', 'polarArea'];
const chartTypeLabels = {
    line: 'Línea',
    bar: 'Barras',
    doughnut: 'Dona',
    pie: 'Torta',
    polarArea: 'Polar'
};
const currentChartTypes = {
    revenue: 'line',
    status: 'doughnut',
    products: 'bar',
    payments: 'bar'
};

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="report_stats"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');

    Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
    Chart.defaults.color = "#64748b";

    setupChartTypeControls();
    initCharts();
    loadStats();
});

function setupChartTypeControls() {
    document.querySelectorAll('.chart-type-select').forEach(select => {
        select.innerHTML = chartTypes.map(type => `<option value="${type}">${chartTypeLabels[type]}</option>`).join('');
        const key = select.dataset.chart;
        select.value = currentChartTypes[key] || 'bar';
        if (window.jQuery) {
            window.jQuery(select)
                .off('change.statsChart')
                .on('change.statsChart', function() {
                    changeChartType(key, this.value);
                })
                .trigger('change.select2');
        } else {
            select.onchange = function() {
                changeChartType(key, this.value);
            };
        }
    });
}

function initCharts() {
    charts.revenue = createChart('revenue', currentChartTypes.revenue);
    charts.status = createChart('status', currentChartTypes.status);
    charts.products = createChart('products', currentChartTypes.products);
    charts.payments = createChart('payments', currentChartTypes.payments);
}

function createChart(key, type) {
    destroyChart(key);
    const ctx = document.getElementById(chartCanvasIds[key]).getContext('2d');
    const cached = chartDataCache[key] || { labels: [], data: [] };
    const dataset = buildDataset(key, type, cached.data);
    return new Chart(ctx, {
        type,
        data: { labels: cached.labels, datasets: [dataset] },
        options: buildOptions(key, type)
    });
}

function buildDataset(key, type, data) {
    const palettes = {
        revenue: ['#1A365D', '#E77817', '#10B981', '#6366F1', '#F59E0B'],
        status: ['#E77817', '#10B981', '#F59E0B', '#EF4444', '#64748b'],
        products: ['#10B981', '#34D399', '#059669', '#6366F1', '#E77817'],
        payments: ['#6366F1', '#818CF8', '#10B981', '#E77817', '#F59E0B']
    };
    const colors = palettes[key] || palettes.revenue;
    const circular = ['doughnut', 'pie', 'polarArea'].includes(type);
    return {
        label: key === 'revenue' ? 'Ventas ($)' : key === 'products' ? 'Unidades vendidas' : key === 'payments' ? 'Transacciones' : 'Estados',
        data,
        borderColor: colors[0],
        backgroundColor: circular ? colors : colors[0],
        borderWidth: circular ? 0 : 3,
        borderRadius: type === 'bar' ? 6 : 0,
        fill: key === 'revenue' && type === 'line',
        tension: 0.4
    };
}

function buildOptions(key, type) {
    const circular = ['doughnut', 'pie', 'polarArea'].includes(type);
    if (circular) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } } }
        };
    }
    return {
        indexAxis: key === 'payments' && type === 'bar' ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            y: { beginAtZero: true, grid: { borderDash: [4, 4], color: '#e2e8f0' }, ticks: { callback: v => key === 'revenue' ? `$${v}` : v } },
            x: { beginAtZero: key === 'payments' && type === 'bar', grid: { display: key === 'payments' && type === 'bar' } }
        }
    };
}

function destroyChart(key) {
    const canvas = document.getElementById(chartCanvasIds[key]);
    const existingChart = canvas && typeof Chart.getChart === 'function' ? Chart.getChart(canvas) : charts[key];
    if (existingChart) existingChart.destroy();
    charts[key] = null;
}

function changeChartType(key, type) {
    currentChartTypes[key] = chartTypes.includes(type) ? type : 'bar';
    const select = document.querySelector(`.chart-type-select[data-chart="${key}"]`);
    if (select && select.value !== currentChartTypes[key]) {
        select.value = currentChartTypes[key];
        if (window.jQuery) window.jQuery(select).trigger('change.select2');
    }
    if (charts[key]?.config?.type === currentChartTypes[key]) return;
    charts[key] = createChart(key, currentChartTypes[key]);
}

function updateChart(key, labels, data) {
    chartDataCache[key] = { labels, data };
    if (!charts[key]) charts[key] = createChart(key, currentChartTypes[key]);
    charts[key].data.labels = labels;
    charts[key].data.datasets[0] = buildDataset(key, currentChartTypes[key], data);
    charts[key].options = buildOptions(key, currentChartTypes[key]);
    charts[key].update();
}

function loadStats() {
    const days = document.getElementById('timelineFilter').value;

    apiCall(`/api/stats/revenue?days=${days}`).then(res => {
        if(res.data) updateChart('revenue', res.data.labels, res.data.data);
    });

    apiCall('/api/stats/status').then(res => {
        if(res.data) updateChart('status', res.data.labels, res.data.data);
    });

    apiCall('/api/stats/products').then(res => {
        if(res.data) updateChart('products', res.data.labels, res.data.data);
    });

    apiCall('/api/stats/payments').then(res => {
        if(res.data) updateChart('payments', res.data.labels, res.data.data);
    });
}
