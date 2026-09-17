"""Deterministic coverage for business intents and exact tire notation."""

import pytest

from componente_ia.lite.lite_entities import extract_entities, parse_tire_size
from componente_ia.lite.lite_router import route_intent


INTENTS = [
    ("Hola", "greeting"),
    ("Buenas", "greeting"),
    ("Buenos días", "greeting"),
    ("Buenas tardes", "greeting"),
    ("Buenas noches", "greeting"),
    ("¿Qué métodos de pago aceptan?", "payment_methods"),
    ("¿Aceptan Zelle?", "payment_methods"),
    ("¿Aceptan Binance?", "payment_methods"),
    ("¿Aceptan pago móvil?", "payment_methods"),
    ("¿Cómo puedo pagar?", "payment_methods"),
    ("Formas de pago", "payment_methods"),
    ("¿Reciben Zelle?", "payment_methods"),
    ("¿Tienen pago movil?", "payment_methods"),
    ("¿Dónde están ubicados?", "branches"),
    ("¿Cuáles son las sucursales?", "branches"),
    ("¿Qué sedes tienen?", "branches"),
    ("Dirección de Transalca", "branches"),
    ("Ubicación de la sucursal", "branches"),
    ("¿Qué servicios tienen?", "services"),
    ("¿Hacen alineación?", "services"),
    ("¿Hacen balanceo?", "services"),
    ("Servicios disponibles", "services"),
    ("¿Tienen servicio de alineacion?", "services"),
    ("Necesito balanceo", "services"),
    ("¿Qué categorías tienen?", "categories"),
    ("¿Qué productos venden?", "categories"),
    ("Categorías de productos", "categories"),
    ("¿Cuáles categorías manejan?", "categories"),
    ("¿Tienen 265/65R17?", "inventory_by_size"),
    ("Busco cauchos 295/80R22.5", "inventory_by_size"),
    ("Necesito neumáticos 315/80R22.5", "inventory_by_size"),
    ("Gomas 12R22.5", "inventory_by_size"),
    ("¿Hay caucho 7.00R15?", "inventory_by_size"),
    ("¿Tienen Michelin?", "inventory_by_brand"),
    ("Busco cauchos Goodyear", "inventory_by_brand"),
    ("Necesito gomas RoadMax", "inventory_by_brand"),
    ("Cauchos Budget", "inventory_by_brand"),
    ("¿Tienen A/T?", "inventory_by_type"),
    ("Busco cauchos H/T", "inventory_by_type"),
    ("Necesito gomas M/T", "inventory_by_type"),
    ("Neumáticos todo terreno", "inventory_by_type"),
    ("¿Cuánto cuesta?", "price"),
    ("¿Cuanto cuesta 265/65R17?", "price"),
    ("Precio del caucho", "price"),
    ("¿Qué stock hay?", "stock"),
    ("¿Tienen existencia?", "stock"),
    ("¿Cuál es el más barato?", "cheapest"),
    ("Busco el caucho más económico", "cheapest"),
    ("¿Cuál tiene más stock?", "most_stock"),
    ("El que tenga mayor existencia", "most_stock"),
]


@pytest.mark.parametrize("message,expected", INTENTS)
def test_business_and_inventory_intents(message, expected):
    entities = extract_entities(message, brands=("Michelin", "Goodyear", "RoadMax", "Budget"))
    assert route_intent(message, entities=entities) == expected


VALID_SIZES = [
    ("265/65R17", "265/65R17", 17),
    ("295/80R22.5", "295/80R22.5", 22.5),
    ("315/80R22.5", "315/80R22.5", 22.5),
    ("12R22.5", "12R22.5", 22.5),
    ("11R22.5", "11R22.5", 22.5),
    ("35X12.50R17", "35X12.50R17", 17),
    ("33X12.50R15", "33X12.50R15", 15),
    ("31X10.50R15", "31X10.50R15", 15),
    ("LT285/75R16", "LT285/75R16", 16),
    ("P235/75R15", "P235/75R15", 15),
    ("195R14C", "195R14C", 14),
    ("215/75R17.5", "215/75R17.5", 17.5),
    ("7.00R15", "7.00R15", 15),
    ("225/45R18", "225/45R18", 18),
    ("205/55R16", "205/55R16", 16),
    ("185/65R14", "185/65R14", 14),
    ("175/70R13", "175/70R13", 13),
    ("275/70R22.5", "275/70R22.5", 22.5),
    ("235/75R17.5", "235/75R17.5", 17.5),
    ("8.25R16", "8.25R16", 16),
    ("9.5R17.5", "9.5R17.5", 17.5),
    ("10R22.5", "10R22.5", 22.5),
    ("225/75R16C", "225/75R16C", 16),
    ("LT245/75R16", "LT245/75R16", 16),
    ("P215/65R16", "P215/65R16", 16),
    ("265/65r17", "265/65R17", 17),
    ("lt285/75r16", "LT285/75R16", 16),
    ("p235/75r15", "P235/75R15", 15),
    ("35x12.50r17", "35X12.50R17", 17),
    ("195r14c", "195R14C", 14),
]


@pytest.mark.parametrize("value,expected,rim", VALID_SIZES)
def test_valid_sizes_preserve_units_prefix_suffix_and_decimal_rim(value, expected, rim):
    assert parse_tire_size(value) == expected
    entities = extract_entities(f"¿Tienen cauchos {value}?")
    assert entities["tire_size"] == expected
    assert entities["rim"] == rim


INVALID_SIZES = [
    "", "hola", "265/65", "R17", "265/65R", "265//65R17",
    "265/65RR17", "265/65R17.5.1", "265/65R170", "265/0R17",
    "265/105R17", "0/65R17", "265/65R0", "35X0R17", "35X12.50R0",
    "12R0", "999/99R99", "abc265/65R17xyz", "-265/65R17", "265/65R-17",
]


@pytest.mark.parametrize("value", INVALID_SIZES)
def test_invalid_sizes_are_not_truncated_or_repaired(value):
    assert parse_tire_size(value) is None
    assert not extract_entities(value).get("tire_size")


@pytest.mark.parametrize("text,rim", [("rin 22.5", 22.5), ("rines 17.5", 17.5), ("rin 17", 17)])
def test_standalone_rims_keep_decimal(text, rim):
    assert extract_entities(text)["rim"] == rim


def test_dynamic_entities_only_recognize_configured_labels():
    entities = extract_entities(
        "RoadMax Trail 265/65R17 A/T en Centro",
        brands=("RoadMax",), models=("Trail",), branches=("Centro",),
    )
    assert entities["brand"] == "RoadMax"
    assert entities["model"] == "Trail"
    assert entities["branch"] == "Centro"
    assert entities["tire_type"] == "A/T"


def test_unknown_brand_is_not_reported_as_existing():
    entities = extract_entities("Busco marca NoExiste", brands=("RoadMax",))
    assert not entities.get("brand")
