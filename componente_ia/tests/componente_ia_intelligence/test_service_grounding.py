from componente_ia.catalog_retriever import CatalogSnapshot
from componente_ia.service_retriever import ServiceRetriever


ACTIVE = [
    {
        "id": 1,
        "nombre": "Alineación",
        "descripcion": "Servicio de alineación",
        "precio": 22.5,
        "duracion_estimada": 45,
        "tipo": "alineacion",
        "sucursal_nombre": "Centro",
    },
    {
        "id": 2,
        "nombre": "Balanceo",
        "descripcion": "Balanceo computarizado",
        "precio": None,
        "duracion_estimada": None,
        "tipo": "balanceo",
        "sucursal_nombre": "Norte",
    },
]


def _retriever(services=ACTIVE, error=None):
    snapshot = CatalogSnapshot(
        products=[], services=services, catalog_available=error is None, service_error=error,
    )
    return ServiceRetriever(snapshot=snapshot)


def _availability(result, service_id):
    return next(
        item for item in result.evidence
        if item.kind == "service_availability" and item.data.get("service_id") == service_id
    )


def test_static_explanation_is_separate_from_active_database_evidence():
    result = _retriever().explain("alignment")
    kinds = [item.kind for item in result.evidence]
    assert kinds == ["service_knowledge", "service_availability"]
    static, dynamic = result.evidence
    assert static.dynamic is False and static.source == "service_knowledge.json"
    assert dynamic.dynamic is True and dynamic.source == "catalog_database"
    assert dynamic.data["availability"] == "active"


def test_price_duration_and_branch_only_come_from_active_database():
    result = _retriever().explain("alignment")
    active = _availability(result, "alignment")
    assert active.data["price"] == 22.5
    assert active.data["price_available"] is True
    assert active.data["duration"] == 45
    assert active.data["duration_available"] is True
    assert active.data["branch"] == "Centro"


def test_null_dynamic_values_are_not_converted_to_zero_or_defaults():
    result = _retriever().explain("balancing")
    active = _availability(result, "balancing")
    assert active.data["availability"] == "active"
    assert active.data["price"] is None
    assert active.data["price_available"] is False
    assert active.data["duration"] is None
    assert active.data["duration_available"] is False


def test_curated_service_not_in_active_catalog_is_not_claimed_as_available():
    result = _retriever().explain("rotation")
    availability = _availability(result, "rotation")
    assert availability.data["availability"] == "inactive_or_unlisted"
    assert availability.data["price"] is None


def test_database_failure_keeps_general_knowledge_but_marks_commercial_data_unknown():
    result = _retriever(services=[], error="DatabaseUnavailable").explain("alignment")
    assert result.partial is True
    static = next(item for item in result.evidence if item.kind == "service_knowledge")
    availability = _availability(result, "alignment")
    assert static.content
    assert availability.verified is False
    assert availability.data["availability"] == "unavailable"
    assert availability.data["price"] is None


def test_list_services_is_strictly_the_active_database_list():
    result = _retriever().list_active()
    assert {item.data["name"] for item in result.evidence} == {"Alineación", "Balanceo"}
    assert all(item.data["availability"] == "active" for item in result.evidence)


def test_symptoms_retrieve_relevant_knowledge_without_claiming_diagnosis():
    vibration = _retriever().recommend("vibra el volante a velocidad")
    service_ids = {
        item.data.get("service_id") for item in vibration.evidence if item.kind == "service_knowledge"
    }
    assert "balancing" in service_ids
    for item in vibration.evidence:
        if item.kind == "service_knowledge":
            assert item.data.get("not_a_substitute_for") is not None

