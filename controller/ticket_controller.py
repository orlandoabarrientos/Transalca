from flask import Blueprint, request, jsonify, session
from model.ticket_model import TicketModel
from model.notification_model import NotificationModel
from model.connection import Connection
from controller._guards import can_access_client, deny, is_employee, require_login
from config.constants import ESTADOS_TICKET, PRIORIDADES_TICKET, validate_choice

ticket_bp = Blueprint('ticket_bp', __name__)
model = TicketModel()
notif_model = NotificationModel()


@ticket_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        estado = request.args.get('estado')
        prioridad = request.args.get('prioridad')
        cliente = request.args.get('cliente')
        if estado:
            validate_choice(estado, ESTADOS_TICKET, 'estado')
        if prioridad:
            validate_choice(prioridad, PRIORIDADES_TICKET, 'prioridad')
        if not is_employee():
            return jsonify({"status": "success", "data": model.get_by_cliente(session.get('user_cedula'))})
        if cliente:
            return jsonify({"status": "success", "data": model.get_by_cliente(cliente)})
        return jsonify({"status": "success", "data": model.get_all(estado, prioridad)})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@ticket_bp.route('/<int:tid>', methods=['GET'])
def get_one(tid):
    try:
        auth = require_login()
        if auth:
            return auth
        t = model.get_by_id(tid)
        if not t:
            return jsonify({"status": "error", "message": "Ticket no encontrado."}), 404
        if not can_access_client(t.get('cliente_cedula')):
            return deny()
        return jsonify({"status": "success", "data": t})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@ticket_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        data = request.get_json() or {}
        if not is_employee():
            data['cliente_cedula'] = session.get('user_cedula')
        if not data.get('cliente_cedula') or not data.get('asunto'):
            return jsonify({"status": "error", "message": "Datos incompletos."}), 400
        if not can_access_client(data.get('cliente_cedula')):
            return deny()
        validate_choice(data.get('prioridad', 'media'), PRIORIDADES_TICKET, 'prioridad')
        tid = model.create(data)
        return jsonify({"status": "success", "message": "Ticket registrado correctamente.", "id": tid}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@ticket_bp.route('/<int:tid>/status', methods=['PUT'])
def update_status(tid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        estado = data.get('estado')
        validate_choice(estado, ESTADOS_TICKET, 'estado')
        model.update_status(tid, estado)
        ticket = model.get_by_id(tid)
        if ticket:
            conn = Connection()
            user = conn.fetch_one("mantenimiento",
                "SELECT id FROM usuarios WHERE cedula=%s", (ticket['cliente_cedula'],))
            if user:
                notif_model.notify_ticket_update(user['id'], tid,
                    f"Su ticket '{ticket['asunto']}' cambio a: {estado}")
        return jsonify({"status": "success", "message": "Estado modificado correctamente."})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@ticket_bp.route('/<int:tid>/assign', methods=['PUT'])
def assign(tid):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json() or {}
        cedula = data.get('mecanico_cedula')
        if not cedula:
            return jsonify({"status": "error", "message": "Mecanico requerido."}), 400
        model.assign_to(tid, cedula)
        return jsonify({"status": "success", "message": "Ticket asignado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@ticket_bp.route('/<int:tid>/reply', methods=['POST'])
def reply(tid):
    try:
        auth = require_login()
        if auth:
            return auth
        ticket = model.get_by_id(tid)
        if not ticket:
            return jsonify({"status": "error", "message": "Ticket no encontrado."}), 404
        if not can_access_client(ticket.get('cliente_cedula')):
            return deny()
        data = request.get_json() or {}
        if not data.get('mensaje'):
            return jsonify({"status": "error", "message": "Mensaje requerido."}), 400
        autor_tipo = 'admin' if is_employee() else 'cliente'
        rid = model.add_response({
            'ticket_id': tid,
            'autor_id': session.get('user_id'),
            'autor_tipo': autor_tipo,
            'mensaje': data['mensaje'],
            'adjunto_url': data.get('adjunto_url')
        })
        return jsonify({"status": "success", "message": "Respuesta enviada correctamente.", "id": rid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@ticket_bp.route('/stats', methods=['GET'])
def stats():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.count_by_estado()})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
