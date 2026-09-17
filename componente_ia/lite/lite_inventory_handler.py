"""Read through InventoryRetriever; strict Lite filtering never duplicates SQL."""

import re
from .lite_entities import extract_sizes, normalize, parse_tire_size
from .lite_response_templates import MISSING, SYNTHETIC_NOTE, number, product_line, public_text


def _base(size):
    # Prefixes indicate construction/use. They are preserved, never silently equated.
    return parse_tire_size(size)


class LiteInventoryHandler:
    def __init__(self, inventory_retriever):
        self.retriever = inventory_retriever

    def load_products(self):
        # All active rows are needed for correct minimum/maximum after Lite filters.
        # Canonical filters are not changed; Lite validates formats independently.
        result = self.retriever.search("", entities={}, filters={},
                                       limit=100000, include_out_of_stock=True)
        if not result.available:
            return None
        products = []
        for item in result.evidence:
            data = item.data
            if not item.verified or data.get("active") is False:
                continue
            name = public_text(data.get("name"))
            if not name:
                continue
            sizes = list(dict.fromkeys(size for size in [
                *(parse_tire_size(value) for value in data.get("sizes", [])),
                *extract_sizes(data.get("name")), *extract_sizes(data.get("description"))] if size))
            stock_value = number(data.get("stock"))
            stock = int(stock_value) if stock_value is not None and stock_value.is_integer() else None
            provenance = data.get("inventory_provenance") or {}
            synthetic = bool(provenance.get("synthetic_inventory_mode") or provenance.get("stock_source") == "synthetic_seed")
            tire_type = re.sub(r"[^A-Z]", "", str(data.get("tire_type") or "").upper()) or None
            category = public_text(data.get("category"))
            is_tire = bool(data.get("is_tire") or (category and category.lower() in {"caucho", "cauchos", "tires", "tire"}))
            products.append({"codigo": data.get("code"), "nombre": name,
                             "categoria": category, "marca": public_text(data.get("brand")) or None,
                             "modelo": public_text(data.get("model")) or None,
                             "precio": number(data.get("price")) if data.get("price_available") else None,
                             "stock": stock, "sucursal": public_text(data.get("branch")) if data.get("branch_available") else None,
                             "sizes": sizes, "normalized_size": sizes[0] if sizes else None,
                             "rim": data.get("rim"), "tire_type": tire_type,
                             "is_tire": is_tire,
                             "inventory_provenance": {"stock_source": "synthetic_seed" if synthetic else public_text(provenance.get("stock_source")) or "database",
                                                      "synthetic_inventory_mode": synthetic},
                             "compatibility": "inventory_only_no_vehicle_fitment"})
        return products

    def handle(self, intent, entities, state, products=None):
        filters = {key: entities.get(key) if entities.get(key) is not None else state.get(key)
                   for key in ("tire_size", "rim", "tire_type", "brand", "model", "branch", "category", "product_query")}
        specific_filters = [filters.get(k) for k in ("tire_size", "rim", "tire_type", "brand", "model", "branch", "category")]
        if intent in {"price", "cheapest", "most_stock"} and not any(specific_filters) and not state.get("last_products"):
            return "Indícame la medida, marca o tipo de caucho para revisar el catálogo.", [], False
        if products is None:
            products = self.load_products()
        if products is None:
            return MISSING, [], False
        selected = state.get("selected_product")
        if selected and not any(entities.get(key) for key in filters) and intent in {"price", "stock"}:
            products = [item for item in products if str(item["codigo"]) == str(selected.get("codigo"))]
        if filters.get("category"):
            cat_req = normalize(filters["category"])
            matched_cat = [item for item in products if cat_req in normalize(item.get("categoria") or "")]
            if matched_cat:
                products = matched_cat
        size, rim = filters["tire_size"], filters["rim"]
        if size:
            products = [item for item in products if _base(size) in item["sizes"]]
        if rim is not None:
            products = [item for item in products if item.get("rim") == rim or any(
                float(re.search(r"R(\d+(?:\.5)?)", current).group(1)) == rim for current in item["sizes"])]
        if filters["tire_type"]:
            requested_type = normalize(filters["tire_type"]).replace("/", "")
            products = [item for item in products if requested_type == normalize(item.get("tire_type") or "").replace("/", "")]
        if filters["brand"]:
            requested_brand = normalize(filters["brand"])
            matched_brand = [item for item in products if requested_brand == normalize(item.get("marca") or "") or requested_brand in normalize(item.get("nombre") or "")]
            if matched_brand:
                products = matched_brand
        if filters["model"]:
            requested_model = normalize(filters["model"])
            matched_model = [item for item in products if requested_model in normalize(item.get("modelo") or "") or requested_model in normalize(item.get("nombre") or "")]
            if matched_model:
                products = matched_model
        if filters.get("product_query"):
            tokens = [tok for tok in normalize(filters["product_query"]).split() if len(tok) >= 3 and tok not in {"amp", "bateria", "baterias"}]
            if tokens:
                matched_query = [item for item in products if any(tok in normalize(item.get("nombre") or "") for tok in tokens)]
                if matched_query:
                    products = matched_query
        if filters["branch"]:
            branch = normalize(filters["branch"])
            products = [item for item in products if branch in [normalize(part) for part in (item.get("sucursal") or "").split(",")]]
        # Availability queries do not advertise zero/unknown inventory as in stock.
        availability = intent in {"stock", "inventory_by_size", "inventory_by_brand", "inventory_by_type", "cheapest", "most_stock"}
        if availability:
            products = [item for item in products if item["stock"] is not None and item["stock"] > 0]
        query_val = normalize(entities.get("product_query") or entities.get("raw") or "")
        brand_val = normalize(filters.get("brand") or "")

        def _rank(item):
            name_norm = normalize(item.get("nombre") or "")
            model_norm = normalize(item.get("modelo") or "")
            brand_norm = normalize(item.get("marca") or "")
            if query_val and (query_val in name_norm or name_norm in query_val or (model_norm and model_norm in query_val)):
                return 0
            if brand_val and (brand_val == brand_norm or brand_val in name_norm):
                return 1
            return 2

        if intent == "cheapest":
            products = [item for item in products if item["precio"] is not None]
            products.sort(key=lambda item: (item["precio"], str(item["codigo"])))
        elif intent == "most_stock":
            products.sort(key=lambda item: (-item["stock"], str(item["codigo"])))
        else:
            products.sort(key=lambda item: (_rank(item), normalize(item["nombre"]), str(item["codigo"])))
        if not products:
            qualifier = f" en medida {size}" if size else " con esos datos"
            return f"No encontré opciones verificadas{qualifier} en el catálogo actual.", [], True
        count = len(products)
        matches = products[:1] if intent in {"cheapest", "most_stock"} else products[:6]
        lines = [product_line(item) for item in matches[:3]]
        if intent in {"inventory_by_size", "inventory_by_brand", "inventory_by_type", "stock"}:
            prefix = f"Sí, encontré {count} opciones" + (f" en medida {size}" if size else " en el catálogo") + "."
            if any(item["inventory_provenance"]["synthetic_inventory_mode"] for item in matches):
                prefix = f"Encontré {count} opciones registradas" + (f" en medida {size}" if size else " en el catálogo") + "."
            lines.insert(0, prefix)
        if any(item["inventory_provenance"]["synthetic_inventory_mode"] for item in matches):
            lines.append(SYNTHETIC_NOTE)
        return "\n".join(lines), matches, True
