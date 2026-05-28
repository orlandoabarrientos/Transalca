import re
import time
import unicodedata
from difflib import SequenceMatcher

import requests

from model.product_model import ProductModel
from model.service_model import ServiceModel


MAX_MESSAGE_LENGTH = 255
EXTERNAL_CACHE_TTL = 1800
EXTERNAL_TIMEOUT = 4
CATALOG_CACHE_TTL = 60
SESSION_CACHE_TTL = 1800
RIM_PATTERN = re.compile(r'\b(?:rin|aro|r)\s*-?\s*(\d{2})\b|\b(?:lt|p)?\d{3}\s*/\s*\d{2}\s*r\s*(\d{2})\b')
SIZE_PATTERN = re.compile(r'\b(?:lt|p)?\d{3}\s*/\s*\d{2}\s*r\s*\d{2}\b')

_external_cache = {}
_catalog_cache = {'time': 0, 'products': [], 'services': []}
_session_cache = {}

STOPWORDS = {
    'que', 'cual', 'cuales', 'para', 'con', 'una', 'uno', 'unos', 'unas', 'los', 'las',
    'el', 'la', 'de', 'del', 'mi', 'tu', 'su', 'en', 'al', 'por', 'como', 'donde',
    'tiene', 'tienen', 'hay', 'quiero', 'necesito',
    'recomienda', 'recomiendas', 'bueno', 'buenos', 'mejor', 'mejores'
}

DOMAIN_TERMS = {
    'producto', 'productos', 'repuesto', 'repuestos', 'servicio', 'servicios', 'mantenimiento',
    'vehiculo', 'vehiculos', 'carro', 'auto', 'automotriz', 'motor', 'aceite', 'filtro',
    'filtros', 'caucho', 'cauchos', 'llanta', 'llantas', 'neumatico', 'neumaticos',
    'bateria', 'baterias', 'freno', 'frenos', 'pastilla', 'pastillas', 'amortiguador',
    'amortiguadores', 'correa', 'correas', 'refrigerante', 'todo', 'terreno', 'all',
    'terrain', 'at', 'mt', 'ht', 'precio', 'precios', 'promocion', 'promociones',
    'sucursal', 'sucursales', 'pedido', 'pedidos', 'pago', 'pagos', 'garantia',
    'comprar', 'compra', 'catalogo', 'rueda', 'ruedas', 'volante', 'vibracion',
    'vibra', 'temblor', 'jala', 'desvia', 'rin', 'rines', 'aro', 'aros',
    'medida', 'medidas', 'talla', 'stock', 'disponible', 'disponibles',
    'venden', 'vendes', 'venta', 'luz', 'check', 'tablero', 'falla', 'fallas',
    'prendida', 'encendida', 'ruido', 'ruidos', 'suena', 'chilla', 'chirrido',
    'tiembla', 'barato', 'economico', 'caro', 'comprobante', 'subo', 'subir',
    'cargar', 'arranca', 'prende', 'tac', 'combo', 'combos', 'paquete', 'paquetes'
}

SYNONYMS = {
    'caucho': {'caucho', 'cauchos', 'llanta', 'llantas', 'neumatico', 'neumaticos', 'goma'},
    'allterrain': {'all', 'terrain', 'todo', 'terreno', 'mixto', 'at', 'a/t'},
    'aceite': {'aceite', 'lubricante', 'motor'},
    'filtro': {'filtro', 'filtros', 'aire', 'gasolina', 'gasoil', 'combustible'},
    'bateria': {'bateria', 'baterias', 'acumulador'},
    'freno': {'freno', 'frenos', 'pastilla', 'pastillas', 'disco', 'discos'},
}

SERVICE_TERMS = {
    'servicio', 'servicios', 'mantenimiento', 'revision', 'revisar', 'instalar',
    'instalacion', 'cambiar', 'cambio', 'reemplazo', 'diagnostico'
}

PRODUCT_TERMS = {
    'producto', 'productos', 'repuesto', 'repuestos', 'comprar', 'compra',
    'catalogo', 'precio', 'precios', 'medida', 'medidas', 'rin', 'rines',
    'aro', 'aros', 'talla', 'tienes', 'tienen', 'hay', 'venden', 'vendes',
    'disponible', 'disponibles', 'stock'
}

INVENTORY_TERMS = {'tienes', 'tienen', 'hay', 'venden', 'vendes', 'disponible', 'disponibles', 'stock', 'catalogo'}

VEHICLE_MODEL_TERMS = {
    '4runner', 'runner', 'hilux', 'fortuner', 'corolla', 'yaris', 'camry',
    'terios', 'machito', 'prado', 'tacoma', 'silverado', 'aveo', 'cruze',
    'fiesta', 'explorer', 'cherokee', 'grand', 'vitara'
}

VEHICLE_SIZE_PREFS = {
    '4runner': ('265/65r17', '265/70r17', '265/70r16', '245/70r16'),
    'runner': ('265/65r17', '265/70r17', '265/70r16', '245/70r16')
}

CATEGORY_ALIASES = {
    'Cauchos': {'caucho', 'cauchos', 'llanta', 'llantas', 'neumatico', 'neumaticos', 'goma', 'rin', 'rines', 'aro', 'aros'},
    'Lubricantes': {'aceite', 'aceites', 'lubricante', 'lubricantes', 'motor', '5w30', '10w40', '15w40'},
    'Filtros': {'filtro', 'filtros', 'aire', 'aceite', 'cabina', 'gasolina', 'combustible'},
    'Frenos': {'freno', 'frenos', 'pastilla', 'pastillas', 'disco', 'discos', 'liga'},
    'Baterias': {'bateria', 'baterias', 'acumulador', 'arranque'},
    'Repuestos': {'repuesto', 'repuestos', 'bujia', 'bujias', 'pieza', 'piezas'},
    'Combos': {'combo', 'combos', 'paquete', 'paquetes', 'cashea'}
}

