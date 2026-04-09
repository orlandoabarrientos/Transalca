from flask import Blueprint, request, jsonify, session
from model.order_model import OrderModel
from model.bitacora_model import BitacoraModel
import os
from werkzeug.utils import secure_filename

order_bp = Blueprint('orders', __name__)
model = OrderModel()
bitacora = BitacoraModel()
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'comprobantes')


@order_bp.route('/cart', methods=['GET'])
def get_cart():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion"}), 401
        items = model.get_cart(session['user_id'])
        return jsonify({"status": "success", "data": items})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/cart/count', methods=['GET'])
def cart_count():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "success", "count": 0})
        count = model.get_cart_count(session['user_id'])
        return jsonify({"status": "success", "count": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion para agregar al carrito"}), 401
        data = request.get_json()
        if not data.get('item_id'):
            return jsonify({"status": "error", "message": "Producto requerido"}), 400
        model.add_to_cart(session['user_id'], data['item_id'], data.get('tipo', 'producto'), data.get('cantidad', 1))
        return jsonify({"status": "success", "message": "Agregado al carrito"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/cart/<int:cart_id>/update', methods=['PUT'])
def update_cart(cart_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        if not data.get('cantidad') or int(data['cantidad']) <= 0:
            return jsonify({"status": "error", "message": "Cantidad invalida"}), 400
        model.update_cart_quantity(cart_id, data['cantidad'])
        return jsonify({"status": "success", "message": "Carrito actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/cart/<int:cart_id>/remove', methods=['DELETE'])
def remove_from_cart(cart_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.remove_from_cart(cart_id)
        return jsonify({"status": "success", "message": "Eliminado del carrito"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.clear_cart(session['user_id'])
        return jsonify({"status": "success", "message": "Carrito vaciado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/checkout', methods=['POST'])
def checkout():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion para comprar"}), 401
        comprobante_url = ''
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file.filename:
                filename = f"comp_{session['user_id']}_{secure_filename(file.filename)}"
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                comprobante_url = filename
        metodo_pago = request.form.get('metodo_pago', 'transferencia')
        sucursal_id = request.form.get('sucursal_id') or None
        order_id = model.create_sale_order(session['user_id'], metodo_pago, comprobante_url, sucursal_id)
        if order_id:
            bitacora.log_action(session['user_id'], 'CREAR', 'ORDENES',
                f"Orden de venta creada ID: {order_id}", request.remote_addr)
            return jsonify({"status": "success", "message": "Orden creada", "id": order_id})
        return jsonify({"status": "error", "message": "Carrito vacio o error al crear orden"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/my-orders', methods=['GET'])
def my_orders():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        orders = model.get_client_orders(session['user_id'])
        return jsonify({"status": "success", "data": orders})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = model.get_order_detail(order_id)
        if order:
            return jsonify({"status": "success", "data": order})
        return jsonify({"status": "error", "message": "Orden no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
