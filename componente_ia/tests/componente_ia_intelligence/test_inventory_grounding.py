from componente_ia.catalog_retriever import CatalogSnapshot
from componente_ia.entity_extractor import extract
from componente_ia.inventory_retriever import InventoryRetriever


PRODUCTS = [
    {
        "codigo": "T-001",
        "nombre": "RoadMax 265/65R17 A/T",
        "descripcion": "Caucho todo terreno",
        "precio": 120.0,
        "stock": 4,
        "categoria": "Cauchos",
        "marca": "RoadMax",
        "sucursal_nombre": "Centro",
    },
    {
        "codigo": "T-002",
        "nombre": "Budget 265/65R17 A/T",
        "descripcion": "Caucho A/T",
        "precio": 95.0,
        "stock": 0,
        "categoria": "Cauchos",
        "marca": "Budget",
        "sucursal_nombre": "Norte",
    },
    {
        "codigo": "T-003",
        "nombre": "UnknownPrice 265/65R17 A/T",
        "descripcion": "Caucho A/T",
        "precio": None,
        "stock": 8,
        "categoria": "Cauchos",
        "marca": "NoPrice",
        "sucursal_nombre": "Centro",
    },
    {
        "codigo": "T-004",
        "nombre": "OtherSize 285/70R17 M/T",
        "descripcion": "Caucho de barro",
        "precio": 150.0,
        "stock": 5,
        "categoria": "Cauchos",
        "marca": "MudCo",
        "sucursal_nombre": "Centro",
    },
]


def _retriever(products=PRODUCTS):
    return InventoryRetriever(snapshot=CatalogSnapshot(products=products, services=[], catalog_available=True))


def test_exact_size_never_includes_a_different_size():
    result = _retriever().search_tires("265/65R17", entities=extract("¿Tienen 265/65R17?"))
    assert result.available is True
    assert result.evidence
    assert all("265/65R17" in item.data["sizes"] for item in result.evidence)
    assert all(item.data["match"] in {"medida_exacta", "medida_equivalente_sin_prefijo"} for item in result.evidence)


def test_same_rim_is_explicitly_not_fitment_confirmation():
    result = _retriever().search_tires("rin 17", entities=extract("¿Tienen cauchos rin 17?"))
    assert {item.data["sizes"][0] for item in result.evidence} >= {"265/65R17", "285/70R17"}
    assert all(item.data["match"] == "mismo_rin_no_confirma_fitment" for item in result.evidence)


def test_zero_stock_is_never_marked_available():
    result = _retriever().search_tires("265/65R17", entities=extract("¿Tienen 265/65R17?"))
    budget = next(item for item in result.evidence if item.data["code"] == "T-002")
    assert budget.data["stock"] == 0
    assert budget.data["stock_status"] == "out_of_stock"
    only_available = _retriever().search_tires(
        "265/65R17", entities=extract("¿Tienen 265/65R17?"), include_out_of_stock=False,
    )
    assert all(item.data["stock_status"] == "available" for item in only_available.evidence)


def test_null_price_is_preserved_and_not_rendered_as_zero():
    result = _retriever().search_tires("265/65R17", entities=extract("precio 265/65R17"))
    item = next(value for value in result.evidence if value.data["code"] == "T-003")
    assert item.data["price"] is None
    assert item.data["price_available"] is False


def test_economy_budget_sorts_only_confirmed_prices_first():
    entities = extract("Busco 265/65R17 A/T barato")
    result = _retriever().search_tires("265/65R17 A/T barato", entities=entities)
    priced = [item.data["price"] for item in result.evidence if item.data["price_available"]]
    assert priced == sorted(priced)
    assert result.evidence[-1].data["price_available"] is False


class BrokenProvider:
    def load(self):
        raise RuntimeError("database unavailable: SELECT secret")


def test_database_failure_is_grounded_and_does_not_leak_exception_text():
    result = InventoryRetriever(catalog_provider=BrokenProvider()).search("cauchos")
    assert result.available is False
    assert result.status == "unavailable"
    assert result.reason == "inventory_source_unavailable"
    assert result.evidence == []
    assert "SELECT" not in str(result.to_dict())


def test_canonical_product_categories_match_spanish_database_categories():
    products = [{
        "codigo": "BAT-1", "nombre": "Batería 12V", "descripcion": "Batería automotriz",
        "precio": 80, "stock": 2, "categoria": "Baterías", "marca": "Power",
    }]
    result = _retriever(products).search("baterías", entities=extract("¿Tienen baterías?"))
    assert result.evidence
    assert result.evidence[0].data["code"] == "BAT-1"
