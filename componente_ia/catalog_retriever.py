import logging
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from componente_ia.automotive_entities import (
    SERVICE_SYMPTOMS,
    TIRE_TERMS,
    compact_text,
    extract_sizes,
    extract_tire_type,
    normalize_text,
)
from model.product_model import ProductModel
from model.service_model import ServiceModel


logger = logging.getLogger(__name__)


class CatalogError(Exception):
    pass


@dataclass
class CatalogSnapshot:
    products: list[dict] = field(default_factory=list)
    services: list[dict] = field(default_factory=list)
    catalog_available: bool = True
    product_error: str | None = None
    service_error: str | None = None
    loaded_at: float = field(default_factory=time.time)


def decimal_to_float(value, default=None):
    if value in (None, ''):
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def int_value(value, default=0):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def item_text(item):
    return normalize_text(
        ' '.join(str(item.get(key) or '') for key in (
            'codigo', 'nombre', 'descripcion', 'categoria_nombre', 'categoria', 'marca_nombre', 'marca'
        )),
        autocorrect=False,
    )


def normalize_catalog_item(raw, kind):
    text = item_text(raw)
    sizes = extract_sizes(text)
    size = sizes[0].normalized if sizes else None
    rim = sizes[0].rim if sizes else None
    category = raw.get('categoria') or raw.get('categoria_nombre') or ''
    name = str(raw.get('nombre') or 'Sin nombre')
    description = str(raw.get('descripcion') or '')
    brand = str(raw.get('marca') or raw.get('marca_nombre') or '')
    tire_type = extract_tire_type(text, set(text.split()))
    normalized = {
        'kind': kind,
        'raw': raw,
        'codigo': raw.get('codigo') or raw.get('id'),
        'nombre': name,
        'descripcion': description,
        'categoria': category,
        'marca': brand,
        'precio': decimal_to_float(raw.get('precio')),
        'stock': int_value(raw.get('stock')) if kind == 'producto' else None,
        'sucursal': raw.get('sucursal_nombre'),
        'text': text,
        'compact': compact_text(text),
        'sizes': [size_item.normalized for size_item in sizes],
        'size': size,
        'rim': rim,
        'tire_type': tire_type,
        'is_tire': kind == 'producto' and _is_tire_product(category, text, sizes),
    }
    return normalized


def _is_tire_product(category, text, sizes):
    category_clean = normalize_text(category, autocorrect=False)
    return category_clean == 'cauchos' or bool(sizes) or bool(set(text.split()) & TIRE_TERMS)


class CatalogProvider:
    def __init__(self, ttl_seconds=60):
        self.ttl_seconds = ttl_seconds
        self._cache = None
        self._lock = threading.RLock()
        self.last_success_at = None
        self.last_error_at = None

    def load(self, force=False):
        with self._lock:
            if not force and self._cache and time.time() - self._cache.loaded_at < self.ttl_seconds:
                return self._cache
            product_error = None
            service_error = None
            try:
                raw_products = ProductModel().ejecutar("get_active") or []
                products = [normalize_catalog_item(item, 'producto') for item in raw_products if str(item.get('codigo') or '') != 'SIN_PRODUCTO']
            except Exception as exc:
                logger.exception('assistant.catalog.products_failed')
                product_error = exc.__class__.__name__
                products = []
            try:
                raw_services = ServiceModel().ejecutar("get_active") or []
                services = [normalize_catalog_item(item, 'servicio') for item in raw_services]
            except Exception as exc:
                logger.exception('assistant.catalog.services_failed')
                service_error = exc.__class__.__name__
                services = []
            snapshot = CatalogSnapshot(
                products=products,
                services=services,
                catalog_available=not (product_error or service_error),
                product_error=product_error,
                service_error=service_error,
            )
            self._cache = snapshot
            if snapshot.catalog_available:
                self.last_success_at = time.time()
            else:
                self.last_error_at = time.time()
            return snapshot

    def health(self):
        snapshot = self.load(force=False)
        return {
            'available': snapshot.catalog_available,
            'products': len(snapshot.products),
            'services': len(snapshot.services),
            'cached_items': len(snapshot.products) + len(snapshot.services),
            'last_success_at': _iso(self.last_success_at),
            'last_error_at': _iso(self.last_error_at),
            'product_error': snapshot.product_error,
            'service_error': snapshot.service_error,
        }


