from flask import Blueprint, request, jsonify, session
from model.qr_model import QRModel

from config.validation import ValidationError

qr_bp = Blueprint('qr', __name__)
model = QRModel()



@qr_bp.route('/', methods=['GET'])
def get_all():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.ejecutar("get_all_qrs")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@qr_bp.route('/my', methods=['GET'])
def my_qrs():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if session.get('user_tipo') != 'cliente':
            return jsonify({"status": "error", "message": "Solo clientes"}), 403
        return jsonify({"status": "success", "data": model.ejecutar("get_user_qrs", session['user_cedula'])})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@qr_bp.route('/<int:qr_id>', methods=['GET'])
def get_one(qr_id):
    try:
        qr = model.ejecutar("get_by_id", qr_id)
        if qr:
            return jsonify({"status": "success", "data": qr})
        return jsonify({"status": "error", "message": "QR no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@qr_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        data['usuario_cedula'] = session['user_cedula']
        qr_id = model.ejecutar("create_qr", data)
        return jsonify({"status": "success", "message": "QR registrado correctamente.", "id": qr_id})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@qr_bp.route('/<int:qr_id>', methods=['PUT'])
def update(qr_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        model.ejecutar("update_qr", qr_id, data)
        return jsonify({"status": "success", "message": "QR modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@qr_bp.route('/<int:qr_id>', methods=['DELETE'])
def delete(qr_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.ejecutar("soft_delete", qr_id)


        return jsonify({"status": "success", "message": "QR eliminado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@qr_bp.route('/scan/<int:qr_id>', methods=['GET'])
def scan(qr_id):
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = model.ejecutar("get_qr_data", qr_id)
        if data:
            return jsonify({"status": "success", "data": data})
        return jsonify({"status": "error", "message": "QR no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@qr_bp.route('/<int:qr_id>/image', methods=['GET'])
def generate_image(qr_id):
    try:
        qr_obj = model.ejecutar("get_by_id", qr_id)
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
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
