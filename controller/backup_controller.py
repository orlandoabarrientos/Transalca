from flask import Blueprint, request, jsonify, session, send_file
from model.backup_model import BackupModel
from model.bitacora_model import BitacoraModel

backup_bp = Blueprint('backup', __name__)
model = BackupModel()
bitacora = BitacoraModel()


@backup_bp.route('/', methods=['GET'])
def list_backups():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.list_backups()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@backup_bp.route('/create', methods=['POST'])
def create_backup():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        files = model.create_backup()
        if files:
            bitacora.log_action(session['user_id'], 'CREAR', 'RESPALDOS',
                f"Respaldo creado: {', '.join([f['filename'] for f in files])}", request.remote_addr)
            return jsonify({"status": "success", "message": "Respaldo creado", "data": files})
        return jsonify({"status": "error", "message": "Error al crear respaldo"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@backup_bp.route('/download/<filename>', methods=['GET'])
def download(filename):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        filepath = model.get_backup_path(filename)
        if filepath:
            return send_file(filepath, as_attachment=True)
        return jsonify({"status": "error", "message": "Archivo no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@backup_bp.route('/delete/<filename>', methods=['DELETE'])
def delete(filename):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if model.delete_backup(filename):
            bitacora.log_action(session['user_id'], 'ELIMINAR', 'RESPALDOS',
                f"Respaldo eliminado: {filename}", request.remote_addr)
            return jsonify({"status": "success", "message": "Respaldo eliminado"})
        return jsonify({"status": "error", "message": "Archivo no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
