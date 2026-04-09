"""
BCV Exchange Rate Scraper
Adapted from API BCV project - webscraping bcv.org.ve
"""
import logging
import re
from typing import Dict

import requests
from bs4 import BeautifulSoup

BCV_URL = "https://www.bcv.org.ve"
_CURRENCY_KEYWORDS = {
    "usd": ("dólar", "dolar", "usd", "estados unidos"),
    "eur": ("euro", "eur"),
}

logger = logging.getLogger(__name__)


class ScraperError(RuntimeError):
    """Raised when the BCV rates cannot be retrieved."""


def _normalize_number(value: str) -> float:
    match = re.search(r"(\d[\d.,]*)", value)
    if not match:
        raise ValueError(f"No numeric value found in '{value}'")
    normalized = match.group(1).replace(".", "").replace(",", ".")
    return float(normalized)


def _match_currency(container_text: str) -> set:
    text = container_text.lower()
    matches = set()
    for code, keywords in _CURRENCY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matches.add(code)
    return matches


def _extract_from_dom(soup: BeautifulSoup) -> Dict[str, float]:
    rates = {}
    for container in soup.select("div.centrado"):
        label_text = container.get_text(" ", strip=True)
        if not label_text:
            continue
        value_el = container.find("strong")
        if not value_el:
            continue
        try:
            value = _normalize_number(value_el.get_text(strip=True))
        except ValueError:
            continue
        for code in _match_currency(label_text):
            rates.setdefault(code, value)
    return rates


def _extract_by_currency_code(soup: BeautifulSoup) -> Dict[str, float]:
    rates = {}
    for code in _CURRENCY_KEYWORDS:
        label = code.upper()
        for node in soup.find_all(string=True):
            if not node:
                continue
            if node.strip().upper() != label:
                continue
            parent = node.parent
            strong = parent.find_next("strong") if parent else None
            if not strong:
                continue
            try:
                value = _normalize_number(strong.get_text(strip=True))
            except ValueError:
                continue
            rates.setdefault(code, value)
            break
    return rates


def _fallback_by_index(soup: BeautifulSoup, rates: Dict[str, float]) -> None:
    if all(code in rates for code in _CURRENCY_KEYWORDS):
        return
    strong_nodes = [node for node in soup.select("div.centrado strong")]
    if len(strong_nodes) >= 6:
        try:
            usd_value = _normalize_number(strong_nodes[4].get_text(strip=True))
            rates.setdefault("usd", usd_value)
        except (IndexError, ValueError):
            pass
        try:
            eur_value = _normalize_number(strong_nodes[5].get_text(strip=True))
            rates.setdefault("eur", eur_value)
        except (IndexError, ValueError):
            pass


def get_bcv_rates(targets=None, timeout=10, verify=False) -> Dict[str, float]:
    """Fetch exchange rates from BCV website."""
    try:
        response = requests.get(BCV_URL, timeout=timeout, verify=verify)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error fetching BCV homepage: %s", exc)
        raise ScraperError("No se pudo obtener la pagina del BCV") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    rates = _extract_from_dom(soup)
    rates.update(_extract_by_currency_code(soup))
    _fallback_by_index(soup, rates)

    requested = set(code.lower() for code in (targets or _CURRENCY_KEYWORDS.keys()))
    missing = [code for code in requested if code not in rates]
    if missing:
        raise ScraperError(f"No se encontraron las tasas para: {', '.join(missing)}")

    return {code: rates[code] for code in requested}
