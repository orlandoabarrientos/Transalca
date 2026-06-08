$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="categories"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html');
    loadData();
    Validator.setRules('categoryForm', {
        nombre: {
            required: true,
            minLength: 3,
            maxLength: 30,
            pattern: /^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+(?: [a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+)*$/,
            requiredMsg: 'El nombre de la categoría es obligatorio',
            minLengthMsg: 'El nombre debe tener al menos 3 caracteres',
            maxLengthMsg: 'El nombre no puede superar los 30 caracteres.',
            patternMsg: 'El nombre solo puede contener letras, números y espacios simples.'
        },
        descripcion: {
            maxLength: 150,
            pattern: /^$|^[^<>]+$/,
            maxLengthMsg: 'La descripción no puede superar los 150 caracteres.',
            patternMsg: 'La descripción contiene caracteres no permitidos.'
        }
    });
    Validator.setupRealtime('categoryForm');


    let checkTimeout = null;
    const nameInput = document.getElementById('nombre');
    if (nameInput) {
        nameInput.addEventListener('input', () => {
            clearTimeout(checkTimeout);
            const val = nameInput.value.trim();
            const exclude = document.getElementById('categoryOldNombre').value.trim();
            if (val.length < 3) return;
            checkTimeout = setTimeout(() => {
                fetch(`/api/categories/check-unique?value=${encodeURIComponent(val)}&exclude=${encodeURIComponent(exclude)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'success' && !data.unique) {
                            nameInput.dataset.externalError = 'La categoría ya existe';
                            setFieldError(nameInput, 'La categoría ya existe');
                        } else {
                            delete nameInput.dataset.externalError;
                            if (nameInput.classList.contains('is-invalid') && getFieldFeedback(nameInput).textContent === 'La categoría ya existe') {
                                clearFieldError(nameInput);
                                nameInput.classList.add('is-valid');
                            }
                        }
                        updateFormSubmitState('categoryForm');
                    });
            }, 350);
        });
    }

    document.getElementById('imagen')?.addEventListener('change', function(e) {
        const file = e?.target?.files?.[0];
        if (!file) {
            setImagePreview('');
            return;
        }
        if (!['image/png', 'image/jpeg', 'image/webp', 'image/jpg'].includes(file.type)) {
            e.target.value = '';
            setImagePreview('');
            return showToast('El archivo debe ser una imagen png, jpg, jpeg o webp', 'warning');
        }
        if (file.size > 2 * 1024 * 1024) {
            e.target.value = '';
            setImagePreview('');
            return showToast('La imagen no debe superar los 2MB', 'warning');
        }
        const reader = new FileReader();
        reader.onload = function (evt) {
            setImagePreview(evt?.target?.result || '');
        };
        reader.readAsDataURL(file);
    });
});

function setImagePreview(src) {
    const container = document.getElementById('imagePreviewContainer');
    const img = document.getElementById('imagePreview');
    if (!img || !container) return;
    if (!src) {
        container.style.display = 'none';
        img.src = '';
        return;
    }
    img.src = src;
    container.style.display = 'block';
}

let paginator = null;

function loadData() {
    apiCall('/api/categories/').then(res => {
        if (!paginator) {
            paginator = new TablePaginator('categoryBody', {
                allData: res.data || [],
                itemName: 'categorías',
                renderRow: (c) => {
                    const categoryImgUrl = c.imagen ? `/public/assets/images/${encodeURIComponent(c.imagen)}` : '/public/assets/images/product-default-parts.png';
                    return `<tr class="fade-in-up">
                        <td><img src="${categoryImgUrl}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 6px;" class="border shadow-sm"></td>
                        <td><strong>${escapeHtml(c.nombre)}</strong></td>
                        <td>${escapeHtml(c.descripcion || '-')}</td>
                        <td>${c.total_productos || 0}</td>
                        <td>
                            <button class="btn btn-icon btn-outline-orange btn-sm" onclick="editData('${escape(c.nombre)}')" title="Modificar Categoría"><i class="bi bi-pencil"></i></button>
                            <button class="btn btn-icon btn-sm btn-warning" onclick="toggleEstado('${escape(c.nombre)}')" title="Eliminar Categoría"><i class="bi bi-trash"></i></button>
                        </td>
                    </tr>`;
                },
                onEmpty: () => '<tr><td colspan="5" class="text-center py-4"><div class="empty-state"><i class="bi bi-tags"></i><p>No hay categorías registradas</p></div></td></tr>'
            });
        } else {
            paginator.updateData(res.data || []);
        }
    });
}

function openModal(nombre = null) {
    Validator.clearForm('categoryForm');
    document.getElementById('categoryOldNombre').value = nombre ? unescape(nombre) : '';
    document.getElementById('modalTitle').textContent = nombre ? 'Modificar Categoría' : 'Registrar Categoría';
    document.getElementById('imagen').value = '';
    setImagePreview('');
    new bootstrap.Modal(document.getElementById('categoryModal')).show();
    Validator.initTracking('categoryForm');
}

function editData(nombre) {
    nombre = unescape(nombre);
    apiCall(`/api/categories/${encodeURIComponent(nombre)}`).then(res => {
        const c = res.data;
        document.getElementById('categoryOldNombre').value = c.nombre;
        document.getElementById('nombre').value = c.nombre;
        document.getElementById('descripcion').value = c.descripcion || '';
        document.getElementById('modalTitle').textContent = 'Modificar Categoría';
        document.getElementById('imagen').value = '';
        if (c.imagen) {
            setImagePreview(`/public/assets/images/${encodeURIComponent(c.imagen)}`);
        } else {
            setImagePreview('');
        }
        new bootstrap.Modal(document.getElementById('categoryModal')).show();
        Validator.initTracking('categoryForm');
    });
}

function saveData() {
    if (!Validator.validate('categoryForm')) return showToast('Corrija los errores', 'warning');
    const oldNombre = document.getElementById('categoryOldNombre').value;
    const formEl = document.getElementById('categoryForm');
    const formData = new FormData(formEl);
    
    if (oldNombre) {
        formData.append('old_nombre', oldNombre);
        apiCall('/api/categories/update', 'PUT', formData).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('categoryForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
            showToast(res.message); loadData();
        });
    } else {
        apiCall('/api/categories/', 'POST', formData).then(res => {
            if (res.status === 'error') { Validator.showServerErrors('categoryForm', res.errors); return showToast(res.message, 'error'); }
            bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
            showToast(res.message); loadData();
        });
    }
}

function toggleEstado(nombre) {
    nombre = unescape(nombre);
    confirmAction('¿Estás seguro de que deseas eliminar esta categoría?', () => {
        apiCall('/api/categories/delete', 'DELETE', { nombre }).then(res => { showToast(res.message); loadData(); });
    });
}
