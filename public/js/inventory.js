let currentStockPage = 1;
const stockPerPage = 30;
let stockSearchTimer = null;

$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="inventory"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadSucursales('filterSucursal', true).then(() => {
        enhanceSearchableSelects();
    });
    loadStock();
});

function loadStock(page = 1) {
    currentStockPage = page;
    const tbody = document.getElementById('stockBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="spinner-border text-warning" role="status"></div></td></tr>';
    }

    const params = new URLSearchParams({
        page: String(page),
        per_page: String(stockPerPage)
    });
    const sucursal = document.getElementById('filterSucursal')?.value || '';
    const q = document.getElementById('searchStock')?.value.trim() || '';
    if (sucursal) params.set('sucursal_id', sucursal);
    if (q) params.set('q', q);

    apiCall(`/api/inventory/?${params.toString()}`).then(res => {
        if (!tbody) return;
        tbody.innerHTML = '';
        if (res.status === 'error') {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">No se pudo cargar el stock.</td></tr>';
            renderStockPagination(0, 1, 0, stockPerPage);
            return;
        }

        (res.data || []).forEach(s => {
            const isLow = Number(s.stock || 0) <= Number(s.stock_minimo || 5);
            tbody.innerHTML += `<tr class="fade-in-up ${isLow ? 'table-warning' : ''}">
                <td><strong>${escapeHtml(s.producto_nombre || '')}</strong></td>
                <td>${escapeHtml(s.codigo || '')}</td>
                <td>${escapeHtml(s.sucursal_nombre || 'N/A')}</td>
                <td class="fw-bold">${Number(s.stock || 0)}</td>
                <td>${Number(s.stock_minimo || 5)}</td>
                <td>${isLow ? '<span class="badge-status badge-pending"><i class="bi bi-exclamation-triangle me-1"></i>Bajo</span>' : '<span class="badge-status badge-active">OK</span>'}</td>
            </tr>`;
        });

        if (!res.data?.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="empty-state"><i class="bi bi-archive"></i><p>Sin datos de stock</p></div></td></tr>';
        }

        renderStockPagination(res.total || 0, res.page || page, res.pages || 0, res.per_page || stockPerPage);
    });
}

function scheduleStockSearch() {
    clearTimeout(stockSearchTimer);
    stockSearchTimer = setTimeout(() => loadStock(1), 300);
}

function filterTable() {
    scheduleStockSearch();
}

function renderStockPagination(total, page, pages, perPage) {
    const info = document.getElementById('stockPaginationInfo');
    const controls = document.getElementById('stockPaginationControls');
    if (info) {
        const start = total ? (page - 1) * perPage + 1 : 0;
        const end = Math.min(page * perPage, total);
        info.textContent = `Mostrando ${start} a ${end} de ${total} registros`;
    }
    if (!controls) return;
    controls.innerHTML = '';
    if (pages <= 1) return;

    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page > 1}) loadStock(${page - 1})"><i class="bi bi-chevron-left"></i></a>`;
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
        firstLi.innerHTML = '<a class="page-link" href="#" onclick="event.preventDefault(); loadStock(1)">1</a>';
        controls.appendChild(firstLi);

        if (startPage > 2) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = '<span class="page-link">...</span>';
            controls.appendChild(ellipsisLi);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${page === i ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); loadStock(${i})">${i}</a>`;
        controls.appendChild(li);
    }

    if (endPage < pages) {
        if (endPage < pages - 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = '<span class="page-link">...</span>';
            controls.appendChild(ellipsisLi);
        }
        const lastLi = document.createElement('li');
        lastLi.className = 'page-item';
        lastLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); loadStock(${pages})">${pages}</a>`;
        controls.appendChild(lastLi);
    }

    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${page === pages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page < pages}) loadStock(${page + 1})"><i class="bi bi-chevron-right"></i></a>`;
    controls.appendChild(nextLi);
}
