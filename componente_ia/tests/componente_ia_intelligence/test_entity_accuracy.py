import pytest

from componente_ia.entity_extractor import extract, extract_tire_sizes


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("265/65R17", "265/65R17"),
        ("265 65 17", "265/65R17"),
        ("265-65-17", "265/65R17"),
        ("265.65.17", "265/65R17"),
        ("LT265/70R17", "LT265/70R17"),
        ("P265/70R17", "P265/70R17"),
        ("31x10.50R15", "31X10.5R15"),
        ("295/80R22.5", "295/80R22.5"),
        ("315/80R22.5", "315/80R22.5"),
        ("11R22.5", "11R22.5"),
        ("12R22.5", "12R22.5"),
        ("7.50R16", "7.50R16"),
        ("8.25R16", "8.25R16"),
        ("10.00R20", "10.00R20"),
        ("900R20", "9.00R20"),
        ("1200R24", "12.00R24"),
    ],
)
def test_all_required_tire_size_formats(raw, expected):
    values = extract_tire_sizes(raw)
    assert values and values[0].normalized == expected


@pytest.mark.parametrize(
    ("message", "make", "model"),
    [
        ("tengo una forruner", "toyota", "4runner"),
        ("mi corola 2017", "toyota", "corolla"),
        ("una autanna", "toyota", "autana"),
        ("jeep cheroky", "jeep", "cherokee"),
        ("ford explore 2018", "ford", "explorer"),
        ("chevrolet silveradoo", "chevrolet", "silverado"),
        ("l200 triton", "mitsubishi", "l200"),
        ("nissan fronetier", "nissan", "frontier"),
        ("la Merú", "toyota", "meru"),
        ("Hino 500", "hino", "hino 500"),
        ("un NPR", "isuzu", "npr"),
    ],
)
def test_vehicle_aliases_and_real_world_typos(message, make, model):
    entities = extract(message)
    assert entities["make"] == make
    assert entities["model"] == model


def test_entity_schema_is_stable():
    entities = extract("Hilux 2020 A/T rin 17 para carga, barata y con stock")
    required = {
        "vehicle_type", "make", "model", "submodel", "year", "trim", "engine",
        "drivetrain", "current_rim", "current_tire_size", "requested_rim",
        "requested_tire_size", "tire_type", "load_index", "speed_rating",
        "load_range", "usage", "budget", "branch", "product_category", "service",
        "order_reference", "asks_price", "asks_stock", "asks_comparison",
    }
    assert required <= entities.keys()
    assert entities["year"] == 2020
    assert entities["requested_rim"] == 17
    assert entities["tire_type"] == "A/T"
    assert "load" in entities["usage"]
    assert entities["budget"] == "economy"


def test_rim_followed_by_conjunction_is_not_a_load_speed_code():
    entities = extract("Hilux rin 17 y dime cuál tienen barato")
    assert entities["load_index"] is None
    assert entities["speed_rating"] is None
    assert entities["asks_price"] is True


def test_dual_load_index_and_speed_rating_are_extracted():
    entities = extract("¿Qué significa 121/118S en un caucho de carga?")
    assert entities["load_index"] == "121/118"
    assert entities["speed_rating"] == "S"


def test_change_of_size_preserves_current_and_requested_order():
    entities = extract("¿Cuánto cambia si paso de 265/65R17 a 285/70R17?")
    assert entities["current_tire_size"] == "265/65R17"
    assert entities["requested_tire_size"] == "285/70R17"
    assert entities["asks_comparison"] is True


def test_unknown_vehicle_is_preserved_as_uncertain_not_fabricated():
    entities = extract("Tengo una Zorak X9 2024, ¿qué cauchos usa?")
    resolution = entities["vehicle_resolution"]
    assert resolution["known_model"] is False
    assert resolution["needs_web"] is True
    assert entities["model"]


def test_curated_entity_fact_f1_is_at_least_95_percent():
    from componente_ia.evaluation import entity_metrics

    metrics = entity_metrics()
    assert metrics["f1"] >= 0.95, metrics["failures"]
