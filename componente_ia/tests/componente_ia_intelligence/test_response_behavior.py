from componente_ia.catalog_retriever import CatalogSnapshot
from componente_ia.entity_extractor import extract
from componente_ia.guardrails import DOMAIN_RESPONSE
from componente_ia.inventory_retriever import InventoryRetriever
from componente_ia.knowledge_types import Evidence, RetrievalResult
from componente_ia.response_composer import ResponseComposer
from componente_ia.service_retriever import ServiceRetriever
from componente_ia.tire_fitment import TireFitmentRepository, compare_tire_sizes


def test_out_of_scope_response_is_stable_and_brief():
    answer = ResponseComposer().compose("out_of_scope", extract("fútbol"), {}, {})
    assert answer == DOMAIN_RESPONSE


def test_unavailable_inventory_never_invents_product_stock_or_price():
    result = RetrievalResult(
        query="265/65R17", status="unavailable", available=False,
        reason="inventory_source_unavailable",
    )
    answer = ResponseComposer().compose(
        "tire_inventory", extract("¿Tienen 265/65R17?"), {}, {"inventory": result},
    )
    lower = answer.lower()
    assert "no puedo consultar" in lower
    assert "no voy a asumir stock ni precio" in lower
    assert "$" not in answer


def test_inventory_answer_renders_only_database_values_and_labels_same_rim():
    snapshot = CatalogSnapshot(products=[{
        "codigo": "T-1", "nombre": "Caucho 265/65R17 A/T", "precio": 110,
        "stock": 3, "categoria": "Cauchos", "marca": "MarcaDB", "sucursal_nombre": "Centro",
    }], services=[])
    entities = extract("cauchos rin 17")
    result = InventoryRetriever(snapshot=snapshot).search_tires("rin 17", entities=entities)
    answer = ResponseComposer().compose("tire_inventory", entities, {}, {"inventory": result})
    assert "Caucho 265/65R17 A/T" in answer
    assert "stock 3" in answer
    assert "$110.00" in answer
    assert "Centro" in answer
    assert "mismo rin; compatibilidad no confirmada" in answer


def test_service_answer_separates_general_knowledge_from_commercial_status():
    snapshot = CatalogSnapshot(products=[], services=[], catalog_available=False, service_error="down")
    result = ServiceRetriever(snapshot=snapshot).explain("balancing")
    answer = ResponseComposer().compose(
        "service_explanation", extract("cómo funciona el balanceo"), {}, {"services": result},
    )
    lower = answer.lower()
    assert "referencia general" in lower
    assert "cómo funciona" in lower
    assert "no se pudieron verificar" in lower or "requieren consulta" in lower
    assert "$" not in answer


def test_service_price_is_shown_only_when_active_source_has_it():
    active = [{
        "id": 1, "nombre": "Alineación", "descripcion": "Alineación", "precio": 25,
        "duracion_estimada": 45, "tipo": "alineacion", "sucursal_nombre": "Centro",
    }]
    result = ServiceRetriever(snapshot=CatalogSnapshot(products=[], services=active)).explain("alignment")
    answer = ResponseComposer().compose(
        "service_price", extract("precio de alineación"), {}, {"services": result},
    )
    assert "$25.00" in answer
    assert "aparece activo" in answer


def test_tire_size_change_reports_geometry_but_not_compatibility():
    entities = extract("paso de 265/65R17 a 285/70R17")
    comparison = compare_tire_sizes("265/65R17", "285/70R17")
    answer = ResponseComposer().compose(
        "tire_change_compatibility", entities, {}, {"size_comparison": comparison},
    )
    assert "cambia el diámetro" in answer
    assert "%" in answer
    assert "No tengo evidencia suficiente" in answer
    assert "offset" in answer


def test_local_fitment_never_returns_all_records_when_vehicle_or_year_is_missing():
    repository = TireFitmentRepository()
    generic = repository.lookup(extract("quiero cauchos silenciosos para lluvia"))
    missing_year = repository.lookup(extract("tengo una Hilux"))
    assert generic["status"] == "insufficient_data" and generic["sizes"] == []
    assert missing_year["status"] == "insufficient_data" and missing_year["sizes"] == []


def test_fitment_and_inventory_are_visibly_separated():
    entities = extract("Hilux 2020 rin 17")
    inventory = RetrievalResult(query="", available=True, status="empty", evidence=[])
    fitment = {
        "sizes": ["225/70R17", "265/65R17"],
        "disclaimer": "Confirmar con etiqueta y manual.",
    }
    answer = ResponseComposer().compose(
        "tire_size_lookup", entities, {}, {"fitment": fitment, "inventory": inventory},
    )
    assert "Referencia técnica local" in answer
    assert "Inventario Transalca" in answer
    assert "Confirmar con etiqueta y manual" in answer


