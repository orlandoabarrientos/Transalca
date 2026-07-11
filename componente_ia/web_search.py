import html
import logging
import os
import re
import threading
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests

from componente_ia.metrics import assistant_metrics
from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id


logger = logging.getLogger(__name__)


class SearchError(Exception):
    pass


@dataclass
class SearchSource:
    title: str
    url: str
    domain: str
    snippet: str
    provider: str
    fetched_at: float
    reliability: float = 0.4
    query: str = ''
    status: str = 'ok'
    quality: dict = field(default_factory=dict)

    def to_dict(self):
        data = asdict(self)
        data['fetched_at'] = int(self.fetched_at)
        return data

    def to_evidence(self):
        quality = dict(self.quality or {})
        return Evidence(
            id=evidence_id('web', self.url, self.query),
            kind='web_source',
            source=self.domain or self.provider,
            title=self.title,
            content=self.snippet,
            confidence=float(quality.get('score', quality.get('relevance', self.reliability)) or 0.0),
            verified=bool(quality.get('accepted', False)),
            dynamic=False,
            data={
                'url': self.url,
                'domain': self.domain,
                'provider': self.provider,
                'quality': quality,
                'status': self.status,
            },
            citations=(self.url,) if self.url else (),
        )


class TTLCache:
    def __init__(self, ttl_seconds=1800, max_items=64):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key):
        with self._lock:
            item = self._items.get(key)
            if not item:
                return None
            if time.time() - item['time'] > self.ttl_seconds:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return item['value']

    def set(self, key, value):
        with self._lock:
            self._items[key] = {'time': time.time(), 'value': value}
            self._items.move_to_end(key)
            while len(self._items) > self.max_items:
                self._items.popitem(last=False)

    def clear(self):
        with self._lock:
            self._items.clear()

    def stats(self):
        with self._lock:
            now = time.time()
            expired = [key for key, item in self._items.items() if now - item['time'] > self.ttl_seconds]
            for key in expired:
                self._items.pop(key, None)
            return {
                'items': len(self._items),
                'max_items': self.max_items,
                'ttl_seconds': self.ttl_seconds,
            }


class CircuitBreaker:
    def __init__(self, max_failures=3, cooldown_seconds=120):
        self.max_failures = max_failures
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.opened_at = 0
        self._lock = threading.RLock()

    def allow(self):
        with self._lock:
            if self.failures < self.max_failures:
                return True
            return time.time() - self.opened_at > self.cooldown_seconds

    def success(self):
        with self._lock:
            self.failures = 0
            self.opened_at = 0

    def failure(self):
        with self._lock:
            self.failures += 1
            if self.failures >= self.max_failures:
                self.opened_at = time.time()

    def status(self):
        with self._lock:
            return {
                'open': not self.allow(),
                'failures': self.failures,
            }


class SearchProvider:
    name = 'base'

    def search(self, query, max_results=4):
        raise NotImplementedError

    def health(self):
        return {'provider': self.name, 'configured': True}


class DisabledSearchProvider(SearchProvider):
    name = 'disabled'

    def search(self, query, max_results=4):
        return []

    def health(self):
        return {'provider': self.name, 'configured': False, 'enabled': False}


class FakeSearchProvider(SearchProvider):
    """Deterministic provider for tests; no network access is performed."""

    name = 'fake'

    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []

    def search(self, query, max_results=4):
        self.calls.append({'query': query, 'max_results': max_results})
        return list(self.results[:max_results])


MockSearchProvider = FakeSearchProvider


