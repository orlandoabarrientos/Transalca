from flask import Blueprint, request, jsonify, session, send_file
from model.scanner_model import ScannerModel
from model.bitacora_model import BitacoraModel
import qrcode
import io


scanner_bp = Blueprint('scanner', __name__)
model = ScannerModel()
bitacora = BitacoraModel()


def _is_employee():
    return session.get('user_tipo') in ['empleado', 'admin']


@scanner_bp.route('/scan', methods=['POST'])
def scan_qr():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion para escanear"}), 401

        data = request.get_json() or {}
        raw = data.get('raw') or data.get('codigo') or ''

        qr, error = model.resolve_qr_from_raw(raw)
        if error:
            return jsonify({"status": "error", "message": error}), 400

        if _is_employee():
            result = model.process_scan_for_employee(qr)
        elif session.get('user_tipo') == 'cliente':
            result = model.process_scan_for_client(qr, session.get('user_cedula'))
        else:
            return jsonify({"status": "error", "message": "Tipo de usuario no permitido"}), 403

        bitacora.log_action(session['user_id'], 'LEER', 'ESCANER',
            f"QR escaneado ID: {qr['id']} | Modo: {result.get('mode', 'N/A')}", request.remote_addr)

        return jsonify({
            "status": "success",
            "message": result.get('message', 'QR procesado'),
            "data": {
                "qr_id": qr['id'],
                "qr_tipo": qr.get('tipo'),
                "qr_utilidad": qr.get('utilidad'),
                **result
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@scanner_bp.route('/table-qrs', methods=['GET'])
def get_table_qrs():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        return jsonify({"status": "success", "data": model.get_table_qrs()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@scanner_bp.route('/table-qrs', methods=['POST'])
def create_table_qr():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        data = request.get_json() or {}
        codigo_mesa = data.get('codigo_mesa') or data.get('codigo')
        if not codigo_mesa:
            return jsonify({"status": "error", "message": "Codigo de mesa requerido"}), 400

        result = model.create_table_qr(session.get('user_cedula'), codigo_mesa)

        bitacora.log_action(session['user_id'], 'CREAR', 'ESCANER',
            f"QR de mesa creado/reutilizado ID: {result['id']}", request.remote_addr)

        msg = 'QR de mesa creado' if result.get('created') else 'Ya existe un QR activo para esa mesa'
        return jsonify({"status": "success", "message": msg, "data": result})
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@scanner_bp.route('/table-qrs/<int:qr_id>/action', methods=['PUT'])
def update_table_qr_action(qr_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        data = request.get_json() or {}
        accion = data.get('accion')
        promocion_id = data.get('promocion_id')

        qr = model.set_table_qr_action(qr_id, accion, promocion_id)

        bitacora.log_action(session['user_id'], 'MODIFICAR', 'ESCANER',
            f"Accion actualizada en QR de mesa ID: {qr_id}", request.remote_addr)

        return jsonify({"status": "success", "message": "Accion actualizada", "data": qr})
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@scanner_bp.route('/promotions', methods=['GET'])
def scanner_promotions():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        return jsonify({"status": "success", "data": model.get_active_promotions()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@scanner_bp.route('/invoice/<int:order_id>/image', methods=['GET'])
def invoice_qr_image(order_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401

        order = model.get_order_full(order_id)
        if not order:
            return jsonify({"status": "error", "message": "Orden no encontrada"}), 404

        if session.get('user_tipo') == 'cliente' and order.get('cliente_cedula') != session.get('user_cedula'):
            return jsonify({"status": "error", "message": "Sin permisos para esta factura"}), 403

        qr_obj = model.ensure_invoice_qr(order_id)
        if not qr_obj:
            return jsonify({"status": "error", "message": "No se pudo generar QR de factura"}), 500

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        contenido = request.host_url.rstrip('/') + f"/scanner?qr={qr_obj['id']}"
        qr.add_data(contenido)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return send_file(img_byte_arr, mimetype='image/png')
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
