let allServices = [];
        let catalogFilterTimer = null;
        let catalogProductRequest = 0;
        const catalogProductsPerPage = 30;

        $(document).ready(function () {
            $('#navbarContainer').load('/components/client_navbar.html', () => checkSession());
            $('#footerContainer').load('/components/client_footer.html');
            loadCatalog();
        });

        async function loadCatalog() {
            const params = new URLSearchParams(window.location.search);
            try {
                const cats = await fetch('/api/categories/active').then(r => r.json());
                const sel = document.getElementById('filterCategory');
                (cats.data || []).forEach(c => sel.innerHTML += `<option value="${c.nombre}">${c.nombre}</option>`);
                applyInitialCatalogCategory(params.get('category'));
            } catch (e) { }
            try {
                const branches = await fetch('/api/sucursales/active').then(r => r.json());
                const sel = document.getElementById('filterBranch');
                const chips = document.getElementById('sucursalChips');
                chips.innerHTML = '<button type="button" class="sucursal-chip active" data-branch-id="" onclick="selectBranch(this,\'\')"><i class="bi bi-grid"></i>Todas</button>';
                (branches.data || []).forEach(b => {
                    sel.innerHTML += `<option value="${b.id}">${b.nombre}</option>`;
                    chips.innerHTML += `<button type="button" class="sucursal-chip" data-branch-id="${b.id}" onclick="selectBranch(this,'${b.id}')"><i class="bi bi-geo-alt"></i>${b.nombre}</button>`;
                });
            } catch (e) { }

            loadProducts(1);

            try {
                const res = await fetch('/api/services/active').then(r => r.json());
                allServices = res.data || [];
                filterServices();
            } catch (e) { }
        }

        function applyInitialCatalogCategory(requestedCategory) {
            const sel = document.getElementById('filterCategory');
            if (!sel) return;
            const options = Array.from(sel.options);
            if (requestedCategory && options.some(o => o.value === requestedCategory)) {
                sel.value = requestedCategory;
            }
        }

        function selectBranch(el, branchId) {
            document.querySelectorAll('.sucursal-chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('filterBranch').value = branchId;
            filterProducts();
        }

        function syncBranchChip(branchId) {
            document.querySelectorAll('.sucursal-chip').forEach(c => {
                c.classList.toggle('active', String(c.dataset.branchId || '') === String(branchId || ''));
            });
        }

        function clearCatalogFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('filterCategory').value = '';
            document.getElementById('filterBranch').value = '';
            document.getElementById('filterSort').value = '';
            syncBranchChip('');
            filterProducts();
        }

        function getCatalogFilters() {
            return {
                q: document.getElementById('searchInput').value.trim(),
                cat: document.getElementById('filterCategory').value,
                branch: document.getElementById('filterBranch').value,
                sort: document.getElementById('filterSort').value
            };
        }

        function filterProducts(page = 1) {
            clearTimeout(catalogFilterTimer);
            catalogFilterTimer = setTimeout(() => {
                loadProducts(page);
                filterServices();
            }, page === 1 ? 180 : 0);
        }

        async function loadProducts(page = 1) {
            const requestId = ++catalogProductRequest;
            const { q, cat, branch, sort } = getCatalogFilters();
            syncBranchChip(branch);

            const params = new URLSearchParams({
                page: String(page),
                per_page: String(catalogProductsPerPage)
            });
            if (q) params.set('q', q);
            if (cat) params.set('category', cat);
            if (branch) params.set('branch', branch);
            if (sort) params.set('sort', sort);

            renderProductLoading();
            try {
                const res = await fetch(`/api/products/active?${params.toString()}`).then(r => r.json());
                if (requestId !== catalogProductRequest) return;
                const data = res.data || [];
                renderProducts(data, res.total ?? data.length, res.page || page, res.pages || 0);
            } catch (e) {
                if (requestId !== catalogProductRequest) return;
                document.getElementById('productGrid').innerHTML = '<div class="col-12"><div class="empty-state"><i class="bi bi-wifi-off"></i><p>No se pudieron cargar los productos</p></div></div>';
                renderCatalogPagination(0, 1, 0);
            }
        }

        function filterServices() {
            const { q, branch } = getCatalogFilters();
            const normalizedQ = q.toLowerCase();
            let filteredS = allServices.filter(s => {
                if (normalizedQ && !(s.nombre || '').toLowerCase().includes(normalizedQ)) return false;
                if (branch && s.sucursal_id && s.sucursal_id != branch) return false;
                return true;
            });
            renderServices(filteredS);
        }

        function renderProductLoading() {
            const grid = document.getElementById('productGrid');
            grid.innerHTML = Array.from({ length: 8 }).map(() => `<div class="col-6 col-md-4 col-lg-3">
                <article class="product-card catalog-product-card catalog-product-skeleton">
                    <div class="product-img"></div>
                    <div class="product-info">
                        <span></span>
                        <strong></strong>
                        <em></em>
                    </div>
                </article>
            </div>`).join('');
        }

        function renderProducts(products, total = products.length, page = 1, pages = 0) {
            const grid = document.getElementById('productGrid');
            const count = document.getElementById('productCount');
            if (count) count.textContent = `${total} producto${total === 1 ? '' : 's'}`;
            grid.innerHTML = '';
            products.forEach(p => {
                const safeName = escapeHtml(p.nombre || '');
                const safeCode = escapeHtml(p.codigo || '');
                const safeCategory = escapeHtml(p.categoria_nombre || p.categoria || 'Producto');
                const safeBranch = escapeHtml(p.sucursal_nombre || '');
                const cartCode = encodeURIComponent(String(p.codigo || ''));
                const img = buildProductImageHtml(p, p.nombre || 'Producto');
                grid.innerHTML += `<div class="col-6 col-md-4 col-lg-3 fade-in-up">
                    <article class="product-card catalog-product-card">
                        <div class="product-img">
                            <span class="catalog-product-badge"><i class="bi bi-box-seam"></i>${safeCategory}</span>
                            ${img}
                        </div>
                        <div class="product-info">
                            <div class="product-meta-row">
                                <span>${safeCategory}</span>
                                ${safeCode ? `<small>#${safeCode}</small>` : ''}
                            </div>
                            <div class="product-name">${safeName}</div>
                            <div class="product-price-row">
                                <span class="product-price" data-usd-price="${p.precio}">${formatUsdBs(p.precio)}</span>
                                <span class="product-stock"><i class="bi bi-check2-circle"></i>Disponible</span>
                            </div>
                            ${safeBranch ? `<div class="product-branch"><i class="bi bi-geo-alt"></i>${safeBranch}</div>` : ''}
                        </div>
                        <button class="btn-add-cart" onclick="addToCart(decodeURIComponent('${cartCode}'))"><i class="bi bi-cart-plus me-1"></i>Agregar al carrito</button>
                    </article>
                </div>`;
            });
            if (!products.length) grid.innerHTML = '<div class="col-12"><div class="empty-state"><i class="bi bi-search"></i><p>No se encontraron productos</p></div></div>';
            renderCatalogPagination(total, page, pages);
            hydrateDualPrices(grid);
        }

        function catalogGoToPage(page) {
            filterProducts(page);
            document.getElementById('tabProducts')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function renderCatalogPagination(total, page, pages) {
            const info = document.getElementById('catalogPaginationInfo');
            const controls = document.getElementById('catalogPaginationControls');
            if (info) {
                const start = total ? (page - 1) * catalogProductsPerPage + 1 : 0;
                const end = Math.min(page * catalogProductsPerPage, total);
                info.textContent = total ? `Mostrando ${start} a ${end} de ${total} productos` : 'Mostrando 0 productos';
            }
            if (!controls) return;
            controls.innerHTML = '';
            if (pages <= 1) return;

            const prevLi = document.createElement('li');
            prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
            prevLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page > 1}) catalogGoToPage(${page - 1})"><i class="bi bi-chevron-left"></i></a>`;
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
                firstLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); catalogGoToPage(1)">1</a>`;
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
                li.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); catalogGoToPage(${i})">${i}</a>`;
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
                lastLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); catalogGoToPage(${pages})">${pages}</a>`;
                controls.appendChild(lastLi);
            }

            const nextLi = document.createElement('li');
            nextLi.className = `page-item ${page === pages ? 'disabled' : ''}`;
            nextLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); if(${page < pages}) catalogGoToPage(${page + 1})"><i class="bi bi-chevron-right"></i></a>`;
            controls.appendChild(nextLi);
        }

        function renderServices(services) {
            const grid = document.getElementById('serviceGrid');
            const count = document.getElementById('serviceCount');
            if (count) count.textContent = `${services.length} servicio${services.length === 1 ? '' : 's'}`;
            grid.innerHTML = '';
            const icons = { alineacion: 'bi-rulers', rotacion: 'bi-arrow-repeat', balanceo: 'bi-speedometer', cambio_aceite: 'bi-droplet-fill', frenos: 'bi-disc', general: 'bi-wrench-adjustable' };
            const tipoLabels = { alineacion: 'Alineacion', rotacion: 'Rotacion', balanceo: 'Balanceo', cambio_aceite: 'Cambio de aceite', frenos: 'Frenos', general: 'Servicio general' };
            services.forEach(s => {
                const safeName = escapeHtml(s.nombre || '');
                const safeDesc = escapeHtml(s.descripcion || 'Servicio profesional realizado por nuestros mecanicos certificados.');
                const safeBranch = escapeHtml(s.sucursal_nombre || 'Todas las sucursales');
                const tipoLabel = escapeHtml(tipoLabels[s.tipo] || (s.tipo || 'Servicio').replace(/_/g, ' '));
                const duracion = s.duracion_estimada ? escapeHtml(String(s.duracion_estimada)) : null;
                grid.innerHTML += `<div class="col-12 col-md-6 col-xl-4 fade-in-up">
                    <article class="service-pro-card h-100">
                        <header class="service-pro-head">
                            <div class="service-pro-icon"><i class="bi ${icons[s.tipo] || 'bi-wrench-adjustable'}"></i></div>
                            <div>
                                <span class="service-pro-type">${tipoLabel}</span>
                                <h6 class="service-pro-title">${safeName}</h6>
                            </div>
                            <span class="service-pro-status"><i class="bi bi-check-circle-fill me-1"></i>Disponible</span>
                        </header>
                        <p class="service-pro-desc">${safeDesc}</p>
                        <ul class="service-pro-meta">
                            ${duracion ? `<li><i class="bi bi-clock"></i> Duracion aprox.: ${duracion} min</li>` : ''}
                            <li><i class="bi bi-geo-alt"></i> ${safeBranch}</li>
                            <li><i class="bi bi-shield-check"></i> Garantia de servicio Transalca</li>
                        </ul>
                        <footer class="service-pro-footer">
                            <div class="service-pro-price">
                                <small>Precio</small>
                                <strong class="service-price" data-usd-price="${s.precio}">${formatUsdBs(s.precio)}</strong>
                            </div>
                            <button type="button" class="btn btn-orange service-pro-cta" onclick="addToCart(${s.id},'servicio')">
                                <i class="bi bi-cart-plus me-1"></i>Solicitar
                            </button>
                        </footer>
                    </article>
                </div>`;
            });
            if (!services.length) grid.innerHTML = '<div class="col-12"><div class="empty-state"><i class="bi bi-wrench"></i><p>No se encontraron servicios</p></div></div>';
        }
