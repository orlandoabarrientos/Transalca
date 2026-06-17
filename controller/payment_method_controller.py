from flask import Blueprint, jsonify, request, session
from controller._guards import deny, is_employee, require_login

from model.payment_method_model import PaymentMethodModel
from config.validation import ValidationError

payment_method_bp = Blueprint('payment_methods', __name__)
model = PaymentMethodModel()


@payment_method_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@payment_method_bp.route('/active', methods=['GET'])
def get_active():
    try:
        auth = require_login()
        if auth:
            return auth
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los métodos de pago."}), 500


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
        return jsonify({"status": "success", "unique": not model.ejecutar("name_exists", value, exclude)})
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
        item = model.ejecutar("get_by_id", method_id)
        if not item:
            return jsonify({"status": "error", "message": "Método de pago no encontrado."}), 404
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
        method_id = model.ejecutar("create", request.get_json() or {})
        return jsonify({"status": "success", "message": "Método de pago registrado correctamente.", "id": method_id}), 201
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
        if not model.ejecutar("get_by_id", method_id):
            return jsonify({"status": "error", "message": "Método de pago no encontrado."}), 404
        model.ejecutar("update_method", method_id, request.get_json() or {})
        return jsonify({"status": "success", "message": "Método de pago modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
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
        item = model.ejecutar("get_by_id", method_id)
        if not item:
            return jsonify({"status": "error", "message": "Método de pago no encontrado."}), 404
        model.ejecutar("soft_delete", method_id)

        return jsonify({"status": "success", "message": "Método de pago eliminado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
