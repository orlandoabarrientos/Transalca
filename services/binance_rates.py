"""
Binance P2P Rate Fetcher
Gets USDT/VES median rate from Binance P2P market
"""
import logging
import requests

logger = logging.getLogger(__name__)


def _median(arr):
    """Calculate median of a list of numbers."""
    if not arr or len(arr) == 0:
        return 0
    s = sorted(arr)
    mid = len(s) // 2
    if len(s) % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def get_usdt_rate_ves(timeout=15) -> float:
    """Fetch USDT/VES median rate from Binance P2P."""
    try:
        response = requests.post(
            "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search",
            json={
                "page": 1,
                "rows": 20,
                "payTypes": [],
                "asset": "USDT",
                "tradeType": "BUY",
                "fiat": "VES"
            },
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )
        response.raise_for_status()
        data = response.json()

        raw = data.get("data", [])
        if not isinstance(raw, list):
            raw = []

        prices = []
        for item in raw:
            try:
                p = float(item.get("adv", {}).get("price", 0))
                if p > 0:
                    prices.append(p)
            except (ValueError, TypeError):
                continue

        if not prices:
            logger.warning("No prices found from Binance P2P")
            return 0

        unique = sorted(set(prices))
        return _median(unique)

    except requests.RequestException as exc:
        logger.error("Error fetching Binance P2P rate: %s", exc)
        return 0
    except Exception as exc:
        logger.error("Unexpected error in Binance rate fetch: %s", exc)
        return 0
