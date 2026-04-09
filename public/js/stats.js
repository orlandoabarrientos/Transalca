let charts = {};

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="report_stats"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    
    Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
    Chart.defaults.color = "#64748b";
    
    initCharts();
    
    loadStats();
});

function initCharts() {
    const revCtx = document.getElementById('revenueChart').getContext('2d');
    const gradient = revCtx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(26, 54, 93, 0.4)');
    gradient.addColorStop(1, 'rgba(26, 54, 93, 0.0)');
    
    charts.revenue = new Chart(revCtx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Ventas ($)', data: [], borderColor: '#1A365D', backgroundColor: gradient, borderWidth: 3, pointBackgroundColor: '#E77817', pointBorderColor: '#fff', pointHoverBackgroundColor: '#fff', pointHoverBorderColor: '#E77817', pointRadius: 4, pointHoverRadius: 6, fill: true, tension: 0.4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', padding: 12, titleFont: { size: 14 }, bodyFont: { size: 14, weight: 'bold' } } }, scales: { y: { beginAtZero: true, grid: { borderDash: [4, 4], color: '#e2e8f0' }, ticks: { callback: v => '$'+v } }, x: { grid: { display: false } } } }
    });

    const statusCtx = document.getElementById('statusChart').getContext('2d');
    charts.status = new Chart(statusCtx, {
        type: 'doughnut',
        data: { labels: [], datasets: [{ data: [], backgroundColor: ['#E77817', '#10B981', '#F59E0B', '#EF4444', '#64748b'], borderWidth: 0, hoverOffset: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } } } }
    });
    
    const prodCtx = document.getElementById('productsChart').getContext('2d');
    charts.products = new Chart(prodCtx, {
        type: 'bar',
        data: { labels: [], datasets: [{ label: 'Unidades Vendidas', data: [], backgroundColor: '#10B981', borderRadius: 6, barThickness: 24 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { borderDash: [4, 4] } }, x: { grid: { display: false } } } }
    });

    const payCtx = document.getElementById('paymentsChart').getContext('2d');
    charts.payments = new Chart(payCtx, {
        type: 'bar',
        data: { labels: [], datasets: [{ label: 'Transacciones', data: [], backgroundColor: '#6366F1', borderRadius: 6, barThickness: 24 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, grid: { borderDash: [4, 4] } }, y: { grid: { display: false } } } }
    });
}

function loadStats() {
    const days = document.getElementById('timelineFilter').value;
    
    apiCall(`/api/stats/revenue?days=${days}`).then(res => {
        if(res.data) {
            charts.revenue.data.labels = res.data.labels;
            charts.revenue.data.datasets[0].data = res.data.data;
            charts.revenue.update();
        }
    });
    
    apiCall(`/api/stats/status`).then(res => {
        if(res.data) {
            charts.status.data.labels = res.data.labels;
            charts.status.data.datasets[0].data = res.data.data;
            charts.status.update();
        }
    });
    
    apiCall(`/api/stats/products`).then(res => {
        if(res.data) {
            charts.products.data.labels = res.data.labels;
            charts.products.data.datasets[0].data = res.data.data;
            charts.products.update();
        }
    });

    apiCall(`/api/stats/payments`).then(res => {
        if(res.data) {
            charts.payments.data.labels = res.data.labels;
            charts.payments.data.datasets[0].data = res.data.data;
            charts.payments.update();
        }
    });
}