def _iso(epoch):
    if not epoch:
        return None
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace('+00:00', 'Z')


def product_line(item, include_stock=True):
    name = item.get('nombre') or 'Sin nombre'
    price = item.get('precio')
    price_text = f" - ${price:.2f}" if price not in (None, '') else ''
    stock_text = ''
    if include_stock and item.get('kind') == 'producto':
        stock = int_value(item.get('stock'))
        stock_text = f" - stock {stock}" if stock > 0 else " - sin stock"
    branch = item.get('sucursal') or item.get('sucursal_nombre')
    branch_text = f" - {branch}" if branch else ''
    return f"{name}{price_text}{stock_text}{branch_text}"


def serialize_match(item, compatibility='textual', score=0.0):
    return {
        'tipo': item.get('kind'),
        'nombre': item.get('nombre'),
        'precio': decimal_to_float(item.get('precio')),
        'stock': int_value(item.get('stock')) if item.get('kind') == 'producto' else None,
        'categoria': item.get('categoria'),
        'compatibility': compatibility,
        'score': round(float(score or 0), 3),
    }


def tire_products(products):
    return [item for item in products if item.get('is_tire')]


def active_stock(products):
    return [item for item in products if int_value(item.get('stock')) > 0]


def find_exact_size_products(products, size):
    if not size:
        return []
    normalized = size.upper()
    requested_base = size_base(normalized)
    return [
        item for item in tire_products(products)
        if normalized in item.get('sizes', []) or requested_base in {size_base(value) for value in item.get('sizes', [])}
    ]


def find_rim_products(products, rim):
    if not rim:
        return []
    return [item for item in tire_products(products) if item.get('rim') == int(rim)]


def score_tire_candidate(item, entities, compatible_sizes=None, allow_rim_possible=False):
    compatible_sizes = set(compatible_sizes or [])
    score = 0.0
    compatibility = 'textual'
    constrained = bool(entities.tire_size or compatible_sizes or entities.rim)
    matched_constraint = False
    item_sizes = set(item.get('sizes', []))
    item_size_bases = {size_base(value) for value in item_sizes}

    if entities.tire_size:
        requested = entities.tire_size.normalized
        requested_base = size_base(requested)
        if requested in item_sizes:
            score += 80
            compatibility = 'exacta'
            matched_constraint = True
        elif requested_base in item_size_bases:
            score += 68
            compatibility = 'compatible'
            matched_constraint = True
        else:
            return None
    elif compatible_sizes and (item_sizes & compatible_sizes or item_size_bases & {size_base(value) for value in compatible_sizes}):
        score += 70
        compatibility = 'compatible'
        matched_constraint = True
    elif allow_rim_possible and entities.rim and item.get('rim') == entities.rim:
        score += 25
        compatibility = 'posible'
        matched_constraint = True
    elif entities.rim and item.get('rim') == entities.rim and not compatible_sizes:
        score += 20
        compatibility = 'posible'
        matched_constraint = True
    elif constrained:
        return None

    if entities.tire_type:
        if item.get('tire_type') == entities.tire_type:
            score += 18
        elif item.get('tire_type'):
            score -= 8
    elif item.get('tire_type') == 'A/T' and entities.uses & {'tierra', 'grava', 'lluvia'}:
        score += 8

    if entities.uses:
        score += _terrain_score(item.get('tire_type'), entities.uses)

    stock = int_value(item.get('stock'))
    if stock > 0:
        score += 18
        if stock >= 4:
            score += 3
    else:
        score -= 45

    price = item.get('precio')
    if entities.budget == 'economico' and price is not None:
        score += max(0, 12 - price / 30)
    if entities.max_price:
        score += 8 if price is not None and price <= entities.max_price else -20

    if entities.brand_preference and normalize_text(entities.brand_preference, autocorrect=False) in item.get('text', ''):
        score += 8

    if constrained and not matched_constraint:
        return None
    return {
        'item': item,
        'score': score,
        'compatibility': compatibility,
    }