class ConfiguredSearchProvider(SearchProvider):
    def __init__(self):
        self.name = 'disabled'
        self.session = requests.Session()
        self.user_agent = os.getenv('ASSISTANT_WEB_USER_AGENT', 'Mozilla/5.0 TransalcaAssistant/1.0')
        self.connect_timeout = float(os.getenv('ASSISTANT_WEB_CONNECT_TIMEOUT', '0.35'))
        self.read_timeout = float(os.getenv('ASSISTANT_WEB_READ_TIMEOUT', '0.85'))
        total_budget = os.getenv('ASSISTANT_WEB_TOTAL_BUDGET', os.getenv('ASSISTANT_WEB_TOTAL_TIMEOUT', '1.3'))
        self.total_timeout = max(0.2, float(total_budget))
        self._budget = threading.local()
        self.provider = os.getenv('ASSISTANT_SEARCH_PROVIDER', '').strip().lower()
        self.enabled = os.getenv('ASSISTANT_WEB_ENABLED', '1').strip().lower() not in {'0', 'false', 'no'}
        self.direct_fitment_enabled = os.getenv('ASSISTANT_DIRECT_FITMENT_ENABLED', '1').strip().lower() not in {'0', 'false', 'no'}

    def health(self):
        configured = self.enabled and self._configured_provider() != 'disabled'
        return {
            'provider': self._configured_provider(),
            'configured': configured,
            'enabled': self.enabled,
            'total_timeout_seconds': self.total_timeout,
        }

    def _configured_provider(self):
        if not self.enabled:
            return 'disabled'
        if self.provider:
            return self.provider
        if os.getenv('BRAVE_SEARCH_API_KEY'):
            return 'brave'
        if os.getenv('SERPER_API_KEY'):
            return 'serper'
        if os.getenv('BING_SEARCH_API_KEY'):
            return 'bing'
        return 'auto'

    def search(self, query, max_results=4):
        if not self.enabled:
            return []
        self._budget.deadline = time.monotonic() + self.total_timeout
        provider = self._configured_provider()
        if provider == 'brave':
            found = self._safe_search(self._search_brave, query, max_results)
            return found or self._fallback_sources(query, max_results)
        if provider == 'serper':
            found = self._safe_search(self._search_serper, query, max_results)
            return found or self._fallback_sources(query, max_results)
        if provider == 'bing':
            found = self._safe_search(self._search_bing, query, max_results)
            return found or self._fallback_sources(query, max_results)
        if provider == 'duckduckgo_html':
            found = self._safe_search(self._search_duckduckgo_html, query, max_results)
            return found or self._fallback_sources(query, max_results)
        if provider == 'duckduckgo_lite':
            found = self._safe_search(self._search_duckduckgo_lite, query, max_results)
            return found or self._fallback_sources(query, max_results)
        if provider == 'duckduckgo_ia':
            return self._safe_search(self._search_duckduckgo_ia, query, max_results)
        return self._fallback_sources(query, max_results)

    def _fallback_sources(self, query, max_results):
        sources = []
        if self.direct_fitment_enabled and self._remaining_budget() > 0.05:
            sources.extend(self._safe_search(self._search_direct_fitment, query, max_results))
            if sources:
                return sources[:max_results]
        if len(sources) < max_results and self._remaining_budget() > 0.05:
            sources.extend(self._dedupe(sources, self._safe_search(self._search_duckduckgo_html, query, max_results - len(sources))))
        if len(sources) < max_results and self._remaining_budget() > 0.05:
            sources.extend(self._dedupe(sources, self._safe_search(self._search_duckduckgo_lite, query, max_results - len(sources))))
        ia_sources = self._safe_search(self._search_duckduckgo_ia, query, max_results) if self._remaining_budget() > 0.05 else []
        if sources and ia_sources:
            sources.extend(self._dedupe(sources, ia_sources))
        return sources[:max_results]

    def _safe_search(self, method, query, max_results):
        if self._remaining_budget() <= 0.05:
            return []
        try:
            return method(query, max_results) or []
        except requests.Timeout:
            logger.info('assistant.web.provider_timeout', extra={'provider': getattr(method, '__name__', 'unknown')})
            return []
        except requests.RequestException:
            logger.info('assistant.web.provider_http_error', extra={'provider': getattr(method, '__name__', 'unknown')})
            return []
        except Exception:
            logger.exception('assistant.web.provider_failed')
            return []

    def _dedupe(self, existing, incoming):
        seen = {source.url for source in existing}
        unique = []
        for source in incoming or []:
            if source.url in seen:
                continue
            seen.add(source.url)
            unique.append(source)
        return unique

    def _headers(self):
        return {'User-Agent': self.user_agent}

    def _timeout(self):
        remaining = max(0.02, self._remaining_budget())
        connect = max(0.01, min(self.connect_timeout, remaining * 0.35))
        read = max(0.01, min(self.read_timeout, remaining - connect))
        return (connect, read)

    def _remaining_budget(self):
        deadline = getattr(self._budget, 'deadline', None)
        if deadline is None:
            return self.total_timeout
        return max(0.0, deadline - time.monotonic())

    def _search_brave(self, query, max_results):
        key = os.getenv('BRAVE_SEARCH_API_KEY')
        if not key:
            return []
        response = self.session.get(
            'https://api.search.brave.com/res/v1/web/search',
            params={'q': query, 'count': max_results},
            headers={**self._headers(), 'X-Subscription-Token': key},
            timeout=self._timeout(),
        )
        response.raise_for_status()
        data = response.json()
        results = data.get('web', {}).get('results') or []
        return [self._source(item.get('title'), item.get('url'), item.get('description'), 'brave', query=query, status='ok') for item in results[:max_results]]

    def _search_serper(self, query, max_results):
        key = os.getenv('SERPER_API_KEY')
        if not key:
            return []
        response = self.session.post(
            'https://google.serper.dev/search',
            json={'q': query, 'num': max_results},
            headers={**self._headers(), 'X-API-KEY': key},
            timeout=self._timeout(),
        )
        response.raise_for_status()
        data = response.json()
        results = data.get('organic') or []
        return [self._source(item.get('title'), item.get('link'), item.get('snippet'), 'serper', query=query, status='ok') for item in results[:max_results]]

    def _search_bing(self, query, max_results):
        key = os.getenv('BING_SEARCH_API_KEY')
        if not key:
            return []
        response = self.session.get(
            'https://api.bing.microsoft.com/v7.0/search',
            params={'q': query, 'count': max_results, 'responseFilter': 'Webpages'},
            headers={**self._headers(), 'Ocp-Apim-Subscription-Key': key},
            timeout=self._timeout(),
        )
        response.raise_for_status()
        data = response.json()
        results = data.get('webPages', {}).get('value') or []
        return [self._source(item.get('name'), item.get('url'), item.get('snippet'), 'bing', query=query, status='ok') for item in results[:max_results]]

    def _search_duckduckgo_html(self, query, max_results):
        response = self.session.get(
            'https://html.duckduckgo.com/html/',
            params={'q': query},
            headers=self._headers(),
            timeout=self._timeout(),
        )
        response.raise_for_status()
        body = response.text[:250000]
        blocks = re.findall(r'(<div class="result(?: result--\w+)?".*?</div>\s*</div>)', body, flags=re.DOTALL)
        sources = []
        for block in blocks:
            title_match = re.search(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, flags=re.DOTALL)
            if not title_match:
                continue
            url = self._clean_ddg_url(html.unescape(title_match.group(1)))
            title = self._strip_html(title_match.group(2))
            snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>|class="result__snippet"[^>]*>(.*?)</div>', block, flags=re.DOTALL)
            snippet = self._strip_html(snippet_match.group(1) or snippet_match.group(2)) if snippet_match else ''
            if self._safe_url(url):
                sources.append(self._source(title, url, snippet, 'duckduckgo_html', query=query, status='ok'))
            if len(sources) >= max_results:
                break
        return sources

    def _search_duckduckgo_lite(self, query, max_results):
        response = self.session.get(
            'https://lite.duckduckgo.com/lite/',
            params={'q': query},
            headers=self._headers(),
            timeout=self._timeout(),
        )
        response.raise_for_status()
        body = response.text[:180000]
        rows = re.findall(r'<a rel="nofollow" href="([^"]+)">(.*?)</a>', body, flags=re.DOTALL)
        sources = []
        for href, title_html in rows:
            url = self._clean_ddg_url(html.unescape(href))
            if not self._safe_url(url):
                continue
            title = self._strip_html(title_html)
            sources.append(self._source(title, url, '', 'duckduckgo_lite', query=query, status='ok'))
            if len(sources) >= max_results:
                break
        return sources

    def _search_duckduckgo_ia(self, query, max_results):
        response = self.session.get(
            'https://api.duckduckgo.com/',
            params={'q': query, 'format': 'json', 'no_html': '1', 'skip_disambig': '1'},
            headers=self._headers(),
            timeout=self._timeout(),
        )
        response.raise_for_status()
        data = response.json()
        url = data.get('AbstractURL') or data.get('AbstractSource')
        snippet = data.get('AbstractText') or data.get('Heading') or ''
        if not url or not self._safe_url(url):
            return []
        title = data.get('Heading') or data.get('AbstractSource') or 'DuckDuckGo Instant Answer'
        return [self._source(title, url, snippet, 'duckduckgo_ia', query=query, status='ok')]

    def _search_direct_fitment(self, query, max_results):
        from componente_ia.entity_extractor import extract as extract_entities

        entities = extract_entities(query)
        if not (entities.make and entities.model and entities.year):
            return []
        for candidate in self._direct_fitment_candidates(entities):
            if self._remaining_budget() <= 0.05:
                break
            try:
                source = self._fetch_direct_source(candidate, entities, query)
            except requests.Timeout:
                continue
            except requests.RequestException:
                continue
            if source:
                return [source]
        return []

    def _direct_fitment_candidates(self, entities):
        make_slug = self._slug(entities.make)
        model_slug = self._model_slug(entities.model)
        display_make = self._display_make(entities.make)
        display_model = self._display_model(entities.model)
        year = entities.year
        tirerack = {
            'url': (
                'https://www.tirerack.com/tires/SelectTireSize.jsp'
                f'?autoMake={quote_plus(display_make)}&autoModel={quote_plus(display_model)}&autoYear={year}'
            ),
            'provider': 'direct_fitment_tirerack',
            'strict': True,
        }
        model_specific = [
            {
                'url': f'https://tiresize.com/tires/{display_make}/{display_model}/{year}/',
                'provider': 'direct_fitment_tiresize',
                'strict': True,
            },
            tirerack,
            {
                'url': f'https://www.wheel-size.com/size/{make_slug}/{model_slug}/{year}/',
                'provider': 'direct_fitment_wheel_size',
                'strict': True,
            },
        ]
        official = self._official_manual_candidate(entities)
        if entities.make == 'ford':
            return [tirerack, official, *[item for item in model_specific if item['provider'] != 'direct_fitment_tirerack']]
        if official and entities.model in {'l200', 'amarok', 'x-trail'}:
            return [official, *model_specific]
        if official:
            return [*model_specific, official]
        return model_specific

    def _official_manual_candidate(self, entities):
        make = entities.make
        model_slug = self._model_slug(entities.model)
        year = entities.year
        urls = {
            'ford': f'https://www.ford.com/support/vehicle/{model_slug}/{year}/owner-manuals/',
            'nissan': 'https://www.nissanusa.com/owners/manuals-guides.html',
            'mitsubishi': 'https://owners.mitsubishicars.com/s/services/ownersmanual',
            'volkswagen': 'https://www.vw.com/en/owners-and-services/about-my-vehicle/owners-manuals.html',
            'toyota': 'https://www.toyota.com/owners/warranty-owners-manuals/',
            'hyundai': 'https://owners.hyundaiusa.com/us/en/resources/manuals-warranties',
            'kia': 'https://owners.kia.com/us/en/manuals.html',
            'jeep': 'https://www.tirerack.com/tires/tiretech/techpage.jsp',
            'ram': 'https://www.tirerack.com/tires/tiretech/techpage.jsp',
        }
        url = urls.get(make)
        if not url:
            return None
        return {'url': url, 'provider': f'direct_manual_{make}', 'strict': False, 'no_body': True}

    def _fetch_direct_source(self, candidate, entities, query):
        response = self.session.get(
            candidate['url'],
            headers=self._headers(),
            timeout=self._timeout(),
            allow_redirects=True,
            stream=bool(candidate.get('no_body')),
        )
        if response.status_code in {403, 404, 405, 429}:
            response.close()
            return None
        response.raise_for_status()
        if candidate.get('no_body'):
            final_url = response.url
            response.close()
            title = self._default_direct_title(entities, candidate)
            snippet = (
                f'External owner manual or tire placard lookup checked for {entities.year} {entities.make} {entities.model}. '
                'Use it as reference only and validate final tire fitment against the vehicle placard and owner manual.'
            )
            return self._source(title, final_url, snippet, candidate['provider'], query=query, status='ok')
        body = response.text[:120000]
        title = self._extract_title(body) or self._default_direct_title(entities, candidate)
        if candidate.get('strict'):
            relevance_text = self._compact_text(f"{title} {candidate['url']} {body[:2000]}")
            relevant = str(entities.year) in relevance_text and self._compact_text(entities.model) in relevance_text
            if not relevant:
                return None
            if self._compact_text(entities.model) not in self._compact_text(title):
                title = self._default_direct_title(entities, candidate)
        elif self._compact_text(entities.make) not in self._compact_text(f"{title} {candidate['url']} {body[:2000]}"):
            title = self._default_direct_title(entities, candidate)
        snippet = self._extract_meta_description(body) or (
            f'External source consulted for {entities.year} {entities.make} {entities.model}. '
            'Use it as reference only and validate final tire fitment against the vehicle placard and owner manual.'
        )
        return self._source(title, response.url, snippet, candidate['provider'], query=query, status='ok')

    def _source(self, title, url, snippet, provider, query='', status='ok'):
        url = str(url or '').strip()
        domain = urlparse(url).netloc.lower().replace('www.', '')
        return SearchSource(
            title=self._strip_html(title)[:120] or domain,
            url=url,
            domain=domain,
            snippet=self._strip_html(snippet)[:500],
            provider=provider,
            fetched_at=time.time(),
            reliability=source_reliability(domain),
            query=query,
            status=status,
        )

    def _strip_html(self, value):
        text = html.unescape(str(value or ''))
        text = re.sub(r'<[^>]+>', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def _clean_ddg_url(self, url):
        parsed = urlparse(url)
        if parsed.netloc.endswith('duckduckgo.com') and parsed.path.startswith('/l/'):
            target = parse_qs(parsed.query).get('uddg', [''])[0]
            return unquote(target)
        return url

    def _safe_url(self, url):
        parsed = urlparse(url)
        return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)

    def _slug(self, value):
        value = str(value or '').strip().lower()
        value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
        return value

    def _model_slug(self, model):
        aliases = {
            'f150': 'f-150',
            'bt50': 'bt-50',
            'cr-v': 'cr-v',
            'd-max': 'd-max',
            'x-trail': 'x-trail',
            '1500': '1500',
        }
        return aliases.get(model, self._slug(model))

    def _display_make(self, make):
        return {
            'ram': 'Ram',
            'volkswagen': 'Volkswagen',
        }.get(make, str(make or '').replace('-', ' ').title().replace(' ', '-'))

    def _display_model(self, model):
        aliases = {
            'x-trail': 'X-Trail',
            'cr-v': 'CR-V',
            'd-max': 'D-Max',
            'f150': 'F-150',
            'bt50': 'BT-50',
            'l200': 'L200',
            '1500': '1500',
        }
        return aliases.get(model, str(model or '').replace('-', ' ').title().replace(' ', '-'))

    def _default_direct_title(self, entities, candidate):
        if candidate.get('provider', '').startswith('direct_manual_'):
            return f'{entities.year} {entities.make} {entities.model} owner manual lookup'
        return f'{entities.year} {entities.make} {entities.model} tire size reference'

    def _extract_title(self, body):
        match = re.search(r'<title[^>]*>(.*?)</title>', body or '', flags=re.DOTALL | re.IGNORECASE)
        return self._strip_html(match.group(1)) if match else ''

    def _extract_meta_description(self, body):
        match = re.search(
            r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)["\']',
            body or '',
            flags=re.DOTALL | re.IGNORECASE,
        )
        return self._strip_html(match.group(1)) if match else ''

    def _compact_text(self, value):
        return re.sub(r'[^a-z0-9]', '', str(value or '').lower())


