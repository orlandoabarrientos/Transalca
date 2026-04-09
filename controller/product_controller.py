from flask import Blueprint, request, jsonify, session
from model.product_model import ProductModel
from model.bitacora_model import BitacoraModel

product_bp = Blueprint('products', __name__)
model = ProductModel()
bitacora = BitacoraModel()


@product_bp.route('/', methods=['GET'])
def get_all():
    try:
        estado = request.args.get('estado')
        if estado is not None:
            products = model.get_by_estado(int(estado))
        else:
            products = model.get_all()
        return jsonify({"status": "success", "data": products})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/active', methods=['GET'])
def get_active():
    try:
        return jsonify({"status": "success", "data": model.get_active()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/<int:pid>', methods=['GET'])
def get_one(pid):
    try:
        product = model.get_by_id(pid)
        if product:
            return jsonify({"status": "success", "data": product})
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/category/<int:cid>', methods=['GET'])
def get_by_category(cid):
    try:
        return jsonify({"status": "success", "data": model.get_by_category(cid)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/brand/<int:bid>', methods=['GET'])
def get_by_brand(bid):
    try:
        return jsonify({"status": "success", "data": model.get_by_brand(bid)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/search', methods=['GET'])
def search():
    try:
        q = request.args.get('q', '')
        return jsonify({"status": "success", "data": model.search(q)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/sucursal/<int:sid>', methods=['GET'])
def get_by_sucursal(sid):
    try:
        return jsonify({"status": "success", "data": model.get_by_sucursal(sid)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('codigo') or len(data['codigo'].strip()) < 2:
            errors['codigo'] = 'El codigo es requerido (min 2 caracteres)'
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        try:
            precio = float(data.get('precio', 0))
            if precio <= 0:
                errors['precio'] = 'El precio debe ser mayor a 0'
        except (ValueError, TypeError):
            errors['precio'] = 'Precio invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.codigo_exists(data['codigo'].strip()):
            return jsonify({"status": "error", "message": "El codigo ya existe", "errors": {"codigo": "El codigo ya existe"}}), 400
        pid = model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'PRODUCTOS',
            f"Producto creado: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Producto creado", "id": pid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/<int:pid>', methods=['PUT'])
def update(pid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('codigo') or len(data['codigo'].strip()) < 2:
            errors['codigo'] = 'El codigo es requerido'
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        try:
            precio = float(data.get('precio', 0))
            if precio <= 0:
                errors['precio'] = 'El precio debe ser mayor a 0'
        except (ValueError, TypeError):
            errors['precio'] = 'Precio invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.codigo_exists(data['codigo'].strip(), pid):
            return jsonify({"status": "error", "message": "El codigo ya existe", "errors": {"codigo": "El codigo ya existe"}}), 400
        model.update_product(pid, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PRODUCTOS',
            f"Producto modificado ID: {pid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Producto actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/<int:pid>', methods=['DELETE'])
def delete(pid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(pid)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'PRODUCTOS',
            f"Producto desactivado ID: {pid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Producto desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/<int:pid>/toggle', methods=['PUT'])
def toggle(pid):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.toggle_estado(pid)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PRODUCTOS',
            f"Estado producto cambiado ID: {pid}", request.remote_addr)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
