import json
from pathlib import Path


def test_json_fixtures_load():
    """Load every JSON file under data/examples to ensure they are syntactically valid."""
    base_dir = Path(__file__).resolve().parents[2] / "data" / "examples"
    json_files = list(base_dir.rglob("*.json"))
    assert json_files, "No JSON fixture files found under data/examples"

    for json_path in json_files:
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as exc:
                assert False, f"Invalid JSON in {json_path}: {exc}"
