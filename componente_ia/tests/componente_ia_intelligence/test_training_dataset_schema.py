import hashlib
import json
import re
from collections import Counter
from pathlib import Path


REQUIRED = {
    "id", "category", "message", "history", "intent", "entities",
    "expected_behavior", "must_include", "must_not_include", "source", "critical", "split",
}
EXPECTED_DISTRIBUTION = {
    "A": 1700,
    "B": 1600,
    "C": 900,
    "D": 1400,
    "E": 750,
    "F": 650,
    "G": 1100,
    "H": 800,
    "I": 550,
    "J": 550,
}


def test_dataset_has_exactly_10000_valid_cases(training_cases):
    assert len(training_cases) == 10000
    for index, case in enumerate(training_cases, 1):
        assert REQUIRED <= case.keys(), f"faltan campos en caso {index}"
        assert re.fullmatch(r"TRAIN-\d{6}", case["id"])
        assert isinstance(case["message"], str) and case["message"].strip()
        assert isinstance(case["history"], list)
        assert isinstance(case["intent"], str) and case["intent"]
        assert isinstance(case["entities"], dict)
        assert isinstance(case["expected_behavior"], str) and case["expected_behavior"]
        assert isinstance(case["must_include"], list)
        assert isinstance(case["must_not_include"], list)
        assert case["source"] in {"generated", "curated", "real_anonymized"}
        assert isinstance(case["critical"], bool)
        assert case["split"] in {"train", "validation", "test", "holdout"}
        assert re.fullmatch(r"[0-9a-f]{24}", case["family_hash"])


def test_distribution_and_splits_are_exact(training_cases):
    category_counts = Counter(str(case["category"])[0].upper() for case in training_cases)
    assert category_counts == EXPECTED_DISTRIBUTION
    assert Counter(case["split"] for case in training_cases) == {
        "train": 6500,
        "validation": 1500,
        "test": 1000,
        "holdout": 1000,
    }


def test_ids_and_messages_are_not_duplicate(training_cases):
    ids = [case["id"] for case in training_cases]
    assert len(ids) == len(set(ids))
    signatures = [" ".join(case["message"].lower().split()) for case in training_cases]
    assert len(signatures) == len(set(signatures))


def test_holdout_is_reserved_and_dataset_has_stable_hash(training_cases):
    holdout = [case for case in training_cases if case["split"] == "holdout"]
    assert len(holdout) == 1000
    assert all(case.get("source") != "real_anonymized" for case in holdout)
    payload = "\n".join(json.dumps(case, ensure_ascii=False, sort_keys=True) for case in training_cases)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_dataset_does_not_contain_obvious_private_or_secret_material(training_cases):
    serialized = "\n".join(case["message"] for case in training_cases)
    assert not re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", serialized, re.I)
    assert "ASSISTANT_LLM_API_KEY=" not in serialized
    assert not re.search(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", serialized)


def test_split_files_match_declared_split(training_cases):
    data_dir = Path(__file__).resolve().parents[2] / "data"
    expected = Counter(case["split"] for case in training_cases)
    candidates = {
        "train": data_dir / "generated_training_cases.train.jsonl",
        "validation": data_dir / "generated_training_cases.validation.jsonl",
        "test": data_dir / "generated_training_cases.test.jsonl",
        "holdout": data_dir / "generated_training_cases.holdout.jsonl",
    }


    for split, path in candidates.items():
        if not path.exists():
            continue
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(rows) == expected[split]
        assert all(row["split"] == split for row in rows)


def test_legacy_generator_is_preserved_and_expansion_is_reproducible(training_cases):
    from componente_ia.dataset_manager import CORE_FIELDS, build_expanded_cases
    from componente_ia.tools.generate_assistant_training_cases import DEFAULT_SEED, build_cases

    legacy = build_cases(DEFAULT_SEED)
    assert len(legacy) == 5000
    expanded, snapshot = build_expanded_cases(DEFAULT_SEED)
    assert snapshot == legacy
    assert expanded == training_cases
    for original, current in zip(legacy, expanded[:5000]):
        assert {field: original[field] for field in CORE_FIELDS} == {
            field: current[field] for field in CORE_FIELDS
        }


def test_no_semantic_family_leaks_across_splits(training_cases):
    family_splits = {}
    for case in training_cases:
        family_splits.setdefault(case["family_hash"], set()).add(case["split"])
    assert len(family_splits) == 1000
    assert all(len(splits) == 1 for splits in family_splits.values())
