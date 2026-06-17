(function () {
    'use strict';

    const ASSISTANT_API_URL = window.TRANSALCA_ASSISTANT_API_URL || resolveAssistantApiUrl();
    const BOT_NAME = 'Asistente Transalca';
    const MAX_MESSAGE_LENGTH = Number(window.TRANSALCA_ASSISTANT_MAX_MESSAGE_LENGTH || 1000);
    const REQUEST_TIMEOUT_MS = Number(window.TRANSALCA_ASSISTANT_TIMEOUT_MS || 12000);
    const SHOW_SUGGESTIONS = window.TRANSALCA_ASSISTANT_SHOW_SUGGESTIONS !== false
        && String(window.TRANSALCA_ASSISTANT_SHOW_SUGGESTIONS ?? 'true').toLowerCase() !== 'false';
    const STORAGE_SESSION_KEY = 'transalca_chat_session_id';
    const STORAGE_MESSAGES_KEY = 'transalca_chat_messages';
    const WELCOME_MSG = 'Hola. Soy el asistente de Transalca C.A. Puedo ayudarte con productos, servicios, mantenimiento, compras y pedidos.';
    const SUGGESTIONS = [
        'Que cauchos son buenos para todo terreno?',
        'Consultar productos',
        'Cambio de aceite',
        'Precios y promociones',
        'Estado de mi pedido'
    ];

    let sessionId = null;
    let isOpen = false;
    let isSending = false;
    let messages = [];
    let requestSeq = 0;

    function resolveAssistantApiUrl() {
        const devPorts = ['3000', '5173', '5500', '5501'];
        const isDetachedFrontend = window.location.protocol === 'file:' || devPorts.includes(window.location.port);
        if (isDetachedFrontend) {
            return 'http://127.0.0.1:5000/api/asistente/mensaje';
        }
        return '/api/asistente/mensaje';
    }

    function loadStoredState() {
        try {
            sessionId = window.localStorage.getItem(STORAGE_SESSION_KEY) || null;
            const storedMessages = JSON.parse(window.localStorage.getItem(STORAGE_MESSAGES_KEY) || '[]');
            messages = Array.isArray(storedMessages)
                ? storedMessages.slice(-30).map((msg) => ({
                    type: msg.type === 'user' ? 'user' : 'bot',
                    text: String(msg.text || '').slice(0, 1000),
                    sources: Array.isArray(msg.sources) ? msg.sources.slice(0, 4) : [],
                    time: msg.time ? new Date(msg.time) : new Date()
                }))
                : [];
        } catch (error) {
            sessionId = null;
            messages = [];
        }
    }

    function saveStoredState() {
        try {
            if (sessionId) window.localStorage.setItem(STORAGE_SESSION_KEY, sessionId);
            window.localStorage.setItem(STORAGE_MESSAGES_KEY, JSON.stringify(messages.slice(-30)));
        } catch (error) { }
    }

    function generateSessionId() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let id = '';
        if (window.crypto && window.crypto.getRandomValues) {
            const arr = new Uint32Array(20);
            window.crypto.getRandomValues(arr);
            for (let i = 0; i < 20; i += 1) {
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
        if (document.getElementById('chatToggleBtn')) return;
        loadStoredState();

        const btn = document.createElement('button');
        btn.id = 'chatToggleBtn';
        btn.className = 'chat-toggle-btn';
        btn.type = 'button';
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
                    <div class="chat-header-sub">Asistente ligero</div>
                </div>
                <div class="chat-header-actions">
                    <button type="button" onclick="TransalcaChat.clearSession()">Cerrar sesion</button>
                    <button type="button" class="chat-close-btn" onclick="TransalcaChat.close()">x</button>
                </div>
            </div>
            <div class="chat-chips" id="chatChips"></div>
            <div class="chat-messages" id="chatMessages"></div>
            <div class="chat-input-area">
                <input type="text" class="chat-input" id="chatInput" placeholder="Escribe tu pregunta..." autocomplete="off" maxlength="${MAX_MESSAGE_LENGTH}">
                <button type="button" class="chat-send-btn" id="chatSendBtn" onclick="TransalcaChat.send()"><i class="bi bi-send-fill"></i></button>
            </div>
        `;
        document.body.appendChild(panel);

        const input = document.getElementById('chatInput');
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                window.TransalcaChat.send();
            }
        });

        input.addEventListener('input', function () {
            if (input.value.length > MAX_MESSAGE_LENGTH) {
                input.value = input.value.slice(0, MAX_MESSAGE_LENGTH);
            }
        });

        document.addEventListener('click', function (e) {
            if (!isOpen) return;
            const currentPanel = document.getElementById('chatPanel');
            const currentBtn = document.getElementById('chatToggleBtn');
            if (currentPanel && currentBtn && !currentPanel.contains(e.target) && !currentBtn.contains(e.target)) {
                closeChat();
            }
        });

        renderChips();
        renderAllMessages();
    }

    function renderAllMessages() {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        container.innerHTML = '';
        messages.forEach((msg) => renderMessage(msg));
        scrollToBottom();
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
        SUGGESTIONS.forEach((text) => {
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
            saveStoredState();
        }
        if (!messages.length) {
            messages = [];
            addBotMessage(WELCOME_MSG);
        }
        isOpen = true;
        document.getElementById('chatPanel')?.classList.add('open');
        const btn = document.getElementById('chatToggleBtn');
        if (btn) {
            btn.classList.add('active');
            btn.innerHTML = '<i class="bi bi-x-lg"></i>';
        }
        setTimeout(() => {
            document.getElementById('chatInput')?.focus();
        }, 300);
    }

    function closeChat() {
        isOpen = false;
        document.getElementById('chatPanel')?.classList.remove('open');
        const btn = document.getElementById('chatToggleBtn');
        if (btn) {
            btn.classList.remove('active');
            btn.innerHTML = '<i class="bi bi-chat-dots-fill"></i><span class="badge-dot"></span>';
        }
    }

    function sendMessage(text) {
        if (isSending) return;
        if (!text || !text.trim()) return;

        const msg = text.trim();
        if (msg.length > MAX_MESSAGE_LENGTH) {
            addBotMessage('La pregunta no puede superar 255 caracteres.');
            return;
        }

        addUserMessage(msg);
        const input = document.getElementById('chatInput');
        if (input) input.value = '';
        setSending(true);
        showTyping();
        sendToAssistant(msg);
    }

    function setSending(value) {
        isSending = value;
        const btn = document.getElementById('chatSendBtn');
        const input = document.getElementById('chatInput');
        if (btn) btn.disabled = value;
        if (input) input.disabled = value;
    }

    function addUserMessage(text) {
        const msg = { type: 'user', text, time: new Date() };
        messages.push(msg);
        renderMessage(msg);
        saveStoredState();
        scrollToBottom();
    }

    function addBotMessage(text, sources) {
        const msg = { type: 'bot', text, sources: Array.isArray(sources) ? sources.slice(0, 4) : [], time: new Date() };
        messages.push(msg);
        renderMessage(msg);
        saveStoredState();
        scrollToBottom();
    }

    function renderMessage(msg) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        const div = document.createElement('div');
        div.className = `chat-msg ${msg.type}`;

        const text = document.createElement('div');
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
        if (!container || document.getElementById('chatTyping')) return;
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
        const currentRequest = requestSeq + 1;
        requestSeq = currentRequest;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        try {
            const response = await fetch(ASSISTANT_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                signal: controller.signal,
                body: JSON.stringify({
                    session_id: sessionId,
                    mensaje: message,
                    history: messages.slice(-7).map((msg) => ({ type: msg.type, text: msg.text })),
                    source: 'transalca_chat'
                })
            });

            if (currentRequest !== requestSeq) return;

            const contentType = response.headers.get('content-type') || '';
            const rawBody = await response.text();
            let data = null;
            if (contentType.includes('application/json')) {
                try {
                    data = rawBody ? JSON.parse(rawBody) : {};
                } catch (error) {
                    data = null;
                }
            }

            if (response.ok) {
                if (!data) {
                    addBotMessage('El asistente respondio, pero el servidor no devolvio JSON valido.');
                    return;
                }
                if (data.session_id) {
                    sessionId = String(data.session_id);
                    saveStoredState();
                }
                addBotMessage(data.respuesta || data.message || 'Recibido.', data.sources || []);
            } else {
                if (!data) {
                    addBotMessage(`El servidor respondio HTTP ${response.status}, pero no devolvio JSON valido.`);
                    return;
                }
                const requestId = data.request_id ? ` Codigo: ${data.request_id}.` : '';
                if (response.status === 400) {
                    addBotMessage((data.message || 'La solicitud no es valida.') + requestId);
                } else if (response.status === 404) {
                    addBotMessage('El endpoint del asistente no esta disponible.' + requestId);
                } else if (response.status >= 500) {
                    addBotMessage('El asistente tuvo un error interno.' + requestId);
                } else {
                    addBotMessage((data.message || `No se pudo procesar la pregunta. HTTP ${response.status}.`) + requestId);
                }
            }
        } catch (error) {
            if (error && error.name === 'AbortError') {
                addBotMessage('La consulta tardo demasiado y fue cancelada. Intenta con una pregunta mas puntual o prueba de nuevo.');
            } else if (!navigator.onLine) {
                addBotMessage('No hay conexion de red en este momento.');
            } else {
                addBotMessage('No pude conectar con el endpoint del asistente. Verifica la red o intenta de nuevo.');
            }
        } finally {
            clearTimeout(timeout);
            hideTyping();
            setSending(false);
        }
    }

    function clearSession() {
        sessionId = generateSessionId();
        messages = [];
        saveStoredState();
        const container = document.getElementById('chatMessages');
        if (container) container.innerHTML = '';
        addBotMessage(WELCOME_MSG);
    }

    window.TransalcaChat = {
        send: function () {
            const input = document.getElementById('chatInput');
            sendMessage(input?.value);
        },
        close: closeChat,
        open: openChat,
        clearSession
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectWidget);
    } else {
        injectWidget();
    }
})();
