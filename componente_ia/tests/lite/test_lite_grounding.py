"""Commercial answers use only the source fields actually supplied."""

from copy import deepcopy
import json

import pytest

from .conftest import PRODUCTS, respond


MISSING = "No tengo esa información configurada/verificada actualmente."


def test_public_payment_methods_are_restricted_to_configured_allowlist(assistant):
    result = respond(assistant, "¿Qué métodos de pago aceptan?")
    assert "Pago Móvil" in result["respuesta"]
    assert "Binance" in result["respuesta"]
    assert "Zelle" in result["respuesta"]
    assert "Tarjeta" not in result["respuesta"]


def test_missing_payment_methods_are_not_filled_from_allowlist(assistant_factory):
    assistant = assistant_factory(business_records={})
    assert respond(assistant, "¿Qué métodos de pago aceptan?")["respuesta"] == MISSING


def test_requested_payment_method_is_not_claimed_unless_configured(assistant_factory):
    assistant = assistant_factory(business_records={"payment_methods": [{"name": "Binance"}]})
    result = respond(assistant, "¿Aceptan Zelle?")
    assert "Actualmente aceptamos: Zelle" not in result["respuesta"]
    assert "sí" not in result["respuesta"].casefold()


@pytest.mark.parametrize("message", ["¿Dónde están ubicados?", "¿Qué categorías tienen?"])
def test_missing_business_data_is_not_invented(assistant_factory, message):
    assistant = assistant_factory(products=[], business_records={})
    assert respond(assistant, message)["respuesta"] == MISSING


def test_service_list_contains_only_active_fixture_services(assistant):
    result = respond(assistant, "¿Qué servicios tienen?")
    assert "Alineación" in result["respuesta"]
    assert "Balanceo" in result["respuesta"]
    assert "frenos" not in result["respuesta"].casefold()
    assert "scanner" not in result["respuesta"].casefold()


def test_no_active_services_does_not_advertise_static_knowledge(assistant_factory):
    assistant = assistant_factory(services=[])
    assert respond(assistant, "¿Qué servicios tienen?")["respuesta"] == MISSING


def test_service_outage_fails_closed(assistant_factory):
    assistant = assistant_factory(service_error="DatabaseUnavailable")
    assert respond(assistant, "¿Qué servicios tienen?")["respuesta"] == MISSING


def test_price_response_uses_exact_fixture_price_and_stock(assistant_factory):
    assistant = assistant_factory(products=[PRODUCTS[0]])
    result = respond(assistant, "¿Cuánto cuesta 265/65R17?")
    assert "RoadMax" in result["respuesta"]
    assert "120" in result["respuesta"]
    assert "4" in result["respuesta"]
    assert "95" not in result["respuesta"]


def test_missing_price_is_never_zero_or_an_estimate(assistant_factory):
    product = deepcopy(PRODUCTS[0])
    product.pop("precio")
    assistant = assistant_factory(products=[product])
    result = respond(assistant, "¿Cuánto cuesta 265/65R17?")
    assert "cuesta 0" not in result["respuesta"]
    assert "$0" not in result["respuesta"]
    assert "120" not in result["respuesta"]
    assert "configurada" in result["respuesta"] or "verificad" in result["respuesta"]


def test_missing_stock_is_never_presented_as_zero_or_positive(assistant_factory):
    product = deepcopy(PRODUCTS[0])
    product.pop("stock")
    assistant = assistant_factory(products=[product])
    result = respond(assistant, "¿Cuánto cuesta 265/65R17?")
    assert "Stock disponible: 0" not in result["respuesta"]
    assert "Stock disponible: 4" not in result["respuesta"]


def test_inventory_outage_does_not_fall_back_to_old_price(assistant_factory):
    assistant = assistant_factory(product_error="DatabaseUnavailable")
    result = respond(assistant, "¿Cuánto cuesta 265/65R17?")
    assert result["respuesta"] == MISSING
    assert not result["matches"]


def test_unavailable_size_does_not_return_nearby_size(assistant):
    result = respond(assistant, "¿Tienen 315/80R22.5?")
    assert not result["matches"]
    assert "295/80R22.5" not in result["respuesta"]


@pytest.mark.parametrize("size,other", [("295/80R22.5", "215/75R17.5"), ("215/75R17.5", "295/80R22.5")])
def test_decimal_rim_inventory_is_not_rounded(assistant, size, other):
    result = respond(assistant, f"¿Cuánto cuesta {size}?")
    assert result["matches"]
    assert size in result["respuesta"]
    assert other not in result["respuesta"]


def test_synthetic_stock_retains_visible_qualification(assistant_factory):
    product = deepcopy(PRODUCTS[0])
    product["inventory_provenance"] = {
        "stock_source": "synthetic_seed", "synthetic_inventory_mode": True,
        "source_note": "generated_by_cleanup_import", "import_batch_id": "fixture-batch",
    }
    assistant = assistant_factory(products=[product])
    result = respond(assistant, "¿Cuánto cuesta 265/65R17?")
    text = result["respuesta"].casefold()
    assert "sintétic" in text or "referencial" in text
    assert "físico garantizado" not in text


def test_private_business_record_fields_never_leak(assistant_factory):
    assistant = assistant_factory(business_records={
        "payment_methods": [{"name": "Zelle", "password": "CANARY_PRIVATE", "account": "SECRET_ACCOUNT"}],
    })
    result = respond(assistant, "¿Qué métodos de pago aceptan?")
    serialized = json.dumps(result)
    assert "CANARY_PRIVATE" not in serialized
    assert "SECRET_ACCOUNT" not in serialized


def test_basic_comparison_uses_only_retrieved_options(assistant):
    respond(assistant, "¿Tienen 265/65R17?")
    result = respond(assistant, "Compara esas opciones")
    assert "RoadMax" in result["respuesta"] or "Budget" in result["respuesta"]
    assert "295/80R22.5" not in result["respuesta"]
    assert "mejor agarre" not in result["respuesta"].casefold()
