import html
import logging
import os
import re
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass
from urllib.parse import parse_qs, unquote, urlparse

import requests


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

    def to_dict(self):
        data = asdict(self)
        data['fetched_at'] = int(self.fetched_at)
        return data


class TTLCache:
    def __init__(self, ttl_seconds=1800, max_items=64):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items = OrderedDict()

    def get(self, key):
        item = self._items.get(key)
        if not item:
            return None
        if time.time() - item['time'] > self.ttl_seconds:
            self._items.pop(key, None)
            return None
        self._items.move_to_end(key)
        return item['value']

    def set(self, key, value):
        self._items[key] = {'time': time.time(), 'value': value}
        self._items.move_to_end(key)
        while len(self._items) > self.max_items:
            self._items.popitem(last=False)

    def clear(self):
        self._items.clear()


class CircuitBreaker:
    def __init__(self, max_failures=3, cooldown_seconds=120):
        self.max_failures = max_failures
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.opened_at = 0

    def allow(self):
        if self.failures < self.max_failures:
            return True
        return time.time() - self.opened_at > self.cooldown_seconds

    def success(self):
        self.failures = 0
        self.opened_at = 0

    def failure(self):
        self.failures += 1
        if self.failures >= self.max_failures:
            self.opened_at = time.time()

    def status(self):
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


class ConfiguredSearchProvider(SearchProvider):
    def __init__(self):
        self.name = 'disabled'
        self.session = requests.Session()
        self.user_agent = os.getenv('ASSISTANT_WEB_USER_AGENT', 'TransalcaAssistant/1.0 (+https://transalca.local)')
        self.connect_timeout = float(os.getenv('ASSISTANT_WEB_CONNECT_TIMEOUT', '2'))
        self.read_timeout = float(os.getenv('ASSISTANT_WEB_READ_TIMEOUT', '4'))
        self.provider = os.getenv('ASSISTANT_SEARCH_PROVIDER', '').strip().lower()
        self.enabled = os.getenv('ASSISTANT_WEB_ENABLED', '1').strip().lower() not in {'0', 'false', 'no'}

    def health(self):
        configured = self.enabled and self._configured_provider() != 'disabled'
        return {
            'provider': self._configured_provider(),
            'configured': configured,
            'enabled': self.enabled,
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
        return 'duckduckgo_html'

    def search(self, query, max_results=4):
        if not self.enabled:
            return []
        provider = self._configured_provider()
        if provider == 'brave':
            return self._search_brave(query, max_results)
        if provider == 'serper':
            return self._search_serper(query, max_results)
        if provider == 'bing':
            return self._search_bing(query, max_results)
        if provider == 'duckduckgo_html':
            return self._search_duckduckgo_html(query, max_results)
        return []

    def _headers(self):
        return {'User-Agent': self.user_agent}

    def _timeout(self):
        return (self.connect_timeout, self.read_timeout)

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
        return [self._source(item.get('title'), item.get('url'), item.get('description'), 'brave') for item in results[:max_results]]

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
        return [self._source(item.get('title'), item.get('link'), item.get('snippet'), 'serper') for item in results[:max_results]]

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
        return [self._source(item.get('name'), item.get('url'), item.get('snippet'), 'bing') for item in results[:max_results]]

    def _search_duckduckgo_html(self, query, max_results):
        response = self.session.post(
            'https://html.duckduckgo.com/html/',
            data={'q': query},
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
                sources.append(self._source(title, url, snippet, 'duckduckgo_html'))
            if len(sources) >= max_results:
                break
        return sources

    def _source(self, title, url, snippet, provider):
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


def source_reliability(domain):
    domain = (domain or '').lower()
    if any(part in domain for part in ('toyota.', 'ford.', 'chevrolet.', 'nissan.', 'honda.', 'mitsubishi.', 'hyundai.', 'kia.')):
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

    def search(self, query, max_results=4):
        if not self.breaker.allow():
            return []
        key = f"{query}|{max_results}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        try:
            results = self.provider.search(query, max_results=max_results)
            self.breaker.success()
            self.cache.set(key, results)
            return results
        except Exception:
            self.breaker.failure()
            logger.exception('assistant.web.search_failed')
            return []

    def health(self):
        provider_health = self.provider.health() if hasattr(self.provider, 'health') else {}
        return {
            **provider_health,
            'circuit': self.breaker.status(),
        }


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

