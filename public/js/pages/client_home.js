$(document).ready(function () {
            $('#navbarContainer').load('/components/client_navbar.html', () => checkSession());
            $('#footerContainer').load('/components/client_footer.html');
            loadHome();
        });

        async function loadHome() {
            try {
                const res = await fetch('/api/categories/active').then(r => r.json());
                const el = document.getElementById('categoriesList');
                (res.data || []).slice(0, 6).forEach(c => {
                    el.innerHTML += `<div class="col-6 col-md-4 col-lg-2"><a href="/client/catalog?category=${encodeURIComponent(c.nombre)}" class="text-decoration-none"><div class="category-card"><i class="bi bi-tag-fill"></i><p>${escapeHtml(c.nombre)}</p></div></a></div>`;
                });
            } catch (e) { }

            try {
                const res = await fetch('/api/products/active?page=1&per_page=8').then(r => r.json());
                const el = document.getElementById('featuredProducts');
                (res.data || []).slice(0, 8).forEach(p => {
                    const safeName = escapeHtml(p.nombre || '');
                    const safeCategory = escapeHtml(p.categoria_nombre || p.categoria || '');
                    const safeBranch = escapeHtml(p.sucursal_nombre || '');
                    const cartCode = encodeURIComponent(String(p.codigo || ''));
                    const img = buildProductImageHtml(p, p.nombre || 'Producto');
                    el.innerHTML += `<div class="col-6 col-md-4 col-lg-3"><div class="product-card">
                <div class="product-img">${img}</div>
                <div class="product-info">
                    <div class="product-category">${safeCategory}</div>
                    <div class="product-name">${safeName}</div>
                <div class="product-price" data-usd-price="${p.precio}">${formatUsdBs(p.precio)}</div>
                    ${safeBranch ? `<div class="product-branch"><i class="bi bi-geo-alt"></i>${safeBranch}</div>` : ''}
                </div>
                <button class="btn-add-cart" onclick="addToCart(decodeURIComponent('${cartCode}'))"><i class="bi bi-cart-plus me-1"></i>Agregar al Carrito</button>
            </div></div>`;
                });
                if (!res.data?.length) el.innerHTML = '<div class="col-12"><div class="empty-state"><i class="bi bi-box-seam"></i><p>Proximamente productos disponibles</p></div></div>';
                hydrateDualPrices(el);
            } catch (e) { }

            try {
                const res = await fetch('/api/services/active').then(r => r.json());
                const el = document.getElementById('servicesList');
                const icons = { alineacion: 'bi-rulers', rotacion: 'bi-arrow-repeat', balanceo: 'bi-speedometer', cambio_aceite: 'bi-droplet-fill', general: 'bi-wrench-adjustable' };
                (res.data || []).slice(0, 6).forEach(s => {
                    el.innerHTML += `<div class="col-6 col-md-4 col-lg-3"><div class="service-card" onclick="addToCart(${s.id},'servicio')">
                <i class="bi ${icons[s.tipo] || 'bi-wrench'}"></i>
                <h6 class="fw-bold mt-2 mb-1">${s.nombre}</h6>
                <p class="text-muted mb-1" style="font-size:0.75rem;">${s.descripcion?.substring(0, 60) || ''}</p>
                <span class="service-price" data-usd-price="${s.precio}">${formatUsdBs(s.precio)}</span>
                ${s.sucursal_nombre ? `<small class="d-block text-muted mt-1"><i class="bi bi-geo-alt"></i> ${s.sucursal_nombre}</small>` : ''}
                <button type="button" class="btn btn-orange btn-sm w-100 mt-2" style="grid-column:1 / -1;" onclick="event.stopPropagation(); addToCart(${s.id},'servicio')"><i class="bi bi-cart-plus me-1"></i>Solicitar</button>
            </div></div>`;
                });
            } catch (e) { }

            try {
                const res = await fetch('/api/sucursales/active').then(r => r.json());
                const el = document.getElementById('branchesList');
                (res.data || []).forEach(s => {
                    el.innerHTML += `<div class="col-md-4"><div class="branch-card">
                <h6 class="fw-bold mb-1"><i class="bi bi-building me-2" style="color:var(--primary);"></i>${s.nombre}</h6>
                <p class="text-muted mb-0" style="font-size:0.8rem;"><i class="bi bi-geo-alt me-1"></i>${s.direccion || ''}</p>
                ${s.telefono ? `<p class="text-muted mb-0" style="font-size:0.8rem;"><i class="bi bi-telephone me-1"></i>${s.telefono}</p>` : ''}
            </div></div>`;
                });
            } catch (e) { }
        }
