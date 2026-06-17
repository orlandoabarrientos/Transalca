import hashlib
import threading
import time
from collections import Counter, deque


class AssistantMetrics:
    def __init__(self, window_size=2000):
        self.window_size = int(window_size)
        self._lock = threading.RLock()
        self._requests = {
            'total': 0,
            'success': 0,
            'errors': 0,
            'security_rejections': 0,
            'fallbacks': 0,
            'out_of_business': 0,
        }
        self._catalog = {'hits': 0, 'misses': 0}
        self._web = {
            'calls': 0,
            'success': 0,
            'fail': 0,
            'timeout': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
        self._latencies = deque(maxlen=self.window_size)
        self._web_latencies = deque(maxlen=self.window_size)
        self._intents = Counter()
        self._domains = Counter()
        self._errors = Counter()
        self.started_at = time.time()

    def record_request(
        self,
        duration_ms,
        success=True,
        intent=None,
        catalog_available=None,
        match_count=0,
        web_used=False,
        domains=None,
        fallback=False,
        error_type=None,
        security_rejected=False,
    ):
        with self._lock:
            self._requests['total'] += 1
            if success:
                self._requests['success'] += 1
            else:
                self._requests['errors'] += 1
            if security_rejected:
                self._requests['security_rejections'] += 1
            if fallback:
                self._requests['fallbacks'] += 1
            if intent == 'fuera_de_negocio':
                self._requests['out_of_business'] += 1
            if intent:
                self._intents[str(intent)] += 1
            if error_type:
                self._errors[str(error_type)] += 1
            if catalog_available is True:
                self._catalog['hits'] += 1
            elif catalog_available is False:
                self._catalog['misses'] += 1
            for domain in domains or []:
                if domain:
                    self._domains[str(domain)[:120]] += 1
            try:
                self._latencies.append(float(duration_ms))
            except (TypeError, ValueError):
                pass

    def record_web_call(self, duration_ms, status='ok', provider=None, result_count=0, cache_hit=False):
        with self._lock:
            if cache_hit:
                self._web['cache_hits'] += 1
            else:
                self._web['cache_misses'] += 1
                self._web['calls'] += 1
            if status == 'ok' and result_count:
                self._web['success'] += 1
            elif status == 'timeout':
                self._web['timeout'] += 1
            elif not cache_hit:
                self._web['fail'] += 1
            try:
                self._web_latencies.append(float(duration_ms))
            except (TypeError, ValueError):
                pass

    def snapshot(self, runtime=None):
        with self._lock:
            result = {
                'uptime_seconds': round(time.time() - self.started_at, 3),
                'requests': dict(self._requests),
                'latency_ms': self._latency_summary(list(self._latencies)),
                'catalog': dict(self._catalog),
                'web': {
                    **self._web,
                    'latency_ms': self._latency_summary(list(self._web_latencies)),
                },
                'top_intents': dict(self._intents.most_common(10)),
                'top_source_domains': dict(self._domains.most_common(10)),
                'error_types': dict(self._errors.most_common(10)),
            }
        if runtime:
            result['runtime'] = runtime
        return result

    def reset(self):
        with self._lock:
            self.__init__(self.window_size)

    def _latency_summary(self, values):
        if not values:
            return {'count': 0, 'p50': 0.0, 'p95': 0.0, 'p99': 0.0, 'max': 0.0}
        ordered = sorted(values)
        return {
            'count': len(ordered),
            'p50': round(percentile(ordered, 50), 3),
            'p95': round(percentile(ordered, 95), 3),
            'p99': round(percentile(ordered, 99), 3),
            'max': round(max(ordered), 3),
        }


def percentile(sorted_values, pct):
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (len(sorted_values) - 1) * (pct / 100.0)
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    weight = rank - low
    return float(sorted_values[low] * (1 - weight) + sorted_values[high] * weight)


def short_hash(value):
    text = str(value or '')
    if not text:
        return ''
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


assistant_metrics = AssistantMetrics()
