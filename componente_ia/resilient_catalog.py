"""Fail-fast access to the existing synchronous catalog provider.

Database drivers used by the legacy models do not expose a per-call timeout here.
This adapter therefore permits at most one daemon load per provider, waits only a
small configurable budget, caches successful snapshots, and never queues more
work while a load is still running.
"""

from __future__ import annotations

import os
import threading
import time
import weakref
from typing import Any

from componente_ia.catalog_retriever import CatalogProvider, CatalogSnapshot
from componente_ia.metrics import assistant_metrics


class CatalogAccessTimeout(TimeoutError):
    pass


class ResilientCatalogAccess:
    def __init__(
        self,
        provider: CatalogProvider,
        *,
        wait_timeout: float | None = None,
        cache_ttl: float = 60.0,
        failure_cache_ttl: float = 5.0,
        cooldown: float = 5.0,
    ) -> None:
        self.provider = provider
        self.wait_timeout = max(0.01, float(
            wait_timeout if wait_timeout is not None else os.getenv("ASSISTANT_DB_RETRIEVAL_TIMEOUT", "0.08")
        ))
        self.cache_ttl = max(0.1, float(cache_ttl))
        self.failure_cache_ttl = max(0.1, float(failure_cache_ttl))
        self.cooldown = max(0.1, float(cooldown))
        self._lock = threading.RLock()
        self._snapshot: CatalogSnapshot | None = None
        self._loaded_at = 0.0
        self._loading = False
        self._event: threading.Event | None = None
        self._last_error: str | None = None
        self._last_timeout_at = 0.0

    def load(self, force: bool = False) -> CatalogSnapshot:
        now = time.monotonic()
        with self._lock:
            if not force and self._fresh(now):
                assistant_metrics.record_cache(hit=True)
                return self._snapshot
            if self._loading:

                if self._snapshot is not None:
                    return self._snapshot
                raise CatalogAccessTimeout("catalog load already in progress")
            elif self._last_timeout_at and now - self._last_timeout_at < self.cooldown:
                if self._snapshot is not None:
                    return self._snapshot
                raise CatalogAccessTimeout("catalog load circuit is cooling down")
            else:
                assistant_metrics.record_cache(hit=False)
                event = threading.Event()
                self._event = event
                self._loading = True
                worker = threading.Thread(
                    target=self._load_worker,
                    args=(event, force),
                    name="assistant-catalog-loader",
                    daemon=True,
                )
                worker.start()
        if event is not None and event.wait(self.wait_timeout):
            with self._lock:
                if self._snapshot is not None:
                    return self._snapshot
                raise RuntimeError(self._last_error or "CatalogProviderError")
        with self._lock:
            self._last_timeout_at = time.monotonic()
            if self._snapshot is not None:
                return self._snapshot
        raise CatalogAccessTimeout("catalog provider exceeded retrieval budget")

    def warm(self) -> bool:
        """Start one background load without waiting or queueing another."""

        with self._lock:
            if self._loading or self._fresh(time.monotonic()):
                return False
            event = threading.Event()
            self._event = event
            self._loading = True
            threading.Thread(
                target=self._load_worker,
                args=(event, False),
                name="assistant-catalog-warmer",
                daemon=True,
            ).start()
            return True

    def _load_worker(self, event: threading.Event, force: bool) -> None:
        started = time.perf_counter()
        snapshot = None
        error = None
        try:
            snapshot = self.provider.load(force=force)
        except Exception as exc:
            error = exc.__class__.__name__
        failed_snapshot = bool(snapshot is not None and snapshot.product_error and snapshot.service_error)
        assistant_metrics.record_db_call(
            (time.perf_counter() - started) * 1000.0,
            status="error" if error or failed_snapshot else "ok",
        )
        with self._lock:
            if snapshot is not None:
                self._snapshot = snapshot
                self._loaded_at = time.monotonic()
                self._last_error = None
                self._last_timeout_at = 0.0
            else:
                self._last_error = error or "CatalogProviderError"
            self._loading = False
            event.set()

    def _fresh(self, now: float) -> bool:
        if self._snapshot is None:
            return False
        failed = bool(self._snapshot.product_error or self._snapshot.service_error)
        ttl = self.failure_cache_ttl if failed else self.cache_ttl
        return now - self._loaded_at < ttl

    def health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "loading": self._loading,
                "cached": self._snapshot is not None,
                "cache_age_seconds": round(max(0.0, time.monotonic() - self._loaded_at), 3) if self._snapshot else None,
                "last_error": self._last_error,
                "wait_timeout_seconds": self.wait_timeout,
            }


_REGISTRY_LOCK = threading.RLock()
_REGISTRY: "weakref.WeakKeyDictionary[CatalogProvider, ResilientCatalogAccess]" = weakref.WeakKeyDictionary()


def resilient_catalog_access(provider: CatalogProvider) -> ResilientCatalogAccess:
    with _REGISTRY_LOCK:
        access = _REGISTRY.get(provider)
        if access is None:
            access = ResilientCatalogAccess(provider)
            _REGISTRY[provider] = access
        return access
