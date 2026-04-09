from flask import Blueprint, request, jsonify, session
from model.stats_model import StatsModel

stats_bp = Blueprint('stats', __name__)
model = StatsModel()

@stats_bp.route('/revenue', methods=['GET'])
def revenue_timeline():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        days = int(request.args.get('days', 30))
        return jsonify({"status": "success", "data": model.get_revenue_timeline(days)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@stats_bp.route('/products', methods=['GET'])
def top_products():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        limit = int(request.args.get('limit', 5))
        return jsonify({"status": "success", "data": model.get_top_performing_products(limit)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@stats_bp.route('/status', methods=['GET'])
def order_status():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.get_order_status_distribution()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@stats_bp.route('/payments', methods=['GET'])
def payment_methods():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        return jsonify({"status": "success", "data": model.get_payments_distribution()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
