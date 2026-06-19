$(document).ready(function () {
            $('#navbarContainer').load('/components/client_navbar.html', () => checkSession());
            $('#footerContainer').load('/components/client_footer.html');
            
            loadExchangeRatesCached()
                .then(loadPaymentMethods)
                .then(loadCart);

            $('#metodoPago').on('change', updateSummaryPrices);

            $('#checkoutForm').on('submit', function (e) {
                e.preventDefault();
                var fd = new FormData();
                fd.append('metodo_pago', $('#metodoPago').val());
                if ($('#comprobante')[0].files[0]) fd.append('comprobante', $('#comprobante')[0].files[0]);
                $('#btnCheckout').prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Procesando...');
                $.ajax({
                    url: '/api/orders/checkout', type: 'POST', data: fd, processData: false, contentType: false,
                    success: function (r) {
                        Swal.fire({ icon: 'success', title: '¡Pedido realizado!', html: '<p>Tu orden <strong>#' + r.id + '</strong> ha sido creada.</p><p>Revisaremos tu comprobante de pago y te notificaremos por correo.</p>', confirmButtonColor: '#e94560' }).then(function () { window.location.href = '/client/my_orders'; });
                    },
                    error: function (x) { $('#btnCheckout').prop('disabled', false).html('<i class="bi bi-bag-check-fill me-2"></i>Finalizar Compra'); showToast(x.responseJSON ? x.responseJSON.message : 'Error al procesar', 'error'); }
                });
            });
        });
        function formatPaymentMethodLabel(value) {
            return String(value || '').replace(/_/g, ' ').replace(/\b\w/g, function (m) { return m.toUpperCase(); });
        }
        function loadPaymentMethods() {
            return $.get('/api/payment-methods/active', function (r) {
                var select = $('#metodoPago');
                select.empty();
                var methods = r.data || [];
                if (!methods.length) {
                    select.append('<option value="">Sin metodos disponibles</option>');
                    $('#btnCheckout').prop('disabled', true);
                    return;
                }
                methods.forEach(function (m) {
                    select.append('<option value="' + escapeHtml(m.nombre) + '" data-moneda="' + escapeHtml(m.moneda || 'usd') + '" data-datos-pago="' + escapeHtml(m.datos_pago || '') + '">' + escapeHtml(formatPaymentMethodLabel(m.nombre)) + '</option>');
                });
                select.trigger('change');
            }).fail(function () {
                var fallback = [
                    { nombre: 'transferencia', moneda: 'bs', datos_pago: 'Banco Mercantil - Cta: 0105-0000-0000-0000-0000' },
                    { nombre: 'pago_movil', moneda: 'bs', datos_pago: 'Pago Móvil Mercantil: V-12345678 - Tel: 0412-0000000' },
                    { nombre: 'efectivo', moneda: 'usd', datos_pago: '' },
                    { nombre: 'zelle', moneda: 'usd', datos_pago: 'zelle@transalca.com' }
                ];
                var select = $('#metodoPago');
                select.empty();
                fallback.forEach(function (m) {
                    select.append('<option value="' + m.nombre + '" data-moneda="' + m.moneda + '" data-datos-pago="' + escapeHtml(m.datos_pago || '') + '">' + formatPaymentMethodLabel(m.nombre) + '</option>');
                });
                select.trigger('change');
            });
        }
        function loadCart() {
            return $.get('/api/orders/cart', function (r) {
                var html = ''; var total = 0;
                if (!r.data || r.data.length === 0) {
                    html = '<div class="text-center py-5"><i class="bi bi-cart-x fs-1 text-muted"></i><p class="text-muted mt-2">Tu carrito está vacío</p><a href="/client/catalog" class="btn btn-primary-custom">Ver Catálogo</a></div>';
                    $('#btnCheckout').prop('disabled', true);
                } else {
                    r.data.forEach(function (item) {
                        var subtotal = item.precio * item.cantidad; total += subtotal;
                        html += '<div class="d-flex justify-content-between align-items-center py-3 border-bottom"><div class="d-flex align-items-center gap-3"><img src="/public/assets/' + (item.imagen_path || 'images/no-image.png') + '" style="width:60px;height:60px;object-fit:cover;border-radius:8px;" onerror="this.src=\'/public/assets/images/no-image.png\'"><div><h6 class="mb-0 fw-bold">' + item.item_nombre + '</h6><small class="text-muted">' + item.tipo + '</small></div></div><div class="d-flex align-items-center gap-3"><div class="input-group input-group-sm" style="width:120px;"><button class="btn btn-outline-secondary" onclick="updateQty(' + item.id + ',' + (item.cantidad - 1) + ')">-</button><input type="text" class="form-control text-center" value="' + item.cantidad + '" readonly><button class="btn btn-outline-secondary" onclick="updateQty(' + item.id + ',' + (item.cantidad + 1) + ')">+</button></div><span class="fw-bold cart-item-price" data-usd-price="' + subtotal + '" data-no-hydrate="true">' + formatUsdBs(subtotal) + '</span><button class="btn btn-sm btn-outline-danger" onclick="removeItem(' + item.id + ')"><i class="bi bi-trash"></i></button></div></div>';
                    });
                }
                $('#cartItems').html(html);
                $('#subtotal').attr('data-usd-price', total);
                $('#total').attr('data-usd-price', total);
                updateSummaryPrices();
            });
        }
        function updateSummaryPrices() {
            var selectedOption = $('#metodoPago option:selected');
            var paymentCurrency = (selectedOption.attr('data-moneda') || 'usd').toLowerCase();
            var rates = window.TransalcaRates || { bcv: 0, usdt: 0 };
            var bcv = parseFloat(rates.bcv || 0);
            var usdt = parseFloat(rates.usdt || 0);

            var formatVal = function (usdVal) {
                if (paymentCurrency === 'bs' && bcv && usdt) {
                    var precioDolar = (usdVal * usdt) / bcv;
                    var bsVal = precioDolar * bcv;
                    return 'Bs. ' + parseFloat(bsVal || 0).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                } else {
                    return '$' + parseFloat(usdVal || 0).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                }
            };

            $('#subtotal').text(formatVal(parseFloat($('#subtotal').attr('data-usd-price') || 0)));
            $('#total').text(formatVal(parseFloat($('#total').attr('data-usd-price') || 0)));

            $('.cart-item-price').each(function () {
                var usdPrice = parseFloat($(this).attr('data-usd-price') || 0);
                $(this).text(formatVal(usdPrice));
            });

            $('#divisasPromoLabel').remove();
            if (paymentCurrency === 'usd') {
                $('<div id="divisasPromoLabel" class="text-danger small fw-bold mb-2">Promoción en divisas</div>').insertBefore('#total');
            }

            var datosPago = selectedOption.attr('data-datos-pago') || '';
            var infoContainer = $('#metodoPagoInfoContainer');
            if (datosPago.trim()) {
                $('#metodoPagoInfoText').text(datosPago);
                infoContainer.show();
            } else {
                $('#metodoPagoInfoText').text('');
                infoContainer.hide();
            }
        }
        function updateQty(cartId, qty) {
            if (qty < 1) { removeItem(cartId); return; }
            $.ajax({ url: '/api/orders/cart/' + cartId + '/update', type: 'PUT', contentType: 'application/json', data: JSON.stringify({ cantidad: qty }), success: function () { loadCart(); updateCartBadge(); } });
        }
        function removeItem(cartId) { $.ajax({ url: '/api/orders/cart/' + cartId + '/remove', type: 'DELETE', success: function () { loadCart(); updateCartBadge(); } }); }
