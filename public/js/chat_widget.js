
(function () {
    'use strict';

    const ASSISTANT_API_URL = window.TRANSALCA_ASSISTANT_API_URL || resolveAssistantApiUrl();
    const WEBHOOK_URL = window.TRANSALCA_ASSISTANT_WEBHOOK_URL || '';
    const BOT_NAME = 'Asistente Transalca';
    const REQUEST_TIMEOUT_MS = Number(window.TRANSALCA_ASSISTANT_TIMEOUT_MS || 12000);
    const SHOW_SUGGESTIONS = window.TRANSALCA_ASSISTANT_SHOW_SUGGESTIONS !== false
        && String(window.TRANSALCA_ASSISTANT_SHOW_SUGGESTIONS ?? 'true').toLowerCase() !== 'false';
    const BRAND_WELCOME_MSG = 'Hola! Soy el asistente de Transalca Group. Cuentame que necesitas y te ayudo. Si quieres hablar con una persona real, me dices y te paso el numero.';
    const WELCOME_MSG = 'Hola! Soy el asistente de Transalca Group. Cuentame que necesitas y te ayudo. Si quieres hablar con una persona real, me dices y te paso el numero.';
    const SUGGESTIONS = [
        'Consultar productos',
        'Precios y promociones',
        'Sucursales cercanas',
        'Hablar con un asesor',
        'Estado de mi pedido'
    ];

    let sessionId = null;
    let isOpen = false;
    let messages = [];

    function resolveAssistantApiUrl() {
        const devPorts = ['3000', '5173', '5500', '5501'];
        const isDetachedFrontend = window.location.protocol === 'file:' || devPorts.includes(window.location.port);
        if (isDetachedFrontend) {
            return 'http://127.0.0.1:5000/api/asistente/mensaje';
        }
        return '/api/asistente/mensaje';
    }

    function generateSessionId() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let id = '';
        if (window.crypto && window.crypto.getRandomValues) {
            const arr = new Uint32Array(20);
            window.crypto.getRandomValues(arr);
            for (let i = 0; i < 20; i++) {
                id += chars.charAt(arr[i] % chars.length);
            }
            return id;
        }
        for (let i = 0; i < 20; i += 1) {
            id += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return id;
    }

    function injectWidget() {
        const btn = document.createElement('button');
        btn.id = 'chatToggleBtn';
        btn.className = 'chat-toggle-btn';
        btn.innerHTML = '<i class="bi bi-chat-dots-fill"></i><span class="badge-dot"></span>';
        btn.onclick = function (e) { e.stopPropagation(); toggleChat(); };
        document.body.appendChild(btn);

        const panel = document.createElement('div');
        panel.id = 'chatPanel';
        panel.className = 'chat-panel';
        panel.onclick = function (e) { e.stopPropagation(); };
        panel.innerHTML = `
            <div class="chat-header">
                <div class="chat-header-info">
                    <div class="chat-header-title">${BOT_NAME}</div>
                    <div class="chat-header-sub">Responde con IA</div>
                </div>
                <div class="chat-header-actions">
                    <button onclick="TransalcaChat.clearSession()">Cerrar sesión</button>
                    <button class="chat-close-btn" onclick="TransalcaChat.close()">✕</button>
                </div>
            </div>
            <div class="chat-chips" id="chatChips"></div>
            <div class="chat-messages" id="chatMessages"></div>
            <div class="chat-input-area">
                <input type="text" class="chat-input" id="chatInput" placeholder="Escribe tu mensaje..." autocomplete="off">
                <button class="chat-send-btn" id="chatSendBtn" onclick="TransalcaChat.send()"><i class="bi bi-send-fill"></i></button>
            </div>
        `;
        document.body.appendChild(panel);

        document.getElementById('chatInput').addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                window.TransalcaChat.send();
            }
        });

        document.addEventListener('click', function (e) {
            if (isOpen) {
                const panel = document.getElementById('chatPanel');
                const btn = document.getElementById('chatToggleBtn');
                if (panel && btn && !panel.contains(e.target) && !btn.contains(e.target)) {
                    closeChat();
                }
            }
        });

        renderChips();
    }

    function renderChips() {
        const container = document.getElementById('chatChips');
        if (!container) return;
        container.innerHTML = '';
        if (!SHOW_SUGGESTIONS) {
            container.style.display = 'none';
            return;
        }
        container.style.display = '';
        SUGGESTIONS.forEach(text => {
            const chip = document.createElement('span');
            chip.className = 'chat-chip';
            chip.textContent = text;
            chip.onclick = () => sendMessage(text);
            container.appendChild(chip);
        });
    }

    function toggleChat() {
        if (isOpen) {
            closeChat();
        } else {
            openChat();
        }
    }

    function openChat() {
        if (!sessionId) {
            sessionId = generateSessionId();
            messages = [];
            addBotMessage(BRAND_WELCOME_MSG);
        }
        isOpen = true;
        document.getElementById('chatPanel').classList.add('open');
        document.getElementById('chatToggleBtn').classList.add('active');
        document.getElementById('chatToggleBtn').innerHTML = '<i class="bi bi-x-lg"></i>';
        setTimeout(() => {
            document.getElementById('chatInput')?.focus();
        }, 350);
    }

    function closeChat() {
        isOpen = false;
        document.getElementById('chatPanel').classList.remove('open');
        document.getElementById('chatToggleBtn').classList.remove('active');
        document.getElementById('chatToggleBtn').innerHTML = '<i class="bi bi-chat-dots-fill"></i><span class="badge-dot"></span>';
    }

    function sendMessage(text) {
        if (!text || !text.trim()) return;
        const msg = text.trim();

        addUserMessage(msg);
        document.getElementById('chatInput').value = '';
        showTyping();
        sendToAssistant(msg);
    }

    function addUserMessage(text) {
        const msg = { type: 'user', text, time: new Date() };
        messages.push(msg);
        renderMessage(msg);
        scrollToBottom();
    }

    function addBotMessage(text, sources) {
        const msg = { type: 'bot', text, sources: Array.isArray(sources) ? sources.slice(0, 4) : [], time: new Date() };
        messages.push(msg);
        renderMessage(msg);
        scrollToBottom();
    }

    function renderMessage(msg) {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        const div = document.createElement('div');
        div.className = `chat-msg ${msg.type}`;

        const text = document.createElement('span');
        text.textContent = msg.text;
        const time = document.createElement('div');
        time.className = 'chat-msg-time';
        time.textContent = msg.time.toLocaleTimeString('es-VE', { hour: '2-digit', minute: '2-digit' });
        div.appendChild(text);
        if (msg.type === 'bot' && Array.isArray(msg.sources) && msg.sources.length) {
            div.appendChild(renderSources(msg.sources));
        }
        div.appendChild(time);
        container.appendChild(div);
    }

    function renderSources(sources) {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-sources';
        const title = document.createElement('div');
        title.className = 'chat-sources-title';
        title.textContent = 'Fuentes';
        wrapper.appendChild(title);
        sources.slice(0, 4).forEach((source) => {
            const url = String(source.url || '');
            const label = String(source.title || source.domain || 'Referencia').slice(0, 90);
            const domain = String(source.domain || '').slice(0, 80);
            const item = document.createElement('a');
            item.className = 'chat-source-link';
            item.textContent = domain ? `${label} (${domain})` : label;
            try {
                const parsed = new URL(url);
                if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
                    item.href = parsed.href;
                    item.target = '_blank';
                    item.rel = 'noopener noreferrer';
                }
            } catch (error) {
                item.removeAttribute('href');
            }
            wrapper.appendChild(item);
        });
        return wrapper;
    }

    function scrollToBottom() {
        const container = document.getElementById('chatMessages');
        if (container) {
            setTimeout(() => { container.scrollTop = container.scrollHeight; }, 100);
        }
    }

    function showTyping() {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        const typing = document.createElement('div');
        typing.className = 'chat-typing';
        typing.id = 'chatTyping';
        typing.innerHTML = '<span></span><span></span><span></span>';
        container.appendChild(typing);
        scrollToBottom();
    }

    function hideTyping() {
        const el = document.getElementById('chatTyping');
        if (el) el.remove();
    }

    async function sendToAssistant(message) {
        if (ASSISTANT_API_URL) {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
            try {
                const response = await fetch(ASSISTANT_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    signal: controller.signal,
                    body: JSON.stringify({
                        session_id: sessionId,
                        id_aleatorio: sessionId,
                        mensaje: message,
                        expected_response: 'json',
                        timestamp: new Date().toISOString(),
                        source: 'transalca_chat'
                    })
                });

                hideTyping();

                if (response.ok) {
                    const data = await response.json();
                    const botReply = data.respuesta || data.message || data.output || data.text || 'Recibido. Un asesor te contactará pronto.';
                    addBotMessage(botReply, data.sources || []);
                } else {
                    addBotMessage('Disculpa, hubo un problema al procesar tu solicitud. Intenta de nuevo o llámanos al +58 424-5026456.');
                }
                clearTimeout(timeout);
                return;
            } catch (error) {
                clearTimeout(timeout);
                hideTyping();
                if (error && error.name === 'AbortError') {
                    addBotMessage('La consulta tardo demasiado y fue cancelada. Intenta con una pregunta mas puntual o prueba de nuevo.');
                } else {
                    addBotMessage('No se pudo conectar con el asistente. Por favor intenta más tarde o contáctanos directamente al +58 424-5026456.');
                }
                return;
            }
        }

        await sendToWebhook(message);
    }

    async function sendToWebhook(message) {
        const payload = {
            session_id: sessionId,
            id_aleatorio: sessionId,
            mensaje: message,
            expected_response: 'json',
            timestamp: new Date().toISOString(),
            source: 'transalca_chat'
        };

        if (!WEBHOOK_URL) {
            setTimeout(() => {
                hideTyping();
                addBotMessage('Gracias por tu mensaje. En este momento nuestro asistente está siendo configurado. Mientras tanto, puedes contactarnos al +58 424-5026456 o visitar nuestras sucursales. ¡Estamos para servirte!');
            }, 1500);
            return;
        }

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
        try {
            const response = await fetch(WEBHOOK_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
                body: JSON.stringify(payload)
            });

            hideTyping();

            if (response.ok) {
                const data = await response.json();
                const botReply = data.respuesta || data.message || data.output || data.text || 'Recibido. Un asesor te contactará pronto.';
                addBotMessage(botReply, data.sources || []);
            } else {
                addBotMessage('Disculpa, hubo un problema al procesar tu solicitud. Intenta de nuevo o llámanos al +58 424-5026456.');
            }
            clearTimeout(timeout);
        } catch (error) {
            clearTimeout(timeout);
            hideTyping();
            if (error && error.name === 'AbortError') {
                addBotMessage('La consulta tardo demasiado y fue cancelada. Intenta con una pregunta mas puntual o prueba de nuevo.');
            } else {
                addBotMessage('No se pudo conectar con el asistente. Por favor intenta más tarde o contáctanos directamente al +58 424-5026456.');
            }
        }
    }

    function clearSession() {
        sessionId = null;
        messages = [];
        const container = document.getElementById('chatMessages');
        if (container) container.innerHTML = '';
        sessionId = generateSessionId();
        addBotMessage(BRAND_WELCOME_MSG);
    }

    window.TransalcaChat = {
        send: function () {
            const input = document.getElementById('chatInput');
            sendMessage(input?.value);
        },
        close: closeChat,
        open: openChat,
        clearSession: clearSession
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectWidget);
    } else {
        injectWidget();
    }

})();
