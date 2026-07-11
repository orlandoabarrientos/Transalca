import json
import time

from componente_ia.business_knowledge import (
    BusinessKnowledge,
    CallableBusinessDataProvider,
    ModelBusinessDataProvider,
    ResilientBusinessDataProvider,
)
from componente_ia.catalog_retriever import CatalogSnapshot, normalize_catalog_item
from componente_ia.entity_extractor import extract
from componente_ia.inventory_retriever import InventoryRetriever
from componente_ia.knowledge_types import Evidence
from componente_ia.lightweight_rag import LightweightRAG, RAGDocument
from componente_ia.resilient_catalog import CatalogAccessTimeout, ResilientCatalogAccess
from componente_ia.service_retriever import ServiceRetriever


def product(**overrides):
    raw = {
        "codigo": "P-1",
        "nombre": "Caucho AT 265/65R17",
        "descripcion": "Todo terreno",
        "categoria": "Cauchos",
        "marca": "Marca Segura",
        "precio": 120,
        "stock": 4,
        "sucursal_nombre": "Centro",
    }
    raw.update(overrides)
    return normalize_catalog_item(raw, "producto")


def service(**overrides):
    raw = {
        "id": 7,
        "nombre": "Alineación",
        "descripcion": "Servicio de alineación",
        "precio": 25,
        "duracion_estimada": 45,
        "sucursal_nombre": "Centro",
    }
    raw.update(overrides)
    return normalize_catalog_item(raw, "servicio")


def test_inventory_retriever_accepts_snapshot_and_returns_serializable_grounding():
    snapshot = CatalogSnapshot(products=[product()])
    result = InventoryRetriever(snapshot=snapshot).search_tires(size="265/65R17")
    assert result.status == "ok"
    assert result.evidence[0].data["stock"] == 4
    assert result.evidence[0].data["price"] == 120.0
    assert result.evidence[0].data["match"] == "medida_exacta"
    json.dumps(result.to_dict())


def test_inventory_never_turns_missing_price_or_stock_into_a_fact():
    item = normalize_catalog_item({"codigo": "P-2", "nombre": "Caucho 265/65R17", "categoria": "Cauchos"}, "producto")
    result = InventoryRetriever(snapshot=CatalogSnapshot(products=[item])).search_tires(size="265/65R17")
    data = result.evidence[0].data
    assert data["price"] is None and data["price_available"] is False
    assert data["stock"] is None and data["stock_status"] == "unknown"


def test_inventory_understands_new_canonical_budget_and_usage_entities():
    cheap = product(codigo="CHEAP", nombre="Caucho HT 265/65R17", precio=90)
    expensive = product(codigo="EXP", nombre="Caucho AT 265/65R17", precio=170)
    entities = extract("cauchos 265/65R17 económicos para autopista")
    result = InventoryRetriever(snapshot=CatalogSnapshot(products=[expensive, cheap])).search("", entities=entities)
    assert result.evidence[0].data["code"] == "CHEAP"


def test_inventory_reports_source_failure_instead_of_empty_stock():
    snapshot = CatalogSnapshot(products=[], product_error="DatabaseError", catalog_available=False)
    result = InventoryRetriever(snapshot=snapshot).search("cauchos")
    assert result.status == "unavailable"
    assert not result.available


def test_service_retriever_separates_curated_explanation_and_active_database_fact():
    result = ServiceRetriever(snapshot=CatalogSnapshot(services=[service()])).explain("alignment")
    knowledge = next(item for item in result.evidence if item.kind == "service_knowledge")
    active = next(item for item in result.evidence if item.data.get("availability") == "active")
    assert knowledge.dynamic is False
    assert active.dynamic and active.verified
    assert active.data["price"] == 25.0
    assert active.data["duration"] == 45


def test_service_does_not_claim_price_or_duration_when_database_omits_them():
    active = normalize_catalog_item({"id": 2, "nombre": "Balanceo"}, "servicio")
    result = ServiceRetriever(snapshot=CatalogSnapshot(services=[active])).explain("balancing")
    availability = next(item for item in result.evidence if item.kind == "service_availability")
    assert availability.data["availability"] == "active"
    assert availability.data["price"] is None
    assert availability.data["duration"] is None


def test_service_database_failure_keeps_general_knowledge_but_marks_availability_unknown():
    snapshot = CatalogSnapshot(services=[], service_error="DatabaseError", catalog_available=False)
    result = ServiceRetriever(snapshot=snapshot).recommend("el volante vibra")
    assert any(item.kind == "service_knowledge" and item.verified for item in result.evidence)
    availability = next(item for item in result.evidence if item.kind == "service_availability")
    assert availability.data["availability"] == "unavailable"
    assert not availability.verified
    assert result.partial


