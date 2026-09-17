"""Isolated Lite fixtures: real read-only retrievers, no production database."""

from copy import deepcopy
import json

import pytest

from componente_ia.business_knowledge import DynamicKnowledgeResult
from componente_ia.business_retriever import BusinessRetriever
from componente_ia.catalog_retriever import CatalogSnapshot
from componente_ia.inventory_retriever import InventoryRetriever
from componente_ia.service_retriever import ServiceRetriever
from componente_ia.lite.lite_assistant import LiteAssistant


PRODUCTS = [
    {"codigo": "L-001", "nombre": "RoadMax Trail 265/65R17 A/T", "modelo": "Trail",
     "descripcion": "Caucho A/T", "precio": 120.0, "stock": 4,
     "categoria": "Cauchos", "marca": "RoadMax", "sucursal_nombre": "Centro"},
    {"codigo": "L-002", "nombre": "Budget Road 265/65R17 A/T", "modelo": "Road",
     "descripcion": "Caucho A/T", "precio": 95.0, "stock": 8,
     "categoria": "Cauchos", "marca": "Budget", "sucursal_nombre": "Norte"},
    {"codigo": "L-003", "nombre": "Michelin Highway 265/65R17 H/T", "modelo": "Highway",
     "descripcion": "Caucho H/T", "precio": 150.0, "stock": 2,
     "categoria": "Cauchos", "marca": "Michelin", "sucursal_nombre": "Centro"},
    {"codigo": "L-004", "nombre": "RoadMax Cargo 295/80R22.5", "modelo": "Cargo",
     "descripcion": "Caucho de carga", "precio": 260.0, "stock": 6,
     "categoria": "Cauchos", "marca": "RoadMax", "sucursal_nombre": "Norte"},
    {"codigo": "L-005", "nombre": "RoadMax Cargo 215/75R17.5", "modelo": "Cargo",
     "descripcion": "Caucho de carga", "precio": 175.0, "stock": 3,
     "categoria": "Cauchos", "marca": "RoadMax", "sucursal_nombre": "Centro"},
    {"codigo": "L-006", "nombre": "Budget Road 235/75R15 H/T", "modelo": "Road",
     "descripcion": "Caucho H/T", "precio": 80.0, "stock": 9,
     "categoria": "Cauchos", "marca": "Budget", "sucursal_nombre": "Norte"},
]

SERVICES = [
    {"id": 1, "nombre": "Alineación", "descripcion": "Alineación",
     "precio": 25.0, "duracion_estimada": 45, "tipo": "alineacion",
     "sucursal_nombre": "Centro"},
    {"id": 2, "nombre": "Balanceo", "descripcion": "Balanceo",
     "precio": 15.0, "duracion_estimada": 30, "tipo": "balanceo",
     "sucursal_nombre": "Centro"},
]


class StaticBusinessProvider:
    def __init__(self, records=None):
        self.calls = []
        self.records = records if records is not None else {
            "payment_methods": [{"name": name} for name in ("Pago Móvil", "Binance", "Zelle", "Tarjeta")],
            "branches": [{"name": "Centro", "address": "Avenida Principal"},
                         {"name": "Norte", "address": "Avenida Norte"}],
            "product_categories": [{"name": "Cauchos"}],
        }

    def resolve(self, source, topic):
        self.calls.append((source, topic))
        records = deepcopy(self.records.get(topic, []))
        return DynamicKnowledgeResult(source=source, records=records, available=bool(records))


@pytest.fixture
def assistant_factory(tmp_path):
    created = []

    def create(*, products=None, services=None, business_records=None, vehicles=None,
               product_error=None, service_error=None):
        snapshot = CatalogSnapshot(
            products=deepcopy(PRODUCTS if products is None else products),
            services=deepcopy(SERVICES if services is None else services),
            product_error=product_error, service_error=service_error,
        )
        provider = StaticBusinessProvider(business_records)
        catalog_path = tmp_path / f"vehicle_catalog_{len(created)}.json"
        catalog_path.write_text(json.dumps({"schema_version": 1, "vehicles": vehicles or []}), encoding="utf-8")
        assistant = LiteAssistant(
            inventory_retriever=InventoryRetriever(snapshot=snapshot),
            service_retriever=ServiceRetriever(snapshot=snapshot),
            business_retriever=BusinessRetriever(data_provider=provider, resilient=False),
            catalog_path=catalog_path,
        )
        created.append(assistant)
        return assistant

    return create


@pytest.fixture
def assistant(assistant_factory):
    return assistant_factory()


def respond(assistant, message, session="lite-test"):
    payload, status = assistant.respond(message, session_id=session)
    assert status == 200
    assert payload["status"] == "success"
    assert payload["diagnostics"]["ai_mode"] == "lite"
    assert isinstance(payload["respuesta"], str) and payload["respuesta"]
    return payload