PRODUCT_CATEGORY_HINTS = {
    'Baterias': 'Estas son las baterias activas en catalogo. Para elegir bien, valida amperaje, CCA, polaridad y espacio disponible.',
    'Cauchos': 'Estos son los cauchos activos en catalogo. Para elegir bien, valida medida, rin, carga, uso y manual del vehiculo.',
    'Lubricantes': 'Estos son los lubricantes activos en catalogo. Para elegir bien, valida viscosidad y especificacion del fabricante.',
    'Filtros': 'Estos son los filtros activos en catalogo. Para elegir bien, valida motor, ano y referencia.',
    'Frenos': 'Estos son los productos de frenos activos en catalogo. Para elegir bien, valida modelo, ano y eje delantero/trasero.',
    'Repuestos': 'Estos son los repuestos activos en catalogo. Para elegir bien, valida referencia y compatibilidad.',
    'Combos': 'Estos son los combos activos en catalogo. Para elegir bien, valida aceite, cantidad de litros y servicio incluido.'
}

TRAINING_DATA = [
    ('tienen cauchos rin 15', 'tire_rim'),
    ('hay cauchos r15 disponibles', 'tire_rim'),
    ('busco llantas aro 16', 'tire_rim'),
    ('cauchos rin 17 en stock', 'tire_rim'),
    ('tengo una 4runner que medida de caucho recomienda', 'tire_vehicle_size'),
    ('medida de caucho para corolla', 'tire_vehicle_size'),
    ('que caucho usa una hilux', 'tire_vehicle_size'),
    ('cauchos all terrain buenos', 'tire_allterrain'),
    ('que llantas todo terreno tienes', 'tire_allterrain'),
    ('necesito balancear mis cauchos', 'service_balance'),
    ('me vibra el volante', 'service_balance'),
    ('servicio de balanceo', 'service_balance'),
    ('necesito cambiar aceite', 'service_oil'),
    ('servicio cambio de aceite', 'service_oil'),
    ('pastillas de freno', 'brakes'),
    ('revision de frenos', 'brakes'),
    ('bateria para carro', 'battery'),
    ('cambiar bateria', 'battery'),
    ('consultar pedido', 'order'),
    ('estado de mi pedido', 'order'),
    ('precio de producto', 'price'),
    ('cuanto cuesta', 'price'),
]

COMMON_TYPOS = {
    'q': 'que',
    'cauchoz': 'cauchos', 'caucos': 'cauchos', 'cauxos': 'cauchos', 'cauhos': 'cauchos', 'cuchos': 'cauchos',
    'llnatas': 'llantas', 'yantas': 'llantas', 'neumaticoz': 'neumaticos',
    'rinn': 'rin', 'rrin': 'rin', 'ar': 'aro',
    'vateria': 'bateria', 'vaterias': 'baterias', 'bateriaz': 'baterias', 'bater': 'bateria',
    'aceyte': 'aceite', 'aseite': 'aceite', 'aciete': 'aceite', 'aseite': 'aceite',
    'filto': 'filtro', 'firtro': 'filtro', 'filtroz': 'filtros',
    'frenoz': 'frenos', 'pastiya': 'pastilla', 'pastiyas': 'pastillas',
    'balansear': 'balancear', 'balansiar': 'balancear', 'valancear': 'balancear',
    'balanseo': 'balanceo', 'balansio': 'balanceo',
    'alineasion': 'alineacion', 'alinasion': 'alineacion',
    'rotasion': 'rotacion', 'rrotacion': 'rotacion',
    'escanner': 'scanner', 'escaner': 'scanner', 'scaner': 'scanner',
    'presio': 'precio', 'presios': 'precios', 'kuanto': 'cuanto',
    'toyotaa': 'toyota', 'corola': 'corolla', 'corrola': 'corolla',
    'forruner': '4runner', 'forrunner': '4runner', 'runer': 'runner',
    'ai': 'hay', 'ay': 'hay', 'stok': 'stock', 'stoc': 'stock',
    'disponivle': 'disponible', 'disponibles?': 'disponibles',
    'suvopago': 'pago', 'subopago': 'pago', 'comprbante': 'comprobante'
}

SPANISH_NUMBERS = {
    'trece': '13', 'catorce': '14', 'quince': '15', 'diesiseis': '16',
    'dieciseis': '16', 'dieziseis': '16', 'diecisiete': '17', 'diesisiete': '17',
    'dieciocho': '18', 'diesiocho': '18', 'diecinueve': '19', 'diesinueve': '19',
    'veinte': '20', 'veintiuno': '21', 'veintidos': '22'
}

for rim in range(13, 23):
    TRAINING_DATA.extend([
        (f'tienen cauchos rin {rim}', 'tire_rim'),
        (f'hay llantas rin {rim}', 'tire_rim'),
        (f'busco neumaticos aro {rim}', 'tire_rim'),
        (f'cauchos r{rim} disponibles', 'tire_rim'),
        (f'y rin {rim}', 'tire_rim'),
    ])

for category, words in CATEGORY_ALIASES.items():
    label = 'product_lookup'
    for word in sorted(words):
        TRAINING_DATA.extend([
            (f'que {word} tienes', label),
            (f'tienen {word}', label),
            (f'hay {word} disponible', label),
            (f'venden {word}', label),
            (f'muestrame {word}', label),
            (f'precio de {word}', 'price'),
        ])

for model in sorted(VEHICLE_MODEL_TERMS):
    TRAINING_DATA.extend([
        (f'que caucho usa una {model}', 'tire_vehicle_size'),
        (f'medida de caucho para {model}', 'tire_vehicle_size'),
        (f'tengo {model} que rin recomienda', 'tire_vehicle_size'),
    ])