def test_business_faq_covers_required_dynamic_topics_without_static_values():
    knowledge = BusinessKnowledge(use_model_provider=False)
    required = {
        "product_categories", "purchase_process", "order_status", "payment_methods",
        "upload_receipt", "branches", "business_hours", "promotions", "warranty",
        "credit", "business_customers", "fleet_service", "contact", "reservations",
        "delivery", "business_policies",
    }
    assert required <= set(knowledge.entries)
    for topic, source in knowledge.dynamic_topics().items():
        entry = knowledge.entries[topic]
        assert entry["value"] == "unavailable"
        assert source


def test_business_dynamic_resolver_marks_only_current_data_verified():
    provider = CallableBusinessDataProvider({"branch_database": lambda topic: [{"name": "Sucursal Prueba"}]})
    knowledge = BusinessKnowledge(data_provider=provider)
    resolved = knowledge.get("branches")
    assert resolved.evidence[0].verified
    assert resolved.evidence[0].data["records"] == [{"name": "Sucursal Prueba"}]
    unresolved = knowledge.get("business_hours")
    assert unresolved.status == "unavailable"
    assert unresolved.evidence[0].data["records"] == []


def test_model_business_adapter_whitelists_payment_fields():
    class FakeModel:
        def ejecutar(self, action):
            assert action == "get_active"
            return [{
                "id": 99, "nombre": "Método de prueba", "moneda": "usd",
                "permite_credito": 1, "datos_pago": "SECRET ACCOUNT",
            }]

    provider = ModelBusinessDataProvider({"payment_methods": FakeModel})
    result = provider.resolve("business_config", "payment_methods")
    assert result.available
    assert result.records == [{"name": "Método de prueba", "currency": "usd", "allows_credit": True}]
    assert "SECRET" not in json.dumps(result.to_dict())


def test_lightweight_rag_handles_accents_and_typo_without_dependencies():
    rag = LightweightRAG([
        RAGDocument(id="pay", title="Métodos de pago", content="Consulta de pagos", keywords=("pagar",)),
        RAGDocument(id="align", title="Alineación", content="Geometría de ruedas", keywords=("alinear",)),
    ])
    assert rag.search("metodos de pago")[0].document.id == "pay"
    assert rag.search("alineasion")[0].document.id == "align"


def test_rag_refuses_private_documents():
    rag = LightweightRAG([
        RAGDocument(id="private", title="secreto", content="token", metadata={"private": True}),
        RAGDocument(id="public", title="cauchos", content="información pública"),
    ])
    assert len(rag) == 1
    assert not rag.search("secreto")


def test_catalog_access_times_out_once_without_queueing_more_workers():
    class SlowProvider:
        def load(self, force=False):
            time.sleep(0.2)
            return CatalogSnapshot()

    access = ResilientCatalogAccess(SlowProvider(), wait_timeout=0.02, cooldown=0.2)
    started = time.perf_counter()
    try:
        access.load()
    except CatalogAccessTimeout:
        pass
    else:
        raise AssertionError("expected timeout")
    first = time.perf_counter() - started
    started = time.perf_counter()
    try:
        access.load()
    except CatalogAccessTimeout:
        pass
    second = time.perf_counter() - started
    assert first < 0.1
    assert second < 0.02


def test_business_resilient_provider_fails_fast_and_does_not_accumulate_calls():
    class SlowProvider:
        def __init__(self):
            self.calls = 0

        def resolve(self, source, topic):
            self.calls += 1
            time.sleep(0.15)
            return None

    slow = SlowProvider()
    provider = ResilientBusinessDataProvider(slow, wait_timeout=0.01)
    assert provider.resolve("branch_database", "branches").error == "dynamic_source_timeout"
    assert provider.resolve("promotion_database", "promotions").error == "dynamic_source_busy"
    assert slow.calls == 1


def test_evidence_serialization_redacts_secret_keys():
    evidence = Evidence(
        id="ev:1", kind="test", source="test", content="ok",
        data={"api_key": "secret", "nested": {"password": "secret"}},
    )
    serialized = evidence.to_dict()
    assert serialized["data"]["api_key"] == "[REDACTED]"
    assert serialized["data"]["nested"]["password"] == "[REDACTED]"

