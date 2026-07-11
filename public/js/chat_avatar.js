(function () {
    'use strict';

    const BOT_AVATAR_URL = window.TRANSALCA_ASSISTANT_AVATAR_URL || '/public/img/chatbot_avatar.svg';

    function makeAvatar(className, alt) {
        const img = document.createElement('img');
        img.className = className;
        img.src = BOT_AVATAR_URL;
        img.alt = alt || '';
        return img;
    }

    function decorateToggle() {
        const btn = document.getElementById('chatToggleBtn');
        if (!btn || btn.classList.contains('active') || btn.querySelector('.chat-toggle-avatar')) return;
        btn.innerHTML = '';
        btn.appendChild(makeAvatar('chat-toggle-avatar', 'Asistente Transalca'));
        const dot = document.createElement('span');
        dot.className = 'badge-dot';
        btn.appendChild(dot);
    }

    function decorateHeader() {
        const header = document.querySelector('#chatPanel .chat-header');
        if (!header || header.querySelector('.chat-header-left')) return;
        const info = header.querySelector('.chat-header-info');
        const actions = header.querySelector('.chat-header-actions');
        if (!info || !actions) return;

        const left = document.createElement('div');
        left.className = 'chat-header-left';
        left.appendChild(makeAvatar('chat-header-avatar'));
        left.appendChild(info);
        header.insertBefore(left, actions);
    }

    function decorateBotMessages() {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        container.querySelectorAll(':scope > .chat-msg.bot').forEach((msg) => {
            const row = document.createElement('div');
            row.className = 'chat-msg-row';
            container.insertBefore(row, msg);
            row.appendChild(makeAvatar('chat-msg-avatar'));
            row.appendChild(msg);
        });
    }

    function decorateChat() {
        decorateToggle();
        decorateHeader();
        decorateBotMessages();
    }

    function observeChat() {
        decorateChat();
        const observer = new MutationObserver(decorateChat);
        observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observeChat);
    } else {
        observeChat();
    }
})();
