import time

from componente_ia.source_quality import evaluate_source
from componente_ia.web_search import FakeSearchProvider, SearchSource, WebSearchService


def test_source_quality_supports_mapping_and_rejects_wrong_year():
    source = {
        "title": "Toyota Hilux 2019 tire size",
        "snippet": "Toyota Hilux 2019 wheel and tire reference",
        "url": "https://www.toyota.com/hilux/2019",
        "domain": "toyota.com",
    }
    quality = evaluate_source(source, entities={"make": "toyota", "model": "hilux", "year": 2020})
    assert not quality["accepted"]
    assert quality["reason_code"] == "year_mismatch"


def test_source_quality_rejects_empty_blocked_and_suspicious_content():
    base = {"url": "https://example.com/hilux", "domain": "example.com"}
    assert evaluate_source({**base, "title": "Hilux", "snippet": ""})["reason_code"] == "empty_content"
    assert evaluate_source({**base, "title": "Hilux", "snippet": "CAPTCHA verify you are human"})["reason_code"] == "blocked_page"
    assert evaluate_source({**base, "title": "Hilux", "snippet": "casino betting tire data"})["reason_code"] == "spam"


def test_web_service_uses_fake_provider_and_returns_only_validated_evidence():
    source = SearchSource(
        title="Toyota Hilux 2020 tire size",
        snippet="Toyota Hilux 2020 wheel and tire reference",
        url="https://www.toyota.com/hilux/2020",
        domain="toyota.com",
        provider="fake",
        fetched_at=time.time(),
        reliability=0.95,
    )
    fake = FakeSearchProvider([source])
    service = WebSearchService(provider=fake)
    result = service.retrieve(
        "Hilux 2020 tire size", entities={"make": "toyota", "model": "hilux", "year": 2020},
    )
    assert result.status == "ok"
    assert result.evidence[0].verified
    assert fake.calls == [{"query": "Hilux 2020 tire size", "max_results": 4}]

