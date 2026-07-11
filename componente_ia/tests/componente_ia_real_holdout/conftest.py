import json
from pathlib import Path

import pytest


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load(name: str):
    path = DATA_DIR / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="session")
def real_holdout_cases():
    return _load("real_holdout_cases.jsonl")


@pytest.fixture(scope="session")
def entity_holdout_cases():
    return _load("entity_holdout_cases.jsonl")


@pytest.fixture(scope="session")
def expanded_training_cases():
    return _load("generated_training_cases.jsonl")
