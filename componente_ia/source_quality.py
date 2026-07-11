import re
import time
from dataclasses import asdict, dataclass
from collections.abc import Mapping
from ipaddress import ip_address
from urllib.parse import urlparse


OFFICIAL_DOMAINS = {
    'toyota.com', 'ford.com', 'nissanusa.com', 'owners.nissanusa.com',
    'mitsubishicars.com', 'owners.mitsubishicars.com', 'vw.com',
    'volkswagen.com', 'hyundaiusa.com', 'owners.hyundaiusa.com',
    'kia.com', 'owners.kia.com', 'honda.com', 'chevrolet.com',
    'ramtrucks.com', 'jeep.com', 'lexus.com', 'macktrucks.com',
    'hino.com', 'hino-global.com', 'isuzu.com', 'isuzucv.com',
    'freightliner.com', 'volvotrucks.com', 'internationaltrucks.com',
}

SPECIALIZED_DOMAINS = {
    'tirerack.com', 'tiresize.com', 'wheel-size.com', 'michelinman.com',
    'bridgestonetire.com', 'goodyear.com', 'continental-tires.com',
    'pirelli.com', 'firestonetire.com',
}

FORUM_MARKERS = ('forum', 'reddit.com', 'club', 'foro')
BLOCKED_MARKERS = (
    'access denied', 'captcha', 'verify you are human', 'enable javascript',
    'just a moment', 'request blocked', 'temporarily unavailable', 'robot check',
)
SPAM_MARKERS = ('casino', 'betting', 'crypto giveaway', 'adult content', 'cheap pills')


@dataclass(frozen=True)
class SourceAssessment:
    domain_allowed: bool
    relevance: float
    source_type: str
    confidence: str
    checked_at: int
    accepted: bool
    reason: str
    reason_code: str
    score: float

    def to_dict(self):
        return asdict(self)


def evaluate_source(source, entities=None, query=''):
    return assess_source(source, entities=entities, query=query).to_dict()


def assess_source(source, entities=None, query=''):
    url = str(_source_value(source, 'url') or '')
    parsed = urlparse(url)
    domain = (_source_value(source, 'domain') or parsed.hostname or '').lower().replace('www.', '')
    title = str(_source_value(source, 'title') or '').strip()
    snippet = str(_source_value(source, 'snippet') or '').strip()
    raw_text = f'{title} {snippet} {parsed.path} {parsed.query}'
    text = _compact(raw_text)
    source_type = classify_domain(domain)
    malicious = (
        _has_malicious_content(title)
        or _has_malicious_content(snippet)
        or not _safe_public_url(parsed)
    )
    empty = not title or not snippet
    blocked = any(marker in raw_text.lower() for marker in BLOCKED_MARKERS)
    spam = any(marker in raw_text.lower() for marker in SPAM_MARKERS) or _looks_like_keyword_spam(raw_text)
    mismatch = _entity_mismatch(raw_text, entities)
    relevance = relevance_score(text, entities)
    rejected = malicious or empty or blocked or spam or bool(mismatch)
    confidence = confidence_level(source_type, relevance, rejected)
    accepted = (not rejected) and relevance >= 0.34 and confidence != 'bajo-rechazado'
    if malicious:
        reason_code, reason = 'unsafe_url_or_content', 'rechazada por URL o contenido potencialmente malicioso'
    elif empty:
        reason_code, reason = 'empty_content', 'rechazada porque título o snippet están vacíos'
    elif blocked:
        reason_code, reason = 'blocked_page', 'rechazada porque la página solo muestra bloqueo o captcha'
    elif spam:
        reason_code, reason = 'spam', 'rechazada por contenido sospechoso o spam'
    elif mismatch:
        reason_code, reason = mismatch, 'rechazada por modelo o año incompatible con la consulta'
    elif relevance < 0.34:
        reason_code, reason = 'low_relevance', 'rechazada por baja coincidencia con marca/modelo/año'
    else:
        reason_code, reason = 'accepted', reason_text(source_type, relevance, False, entities)
    type_weight = {
        'manual oficial': 1.0, 'fabricante': 0.95, 'fuente automotriz': 0.82,
        'tienda especializada': 0.72, 'foro': 0.38, 'desconocida': 0.25,
    }.get(source_type, 0.2)
    score = 0.0 if not accepted else min(1.0, relevance * 0.65 + type_weight * 0.35)
    return SourceAssessment(
        domain_allowed=source_type in {'manual oficial', 'fabricante', 'tienda especializada', 'fuente automotriz'},
        relevance=round(relevance, 3),
        source_type=source_type,
        confidence=confidence,
        checked_at=int(time.time()),
        accepted=bool(accepted),
        reason=reason,
        reason_code=reason_code,
        score=round(score, 3),
    )