class DirectFitmentSearchProvider(ConfiguredSearchProvider):
    """Direct official/specialized source lookup without search-engine fallback."""

    name = 'direct_fitment'

    def search(self, query, max_results=4):
        if not self.enabled or not self.direct_fitment_enabled:
            return []
        self._budget.deadline = time.monotonic() + self.total_timeout
        return self._safe_search(self._search_direct_fitment, query, max_results)[:max_results]


class DuckDuckGoSearchProvider(ConfiguredSearchProvider):
    name = 'duckduckgo'

    def __init__(self, mode='html'):
        super().__init__()
        self.mode = mode if mode in {'html', 'lite', 'ia'} else 'html'

    def search(self, query, max_results=4):
        if not self.enabled:
            return []
        self._budget.deadline = time.monotonic() + self.total_timeout
        method = {
            'html': self._search_duckduckgo_html,
            'lite': self._search_duckduckgo_lite,
            'ia': self._search_duckduckgo_ia,
        }[self.mode]
        return self._safe_search(method, query, max_results)[:max_results]


def source_reliability(domain):
    domain = (domain or '').lower()
    if any(part in domain for part in ('toyota.', 'ford.', 'chevrolet.', 'nissan.', 'nissanusa.', 'honda.', 'mitsubishi.', 'mitsubishicars.', 'hyundai.', 'hyundaiusa.', 'kia.', 'vw.com', 'volkswagen.')):
        return 0.95
    if any(part in domain for part in ('tirerack.com', 'michelin', 'bridgestone', 'goodyear', 'continental', 'pirelli', 'firestone')):
        return 0.82
    if any(part in domain for part in ('manual', 'owners', 'carid', 'wheel-size', 'tiresize')):
        return 0.68
    return 0.45


