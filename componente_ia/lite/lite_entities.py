from __future__ import annotations

import re
import unicodedata


def normalize(value):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", str(value or "").casefold())
                            if not unicodedata.combining(c)).split())


_SIZE = re.compile(r"^(?P<prefix>LT|P)?(?:(?P<width>\d{3})/(?P<aspect>\d{2,3})|"
                   r"(?P<diameter>\d{2})X(?P<floatwidth>\d{1,2}(?:\.\d{1,2})?)|"
                   r"(?P<commercial>\d{1,3}(?:\.\d{1,2})?))R(?P<rim>\d{2}(?:\.5)?)(?P<suffix>C|LT)?$")
_SIZE_CANDIDATE = re.compile(r"(?<![\w./-])(?:LT|P)?\d+(?:[./X]\d+)*\s*R\s*\d+(?:\.\d+)*(?:LT|C)?(?![\w/-])", re.I)
TIRE_BRANDS = ("Michelin", "Goodyear", "Bridgestone", "Firestone", "Pirelli", "Continental", "Dunlop",
               "Hankook", "Kumho", "Yokohama", "Toyo", "Maxxis", "Cooper", "BFGoodrich", "Goodrich",
               "Falken", "General", "Triangle", "Chengshan", "Linglong", "Roadcruza", "Sailun", "Westlake",
               "Goodride", "Roadmax", "Double Coin", "Durun", "Compasal", "Arivo", "Haida", "Grenlander", "Budget")
NON_TIRE_BRANDS = ("Duracell", "Extrema", "Moura", "Duncan", "Titan", "ACDelco", "Dauer", "Gulf", "Mobil", "Valvoline", "Castrol", "Shell", "Motul", "Inca", "PDV")
VEHICLES = {"Toyota": ("Hilux", "Corolla", "Fortuner", "Prado", "Yaris", "4Runner", "Land Cruiser", "Rav4"),
            "Chevrolet": ("Aveo", "Spark", "Optra", "Silverado", "Tahoe", "Corsa", "Cruze"),
            "Ford": ("Explorer", "Fiesta", "Focus", "Ranger", "F-150", "F150", "Escape", "Bronco"),
            "Nissan": ("Sentra", "Frontier", "Navara", "X-Trail", "Patrol"),
            "Mitsubishi": ("Lancer", "Montero", "L200"), "Suzuki": ("Grand Vitara", "Jimny", "Swift"),
            "Honda": ("Civic", "Accord", "CR-V"), "Hyundai": ("Accent", "Tucson", "Elantra"),
            "Kia": ("Rio", "Sportage", "Picanto"), "Jeep": ("Cherokee", "Wrangler", "Renegade"),
            "Volkswagen": ("Golf", "Polo", "Jetta"), "Renault": ("Logan", "Clio", "Duster"),
            "Mazda": ("BT-50", "CX-5"), "Chery": ("Orinoco", "Tiggo"), "Tesla": ("Model 3", "Model Y"),
            "BMW": (), "Mercedes-Benz": (), "Audi": (), "Peugeot": (), "Fiat": (), "Dodge": (),
            "Iveco": (), "Isuzu": (), "Hino": (), "Volvo": (), "Scania": (), "Mack": ()}


def parse_tire_size(value):
    text = re.sub(r"\s+", "", str(value or "").upper()).replace("×", "X")
    match = _SIZE.fullmatch(text)
    if not match:
        return None
    values = match.groupdict()
    rim = float(values["rim"])
    if not 10 <= rim <= 30:
        return None
    if values["width"] and not (100 <= int(values["width"]) <= 455 and 20 <= int(values["aspect"]) <= 95):
        return None
    if values["diameter"] and not (20 <= int(values["diameter"]) <= 44 and 5 <= float(values["floatwidth"]) <= 20):
        return None
    if values["commercial"]:
        width = float(values["commercial"])
        if not (5 <= width <= 14.5 or (100 <= width <= 455 and "." not in values["commercial"])):
            return None
    return text


def extract_sizes(text):
    result = []
    for match in _SIZE_CANDIDATE.finditer(str(text or "").upper().replace("×", "X")):
        size = parse_tire_size(match.group())
        if size and size not in result:
            result.append(size)
    return result


def _find_name(text, names):
    for name in sorted(set(filter(None, names)), key=lambda x: (-len(str(x)), str(x))):
        if re.search(r"(?<!\w)" + re.escape(normalize(name)) + r"(?!\w)", text):
            return str(name)
    return None


