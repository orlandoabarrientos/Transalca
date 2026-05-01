from flask import jsonify, session


def require_login():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "No autorizado"}), 401
    return None


def is_employee():
    return session.get('user_tipo') in ('empleado', 'admin', 'vendedor', 'mecanico', 'soporte')


def is_client():
    return session.get('user_tipo') == 'cliente'


def can_access_client(cedula):
    return is_employee() or (is_client() and session.get('user_cedula') == cedula)


def deny():
    return jsonify({"status": "error", "message": "No autorizado"}), 403
