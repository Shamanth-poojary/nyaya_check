"""
Schema contract freeze snapshot test.

Guards against accidental changes to the JSON contract consumed by downstream
phases (rules engine, report generator, frontend/backend). Any deliberate schema
change requires bumping SCHEMA_VERSION in app/schemas/response.py, updating
schema_snapshot.json, and documenting the change in CHANGELOG.md.
"""

import json
from pathlib import Path
from app.schemas.response import SCHEMA_VERSION, ExtractionResponse

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "schema_snapshot.json"


def test_schema_version_is_set():
    assert SCHEMA_VERSION == "2.0"
    resp = ExtractionResponse.model_construct()
    assert resp.schemaVersion == "2.0"


def test_schema_snapshot_matches():
    assert SNAPSHOT_PATH.exists(), f"Schema snapshot not found at {SNAPSHOT_PATH}"
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        expected_schema = json.load(f)

    current_schema = ExtractionResponse.model_json_schema()
    assert current_schema == expected_schema, (
        "ExtractionResponse JSON schema has changed! If this was deliberate, update "
        "SCHEMA_VERSION in app/schemas/response.py, update schema_snapshot.json, "
        "and document the changes in CHANGELOG.md."
    )
