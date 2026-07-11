import copy

from componente_ia.case_generator import (
    assert_semantic_invariants,
    build_variation_message,
    normalized_message,
)


def test_local_variations_change_form_without_changing_seed_text_facts():
    base_message = "Tengo una Toyota Hilux 2020 y quiero cauchos A/T rin 17"
    messages = [build_variation_message(base_message, index, "B_light_vehicle_fitment") for index in range(16)]
    assert len({normalized_message(message) for message in messages}) == 16
    assert all("2020" in message and "17" in message for message in messages)


def test_semantic_invariant_rejects_changed_intent():
    base = {
        "category": "A_tires_inventory", "intent": "tire_inventory",
        "entities": {"requested_rim": 17}, "expected_behavior": "Consultar inventario.",
        "must_include": ["inventario"], "must_not_include": ["stock inventado"],
        "critical": False, "message": "¿Tienen rin 17?",
    }
    variation = copy.deepcopy(base)
    variation["message"] = "Consulta rápida: ¿Tienen rin 17?"
    variation["intent"] = "service_list"
    try:
        assert_semantic_invariants(base, variation)
    except ValueError as exc:
        assert "intent" in str(exc)
    else:
        raise AssertionError("Debió rechazar una variación que cambia intención")
