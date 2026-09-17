"""Exact local VERIFIED fitment only. No web or inferred sizes."""

import json
from pathlib import Path
from .lite_entities import normalize, parse_tire_size
from .lite_response_templates import UNVERIFIED_VEHICLE, public_text


class LiteVehicleHandler:
    def __init__(self, catalog_path=None):
        self.catalog_path = Path(catalog_path) if catalog_path else Path(__file__).with_name("vehicle_catalog_lite.json")
        try:
            payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            self.vehicles = [row for row in payload.get("vehicles", []) if isinstance(row, dict)]
        except (OSError, ValueError, AttributeError, TypeError):
            self.vehicles = []

    def enrich(self, message, entities):
        value = normalize(message)
        import re
        for row in self.vehicles:
            model = public_text(row.get("model"))
            if model and re.search(r"(?<!\w)" + re.escape(normalize(model)) + r"(?!\w)", value):
                entities["vehicle_model"] = model
                entities["vehicle_brand"] = public_text(row.get("brand")) or entities.get("vehicle_brand")
                break
        return entities

    def handle(self, entities, state):
        brand = entities.get("vehicle_brand") or state.get("vehicle_brand")
        model = entities.get("vehicle_model") or state.get("vehicle_model")
        year = entities.get("vehicle_year") or state.get("vehicle_year")
        verified = []
        for row in self.vehicles:
            if row.get("status") != "VERIFIED" or not row.get("evidence"):
                continue
            size = parse_tire_size(row.get("tire_size"))
            if not size or not row.get("brand") or not row.get("model") or not isinstance(row.get("year"), int):
                continue
            if normalize(row["model"]) != normalize(model) or (brand and normalize(row["brand"]) != normalize(brand)) or row["year"] != year:
                continue
            verified.append((row, size))
        # Ambiguous versions or different measures fail closed.
        identities = {(normalize(row["brand"]), normalize(row["model"]), row["year"], size) for row, size in verified}
        if len(identities) != 1:
            return UNVERIFIED_VEHICLE, None
        row, size = verified[0]
        vehicle = public_text(f"{row['brand']} {row['model']}")
        if not vehicle:
            return UNVERIFIED_VEHICLE, None
        return f"Para {vehicle} {year} tengo registrada la medida {size}.", size
