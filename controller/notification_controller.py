from flask import Blueprint, request, jsonify, session
from model.notification_model import NotificationModel

notification_bp = Blueprint('notification_bp', __name__)
model = NotificationModel()


def sync_credit_notifications_if_needed():
    if session.get('user_tipo') not in ('empleado', 'admin', 'vendedor', 'soporte'):
        return
    try:
        from model.credit_model import CreditModel
        CreditModel().sync_credit_statuses()
    except Exception:
        pass


@notification_bp.route('/', methods=['GET'])
def get_notifications():
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        sync_credit_notifications_if_needed()
        return jsonify({"status": "success", "data": model.get_by_user(uid, session.get('user_cedula'))})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@notification_bp.route('/unread', methods=['GET'])
def get_unread():
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        cedula = session.get('user_cedula')
        sync_credit_notifications_if_needed()
        return jsonify({"status": "success",
                        "data": model.get_unread(uid, cedula),
                        "count": model.count_unread(uid, cedula)})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@notification_bp.route('/count', methods=['GET'])
def count_unread():
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"status": "success", "count": 0})
        sync_credit_notifications_if_needed()
        return jsonify({"status": "success", "count": model.count_unread(uid, session.get('user_cedula'))})
    except Exception as e:
        return jsonify({"status": "success", "count": 0})


@notification_bp.route('/<int:nid>/read', methods=['PUT'])
def mark_read(nid):
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.mark_read(nid, uid, session.get('user_cedula'))
        return jsonify({"status": "success", "message": "Marcada como leída"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@notification_bp.route('/read-all', methods=['PUT'])
def mark_all_read():
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.mark_all_read(uid, session.get('user_cedula'))
        return jsonify({"status": "success", "message": "Todas marcadas como leídas"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@notification_bp.route('/<int:nid>', methods=['DELETE'])
def delete_notification(nid):
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        model.delete_notification(nid, uid, session.get('user_cedula'))
        return jsonify({"status": "success", "message": "Notificación eliminada"})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
