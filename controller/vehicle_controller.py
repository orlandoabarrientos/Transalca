from flask import Blueprint, request, jsonify, session
from model.vehicle_model import VehicleModel
from controller._guards import can_access_client, deny, is_employee, require_login
from model.vehicle_title_ocr_model import OCRError, parse_vehicle_title_image
from config.validation import ValidationError
import os
import time
from werkzeug.utils import secure_filename

vehicle_bp = Blueprint('vehicle_bp', __name__)
model = VehicleModel()

UPLOAD_FOLDER = 'public/assets/images'
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'jfif', 'bmp', 'gif', 'heic', 'heif'}
ALLOWED_MIME = {
    'image/png',
    'image/jpeg',
    'image/webp',
    'image/gif',
    'image/bmp',
    'image/heic',
    'image/heif'
}


def _get_ext(filename):
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower().strip()


def _guess_ext_from_mime(mime):
    m = (mime or '').lower().strip()
    mapping = {
        'image/png': 'png',
        'image/jpeg': 'jpg',
        'image/webp': 'webp',
        'image/gif': 'gif',
        'image/bmp': 'bmp',
        'image/heic': 'heic',
        'image/heif': 'heif'
    }
    return mapping.get(m, '')


def allowed_file(file_obj):
    ext = _get_ext(file_obj.filename)
    if ext in ALLOWED_EXT:
        return True
    mime = (file_obj.mimetype or '').lower().strip()
    if mime in ALLOWED_MIME:
        return True
    return False


def load_owned_vehicle(vid):
    auth = require_login()
    if auth:
        return None, auth
    vehicle = model.ejecutar("get_by_id", vid)
    if not vehicle:
        return None, (jsonify({"status": "error", "message": "Vehiculo no encontrado"}), 404)
    if is_employee():
        return vehicle, None
    if is_client():
        linked_clients = vehicle.get('cliente_cedula', '').split(',')
        if session.get('user_cedula') not in linked_clients:
            return None, deny()
    return vehicle, None


@vehicle_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return jsonify({"status": "success", "data": model.ejecutar("get_by_cliente", session.get('user_cedula'))})
        q = request.args.get('q')
        if q:
            return jsonify({"status": "success", "data": model.ejecutar("search", q)})
        cliente = request.args.get('cliente')
        if cliente:
            return jsonify({"status": "success", "data": model.ejecutar("get_by_cliente", cliente)})
        return jsonify({"status": "success", "data": model.ejecutar("get_all")})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/<path:vid>', methods=['GET'])
def get_one(vid):
    try:
        v, error = load_owned_vehicle(vid)
        if error:
            return error
        v['cauchos'] = model.ejecutar("get_cauchos", vid)
        v['km_history'] = model.ejecutar("get_km_history", vid)
        return jsonify({"status": "success", "data": v})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        data = request.get_json() or {}
        clean = model.ejecutar("validate", data)
        cliente_cedula = (data.get('cliente_cedula') or '').strip()
        if not cliente_cedula:
            raise ValidationError({'cliente_cedula': 'No se pudo identificar el cliente.'})
        if not can_access_client(cliente_cedula):
            return deny()
        existing = model.ejecutar("get_by_placa", clean['placa'])
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'placa': 'Esta placa ya esta registrada.'})
            model.ejecutar("update_vehicle", existing['placa'], data)
            model.ejecutar("reactivar", existing['placa'])
            return jsonify({"status": "success", "message": "Vehiculo registrado correctamente.", "id": existing['placa']}), 201
        vid = model.ejecutar("create", {**data, 'cliente_cedula': cliente_cedula})
        return jsonify({"status": "success", "message": "Vehiculo registrado correctamente.", "id": vid}), 201
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/<path:vid>', methods=['PUT'])
def update(vid):
    try:
        _, error = load_owned_vehicle(vid)
        if error:
            return error
        data = request.get_json() or {}
        model.ejecutar("update_vehicle", vid, data)
        return jsonify({"status": "success", "message": "Vehiculo modificado correctamente."})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/<path:vid>/km', methods=['PUT'])
def update_km(vid):
    try:
        _, error = load_owned_vehicle(vid)
        if error:
            return error
        data = request.get_json()
        km = data.get('kilometraje')
        if km is None:
            return jsonify({"status": "error", "message": "Kilometraje requerido"}), 400
        if not model.ejecutar("update_kilometraje", vid, km):
            return jsonify({"status": "error", "message": "Kilometraje no puede ser menor al actual"}), 400
        return jsonify({"status": "success", "message": "Kilometraje actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/<path:vid>', methods=['DELETE'])
def delete(vid):
    try:
        _, error = load_owned_vehicle(vid)
        if error:
            return error
        model.ejecutar("soft_delete", vid)
        return jsonify({"status": "success", "message": "Vehiculo eliminado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/<path:vid>/carnet', methods=['POST'])
def upload_carnet(vid):
    try:
        _, error = load_owned_vehicle(vid)
        if error:
            return error
        if 'imagen' not in request.files:
            return jsonify({"status": "error", "message": "No se envio imagen"}), 400
        file = request.files['imagen']
        if not file or not allowed_file(file):
            return jsonify({"status": "error", "message": "Archivo no valido. Debe ser una imagen"}), 400
        ext = _get_ext(file.filename)
        if ext not in ALLOWED_EXT:
            ext = _guess_ext_from_mime(file.mimetype)
        if ext not in ALLOWED_EXT:
            ext = 'jpg'
        filename = secure_filename(f"carnet_{vid}_{int(time.time() * 1000)}.{ext}")
        if not filename:
            filename = f"carnet_{vid}_{int(time.time() * 1000)}.jpg"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        model.ejecutar("update_carnet_image", vid, filename)
        return jsonify({"status": "success", "message": "Titulo del vehiculo subido correctamente.", "filename": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/<path:vid>/cauchos', methods=['GET'])
def get_cauchos(vid):
    try:
        _, error = load_owned_vehicle(vid)
        if error:
            return error
        return jsonify({"status": "success", "data": model.ejecutar("get_cauchos", vid)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/<path:vid>/cauchos', methods=['POST'])
def add_caucho(vid):
    try:
        _, error = load_owned_vehicle(vid)
        if error:
            return error
        data = request.get_json() or {}
        cid = model.ejecutar("add_caucho", vid, data)
        return jsonify({"status": "success", "message": "Caucho registrado correctamente.", "id": cid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/scan-title', methods=['POST'])
def scan_title():
    try:
        auth = require_login()
        if auth:
            return auth
        if 'imagen' not in request.files:
            return jsonify({"status": "error", "message": "No se envio imagen"}), 400
        file = request.files['imagen']
        if not file or not allowed_file(file):
            return jsonify({"status": "error", "message": "Archivo no valido. Debe ser una imagen"}), 400
        extracted, raw_text = parse_vehicle_title_image(file)
        return jsonify({
            "status": "success",
            "message": "Documento escaneado correctamente.",
            "data": extracted,
            "raw_text": raw_text
        })
    except OCRError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/cauchos/<int:cid>', methods=['PUT'])
def update_caucho(cid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        model.ejecutar("update_caucho", cid, data)
        return jsonify({"status": "success", "message": "Caucho modificado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@vehicle_bp.route('/cauchos/<int:cid>', methods=['DELETE'])
def delete_caucho(cid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        model.ejecutar("delete_caucho", cid)
        return jsonify({"status": "success", "message": "Caucho eliminado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