def classify_domain(domain):
    domain = (domain or '').lower()
    if any(domain == item or domain.endswith('.' + item) for item in OFFICIAL_DOMAINS):
        if 'owner' in domain or 'manual' in domain:
            return 'manual oficial'
        return 'fabricante'
    if any(domain == item or domain.endswith('.' + item) for item in SPECIALIZED_DOMAINS):
        return 'tienda especializada' if 'tirerack.com' in domain else 'fuente automotriz'
    if any(marker in domain for marker in FORUM_MARKERS):
        return 'foro'
    if domain:
        return 'desconocida'
    return 'desconocida'


def relevance_score(text, entities):
    if not entities:
        return 0.5 if any(term in text for term in ('tire', 'tiresize', 'wheel', 'manual', 'caucho')) else 0.2
    score = 0.0
    checks = 0
    make = _entity_value(entities, 'make')
    model_value = _entity_value(entities, 'model')
    year_value = _entity_value(entities, 'year')
    rim_value = _entity_value(entities, 'requested_rim', 'current_rim', 'rim')
    if make:
        checks += 1
        if _compact(make) in text:
            score += 0.35
        else:
            score -= 0.2
    if model_value:
        checks += 1
        model = _compact(model_value)
        if model and model in text:
            score += 0.35
        elif model:
            score -= 0.35
    if year_value:
        checks += 1
        if str(year_value) in text:
            score += 0.2
        else:
            years = set(re.findall(r'\b(?:19|20)\d{2}\b', text))
            if years:
                score -= 0.35
    if rim_value:
        checks += 1
        if f'r{rim_value}' in text or f'rin{rim_value}' in text or f'/{rim_value}' in text:
            score += 0.1
    if any(term in text for term in ('tire', 'tiresize', 'wheel', 'manual', 'caucho', 'llanta')):
        score += 0.1
    if checks == 0:
        return max(0.0, min(score, 0.6))
    return max(0.0, min(score, 1.0))


def confidence_level(source_type, relevance, malicious=False):
    if malicious:
        return 'bajo-rechazado'
    if source_type in {'manual oficial', 'fabricante'} and relevance >= 0.65:
        return 'alto'
    if source_type in {'tienda especializada', 'fuente automotriz'} and relevance >= 0.55:
        return 'medio'
    if relevance >= 0.45:
        return 'bajo'
    return 'bajo-rechazado'


def reason_text(source_type, relevance, malicious, entities):
    if malicious:
        return 'rechazada por contenido o URL potencialmente maliciosa'
    if relevance < 0.34:
        return 'rechazada por baja coincidencia con marca/modelo/ano'
    label = 'vehiculo consultado'
    if entities:
        parts = [_entity_value(entities, 'make'), _entity_value(entities, 'model'), _entity_value(entities, 'year')]
        label = ' '.join(str(part) for part in parts if part) or label
    return f'aceptada como {source_type} para {label}; validar manual o etiqueta antes de confirmar'


def _has_malicious_content(value):
    text = str(value or '').lower()
    return bool(re.search(r'<\s*script|onerror\s*=|onclick\s*=|onload\s*=|javascript:', text))


def _compact(value):
    return re.sub(r'[^a-z0-9/]+', '', str(value or '').lower())


def _source_value(source, name):
    if isinstance(source, Mapping):
        return source.get(name)
    return getattr(source, name, None)


def _entity_value(entities, *names):
    for name in names:
        if isinstance(entities, Mapping) and entities.get(name) is not None:
            return entities.get(name)
        if entities is not None and getattr(entities, name, None) is not None:
            return getattr(entities, name)
    return None


def _entity_mismatch(raw_text, entities):
    if not entities:
        return None
    normalized = _compact(raw_text)
    expected_model = _compact(_entity_value(entities, 'model'))
    if expected_model and expected_model not in normalized:
        return 'model_mismatch_or_missing'
    expected_year = _entity_value(entities, 'year')
    years = set(re.findall(r'\b(?:19|20)\d{2}\b', raw_text))
    if expected_year and years and str(expected_year) not in years:
        return 'year_mismatch'
    expected_make = _compact(_entity_value(entities, 'make'))
    if expected_make and expected_make not in normalized:
        return 'make_mismatch_or_missing'
    return None


def _safe_public_url(parsed):
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        return False
    hostname = parsed.hostname.lower()
    if hostname in {'localhost'} or hostname.endswith('.local'):
        return False
    try:
        address = ip_address(hostname)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            return False
    except ValueError:
        pass
    return True


def _looks_like_keyword_spam(value):
    tokens = re.findall(r'[a-z0-9]+', str(value or '').lower())
    if len(tokens) < 12:
        return False
    most_common = max((tokens.count(token) for token in set(tokens)), default=0)
    return most_common / len(tokens) > 0.45
