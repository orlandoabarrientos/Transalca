from flask import Blueprint, request, jsonify
from model.pricing_model import PricingModel
from model.bcv_rate_model import get_bcv_rates, ScraperError
from model.binance_rate_model import get_usdt_rate_ves
from controller._guards import deny, is_employee, require_login

pricing_bp = Blueprint('pricing_bp', __name__)
model = PricingModel()


@pricing_bp.route('/rates', methods=['GET'])
def get_rates():
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_rates")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@pricing_bp.route('/rates/active', methods=['GET'])
def get_active_rate():
    try:
        rate = model.ejecutar("get_active_rate")
        if not rate:
            return jsonify({"status": "error", "message": "Sin tasa disponible."}), 404
        return jsonify({"status": "success", "data": rate})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@pricing_bp.route('/rates/manual', methods=['POST'])
def save_manual_rate():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        if not data or not data.get('monto'):
            return jsonify({"status": "error", "message": "Monto requerido."}), 400
        model.ejecutar("save_rate", data.get('tipo', 'interna'), float(data['monto']), data.get('fuente', 'Manual admin'))
        return jsonify({"status": "success", "message": "Tasa guardada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@pricing_bp.route('/rates/scrape', methods=['POST'])
def scrape_rates():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        results = {}
        try:
            bcv = get_bcv_rates(targets=['usd'])
            bcv_rate = bcv.get('usd', 0)
            if bcv_rate > 0:
                if model.ejecutar("should_update_rate", bcv_rate, 'bcv'):
                    model.ejecutar("save_rate", 'bcv', bcv_rate, 'BCV automatico')
                    results['bcv'] = {'monto': bcv_rate, 'updated': True}
                else:
                    results['bcv'] = {'monto': bcv_rate, 'updated': False, 'reason': 'Dentro de banda'}
        except ScraperError:
            results['bcv'] = {'error': "No se pudo consultar la tasa BCV."}
        try:
            usdt_rate = get_usdt_rate_ves()
            if usdt_rate > 0:
                if model.ejecutar("should_update_rate", usdt_rate, 'usdt'):
                    model.ejecutar("save_rate", 'usdt', usdt_rate, 'Binance P2P automatico')
                    results['usdt'] = {'monto': usdt_rate, 'updated': True}
                else:
                    results['usdt'] = {'monto': usdt_rate, 'updated': False, 'reason': 'Dentro de banda'}
        except Exception:
            results['usdt'] = {'error': "No se pudo consultar la tasa USDT."}
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@pricing_bp.route('/calculate', methods=['POST'])
def calculate_price():
    try:
        data = request.get_json()
        precio_usd = data.get('precio_usd')
        if precio_usd is None:
            return jsonify({"status": "error", "message": "Precio USD requerido."}), 400
        result = model.ejecutar("calculate_price_bs", precio_usd)
        if not result:
            return jsonify({"status": "error", "message": "Sin tasa disponible."}), 404
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@pricing_bp.route('/settings', methods=['GET'])
def get_settings():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        return jsonify({"status": "success", "data": model.ejecutar("get_all_settings")})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500


@pricing_bp.route('/settings', methods=['PUT'])
def update_settings():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Datos requeridos."}), 400
        for k, v in data.items():
            model.ejecutar("update_setting", k, str(v))
        return jsonify({"status": "success", "message": "Configuracion modificada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "No se pudo completar la solicitud."}), 500