class WebSearchService:
    def __init__(self, provider=None, ttl_seconds=1800, max_items=64):
        self.provider = provider or ConfiguredSearchProvider()
        self.cache = TTLCache(ttl_seconds=ttl_seconds, max_items=max_items)
        self.breaker = CircuitBreaker()
        self._lock = threading.RLock()
        self.last_success_at = None
        self.last_error_at = None
        self._provider_inflight = False

    def search(self, query, max_results=4):
        started = time.perf_counter()
        normalized_query = re.sub(r'\s+', ' ', str(query or '').strip().lower())
        key = f"{normalized_query}|{max_results}"
        with self._lock:
            if not self.breaker.allow():
                assistant_metrics.record_web_call(0, status='blocked', result_count=0)
                return []
            cached = self.cache.get(key)
            if cached is not None:
                assistant_metrics.record_web_call((time.perf_counter() - started) * 1000, status='ok', result_count=len(cached), cache_hit=True)
                return cached
        try:
            results, provider_status = self._provider_search(query, max_results)
            with self._lock:
                if results:
                    self.breaker.success()
                    self.last_success_at = time.time()
                else:
                    self.last_error_at = time.time()
                    if provider_status == 'timeout':
                        self.breaker.failure()
                self.cache.set(key, results)
            metric_status = 'ok' if results else 'timeout' if provider_status == 'timeout' else 'empty'
            assistant_metrics.record_web_call((time.perf_counter() - started) * 1000, status=metric_status, provider=getattr(self.provider, 'name', ''), result_count=len(results or []))
            return results
        except Exception:
            with self._lock:
                self.breaker.failure()
                self.last_error_at = time.time()
            assistant_metrics.record_web_call((time.perf_counter() - started) * 1000, status='error', provider=getattr(self.provider, 'name', ''), result_count=0)
            logger.exception('assistant.web.search_failed')
            return []

    def _provider_search(self, query, max_results):
        """Apply a hard wall-clock budget to network-capable providers.

        ``requests`` timeouts do not include every DNS/resolver delay. A single
        daemon worker plus an in-flight guard keeps the request path bounded and
        prevents a failing network from accumulating queued work.
        """
        budget = getattr(self.provider, 'total_timeout', None)
        if not isinstance(budget, (int, float)) or budget <= 0:
            return self.provider.search(query, max_results=max_results), 'ok'
        with self._lock:
            if self._provider_inflight:
                return [], 'busy'
            self._provider_inflight = True
        event = threading.Event()
        box = {'results': [], 'error': None}

        def worker():
            try:
                box['results'] = self.provider.search(query, max_results=max_results) or []
            except Exception as exc:
                box['error'] = exc
            finally:
                with self._lock:
                    self._provider_inflight = False
                event.set()

        threading.Thread(target=worker, name='assistant-web-provider', daemon=True).start()
        if not event.wait(float(budget)):
            return [], 'timeout'
        if box['error'] is not None:
            raise box['error']
        return box['results'], 'ok'

    def health(self):
        provider_health = self.provider.health() if hasattr(self.provider, 'health') else {}
        with self._lock:
            last_success_at = self.last_success_at
            last_error_at = self.last_error_at
            provider_inflight = self._provider_inflight
        return {
            **provider_health,
            'circuit': self.breaker.status(),
            'last_success_at': int(last_success_at) if last_success_at else None,
            'last_error_at': int(last_error_at) if last_error_at else None,
            'provider_inflight': provider_inflight,
            'cache': self.cache.stats(),
        }

    def search_validated(self, query, *, entities=None, max_results=4, include_rejected=False):
        from componente_ia.source_quality import evaluate_source

        accepted = []
        rejected = []
        for source in self.search(query, max_results=max_results):
            quality = evaluate_source(source, entities=entities, query=query)
            source.quality = quality
            if quality.get('accepted'):
                accepted.append(source)
            else:
                rejected.append(source)
        return (accepted, rejected) if include_rejected else accepted

    def retrieve(self, query, *, entities=None, max_results=4):
        accepted, rejected = self.search_validated(
            query, entities=entities, max_results=max_results, include_rejected=True
        )
        evidence = [source.to_evidence() for source in accepted]
        return RetrievalResult(
            query=query,
            evidence=evidence,
            status='ok' if evidence else 'empty',
            available=True,
            reason=None if evidence else 'no_accepted_web_source',
            diagnostics={
                'accepted_sources': len(accepted),
                'rejected_sources': len(rejected),
                'provider': getattr(self.provider, 'name', ''),
            },
        )


def extract_tire_sizes_from_sources(sources):
    from componente_ia.automotive_entities import extract_sizes

    counts = {}
    evidence = {}
    for source in sources or []:
        text = f"{source.title} {source.snippet}"
        for size in extract_sizes(text):
            key = size.normalized
            counts[key] = counts.get(key, 0) + source.reliability
            evidence.setdefault(key, []).append(source)
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [(size, score, evidence.get(size, [])) for size, score in ranked]
