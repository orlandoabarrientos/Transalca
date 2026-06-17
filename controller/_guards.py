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


def is_admin():
    return 'Administrador' in (session.get('roles') or [])


def has_module_permission(modulo, accion='leer'):
    if 'user_id' not in session:
        return False
    if is_admin():
        return True
    perms = (session.get('permisos') or {}).get(modulo) or {}
    return bool(perms.get(accion))


def require_module(modulo, accion='leer'):
    login = require_login()
    if login:
        return login
    if not has_module_permission(modulo, accion):
        return deny()
    return None
