from flask import Blueprint, request, jsonify, session
from model.product_model import ProductModel
from model.bitacora_model import BitacoraModel
from config.validation import SELECT_TAMPER_MESSAGE, normalize_decimal, optional_text, require_text

product_bp = Blueprint('products', __name__)
model = ProductModel()
bitacora = BitacoraModel()


def _validate_product(data):
    errors = {}
    codigo = optional_text(errors, 'codigo', data.get('codigo'), 'El codigo', max_len=50, allow_serial=True)
    if not codigo or len(codigo) < 2:
        errors['codigo'] = 'El codigo debe tener al menos 2 caracteres.'
    clean = {
        'codigo': codigo.upper(),
        'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=150, allow_serial=False),
        'descripcion': optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=500, allow_serial=True),
        'precio': normalize_decimal(errors, 'precio', data.get('precio'), 'El precio'),
        'categoria': require_text(errors, 'categoria', data.get('categoria'), 'La categoria', min_len=1, max_len=150, allow_serial=True),
        'marca': require_text(errors, 'marca', data.get('marca'), 'La marca', min_len=1, max_len=150, allow_serial=True)
    }
    if clean['categoria'] and not errors.get('categoria') and not model.category_exists(clean['categoria']):
        errors['categoria'] = SELECT_TAMPER_MESSAGE
    if clean['marca'] and not errors.get('marca') and not model.brand_exists(clean['marca']):
        errors['marca'] = SELECT_TAMPER_MESSAGE
        
    sucursal_ids = data.get('sucursal_ids')
    if sucursal_ids is not None:
        if not isinstance(sucursal_ids, list):
            errors['sucursal_id'] = 'Formato de sucursales invalido.'
        else:
            cleaned_ids = []
            for s_id in sucursal_ids:
                try:
                    cleaned_ids.append(int(s_id))
                except (ValueError, TypeError):
                    continue
            if not cleaned_ids:
                errors['sucursal_id'] = 'Seleccione al menos una sucursal.'
            else:
                clean['sucursal_ids'] = cleaned_ids
    else:
        errors['sucursal_id'] = 'Seleccione al menos una sucursal.'
        
    return clean, errors


@product_bp.route('/', methods=['GET'])
def get_all():
    try:
        estado = request.args.get('estado')
        if estado is not None:
            if estado not in ('0', '1', 0, 1):
                return jsonify({"status": "error", "message": SELECT_TAMPER_MESSAGE}), 400
            products = model.get_by_estado(int(estado))
        else:
            products = model.get_all()
        return jsonify({"status": "success", "data": products})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        codigo = optional_text({}, 'codigo', request.args.get('value'), 'El codigo', max_len=50, allow_serial=True).upper()
        exclude = request.args.get('exclude') or None
        if not codigo:
            return jsonify({"status": "error", "message": "El codigo es obligatorio"}), 400
        return jsonify({"status": "success", "exists": model.codigo_exists(codigo, exclude)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el codigo"}), 500


@product_bp.route('/detail/<path:codigo>', methods=['GET'])
def get_one(codigo):
    try:
        product = model.get_by_codigo(codigo)
        if product:
            return jsonify({"status": "success", "data": product})
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el producto"}), 500


@product_bp.route('/category/<path:categoria>', methods=['GET'])
def get_by_category(categoria):
    try:
        return jsonify({"status": "success", "data": model.get_by_category(categoria)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/brand/<path:marca>', methods=['GET'])
def get_by_brand(marca):
    try:
        return jsonify({"status": "success", "data": model.get_by_brand(marca)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/search', methods=['GET'])
def search():
    try:
        q = request.args.get('q', '')[:80]
        return jsonify({"status": "success", "data": model.search(q)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo buscar productos"}), 500


@product_bp.route('/sucursal/<int:sid>', methods=['GET'])
def get_by_sucursal(sid):
    try:
        return jsonify({"status": "success", "data": model.get_by_sucursal(sid)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data, errors = _validate_product(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        existing = model.get_by_codigo(data['codigo'])
        if existing:
            if existing['estado'] == 1:
                return jsonify({"status": "error", "message": "Este codigo ya esta registrado", "errors": {"codigo": "Este codigo ya esta registrado."}}), 400
            else:
                model.update_product(existing['codigo'], data)
                model.update("transalca", "UPDATE productos SET estado = 1 WHERE codigo = %s", (existing['codigo'],))
                bitacora.log_action(session['user_id'], 'CREAR', 'PRODUCTOS', f"Producto creado: {data['nombre']}", request.remote_addr)
                return jsonify({"status": "success", "message": "Producto registrado correctamente", "codigo": existing['codigo']})
        model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'PRODUCTOS', f"Producto creado: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Producto registrado correctamente", "codigo": data['codigo']})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el producto"}), 500


@product_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        raw = request.get_json() or {}
        old_codigo = raw.get('old_codigo', '')
        data, errors = _validate_product(raw)
        if not old_codigo:
            errors['old_codigo'] = 'Identificador de producto requerido.'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if data['codigo'] != old_codigo and model.codigo_exists(data['codigo']):
            return jsonify({"status": "error", "message": "Este codigo ya esta registrado", "errors": {"codigo": "Este codigo ya esta registrado."}}), 400
        model.update_product(old_codigo, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PRODUCTOS', f"Producto modificado: {old_codigo}", request.remote_addr)
        return jsonify({"status": "success", "message": "Producto modificado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el producto"}), 500


@product_bp.route('/toggle', methods=['PUT'])
def toggle():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        codigo = (data.get('codigo') or '').strip()
        product = model.get_by_codigo(codigo)
        if not product:
            return jsonify({"status": "error", "message": "Producto no encontrado"}), 404
        model.soft_delete(codigo)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PRODUCTOS', f"Estado producto cambiado: {codigo}", request.remote_addr)
        return jsonify({"status": "success", "message": "Producto eliminado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del producto"}), 500
