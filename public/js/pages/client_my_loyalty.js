function formatCardNumber(id) {
            const padded = String(id || 0).padStart(8, '0');
            return `4318 0092 ${padded.slice(0, 4)} ${padded.slice(4)}`;
        }

        function getCardBackground(imagenTarjeta) {
            if (imagenTarjeta) {
                const url = `/public/assets/images/${encodeURIComponent(imagenTarjeta)}`;
                return `url('${url}')`;
            }
            return 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)';
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        function dateFromValue(value) {
            if (!value) return null;
            if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;

            var text = String(value).trim();
            var dateOnly = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
            if (dateOnly) {
                return new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]));
            }

            var parsed = new Date(text);
            return Number.isNaN(parsed.getTime()) ? null : parsed;
        }

        function addOneMonth(value) {
            var date = dateFromValue(value);
            if (!date) return null;

            var targetMonth = date.getMonth() + 1;
            var result = new Date(date.getFullYear(), targetMonth, date.getDate());
            if (result.getMonth() !== targetMonth % 12) {
                result = new Date(date.getFullYear(), targetMonth + 1, 0);
            }
            return result;
        }

        function formatDisplayDate(value) {
            var date = dateFromValue(value);
            if (!date) return '';

            return date.toLocaleDateString('es-VE', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        }

        function getPromotionExpiryText(card) {
            var expiryDate = dateFromValue(card.fecha_vencimiento_promocion) ||
                addOneMonth(card.fecha_aplicacion_promocion || card.fecha_creacion);
            return formatDisplayDate(expiryDate);
        }

        $(document).ready(function () {
            $('#navbarContainer').load('/components/client_navbar.html', () => checkSession());
            $('#footerContainer').load('/components/client_footer.html');

            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('promo_registered') === '1') {
                const promoName = urlParams.get('promo_name') || 'Promoción';
                showToast(`Su tarjeta para "${promoName}" ha sido registrada exitosamente`, 'success');
                const newUrl = window.location.pathname;
                window.history.replaceState({}, document.title, newUrl);
            }

            $.get('/api/promotions/cards/my', function (r) {
                if (!r.data || r.data.length === 0) { $('#noCards').show(); return; }
                var html = '';
                r.data.forEach(function (card) {
                    var accumulated = card.puntos_acumulados || 0;
                    var required = card.puntos_requeridos || 0;

                    var stampsHtml = '<div class="punch-card-grid">';
                    for (var i = 1; i <= required; i++) {
                        var isReward = (i === required);
                        var isFilled = (i <= accumulated);

                        var slotClass = 'punch-slot';
                        if (isReward) slotClass += ' reward-slot';
                        if (isFilled) slotClass += ' filled';

                        var slotContent = '';
                        if (isReward) {
                            slotContent = isFilled ? '<i class="bi bi-gift-fill"></i>' : '<i class="bi bi-gift"></i>';
                        } else {
                            slotContent = i;
                        }

                        stampsHtml += '<div class="' + slotClass + '">' + slotContent + '</div>';
                    }
                    stampsHtml += '</div>';

                    var completedAlertHtml = '';
                    if (required > 0 && accumulated >= required) {
                        var expiryText = getPromotionExpiryText(card);
                        completedAlertHtml = '<div class="completed-promo-alert mb-2">' +
                            '<i class="bi bi-check-circle-fill me-1"></i>Promoci&oacute;n completada. Puede utilizar su promoci&oacute;n.';
                        if (expiryText) {
                            completedAlertHtml += '<small>V&aacute;lida hasta el ' + escapeHtml(expiryText) + '.</small>';
                        }
                        completedAlertHtml += '</div>';
                    }

                    var bg = getCardBackground(card.imagen_tarjeta);
                    var cardNum = formatCardNumber(card.id);
                    var statusClass = card.canjeada ? 'redeemed-badge' : 'active-badge';
                    var statusText = card.canjeada ? 'Canjeada' : 'Activa';

                    html += '<div class="loyalty-card-wrapper fade-in-up">' +
                        '<div class="fidelity-card-physical" style="background: ' + bg + ';">' +
                            '<div class="card-meta-row">' +
                                '<span class="card-brand-logo">TRANSALCA</span>' +
                                '<span class="card-status-badge ' + statusClass + '">' + statusText + '</span>' +
                            '</div>' +
                            '<div class="card-meta-row mt-2">' +
                                '<div class="card-chip-gold"></div>' +
                                '<i class="bi bi-wifi card-contactless"></i>' +
                            '</div>' +
                            '<div class="card-number-display">' + cardNum + '</div>' +
                            '<div class="card-holder-row">' +
                                '<div>' +
                                    '<div class="card-holder-name">' + escapeHtml(card.cliente_nombre || 'N/A') + '</div>' +
                                    '<div class="card-holder-cedula">C.I. ' + escapeHtml(card.cliente_cedula_display || card.cliente_cedula || '-') + '</div>' +
                                    '</div>' +
                                '</div>' +
                            '</div>' +
                        '<div class="card-stamps-panel">' +
                            '<div class="d-flex justify-content-between align-items-center mb-1">' +
                                '<strong class="text-orange fs-6" style="font-weight:700;">' + escapeHtml(card.promo_nombre || card.promocion_nombre || 'Promoción') + '</strong>' +
                                '<span class="small text-muted" style="font-weight:600;">' + accumulated + ' / ' + required + ' Puntos</span>' +
                            '</div>' +
                            '<p class="small text-muted mb-2">' + escapeHtml(card.promo_descripcion || '') + '</p>' +
                            '<div class="small mb-2"><strong class="text-orange">Recompensa:</strong> ' + escapeHtml(card.recompensa || '-') + '</div>' +
                            completedAlertHtml +
                            stampsHtml +
                        '</div>' +
                    '</div>';
                });
                $('#myCards').html(html);
            });
        });
