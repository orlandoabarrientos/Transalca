from flask import Blueprint, request, jsonify, session, send_file
from model.scanner_model import ScannerModel
# from model.bitacora_model import BitacoraModel
import qrcode
import io


scanner_bp = Blueprint('scanner', __name__)
model = ScannerModel()
# bitacora = BitacoraModel()


def _is_employee():
    return session.get('user_tipo') in ['empleado', 'admin', 'vendedor', 'mecanico', 'soporte']


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

        source = data.get('source') or ''
        if source == 'client':
            result = model.process_scan_for_client(qr, session.get('user_cedula'))
        elif _is_employee():
            result = model.process_scan_for_employee(qr)
        elif session.get('user_tipo') == 'cliente':
            result = model.process_scan_for_client(qr, session.get('user_cedula'))
        else:
            return jsonify({"status": "error", "message": "Tipo de usuario no permitido"}), 403

        # bitacora.log_action(session['user_id'], 'LEER', 'ESCANER',
            # f"QR escaneado ID: {qr['id']} | Modo: {result.get('mode', 'N/A')}", request.remote_addr)

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
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@scanner_bp.route('/table-qrs', methods=['GET'])
def get_table_qrs():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        return jsonify({"status": "success", "data": model.get_table_qrs()})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


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

        # bitacora.log_action(session['user_id'], 'CREAR', 'ESCANER',
            # f"QR de mesa creado/reutilizado ID: {result['id']}", request.remote_addr)

        msg = 'QR de mesa creado' if result.get('created') else 'Ya existe un QR activo para esa mesa'
        return jsonify({"status": "success", "message": msg, "data": result})
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


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

        # bitacora.log_action(session['user_id'], 'MODIFICAR', 'ESCANER',
            # f"Accion actualizada en QR de mesa ID: {qr_id}", request.remote_addr)

        return jsonify({"status": "success", "message": "Accion actualizada", "data": qr})
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@scanner_bp.route('/promotions', methods=['GET'])
def scanner_promotions():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        return jsonify({"status": "success", "data": model.get_active_promotions()})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


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

        if str(order.get('estado') or '').lower() not in ('aprobada', 'aprobado', 'verificado', 'pagado'):
            return jsonify({"status": "error", "message": "El QR de factura solo esta disponible cuando el pago esta aprobado."}), 403

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
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@scanner_bp.route('/solicitar-validacion', methods=['POST'])
def solicitar_validacion():
    try:
        if 'user_cedula' not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesion para solicitar validacion"}), 401
        
        data = request.get_json() or {}
        orden_id = data.get('orden_id')
        tipo = data.get('tipo', 'validar_pago')

        if not orden_id:
            return jsonify({"status": "error", "message": "ID de orden requerido"}), 400

        orden = model.fetch_one("transalca", "SELECT * FROM ordenes_venta WHERE id = %s", (orden_id,))
        if not orden:
            return jsonify({"status": "error", "message": "La orden no existe"}), 404
        if orden['cliente_cedula'] != session['user_cedula']:
            return jsonify({"status": "error", "message": "No autorizado para esta orden"}), 403

        existing = model.fetch_one("transalca",
            "SELECT id FROM solicitudes_validacion WHERE orden_venta_id = %s AND estado = 'pendiente'",
            (orden_id,))
        if existing:
            return jsonify({"status": "success", "message": "Ya existe una solicitud de validacion pendiente."})

        model.insert("transalca",
            "INSERT INTO solicitudes_validacion (tipo, orden_venta_id, cliente_cedula, estado) VALUES (%s, %s, %s, 'pendiente')",
            (tipo, orden_id, session['user_cedula']))

        return jsonify({"status": "success", "message": "Solicitud de validacion enviada al administrador."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo procesar la solicitud"}), 500


@scanner_bp.route('/solicitudes-pendientes', methods=['GET'])
def get_solicitudes_pendientes():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        reqs = model.fetch_all("transalca",
            "SELECT * FROM solicitudes_validacion WHERE estado = 'pendiente' ORDER BY created_at ASC")

        result = []
        for r in reqs:
            orden = model.get_order_full(r['orden_venta_id'])
            if not orden:
                continue
            
            comp = model.fetch_one("transalca", "SELECT imagen_url FROM comprobantes_pago WHERE orden_venta_id = %s", (r['orden_venta_id'],))
            comprobante_img = comp['imagen_url'] if comp else None

            client = orden.get('cliente') or {}

            result.append({
                "id": r['id'],
                "tipo": r['tipo'],
                "orden_venta_id": r['orden_venta_id'],
                "cliente_cedula": r['cliente_cedula'],
                "cliente_nombre": f"{client.get('nombre', '')} {client.get('apellido', '')}",
                "cliente_email": client.get('email', ''),
                "cliente_telefono": client.get('telefono', ''),
                "total": float(orden.get('total', 0)),
                "estado_orden": orden.get('estado', ''),
                "fecha_orden": str(orden.get('fecha', '')),
                "metodo_pago": orden.get('metodo_pago_nombre', ''),
                "comprobante_img": comprobante_img,
                "detalles": orden.get('detalles', []),
                "created_at": r['created_at'].isoformat() if hasattr(r['created_at'], 'isoformat') else str(r['created_at'])
            })

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudieron obtener las solicitudes"}), 500


@scanner_bp.route('/responder-validacion', methods=['POST'])
def responder_validacion():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if not _is_employee():
            return jsonify({"status": "error", "message": "Solo empleados"}), 403

        data = request.get_json() or {}
        solicitud_id = data.get('solicitud_id')
        respuesta = data.get('respuesta')

        if not solicitud_id or not respuesta:
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400

        req = model.fetch_one("transalca", "SELECT * FROM solicitudes_validacion WHERE id = %s", (solicitud_id,))
        if not req:
            return jsonify({"status": "error", "message": "Solicitud no encontrada"}), 404

        revisado_por = session['user_cedula']
        estado_solicitud = 'aprobada' if respuesta == 'aprobar' else 'rechazada'

        model.update("transalca", "UPDATE solicitudes_validacion SET estado = %s WHERE id = %s", (estado_solicitud, solicitud_id))

        orden_id = req['orden_venta_id']
        if respuesta == 'aprobar':
            model.update("transalca", "UPDATE ordenes_venta SET estado = 'aprobada' WHERE id = %s", (orden_id,))
            model.update("transalca", "UPDATE comprobantes_pago SET estado = 'verificado', revisado_por = %s WHERE orden_venta_id = %s", (revisado_por, orden_id))
            msg = "Validacion aprobada con exito."
        else:
            if req['tipo'] == 'validar_pago':
                model.update("transalca", "UPDATE ordenes_venta SET estado = 'rechazada' WHERE id = %s", (orden_id,))
                model.update("transalca", "UPDATE comprobantes_pago SET estado = 'rechazado', revisado_por = %s WHERE orden_venta_id = %s", (revisado_por, orden_id))
            msg = "Validacion rechazada."

        # bitacora.log_action(session['user_id'], 'MODIFICAR', 'ESCANER',
            # f"Solicitud validacion ID {solicitud_id} respondida como {respuesta}", request.remote_addr)

        return jsonify({"status": "success", "message": msg})
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al procesar respuesta"}), 500
