import re
import unicodedata
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher


METRIC_SIZE_PATTERN = re.compile(r'(?<![a-z0-9])(?P<prefix>lt|p)?\s*(?P<w>\d{3})\s*/\s*(?P<p>\d{2})\s*r\s*(?P<r>\d{2})\b', re.IGNORECASE)
FLOTATION_SIZE_PATTERN = re.compile(r'(?<![a-z0-9])(?P<h>\d{2})\s*x\s*(?P<w>\d{1,2}(?:\.\d{1,2})?)\s*r\s*(?P<r>\d{2})\b', re.IGNORECASE)
RIM_PATTERN = re.compile(r'\b(?:rin|rines|aro|aros|ring|r)\s*-?\s*(?P<rim>\d{2})\b', re.IGNORECASE)
YEAR_PATTERN = re.compile(r'\b(19[8-9]\d|20[0-3]\d)\b')
OIL_PATTERN = re.compile(r'\b\d{1,2}w-?\d{2}\b', re.IGNORECASE)
LOAD_SPEED_PATTERN = re.compile(r'\b\d{2,3}[a-z]\b', re.IGNORECASE)


COMMON_TYPOS = {
    'q': 'que',
    'k': 'que',
    'xq': 'porque',
    'cauchoz': 'cauchos',
    'caucos': 'cauchos',
    'cauxos': 'cauchos',
    'cauhos': 'cauchos',
    'cuchos': 'cauchos',
    'cauchoos': 'cauchos',
    'llnatas': 'llantas',
    'yantas': 'llantas',
    'neumaticoz': 'neumaticos',
    'neumatikos': 'neumaticos',
    'rinn': 'rin',
    'rrin': 'rin',
    'ar': 'aro',
    'vateria': 'bateria',
    'vaterias': 'baterias',
    'bateriaz': 'baterias',
    'aceyte': 'aceite',
    'aseite': 'aceite',
    'aciete': 'aceite',
    'filto': 'filtro',
    'firtro': 'filtro',
    'filtroz': 'filtros',
    'frenoz': 'frenos',
    'pastiya': 'pastilla',
    'pastiyas': 'pastillas',
    'balansear': 'balancear',
    'balansiar': 'balancear',
    'valancear': 'balancear',
    'balanseo': 'balanceo',
    'balansio': 'balanceo',
    'alineasion': 'alineacion',
    'alinasion': 'alineacion',
    'rotasion': 'rotacion',
    'rrotacion': 'rotacion',
    'escanner': 'scanner',
    'escaner': 'scanner',
    'scaner': 'scanner',
    'presio': 'precio',
    'presios': 'precios',
    'kuanto': 'cuanto',
    'toyotaa': 'toyota',
    'toyta': 'toyota',
    'toyyota': 'toyota',
    'hiliux': 'hilux',
    'hiluxx': 'hilux',
    'corola': 'corolla',
    'corrola': 'corolla',
    'forruner': '4runner',
    'forrunner': '4runner',
    'runer': '4runner',
    'runers': '4runner',
    'ai': 'hay',
    'ay': 'hay',
    'stok': 'stock',
    'stoc': 'stock',
    'disponivle': 'disponible',
    'disponibles?': 'disponibles',
    'todoterreno': 'todo terreno',
    'rustikear': 'rustiquear',
    'rustiqueo': 'rustiqueo',
    'baratas': 'barato',
    'baratos': 'barato',
    'economicos': 'economico',
    'economicas': 'economico',
    'silenciosos': 'silencioso',
    'silenciosas': 'silencioso',
    'chillen': 'chillar',
    'suene': 'sonar',
}

SPANISH_NUMBERS = {
    'trece': '13',
    'catorce': '14',
    'quince': '15',
    'dieciseis': '16',
    'diesiseis': '16',
    'dieziseis': '16',
    'diecisiete': '17',
    'diesisiete': '17',
    'dieciocho': '18',
    'diesiocho': '18',
    'diecinueve': '19',
    'diesinueve': '19',
    'veinte': '20',
    'veintiuno': '21',
    'veintidos': '22',
}