for action, words in {
    'service_balance': ['balancear', 'balanceo', 'vibracion', 'vibra', 'temblor', 'tiembla en carretera', 'vibra el volante', 'volante temblando'],
    'service_oil': ['cambiar aceite', 'cambio de aceite', 'lubricante motor'],
    'brakes': ['frenos', 'pastillas', 'discos de freno', 'ruido al frenar', 'chilla cuando freno'],
    'battery': ['cambiar bateria', 'reemplazo de bateria', 'falla arranque'],
    'scanner': ['luz del motor prendida', 'check engine encendido', 'luz en tablero', 'falla del motor'],
}.items():
    for word in words:
        TRAINING_DATA.extend([
            (f'necesito {word}', action),
            (f'servicio para {word}', action),
            (f'cuanto cuesta {word}', action),
        ])

MESSY_TRAINING = [
    ('tinen cauxos rinn 15', 'tire_rim'),
    ('ay llantas aro catorce', 'tire_rim'),
    ('y rinn 14', 'tire_rim'),
    ('q bateriaz tienen', 'product_lookup'),
    ('venden vateria para carro', 'product_lookup'),
    ('tienen aceyte 5w30', 'product_lookup'),
    ('ay aseite diez cuarenta', 'product_lookup'),
    ('firtro de aciete toyota', 'product_lookup'),
    ('quiero pastiyas de freno corola', 'brakes'),
    ('mi carro hace ruido al frenar', 'brakes'),
    ('el volante tiembla mucho en carretera', 'service_balance'),
    ('necesito balansiar los cauhos', 'service_balance'),
    ('luz check prendida en tablero', 'scanner'),
    ('como suvopago', 'order'),
    ('como subo comprobante de pago', 'order'),
    ('quiero cargar el comprobante', 'order'),
    ('donde veo mi pedido', 'order'),
    ('esta caro o barato', 'price'),
]
TRAINING_DATA.extend(MESSY_TRAINING)


class TinyIntentNetwork:
    def __init__(self, samples):
        self.labels = sorted({label for _, label in samples})
        self.vocab = sorted({word for text, _ in samples for word in normalize_text(text).split() if len(word) > 1})
        self.index = {word: idx for idx, word in enumerate(self.vocab)}
        self.weights = {label: [0.0] * len(self.vocab) for label in self.labels}
        self.bias = {label: 0.0 for label in self.labels}
        self.train(samples)

    def vectorize(self, text):
        vector = [0.0] * len(self.vocab)
        for word in normalize_text(text).split():
            idx = self.index.get(word)
            if idx is not None:
                vector[idx] += 1.0
        return vector

    def scores(self, vector):
        return {
            label: self.bias[label] + sum(weight * value for weight, value in zip(self.weights[label], vector))
            for label in self.labels
        }

    def predict(self, text):
        vector = self.vectorize(text)
        if not any(vector):
            return 'consulta', 0.0
        scores = self.scores(vector)
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        confidence = ordered[0][1] - ordered[1][1] if len(ordered) > 1 else ordered[0][1]
        return ordered[0][0], confidence

    def train(self, samples):
        for _ in range(35):
            for text, label in samples:
                vector = self.vectorize(text)
                prediction, _ = self.predict(text)
                if prediction == label:
                    continue
                for idx, value in enumerate(vector):
                    if value:
                        self.weights[label][idx] += value
                        self.weights[prediction][idx] -= value
                self.bias[label] += 1.0
                self.bias[prediction] -= 1.0

SERVICE_ACTIONS = {
    'balanceo': {'balanceo', 'balancear', 'balanceado', 'balanceando', 'balanceen', 'equilibrar', 'equilibrado', 'vibracion', 'vibra', 'temblor', 'tiembla'},
    'alineacion': {'alineacion', 'alinear', 'alineado', 'volante', 'jala', 'desvia'},
    'rotacion': {'rotacion', 'rotar', 'rotacionar', 'permutar', 'rotarlos', 'rotarlo', 'rotarlas'},
    'montaje': {'montaje', 'montar', 'instalar', 'instalacion'},
    'aceite': {'aceite', 'lubricante'},
    'frenos': {'freno', 'frenos', 'pastilla', 'pastillas', 'disco', 'discos', 'frenar', 'ruido', 'ruidos', 'suena', 'chilla', 'chirrido'},
    'scanner': {'scanner', 'escaner', 'diagnostico', 'codigo', 'codigos', 'luz', 'check', 'tablero', 'falla', 'fallas', 'prendida', 'encendida'},
    'bateria': {'reemplazo', 'arranque', 'encendido', 'arranca', 'prende', 'tac'},
    'inyectores': {'inyector', 'inyectores', 'limpieza'}
}

SERVICE_HINTS = {
    'balanceo': 'Para balancear cauchos o corregir vibraciones, el servicio principal es Balanceo. Ayuda a reducir vibraciones y desgaste irregular.',
    'alineacion': 'Para problemas de direccion, volante desviado o desgaste irregular, conviene revisar Alineacion.',
    'rotacion': 'Para alargar la vida de los cauchos, la Rotacion ayuda a repartir el desgaste.',
    'montaje': 'Para instalar cauchos nuevos, solicita Montaje de cauchos.',
    'aceite': 'Para mantenimiento de motor, solicita Cambio de aceite y revisa tambien el filtro.',
    'frenos': 'Para ruidos, vibracion o baja respuesta al frenar, solicita Revision de sistema de frenos.',
    'scanner': 'Para luces de falla o codigos del tablero, solicita Diagnostico con scanner automotriz.',
    'bateria': 'Para fallas de arranque, revisa Reemplazo de bateria o diagnostico electrico.',
    'inyectores': 'Para consumo alto o falla de combustion, puede ayudar la Limpieza de inyectores.'
}

ACTION_PRIORITY = ['scanner', 'balanceo', 'alineacion', 'rotacion', 'montaje', 'aceite', 'frenos', 'bateria', 'inyectores']

