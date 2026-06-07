const adminTicketState = {
    tickets: [],
    selectedId: null
};

$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="tickets"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
    bindAdminTicketEvents();
    loadAdminTickets();
});

function bindAdminTicketEvents() {
    $('#ticketFilterBtn').on('click', () => loadAdminTickets());
    $('#ticketRefreshBtnAdmin').on('click', () => loadAdminTickets());
    $('#ticketFilterStatus,#ticketFilterPriority').on('change', () => loadAdminTickets());
    $('#adminReplyForm').on('submit', sendAdminReply);
    $('#adminTicketStatusBtn').on('click', updateAdminTicketStatus);
}

async function loadAdminTickets() {
    const params = new URLSearchParams();
    const estado = ($('#ticketFilterStatus').val() || '').trim();
    const prioridad = ($('#ticketFilterPriority').val() || '').trim();
    if (estado) params.set('estado', estado);
    if (prioridad) params.set('prioridad', prioridad);

    const query = params.toString() ? `?${params.toString()}` : '';
    try {
        const res = await fetch(`/api/tickets/${query}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudieron cargar tickets', 'error');
            return;
        }
        adminTicketState.tickets = Array.isArray(data.data) ? data.data : [];
        $('#ticketCountAdmin').text(adminTicketState.tickets.length);
        renderAdminTicketsList();

        if (!adminTicketState.tickets.length) {
            clearAdminTicketDetail();
            return;
        }
        const keep = adminTicketState.tickets.find(t => Number(t.id) === Number(adminTicketState.selectedId));
        if (keep) {
            await openAdminTicket(keep.id, true);
        } else {
            await openAdminTicket(adminTicketState.tickets[0].id, true);
        }
    } catch (e) {
        showToast('Error cargando tickets', 'error');
    }
}

let paginator = null;

function renderAdminTicketsList() {
    if (!paginator) {
        paginator = new TablePaginator('adminTicketsList', {
            allData: adminTicketState.tickets,
            itemName: 'tickets',
            renderRow: (t) => {
                const active = Number(t.id) === Number(adminTicketState.selectedId) ? 'active' : '';
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = `list-group-item list-group-item-action ${active}`;
                btn.dataset.ticketId = t.id;
                btn.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="text-start">
                            <div class="fw-semibold">#${t.id} ${escapeHtml(t.asunto || '')}</div>
                            <div class="small text-muted">${escapeHtml((t.cliente_nombre || '') + ' ' + (t.cliente_apellido || ''))}</div>
                            <div class="small text-muted">${formatDate(t.created_at)}</div>
                        </div>
                        <div class="text-end">
                            <div>${estadoBadge(t.estado || 'abierto')}</div>
                            <div class="mt-1">${estadoBadge(t.prioridad || 'media')}</div>
                        </div>
                    </div>
                `;
                btn.addEventListener('click', async () => {
                    await openAdminTicket(t.id);
                });
                return btn;
            },
            onEmpty: () => '<div class="p-3 text-muted">Sin tickets para este filtro.</div>'
        });
    } else {
        paginator.updateData(adminTicketState.tickets);
    }
}

