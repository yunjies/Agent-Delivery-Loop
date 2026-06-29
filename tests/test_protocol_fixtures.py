import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fixture_json_is_valid():
    for path in (ROOT / "protocol" / "fixtures").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_schema_json_is_valid():
    for path in (ROOT / "protocol" / "schemas").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_minimal_task_denies_business_mutation():
    task = json.loads((ROOT / "protocol" / "fixtures" / "minimal-task.example.json").read_text(encoding="utf-8"))
    permissions = task["spec"]["permissions"]
    assert permissions["docs_write"] is False
    assert permissions["delete_move_archive"] is False
    assert permissions["cron_mutation"] is False
    assert permissions["workflow_mutation"] is False
