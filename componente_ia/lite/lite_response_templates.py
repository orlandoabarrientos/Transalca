import math
import re
from .lite_entities import normalize

MISSING = "No tengo esa información configurada/verificada actualmente."
UNVERIFIED_VEHICLE = "No tengo esa compatibilidad verificada actualmente. Si me indicas la medida del caucho, puedo revisar disponibilidad y precios."
UNSUPPORTED = "Solo puedo ayudarte con información de Transalca, cauchos, servicios y vehículos registrados."
GREETING = "Puedo ayudarte con cauchos, precios, disponibilidad, servicios, métodos de pago, sucursales y algunos vehículos que tenemos verificados."
SYNTHETIC_NOTE = "Stock sintético registrado; no garantiza el conteo físico."

def public_text(value, limit=160):
    text = " ".join(str(value or "").split())
    if not text or normalize(text) in {"none", "null", "undefined", "por configurar", "configurar en panel admin", "todo config"}:
        return ""
    if re.search(r"(?i)password|passwd|secret|token|api[_ -]?key|\.env|<|>|://|[\w.+-]+@[\w.-]+", text):
        return ""
    return text[:limit]

def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else None
    except (TypeError, ValueError):
        return None

def money(value):
    result = number(value)
    return f"${result:.2f}" if result is not None else "precio no configurado / verificado"

def product_line(product):
    name = public_text(product.get("nombre")) or "Producto"
    price, stock = product.get("precio"), product.get("stock")
    sentence = f"{name} cuesta {money(price)}." if price is not None else f"{name}: precio no configurado / verificado."
    synthetic = product.get("inventory_provenance", {}).get("synthetic_inventory_mode", False)
    label = "Stock sintético registrado" if synthetic else "Stock disponible"
    sentence += f" {label}: {stock}." if stock is not None else " Stock no verificado."
    if product.get("sucursal"):
        sentence += f" Sucursal: {product['sucursal']}."
    return sentence
