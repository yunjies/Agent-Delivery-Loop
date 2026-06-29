from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .validation import validate_object


KIND_DIRS = {
    "IntakeAssessment": "intake",
    "Demand": "demands",
    "Goal": "goals",
    "Task": "tasks",
    "Attempt": "attempts",
    "Expert": "experts",
    "LoopDecision": "decisions",
    "Approval": "approvals",
}


class FilesystemStore:
    def __init__(self, root):
        self.root = Path(root)

    def init(self):
        for dirname in [*KIND_DIRS.values(), "events", "evidence"]:
            (self.root / dirname).mkdir(parents=True, exist_ok=True)
        return self

    def save(self, obj):
        validate_object(obj)
        kind = obj["kind"]
        obj_id = obj["metadata"]["id"]
        directory = self.root / KIND_DIRS[kind]
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{obj_id}.json"
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.append_event(kind, obj_id, "object_saved", {"path": str(path)})
        return path

    def load(self, kind, obj_id):
        path = self.root / KIND_DIRS[kind] / f"{obj_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def list_objects(self, kind):
        directory = self.root / KIND_DIRS[kind]
        if not directory.exists():
            return []
        objects = []
        for path in sorted(directory.glob("*.json")):
            objects.append(json.loads(path.read_text(encoding="utf-8")))
        return objects

    def summary(self):
        counts = {}
        for kind in KIND_DIRS:
            counts[kind] = len(self.list_objects(kind))
        event_count = 0
        events_dir = self.root / "events"
        if events_dir.exists():
            for path in events_dir.glob("*.jsonl"):
                event_count += len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])
        return {
            "workspace": str(self.root),
            "counts": counts,
            "events": event_count,
        }

    def append_event(self, kind, obj_id, event_type, payload):
        events_dir = self.root / "events"
        events_dir.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "object_id": obj_id,
            "type": event_type,
            "payload": payload,
        }
        with (events_dir / f"{obj_id}.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        return event
