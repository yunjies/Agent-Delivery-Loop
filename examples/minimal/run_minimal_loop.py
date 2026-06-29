#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "adapters" / "filesystem"))

from agent_delivery_filesystem import FilesystemWorkspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal Agent Delivery Loop filesystem demo")
    parser.add_argument("--workspace", default=str(Path(tempfile.gettempdir()) / "agent-delivery-loop-demo"))
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    workspace_path = Path(args.workspace)
    if args.reset and workspace_path.exists():
        shutil.rmtree(workspace_path)

    workspace = FilesystemWorkspace(workspace_path)
    expert = json.loads((ROOT / "protocol" / "fixtures" / "mind-palace-expert.example.json").read_text(encoding="utf-8"))
    workspace.register_expert(expert)
    _, goal = workspace.start_goal(
        title="Maintain Mind Palace wiki health",
        request="Keep the Mind Palace wiki healthy and propose safe next steps.",
        requester={"kind": "human", "id": "requester-example"},
        success_criteria=["lint report succeeds", "index plan remains proposal-only"],
        budget={"token_limit": 120000, "token_used_estimate": 0, "stop_when_remaining_below": 15000},
        permissions={"docs_write": False, "delete_move_archive": False, "cron_mutation": False, "external_send": True},
    )
    task, decision, ranked = workspace.propose_task(
        goal,
        task_type="workflow_run",
        objective="Run wiki_lint for Mind Palace and produce a report.",
        experts=[expert],
        permissions={"docs_write": False, "delete_move_archive": False, "cron_mutation": False, "external_send": True},
        acceptance={"evidence_required": True, "expected_evidence": ["report"]},
        required_capabilities=["wiki_lint"],
        budget={"token_limit": 12000, "token_used_estimate": 0, "max_attempts": 1},
    )
    if task is None:
        print(json.dumps({"ok": False, "decision": decision, "ranked": ranked}, ensure_ascii=False, indent=2))
        return 1
    attempt = workspace.submit_attempt(
        task,
        executor={"kind": "expert", "id": "mind-palace"},
        status="succeeded",
        summary="Demo report completed.",
        evidence=[{"kind": "report", "path": str(workspace_path / "reports" / "mind-palace-lint.md")}],
        budget_used={"token_used_estimate": 0, "time_limit_seconds": 1},
    )
    task = workspace.accept_task(task)
    print(json.dumps({
        "ok": True,
        "workspace": str(workspace_path),
        "goal_id": goal["metadata"]["id"],
        "task_id": task["metadata"]["id"],
        "attempt_id": attempt["metadata"]["id"],
        "decision_id": decision["metadata"]["id"],
        "ranked": ranked,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
