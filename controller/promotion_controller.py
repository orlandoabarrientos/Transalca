from flask import Blueprint, request, jsonify, session
from controller._guards import can_access_client, deny, is_employee, require_login
from model.promotion_model import PromotionModel

from config.validation import ValidationError, optional_text
import os
from werkzeug.utils import secure_filename

promotion_bp = Blueprint('promotions', __name__)
model = PromotionModel()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'images')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _require_employee():
    login_error = require_login()
    if login_error:
        return login_error
    if not is_employee():
        return deny()
    return None


def _get_accessible_card(card_id):
    login_error = require_login()
    if login_error:
        return None, login_error

    card = model.ejecutar("get_card_by_id", card_id)
    if not card:
        return None, (jsonify({"status": "error", "message": "Tarjeta no encontrada."}), 404)
    if not can_access_client(card.get('cliente_cedula')):
        return None, deny()
    return card, None


@promotion_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        value = request.args.get('value', '').strip()
        exclude = request.args.get('exclude', '').strip()
        if not value:
            return jsonify({"status": "success", "unique": True})
        exists = model.ejecutar("nombre_exists", value, exclude if exclude else None)
        return jsonify({"status": "success", "unique": not exists})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@promotion_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las promociones."}), 500


@promotion_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las promociones."}), 500


@promotion_bp.route('/<int:promo_id>', methods=['GET'])
def get_one(promo_id):
    try:
        promo = model.ejecutar("get_by_id", promo_id)
        if promo:
            return jsonify({"status": "success", "data": promo})
        return jsonify({"status": "error", "message": "Promocion no encontrada."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar la promocion."}), 500


@promotion_bp.route('/', methods=['POST'])
def create():
    try:
        auth_error = _require_employee()
        if auth_error:
            return auth_error
        promo_id = model.ejecutar("create", request.get_json() or {})
        return jsonify({"status": "success", "message": "Promocion registrada correctamente.", "id": promo_id})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar la promocion."}), 500


@promotion_bp.route('/<int:promo_id>', methods=['PUT'])
def update(promo_id):
    try:
        auth_error = _require_employee()
        if auth_error:
            return auth_error
        model.ejecutar("update_promotion", promo_id, request.get_json() or {})
        return jsonify({"status": "success", "message": "Promocion modificada correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar la promocion."}), 500


@promotion_bp.route('/<int:promo_id>', methods=['DELETE'])
def delete(promo_id):
    try:
        auth_error = _require_employee()
        if auth_error:
            return auth_error
        new_estado = model.ejecutar("soft_delete", promo_id)
        if new_estado is None:
            return jsonify({"status": "error", "message": "Promocion no encontrada."}), 404

        return jsonify({"status": "success", "message": "Promocion eliminada correctamente.", "estado": new_estado})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado de la promocion."}), 500


@promotion_bp.route('/<int:promo_id>/image', methods=['POST'])
def upload_image(promo_id):
    try:
        auth_error = _require_employee()
        if auth_error:
            return auth_error
        if not model.ejecutar("get_by_id", promo_id):
            return jsonify({"status": "error", "message": "Promocion no encontrada."}), 404
        if 'image' not in request.files:
            return jsonify({"status": "error", "message": "No se envio archivo."}), 400
        file = request.files['image']
        if not file.filename:
            return jsonify({"status": "error", "message": "Archivo vacio."}), 400
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_IMAGE_EXTENSIONS or file.mimetype not in {'image/png', 'image/jpeg', 'image/webp'}:
            return jsonify({"status": "error", "message": "El archivo debe ser una imagen png, jpg, jpeg o webp."}), 400
        filename = secure_filename(f"promo_{promo_id}_{file.filename}")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        model.ejecutar("update_image", promo_id, filename)
        return jsonify({"status": "success", "message": "Imagen modificada correctamente.", "filename": filename})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo subir la imagen."}), 500


@promotion_bp.route('/assign-card', methods=['POST'])
def assign_card():
    try:
        auth_error = _require_employee()
        if auth_error:
            return auth_error
        data = request.get_json() or {}
        if not data.get('cliente_cedula') or not data.get('promocion_id'):
            return jsonify({"status": "error", "message": "Datos incompletos."}), 400
        card_id = model.ejecutar("assign_card_to_client", data['cliente_cedula'], data['promocion_id'])
        if not card_id:
            return jsonify({"status": "error", "message": "No se pudo registrar la tarjeta."}), 400

        return jsonify({"status": "success", "message": "Tarjeta registrada correctamente.", "id": card_id})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar la tarjeta."}), 500


@promotion_bp.route('/cards/client/<path:cliente_cedula>', methods=['GET'])
def client_cards(cliente_cedula):
    try:
        login_error = require_login()
        if login_error:
            return login_error
        if not can_access_client(cliente_cedula):
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_client_cards", cliente_cedula, scanned_only=True)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las tarjetas."}), 500


@promotion_bp.route('/cards/my', methods=['GET'])
def my_cards():
    try:
        login_error = require_login()
        if login_error:
            return login_error
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        return jsonify({"status": "success", "data": model.ejecutar("get_client_cards", session['user_cedula'], scanned_only=True)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las tarjetas."}), 500


@promotion_bp.route('/cards/<int:card_id>/add-point', methods=['POST'])
def add_point(card_id):
    try:
        auth_error = _require_employee()
        if auth_error:
            return auth_error
        data = request.get_json() or {}
        descripcion = optional_text({}, 'descripcion', data.get('descripcion', 'Punto registrado'), 'La descripcion', max_len=200, allow_serial=True)
        result = model.ejecutar("add_point", card_id, descripcion or 'Punto registrado')
        if result:
            return jsonify({"status": "success", "message": "Punto registrado correctamente.", "data": result})
        return jsonify({"status": "error", "message": "Tarjeta no valida o ya canjeada."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el punto."}), 500


@promotion_bp.route('/cards/<int:card_id>/history', methods=['GET'])
def card_history(card_id):
    try:
        _, access_error = _get_accessible_card(card_id)
        if access_error:
            return access_error
        return jsonify({"status": "success", "data": model.ejecutar("get_card_history", card_id)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el historial."}), 500


@promotion_bp.route('/cards', methods=['GET'])
def all_cards():
    try:
        auth_error = _require_employee()
        if auth_error:
            return auth_error
        return jsonify({"status": "success", "data": model.ejecutar("get_all_cards", scanned_only=True)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las tarjetas."}), 500


@promotion_bp.route('/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    try:
        card, access_error = _get_accessible_card(card_id)
        if access_error:
            return access_error
        return jsonify({"status": "success", "data": card})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar la tarjeta."}), 500
