"""
Rates Controller
Provides BCV and Binance P2P exchange rates
"""
from flask import Blueprint, jsonify
import time
import threading
import logging

logger = logging.getLogger(__name__)
rates_bp = Blueprint('rates', __name__)


_cache = {
    "data": None,
    "timestamp": 0,
    "lock": threading.Lock()
}
CACHE_TTL = 300  


def _fetch_rates():
    """Fetch rates from both BCV and Binance with error handling."""
    result = {
        "bcv": {"usd": 0, "eur": 0, "error": None},
        "binance": {"usdt_ves": 0, "error": None},
        "timestamp": time.time()
    }

    
    try:
        from services.bcv_scraper import get_bcv_rates
        bcv = get_bcv_rates(verify=False)
        result["bcv"]["usd"] = round(bcv.get("usd", 0), 4)
        result["bcv"]["eur"] = round(bcv.get("eur", 0), 4)
    except Exception as e:
        logger.error("Error BCV: %s", e)
        result["bcv"]["error"] = str(e)

    
    try:
        from services.binance_rates import get_usdt_rate_ves
        rate = get_usdt_rate_ves()
        result["binance"]["usdt_ves"] = round(rate, 2)
    except Exception as e:
        logger.error("Error Binance: %s", e)
        result["binance"]["error"] = str(e)

    return result


@rates_bp.route('/', methods=['GET'])
def get_rates():
    """Get current exchange rates (cached 5 min)."""
    try:
        now = time.time()
        with _cache["lock"]:
            if _cache["data"] and (now - _cache["timestamp"]) < CACHE_TTL:
                return jsonify({"status": "success", "data": _cache["data"], "cached": True})
            
            rates = _fetch_rates()
            _cache["data"] = rates
            _cache["timestamp"] = now

        return jsonify({"status": "success", "data": rates, "cached": False})

    except Exception as e:
        logger.error("Error in rates endpoint: %s", e)
        return jsonify({"status": "error", "message": "Error obteniendo tasas de cambio"}), 500


@rates_bp.route('/bcv', methods=['GET'])
def get_bcv_only():
    """Get only BCV rates."""
    try:
        from services.bcv_scraper import get_bcv_rates
        bcv = get_bcv_rates(verify=False)
        return jsonify({
            "status": "success",
            "data": {
                "usd": round(bcv.get("usd", 0), 4),
                "eur": round(bcv.get("eur", 0), 4),
                "source": "BCV"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502


@rates_bp.route('/binance', methods=['GET'])
def get_binance_only():
    """Get only Binance P2P rate."""
    try:
        from services.binance_rates import get_usdt_rate_ves
        rate = get_usdt_rate_ves()
        return jsonify({
            "status": "success",
            "data": {
                "usdt_ves": round(rate, 2),
                "source": "Binance P2P"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502
