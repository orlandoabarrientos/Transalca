import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from componente_ia.dataset_manager import (
    CATEGORY_SPLITS,
    CORE_FIELDS,
    TARGET_DISTRIBUTION,
    validate_expanded_cases,
)
from componente_ia.tools.generate_assistant_training_cases import DEFAULT_SEED, build_cases


def test_exact_distribution_and_family_splits(expanded_training_cases):
    report = validate_expanded_cases(expanded_training_cases)
    assert report["total"] == 10000
    assert report["categories"] == TARGET_DISTRIBUTION
    assert report["splits"] == {
        "train": 6500,
        "validation": 1500,
        "test": 1000,
        "holdout": 1000,
    }
    assert report["per_category_splits"] == CATEGORY_SPLITS
    assert report["family_leakage_count"] == 0


def test_all_5000_foundational_cases_are_semantically_unchanged(expanded_training_cases):
    originals = build_cases(DEFAULT_SEED)
    current = {row["id"]: row for row in expanded_training_cases}
    assert len(originals) == 5000
    for original in originals:
        assert {field: current[original["id"]][field] for field in CORE_FIELDS} == {
            field: original[field] for field in CORE_FIELDS
        }


def test_legacy_snapshot_keeps_the_audited_byte_hash():
    path = Path(__file__).resolve().parents[2] / "data" / "generated_training_cases.legacy_5000.jsonl"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "43af6f239602d9a040c2c8fad0280e3432037fd545ea3e5e86d36056c51a7a34"
    )


def test_expansion_phases_are_exact_and_no_family_crosses_a_split(expanded_training_cases):
    assert Counter(row.get("generation_phase", "legacy") for row in expanded_training_cases) == {
        "legacy": 5000,
        "phase_2_gap_expansion": 2500,
        "phase_3_weak_class_expansion": 2500,
    }
    family_splits = defaultdict(set)
    for row in expanded_training_cases:
        family_splits[row["family_hash"]].add(row["split"])
    assert len(family_splits) == 1000
    assert all(len(values) == 1 for values in family_splits.values())


def test_physical_split_files_match_the_canonical_dataset(expanded_training_cases):
    data_dir = Path(__file__).resolve().parents[2] / "data"
    expected = Counter(row["split"] for row in expanded_training_cases)
    for split in ("train", "validation", "test", "holdout"):
        rows = [
            json.loads(line)
            for line in (data_dir / f"generated_training_cases.{split}.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(rows) == expected[split]
        assert all(row["split"] == split for row in rows)