async function openAdminTicket(ticketId, silent = false) {
    try {
        const res = await fetch(`/api/tickets/${ticketId}`, { credentials: 'same-origin' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            if (!silent) showToast(data.message || 'No se pudo abrir el ticket', 'error');
            return;
        }
        adminTicketState.selectedId = ticketId;
        renderAdminTicketsList();
        renderAdminTicketDetail(data.data);
    } catch (e) {
        if (!silent) showToast('Error abriendo ticket', 'error');
    }
}

function clearAdminTicketDetail() {
    $('#adminTicketDetail').html('Seleccione un ticket para abrir la conversación.');
    $('#adminTicketChat').html('<div class="text-muted small">Sin mensajes</div>');
    $('#adminReplyForm').hide();
    $('#adminTicketStatusSelect').prop('disabled', true);
    $('#adminTicketStatusBtn').prop('disabled', true);
}

function renderAdminTicketDetail(ticket) {
    const messages = [];
    messages.push({
        autor_tipo: 'cliente',
        autor_nombre: `${ticket.cliente_nombre || ''} ${ticket.cliente_apellido || ''}`.trim() || 'Cliente',
        mensaje: ticket.descripcion || '',
        created_at: ticket.created_at
    });
    (ticket.respuestas || []).forEach(r => messages.push(r));

    const chatHtml = messages.map(m => {
        const isAgent = (m.autor_tipo || '') !== 'cliente';
        const align = isAgent ? 'justify-content-end' : 'justify-content-start';
        const bubbleClass = isAgent ? 'bg-primary text-white' : 'bg-light border';
        const author = isAgent ? (m.autor_nombre || 'Agente') : (m.autor_nombre || 'Cliente');
        return `
            <div class="d-flex ${align} mb-2">
                <div class="p-2 rounded ${bubbleClass}" style="max-width:80%;">
                    <div class="small fw-semibold mb-1">${escapeHtml(author)}</div>
                    <div>${escapeHtml(m.mensaje || '')}</div>
                    <div class="small ${isAgent ? 'text-white-50' : 'text-muted'} mt-1">${formatDate(m.created_at)}</div>
                </div>
            </div>
        `;
    }).join('');

    $('#adminTicketDetail').html(`
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <h6 class="mb-1">#${ticket.id} ${escapeHtml(ticket.asunto || '')}</h6>
                <div class="small text-muted">Cliente: ${escapeHtml((ticket.cliente_nombre || '') + ' ' + (ticket.cliente_apellido || ''))}</div>
                <div class="small text-muted">Referencia: ${escapeHtml(ticketReferenceLabel(ticket))}</div>
            </div>
            <div class="text-end">
                ${estadoBadge(ticket.prioridad || 'media')}
            </div>
        </div>
    `);

    $('#adminTicketChat').html(chatHtml || '<div class="text-muted small">Sin mensajes</div>');
    const chat = document.getElementById('adminTicketChat');
    if (chat) chat.scrollTop = chat.scrollHeight;

    const isClosed = ['resuelto', 'cerrado'].includes((ticket.estado || '').toLowerCase());
    $('#adminReplyForm').show();
    $('#adminReplyMessage').prop('disabled', isClosed);
    $('#adminReplyForm button[type="submit"]').prop('disabled', isClosed);
    $('#adminTicketStatusSelect').prop('disabled', false).val(ticket.estado || 'abierto');
    $('#adminTicketStatusBtn').prop('disabled', false);
}

function ticketReferenceLabel(ticket) {
    const type = (ticket.referencia_tipo || 'general').toLowerCase();
    if (type === 'vehiculo') return `${ticket.vehiculo_placa || 'N/A'} ${ticket.vehiculo_marca || ''} ${ticket.vehiculo_modelo || ''}`.trim();
    if (type === 'producto') return `Producto ${ticket.producto_nombre || ticket.referencia_id || 'N/A'}`;
    if (type === 'servicio') return `Servicio ${ticket.servicio_nombre || ticket.referencia_id || 'N/A'}`;
    return 'General';
}

async function sendAdminReply(event) {
    event.preventDefault();
    if (!adminTicketState.selectedId) return;
    const mensaje = ($('#adminReplyMessage').val() || '').trim();
    if (!mensaje) {
        showToast('Mensaje requerido', 'warning');
        return;
    }
    try {
        const res = await fetch(`/api/tickets/${adminTicketState.selectedId}/reply`, {
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
        $('#adminReplyMessage').val('');
        await openAdminTicket(adminTicketState.selectedId, true);
        await loadAdminTickets();
    } catch (e) {
        showToast('Error enviando respuesta', 'error');
    }
}

async function updateAdminTicketStatus() {
    if (!adminTicketState.selectedId) return;
    const estado = ($('#adminTicketStatusSelect').val() || '').trim();
    if (!estado) {
        showToast('Estado requerido', 'warning');
        return;
    }
    try {
        const res = await fetch(`/api/tickets/${adminTicketState.selectedId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ estado })
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.message || 'No se pudo actualizar estado', 'error');
            return;
        }
        showToast('Estado actualizado', 'success');
        await openAdminTicket(adminTicketState.selectedId, true);
        await loadAdminTickets();
    } catch (e) {
        showToast('Error actualizando estado', 'error');
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