def extract_entities(text, *, brands=(), models=(), branches=()):
    value = normalize(text)
    sizes = extract_sizes(text)
    size = sizes[0] if sizes else None
    rim_match = re.search(r"\b(?:rin|rines|aro)\s*(\d{2}(?:\.5)?)(?![\d.])", value)
    rim = float(re.search(r"R(\d+(?:\.5)?)", size).group(1)) if size else float(rim_match.group(1)) if rim_match else None
    rim = int(rim) if rim is not None and rim.is_integer() else rim
    if rim is not None and not 10 <= rim <= 30:
        rim = None
    tire_type = None
    for key, pattern in (("A/T", r"\ba\s*[/ -]?\s*t\b|\ball terrain\b|\btodo terreno\b"),
                         ("M/T", r"\bm\s*[/ -]?\s*t\b|\bmud terrain\b|\bfang(?:o|ueros?)\b"),
                         ("H/T", r"\bh\s*[/ -]?\s*t\b|\bhighway terrain\b|\bcarretera\b")):
        if re.search(pattern, value):
            tire_type = key
            break
    brand = _find_name(value, (*TIRE_BRANDS, *NON_TIRE_BRANDS, *brands))
    model = _find_name(value, models)
    model_match = re.search(r"\bmodelo\s+([\w-]+)", value)
    if not model and model_match:
        model = model_match.group(1)
    category = None
    if re.search(r"\b(?:baterias?|acumulador(?:es)?)\b", value):
        category = "Baterias"
    elif re.search(r"\b(?:lubricantes?|aceites?|fluidos?|valvulina(?:s)?)\b", value):
        category = "Lubricantes"
    elif re.search(r"\b(?:cauchos?|neumaticos?|gomas?|llantas?)\b", value):
        category = "Cauchos"
    elif re.search(r"\bcombos?\b", value):
        category = "Combos"
    clean_query = re.sub(r"\b(?:tienen|tiene|hay|disponibles?|disponibilidad|cuanto cuesta|cuanto vale|precio de|precio|stock de|stock|baterias?|cauchos?|aceite|por favor|buenas|hola|cual es|el mas|la mas|mas barat[oa]s?|mas economic[oa]s?|mas stock|mayor stock)\b", " ", value).strip(" ?¿!.,")
    clean_query = " ".join(clean_query.split())
    product_query = clean_query if len(clean_query) >= 3 else None
    vehicle_brand, vehicle_model = None, None
    for make, names in VEHICLES.items():
        found = _find_name(value, names)
        if found:
            vehicle_brand, vehicle_model = make, found
            break
    vehicle_brand = vehicle_brand or _find_name(value, VEHICLES)
    if vehicle_brand and not vehicle_model:
        after = re.search(re.escape(normalize(vehicle_brand)) + r"\s+([a-z][\w-]*(?:\s+\d{1,3})?)", value)
        if after and after.group(1) not in {"del", "de", "usa", "lleva", "modelo", "ano"}:
            vehicle_model = after.group(1)
    if not vehicle_model:
        unknown = re.search(r"\b(?:tengo (?:un|una)?|mi|para mi|de mi)\s+(?!cauchos?\b|neumaticos?\b|gomas?\b)([a-z][\w-]*)", value)
        if unknown:
            vehicle_model = unknown.group(1)
    year_match = re.search(r"\b(19[5-9]\d|20[0-3]\d)\b", value)
    service = _find_name(value, ("alineación", "balanceo", "montaje", "rotación", "vulcanización", "reparación"))
    payment = _find_name(value, ("Pago Móvil", "Zelle", "Binance"))
    branch = _find_name(value, branches)
    branch_match = re.search(r"\b(?:sucursal|sede)\s+(?!tienen\b|estan\b|esta\b|hay\b)([\w -]{2,45})", value)
    if not branch and branch_match:
        branch = branch_match.group(1).strip()
    return {"tire_size": size, "rim": rim, "tire_type": tire_type, "brand": brand, "model": model,
            "category": category, "product_query": product_query, "raw": text,
            "vehicle_brand": vehicle_brand, "vehicle_model": vehicle_model,
            "vehicle_year": int(year_match.group(1)) if year_match else None, "service": service,
            "payment_method": payment, "branch": branch,
            "asks_price": bool(re.search(r"\b(?:precios?|cuanto (?:cuesta|cuestan|vale|valen|sale|salen)|costo|valor)\b", value)),
            "asks_stock": bool(re.search(r"\b(?:hay|tienen|tienes|disponibles?|disponibilidad|existencia|stock|quedan|cantidad|cuantos)\b", value)),
            "asks_cheapest": bool(re.search(r"\b(?:mas (?:barat[oa]s?|economic[oa]s?)|menor precio|barat[oa]s?|economic[oa]s?)\b", value)),
            "asks_most_stock": bool(re.search(r"\b(?:mas (?:stock|existencias?|cantidad)|mayor (?:stock|existencia|cantidad))\b", value))}
