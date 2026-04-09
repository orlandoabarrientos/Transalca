from flask import Blueprint, request, jsonify, session
from model.promotion_model import PromotionModel
from model.bitacora_model import BitacoraModel
import os
from werkzeug.utils import secure_filename

promotion_bp = Blueprint('promotions', __name__)
model = PromotionModel()
bitacora = BitacoraModel()
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'images')


@promotion_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/<int:promo_id>', methods=['GET'])
def get_one(promo_id):
    try:
        promo = model.get_by_id(promo_id)
        if promo:
            return jsonify({"status": "success", "data": promo})
        return jsonify({"status": "error", "message": "Promocion no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if not data.get('tipo'):
            errors['tipo'] = 'Seleccione un tipo de promocion'
        try:
            pts = int(data.get('puntos_requeridos', 0))
            if pts <= 0:
                errors['puntos_requeridos'] = 'Los puntos deben ser mayor a 0'
        except (ValueError, TypeError):
            errors['puntos_requeridos'] = 'Valor invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        promo_id = model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'PROMOCIONES',
            f"Promocion creada: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Promocion creada", "id": promo_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/<int:promo_id>', methods=['PUT'])
def update(promo_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_promotion(promo_id, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PROMOCIONES',
            f"Promocion modificada ID: {promo_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Promocion actualizada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/<int:promo_id>', methods=['DELETE'])
def delete(promo_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(promo_id)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'PROMOCIONES',
            f"Promocion desactivada ID: {promo_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Promocion desactivada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/<int:promo_id>/image', methods=['POST'])
def upload_image(promo_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if 'image' not in request.files:
            return jsonify({"status": "error", "message": "No se envio archivo"}), 400
        file = request.files['image']
        filename = f"promo_{promo_id}_{secure_filename(file.filename)}"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        model.update_image(promo_id, filename)
        return jsonify({"status": "success", "message": "Imagen actualizada", "filename": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/assign-card', methods=['POST'])
def assign_card():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        if not data.get('cliente_id') or not data.get('promocion_id'):
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        card_id = model.assign_card_to_client(data['cliente_id'], data['promocion_id'])
        bitacora.log_action(session['user_id'], 'CREAR', 'PROMOCIONES',
            f"Tarjeta asignada al cliente ID: {data['cliente_id']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Tarjeta asignada", "id": card_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/cards/client/<int:cliente_id>', methods=['GET'])
def client_cards(cliente_id):
    try:
        return jsonify({"status": "success", "data": model.get_client_cards(cliente_id)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/cards/my', methods=['GET'])
def my_cards():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.get_client_cards(session['user_id'])})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/cards/<int:card_id>/add-point', methods=['POST'])
def add_point(card_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        result = model.add_point(card_id, data.get('descripcion', 'Punto agregado'))
        if result:
            return jsonify({"status": "success", "message": "Punto agregado", "data": result})
        return jsonify({"status": "error", "message": "Tarjeta no valida o ya canjeada"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/cards/<int:card_id>/history', methods=['GET'])
def card_history(card_id):
    try:
        return jsonify({"status": "success", "data": model.get_card_history(card_id)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/cards', methods=['GET'])
def all_cards():
    try:
        return jsonify({"status": "success", "data": model.get_all_cards()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@promotion_bp.route('/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    try:
        card = model.get_card_by_id(card_id)
        if card:
            return jsonify({"status": "success", "data": card})
        return jsonify({"status": "error", "message": "Tarjeta no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