VEHICLE_MAKES = {
    'toyota', 'chevrolet', 'ford', 'jeep', 'nissan', 'mitsubishi', 'hyundai',
    'kia', 'honda', 'mazda', 'dodge', 'ram', 'fiat', 'renault', 'volkswagen',
    'vw', 'mercedes', 'benz', 'bmw', 'chery', 'dongfeng', 'jac'
}

MODEL_ALIASES = {
    '4runner': '4runner',
    '4 runner': '4runner',
    'runner': '4runner',
    'forrunner': '4runner',
    'forruner': '4runner',
    'hilux': 'hilux',
    'corolla': 'corolla',
    'yaris': 'yaris',
    'camry': 'camry',
    'rav4': 'rav4',
    'fortuner': 'fortuner',
    'prado': 'prado',
    'machito': 'machito',
    'tacoma': 'tacoma',
    'terios': 'terios',
    'aveo': 'aveo',
    'cruze': 'cruze',
    'silverado': 'silverado',
    'spark': 'spark',
    'fiesta': 'fiesta',
    'explorer': 'explorer',
    'ranger': 'ranger',
    'f150': 'f150',
    'cherokee': 'cherokee',
    'grand cherokee': 'grand cherokee',
    'grand': 'grand',
    'vitara': 'vitara',
    'grand vitara': 'grand vitara',
    'gran vitara': 'grand vitara',
    'frontier': 'frontier',
    'patrol': 'patrol',
    'sentra': 'sentra',
    'l200': 'l200',
    'montero': 'montero',
    'tucson': 'tucson',
    'elantra': 'elantra',
    'accent': 'accent',
    'rio': 'rio',
    'sportage': 'sportage',
    'civic': 'civic',
    'accord': 'accord',
    'bt50': 'bt50',
}

MODEL_MAKE = {
    '4runner': 'toyota',
    'hilux': 'toyota',
    'corolla': 'toyota',
    'yaris': 'toyota',
    'camry': 'toyota',
    'rav4': 'toyota',
    'fortuner': 'toyota',
    'prado': 'toyota',
    'machito': 'toyota',
    'tacoma': 'toyota',
    'terios': 'daihatsu',
    'aveo': 'chevrolet',
    'cruze': 'chevrolet',
    'silverado': 'chevrolet',
    'spark': 'chevrolet',
    'fiesta': 'ford',
    'explorer': 'ford',
    'ranger': 'ford',
    'f150': 'ford',
    'cherokee': 'jeep',
    'grand cherokee': 'jeep',
    'vitara': 'suzuki',
    'grand vitara': 'suzuki',
    'frontier': 'nissan',
    'patrol': 'nissan',
    'sentra': 'nissan',
    'l200': 'mitsubishi',
    'montero': 'mitsubishi',
    'tucson': 'hyundai',
    'elantra': 'hyundai',
    'accent': 'hyundai',
    'rio': 'kia',
    'sportage': 'kia',
    'civic': 'honda',
    'accord': 'honda',
    'bt50': 'mazda',
}

TIRE_TERMS = {
    'caucho', 'cauchos', 'llanta', 'llantas', 'neumatico', 'neumaticos',
    'goma', 'gomas', 'rin', 'rines', 'aro', 'aros', 'rueda', 'ruedas'
}

SERVICE_TERMS = {
    'servicio', 'servicios', 'mantenimiento', 'revision', 'revisar',
    'diagnostico', 'balanceo', 'balancear', 'alineacion', 'alinear',
    'rotacion', 'montaje', 'instalacion', 'cambio', 'cambiar', 'scanner'
}

PRODUCT_TERMS = {
    'producto', 'productos', 'repuesto', 'repuestos', 'catalogo', 'precio',
    'precios', 'comprar', 'compra', 'stock', 'disponible', 'disponibles',
    'tienen', 'tienes', 'hay', 'venden', 'venta'
}

