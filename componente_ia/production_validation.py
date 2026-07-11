"""Pruebas de carga reproducibles y sin dependencias externas obligatorias."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from componente_ia.assistant_orchestrator import AssistantOrchestrator
from componente_ia.business_knowledge import BusinessKnowledge
from componente_ia.catalog_retriever import CatalogSnapshot, normalize_catalog_item
from componente_ia.inventory_retriever import InventoryRetriever
from componente_ia.service_retriever import ServiceRetriever
from componente_ia.web_search import (
    ConfiguredSearchProvider, DisabledSearchProvider, SearchProvider, SearchSource,
    WebSearchService,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = BASE_DIR / "artifacts" / "ia_performance_results.json"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100.0
    low, high = math.floor(rank), math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - rank) + ordered[high] * (rank - low)


def latency_summary(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values), "p50_ms": round(percentile(values, 50), 3),
        "p95_ms": round(percentile(values, 95), 3), "p99_ms": round(percentile(values, 99), 3),
        "max_ms": round(max(values), 3) if values else 0.0,
        "mean_ms": round(statistics.fmean(values), 3) if values else 0.0,
    }


def _catalog(size: int = 80) -> CatalogSnapshot:
    tire_sizes = (
        "165/70R13", "175/65R14", "185/65R15", "195/65R15", "205/55R16",
        "215/60R16", "225/65R17", "235/60R18", "245/70R16", "255/70R16",
        "265/65R17", "265/70R17", "275/55R20", "285/70R17", "295/80R22.5",
        "315/80R22.5", "11R22.5", "12R22.5", "7.50R16", "10.00R20",
    )
    products = []
    for index in range(size):
        tire_size = tire_sizes[index % len(tire_sizes)]
        terrain = ("A/T", "H/T", "M/T")[index % 3]
        products.append(normalize_catalog_item({
            "codigo": f"PERF-{index:05d}",
            "nombre": f"Performance Tire {tire_size} {terrain} #{index}",
            "descripcion": f"Caucho {terrain} de prueba sintética",
            "precio": float(70 + index % 240),
            "stock": index % 17,
            "categoria": "Cauchos",
            "marca": f"Marca{index % 12}",
            "sucursal_nombre": ("Centro", "Norte", "Sur")[index % 3],
        }, "producto"))
    services = [
        {"id": 1, "nombre": "Alineación", "descripcion": "Alineación", "precio": 20, "duracion_estimada": 45, "tipo": "alineacion"},
        {"id": 2, "nombre": "Balanceo", "descripcion": "Balanceo", "precio": 15, "duracion_estimada": 30, "tipo": "balanceo"},
    ]
    return CatalogSnapshot(products=products, services=services, catalog_available=True)


def _assistant(snapshot: CatalogSnapshot | None = None) -> AssistantOrchestrator:
    snapshot = snapshot or _catalog()
    inventory = InventoryRetriever(snapshot=snapshot)
    services = ServiceRetriever(snapshot=snapshot)
    return AssistantOrchestrator(
        inventory=inventory,
        services=services,
        search_service=WebSearchService(provider=DisabledSearchProvider()),
        business=BusinessKnowledge(use_model_provider=False),
    )


class DelayedProvider(SearchProvider):
    name = "simulated_latency"

    def __init__(self, delay: float = 0.02) -> None:
        self.delay = delay

    def search(self, query, max_results=4):
        time.sleep(self.delay)
        return [SearchSource(
            title="Technical tire reference", url="https://www.toyota.com/owners/",
            domain="toyota.com", snippet="Owner manual tire reference.", provider=self.name,
            fetched_at=time.time(), query=query,
        )]


class IntermittentProvider:
    def __init__(self, snapshot: CatalogSnapshot, fail: bool) -> None:
        self.snapshot, self.fail = snapshot, fail

    def load(self, force=False):
        if self.fail:
            raise RuntimeError("database unavailable")
        return self.snapshot


def run_validation(
    *,
    sequential_requests: int = 1000,
    concurrent_requests: int = 100,
    catalog_size: int = 10000,
    soak_iterations: int = 2000,
    live_web: bool = False,
) -> dict[str, Any]:
    previous_web = os.environ.get("ASSISTANT_WEB_ENABLED")
    os.environ["ASSISTANT_WEB_ENABLED"] = "0"
    cpu_started = time.process_time()
    assistant = _assistant()
    errors: list[str] = []


    assistant.handle("¿Qué significa 121/118S?", session_id="warmup-session")
    local_latencies = []
    for index in range(sequential_requests):
        started = time.perf_counter()
        try:
            payload, status = assistant.handle("¿Qué significa 121/118S?", session_id="sequential-session")
            if status != 200 or not payload.get("respuesta"):
                errors.append(f"sequential:{index}")
        except Exception as exc:
            errors.append(f"sequential:{index}:{exc.__class__.__name__}")
        local_latencies.append((time.perf_counter() - started) * 1000.0)

    def concurrent_call(index: int) -> float:
        started = time.perf_counter()
        payload, status = assistant.handle(
            "¿Qué diferencia hay entre alineación y balanceo?",
            session_id=f"concurrent-{index:04d}",
        )
        if status != 200 or not payload.get("respuesta"):
            raise RuntimeError("invalid_response")
        return (time.perf_counter() - started) * 1000.0

    concurrent_latencies = []
    with ThreadPoolExecutor(max_workers=concurrent_requests) as pool:
        futures = [pool.submit(concurrent_call, index) for index in range(concurrent_requests)]
        for future in as_completed(futures):
            try:
                concurrent_latencies.append(future.result())
            except Exception as exc:
                errors.append(f"concurrent:{exc.__class__.__name__}")

    large_snapshot = _catalog(catalog_size)
    large_inventory = InventoryRetriever(snapshot=large_snapshot)
    large_latencies = []
    for _ in range(12):
        started = time.perf_counter()
        result = large_inventory.search_tires("265/65R17", size="265/65R17", limit=6, include_out_of_stock=False)
        large_latencies.append((time.perf_counter() - started) * 1000.0)
        if not result.evidence:
            errors.append("large_catalog:no_results")

    web_service = WebSearchService(provider=DelayedProvider(0.02), ttl_seconds=1, max_items=128)
    web_latencies = []
    for index in range(40):
        started = time.perf_counter()
        result = web_service.search(f"fitment query {index}", max_results=3)
        web_latencies.append((time.perf_counter() - started) * 1000.0)
        if not result:
            errors.append(f"web_simulated:{index}")

    intermittent_latencies = []
    intermittent_success = intermittent_fail = 0
    small_snapshot = _catalog(20)
    for index in range(30):
        retriever = InventoryRetriever(catalog_provider=IntermittentProvider(small_snapshot, fail=index % 3 == 0))
        started = time.perf_counter()
        result = retriever.search("cauchos", filters={"category": "cauchos"}, limit=3)
        intermittent_latencies.append((time.perf_counter() - started) * 1000.0)
        if result.available:
            intermittent_success += 1
        else:
            intermittent_fail += 1

    tracemalloc.start()
    before_current, _ = tracemalloc.get_traced_memory()
    for index in range(soak_iterations):

        assistant.handle("¿Qué significa LT265/70R17?", session_id=f"soak-{index % 260:03d}")
    after_current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    memory_stats = assistant.memory.stats()

    live_result: dict[str, Any] = {"executed": False, "passed": None}
    if live_web:
        os.environ["ASSISTANT_WEB_ENABLED"] = "1"
        provider = ConfiguredSearchProvider()
        live_service = WebSearchService(provider=provider, ttl_seconds=1, max_items=4)
        started = time.perf_counter()
        found = live_service.search("Toyota Hilux 2020 official owner manual tire size", max_results=2)
        elapsed = (time.perf_counter() - started) * 1000.0
        live_result = {
            "executed": True, "results": len(found), "latency_ms": round(elapsed, 3),
            "passed": elapsed < 1500.0,
            "provider": provider.health().get("provider"),
        }

    if previous_web is None:
        os.environ.pop("ASSISTANT_WEB_ENABLED", None)
    else:
        os.environ["ASSISTANT_WEB_ENABLED"] = previous_web

    local = latency_summary(local_latencies)
    concurrent = latency_summary(concurrent_latencies)
    large = latency_summary(large_latencies)
    web = latency_summary(web_latencies)
    intermittent = latency_summary(intermittent_latencies)
    gates = {
        "local_p95_under_150_ms": local["p95_ms"] < 150.0,
        "catalog_10000_p95_under_700_ms": large["p95_ms"] < 700.0,
        "web_p95_under_1500_ms": web["p95_ms"] < 1500.0,
        "concurrency_completed_without_errors": len(concurrent_latencies) == concurrent_requests,
        "db_intermittent_degraded_without_exceptions": intermittent_success > 0 and intermittent_fail > 0,
        "memory_sessions_bounded": memory_stats["sessions"] <= memory_stats["max_sessions"],
        "memory_growth_under_32_mb": after_current - before_current < 32 * 1024 * 1024,
        "no_runtime_errors": not errors,
    }
    if live_web:
        gates["live_web_under_1500_ms"] = bool(live_result["passed"])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "configuration": {
            "sequential_requests": sequential_requests, "concurrent_requests": concurrent_requests,
            "catalog_products": catalog_size, "soak_iterations": soak_iterations,
        },
        "local": local,
        "concurrent_100": concurrent,
        "catalog_10000": large,
        "web_simulated": web,
        "web_live": live_result,
        "database_intermittent": {
            **intermittent, "success_responses": intermittent_success,
            "degraded_responses": intermittent_fail,
        },
        "memory": {
            **memory_stats, "current_growth_bytes": after_current - before_current,
            "peak_traced_bytes": peak,
        },
        "cpu_process_seconds": round(time.process_time() - cpu_started, 3),
        "errors": errors[:50], "gates": gates, "passed": all(gates.values()),
    }


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    command.add_argument("--sequential", type=int, default=1000)
    command.add_argument("--concurrent", type=int, default=100)
    command.add_argument("--catalog-size", type=int, default=10000)
    command.add_argument("--soak", type=int, default=2000)
    command.add_argument("--live-web", action="store_true")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = run_validation(
        sequential_requests=args.sequential,
        concurrent_requests=args.concurrent,
        catalog_size=args.catalog_size,
        soak_iterations=args.soak,
        live_web=args.live_web,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "passed": result["passed"], "local_p95_ms": result["local"]["p95_ms"],
        "catalog_p95_ms": result["catalog_10000"]["p95_ms"],
        "web_p95_ms": result["web_simulated"]["p95_ms"],
        "concurrent_completed": result["concurrent_100"]["count"],
        "memory_growth_bytes": result["memory"]["current_growth_bytes"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["latency_summary", "percentile", "run_validation"]
