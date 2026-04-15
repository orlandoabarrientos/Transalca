from flask import Blueprint, request, jsonify, session
from model.qr_model import QRModel
from model.bitacora_model import BitacoraModel

qr_bp = Blueprint('qr', __name__)
model = QRModel()
bitacora = BitacoraModel()


@qr_bp.route('/', methods=['GET'])
def get_all():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.get_all_qrs()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@qr_bp.route('/my', methods=['GET'])
def my_qrs():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if session.get('user_tipo') != 'cliente':
            return jsonify({"status": "error", "message": "Solo clientes"}), 403
        return jsonify({"status": "success", "data": model.get_user_qrs(session['user_cedula'])})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@qr_bp.route('/<int:qr_id>', methods=['GET'])
def get_one(qr_id):
    try:
        qr = model.get_by_id(qr_id)
        if qr:
            return jsonify({"status": "success", "data": qr})
        return jsonify({"status": "error", "message": "QR no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@qr_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        errors = {}
        if not data.get('tipo'):
            errors['tipo'] = 'Seleccione un tipo de QR'
        utilidad_tipo = (data.get('utilidad_tipo') or '').strip().lower()
        if utilidad_tipo:
            if utilidad_tipo in ('promocion', 'validar_pago', 'mesa') and not str(data.get('referencia_id') or '').strip():
                errors['referencia_id'] = 'Seleccione una referencia para esta utilidad'
        elif not data.get('contenido') or len(data.get('contenido', '').strip()) < 3:
            errors['contenido'] = 'El contenido es requerido (min 3 caracteres)'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        data['usuario_cedula'] = session['user_cedula']
        qr_id = model.create_qr(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'QR',
            f"QR creado ID: {qr_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "QR creado", "id": qr_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@qr_bp.route('/<int:qr_id>', methods=['PUT'])
def update(qr_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        errors = {}
        utilidad_tipo = (data.get('utilidad_tipo') or '').strip().lower()
        if utilidad_tipo and utilidad_tipo in ('promocion', 'validar_pago', 'mesa') and not str(data.get('referencia_id') or '').strip():
            errors['referencia_id'] = 'Seleccione una referencia para esta utilidad'
        elif not utilidad_tipo and (not data.get('contenido') or len(data.get('contenido', '').strip()) < 3):
            errors['contenido'] = 'El contenido es requerido (min 3 caracteres)'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        model.update_qr(qr_id, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'QR',
            f"QR modificado ID: {qr_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "QR actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@qr_bp.route('/<int:qr_id>', methods=['DELETE'])
def delete(qr_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.soft_delete(qr_id)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'QR',
            f"QR desactivado ID: {qr_id}", request.remote_addr)
        return jsonify({"status": "success", "message": "QR desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@qr_bp.route('/scan/<int:qr_id>', methods=['GET'])
def scan(qr_id):
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = model.get_qr_data(qr_id)
        if data:
            return jsonify({"status": "success", "data": data})
        return jsonify({"status": "error", "message": "QR no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@qr_bp.route('/<int:qr_id>/image', methods=['GET'])
def generate_image(qr_id):
    try:
        qr_obj = model.get_by_id(qr_id)
        if not qr_obj:
            return jsonify({"status": "error", "message": "QR no encontrado"}), 404
            
        import qrcode
        import io
        from flask import send_file
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        
        contenido = request.host_url.rstrip('/') + f"/scanner?qr={qr_id}"
        
        qr.add_data(contenido)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return send_file(img_byte_arr, mimetype='image/png')
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
