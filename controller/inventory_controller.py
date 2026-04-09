from flask import Blueprint, request, jsonify, session
from model.inventory_model import InventoryModel
from model.bitacora_model import BitacoraModel

inventory_bp = Blueprint('inventory', __name__)
model = InventoryModel()
bitacora = BitacoraModel()


@inventory_bp.route('/', methods=['GET'])
def get_all():
    try:
        sucursal_id = request.args.get('sucursal_id')
        if sucursal_id:
            inventory = model.get_by_sucursal(int(sucursal_id))
        else:
            inventory = model.get_all()
        return jsonify({"status": "success", "data": inventory})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/low-stock', methods=['GET'])
def low_stock():
    try:
        items = model.get_low_stock()
        return jsonify({"status": "success", "data": items})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/update-stock', methods=['PUT'])
def update_stock():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('producto_id'):
            errors['producto_id'] = 'Debe seleccionar un producto'
        try:
            stock = int(data.get('stock', -1))
            if stock < 0:
                errors['stock'] = 'El stock no puede ser negativo'
        except (ValueError, TypeError):
            errors['stock'] = 'Stock invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_stock(data['producto_id'], stock, data.get('sucursal_id'))
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'INVENTARIO',
            f"Stock actualizado producto ID: {data['producto_id']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Stock actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/purchase-orders', methods=['GET'])
def get_purchase_orders():
    try:
        orders = model.get_purchase_orders()
        return jsonify({"status": "success", "data": orders})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/purchase-orders/<int:order_id>', methods=['GET'])
def get_purchase_order(order_id):
    try:
        order = model.get_purchase_order_detail(order_id)
        if order:
            return jsonify({"status": "success", "data": order})
        return jsonify({"status": "error", "message": "Orden no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/purchase-orders', methods=['POST'])
def create_purchase_order():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('proveedor_id'):
            errors['proveedor_id'] = 'Debe seleccionar un proveedor'
        if not data.get('detalles') or len(data['detalles']) == 0:
            errors['detalles'] = 'Debe agregar al menos un producto'
        for i, det in enumerate(data.get('detalles', [])):
            if not det.get('producto_id'):
                errors[f'producto_{i}'] = 'Producto requerido'
            if not det.get('cantidad') or int(det.get('cantidad', 0)) <= 0:
                errors[f'cantidad_{i}'] = 'Cantidad debe ser mayor a 0'
            if not det.get('precio_unitario') or float(det.get('precio_unitario', 0)) <= 0:
                errors[f'precio_{i}'] = 'Precio debe ser mayor a 0'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        order_data = {
            'proveedor_id': data['proveedor_id'],
            'usuario_id': session['user_id'],
            'sucursal_id': data.get('sucursal_id'),
            'total': data.get('total', 0),
            'observaciones': data.get('observaciones', '')
        }
        order_id = model.create_purchase_order(order_data, data['detalles'])
        if order_id:
            bitacora.log_action(session['user_id'], 'CREAR', 'INVENTARIO',
                f"Orden de compra creada ID: {order_id}", request.remote_addr)
            return jsonify({"status": "success", "message": "Orden de compra creada", "id": order_id})
        return jsonify({"status": "error", "message": "Error al crear orden"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/purchase-orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        if not data.get('estado'):
            return jsonify({"status": "error", "message": "Estado requerido"}), 400
        model.update_purchase_order_status(order_id, data['estado'])
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'INVENTARIO',
            f"Estado orden compra actualizado ID: {order_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/sales-orders', methods=['GET'])
def get_sales_orders():
    try:
        orders = model.get_sales_orders()
        return jsonify({"status": "success", "data": orders})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/sales-orders/<int:order_id>', methods=['GET'])
def get_sales_order(order_id):
    try:
        order = model.get_sales_order_detail(order_id)
        if order:
            return jsonify({"status": "success", "data": order})
        return jsonify({"status": "error", "message": "Orden no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