BUSINESS_TERMS = (
    TIRE_TERMS | SERVICE_TERMS | PRODUCT_TERMS | {
        'automotriz', 'carro', 'auto', 'vehiculo', 'camioneta', 'rustiqueo',
        'trocha', 'carretera', 'autopista', 'tierra', 'barro', 'grava',
        'lluvia', 'aceite', 'lubricante', 'filtro', 'filtros', 'bateria',
        'baterias', 'freno', 'frenos', 'pastilla', 'pastillas', 'disco',
        'discos', 'motor', 'pedido', 'pedidos', 'pago', 'pagos',
        'promocion', 'promociones', 'sucursal', 'sucursales', 'volante',
        'vibra', 'vibracion', 'tiembla', 'temblor', 'arranca', 'check',
        'tablero', 'luz', 'ruido', 'chilla', 'remolque', 'carga'
    }
)

FOLLOWUP_TERMS = {
    'barato', 'economico', 'caro', 'mejor', 'ese', 'esa', 'esos', 'esas',
    'sirve', 'stock', 'disponible', 'disponibles', 'otro', 'otra', 'mas',
    'menos', 'primero', 'primera', 'segundo', 'segunda', 'ese?', 'cual'
}

USE_TERMS = {
    'ciudad': {'ciudad', 'urbano'},
    'autopista': {'autopista', 'carretera', 'asfalto', 'viaje'},
    'lluvia': {'lluvia', 'mojado', 'agua'},
    'grava': {'grava', 'piedra'},
    'tierra': {'tierra', 'trocha', 'rustiqueo', 'rustiquear', 'camino'},
    'barro': {'barro', 'lodo', 'fango'},
    'carga': {'carga', 'cargar', 'peso'},
    'remolque': {'remolque', 'remolcar'},
}

SERVICE_SYMPTOMS = {
    'balanceo': {'balanceo', 'balancear', 'balanceado', 'vibracion', 'vibra', 'tiembla', 'temblor', 'volante'},
    'alineacion': {'alineacion', 'alinear', 'desvia', 'jala', 'direccion', 'volante'},
    'rotacion': {'rotacion', 'rotar', 'permutar', 'desgaste'},
    'frenos': {'chilla', 'chirrido', 'frenar', 'ruido'},
    'scanner': {'scanner', 'diagnostico', 'check', 'tablero', 'luz', 'codigo', 'codigos', 'falla'},
    'aceite': set(),
    'bateria': {'arranca', 'arranque', 'prende'},
}

KNOWN_WORDS = sorted(
    BUSINESS_TERMS
    | set(COMMON_TYPOS.values())
    | VEHICLE_MAKES
    | set(MODEL_ALIASES)
    | {word for words in USE_TERMS.values() for word in words}
    | {word for words in SERVICE_SYMPTOMS.values() for word in words}
)


@dataclass
class TireSize:
    raw: str
    normalized: str
    width: int | None = None
    profile: int | None = None
    rim: int | None = None
    prefix: str = ''
    flotation: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class AutomotiveEntities:
    raw: str = ''
    clean: str = ''
    tokens: set[str] = field(default_factory=set)
    intent_hint: str = 'consulta'
    make: str | None = None
    model: str | None = None
    year: int | None = None
    trim: str | None = None
    engine: str | None = None
    tire_size: TireSize | None = None
    all_sizes: list[TireSize] = field(default_factory=list)
    width: int | None = None
    profile: int | None = None
    rim: int | None = None
    tire_type: str | None = None
    uses: set[str] = field(default_factory=set)
    budget: str | None = None
    max_price: float | None = None
    brand_preference: str | None = None
    quantity: int | None = None
    need: str | None = None
    followup: bool = False
    safety_constraints: list[str] = field(default_factory=list)

    def has_vehicle(self):
        return bool(self.make or self.model or self.year)

    def has_tire_request(self):
        return bool(self.tire_size or self.rim or self.tire_type or self.tokens & TIRE_TERMS)

    def to_public_dict(self):
        data = asdict(self)
        data['tokens'] = sorted(self.tokens)
        data['uses'] = sorted(self.uses)
        return data


def _strip_accents(value):
    return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')


