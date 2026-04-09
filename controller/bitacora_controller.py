from flask import Blueprint, request, jsonify, session
from model.bitacora_model import BitacoraModel

bitacora_bp = Blueprint('bitacora', __name__)
model = BitacoraModel()


@bitacora_bp.route('/', methods=['GET'])
def get_all():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        logs = model.get_all(limit, offset)
        total = model.count_all()
        return jsonify({"status": "success", "data": logs, "total": total, "page": page})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bitacora_bp.route('/user/<int:user_id>', methods=['GET'])
def get_by_user(user_id):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.get_by_user(user_id)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bitacora_bp.route('/module/<modulo>', methods=['GET'])
def get_by_module(modulo):
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.get_by_module(modulo)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bitacora_bp.route('/search', methods=['GET'])
def search():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        query = request.args.get('q', '')
        return jsonify({"status": "success", "data": model.search(query)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bitacora_bp.route('/filter', methods=['GET'])
def filter_by_date():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        start = request.args.get('start', '')
        end = request.args.get('end', '')
        if start and end:
            return jsonify({"status": "success", "data": model.get_by_date_range(start, end)})
        return jsonify({"status": "error", "message": "Fechas requeridas"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
