import time

from componente_ia.entity_extractor import extract
from componente_ia.source_quality import classify_domain, evaluate_source
from componente_ia.web_search import SearchProvider, SearchSource, WebSearchService


def _source(title, url, snippet, provider="fake"):
    return SearchSource(
        title=title,
        url=url,
        domain=url.split("/")[2] if "://" in url else "",
        snippet=snippet,
        provider=provider,
        fetched_at=time.time(),
    )


def test_official_matching_source_is_high_quality():
    entities = extract("Ford Explorer 2018")
    source = _source(
        "2018 Ford Explorer owner manual tire information",
        "https://www.ford.com/support/vehicle/explorer/2018/owner-manuals/",
        "Ford Explorer 2018 tire and wheel specifications from the owner manual.",
    )
    quality = evaluate_source(source, entities, "Ford Explorer 2018 tire size")
    assert quality["accepted"] is True
    assert quality["source_type"] in {"fabricante", "manual oficial"}
    assert quality["confidence"] == "alto"


def test_other_model_or_incompatible_year_is_rejected():
    entities = extract("Ford Explorer 2018")
    wrong_model = _source(
        "2018 Ford Escape tire size",
        "https://www.ford.com/escape/2018/",
        "Specifications for Ford Escape 2018.",
    )
    wrong_year = _source(
        "Ford Explorer 2005 tire size",
        "https://www.ford.com/explorer/2005/",
        "Specifications for Ford Explorer 2005.",
    )
    assert evaluate_source(wrong_model, entities)["accepted"] is False
    assert evaluate_source(wrong_year, entities)["accepted"] is False


def test_empty_blocked_spam_and_active_content_are_rejected():
    entities = extract("Toyota Hilux 2020")
    sources = [
        _source("", "https://example.com/page", ""),
        _source("Access denied", "https://example.com/blocked", "Enable JavaScript or solve CAPTCHA"),
        _source("BUY NOW CHEAP", "https://spam.invalid/hilux", "click here casino tire pills"),
        _source("Hilux", "javascript:alert(1)", "<script>alert(1)</script>"),
    ]
    assert all(evaluate_source(source, entities)["accepted"] is False for source in sources)


def test_domain_classifier_distinguishes_source_tiers():
    assert classify_domain("owners.nissanusa.com") == "manual oficial"
    assert classify_domain("michelinman.com") in {"fuente automotriz", "fabricante"}
    assert classify_domain("reddit.com") == "foro"
    assert classify_domain("unknown.invalid") == "desconocida"


class CountingProvider(SearchProvider):
    name = "simulated"

    def __init__(self):
        self.calls = 0

    def search(self, query, max_results=4):
        self.calls += 1
        return [_source("Toyota Hilux 2020 tire", "https://www.toyota.com/hilux/", "Hilux 2020 tire reference", self.name)]


def test_web_service_cache_avoids_duplicate_calls():
    provider = CountingProvider()
    service = WebSearchService(provider=provider, ttl_seconds=60, max_items=4)
    first = service.search("Toyota Hilux 2020 tire", max_results=3)
    second = service.search(" Toyota   Hilux 2020 TIRE ", max_results=3)
    assert first and second
    assert provider.calls == 1


class BrokenProvider(SearchProvider):
    name = "broken"

    def search(self, query, max_results=4):
        raise TimeoutError("private backend detail")


def test_web_failure_returns_empty_and_never_leaks_provider_exception():
    service = WebSearchService(provider=BrokenProvider())
    result = service.search("Hino 500 tire size")
    assert result == []
    health = service.health()
    assert "private backend detail" not in str(health)


def test_inventory_and_local_fitment_do_not_trigger_unneeded_web(assistant):
    provider = assistant.search_service.provider
    assistant.handle("¿Tienen 265/65R17?", session_id="web-policy-1")
    assistant.handle("¿Qué medida usa una Hilux 2020?", session_id="web-policy-2")
    assert provider.calls == []


def test_unknown_vehicle_triggers_web_but_keeps_compatibility_uncertain(assistant):
    provider = assistant.search_service.provider
    payload, _ = assistant.handle("Tengo una Zorak X9 2024, ¿qué cauchos usa?", session_id="web-policy-3")
    assert provider.calls
    assert payload["diagnostics"]["web_attempted"] is True
    assert "validarse" in payload["respuesta"].lower() or "confirmar" in payload["respuesta"].lower()


def test_vehicle_specific_product_recommendation_uses_manual_search_not_web_inventory(assistant):
    provider = assistant.search_service.provider
    assistant.handle("¿Qué batería usa mi Corolla 2018?", session_id="web-policy-4")
    assert provider.calls
    query = provider.calls[-1]["query"].lower()
    assert "official owner manual" in query
    assert "batteries" in query
