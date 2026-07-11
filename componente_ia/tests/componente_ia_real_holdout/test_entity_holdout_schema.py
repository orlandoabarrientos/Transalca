import json
from pathlib import Path


def test_entity_benchmark_meets_size_and_fact_requirements(entity_holdout_cases):
    assert len(entity_holdout_cases) == 1000
    assert sum(row["fact_count"] for row in entity_holdout_cases) == 5750
    assert all(row["fact_count"] >= 4 for row in entity_holdout_cases)


def test_entity_benchmark_is_explicitly_excluded_from_tuning(entity_holdout_cases):
    assert all(row["split"] == "entity_holdout" for row in entity_holdout_cases)
    assert all(row["excluded_from_tuning"] is True for row in entity_holdout_cases)
    assert all(row["source"] == "deterministic_annotated_grammar" for row in entity_holdout_cases)


def test_entity_annotations_are_non_null_explicit_facts(entity_holdout_cases):
    for row in entity_holdout_cases:
        expected = row["expected_entities"]
        counted = sum(
            1 for value in expected.values()
            if value is not None and value != [] and value is not False
        )
        assert counted == row["fact_count"]


def test_entity_evaluation_artifact_meets_declared_threshold():
    path = Path(__file__).resolve().parents[2] / "artifacts" / "ia_entity_holdout_results.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["messages"] == 1000
    assert result["annotated_facts"] == 5750
    assert result["f1"] >= 0.97
    assert result["passed"] is True
    assert result["excluded_from_tuning"] is True
