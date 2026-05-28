const helpState = {
    initialized: false,
    selectedTicketId: null,
    tickets: [],
    vehicles: [],
    refreshTimer: null
};

$(document).ready(function () {
    $('#navbarContainer').load('/components/client_navbar.html', async () => {
        await initializeHelpPage();
    });
    $('#footerContainer').load('/components/client_footer.html');
});

async function initializeHelpPage() {
    if (helpState.initialized) return;
    helpState.initialized = true;

    const loggedIn = await checkSession();
    if (!loggedIn || !currentUser || currentUser.tipo !== 'cliente') {
        $('#guestHelpBox').show();
        $('#clientHelpApp').hide();
        return;
    }

    $('#guestHelpBox').hide();
    $('#clientHelpApp').show();
    bindHelpEvents();
    await loadHelpVehicles();
    await loadHelpTickets();
    helpState.refreshTimer = setInterval(() => loadHelpTickets(true), 30000);
}

function bindHelpEvents() {
    $('#ticketRefreshBtn').on('click', () => loadHelpTickets());
    $('#newTicketForm').on('submit', createNewHelpTicket);
    $('#replyForm').on('submit', sendHelpReply);
}

async function loadHelpVehicles() {
    try {
        const res = await fetch('/api/vehicles/', { credentials: 'same-origin' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') return;
        helpState.vehicles = Array.isArray(data.data) ? data.data : [];
        const select = $('#newTicketVehicle');
        select.find('option:not(:first)').remove();
        helpState.vehicles.forEach(v => {
            const label = `${v.placa || 'S/P'} - ${v.marca || ''} ${v.modelo || ''}`.trim();
            select.append(`<option value="${escapeHtml(v.placa || v.id || '')}">${escapeHtml(label)}</option>`);
        });
    } catch (e) { }
}

async function loadHelpTickets(silent = false) {
    try {
        const res = await fetch('/api/tickets/', { credentials: 'same-origin' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            if (!silent) showToast(data.message || 'No se pudieron cargar los tickets', 'error');
            return;
        }

        const prevSelected = helpState.selectedTicketId;
        helpState.tickets = Array.isArray(data.data) ? data.data : [];
        renderHelpTicketList();

        if (helpState.tickets.length === 0) {
            helpState.selectedTicketId = null;
            renderEmptyHelpTicketDetail();
            return;
        }

        const keep = helpState.tickets.find(t => Number(t.id) === Number(prevSelected));
        if (keep) {
            await openHelpTicket(keep.id, true);
        } else {
            await openHelpTicket(helpState.tickets[0].id, true);
        }
    } catch (e) {
        if (!silent) showToast('Error cargando tickets', 'error');
    }
}

function renderHelpTicketList() {
    const container = $('#helpTicketsList');
    container.empty();

    if (helpState.tickets.length === 0) {
        container.html('<div class="text-muted small border rounded p-3">No hay tickets abiertos todavia.</div>');
        return;
    }

    helpState.tickets.forEach(t => {
        const active = Number(t.id) === Number(helpState.selectedTicketId) ? 'active' : '';
        const statusBadge = estadoBadge(t.estado || 'abierto');
        const priorityBadge = estadoBadge(t.prioridad || 'media');
        const item = `
            <button type="button" class="list-group-item list-group-item-action ${active}" data-ticket-id="${t.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="text-start">
                        <div class="fw-semibold">#${t.id} ${escapeHtml(t.asunto || '')}</div>
                        <div class="small text-muted">${formatDate(t.created_at)}</div>
                    </div>
                    <div class="text-end">
                        <div>${statusBadge}</div>
                        <div class="mt-1">${priorityBadge}</div>
                    </div>
                </div>
            </button>
        `;
        container.append(item);
    });

    container.find('[data-ticket-id]').on('click', async function () {
        const ticketId = $(this).data('ticket-id');
        await openHelpTicket(ticketId);
    });
}

async function openHelpTicket(ticketId, silent = false) {
    try {
        const res = await fetch(`/api/tickets/${ticketId}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            if (!silent) showToast(data.message || 'No se pudo abrir el ticket', 'error');
            return;
        }
        helpState.selectedTicketId = ticketId;
        renderHelpTicketList();
        renderHelpTicketDetail(data.data);
    } catch (e) {
        if (!silent) showToast('Error al abrir ticket', 'error');
    }
}

function renderEmptyHelpTicketDetail() {
    $('#helpTicketDetail').html('<p class="text-muted mb-0">Abra un ticket nuevo para conversar con soporte.</p>');
    $('#replyForm').hide();
}

function renderHelpTicketDetail(ticket) {
    const messages = [];
    messages.push({
        autor_tipo: 'cliente',
        autor_nombre: currentUser ? `${currentUser.nombre} ${currentUser.apellido || ''}`.trim() : 'Cliente',
        mensaje: ticket.descripcion || '',
        created_at: ticket.created_at
    });
    (ticket.respuestas || []).forEach(r => messages.push(r));

    const isClosed = ['resuelto', 'cerrado'].includes((ticket.estado || '').toLowerCase());
    const messagesHtml = messages.map(m => {
        const mine = (m.autor_tipo || '') === 'cliente';
        const align = mine ? 'justify-content-end' : 'justify-content-start';
        const bubbleClass = mine ? 'bg-primary text-white' : 'bg-light border';
        const author = mine ? 'Usted' : (m.autor_nombre || 'Agente');
        return `
            <div class="d-flex ${align} mb-2">
                <div class="p-2 rounded ${bubbleClass}" style="max-width:80%;">
                    <div class="small fw-semibold mb-1">${escapeHtml(author)}</div>
                    <div>${escapeHtml(m.mensaje || '')}</div>
                    <div class="small ${mine ? 'text-white-50' : 'text-muted'} mt-1">${formatDate(m.created_at)}</div>
                </div>
            </div>
        `;
    }).join('');

    $('#helpTicketDetail').html(`
        <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
                <h6 class="mb-1">#${ticket.id} ${escapeHtml(ticket.asunto || '')}</h6>
                <div class="small text-muted">Creado: ${formatDate(ticket.created_at)}</div>
            </div>
            <div class="text-end">
                ${estadoBadge(ticket.estado || 'abierto')}
                <div class="mt-1">${estadoBadge(ticket.prioridad || 'media')}</div>
            </div>
        </div>
        <div id="helpChatMessages" class="border rounded p-2" style="height:320px;overflow-y:auto;">
            ${messagesHtml || '<div class="text-muted small">Sin mensajes</div>'}
        </div>
    `);

    const chatBox = document.getElementById('helpChatMessages');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;

    $('#replyForm').show();
    $('#replyMessage').prop('disabled', isClosed);
    $('#replyBtn').prop('disabled', isClosed);
    if (isClosed) {
        $('#replyMessage').attr('placeholder', 'Ticket cerrado. No admite nuevas respuestas.');
    } else {
        $('#replyMessage').attr('placeholder', 'Escriba su mensaje...');
    }
}

async function createNewHelpTicket(event) {
    event.preventDefault();
    const payload = {
        asunto: ($('#newTicketSubject').val() || '').trim(),
        prioridad: ($('#newTicketPriority').val() || 'media').trim(),
        descripcion: ($('#newTicketDescription').val() || '').trim()
    };
    const vehiculoId = $('#newTicketVehicle').val();
    if (vehiculoId) payload.vehiculo_id = vehiculoId;

    if (!payload.asunto || !payload.descripcion) {
        showToast('Asunto y descripcion son requeridos', 'error');
        return;
    }

    try {
        const res = await fetch('/api/tickets/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudo crear el ticket', 'error');
            return;
        }

        showToast('Ticket enviado a soporte', 'success');
        $('#newTicketForm')[0].reset();
        $('#newTicketPriority').val('media');
        await loadHelpTickets(true);
        if (data.id) await openHelpTicket(data.id, true);
    } catch (e) {
        showToast('Error creando ticket', 'error');
    }
}

async function sendHelpReply(event) {
    event.preventDefault();
    if (!helpState.selectedTicketId) {
        showToast('Seleccione un ticket primero', 'warning');
        return;
    }

    const mensaje = ($('#replyMessage').val() || '').trim();
    if (!mensaje) {
        showToast('Mensaje requerido', 'warning');
        return;
    }

    try {
        const res = await fetch(`/api/tickets/${helpState.selectedTicketId}/reply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ mensaje })
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudo enviar la respuesta', 'error');
            return;
        }
        $('#replyMessage').val('');
        await openHelpTicket(helpState.selectedTicketId, true);
    } catch (e) {
        showToast('Error enviando respuesta', 'error');
    }
}

function escapeHtml(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
