from flask import Blueprint, jsonify, request, session
from controller._guards import deny, is_employee, require_login
from model.bitacora_model import BitacoraModel
from model.payment_method_model import PaymentMethodModel
from config.validation import require_text

payment_method_bp = Blueprint('payment_methods', __name__)
model = PaymentMethodModel()
bitacora = BitacoraModel()


def _validate(data):
    errors = {}
    clean = {}
    clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=100, allow_serial=True)
    clean['datos'] = require_text(errors, 'datos', data.get('datos'), 'Los datos del metodo de pago', min_len=3, max_len=1000, allow_serial=True)
    return clean, errors


@payment_method_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@payment_method_bp.route('/active', methods=['GET'])
def get_active():
    try:
        auth = require_login()
        if auth:
            return auth
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar los metodos de pago."}), 500


@payment_method_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        value = (request.args.get('value') or '').strip()
        exclude = request.args.get('exclude') or None
        return jsonify({"status": "success", "unique": not model.name_exists(value, exclude)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@payment_method_bp.route('/<int:method_id>', methods=['GET'])
def get_one(method_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        item = model.get_by_id(method_id)
        if not item:
            return jsonify({"status": "error", "message": "Metodo de pago no encontrado."}), 404
        return jsonify({"status": "success", "data": item})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@payment_method_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        clean, errors = _validate(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.name_exists(clean['nombre']):
            return jsonify({"status": "error", "message": "Este metodo de pago ya esta registrado.", "errors": {"nombre": "Este metodo de pago ya esta registrado."}}), 400
        clean['usuario_id'] = session['user_id']
        method_id = model.create(clean)
        bitacora.log_action(session['user_id'], 'CREAR', 'METODOS_PAGO', f"Metodo de pago creado: {clean['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Metodo de pago registrado correctamente.", "id": method_id}), 201
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@payment_method_bp.route('/<int:method_id>', methods=['PUT'])
def update(method_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        if not model.get_by_id(method_id):
            return jsonify({"status": "error", "message": "Metodo de pago no encontrado."}), 404
        clean, errors = _validate(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.name_exists(clean['nombre'], method_id):
            return jsonify({"status": "error", "message": "Este metodo de pago ya esta registrado.", "errors": {"nombre": "Este metodo de pago ya esta registrado."}}), 400
        model.update_method(method_id, clean)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'METODOS_PAGO', f"Metodo de pago modificado: {clean['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Metodo de pago modificado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@payment_method_bp.route('/<int:method_id>', methods=['DELETE'])
def delete(method_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        item = model.get_by_id(method_id)
        if not item:
            return jsonify({"status": "error", "message": "Metodo de pago no encontrado."}), 404
        model.soft_delete(method_id)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'METODOS_PAGO', f"Metodo de pago eliminado: {item['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Metodo de pago eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
