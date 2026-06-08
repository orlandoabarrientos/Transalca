$(document).ready(function () {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => { document.querySelector('[data-page="qr"]')?.classList.add('active'); });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    loadActivePromotions();
    Validator.setRules('qrForm', {
        tipo: { required: true, requiredMsg: 'Seleccione un tipo de QR' },
        utilidad_tipo: { required: true, requiredMsg: 'Seleccione una utilidad' },
        contenido: { maxLength: 150, maxLengthMsg: 'El contenido no puede superar los 150 caracteres.' }
    });
    Validator.setupRealtime('qrForm');
    $('#utilidad_tipo, #tipo').on('change', toggleUtilityFields);
});

let paginator = null;

function loadData() {
    apiCall('/api/qr/').then(res => {
        if (!paginator) {
            paginator = new TablePaginator('qrBody', {
                allData: res.data || [],
                itemName: 'códigos QR',
                renderRow: (q) => {
                    const utilidad = q.utilidad || 'sin utilidad';
                    const utilidadEstado = q.utilidad_estado || 'activa';
                    const utilidadTexto = utilidadEstado === 'activa' ? utilidad : `${utilidad} (${utilidadEstado})`;
                    const contenido = (q.contenido_resumen || q.contenido || '').toString();
                    return `<tr class="fade-in-up">
                        <td class="col-id">${q.id}</td>
                        <td><span class="badge-status badge-info">${q.tipo}</span></td>
                        <td>${escapeHtml(utilidadTexto)}</td>
                        <td>${escapeHtml(contenido.substring(0, 50))}${contenido.length > 50 ? '...' : ''}</td>
                        <td>${q.usuario_nombre || 'N/A'}</td>
                        <td>${formatDate(q.created_at)}</td>
                        <td>
                            <button class="btn btn-icon btn-outline-info btn-sm" onclick="viewQRImage(${q.id})" title="Ver Codigo QR"><i class="bi bi-qr-code-scan"></i></button>
                            <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData(${q.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                            <button class="btn btn-icon btn-sm btn-warning" onclick="deleteQR(${q.id})" title="Eliminar"><i class="bi bi-trash"></i></button>
                        </td>
                    </tr>`;
                },
                onEmpty: () => '<tr><td colspan="7" class="text-center py-4"><div class="empty-state"><i class="bi bi-qr-code"></i><p>Sin codigos QR</p></div></td></tr>'
            });
        } else {
            paginator.updateData(res.data || []);
        }
    });
}

function openModal() { Validator.clearForm('qrForm'); document.getElementById('qrId').value = ''; document.getElementById('modalTitle').textContent = 'Nuevo QR'; document.getElementById('contenido').value = ''; document.getElementById('utilidad_tipo').value = ''; document.getElementById('referenciaId').value = ''; document.getElementById('promocionRefSelect').value = ''; document.getElementById('ttlMinutos').value = '10'; toggleUtilityFields(); new bootstrap.Modal(document.getElementById('qrModal')).show(); }

function editData(id) {
    apiCall(`/api/qr/${id}`).then(res => {
        const q = res.data;
        document.getElementById('qrId').value = q.id;
        document.getElementById('tipo').value = q.tipo;
        document.getElementById('contenido').value = q.contenido_resumen || q.contenido || '';
        document.getElementById('utilidad_tipo').value = q.utilidad || '';
        document.getElementById('referenciaId').value = q.utilidad_referencia_id || '';
        const isPromo = (q.tipo === 'promocion' || q.utilidad === 'promocion');
        document.getElementById('promocionRefSelect').value = isPromo ? (q.utilidad_referencia_id || '') : '';
        document.getElementById('ttlMinutos').value = '10';
        document.getElementById('modalTitle').textContent = 'Editar QR';
        toggleUtilityFields();
        new bootstrap.Modal(document.getElementById('qrModal')).show();
    });
}

