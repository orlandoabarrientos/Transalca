import logging

from flask import Blueprint, request, jsonify, session, send_file
from model.backup_model import BackupModel


backup_bp = Blueprint('backup', __name__)
model = BackupModel()
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _can_restore():
    if 'user_id' not in session:
        return False
    if 'Administrador' in (session.get('roles') or []):
        return True
    return bool((session.get('permisos') or {}).get('respaldos', {}).get('actualizar'))


def _can_create():
    if 'user_id' not in session:
        return False
    if 'Administrador' in (session.get('roles') or []):
        return True
    return bool((session.get('permisos') or {}).get('respaldos', {}).get('crear'))


@backup_bp.route('/', methods=['GET'])
def list_backups():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        try:
            model.ejecutar("cleanup_old_backups")
        except Exception:
            logger.exception("No se pudo limpiar respaldos antiguos antes de listar.")
        return jsonify({"status": "success", "data": model.ejecutar("list_backups")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@backup_bp.route('/create', methods=['POST'])
def create_backup():
    try:
        if not _can_create():
            return jsonify({"status": "error", "message": "No autorizado para crear respaldos."}), 403
        files = model.ejecutar("create_backup")
        if files:


            model.ejecutar("log_event", session['user_id'], 'CREAR', 'RESPALDOS', f"Respaldo creado: {', '.join([f['filename'] for f in files])}", request.remote_addr, 1)
            return jsonify({"status": "success", "message": "Respaldo creado", "data": files})
        return jsonify({"status": "error", "message": "Error al crear respaldo"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@backup_bp.route('/download/<filename>', methods=['GET'])
def download(filename):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        filepath = model.ejecutar("get_backup_path", filename)
        if filepath:
            return send_file(filepath, as_attachment=True)
        return jsonify({"status": "error", "message": "Archivo no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@backup_bp.route('/delete/<filename>', methods=['DELETE'])
def delete(filename):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if model.ejecutar("delete_backup", filename):


            model.ejecutar("log_event", session['user_id'], 'ELIMINAR', 'RESPALDOS', f"Respaldo eliminado: {filename}", request.remote_addr)
            return jsonify({"status": "success", "message": "Respaldo eliminado"})
        return jsonify({"status": "error", "message": "Archivo no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@backup_bp.route('/upload', methods=['POST'])
def upload_backup():
    try:
        if not _can_restore():
            return jsonify({"status": "error", "message": "No autorizado para instalar respaldos."}), 403
        file = request.files.get('backup')
        if not file or not file.filename:
            return jsonify({"status": "error", "message": "Debe seleccionar un archivo de respaldo."}), 400
        content = file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            return jsonify({"status": "error", "message": "El archivo supera el tamaño permitido."}), 400
        filename = model.ejecutar("save_uploaded_backup", file.filename, content)
        model.ejecutar("log_event", session['user_id'], 'CREAR', 'RESPALDOS',
            f"Respaldo importado: {filename}", request.remote_addr, 0)
        return jsonify({"status": "success", "message": "Respaldo importado correctamente.", "filename": filename})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo importar el respaldo."}), 500


@backup_bp.route('/restore', methods=['POST'])
def restore_backup():
    try:
        if not _can_restore():
            return jsonify({"status": "error", "message": "No autorizado para restaurar respaldos."}), 403
        data = request.get_json() or {}
        filename = (data.get('filename') or '').strip()
        if not filename:
            return jsonify({"status": "error", "message": "Debe seleccionar un respaldo para restaurar."}), 400
        result = model.ejecutar("restore_backup", filename)
        model.ejecutar("log_event", session['user_id'], 'ACTUALIZAR', 'RESPALDOS',
            f"Respaldo restaurado: {filename} (BD {result.get('database')})", request.remote_addr, 0)
        return jsonify({
            "status": "success",
            "message": "Respaldo restaurado correctamente. Se creo un respaldo de seguridad del estado anterior.",
            "data": result
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo restaurar el respaldo. El estado actual no fue modificado por completo; use el respaldo de seguridad si es necesario."}), 500


@backup_bp.route('/restore-latest', methods=['POST'])
def restore_latest():
    try:
        if not _can_restore():
            return jsonify({"status": "error", "message": "No autorizado para restaurar respaldos."}), 403
        result = model.ejecutar("restore_latest_backup")
        nombres = ', '.join(item["filename"] for item in result.get("restored", []))
        model.ejecutar("log_event", session['user_id'], 'ACTUALIZAR', 'RESPALDOS',
            f"Ultimo respaldo restaurado: {nombres}", request.remote_addr, 0)
        return jsonify({
            "status": "success",
            "message": "Último respaldo restaurado correctamente. Se creó un respaldo de seguridad del estado anterior.",
            "data": result
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception:
        logger.exception("Error restaurando el ultimo respaldo.")
        return jsonify({"status": "error", "message": "No se pudo restaurar el último respaldo. Use el respaldo de seguridad si es necesario."}), 500