LOCAL_KNOWLEDGE = {
    'allterrain': (
        'Los cauchos all terrain sirven para uso mixto: carretera, tierra, grava y caminos irregulares. '
        'Son buena opcion si necesitas equilibrio entre comodidad en asfalto y traccion fuera de carretera. '
        'Hacen mas ruido que un caucho de carretera y son menos extremos que uno mud terrain.'
    ),
    'aceite': (
        'Para aceite de motor conviene respetar viscosidad y especificacion recomendada por el fabricante. '
        'Tambien es importante cambiar filtro de aceite y revisar kilometraje.'
    ),
    'filtro': (
        'Los filtros protegen motor y sistemas del vehiculo. Filtro de aceite, aire y combustible se eligen '
        'segun modelo, motor y uso del vehiculo.'
    ),
    'bateria': (
        'La bateria correcta depende de amperaje, polaridad, tamano y demanda electrica del vehiculo.'
    ),
    'freno': (
        'En frenos se debe revisar pastillas, discos, liga y posibles ruidos. No conviene retrasar ese mantenimiento.'
    ),
    'producto': (
        'Puedes consultar productos disponibles en el catalogo. Si me indicas nombre, marca, categoria o uso, busco coincidencias.'
    ),
    'pedido': (
        'Para pedidos, revisa la seccion Mis pedidos. La factura o QR debe mostrarse solo cuando el pago este aprobado.'
    ),
    'pago': (
        'Para pagos, sube el comprobante desde el pedido correspondiente y espera la aprobacion del administrador.'
    ),
    'sucursal': (
        'Puedes revisar las sucursales activas del sistema. Si necesitas atencion directa, contacta a Transalca por sus canales oficiales.'
    ),
    'promocion': (
        'Las promociones activas se consultan desde fidelizacion o catalogo, segun el tipo de beneficio disponible.'
    ),
    'medida_caucho': (
        'Para recomendar medida exacta de caucho necesito ano, version y rin actual del vehiculo. '
        'En Toyota 4Runner son comunes medidas como 265/65R17 o 265/70R17 segun version. '
        'No conviene cambiar medida sin validar espacio, rin y manual del fabricante.'
    ),
}


_known_words_cache = None


