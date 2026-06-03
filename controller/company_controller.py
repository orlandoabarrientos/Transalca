from decimal import Decimal

from flask import Blueprint, jsonify, request

from config.validation import (
    normalize_cedula,
    normalize_decimal,
    normalize_email,
    normalize_int,
    normalize_phone,
    normalize_rif,
    optional_text,
    require_text,
)
from controller._guards import can_access_client, deny, is_employee, require_login
from model.company_model import CompanyModel


company_bp = Blueprint('companies', __name__)
model = CompanyModel()


def _validate_company(data, require_rif=True):
    errors = {}
    clean = {}
    if require_rif:
        rif, prefix, _ = normalize_rif(errors, data)
        clean['rif'] = rif
        clean['rif_prefijo'] = prefix
    clean['razon_social'] = require_text(errors, 'razon_social', data.get('razon_social'), 'La razon social', min_len=2, max_len=200, allow_serial=True)
    clean['nombre_comercial'] = optional_text(errors, 'nombre_comercial', data.get('nombre_comercial'), 'El nombre comercial', max_len=200)
    clean['telefono'] = normalize_phone(errors, data.get('telefono'))
    clean['email'] = normalize_email(errors, data.get('email'), required=False)
    clean['direccion'] = optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=300)
    clean['representante_nombre'] = optional_text(errors, 'representante_nombre', data.get('representante_nombre'), 'El representante', max_len=150, allow_serial=False)
    rep_required = bool(clean['representante_nombre'])
    rep_cedula, rep_prefijo, _ = normalize_cedula(errors, data, field='representante_cedula', required=rep_required)
    clean['representante_cedula'] = rep_cedula
    clean['representante_cedula_prefijo'] = rep_prefijo
    clean['representante_telefono'] = normalize_phone(errors, data.get('representante_telefono'), 'representante_telefono', required=rep_required)
    clean['representante_email'] = normalize_email(errors, data.get('representante_email'), 'representante_email', required=False)
    clean['sector'] = optional_text(errors, 'sector', data.get('sector'), 'El sector', max_len=150)
    clean['limite_credito'] = normalize_decimal(errors, 'limite_credito', data.get('limite_credito') or '0', 'El limite de credito', min_value=Decimal('0'))
    clean['dias_credito'] = normalize_int(errors, 'dias_credito', data.get('dias_credito') or 0, 'Los dias de credito', min_value=0, max_value=365)
    return clean, errors


@company_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.get_all(request.args.get('q'), request.args.get('estado'))})
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
        return jsonify({"status": "success", "data": model.get_stats()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@company_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        field = (request.args.get('field') or '').strip()
        value = (request.args.get('value') or '').strip()
        exclude = (request.args.get('exclude') or '').strip()
        if field == 'rif':
            errors = {}
            rif, _, _ = normalize_rif(errors, {'rif': value})
            if errors:
                return jsonify({"status": "error", "message": errors['rif']}), 400
            company = model.get_by_rif(rif)
            return jsonify({"status": "success", "exists": bool(company and rif != exclude), "active": bool(company.get('estado')) if company else False})
        if field == 'email':
            errors = {}
            email = normalize_email(errors, value, required=True)
            if errors:
                return jsonify({"status": "error", "message": errors['email']}), 400
            return jsonify({"status": "success", "exists": model.email_exists_globally(email, {"cliente_cedula": exclude})})
        return jsonify({"status": "error", "message": "Campo no valido."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el dato."}), 500


@company_bp.route('/<path:rif>', methods=['GET'])
def get_one(rif):
    try:
        auth = require_login()
        if auth:
            return auth
        company = model.get_by_rif(rif)
        if not company:
            return jsonify({"status": "error", "message": "Empresa no encontrada."}), 404
        if not can_access_client(company['cedula']):
            return deny()
        company['flota'] = model.get_fleet(company['cedula'])
        company['ordenes'] = model.get_orders(company['cedula'])
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
        clean, errors = _validate_company(data, True)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        existing = model.get_by_rif(clean['rif'])
        if existing and existing.get('estado'):
            return jsonify({"status": "error", "message": "Este rif ya esta registrado.", "errors": {"rif": "Este rif ya esta registrado."}}), 400
        if clean.get('email') and model.email_exists_globally(clean['email'], {"cliente_cedula": clean['rif']}):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        result = model.create(clean)
        return jsonify({"status": "success", "message": "Empresa registrada correctamente.", "id": result.get('rif')}), 201
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
        clean, errors = _validate_company({**data, 'rif': rif}, False)
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if clean.get('email') and model.email_exists_globally(clean['email'], {"cliente_cedula": rif}):
            return jsonify({"status": "error", "message": "Este correo ya esta registrado.", "errors": {"email": "Este correo ya esta registrado."}}), 400
        model.update_company(rif, clean)
        return jsonify({"status": "success", "message": "Empresa modificada correctamente."})
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
        model.soft_delete(rif)
        return jsonify({"status": "success", "message": "Empresa eliminada correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
