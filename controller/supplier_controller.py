from flask import Blueprint, request, jsonify, session
from model.supplier_model import SupplierModel
from model.bitacora_model import BitacoraModel
from config.validation import normalize_email, normalize_phone, normalize_rif, optional_text, require_text

supplier_bp = Blueprint('suppliers', __name__)
model = SupplierModel()
bitacora = BitacoraModel()


def _validate_supplier(data):
    errors = {}
    rif, rif_prefijo, rif_numero = normalize_rif(errors, data)
    clean = {
        'rif': rif,
        'rif_prefijo': rif_prefijo,
        'rif_numero': rif_numero,
        'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=150, allow_serial=False),
        'telefono': normalize_phone(errors, data.get('telefono'), required=False),
        'email': normalize_email(errors, data.get('email'), required=False),
        'direccion': optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=255)
    }
    return clean, errors


@supplier_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los proveedores."}), 500


@supplier_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los proveedores."}), 500


@supplier_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        field = (request.args.get('field') or 'rif').strip()
        exclude = request.args.get('exclude') or None
        if field == 'email':
            errors = {}
            email = normalize_email(errors, request.args.get('value', ''), required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            return jsonify({"status": "success", "exists": model.email_exists_globally(email, {"proveedor_rif": exclude})})
        errors = {}
        rif, _, _ = normalize_rif(errors, {'rif': request.args.get('value', '')})
        if errors:
            return jsonify({"status": "error", "message": errors['rif']}), 400
        return jsonify({"status": "success", "exists": model.rif_exists(rif, exclude)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el rif."}), 500


@supplier_bp.route('/<path:rif>', methods=['GET'])
def get_one(rif):
    try:
        supplier = model.get_by_rif(rif)
        if supplier:
            return jsonify({"status": "success", "data": supplier})
        return jsonify({"status": "error", "message": "Proveedor no encontrado."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el proveedor."}), 500


@supplier_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data, errors = _validate_supplier(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.rif_exists(data['rif']):
            return jsonify({"status": "error", "message": "Este rif ya esta registrado.", "errors": {"rif": "Este rif ya esta registrado."}}), 400
        if data.get('email') and model.email_exists_globally(data['email'], {"proveedor_rif": data['rif']}):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'PROVEEDORES', f"Proveedor creado: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Proveedor registrado correctamente.", "rif": data['rif']})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el proveedor."}), 500


@supplier_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        raw = request.get_json() or {}
        old_rif = raw.get('old_rif', '')
        data, errors = _validate_supplier(raw)
        if not old_rif:
            errors['old_rif'] = 'Identificador de proveedor requerido.'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if data['rif'] != old_rif and model.rif_exists(data['rif']):
            return jsonify({"status": "error", "message": "Este rif ya esta registrado.", "errors": {"rif": "Este rif ya esta registrado."}}), 400
        if data.get('email') and model.email_exists_globally(data['email'], {"proveedor_rif": old_rif}):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        model.update_supplier(old_rif, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PROVEEDORES', f"Proveedor modificado: {old_rif}", request.remote_addr)
        return jsonify({"status": "success", "message": "Proveedor modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el proveedor."}), 500


@supplier_bp.route('/toggle', methods=['PUT'])
def toggle():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        rif = (data.get('rif') or '').strip()
        supplier = model.get_by_rif(rif)
        if not supplier:
            return jsonify({"status": "error", "message": "Proveedor no encontrado."}), 404
        model.soft_delete(rif)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PROVEEDORES', f"Estado proveedor cambiado: {rif}", request.remote_addr)
        return jsonify({"status": "success", "message": "Proveedor eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del proveedor."}), 500
