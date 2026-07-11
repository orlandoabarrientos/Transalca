import json
from collections import Counter

from componente_ia.case_generator import normalized_message
from componente_ia.dataset_manager import validate_real_holdout


def test_real_holdout_has_exact_bootstrap_distribution(real_holdout_cases, expanded_training_cases):
    report = validate_real_holdout(real_holdout_cases, expanded_training_cases)
    assert report["total"] == 1000
    assert report["buckets"] == {
        "manual_curated": 300,
        "feedback_manual_proxy": 300,
        "multiturn_curated": 200,
        "truck_curated": 100,
        "security_curated": 100,
    }
    assert report["critical"] == 200
    assert report["training_overlap"] == 0


def test_proxy_feedback_is_never_misrepresented_as_real(real_holdout_cases):
    assert Counter(row["source"] for row in real_holdout_cases)["feedback_manual_proxy"] == 300
    assert all(row["source"] != "real_anonymized" for row in real_holdout_cases)
    assert all(row["real_feedback"] is False for row in real_holdout_cases)


def test_every_holdout_case_is_excluded_from_training(real_holdout_cases):
    assert all(row["excluded_from_training"] is True for row in real_holdout_cases)
    assert all(row["split"] == "real_holdout" for row in real_holdout_cases)
    assert all(row["id"].startswith("HOLDOUT-") for row in real_holdout_cases)


def test_multiturn_cases_are_unique_as_complete_dialogues(real_holdout_cases):
    rows = [row for row in real_holdout_cases if row["provenance_bucket"] == "multiturn_curated"]
    assert len(rows) == 200
    assert all(len(row["history"]) == 2 for row in rows)
    signatures = {
        json.dumps([row["history"], normalized_message(row["message"])], ensure_ascii=False, sort_keys=True)
        for row in rows
    }
    assert len(signatures) == 200


def test_security_and_truck_reservations_are_critical(real_holdout_cases):
    security = [row for row in real_holdout_cases if row["provenance_bucket"] == "security_curated"]
    trucks = [row for row in real_holdout_cases if row["provenance_bucket"] == "truck_curated"]
    assert len(security) == len(trucks) == 100
    assert all(row["critical"] for row in security + trucks)
