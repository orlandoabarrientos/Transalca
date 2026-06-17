from flask import Blueprint, jsonify, request

from config.validation import ValidationError, normalize_cedula, normalize_email, normalize_rif
from controller._guards import can_access_client, deny, is_employee, require_login
from model.company_model import CompanyModel



company_bp = Blueprint('companies', __name__)
model = CompanyModel()



@company_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_all", request.args.get('q'), request.args.get('estado'))})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@company_bp.route('/stats', methods=['GET'])
def stats():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_stats")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@company_bp.route('/check-unique', methods=['POST'])
def check_unique():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        payload = request.get_json(silent=True) or {}
        field = (payload.get('field') or '').strip()
        value = (payload.get('value') or '').strip()
        exclude = (payload.get('exclude') or '').strip()
        if field == 'rif':
            errors = {}
            rif, _, _ = normalize_rif(errors, {'rif': value})
            if errors:
                return jsonify({"status": "error", "message": errors['rif']}), 400
            company = model.ejecutar("get_by_rif", rif)
            return jsonify({"status": "success", "exists": bool(company and rif != exclude), "active": bool(company.get('estado')) if company else False})
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value, required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            return jsonify({"status": "success", "exists": model.ejecutar("email_exists_globally", email, {"cliente_cedula": exclude})})
        if field == 'representante_cedula':
            errors = {}
            cedula, _, _ = normalize_cedula(errors, {'cedula': value}, field='cedula', required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['cedula']}), 400
            owner = model.ejecutar("find_representative_by_cedula", cedula, exclude or None)
            return jsonify({"status": "success", "exists": bool(owner)})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@company_bp.route('/<path:rif>', methods=['GET'])
def get_one(rif):
    try:
        auth = require_login()
        if auth:
            return auth
        company = model.ejecutar("get_by_rif", rif)
        if not company:
            return jsonify({"status": "error", "message": "Empresa no encontrada."}), 404
        if not can_access_client(company['cedula']):
            return deny()
        company['flota'] = model.ejecutar("get_fleet", company['cedula'])
        company['ordenes'] = model.ejecutar("get_orders", company['cedula'])
        company['representantes'] = model.ejecutar("get_representatives", company['cedula'])
        return jsonify({"status": "success", "data": company})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@company_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        result = model.ejecutar("create", data)
        return jsonify({"status": "success", "message": "Empresa registrada correctamente.", "id": result.get('rif')}), 201
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@company_bp.route('/<path:rif>', methods=['PUT'])
def update(rif):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        model.ejecutar("update_company", rif, data)
        return jsonify({"status": "success", "message": "Empresa modificada correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@company_bp.route('/<path:rif>/toggle', methods=['PUT'])
def delete(rif):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.ejecutar("soft_delete", rif)

        return jsonify({"status": "success", "message": "Empresa eliminada correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@company_bp.route('/<path:rif>/representatives', methods=['POST'])
def add_representative(rif):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        model.ejecutar("add_representative", rif, data)
        return jsonify({"status": "success", "message": "Representante guardado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo registrar el representante."}), 500


@company_bp.route('/representatives/<int:rid>/toggle', methods=['PUT'])
def toggle_representative(rid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        estado = int(data.get('estado', 1))
        model.ejecutar("toggle_representative_relation", rid, estado)
        return jsonify({"status": "success", "message": "Estado del representante actualizado correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo actualizar el estado del representante."}), 500