def basic_normalize(value):
    text = str(value or '').strip()
    text = re.sub(r'<[^>]*>', ' ', text)
    text = re.sub(r'javascript:|onerror|onclick|onload|script', ' ', text, flags=re.IGNORECASE)
    text = _strip_accents(text).lower()
    replacements = {
        'diez cuarenta': '10w40',
        'cinco treinta': '5w30',
        'quince cuarenta': '15w40',
        'todo-terreno': 'todo terreno',
        'todo terreno': 'todo terreno',
        'todoterreno': 'todo terreno',
        'all-terrain': 'all terrain',
        'mud-terrain': 'mud terrain',
        'highway-terrain': 'highway terrain',
        'dos mil dieciseis': '2016',
        'dos mil diesiseis': '2016',
        'dos mil diecisiete': '2017',
        'dos mil dieciocho': '2018',
        'dos mil diecinueve': '2019',
        'dos mil veinte': '2020',
        'dos mil veintiuno': '2021',
        'dos mil veintidos': '2022',
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r'\b4\s+runner\b', '4runner', text)
    text = re.sub(r'\bgran\s+vitara\b', 'grand vitara', text)
    text = re.sub(r'\bpa\s+', 'para ', text)
    text = re.sub(r'\btengo(4runner)(20\d{2})rin(\d{2})\b', r'\1 \2 rin \3', text)
    text = re.sub(r'\b(4runner)(20\d{2})rin(\d{2})\b', r'\1 \2 rin \3', text)
    text = re.sub(r'\b(a|m|h|r)\s*/\s*t\b', r'\1/t', text)
    text = re.sub(r'\b(\d{1,2})w\s*-?\s*(\d{2})\b', r'\1w-\2', text)
    text = re.sub(r'(?<![a-z0-9])(lt|p)?\s*(\d{3})\s*/\s*(\d{2})\s*r\s*(\d{2})\b', lambda m: f"{m.group(1) or ''}{m.group(2)}/{m.group(3)}r{m.group(4)}", text)
    text = re.sub(r'(?<![a-z0-9])(\d{2})\s*x\s*(\d{1,2}(?:\.\d{1,2})?)\s*r\s*(\d{2})\b', r'\1x\2r\3', text)
    text = re.sub(r'[^a-z0-9/\.\sx-]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _is_technical_token(token):
    return bool(
        METRIC_SIZE_PATTERN.search(token)
        or FLOTATION_SIZE_PATTERN.search(token)
        or OIL_PATTERN.search(token)
        or LOAD_SPEED_PATTERN.search(token)
        or re.fullmatch(r'[amh r]/t', token or '')
        or any(ch.isdigit() for ch in token)
    )


def correct_token(token):
    token = COMMON_TYPOS.get(token, token)
    if token in SPANISH_NUMBERS:
        return SPANISH_NUMBERS[token]
    if len(token) < 4 or _is_technical_token(token):
        return token
    if token in KNOWN_WORDS:
        return token
    best = ''
    best_score = 0.0
    for candidate in KNOWN_WORDS:
        if abs(len(candidate) - len(token)) > 2:
            continue
        score = SequenceMatcher(None, token, candidate).ratio()
        if score > best_score:
            best = candidate
            best_score = score
    return best if best_score >= 0.86 else token


def normalize_text(value, autocorrect=True):
    text = basic_normalize(value)
    if not autocorrect:
        return text
    return ' '.join(correct_token(token) for token in text.split())


def tokenize(value, autocorrect=True):
    clean = normalize_text(value, autocorrect=autocorrect)
    return {token.strip('.,;:?') for token in re.split(r'[\s-]+', clean) if token.strip('.,;:?')}


def compact_text(value):
    return re.sub(r'[^a-z0-9]', '', normalize_text(value, autocorrect=False))


def extract_sizes(value):
    clean = basic_normalize(value)
    sizes = []
    seen = set()
    for match in METRIC_SIZE_PATTERN.finditer(clean):
        prefix = (match.group('prefix') or '').upper()
        width = int(match.group('w'))
        profile = int(match.group('p'))
        rim = int(match.group('r'))
        normalized = f"{prefix}{width}/{profile}R{rim}"
        if normalized not in seen:
            seen.add(normalized)
            sizes.append(TireSize(match.group(0).upper().replace(' ', ''), normalized, width, profile, rim, prefix, False))
    for match in FLOTATION_SIZE_PATTERN.finditer(clean):
        rim = int(match.group('r'))
        normalized = f"{match.group('h')}X{match.group('w')}R{rim}".upper()
        if normalized not in seen:
            seen.add(normalized)
            sizes.append(TireSize(match.group(0).upper().replace(' ', ''), normalized, None, None, rim, '', True))
    return sizes


def extract_rim(value):
    sizes = extract_sizes(value)
    if sizes and sizes[0].rim:
        return sizes[0].rim
    clean = normalize_text(value)
    match = RIM_PATTERN.search(clean)
    if match:
        return int(match.group('rim'))
    tokens = clean.split()
    for index, token in enumerate(tokens[:-1]):
        if token in {'rin', 'rines', 'aro', 'aros'} and tokens[index + 1] in SPANISH_NUMBERS.values():
            return int(tokens[index + 1])
    return None


def extract_year(value):
    years = [int(match.group(1)) for match in YEAR_PATTERN.finditer(str(value or ''))]
    return years[0] if years else None


def extract_vehicle(clean, tokens):
    make = None
    model = None
    token_list = clean.split()
    for word in token_list:
        if word in VEHICLE_MAKES:
            make = 'volkswagen' if word == 'vw' else word
            break

    joined = ' '.join(token_list)
    for alias in sorted(MODEL_ALIASES, key=len, reverse=True):
        if re.search(rf'\b{re.escape(alias)}\b', joined):
            model = MODEL_ALIASES[alias]
            break

    if model == 'grand' and 'cherokee' in tokens:
        model = 'grand cherokee'
    if model and not make:
        make = MODEL_MAKE.get(model)
    return make, model


def extract_tire_type(clean, tokens):
    joined = f" {clean} "
    tire_context = bool(tokens & TIRE_TERMS) or bool(tokens & {'camioneta', 'rustiqueo', 'rustiquear'})
    if re.search(r'\bm/t\b', clean) or ' mt ' in joined or {'mud', 'terrain'} <= tokens or tokens & {'barro', 'lodo', 'pantano'}:
        return 'M/T'
    if re.search(r'\ba/t\b', clean) or ' at ' in joined or 'at' in tokens or {'carretera', 'tierra'} <= tokens or {'autopista', 'tierra'} <= tokens or {'all', 'terrain'} <= tokens or {'todo', 'terreno'} <= tokens or ' todo terreno' in joined or tokens & {'mixto', 'mixta', 'guerrero', 'guerrera', 'rustiqueo', 'rustiquear'}:
        return 'A/T'
    if re.search(r'\bh/t\b', clean) or ' ht ' in joined or {'highway', 'terrain'} <= tokens or tokens & {'carretera', 'autopista', 'asfalto'}:
        return 'H/T'
    if tire_context and tokens & {'silencioso', 'comodidad', 'consumo', 'chillar'}:
        return 'H/T'
    if re.search(r'\br/t\b', clean) or {'rugged', 'terrain'} <= tokens:
        return 'R/T'
    if ' at ' in joined and tokens & TIRE_TERMS:
        return 'A/T'
    if ' mt ' in joined and tokens & TIRE_TERMS:
        return 'M/T'
    if ' ht ' in joined and tokens & TIRE_TERMS:
        return 'H/T'
    return None


def extract_uses(tokens):
    uses = set()
    for use, words in USE_TERMS.items():
        if tokens & words:
            uses.add(use)
    return uses


def extract_budget(clean, tokens):
    max_price = None
    budget = None
    match = re.search(r'\b(?:menos de|hasta|maximo|max)\s*\$?\s*(\d+(?:\.\d+)?)\b', clean)
    if match:
        max_price = float(match.group(1))
        budget = 'maximo'
    if tokens & {'barato', 'economico', 'economica', 'menor', 'menos'}:
        budget = 'economico'
    if tokens & {'premium', 'mejor', 'calidad'}:
        budget = budget or 'calidad'
    return budget, max_price


def extract_quantity(tokens):
    for token in tokens:
        if token.isdigit():
            value = int(token)
            if 1 <= value <= 12:
                return value
    return None


def infer_need(tokens):
    if tokens & TIRE_TERMS:
        return 'producto'
    if tokens & SERVICE_TERMS or any(tokens & words for words in SERVICE_SYMPTOMS.values()):
        return 'servicio'
    if tokens & {'pedido', 'pedidos', 'pago', 'pagos'}:
        return 'pedido'
    if tokens & PRODUCT_TERMS:
        return 'producto'
    return None


def detect_followup(tokens):
    has_product_context = bool(tokens & (TIRE_TERMS | SERVICE_TERMS | PRODUCT_TERMS))
    return len(tokens) <= 6 and bool(tokens & FOLLOWUP_TERMS) and not has_product_context


def detect_intent_hint(entities):
    tokens = entities.tokens
    if detect_followup(tokens):
        return 'seguimiento'
    if tokens & {'pedido', 'pedidos', 'pago', 'pagos', 'comprobante'}:
        return 'pedido'
    if entities.tire_size or entities.rim or entities.tire_type or tokens & TIRE_TERMS:
        service_explicit = tokens & {'balanceo', 'balancear', 'alineacion', 'alinear', 'rotacion', 'montaje', 'instalacion', 'scanner'}
        if service_explicit and not (entities.tire_size or entities.rim or entities.tire_type):
            return 'servicio'
        if tokens & {'comparar', 'comparacion', 'diferencia', 'comparame', 'compara'}:
            return 'comparacion_cauchos'
        if tokens & {'codigo', 'tir'}:
            return 'inventario_cauchos'
        if entities.tire_size and not entities.has_vehicle():
            return 'inventario_cauchos'
        if entities.has_vehicle() and not entities.tire_size:
            return 'medida_caucho'
        if entities.rim and tokens & TIRE_TERMS and not entities.has_vehicle():
            return 'inventario_cauchos'
        if tokens & {'stock', 'disponible', 'disponibles', 'tienen', 'tienes', 'hay', 'venden', 'precio', 'precios', 'codigo'}:
            return 'inventario_cauchos'
        return 'recomendacion_cauchos'
    if any(tokens & words for words in SERVICE_SYMPTOMS.values()) or tokens & SERVICE_TERMS:
        return 'servicio'
    if tokens & PRODUCT_TERMS:
        return 'producto'
    return 'consulta'


def is_business_related(entities):
    if entities.tire_size or entities.has_vehicle():
        return True
    if entities.tokens & BUSINESS_TERMS:
        return True
    if any(entities.tokens & words for words in SERVICE_SYMPTOMS.values()):
        return True
    return False


def extract_entities(value):
    raw = str(value or '').strip()
    clean = normalize_text(raw)
    tokens = tokenize(raw)
    sizes = extract_sizes(raw)
    make, model = extract_vehicle(clean, tokens)
    tire_size = sizes[0] if sizes else None
    rim = tire_size.rim if tire_size else extract_rim(raw)
    budget, max_price = extract_budget(clean, tokens)
    entities = AutomotiveEntities(
        raw=raw,
        clean=clean,
        tokens=tokens,
        make=make,
        model=model,
        year=extract_year(clean) or extract_year(raw),
        tire_size=tire_size,
        all_sizes=sizes,
        width=tire_size.width if tire_size else None,
        profile=tire_size.profile if tire_size else None,
        rim=rim,
        tire_type=extract_tire_type(clean, tokens),
        uses=extract_uses(tokens),
        budget=budget,
        max_price=max_price,
        quantity=extract_quantity(tokens),
        need=infer_need(tokens),
        followup=detect_followup(tokens) or clean.startswith('y '),
    )
    entities.intent_hint = 'seguimiento' if entities.followup else detect_intent_hint(entities)
    if entities.tire_size and entities.tire_size.prefix in {'LT', 'P'}:
        entities.safety_constraints.append('validar indice de carga y velocidad indicado por el fabricante')
    return entities
