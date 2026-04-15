let scannerUser = null;
let scannerInstance = null;
let scannerRunning = false;
let scanLocked = false;
let promotionsCache = [];

$(document).ready(async function () {
    $('#navbarContainer').load('/components/client_navbar.html', () => checkSession());
    $('#footerContainer').load('/components/client_footer.html');

    try {
        const sessionRes = await fetch('/auth/session', { credentials: 'same-origin' });
        const sessionData = await sessionRes.json();
        if (sessionData.status !== 'success') {
            window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname + window.location.search);
            return;
        }

        scannerUser = sessionData.user;
        const badge = document.getElementById('scannerUserType');
        if (badge) {
            badge.textContent = scannerUser.tipo === 'cliente' ? 'Sesion cliente' : 'Sesion empleado';
        }

        bindScannerEvents();

        if (isEmployee()) {
            document.getElementById('employeeTools').style.display = '';
            await loadPromotions();
            await loadTableQrs();
        }

        const autoQr = new URLSearchParams(window.location.search).get('qr');
        if (autoQr && /^\d+$/.test(autoQr)) {
            const raw = `${window.location.origin}/scanner?qr=${autoQr}`;
            document.getElementById('qrInput').value = raw;
            await processScan(raw);
        }
    } catch (e) {
        showToast('No se pudo iniciar el modulo escaner', 'error');
    }
});

function isEmployee() {
    return scannerUser && (scannerUser.tipo === 'empleado' || scannerUser.tipo === 'admin');
}

function bindScannerEvents() {
    document.getElementById('btnProcessQr')?.addEventListener('click', () => processScan());
    document.getElementById('qrInput')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            processScan();
        }
    });

    document.getElementById('btnStartCamera')?.addEventListener('click', startCamera);
    document.getElementById('btnStopCamera')?.addEventListener('click', stopCamera);

    document.getElementById('btnCreateMesaQr')?.addEventListener('click', createMesaQr);

    $('#tableQrList').on('change', '.action-select', function () {
        const qrId = this.getAttribute('data-id');
        const action = this.value;
        const promoSelect = document.querySelector(`.promo-select[data-id="${qrId}"]`);
        if (!promoSelect) return;
        promoSelect.style.display = action === 'promocion' ? '' : 'none';
    });

    $('#tableQrList').on('click', '.btn-save-action', async function () {
        const qrId = this.getAttribute('data-id');
        const actionSelect = document.querySelector(`.action-select[data-id="${qrId}"]`);
        const promoSelect = document.querySelector(`.promo-select[data-id="${qrId}"]`);
        if (!actionSelect) return;

        const action = actionSelect.value;
        const promoId = promoSelect ? promoSelect.value : '';

        const payload = {
            accion: action,
            promocion_id: action === 'promocion' ? promoId : null
        };

        try {
            const res = await fetch(`/api/scanner/table-qrs/${qrId}/action`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!res.ok || data.status === 'error') {
                showToast(data.message || 'No se pudo actualizar la accion', 'error');
                return;
            }
            showToast(data.message || 'Accion actualizada', 'success');
            await loadTableQrs();
        } catch (e) {
            showToast('Error de conexion al actualizar accion', 'error');
        }
    });
}

async function processScan(rawOverride = null) {
    if (scanLocked) return;
    const raw = (rawOverride || document.getElementById('qrInput')?.value || '').trim();
    if (!raw) {
        showToast('Ingrese o escanee un QR', 'warning');
        return;
    }

    scanLocked = true;

    try {
        const res = await fetch('/api/scanner/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ raw })
        });
        const data = await res.json();

        if (!res.ok || data.status === 'error') {
            showToast(data.message || 'No se pudo procesar el QR', 'error');
            return;
        }

        renderScanResult(data.data || {});
        showToast(data.message || 'QR procesado', 'success');
    } catch (e) {
        showToast('Error de conexion al procesar QR', 'error');
    } finally {
        scanLocked = false;
    }
}

