import json
from pathlib import Path

import pytest

from componente_ia.assistant_orchestrator import AssistantOrchestrator
from componente_ia.business_knowledge import BusinessKnowledge
from componente_ia.catalog_retriever import CatalogSnapshot
from componente_ia.web_search import FakeSearchProvider, SearchSource, WebSearchService


COMPONENT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = COMPONENT_DIR / "data"
ARTIFACT_DIR = COMPONENT_DIR / "artifacts"


@pytest.fixture(scope="session")
def training_cases():
    path = DATA_DIR / "generated_training_cases.jsonl"
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                pytest.fail(f"JSON inválido en línea {number}: {exc}")
            rows.append(value)
    return rows


class StaticCatalogProvider:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def load(self, force=False):
        return self.snapshot


@pytest.fixture
def assistant(monkeypatch):
    monkeypatch.setenv("ASSISTANT_WEB_ENABLED", "1")
    products = [
        {
            "codigo": "T-001", "nombre": "RoadMax 265/65R17 A/T",
            "descripcion": "Caucho A/T", "precio": 120.0, "stock": 4,
            "categoria": "Cauchos", "marca": "RoadMax", "sucursal_nombre": "Centro",
        },
        {
            "codigo": "T-002", "nombre": "Budget 265/65R17 A/T",
            "descripcion": "Caucho A/T", "precio": 95.0, "stock": 0,
            "categoria": "Cauchos", "marca": "Budget", "sucursal_nombre": "Norte",
        },
        {
            "codigo": "B-001", "nombre": "Batería 12V",
            "descripcion": "Batería automotriz", "precio": 80.0, "stock": 2,
            "categoria": "Baterías", "marca": "Power", "sucursal_nombre": "Centro",
        },
    ]
    services = [
        {
            "id": 1, "nombre": "Alineación", "descripcion": "Alineación",
            "precio": 25.0, "duracion_estimada": 45, "tipo": "alineacion",
            "sucursal_nombre": "Centro",
        },
        {
            "id": 2, "nombre": "Balanceo", "descripcion": "Balanceo",
            "precio": 15.0, "duracion_estimada": 30, "tipo": "balanceo",
            "sucursal_nombre": "Centro",
        },
    ]
    snapshot = CatalogSnapshot(products=products, services=services, catalog_available=True)
    web_source = SearchSource(
        title="2024 Zorak X9 owner manual tire information",
        url="https://www.toyota.com/owners/manuals/",
        domain="toyota.com",
        snippet="Zorak X9 2024 tire information owner manual reference.",
        provider="fake",
        fetched_at=1.0,
    )
    return AssistantOrchestrator(
        catalog_provider=StaticCatalogProvider(snapshot),
        search_service=WebSearchService(provider=FakeSearchProvider([web_source])),
        business=BusinessKnowledge(use_model_provider=False),
    )
