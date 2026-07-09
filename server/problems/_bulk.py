import json
from pathlib import Path

from problems.schema import TestCase

_DATA_DIR = Path(__file__).resolve().parent / "data"


def load_bulk_cases(filename: str) -> list[TestCase]:
    """Load dataset-sourced breadth test cases (see dev/merge_dataset_cases.py).

    These are unlabeled bulk cases (is_edge_case=False) that widen coverage
    beyond the hand-authored, explained edge cases already in each problem
    file. IDs are prefixed 'ds_' to distinguish their provenance.
    """
    path = _DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [
        TestCase(id=f"ds_{i:03d}", args=entry["args"], expected=entry["expected"])
        for i, entry in enumerate(raw)
    ]