function renderScanResult(data) {
    const card = document.getElementById('scanResultCard');
    const body = document.getElementById('scanResultBody');
    if (!card || !body) return;

    card.style.display = '';

    if (data.mode === 'factura_validada') {
        body.innerHTML = renderOrderBlock(data.order, 'Factura validada correctamente');
        return;
    }

    if (data.mode === 'factura_cliente') {
        body.innerHTML = renderOrderBlock(data.order, 'Factura del cliente cargada');
        return;
    }

    if (data.mode === 'mesa_promocion_aplicada') {
        const cardData = data.card || {};
        body.innerHTML = `
            <div class="alert alert-success mb-3">${escapeHtml(data.message || 'Promocion aplicada')}</div>
            <div><strong>Mesa:</strong> ${escapeHtml(data.codigo_mesa || '-')}</div>
            <div><strong>Tarjeta:</strong> #${cardData.id || '-'}</div>
            <div><strong>Promocion:</strong> ${escapeHtml(cardData.promo_nombre || '-')}</div>
            <div><strong>Puntos:</strong> ${cardData.puntos_acumulados || 0} / ${cardData.puntos_requeridos || '-'}</div>
            <div><strong>Recompensa:</strong> ${escapeHtml(cardData.recompensa || '-')}</div>
        `;
        return;
    }

    if (data.mode === 'promocion_info') {
        const promo = data.promocion || {};
        body.innerHTML = `
            <div class="alert alert-info mb-3">${escapeHtml(data.message || 'Promocion disponible')}</div>
            <div><strong>Promocion:</strong> ${escapeHtml(promo.nombre || '-')}</div>
            <div><strong>Puntos requeridos:</strong> ${promo.puntos_requeridos || '-'}</div>
            <div><strong>Recompensa:</strong> ${escapeHtml(promo.recompensa || '-')}</div>
        `;
        return;
    }

    if (data.mode === 'promocion_directa_aplicada') {
        const cardData = data.card || {};
        body.innerHTML = `
            <div class="alert alert-success mb-3">${escapeHtml(data.message || 'Promocion aplicada')}</div>
            <div><strong>Tarjeta:</strong> #${cardData.id || '-'}</div>
            <div><strong>Promocion:</strong> ${escapeHtml(cardData.promo_nombre || '-')}</div>
            <div><strong>Puntos:</strong> ${cardData.puntos_acumulados || 0} / ${cardData.puntos_requeridos || '-'}</div>
        `;
        return;
    }

    if (data.mode === 'mesa_validar_pago') {
        const header = `<div class="alert alert-info mb-3">${escapeHtml(data.message || 'Validacion de pago')}</div><div><strong>Mesa:</strong> ${escapeHtml(data.codigo_mesa || '-')}</div>`;
        if (!data.order) {
            body.innerHTML = `${header}<div class="mt-2 text-muted">No se encontro factura reciente para este cliente.</div>`;
            return;
        }
        body.innerHTML = `${header}${renderOrderBlock(data.order, 'Ultima factura del cliente')}`;
        return;
    }

    if (data.mode === 'mesa_info') {
        body.innerHTML = `
            <div class="alert alert-secondary mb-3">${escapeHtml(data.message || 'QR de mesa')}</div>
            <div><strong>Mesa:</strong> ${escapeHtml(data.codigo_mesa || '-')}</div>
            <div><strong>Accion:</strong> ${escapeHtml(data.accion || 'sin_accion')}</div>
            <div><strong>Promocion ID:</strong> ${data.promocion_id || '-'}</div>
        `;
        return;
    }

    if (data.mode === 'mesa_sin_accion' || data.mode === 'factura_restringida' || data.mode === 'factura_invalida' || data.mode === 'qr_sin_utilidad') {
        body.innerHTML = `<div class="alert alert-warning mb-0">${escapeHtml(data.message || 'Sin accion configurada')}</div>`;
        return;
    }

    body.innerHTML = `<pre class="scanner-result-pre">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
}

function renderOrderBlock(order, title) {
    if (!order) {
        return `<div class="alert alert-warning">No se encontro informacion de factura.</div>`;
    }

    const cliente = order.cliente || {};
    const detailsRows = (order.detalles || []).map(d => `
        <tr>
            <td>${escapeHtml(d.item_nombre || '-')}</td>
            <td>${d.cantidad || 0}</td>
            <td>$${formatMoney(d.precio_unitario || d.precio || 0)}</td>
            <td>$${formatMoney(d.subtotal || 0)}</td>
        </tr>
    `).join('');

    const employeeTools = isEmployee() ? `<div class="mt-2"><a href="/admin/service_mechanics" class="btn btn-sm btn-outline-orange"><i class="bi bi-tools me-1"></i>Ir a Servicio Mecanico</a></div>` : '';

    return `
        <div class="mb-3">
            <h6 class="fw-bold mb-2">${escapeHtml(title || 'Factura')}</h6>
            <div><strong>Factura:</strong> #${order.id || '-'}</div>
            <div><strong>Estado:</strong> ${escapeHtml(order.estado || '-')}</div>
            <div><strong>Fecha:</strong> ${formatDate(order.fecha)}</div>
            <div><strong>Cliente:</strong> ${escapeHtml((cliente.nombre || '') + ' ' + (cliente.apellido || ''))} (${escapeHtml(order.cliente_cedula || '')})</div>
            <div><strong>Correo:</strong> ${escapeHtml(cliente.email || '-')}</div>
            <div><strong>Total:</strong> $${formatMoney(order.total || 0)}</div>
            ${employeeTools}
        </div>
        <div class="table-responsive">
            <table class="table table-sm mb-0">
                <thead>
                    <tr><th>Item</th><th>Cantidad</th><th>Precio</th><th>Subtotal</th></tr>
                </thead>
                <tbody>
                    ${detailsRows || '<tr><td colspan="4" class="text-muted">Sin detalles</td></tr>'}
                </tbody>
            </table>
        </div>
    `;
}

async function startCamera() {
    if (scannerRunning) return;
    if (typeof Html5Qrcode === 'undefined') {
        showToast('La camara no esta disponible en este navegador', 'warning');
        return;
    }

    const reader = document.getElementById('qrReader');
    if (!reader) return;

    try {
        scannerInstance = new Html5Qrcode('qrReader');
        await scannerInstance.start(
            { facingMode: 'environment' },
            { fps: 10, qrbox: { width: 220, height: 220 } },
            async (decodedText) => {
                if (!decodedText || scanLocked) return;
                await stopCamera();
                document.getElementById('qrInput').value = decodedText;
                await processScan(decodedText);
            },
            () => { }
        );

        scannerRunning = true;
        document.getElementById('btnStartCamera').disabled = true;
        document.getElementById('btnStopCamera').disabled = false;
    } catch (e) {
        showToast('No se pudo iniciar la camara', 'error');
    }
}

async function stopCamera() {
    if (!scannerRunning || !scannerInstance) return;

    try {
        await scannerInstance.stop();
        await scannerInstance.clear();
    } catch (e) {
    }

    scannerRunning = false;
    document.getElementById('btnStartCamera').disabled = false;
    document.getElementById('btnStopCamera').disabled = true;
}

async function loadPromotions() {
    try {
        const res = await fetch('/api/scanner/promotions', { credentials: 'same-origin' });
        const data = await res.json();
        if (!res.ok || data.status === 'error') {
            promotionsCache = [];
            return;
        }
        promotionsCache = data.data || [];
    } catch (e) {
        promotionsCache = [];
    }
}

async function loadTableQrs() {
    if (!isEmployee()) return;

    try {
        const res = await fetch('/api/scanner/table-qrs', { credentials: 'same-origin' });
        const data = await res.json();

        if (!res.ok || data.status === 'error') {
            showToast(data.message || 'No se pudo cargar los QR de mesa', 'error');
            return;
        }

        renderTableQrs(data.data || []);
    } catch (e) {
        showToast('Error al cargar QR de mesas', 'error');
    }
}

function renderTableQrs(items) {
    const container = document.getElementById('tableQrList');
    if (!container) return;

    if (!items.length) {
        container.innerHTML = '<div class="text-muted">No hay QR de mesa registrados.</div>';
        return;
    }

    const html = items.map(item => {
        const action = item.accion || 'sin_accion';
        const promoSelectStyle = action === 'promocion' ? '' : 'display:none;';

        return `
            <div class="border rounded p-3 mb-3">
                <div class="d-flex gap-3 align-items-start mb-2">
                    <img class="scanner-mini-qr" src="/api/qr/${item.id}/image?t=${Date.now()}" alt="QR mesa">
                    <div class="flex-grow-1">
                        <div><strong>${escapeHtml(item.codigo_mesa || '-')}</strong></div>
                        <small class="text-muted d-block mb-2">QR #${item.id}</small>
                        <select class="form-select form-select-sm action-select" data-id="${item.id}">
                            <option value="sin_accion" ${action === 'sin_accion' ? 'selected' : ''}>Sin accion</option>
                            <option value="promocion" ${action === 'promocion' ? 'selected' : ''}>Asignar promocion</option>
                            <option value="validar_pago" ${action === 'validar_pago' ? 'selected' : ''}>Validar pago</option>
                        </select>
                        <select class="form-select form-select-sm mt-2 promo-select" data-id="${item.id}" style="${promoSelectStyle}">
                            <option value="">Seleccione promocion</option>
                            ${buildPromotionOptions(item.promocion_id)}
                        </select>
                        <button class="btn btn-sm btn-orange mt-2 btn-save-action" data-id="${item.id}">Guardar accion</button>
                        <a class="btn btn-sm btn-outline-orange mt-2 ms-2" href="/scanner?qr=${item.id}" target="_blank">Abrir QR</a>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

function buildPromotionOptions(selectedId) {
    return promotionsCache.map(p => {
        const selected = Number(selectedId) === Number(p.id) ? 'selected' : '';
        return `<option value="${p.id}" ${selected}>${escapeHtml(p.nombre)}</option>`;
    }).join('');
}

async function createMesaQr() {
    if (!isEmployee()) return;

    const codeInput = document.getElementById('mesaCodeInput');
    const codigo = (codeInput?.value || '').trim();
    if (!codigo) {
        showToast('Ingrese el codigo de mesa', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/scanner/table-qrs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ codigo_mesa: codigo })
        });
        const data = await res.json();
        if (!res.ok || data.status === 'error') {
            showToast(data.message || 'No se pudo crear el QR de mesa', 'error');
            return;
        }

        showToast(data.message || 'QR de mesa generado', 'success');
        codeInput.value = '';
        await loadTableQrs();
    } catch (e) {
        showToast('Error de conexion al crear QR de mesa', 'error');
    }
}

function formatMoney(value) {
    return parseFloat(value || 0).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(value) {
    if (!value) return '-';
    return new Date(value).toLocaleString('es-VE');
}

function escapeHtml(text) {
    const val = String(text || '');
    return val
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
