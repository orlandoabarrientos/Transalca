"""Short multi-turn conversations must retain only the correct session scope."""

import json

import pytest

from .conftest import respond


FOLLOWUPS = [
    ("¿Tienen 265/65R17?", "¿Cuánto cuesta?", "price", "tire_size", "265/65R17"),
    ("¿Tienen 265/65R17?", "¿Cuál es el más barato?", "cheapest", "tire_size", "265/65R17"),
    ("¿Tienen 265/65R17?", "¿Cuál tiene más stock?", "most_stock", "tire_size", "265/65R17"),
    ("¿Tienen 265/65R17?", "¿Hay existencia?", "stock", "tire_size", "265/65R17"),
    ("¿Tienen 295/80R22.5?", "¿Cuánto cuesta?", "price", "tire_size", "295/80R22.5"),
    ("¿Tienen 295/80R22.5?", "¿Cuál es el más barato?", "cheapest", "tire_size", "295/80R22.5"),
    ("¿Tienen 295/80R22.5?", "¿Cuál tiene más stock?", "most_stock", "tire_size", "295/80R22.5"),
    ("¿Tienen 295/80R22.5?", "¿Hay existencia?", "stock", "tire_size", "295/80R22.5"),
    ("¿Tienen 215/75R17.5?", "¿Cuánto cuesta?", "price", "tire_size", "215/75R17.5"),
    ("¿Tienen 235/75R15?", "¿Cuál tiene más stock?", "most_stock", "tire_size", "235/75R15"),
    ("¿Tienen A/T?", "¿Cuánto cuesta?", "price", "tire_type", "A/T"),
    ("¿Tienen A/T?", "¿Cuál es el más barato?", "cheapest", "tire_type", "A/T"),
    ("¿Tienen A/T?", "¿Hay existencia?", "stock", "tire_type", "A/T"),
    ("¿Tienen H/T?", "¿Cuál tiene más stock?", "most_stock", "tire_type", "H/T"),
    ("¿Tienen RoadMax?", "¿Cuánto cuesta?", "price", "brand", "RoadMax"),
    ("¿Tienen Budget?", "¿Cuál es el más barato?", "cheapest", "brand", "Budget"),
    ("¿Tienen Michelin?", "¿Hay existencia?", "stock", "brand", "Michelin"),
    ("¿Tienen 265/65R17?", "Ahora busco 235/75R15", "inventory_by_size", "tire_size", "235/75R15"),
    ("¿Tienen 265/65R17?", "Mejor 295/80R22.5", "inventory_by_size", "tire_size", "295/80R22.5"),
    ("¿Tienen A/T?", "Mejor H/T", "inventory_by_type", "tire_type", "H/T"),
]


@pytest.mark.parametrize("first,followup,intent,key,value", FOLLOWUPS)
def test_inventory_followups_keep_or_replace_explicit_scope(assistant, first, followup, intent, key, value):
    respond(assistant, first)
    result = respond(assistant, followup)
    assert result["intent"] == intent
    assert assistant.state_store.get("lite-test")[key] == value
    assert result["matches"], result
    serialized = json.dumps(result["matches"], ensure_ascii=False)
    assert value.casefold() in serialized.casefold()


def test_cheapest_is_grounded_in_current_size_not_global_catalog(assistant):
    respond(assistant, "¿Tienen 265/65R17?")
    result = respond(assistant, "¿Cuál es el más barato?")
    assert "95" in result["respuesta"]
    assert "Budget" in result["respuesta"]
    assert "235/75R15" not in result["respuesta"]
    assert "80.00" not in result["respuesta"]


def test_most_stock_is_grounded_in_current_size(assistant):
    respond(assistant, "¿Tienen 265/65R17?")
    result = respond(assistant, "¿Cuál tiene más stock?")
    assert "Budget" in result["respuesta"]
    assert "8" in result["respuesta"]
    assert "235/75R15" not in result["respuesta"]


def test_sessions_never_share_tire_size_or_products(assistant):
    respond(assistant, "¿Tienen 265/65R17?", "alice")
    respond(assistant, "¿Tienen 295/80R22.5?", "bob")
    result_a = respond(assistant, "¿Cuánto cuesta?", "alice")
    result_b = respond(assistant, "¿Cuánto cuesta?", "bob")
    assert "265/65R17" in result_a["respuesta"]
    assert "295/80R22.5" not in result_a["respuesta"]
    assert "295/80R22.5" in result_b["respuesta"]
    assert "265/65R17" not in result_b["respuesta"]


def test_reset_session_removes_price_context_and_does_not_reset_others(assistant):
    respond(assistant, "¿Tienen 265/65R17?", "alice")
    respond(assistant, "¿Tienen 295/80R22.5?", "bob")
    assistant.reset_session("alice")
    state = assistant.state_store.get("alice")
    assert not state["tire_size"]
    assert not state["last_products"]
    assert not state["selected_product"]
    assert assistant.state_store.get("bob")["tire_size"] == "295/80R22.5"
    result = respond(assistant, "¿Cuánto cuesta?", "alice")
    assert not result["matches"]
    assert "120" not in result["respuesta"]


def test_unknown_vehicle_does_not_reuse_previous_inventory_for_fitment_or_price(assistant):
    respond(assistant, "¿Tienen 265/65R17?")
    respond(assistant, "Tengo una Hilux")
    respond(assistant, "2020")
    fitment = respond(assistant, "¿Qué caucho usa?")
    price = respond(assistant, "¿Y cuánto cuesta?")
    assert "No tengo esa compatibilidad verificada actualmente." in fitment["respuesta"]
    assert "265/65R17" not in fitment["respuesta"]
    assert not price["matches"]
    assert "120" not in price["respuesta"]
    state = assistant.state_store.get("lite-test")
    assert str(state["vehicle_year"]) == "2020"


def test_user_size_allows_inventory_but_does_not_verify_vehicle(assistant):
    respond(assistant, "Tengo una Hilux 2020")
    inventory = respond(assistant, "La medida que tengo es 265/65R17")
    assert inventory["matches"]
    result = respond(assistant, "¿Qué caucho usa?")
    assert "No tengo esa compatibilidad verificada actualmente." in result["respuesta"]
    assert "compatible" not in result["respuesta"].casefold()


def test_business_question_does_not_erase_followup_inventory_scope(assistant):
    respond(assistant, "¿Tienen 265/65R17?")
    respond(assistant, "¿Aceptan Zelle?")
    result = respond(assistant, "¿Cuál es el más barato?")
    assert "265/65R17" in result["respuesta"]
    assert "95" in result["respuesta"]
