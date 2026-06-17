import re
import time
from urllib.parse import urlparse


OFFICIAL_DOMAINS = {
    'toyota.com', 'ford.com', 'nissanusa.com', 'owners.nissanusa.com',
    'mitsubishicars.com', 'owners.mitsubishicars.com', 'vw.com',
    'volkswagen.com', 'hyundaiusa.com', 'owners.hyundaiusa.com',
    'kia.com', 'owners.kia.com', 'honda.com', 'chevrolet.com',
    'ramtrucks.com', 'jeep.com', 'lexus.com',
}

SPECIALIZED_DOMAINS = {
    'tirerack.com', 'tiresize.com', 'wheel-size.com', 'michelinman.com',
    'bridgestonetire.com', 'goodyear.com', 'continental-tires.com',
    'pirelli.com', 'firestonetire.com',
}

FORUM_MARKERS = ('forum', 'reddit.com', 'club', 'foro')


def evaluate_source(source, entities=None, query=''):
    url = str(getattr(source, 'url', '') or '')
    parsed = urlparse(url)
    domain = (getattr(source, 'domain', '') or parsed.netloc or '').lower().replace('www.', '')
    title = str(getattr(source, 'title', '') or '')
    snippet = str(getattr(source, 'snippet', '') or '')
    text = _compact(f'{title} {snippet} {url} {query}')
    source_type = classify_domain(domain)
    malicious = _has_malicious_content(title) or _has_malicious_content(snippet) or parsed.scheme not in {'http', 'https'}
    relevance = relevance_score(text, entities)
    confidence = confidence_level(source_type, relevance, malicious)
    accepted = (not malicious) and relevance >= 0.34 and confidence != 'bajo-rechazado'
    reason = reason_text(source_type, relevance, malicious, entities)
    return {
        'domain_allowed': source_type in {'manual oficial', 'fabricante', 'tienda especializada', 'fuente automotriz'},
        'relevance': round(relevance, 3),
        'source_type': source_type,
        'confidence': confidence,
        'checked_at': int(time.time()),
        'accepted': bool(accepted),
        'reason': reason,
    }


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
    if getattr(entities, 'make', None):
        checks += 1
        if _compact(entities.make) in text:
            score += 0.35
        else:
            score -= 0.2
    if getattr(entities, 'model', None):
        checks += 1
        model = _compact(entities.model)
        if model and model in text:
            score += 0.35
        elif model:
            score -= 0.35
    if getattr(entities, 'year', None):
        checks += 1
        if str(entities.year) in text:
            score += 0.2
        else:
            years = set(re.findall(r'\b(?:19|20)\d{2}\b', text))
            if years:
                score -= 0.35
    if getattr(entities, 'rim', None):
        checks += 1
        if f'r{entities.rim}' in text or f'rin{entities.rim}' in text or f'/{entities.rim}' in text:
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
        parts = [getattr(entities, 'make', None), getattr(entities, 'model', None), getattr(entities, 'year', None)]
        label = ' '.join(str(part) for part in parts if part) or label
    return f'aceptada como {source_type} para {label}; validar manual o etiqueta antes de confirmar'


def _has_malicious_content(value):
    text = str(value or '').lower()
    return bool(re.search(r'<\s*script|onerror\s*=|onclick\s*=|onload\s*=|javascript:', text))


def _compact(value):
    return re.sub(r'[^a-z0-9/]+', '', str(value or '').lower())