def test_unverified_dynamic_business_evidence_is_not_presented_as_fact():
    evidence = Evidence(
        id="business:hours", kind="business_knowledge", source="business_config",
        title="Horario", content="El horario debe consultarse en configuración.",
        dynamic=True, verified=False, data={"availability": "unavailable"},
    )
    result = RetrievalResult(query="horario", evidence=[evidence], status="unavailable", available=False)
    answer = ResponseComposer().compose("business_hours", extract("horario"), {}, {"business": result})
    assert "No puedo confirmar" in answer
    assert "9:00" not in answer


def test_technical_answer_uses_supplied_general_evidence_only():
    technical = [Evidence(
        id="technical:load", kind="technical_knowledge", source="curated_local",
        title="Índice dual", content="121/118 indica capacidad distinta en montaje simple y dual; S es el símbolo de velocidad.",
        verified=True, dynamic=False,
    )]
    answer = ResponseComposer().compose(
        "tire_technical_explanation", extract("qué significa 121/118S"), {}, {"technical": technical},
    )
    assert "121/118" in answer
    assert "símbolo de velocidad" in answer


def test_orchestrator_multi_intent_is_grounded_in_inventory(assistant):
    payload, status = assistant.handle(
        "Tengo una Hilux 2020, quiero A/T rin 17 y dime cuál tienen barato",
        session_id="grounded-session",
    )
    assert status == 200
    assert payload["intent"] == "tire_recommendation"
    assert {"tire_inventory", "product_price"} <= set(payload["secondary_intents"])
    assert "RoadMax 265/65R17 A/T" in payload["respuesta"]
    assert "$120.00" in payload["respuesta"]
    assert all("Budget" not in str(item.get("nombre")) for item in payload["matches"])
    assert all(item["stock"] > 0 for item in payload["matches"])


def test_orchestrator_service_comparison_mentions_both_distinct_operations(assistant):
    payload, _ = assistant.handle(
        "¿Qué diferencia hay entre alineación y balanceo?", session_id="service-session",
    )
    lower = payload["respuesta"].lower()
    assert "alineación" in lower
    assert "balanceo" in lower
    assert "geometría" in lower
    assert "masa" in lower
    assert "rotación:" not in lower


def test_orchestrator_technical_code_does_not_invent_capacity(assistant):
    payload, _ = assistant.handle("¿Qué significa 121/118S?", session_id="technical-session")
    answer = payload["respuesta"]
    assert "montaje simple" in answer
    assert "montaje dual" in answer
    assert "tabla técnica" in answer
    assert "kg" not in answer.lower()


def test_orchestrator_handles_db_unavailable_without_dynamic_claims(monkeypatch):
    from componente_ia.assistant_orchestrator import AssistantOrchestrator
    from componente_ia.business_knowledge import BusinessKnowledge
    from componente_ia.web_search import DisabledSearchProvider, WebSearchService

    class Broken:
        def load(self, force=False):
            raise RuntimeError("SELECT password FROM clients")

    monkeypatch.setenv("ASSISTANT_WEB_ENABLED", "0")
    assistant = AssistantOrchestrator(
        catalog_provider=Broken(),
        search_service=WebSearchService(provider=DisabledSearchProvider()),
        business=BusinessKnowledge(use_model_provider=False),
    )
    payload, status = assistant.handle("¿Tienen 265/65R17 y cuánto cuesta?", session_id="broken-db")
    assert status == 200
    assert payload["fallback"] is True
    assert "No puedo consultar el inventario" in payload["respuesta"]
    serialized = str(payload)
    assert "SELECT password" not in serialized
    assert "$0" not in serialized


def test_business_purchase_flow_uses_curated_faq_while_dynamic_policies_fail_closed(assistant):
    purchase, _ = assistant.handle("¿Cómo hago un pedido?", session_id="business-flow-1")
    assert purchase["intent"] == "business_info"
    assert "productos activos" in purchase["respuesta"].lower()
    delivery, _ = assistant.handle("¿Tienen delivery?", session_id="business-flow-2")
    assert delivery["intent"] == "business_info"
    assert "No puedo confirmar" in delivery["respuesta"]


def test_incomplete_tire_recommendation_gives_useful_general_guidance_and_asks_minimum(assistant):
    payload, _ = assistant.handle(
        "Busco algo económico, silencioso y bueno para lluvia", session_id="minimal-help-session",
    )
    answer = payload["respuesta"]
    assert payload["intent"] == "tire_recommendation"
    assert "Orientación general" in answer
    assert "no confirma medida ni fitment" in answer
    assert "Para avanzar" in answer


def test_vehicle_with_missing_year_does_not_receive_unrelated_technical_guidance(assistant):
    payload, _ = assistant.handle(
        "Tengo una Jeep Grand Cherokee, pero no sé el año", session_id="missing-year-session",
    )
    answer = payload["respuesta"]
    assert "No puedo confirmar una medida exacta" in answer
    assert "Para avanzar" in answer
    assert "Cambio de diámetro" not in answer
    assert "Orientación general" not in answer
