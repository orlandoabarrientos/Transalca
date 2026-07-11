"""Evaluación reproducible del dataset, modelo y guardrails del asistente."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from componente_ia.catalog_retriever import CatalogSnapshot
from componente_ia.conversation_memory import ConversationMemory
from componente_ia.entity_extractor import extract
from componente_ia.guardrails import Guardrails
from componente_ia.intent_router import IntentRouter
from componente_ia.inventory_retriever import InventoryRetriever
from componente_ia.knowledge_types import RetrievalResult
from componente_ia.response_composer import ResponseComposer
from componente_ia.service_retriever import ServiceRetriever
from componente_ia.training_pipeline import DEFAULT_DATASET, DEFAULT_MODEL, IntentModel, evaluate_model_rows, load_jsonl


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ARTIFACTS = BASE_DIR / "artifacts"


ENTITY_BENCHMARK = [
    ("Toyota Hilux 2020 A/T rin 17", {"make": "toyota", "model": "hilux", "year": 2020, "requested_rim": 17, "tire_type": "A/T"}),
    ("Ford Explorer 2018 rin 20", {"make": "ford", "model": "explorer", "year": 2018, "requested_rim": 20}),
    ("Jeep Grand Cherokee 2019", {"make": "jeep", "model": "grand cherokee", "year": 2019}),
    ("Hino 500 2022 para carga", {"make": "hino", "model": "hino 500", "year": 2022, "vehicle_type": "camion mediano", "usage": ["load"]}),
    ("Necesito cauchos para un NPR", {"make": "isuzu", "model": "npr", "vehicle_type": "camion liviano"}),
    ("una forruner 2017", {"make": "toyota", "model": "4runner", "year": 2017}),
    ("mi corola 2016", {"make": "toyota", "model": "corolla", "year": 2016}),
    ("Toyota autanna", {"make": "toyota", "model": "autana"}),
    ("jeep cheroky", {"make": "jeep", "model": "cherokee"}),
    ("ford explore", {"make": "ford", "model": "explorer"}),
    ("chevrolet silveradoo", {"make": "chevrolet", "model": "silverado"}),
    ("l200 triton", {"make": "mitsubishi", "model": "l200"}),
    ("nissan fronetier", {"make": "nissan", "model": "frontier"}),
    ("265/65R17", {"requested_tire_size": "265/65R17", "requested_rim": 17}),
    ("265 65 17", {"requested_tire_size": "265/65R17", "requested_rim": 17}),
    ("265-65-17", {"requested_tire_size": "265/65R17", "requested_rim": 17}),
    ("265.65.17", {"requested_tire_size": "265/65R17", "requested_rim": 17}),
    ("LT265/70R17", {"requested_tire_size": "LT265/70R17", "requested_rim": 17}),
    ("P265/70R17", {"requested_tire_size": "P265/70R17", "requested_rim": 17}),
    ("31x10.50R15", {"requested_tire_size": "31X10.5R15", "requested_rim": 15}),
    ("295/80R22.5", {"requested_tire_size": "295/80R22.5", "requested_rim": 22.5}),
    ("11R22.5", {"requested_tire_size": "11R22.5", "requested_rim": 22.5}),
    ("7.50R16", {"requested_tire_size": "7.50R16", "requested_rim": 16}),
    ("900R20", {"requested_tire_size": "9.00R20", "requested_rim": 20}),
    ("1200R24", {"requested_tire_size": "12.00R24", "requested_rim": 24}),
    ("paso de 265/65R17 a 285/70R17", {"current_tire_size": "265/65R17", "requested_tire_size": "285/70R17", "asks_comparison": True}),
    ("qué significa 121/118S", {"load_index": "121/118", "speed_rating": "S"}),
    ("load range E", {"load_range": "E"}),
    ("la uso en lluvia y autopista", {"usage": ["rain", "highway"]}),
    ("la uso para carga y remolque", {"usage": ["load", "trailer"]}),
    ("quiero algo barato", {"budget": "economy", "asks_price": True}),
    ("quiero algo premium", {"budget": "premium"}),
    ("¿tienen baterías?", {"product_category": "batteries", "asks_stock": True}),
    ("precio de un filtro", {"product_category": "filters", "asks_price": True}),
    ("servicio de alineación", {"service": "alignment"}),
    ("el volante vibra", {"service": "balancing"}),
    ("el carro jala hacia un lado", {"service": "alignment"}),
    ("cambio de aceite", {"service": "oil_change", "product_category": "oil"}),
    ("sucursal Valencia", {"branch": "valencia"}),
    ("pedido PED-12345", {"order_reference": "PED-12345"}),
    ("Hilux rin 17 y dime", {"year": None, "load_index": None, "speed_rating": None, "requested_rim": 17}),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: Any) -> Any:
    if isinstance(value, (list, tuple, set)):
        return tuple(sorted(_norm(item) for item in value))
    if isinstance(value, str):
        folded = unicodedata.normalize("NFKD", value.casefold())
        return " ".join("".join(char for char in folded if not unicodedata.combining(char)).split())
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def entity_metrics() -> dict[str, Any]:
    tp = fp = fn = 0
    failures = []
    for message, expected in ENTITY_BENCHMARK:
        predicted = extract(message)
        for field, expected_value in expected.items():
            actual_value = predicted.get(field)
            expected_norm, actual_norm = _norm(expected_value), _norm(actual_value)
            if isinstance(expected_norm, tuple):
                expected_set = set(expected_norm)
                actual_set = set(actual_norm or ())
                tp += len(expected_set & actual_set)
                fp += len(actual_set - expected_set)
                fn += len(expected_set - actual_set)
                if expected_set != actual_set:
                    failures.append({"message": message, "field": field, "expected": expected_value, "actual": actual_value})
            elif expected_value is None:
                if actual_value not in (None, "", [], {}):
                    fp += 1
                    failures.append({"message": message, "field": field, "expected": None, "actual": actual_value})
            elif expected_norm == actual_norm:
                tp += 1
            else:
                fn += 1
                if actual_value not in (None, "", [], {}):
                    fp += 1
                failures.append({"message": message, "field": field, "expected": expected_value, "actual": actual_value})
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "cases": len(ENTITY_BENCHMARK), "facts_correct": tp, "false_positive_facts": fp,
        "false_negative_facts": fn, "precision": round(precision, 6),
        "recall": round(recall, 6), "f1": round(f1, 6), "failures": failures[:30],
        "method": "curated explicit fact benchmark; null expectations count false positives",
    }


def dataset_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    signatures = [" ".join(str(row.get("message") or "").casefold().split()) for row in rows]
    categories = Counter(str(row.get("category")) for row in rows)
    splits = Counter(str(row.get("split")) for row in rows)
    required = {
        "id", "category", "message", "history", "intent", "entities", "expected_behavior",
        "must_include", "must_not_include", "source", "critical", "split",
    }
    invalid = sum(not required <= row.keys() for row in rows)
    return {
        "total": len(rows), "unique_ids": len({row.get("id") for row in rows}),
        "unique_messages": len(set(signatures)), "invalid_schema_rows": invalid,
        "categories": dict(sorted(categories.items())), "splits": dict(sorted(splits.items())),
        "valid": len(rows) == 5000 and len(set(signatures)) == 5000 and invalid == 0
        and splits == {"train": 3500, "validation": 750, "holdout": 750},
    }


def security_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dedicated = [row for row in rows if row.get("category") == "I_security_scope"]
    for filename in ("negative_cases.jsonl", "red_team_cases.jsonl"):
        dedicated.extend(load_jsonl(BASE_DIR / "data" / filename))
    guardrails, router = Guardrails(), IntentRouter()
    failures = []
    for row in dedicated:
        decision = guardrails.check(row["message"])
        predicted = decision.intent if not decision.allowed and decision.intent else router.classify(
            row["message"], extract(row["message"]), context={},
        ).primary
        if predicted != row["intent"]:
            failures.append({"id": row.get("id"), "expected": row["intent"], "predicted": predicted})
    total = len(dedicated)
    return {
        "total": total, "correct": total - len(failures),
        "accuracy": round((total - len(failures)) / total, 6) if total else 1.0,
        "failures": failures[:30],
    }


def grounding_metrics() -> dict[str, Any]:
    composer = ResponseComposer()
    unavailable = RetrievalResult(query="", status="unavailable", available=False, reason="source_unavailable")
    inventory_answer = composer.compose("tire_inventory", extract("265/65R17"), {}, {"inventory": unavailable})
    price_violation = bool(re.search(r"\$\s*\d|\b(?:bs|usd)\.?\s*\d", inventory_answer, re.I))
    inventory_violation = bool(re.search(r"\b(?:tenemos|disponible)\b.{0,30}\bstock\s+\d", inventory_answer, re.I))

    service_result = ServiceRetriever(snapshot=CatalogSnapshot(products=[], services=[], service_error="down")).explain("alignment")
    service_answer = composer.compose("service_price", extract("precio alineación"), {}, {"services": service_result})
    service_violation = "aparece activo" in service_answer.lower() or bool(re.search(r"\$\s*\d", service_answer))

    stock_result = InventoryRetriever(snapshot=CatalogSnapshot(products=[{
        "codigo": "ZERO", "nombre": "Caucho 265/65R17", "precio": None, "stock": 0,
        "categoria": "Cauchos", "marca": "Test",
    }], services=[])).search("265/65R17", entities=extract("¿Tienen 265/65R17?"))
    zero_stock_correct = bool(stock_result.evidence) and all(
        item.data.get("stock_status") != "available" for item in stock_result.evidence
    )
    return {
        "inventory_hallucination_rate": 1.0 if inventory_violation else 0.0,
        "price_hallucination_rate": 1.0 if price_violation else 0.0,
        "service_hallucination_rate": 1.0 if service_violation else 0.0,
        "zero_stock_never_available": zero_stock_correct,
        "checks": 4,
        "passed": not any((inventory_violation, price_violation, service_violation)) and zero_stock_correct,
    }


def multiturn_metrics() -> dict[str, Any]:
    checks = []
    memory = ConversationMemory()
    memory.update("a", extract("Jeep Grand Cherokee"), intent="tire_size_lookup")
    resolved = memory.resolve("a", entities=extract("Es 2018"))
    checks.append(resolved.entities.get("model") == "grand cherokee" and resolved.entities.get("year") == 2018)
    memory.update("a", extract("rin 17 A/T"), evidence={"inventory": [{"name": "old"}]})
    memory.update("a", extract("En realidad es una Hilux"))
    state = memory.get("a") or {}
    checks.append((state.get("vehicle") or {}).get("model") == "hilux" and state.get("tire") == {})
    memory.update("b", extract("Ford Explorer 2020"))
    a = memory.resolve("a", entities=extract("rin 17"))
    b = memory.resolve("b", entities=extract("rin 20"))
    checks.append(a.entities.get("model") == "hilux" and b.entities.get("model") == "explorer")
    return {
        "checks": len(checks), "correct": sum(checks),
        "accuracy": round(sum(checks) / len(checks), 6),
    }


def evaluate(
    dataset_path: Path = DEFAULT_DATASET,
    model_path: Path = DEFAULT_MODEL,
    output_dir: Path = DEFAULT_ARTIFACTS,
) -> dict[str, Any]:
    rows = load_jsonl(Path(dataset_path))
    model = IntentModel.load(Path(model_path))
    validation = evaluate_model_rows(model, [row for row in rows if row.get("split") == "validation"])
    holdout = evaluate_model_rows(model, [row for row in rows if row.get("split") == "holdout"])
    dataset = dataset_metrics(rows)
    entities = entity_metrics()
    security = security_metrics(rows)
    grounding = grounding_metrics()
    multiturn = multiturn_metrics()
    system_critical_checks = security["total"] + grounding["checks"] + multiturn["checks"]
    system_critical_correct = security["correct"] + (grounding["checks"] if grounding["passed"] else 0) + multiturn["correct"]
    critical_accuracy = system_critical_correct / system_critical_checks if system_critical_checks else 1.0
    thresholds = {
        "dataset_5000_valid": dataset["valid"],
        "intent_accuracy_gte_0_97": validation["accuracy"] >= 0.97,
        "entity_f1_gte_0_95": entities["f1"] >= 0.95,
        "holdout_gte_0_94": holdout["accuracy"] >= 0.94,
        "system_critical_behavior_1_0": critical_accuracy == 1.0,
        "security_1_0": security["accuracy"] == 1.0,
        "out_of_scope_1_0": holdout["out_of_scope_accuracy"] == 1.0,
        "multiturn_gte_0_95": multiturn["accuracy"] >= 0.95,
        "inventory_hallucination_0": grounding["inventory_hallucination_rate"] == 0.0,
        "price_hallucination_0": grounding["price_hallucination_rate"] == 0.0,
        "service_hallucination_0": grounding["service_hallucination_rate"] == 0.0,
    }
    result = {
        "generated_at": _now(), "dataset": dataset, "intent_validation": validation,
        "entity_extraction": entities, "security_and_scope": security,
        "grounding": grounding, "multiturn": multiturn,
        "system_critical_behavior_accuracy": round(critical_accuracy, 6),
        "thresholds": thresholds, "passed": all(thresholds.values()),
        "classification": "APTO_PENDIENTE_RENDIMIENTO" if all(thresholds.values()) else "NO_APTO",
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ia_5000_cases_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8",
    )
    holdout_result = {
        "generated_at": _now(), "model_version": model.artifact.get("version"),
        "dataset_sha256": model.artifact.get("dataset", {}).get("sha256"),
        "holdout_policy": "reserved; not used for epoch or parameter selection",
        "metrics": holdout, "passed": holdout["accuracy"] >= 0.94,
    }
    (output_dir / "ia_holdout_results.json").write_text(
        json.dumps(holdout_result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8",
    )
    performance_path = output_dir / "ia_performance_results.json"
    performance = json.loads(performance_path.read_text(encoding="utf-8")) if performance_path.exists() else {}
    result["thresholds"]["performance_passed"] = performance.get("passed") is True
    result["passed"] = all(result["thresholds"].values())
    if not result["passed"]:
        result["classification"] = "NO_APTO" if performance else "APTO_PENDIENTE_RENDIMIENTO"
    elif (performance.get("web_live") or {}).get("executed") and not (performance.get("web_live") or {}).get("results"):
        result["classification"] = "APTO_CON_MONITOREO"
    else:
        result["classification"] = "APTO_PARA_PRODUCCION"
    release_evidence = {
        "inventory_hallucination_rate": grounding["inventory_hallucination_rate"],
        "price_hallucination_rate": grounding["price_hallucination_rate"],
        "service_hallucination_rate": grounding["service_hallucination_rate"],
        "security_accuracy": security["accuracy"],
        "critical_behavior_accuracy": round(critical_accuracy, 6),
        "performance_p95_ms": (performance.get("local") or {}).get("p95_ms"),
        "performance_budget_ms": 150.0,
        "catalog_p95_ms": (performance.get("catalog_10000") or {}).get("p95_ms"),
        "web_p95_ms": max(
            float((performance.get("web_simulated") or {}).get("p95_ms") or 0.0),
            float((performance.get("web_live") or {}).get("latency_ms") or 0.0),
        ) if performance else None,
        "performance_passed": performance.get("passed") is True,
        "evaluation_passed": result["passed"],
    }
    (output_dir / "ia_release_evidence.json").write_text(
        json.dumps({"generated_at": _now(), "release_evidence": release_evidence}, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    (output_dir / "ia_5000_cases_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8",
    )
    return result


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("command", nargs="?", choices=["evaluate"], default="evaluate")
    command.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    command.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    command.add_argument("--output-dir", type=Path, default=DEFAULT_ARTIFACTS)
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = evaluate(args.dataset, args.model, args.output_dir)
    print(json.dumps({
        "passed": result["passed"], "classification": result["classification"],
        "intent_accuracy": result["intent_validation"]["accuracy"],
        "entity_f1": result["entity_extraction"]["f1"],
        "security_accuracy": result["security_and_scope"]["accuracy"],
        "critical_behavior_accuracy": result["system_critical_behavior_accuracy"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["ENTITY_BENCHMARK", "entity_metrics", "evaluate", "grounding_metrics", "security_metrics"]
