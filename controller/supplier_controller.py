from flask import Blueprint, request, jsonify, session
from model.supplier_model import SupplierModel
from model.bitacora_model import BitacoraModel
import re

supplier_bp = Blueprint('suppliers', __name__)
model = SupplierModel()
bitacora = BitacoraModel()


@supplier_bp.route('/', methods=['GET'])
def get_all():
    try:
        suppliers = model.get_all()
        return jsonify({"status": "success", "data": suppliers})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@supplier_bp.route('/active', methods=['GET'])
def get_active():
    try:
        suppliers = model.get_active()
        return jsonify({"status": "success", "data": suppliers})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@supplier_bp.route('/<int:supplier_id>', methods=['GET'])
def get_one(supplier_id):
    try:
        supplier = model.get_by_id(supplier_id)
        if supplier:
            return jsonify({"status": "success", "data": supplier})
        return jsonify({"status": "error", "message": "Proveedor no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@supplier_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if not data.get('rif') or not re.match(r'^[JGVEP]-\d{8}-\d$', data['rif'].strip()):
            errors['rif'] = 'RIF invalido. Formato: J-12345678-9'
        if data.get('email') and not re.match(r'^[^@]+@[^@]+\.[^@]+$', data['email']):
            errors['email'] = 'Email invalido'
        if data.get('telefono') and len(data['telefono'].strip()) < 7:
            errors['telefono'] = 'Telefono debe tener al menos 7 caracteres'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.rif_exists(data['rif'].strip()):
            return jsonify({"status": "error", "message": "El RIF ya esta registrado", "errors": {"rif": "El RIF ya esta registrado"}}), 400
        supplier_id = model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'PROVEEDORES',
            f"Proveedor creado: {data['nombre']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Proveedor creado", "id": supplier_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@supplier_bp.route('/<int:supplier_id>', methods=['PUT'])
def update(supplier_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 3:
            errors['nombre'] = 'El nombre debe tener al menos 3 caracteres'
        if not data.get('rif') or not re.match(r'^[JGVEP]-\d{8}-\d$', data['rif'].strip()):
            errors['rif'] = 'RIF invalido. Formato: J-12345678-9'
        if data.get('email') and not re.match(r'^[^@]+@[^@]+\.[^@]+$', data['email']):
            errors['email'] = 'Email invalido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.rif_exists(data['rif'].strip(), supplier_id):
            return jsonify({"status": "error", "message": "El RIF ya esta registrado", "errors": {"rif": "El RIF ya esta registrado"}}), 400
        model.update_supplier(supplier_id, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PROVEEDORES',
            f"Proveedor modificado ID: {supplier_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Proveedor actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@supplier_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete(supplier_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(supplier_id)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'PROVEEDORES',
            f"Proveedor desactivado ID: {supplier_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Proveedor desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@supplier_bp.route('/<int:supplier_id>/toggle', methods=['PUT'])
def toggle(supplier_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.toggle_estado(supplier_id)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'PROVEEDORES',
            f"Estado proveedor cambiado ID: {supplier_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "Estado actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