def basic_normalize(value):
    text = str(value or '').strip()
    text = re.sub(r'<[^>]*>', ' ', text)
    text = re.sub(r'javascript:|onerror|onclick|onload|script', ' ', text, flags=re.IGNORECASE)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    phrase_replacements = {
        'diez cuarenta': '10w40',
        'diez cuarenta y': '10w40',
        'cinco treinta': '5w30',
        'quince cuarenta': '15w40',
        'quince cuarenta y': '15w40'
    }
    for phrase, replacement in phrase_replacements.items():
        text = text.replace(phrase, replacement)
    text = re.sub(r'[^a-z0-9/\s-]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def known_words():
    global _known_words_cache
    if _known_words_cache is not None:
        return _known_words_cache
    words = set(DOMAIN_TERMS) | set(PRODUCT_TERMS) | set(SERVICE_TERMS) | set(INVENTORY_TERMS) | set(VEHICLE_MODEL_TERMS)
    for group in SYNONYMS.values():
        words.update(group)
    for group in SERVICE_ACTIONS.values():
        words.update(group)
    for group in CATEGORY_ALIASES.values():
        words.update(group)
    for text, _ in TRAINING_DATA:
        words.update(basic_normalize(text).split())
    _known_words_cache = {word for word in words if len(word) > 1}
    return _known_words_cache


def correct_token(token):
    if token in COMMON_TYPOS:
        return COMMON_TYPOS[token]
    if len(token) < 4 or any(ch.isdigit() for ch in token):
        return token
    candidates = known_words()
    if token in candidates:
        return token
    best = ''
    best_score = 0.0
    for candidate in candidates:
        if abs(len(candidate) - len(token)) > 2:
            continue
        score = SequenceMatcher(None, token, candidate).ratio()
        if score > best_score:
            best = candidate
            best_score = score
    return best if best_score >= 0.82 else token


def normalize_text(value, autocorrect=True):
    text = basic_normalize(value)
    if not autocorrect:
        return text
    return ' '.join(correct_token(token) for token in text.split())


_intent_model = TinyIntentNetwork(TRAINING_DATA)


def tokenize(text):
    tokens = [t for t in normalize_text(text).replace('-', ' ').split() if len(t) > 1]
    expanded = set()
    for token in tokens:
        if token not in STOPWORDS:
            expanded.add(token)
        for group in SYNONYMS.values():
            if token in group:
                expanded.update(group)
        for group in SERVICE_ACTIONS.values():
            if token in group:
                expanded.update(group)
    if {'all', 'terrain'} <= set(tokens) or {'todo', 'terreno'} <= set(tokens):
        expanded.update(SYNONYMS['allterrain'])
    return expanded


def raw_terms(text):
    return {t for t in normalize_text(text).replace('-', ' ').split() if len(t) > 1}


def infer_topic_from_history(client_history):
    if not isinstance(client_history, list):
        return None
    combined = set()
    for item in client_history[-6:]:
        if not isinstance(item, dict) or item.get('type') not in ('user', 'bot'):
            continue
        combined.update(tokenize(str(item.get('text') or '')))
    return category_from_tokens(combined)


def get_session_context(session_id, client_history=None):
    context = _session_cache.get(session_id) if session_id else None
    if context and time.time() - context.get('time', 0) <= SESSION_CACHE_TTL:
        return context
    topic = infer_topic_from_history(client_history)
    if session_id and topic:
        context = {'time': time.time(), 'topic': topic, 'history': [], 'last_matches': []}
        _session_cache[session_id] = context
        return context
    return None


def merge_session_context(clean, session_id, client_history=None):
    context = get_session_context(session_id, client_history)
    if not context:
        return clean
    terms = raw_terms(clean)
    if len(terms) > 5 and not clean.startswith('y '):
        return clean
    topic = context.get('topic')
    if topic == 'Cauchos' and (extract_rim(clean) or terms & {'rin', 'rines', 'aro', 'aros', 'medida', 'medidas'}):
        return f"cauchos {clean}"
    if topic and clean.startswith('y '):
        return f"{topic.lower()} {clean}"
    return clean


def light_match(kind, item):
    return {
        'tipo': kind,
        'nombre': item.get('nombre'),
        'precio': float(item.get('precio') or 0),
        'stock': int(item.get('stock') or 0) if kind == 'producto' else None,
        'categoria': item.get('categoria') or item.get('categoria_nombre')
    }


def update_session_context(session_id, raw, clean, tokens, matches, answer):
    if not session_id:
        return
    topic = category_from_tokens(tokens)
    if not topic and matches:
        first = matches[0][2]
        topic = first.get('categoria') or first.get('categoria_nombre')
    context = _session_cache.get(session_id, {'history': [], 'last_matches': []})
    history = context.get('history') or []
    history.append({'user': raw, 'clean': clean, 'answer': answer[:240]})
    context.update({
        'time': time.time(),
        'topic': topic or context.get('topic'),
        'history': history[-3:],
        'last_matches': [light_match(kind, item) for kind, _, item in matches[:4]]
    })
    _session_cache[session_id] = context


def followup_response(clean, tokens, session_id, client_history=None):
    context = get_session_context(session_id, client_history)
    if not context:
        return '', []
    last_matches = context.get('last_matches') or []
    if not last_matches:
        return '', []
    terms = raw_terms(clean)
    short = len(terms) <= 5
    wants_price = bool(terms & {'precio', 'precios', 'cuanto', 'cuesta', 'vale', 'barato', 'economico', 'caro'})
    wants_stock = bool(terms & {'stock', 'disponible', 'disponibles', 'hay', 'quedan'})
    if short and wants_price:
        ordered = sorted(last_matches, key=lambda item: item.get('precio') or 0)
        if terms & {'barato', 'economico'}:
            item = ordered[0]
            return f"La opcion mas economica de lo que vimos es {item['nombre']} - ${item['precio']:.2f}.", []
        lines = '; '.join(f"{item['nombre']} - ${item['precio']:.2f}" for item in last_matches)
        return f"Precios de lo que vimos: {lines}.", []
    if short and wants_stock:
        product_lines = [
            f"{item['nombre']} - stock {item['stock']}"
            for item in last_matches
            if item.get('tipo') == 'producto' and item.get('stock') is not None
        ]
        if product_lines:
            return f"Disponibilidad de lo que vimos: {'; '.join(product_lines)}.", []
    return '', []


def trained_intent(text):
    return _intent_model.predict(text)


def extract_rim(text):
    clean = normalize_text(text)
    match = RIM_PATTERN.search(clean)
    if match:
        return match.group(1) or match.group(2)
    tokens = clean.split()
    for index, token in enumerate(tokens[:-1]):
        if token in {'rin', 'aro', 'rines', 'aros'}:
            next_token = tokens[index + 1]
            if next_token in SPANISH_NUMBERS:
                return SPANISH_NUMBERS[next_token]
    return None


def extract_sizes(text):
    clean = normalize_text(text)
    return [re.sub(r'\s+', '', size).upper() for size in SIZE_PATTERN.findall(clean)]


def is_tire_product(item):
    category = normalize_text(item.get('categoria') or item.get('categoria_nombre'))
    if category == normalize_text('Cauchos'):
        return True
    text = item_text(item)
    return any(term in text for term in ('caucho', 'cauchos', 'llanta', 'llantas', 'neumatico', 'neumaticos'))


def tire_products(products):
    return [product for product in products if str(product.get('codigo') or '') != 'SIN_PRODUCTO' and is_tire_product(product)]


def available_tire_sizes(products):
    sizes = []
    seen = set()
    for product in tire_products(products):
        for size in extract_sizes(item_text(product)):
            if size not in seen:
                seen.add(size)
                sizes.append(size)
    return sizes


def category_from_tokens(tokens):
    if tokens & {'luz', 'check', 'tablero', 'falla', 'fallas', 'prendida', 'encendida'}:
        return None
    if tokens & {'filtro', 'filtros'}:
        return 'Filtros'
    if tokens & {'combo', 'combos', 'paquete', 'paquetes', 'cashea'}:
        return 'Combos'
    if tokens & {'aceite', 'aceites', 'lubricante', 'lubricantes', '5w30', '10w40', '15w40'}:
        return 'Lubricantes'
    if tokens & {'bateria', 'baterias', 'acumulador'}:
        return 'Baterias'
    if tokens & {'caucho', 'cauchos', 'llanta', 'llantas', 'neumatico', 'neumaticos', 'rin', 'rines', 'aro', 'aros'}:
        return 'Cauchos'
    if tokens & {'freno', 'frenos', 'pastilla', 'pastillas', 'disco', 'discos'}:
        return 'Frenos'
    if tokens & {'repuesto', 'repuestos', 'bujia', 'bujias'}:
        return 'Repuestos'
    best = None
    best_score = 0
    for category, aliases in CATEGORY_ALIASES.items():
        score = len(tokens & aliases)
        if score > best_score:
            best = category
            best_score = score
    return best


def products_by_category(products, category):
    if not category:
        return []
    return [
        product for product in products
        if str(product.get('codigo') or '') != 'SIN_PRODUCTO'
        and normalize_text(product.get('categoria') or product.get('categoria_nombre')) == normalize_text(category)
    ]


def stock_value(product):
    try:
        return int(product.get('stock') or 0)
    except (TypeError, ValueError):
        return 0


def price_value(item):
    try:
        return float(item.get('precio') or 0)
    except (TypeError, ValueError):
        return 0.0


def sort_catalog_products(products, tokens=None):
    tokens = tokens or set()
    return sorted(
        products,
        key=lambda product: (
            0 if stock_value(product) > 0 else 1,
            -specific_product_score(tokens, product) if tokens else 0,
            price_value(product),
            normalize_text(product.get('nombre'))
        )
    )


def compact_text(value):
    return re.sub(r'[^a-z0-9]', '', normalize_text(value))


def specific_product_score(tokens, product):
    text = item_text(product)
    compact = compact_text(text)
    score = len(tokens & set(text.split()))
    for token in tokens:
        if len(token) >= 3 and compact_text(token) in compact:
            score += 3
    return score


def product_lookup_response(tokens, products):
    category = category_from_tokens(tokens)
    if not category:
        return '', []
    matches = products_by_category(products, category)
    category_words = CATEGORY_ALIASES.get(category, set())
    specific_tokens = {token for token in tokens if token not in category_words or any(ch.isdigit() for ch in token)}
    specific = [product for product in matches if specific_product_score(specific_tokens, product) > 0]
    if specific:
        matches = specific
    matches = sort_catalog_products(matches, specific_tokens or tokens)
    if matches:
        names = '; '.join(product_line('producto', product) for product in matches[:4])
        intro = PRODUCT_CATEGORY_HINTS.get(category, 'Estos productos estan activos en catalogo.')
        return f"{intro} {names}.", [('producto', 10, product) for product in matches[:4]]
    return f"No veo productos activos de {category.lower()} en el catalogo en este momento.", []


def detect_intent(tokens):
    if tokens & {'precio', 'precios', 'costo', 'cuesta'}:
        return 'precio'
    if tokens & {'comparar', 'comparacion', 'diferencia'}:
        return 'comparacion'
    if tokens & {'recomienda', 'recomendar', 'recomendacion', 'bueno', 'buenos', 'mejor', 'mejores'}:
        return 'recomendacion'
    if tokens & {'sucursal', 'sucursales', 'ubicacion', 'direccion'}:
        return 'sucursal'
    if tokens & {'pedido', 'pedidos', 'pago', 'pagos'}:
        return 'pedido'
    return 'consulta'


def is_business_question(tokens, products, services):
    if tokens & DOMAIN_TERMS:
        return True
    for item in list(products or []) + list(services or []):
        if tokens & set(item_text(item).split()):
            return True
    return False


def item_text(item):
    values = [
        item.get('nombre'), item.get('descripcion'), item.get('categoria_nombre'),
        item.get('categoria'), item.get('marca_nombre'), item.get('marca')
    ]
    return normalize_text(' '.join(str(v or '') for v in values))


def action_groups(tokens):
    return {key for key, words in SERVICE_ACTIONS.items() if tokens & words}


def ordered_action_groups(tokens):
    groups = action_groups(tokens)
    return [key for key in ACTION_PRIORITY if key in groups]


def wants_service(tokens):
    return bool(tokens & SERVICE_TERMS or action_groups(tokens))


def wants_product(tokens):
    if tokens & SYNONYMS['caucho'] and not action_groups(tokens):
        return True
    return bool(tokens & PRODUCT_TERMS or tokens & SYNONYMS['allterrain'] or tokens & VEHICLE_MODEL_TERMS)


def explicit_service_request(tokens):
    return bool(tokens & {
        'servicio', 'servicios', 'mantenimiento', 'revision', 'revisar', 'instalar',
        'instalacion', 'cambiar', 'cambio', 'reemplazo', 'diagnostico', 'ruido',
        'ruidos', 'suena', 'chilla', 'chirrido', 'tac', 'arranca', 'prende'
    })


def score_item(tokens, item, kind='producto'):
    text = item_text(item)
    item_tokens = set(text.split())
    overlap = len(tokens & item_tokens)
    joined = ' '.join(sorted(tokens))
    ratio = SequenceMatcher(None, joined, text[:180]).ratio() if joined and text else 0
    boost = 0
    compact = compact_text(text)
    for token in tokens:
        if len(token) >= 4 and compact_text(token) in compact:
            boost += 3
    if tokens & SYNONYMS['allterrain'] and any(term in text for term in ('all terrain', 'todo terreno', 'a/t', ' at ', 'mixto')):
        boost += 3
    if tokens & SYNONYMS['caucho'] and any(term in text for term in ('caucho', 'llanta', 'neumatico')):
        boost += 2
    if kind == 'servicio':
        for group in action_groups(tokens):
            if any(term in text for term in SERVICE_ACTIONS[group]):
                boost += 8
        if tokens & SYNONYMS['caucho'] and any(term in text for term in ('caucho', 'rueda', 'ruedas', 'llanta')):
            boost += 3
    elif wants_service(tokens) and not wants_product(tokens):
        boost -= 4
    if kind == 'producto':
        for model, sizes in VEHICLE_SIZE_PREFS.items():
            if model in tokens:
                for index, size in enumerate(sizes):
                    if size in text:
                        boost += max(2, 7 - index)
                        break
    if overlap == 0 and boost == 0:
        return 0
    return (overlap * 2) + boost + ratio


def tire_size_response(tokens, clean, products):
    rim = extract_rim(clean)
    tires = tire_products(products)
    requested_sizes = extract_sizes(clean)
    if requested_sizes:
        size = normalize_text(requested_sizes[0])
        matches = sort_catalog_products([product for product in tires if size in item_text(product)], tokens)
        if matches:
            with_stock = [product for product in matches if stock_value(product) > 0]
            selected = with_stock or matches
            names = '; '.join(product_line('producto', product) for product in selected[:4])
            if with_stock:
                return f"Si tenemos la medida {requested_sizes[0]} con stock registrado: {names}."
            return f"La medida {requested_sizes[0]} aparece en catalogo, pero sin stock registrado ahora: {names}."
        return f"No veo la medida {requested_sizes[0]} activa en el catalogo en este momento."
    if rim:
        matches = sort_catalog_products([product for product in tires if f"r{rim}" in item_text(product)], tokens)
        if matches:
            with_stock = [product for product in matches if stock_value(product) > 0]
            selected = with_stock or matches
            names = '; '.join(product_line('producto', product) for product in selected[:5])
            if with_stock:
                return f"Si tenemos cauchos rin {rim} con stock registrado: {names}."
            return f"Tenemos cauchos rin {rim} en catalogo, pero sin stock registrado ahora: {names}."
        sizes = available_tire_sizes(products)
        suffix = f" Medidas disponibles ahora: {', '.join(sizes[:10])}." if sizes else ''
        return f"No veo cauchos rin {rim} activos en el catalogo en este momento.{suffix}"
    if tokens & VEHICLE_MODEL_TERMS:
        return LOCAL_KNOWLEDGE['medida_caucho']
    return 'Para recomendar medida exacta de caucho necesito la medida completa del caucho actual, el rin o el modelo y ano del vehiculo.'


def find_matches(tokens, products, services, limit=3, min_score=0.35, clean=''):
    rim = extract_rim(clean)
    if rim and (tokens & SYNONYMS['caucho'] or tokens & INVENTORY_TERMS or extract_sizes(clean)):
        matches = []
        for product in tire_products(products):
            if f"r{rim}" in item_text(product):
                matches.append(('producto', 10, product))
        matches.sort(key=lambda item: (0 if stock_value(item[2]) > 0 else 1, price_value(item[2]), normalize_text(item[2].get('nombre'))))
        return matches[:limit]

    prefer_service = wants_service(tokens)
    prefer_product = wants_product(tokens) and not prefer_service
    service_matches = []
    for product in products:
        if str(product.get('codigo') or '') == 'SIN_PRODUCTO':
            continue
        if prefer_service:
            continue
        score = score_item(tokens, product, 'producto')
        if score >= min_score:
            service_matches.append(('producto', score, product))
    if prefer_product:
        service_matches.sort(key=lambda x: x[1], reverse=True)
        return service_matches[:limit]
    groups = action_groups(tokens)
    for service in services:
        service_text = item_text(service)
        if groups and not any(any(term in service_text for term in SERVICE_ACTIONS[group]) for group in groups):
            continue
        if 'scanner' in groups and tokens & {'luz', 'check', 'tablero', 'falla', 'fallas', 'prendida', 'encendida'} and not any(term in service_text for term in ('scanner', 'escaner', 'diagnostico', 'codigo', 'codigos')):
            continue
        score = score_item(tokens, service, 'servicio')
        if score >= min_score:
            service_matches.append(('servicio', score, service))
    service_matches.sort(key=lambda x: x[1], reverse=True)
    if groups:
        diverse = []
        used = set()
        for group in ordered_action_groups(tokens):
            named = [
                match for match in service_matches
                if match[2].get('nombre') not in used
                and any(term in normalize_text(match[2].get('nombre')) for term in SERVICE_ACTIONS[group])
            ]
            if named:
                diverse.append(named[0])
                used.add(named[0][2].get('nombre'))
                continue
            for match in service_matches:
                name = match[2].get('nombre')
                if name in used:
                    continue
                if any(term in item_text(match[2]) for term in SERVICE_ACTIONS[group]):
                    diverse.append(match)
                    used.add(name)
                    break
        for match in service_matches:
            name = match[2].get('nombre')
            if name not in used:
                diverse.append(match)
                used.add(name)
        return diverse[:limit]
    return service_matches[:limit]


def external_summary(query, tokens):
    if not tokens & (SYNONYMS['caucho'] | SYNONYMS['aceite'] | SYNONYMS['filtro'] | SYNONYMS['bateria'] | SYNONYMS['freno']):
        return ''
    cache_key = ' '.join(sorted(tokens))
    cached = _external_cache.get(cache_key)
    if cached and time.time() - cached['time'] < EXTERNAL_CACHE_TTL:
        return cached['text']
    try:
        params = {
            'q': f"{query} automotriz",
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        response = requests.get('https://api.duckduckgo.com/', params=params, timeout=EXTERNAL_TIMEOUT)
        if not response.ok:
            return ''
        data = response.json()
        text = str(data.get('AbstractText') or '').strip()
        if not text:
            topics = data.get('RelatedTopics') or []
            for topic in topics:
                if isinstance(topic, dict) and topic.get('Text'):
                    text = str(topic['Text']).strip()
                    break
        text = re.sub(r'\s+', ' ', text)[:280]
        _external_cache[cache_key] = {'time': time.time(), 'text': text}
        return text
    except Exception:
        return ''


def load_catalog():
    if time.time() - _catalog_cache['time'] < CATALOG_CACHE_TTL:
        return _catalog_cache['products'], _catalog_cache['services']
    try:
        products = ProductModel().get_active()
    except Exception:
        products = []
    try:
        services = ServiceModel().get_active()
    except Exception:
        services = []
    _catalog_cache.update({
        'time': time.time(),
        'products': products or [],
        'services': services or []
    })
    return _catalog_cache['products'], _catalog_cache['services']


def product_line(kind, item):
    name = item.get('nombre') or 'Sin nombre'
    price = item.get('precio')
    stock = item.get('stock')
    price_text = f" - ${float(price):.2f}" if price not in (None, '') else ''
    if kind == 'producto':
        stock_text = f" - stock {int(stock or 0)}" if int(stock or 0) > 0 else " - sin stock registrado"
        return f"{name}{price_text}{stock_text}"
    return f"{name}{price_text}"


def local_context(tokens, clean='', products=None, model_intent='consulta'):
    if (
        model_intent in ('tire_rim', 'tire_vehicle_size')
        or extract_sizes(clean)
        or (extract_rim(clean) and tokens & INVENTORY_TERMS)
        or (tokens & SYNONYMS['caucho'] and (tokens & PRODUCT_TERMS or tokens & VEHICLE_MODEL_TERMS))
    ):
        return tire_size_response(tokens, clean, products or [])
    groups = ordered_action_groups(tokens)
    if 'balanceo' in groups and 'rotacion' in groups:
        return 'Para balancear y rotar cauchos puedes solicitar Balanceo y Rotacion de cauchos. Balanceo corrige vibraciones; Rotacion reparte mejor el desgaste.'
    if 'balanceo' in groups and 'alineacion' in groups:
        return 'Por vibracion o volante irregular conviene revisar Balanceo y Alineacion. Balanceo reduce vibraciones; Alineacion corrige direccion y desgaste irregular.'
    for group in groups:
        if group in SERVICE_HINTS:
            return SERVICE_HINTS[group]
    if tokens & SYNONYMS['allterrain']:
        return LOCAL_KNOWLEDGE['allterrain']
    for key, words in SYNONYMS.items():
        if key in LOCAL_KNOWLEDGE and tokens & words:
            return LOCAL_KNOWLEDGE[key]
    if tokens & {'producto', 'productos', 'catalogo'}:
        return LOCAL_KNOWLEDGE['producto']
    if tokens & {'pedido', 'pedidos'}:
        return LOCAL_KNOWLEDGE['pedido']
    if tokens & {'pago', 'pagos', 'comprobante', 'subo', 'subir', 'cargar'}:
        return LOCAL_KNOWLEDGE['pago']
    if tokens & {'sucursal', 'sucursales', 'ubicacion', 'direccion'}:
        return LOCAL_KNOWLEDGE['sucursal']
    if tokens & {'promocion', 'promociones'}:
        return LOCAL_KNOWLEDGE['promocion']
    return ''


def build_response(question, session_id=None, client_history=None):
    raw = str(question or '').strip()
    if not raw:
        return {'status': 'error', 'message': 'Mensaje requerido.'}, 400
    if len(raw) > MAX_MESSAGE_LENGTH:
        return {'status': 'error', 'message': 'La pregunta no puede superar 255 caracteres.'}, 400

    clean = merge_session_context(normalize_text(raw), session_id, client_history)
    if not clean:
        return {'status': 'error', 'message': 'Mensaje no valido.'}, 400

    tokens = tokenize(clean)
    raw_intent_terms = set(clean.replace('-', ' ').split())
    intent_tokens = tokens | raw_intent_terms
    model_intent, model_confidence = trained_intent(clean)
    products, services = load_catalog()
    category = category_from_tokens(tokens)
    current_product_query = bool(
        category and (
            raw_intent_terms & INVENTORY_TERMS
            or any(any(ch.isdigit() for ch in token) for token in raw_intent_terms)
            or extract_rim(clean)
        )
    )
    if not current_product_query:
        followup_text, followup_matches = followup_response(clean, tokens, session_id, client_history)
        if followup_text:
            update_session_context(session_id, raw, clean, tokens, [], followup_text)
            return {
                'status': 'success',
                'respuesta': followup_text,
                'intent': 'seguimiento',
                'model_intent': model_intent,
                'matches': followup_matches
            }, 200
    if not is_business_question(tokens, products, services):
        return {
            'status': 'success',
            'respuesta': 'Solo puedo ayudarte con productos, servicios, mantenimiento, compras, pagos o pedidos de Transalca.',
            'intent': 'fuera_de_negocio',
            'matches': []
        }, 200

    intent = detect_intent(intent_tokens)
    if model_intent in ('tire_rim', 'tire_vehicle_size', 'tire_allterrain', 'service_balance', 'service_oil') and model_confidence > 0:
        intent = 'recomendacion'
    direct_product_terms = raw_intent_terms & {'pastilla', 'pastillas', 'disco', 'discos', 'bujia', 'bujias'}
    product_question = bool(
        category
        and (raw_intent_terms & INVENTORY_TERMS or model_intent == 'product_lookup' or direct_product_terms)
        and not (explicit_service_request(raw_intent_terms) and not (raw_intent_terms & INVENTORY_TERMS or direct_product_terms))
    )
    product_context = ''
    product_matches = []
    if product_question and not extract_rim(clean):
        product_context, product_matches = product_lookup_response(tokens, products)
    matches = product_matches or find_matches(tokens, products, services, clean=clean)
    context = product_context or local_context(tokens, clean, products, model_intent)
    web_text = external_summary(clean, tokens) if not context else ''

    parts = []
    if context:
        parts.append(context)
    elif web_text:
        parts.append(f"Referencia general: {web_text}")

    rim_query = bool(
        (extract_rim(clean) or extract_sizes(clean))
        and (tokens & SYNONYMS['caucho'] or tokens & INVENTORY_TERMS or extract_sizes(clean))
    )
    product_already_listed = bool(product_context)
    if matches and not rim_query and not product_already_listed:
        lines = [product_line(kind, item) for kind, _, item in matches]
        parts.append('Relacionado en catalogo: ' + '; '.join(lines) + '.')
    elif not parts:
        parts.append('No tengo informacion suficiente en el catalogo para responder eso con seguridad.')

    if intent == 'precio' and matches:
        parts.append('Los precios pueden cambiar; confirma disponibilidad antes de comprar.')
    elif intent in ('recomendacion', 'comparacion') and not matches and not rim_query:
        parts.append('Puedo ayudarte mejor si indicas marca, medida, modelo del vehiculo o tipo de uso.')

    answer = ' '.join(parts)[:900]
    update_session_context(session_id, raw, clean, tokens, matches, answer)
    return {
        'status': 'success',
        'respuesta': answer,
        'intent': intent,
        'model_intent': model_intent,
        'matches': [
            {
                'tipo': kind,
                'nombre': item.get('nombre'),
                'precio': float(item.get('precio') or 0),
                'stock': int(item.get('stock') or 0) if kind == 'producto' else None
            }
            for kind, _, item in matches
        ]
    }, 200
