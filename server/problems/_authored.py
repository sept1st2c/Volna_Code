import json
from pathlib import Path

from problems.schema import Problem

_DATA_DIR = Path(__file__).resolve().parent / "data" / "authored"


def load_authored_problem(filename: str) -> Problem:
    """Loads one problem's full authored content (statement, constraints,
    hint ladder, test cases, complexity probe, etc.) from its editable JSON
    file in problems/data/authored/ -- the file IS the source of truth,
    validated against the same Problem schema every hardcoded PROBLEM used
    to satisfy directly. Editing a problem is now a JSON edit, not a Python
    edit; each problems/<slug>.py module just points at its file and merges
    in the separate dataset-sourced bulk test cases (see problems/_bulk.py).
    """
    path = _DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return Problem.model_validate(raw)
