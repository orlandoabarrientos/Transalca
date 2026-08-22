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
    return scannerUser && ['empleado', 'admin', 'vendedor', 'mecanico', 'soporte'].includes(scannerUser.tipo);
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
            body: JSON.stringify({ raw, source: 'client' })
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
    if (data.mode === 'promocion_directa_aplicada') {
        const cardData = data.card || {};
        const promoName = cardData.promo_nombre || 'Promoción';
        window.location.href = `/client/my_loyalty?promo_registered=1&promo_name=${encodeURIComponent(promoName)}`;
        return;
    }

    if (data.mode === 'validar_pago_redirect') {
        window.location.href = `/client/my_orders?validar_pago_qr=${data.qr_id}`;
        return;
    }

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

    if (data.mode === 'factura_restringida' || data.mode === 'factura_invalida' || data.mode === 'qr_sin_utilidad') {
        body.innerHTML = `<div class="alert alert-warning mb-0">${escapeHtml(data.message || 'Sin accion configurada')}</div>`;
        return;
    }

    body.innerHTML = `<pre class="scanner-result-pre">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
}

function renderOrderBlock(order, title) {
    if (!order) {
        return `<div class="alert alert-warning">No se encontro informacion de factura.</div>`;
    }

    const orderCurrency = (order.moneda || 'usd').toLowerCase();
    const symbol = orderCurrency === 'bs' ? 'Bs. ' : '$';

    const cliente = order.cliente || {};
    const detailsRows = (order.detalles || []).map(d => `
        <tr>
            <td>${escapeHtml(d.item_nombre || '-')}</td>
            <td>${d.cantidad || 0}</td>
            <td>${symbol}${formatMoney(d.precio_unitario || d.precio || 0)}</td>
            <td>${symbol}${formatMoney(d.subtotal || 0)}</td>
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
            <div><strong>Total:</strong> ${symbol}${formatMoney(order.total || 0)}</div>
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
