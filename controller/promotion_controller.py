from flask import Blueprint, request, jsonify, session
from model.promotion_model import PromotionModel
# from model.bitacora_model import BitacoraModel
from config.constants import TIPOS_PROMOCION
from config.validation import normalize_int, optional_text, require_text, validate_choice
import os
import re
from werkzeug.utils import secure_filename

promotion_bp = Blueprint('promotions', __name__)
model = PromotionModel()
# bitacora = BitacoraModel()
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'images')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_promo(data):
    errors = {}
    clean = {
        'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=150, allow_serial=False),
        'descripcion': optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=500, allow_serial=True),
        'tipo': validate_choice(errors, 'tipo', data.get('tipo'), TIPOS_PROMOCION),
        'puntos_requeridos': normalize_int(errors, 'puntos_requeridos', data.get('puntos_requeridos') or 1, 'Los puntos', min_value=1, max_value=999999),
        'recompensa': optional_text(errors, 'recompensa', data.get('recompensa'), 'La recompensa', max_len=200, allow_serial=True),
        'fecha_inicio': data.get('fecha_inicio') or None,
        'fecha_fin': data.get('fecha_fin') or None
    }
    for field in ('fecha_inicio', 'fecha_fin'):
        if clean[field] and not DATE_RE.match(clean[field]):
            errors[field] = 'La fecha debe tener formato valido.'
    if clean['fecha_inicio'] and clean['fecha_fin'] and clean['fecha_fin'] < clean['fecha_inicio']:
        errors['fecha_fin'] = 'La fecha fin no puede ser menor que la fecha inicio.'
    return clean, errors


@promotion_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        value = request.args.get('value', '').strip()
        exclude = request.args.get('exclude', '').strip()
        if not value:
            return jsonify({"status": "success", "unique": True})
        exists = model.nombre_exists(value, exclude if exclude else None)
        return jsonify({"status": "success", "unique": not exists})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@promotion_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las promociones."}), 500


@promotion_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las promociones."}), 500


@promotion_bp.route('/<int:promo_id>', methods=['GET'])
def get_one(promo_id):
    try:
        promo = model.get_by_id(promo_id)
        if promo:
            return jsonify({"status": "success", "data": promo})
        return jsonify({"status": "error", "message": "Promocion no encontrada."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar la promocion."}), 500


@promotion_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data, errors = _validate_promo(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        existing = model.get_by_nombre(data['nombre'])
        if existing:
            if existing['estado'] == 1:
                return jsonify({"status": "error", "message": "Ya existe una promocion con ese nombre.", "errors": {"nombre": "Ya existe una promocion con ese nombre."}}), 400
            else:
                model.update_promotion(existing['id'], data)
                model.update("transalca", "UPDATE promociones SET estado = 1 WHERE id = %s", (existing['id'],))
                # bitacora.log_action(session['user_id'], 'CREAR', 'PROMOCIONES', f"Promocion creada: {data['nombre']}", request.remote_addr)
                return jsonify({"status": "success", "message": "Promocion registrada correctamente.", "id": existing['id']})
        promo_id = model.create(data)
        # bitacora.log_action(session['user_id'], 'CREAR', 'PROMOCIONES', f"Promocion creada: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Promocion registrada correctamente.", "id": promo_id})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar la promocion."}), 500


@promotion_bp.route('/<int:promo_id>', methods=['PUT'])
def update(promo_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data, errors = _validate_promo(request.get_json() or {})
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400
        if model.nombre_exists(data['nombre'], promo_id):
            return jsonify({"status": "error", "message": "Ya existe una promocion con ese nombre.", "errors": {"nombre": "Ya existe una promocion con ese nombre."}}), 400
        model.update_promotion(promo_id, data)
        # bitacora.log_action(session['user_id'], 'MODIFICAR', 'PROMOCIONES', f"Promocion modificada ID: {promo_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Promocion modificada correctamente."})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar la promocion."}), 500


@promotion_bp.route('/<int:promo_id>', methods=['DELETE'])
def delete(promo_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        new_estado = model.soft_delete(promo_id)
        if new_estado is None:
            return jsonify({"status": "error", "message": "Promocion no encontrada."}), 404
        # bitacora.log_action(session['user_id'], 'MODIFICAR', 'PROMOCIONES', f"Estado promocion cambiado ID: {promo_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Promocion eliminada correctamente.", "estado": new_estado})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado de la promocion."}), 500


@promotion_bp.route('/<int:promo_id>/image', methods=['POST'])
def upload_image(promo_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        if not model.get_by_id(promo_id):
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
        model.update_image(promo_id, filename)
        return jsonify({"status": "success", "message": "Imagen modificada correctamente.", "filename": filename})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo subir la imagen."}), 500


@promotion_bp.route('/assign-card', methods=['POST'])
def assign_card():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        if not data.get('cliente_cedula') or not data.get('promocion_id'):
            return jsonify({"status": "error", "message": "Datos incompletos."}), 400
        card_id = model.assign_card_to_client(data['cliente_cedula'], data['promocion_id'])
        # bitacora.log_action(session['user_id'], 'CREAR', 'PROMOCIONES', f"Tarjeta asignada al cliente: {data['cliente_cedula']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Tarjeta registrada correctamente.", "id": card_id})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar la tarjeta."}), 500


@promotion_bp.route('/cards/client/<path:cliente_cedula>', methods=['GET'])
def client_cards(cliente_cedula):
    try:
        return jsonify({"status": "success", "data": model.get_client_cards(cliente_cedula)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las tarjetas."}), 500


@promotion_bp.route('/cards/my', methods=['GET'])
def my_cards():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        return jsonify({"status": "success", "data": model.get_client_cards(session['user_cedula'])})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las tarjetas."}), 500


@promotion_bp.route('/cards/<int:card_id>/add-point', methods=['POST'])
def add_point(card_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        data = request.get_json() or {}
        descripcion = optional_text({}, 'descripcion', data.get('descripcion', 'Punto registrado'), 'La descripcion', max_len=200, allow_serial=True)
        result = model.add_point(card_id, descripcion or 'Punto registrado')
        if result:
            return jsonify({"status": "success", "message": "Punto registrado correctamente.", "data": result})
        return jsonify({"status": "error", "message": "Tarjeta no valida o ya canjeada."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el punto."}), 500


@promotion_bp.route('/cards/<int:card_id>/history', methods=['GET'])
def card_history(card_id):
    try:
        return jsonify({"status": "success", "data": model.get_card_history(card_id)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el historial."}), 500


@promotion_bp.route('/cards', methods=['GET'])
def all_cards():
    try:
        return jsonify({"status": "success", "data": model.get_all_cards()})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las tarjetas."}), 500


@promotion_bp.route('/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    try:
        card = model.get_card_by_id(card_id)
        if card:
            return jsonify({"status": "success", "data": card})
        return jsonify({"status": "error", "message": "Tarjeta no encontrada."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar la tarjeta."}), 500
