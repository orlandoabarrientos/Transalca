from flask import Blueprint, request, jsonify, session
from model.supplier_model import SupplierModel

from config.validation import ValidationError, normalize_email, normalize_rif

supplier_bp = Blueprint('suppliers', __name__)
model = SupplierModel()


@supplier_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los proveedores."}), 500


@supplier_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los proveedores."}), 500


@supplier_bp.route('/check-unique', methods=['POST'])
def check_unique():
    try:
        payload = request.get_json(silent=True) or {}
        field = (payload.get('field') or 'rif').strip()
        exclude = payload.get('exclude') or None
        if field == 'email':
            errors = {}
            email = normalize_email(errors, payload.get('value', ''), required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            return jsonify({"status": "success", "exists": model.ejecutar("email_exists_globally", email, {"proveedor_rif": exclude})})
        errors = {}
        rif, _, _ = normalize_rif(errors, {'rif': payload.get('value', '')})
        if errors:
            return jsonify({"status": "error", "message": errors['rif']}), 400
        return jsonify({"status": "success", "exists": model.ejecutar("rif_exists", rif, exclude)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el rif."}), 500


@supplier_bp.route('/<path:rif>', methods=['GET'])
def get_one(rif):
    try:
        supplier = model.ejecutar("get_by_rif", rif)
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
        rif = model.ejecutar("create", request.get_json() or {})
        return jsonify({"status": "success", "message": "Proveedor registrado correctamente.", "rif": rif})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el proveedor."}), 500


@supplier_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        raw = request.get_json() or {}
        model.ejecutar("update_supplier", raw.get('old_rif', ''), raw)
        return jsonify({"status": "success", "message": "Proveedor modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el proveedor."}), 500


@supplier_bp.route('/toggle', methods=['PUT'])
def toggle():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        rif = (data.get('rif') or '').strip()
        supplier = model.ejecutar("get_by_rif", rif)
        if not supplier:
            return jsonify({"status": "error", "message": "Proveedor no encontrado."}), 404
        model.ejecutar("soft_delete", rif)

        return jsonify({"status": "success", "message": "Proveedor eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del proveedor."}), 500