def size_base(size):
    return re.sub(r'^(LT|P)', '', str(size or '').upper())


def _terrain_score(tire_type, uses):
    if not tire_type:
        return 0
    score = 0
    if tire_type == 'A/T':
        if uses & {'tierra', 'grava', 'lluvia'}:
            score += 12
        if uses & {'autopista', 'ciudad'}:
            score += 4
        if uses & {'barro'}:
            score += 3
    if tire_type == 'M/T':
        if uses & {'barro'}:
            score += 14
        if uses & {'autopista', 'ciudad'}:
            score -= 8
    if tire_type == 'H/T':
        if uses & {'autopista', 'ciudad', 'lluvia'}:
            score += 10
        if uses & {'barro', 'tierra'}:
            score -= 6
    return score


def rank_tire_candidates(products, entities, compatible_sizes=None, allow_rim_possible=False, limit=6):
    ranked = []
    for item in tire_products(products):
        result = score_tire_candidate(item, entities, compatible_sizes, allow_rim_possible)
        if result:
            ranked.append(result)
    ranked.sort(key=lambda entry: (
        0 if int_value(entry['item'].get('stock')) > 0 else 1,
        -entry['score'],
        entry['item'].get('precio') or 0,
        entry['item'].get('nombre') or '',
    ))
    return ranked[:limit]


def search_category(products, category, tokens, limit=4):
    category_clean = normalize_text(category or '', autocorrect=False)
    token_set = set(tokens or [])
    matches = []
    for item in products:
        if normalize_text(item.get('categoria'), autocorrect=False) != category_clean:
            continue
        score = len(token_set & set(item.get('text', '').split()))
        for token in token_set:
            if len(token) >= 3 and compact_text(token) in item.get('compact', ''):
                score += 2
        matches.append({'item': item, 'score': score, 'compatibility': 'textual'})
    matches.sort(key=lambda entry: (
        0 if int_value(entry['item'].get('stock')) > 0 else 1,
        -entry['score'],
        entry['item'].get('precio') or 0,
        entry['item'].get('nombre') or '',
    ))
    return matches[:limit]


def search_tire_text(products, tokens, limit=5):
    token_set = {compact_text(token) for token in (tokens or []) if len(str(token)) >= 2}
    token_set.discard('')
    matches = []
    for item in tire_products(products):
        compact = item.get('compact', '')
        score = 0
        for token in token_set:
            if len(token) >= 3 and token in compact:
                score += 5
        if item.get('size') and compact_text(item.get('size')) in token_set:
            score += 15
        if score:
            matches.append({'item': item, 'score': score, 'compatibility': 'textual'})
    matches.sort(key=lambda entry: (
        0 if int_value(entry['item'].get('stock')) > 0 else 1,
        -entry['score'],
        entry['item'].get('precio') if entry['item'].get('precio') is not None else 10**9,
        entry['item'].get('nombre') or '',
    ))
    return matches[:limit]


def find_services(services, entities, limit=3):
    groups = []
    for group, words in SERVICE_SYMPTOMS.items():
        if entities.tokens & words:
            groups.append(group)
    if not groups and entities.need == 'servicio':
        groups = ['general']

    ranked = []
    for item in services:
        text_tokens = set(item.get('text', '').split())
        score = 0
        for group in groups:
            words = SERVICE_SYMPTOMS.get(group, set())
            score += 20 if words & text_tokens else 0
            if group in item.get('text', ''):
                score += 10
        if entities.tokens & text_tokens:
            score += len(entities.tokens & text_tokens) * 3
        if score:
            ranked.append({'item': item, 'score': score, 'compatibility': 'servicio'})
    ranked.sort(key=lambda entry: (-entry['score'], entry['item'].get('precio') or 0, entry['item'].get('nombre') or ''))
    return ranked[:limit]