function saveData() {
    if (!Validator.validate('qrForm')) return showToast('Corrija los errores', 'warning');
    const id = document.getElementById('qrId').value;
    const tipo = (document.getElementById('tipo').value || '').trim();
    const utilidadTipo = (document.getElementById('utilidad_tipo').value || '').trim();
    const contenido = (document.getElementById('contenido').value || '').trim();
    const promoRefId = (document.getElementById('promocionRefSelect').value || '').trim();
    const ttlMinutos = (document.getElementById('ttlMinutos').value || '').trim() || '10';

    const isPromo = (tipo === 'promocion' || utilidadTipo === 'promocion');
    const referenciaId = isPromo ? promoRefId : '';

    if (!utilidadTipo && contenido.length < 3) {
        return showToast('El contenido o la utilidad es requerido', 'warning');
    }

    if (isPromo && !referenciaId) {
        return showToast('Debe seleccionar una promocion activa', 'warning');
    }

    const data = {
        tipo: tipo,
        contenido: contenido,
        utilidad: utilidadTipo,
        utilidad_tipo: utilidadTipo,
        referencia_id: referenciaId,
        ttl_minutos: ttlMinutos
    };
    apiCall(id ? `/api/qr/${id}` : '/api/qr/', id ? 'PUT' : 'POST', data).then(res => {
        if (res.status === 'error') { Validator.showServerErrors('qrForm', res.errors); return showToast(res.message, 'error'); }
        bootstrap.Modal.getInstance(document.getElementById('qrModal')).hide(); showToast(res.message); loadData();
    });
}

function deleteQR(id) { confirmAction('¿Estás seguro de que deseas eliminar este código QR?', () => { apiCall(`/api/qr/${id}`, 'DELETE').then(res => { showToast(res.message); loadData(); }); }, { confirmText: 'Eliminar' }); }

function viewQRImage(id) {
    const preview = document.getElementById('qrImagePreview');
    preview.src = `/api/qr/${id}/image?t=${new Date().getTime()}`;
    new bootstrap.Modal(document.getElementById('viewQrModal')).show();
}

function toggleUtilityFields() {
    const tipo = (document.getElementById('tipo')?.value || '').trim();
    const utilityType = (document.getElementById('utilidad_tipo')?.value || '').trim();
    const promoWrap = document.getElementById('promoRefWrap');
    const orderWrap = document.getElementById('orderRefWrap');
    const ttlWrap = document.getElementById('utilidadTtlWrap');

    const showPromo = (tipo === 'promocion' || utilityType === 'promocion');
    if (promoWrap) promoWrap.style.display = showPromo ? '' : 'none';
    if (orderWrap) orderWrap.style.display = 'none';
    if (ttlWrap) ttlWrap.style.display = (utilityType || showPromo) ? '' : 'none';
    if (window.enhanceSearchableSelects) enhanceSearchableSelects(document.getElementById('qrModal'));
    if (window.jQuery?.fn?.select2) window.jQuery('#promocionRefSelect').trigger('change.select2');
}

function loadActivePromotions() {
    const select = document.getElementById('promocionRefSelect');
    const hint = document.getElementById('promoRefHint');
    if (!select) return;

    apiCall('/api/promotions/').then(res => {
        const rows = res.data || [];
        select.innerHTML = '<option value="">Seleccione promocion</option>';
        if (!rows.length) {
            select.innerHTML = '<option value="">No hay promociones activas</option>';
            select.disabled = true;
            if (hint) hint.textContent = 'No hay promociones activas disponibles.';
            return;
        }

        rows.forEach(p => {
            select.innerHTML += `<option value="${p.id}">${escapeHtml(p.nombre)}</option>`;
        });
        select.disabled = false;
        if (hint) hint.textContent = '';
        if (window.enhanceSearchableSelects) enhanceSearchableSelects(document.getElementById('qrModal'));
        if (window.jQuery?.fn?.select2) window.jQuery(select).trigger('change.select2');
    }).catch(() => {
        select.innerHTML = '<option value="">No se pudieron cargar promociones</option>';
        select.disabled = true;
        if (hint) hint.textContent = 'Error al cargar promociones activas.';
    });
}

function escapeHtml(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
