from flask import Blueprint, request, jsonify, session
from model.inventory_model import InventoryModel


inventory_bp = Blueprint('inventory', __name__)
model = InventoryModel()



@inventory_bp.route('/', methods=['GET'])
def get_all():
    try:
        sucursal_raw = request.args.get('sucursal_id')
        sucursal_id = None
        if sucursal_raw:
            try:
                sucursal_id = int(sucursal_raw)
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": "Sucursal invalida"}), 400

        q = (request.args.get('q') or '').strip()[:100] or None
        if request.args.get('page') is not None or request.args.get('per_page') is not None or q is not None:
            try:
                page = max(1, int(request.args.get('page', 1)))
            except (ValueError, TypeError):
                page = 1
            try:
                per_page = max(1, min(100, int(request.args.get('per_page', 30))))
            except (ValueError, TypeError):
                per_page = 30

            paginated = model.get_paginated(page, per_page, sucursal_id=sucursal_id, q=q)
            return jsonify({
                "status": "success",
                "data": paginated["data"],
                "total": paginated["total"],
                "page": paginated["page"],
                "per_page": paginated["per_page"],
                "pages": paginated["pages"]
            })

        if sucursal_id:
            inventory = model.get_by_sucursal(sucursal_id)
        else:
            inventory = model.get_all()
        return jsonify({"status": "success", "data": inventory})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@inventory_bp.route('/low-stock', methods=['GET'])
def low_stock():
    try:
        items = model.get_low_stock()
        return jsonify({"status": "success", "data": items})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@inventory_bp.route('/update-stock', methods=['PUT'])
def update_stock():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('producto_codigo'):
            errors['producto_codigo'] = 'Debe seleccionar un producto'
        try:
            stock = int(data.get('stock', -1))
            if stock < 0:
                errors['stock'] = 'El stock no puede ser negativo'
        except (ValueError, TypeError):
            errors['stock'] = 'Stock invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_stock(data['producto_codigo'], stock, data.get('sucursal_id'))


        return jsonify({"status": "success", "message": "Stock actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@inventory_bp.route('/sales-orders', methods=['GET'])
def get_sales_orders():
    try:
        orders = model.get_sales_orders()
        return jsonify({"status": "success", "data": orders})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@inventory_bp.route('/sales-orders/<int:order_id>', methods=['GET'])
def get_sales_order(order_id):
    try:
        order = model.get_sales_order_detail(order_id)
        if order:
            return jsonify({"status": "success", "data": order})
        return jsonify({"status": "error", "message": "Orden no encontrada"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
