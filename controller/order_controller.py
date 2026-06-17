from flask import Blueprint, request, jsonify, session
from model.order_model import OrderModel

import os
from werkzeug.utils import secure_filename
from config.validation import SELECT_TAMPER_MESSAGE, ValidationError

order_bp = Blueprint('orders', __name__)
model = OrderModel()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'comprobantes')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}


@order_bp.route('/cart', methods=['GET'])
def get_cart():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion"}), 401
        items = model.ejecutar("get_cart", session['user_cedula'])
        return jsonify({"status": "success", "data": items})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el carrito"}), 500


@order_bp.route('/cart/count', methods=['GET'])
def cart_count():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "success", "count": 0})
        count = model.ejecutar("get_cart_count", session['user_cedula'])
        return jsonify({"status": "success", "count": count})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el carrito"}), 500


@order_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion para agregar al carrito"}), 401
        data = request.get_json() or {}
        model.ejecutar("add_to_cart", session['user_cedula'], data)
        return jsonify({"status": "success", "message": "Producto registrado en el carrito correctamente"})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el producto en el carrito"}), 500


@order_bp.route('/cart/<int:cart_id>/update', methods=['PUT'])
def update_cart(cart_id):
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if model.ejecutar("cart_item_owner", cart_id) != session['user_cedula']:
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        data = request.get_json() or {}
        model.ejecutar("update_cart_quantity", cart_id, data.get('cantidad'))
        return jsonify({"status": "success", "message": "Carrito modificado correctamente"})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el carrito"}), 500


@order_bp.route('/cart/<int:cart_id>/remove', methods=['DELETE'])
def remove_from_cart(cart_id):
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if model.ejecutar("cart_item_owner", cart_id) != session['user_cedula']:
            return jsonify({"status": "error", "message": "No autorizado"}), 403
        model.ejecutar("remove_from_cart", cart_id)
        return jsonify({"status": "success", "message": "Producto eliminado del carrito correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el producto del carrito"}), 500


@order_bp.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.ejecutar("clear_cart", session['user_cedula'])
        return jsonify({"status": "success", "message": "Carrito eliminado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo eliminar el carrito"}), 500


@order_bp.route('/checkout', methods=['POST'])
def checkout():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion para comprar"}), 401
        metodo_pago = (request.form.get('metodo_pago') or '').strip()
        if not model.ejecutar("is_valid_payment_method", metodo_pago):
            return jsonify({"status": "error", "message": SELECT_TAMPER_MESSAGE}), 400
        sucursal_id = request.form.get('sucursal_id') or None
        comprobante_url = ''
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                if ext not in ALLOWED_IMAGE_EXTENSIONS:
                    return jsonify({"status": "error", "message": "El comprobante debe ser una imagen o pdf valido"}), 400
                if ext != 'pdf' and file.mimetype not in {'image/png', 'image/jpeg', 'image/webp'}:
                    return jsonify({"status": "error", "message": "El comprobante debe ser una imagen valida"}), 400
                filename = f"comp_{session['user_cedula']}_{secure_filename(file.filename)}"
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                comprobante_url = filename
        order_id = model.ejecutar("create_sale_order", session['user_cedula'], metodo_pago, comprobante_url, sucursal_id)
        if order_id:


            return jsonify({"status": "success", "message": "Orden registrada correctamente", "id": order_id})
        return jsonify({"status": "error", "message": "Carrito vacio o error al crear orden"}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar la orden"}), 500


@order_bp.route('/my-orders', methods=['GET'])
def my_orders():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        orders = model.ejecutar("get_client_orders", session['user_cedula'])
        return jsonify({"status": "success", "data": orders})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las ordenes"}), 500


@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        order = model.ejecutar("get_order_detail", order_id)
        if order:
            if session.get('user_tipo') == 'cliente' and order.get('cliente_cedula') != session.get('user_cedula'):
                return jsonify({"status": "error", "message": "No autorizado"}), 403
            return jsonify({"status": "success", "data": order})
        return jsonify({"status": "error", "message": "Orden no encontrada"}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar la orden"}), 500
