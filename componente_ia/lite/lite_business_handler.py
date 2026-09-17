"""Only source-backed public business records, using existing retrievers."""

from .lite_entities import normalize
from .lite_response_templates import MISSING, money, public_text


class LiteBusinessHandler:
    def __init__(self, business_retriever, service_retriever, inventory_retriever):
        self.business = business_retriever
        self.services = service_retriever
        self.inventory = inventory_retriever

    def handle(self, intent, entities):
        if intent == "services":
            result = self.services.list_active()
            rows = [dict(item.data) for item in result.evidence
                    if item.verified and item.data.get("availability") == "active"] if result.available else []
            service = normalize(entities.get("service"))
            if service:
                rows = [row for row in rows if service in normalize(row.get("name"))]
            if entities.get("asks_price"):
                values = [f"{public_text(row.get('name'))}: {money(row.get('price'))}"
                          for row in rows if public_text(row.get("name")) and row.get("price_available") and row.get("price") is not None]
                return "; ".join(values[:6]) + "." if values else MISSING
            names = list(dict.fromkeys(public_text(row.get("name")) for row in rows))
            names = [name for name in names if name]
            return "Actualmente tenemos estos servicios: " + ", ".join(names[:8]) + "." if names else MISSING
        topic = "product_categories" if intent == "categories" else intent
        result = self.business.resolve(topic)
        records = []
        if result.available:
            for item in result.evidence:
                if item.verified and item.data.get("topic") == topic:
                    records.extend(row for row in item.data.get("records", []) if isinstance(row, dict))
        if intent == "payment_methods":
            allowed = {"pago movil": "Pago Móvil", "binance": "Binance", "zelle": "Zelle"}
            names = list(dict.fromkeys(allowed[normalize(row.get("name"))] for row in records
                                       if normalize(row.get("name")) in allowed))
            requested = entities.get("payment_method")
            if requested:
                names = [name for name in names if normalize(name) == normalize(requested)]
            return "Actualmente aceptamos: " + ", ".join(names) + "." if names else MISSING
        if intent == "branches":
            parts = []
            for row in records:
                name, address = public_text(row.get("name")), public_text(row.get("address"), 240)
                if name:
                    parts.append(name + (f": {address}" if address else " (dirección no configurada)"))
            return "Sucursales: " + "; ".join(parts[:8]) + "." if parts else MISSING
        names = list(dict.fromkeys(public_text(row.get("name")) for row in records))
        names = [name for name in names if name]
        if not names and intent == "categories":
            result = self.inventory.list_categories()
            names = [public_text(name) for item in result.evidence if item.verified
                     for name in item.data.get("categories", []) if public_text(name)] if result.available else []
        return "Categorías disponibles: " + ", ".join(names[:10]) + "." if names else MISSING
