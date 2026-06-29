#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = Path(os.environ.get("ADL_STATE_ROOT", "/opt/data/agent-delivery-loop"))

for rel in [
    "packages/delivery-core",
    "packages/requester-sdk",
    "packages/expert-adapter-sdk",
    "adapters/feishu-notification",
]:
    sys.path.insert(0, str(FRAMEWORK_ROOT / rel))

from agent_delivery_expert import create_attempt
from agent_delivery_feishu_notification import create_notification_payload
from agent_delivery_loop import FilesystemStore, transition_task
from agent_delivery_requester import classify_intake, create_goal_from_demand, promote_intake_to_demand


SYSTEM_RISK_PERMISSIONS = {
    "docs_write",
    "delete_move_archive",
    "cron_mutation",
    "workflow_mutation",
    "profile_mutation",
    "code_write",
    "shell_exec",
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="adl-runtime", description="Hermes runtime helpers for Agent Delivery Loop")
    parser.add_argument("--state-root", default=str(STATE_ROOT))
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("feishu-ingest", help="Ingest one Feishu/Codex/Duoduo text request")
    ingest.add_argument("text")
    ingest.add_argument("--source", default="feishu_dm")
    ingest.add_argument("--requester-id", required=True)
    ingest.add_argument("--requester-kind", default="feishu_user")
    ingest.add_argument("--preferred-expert")
    ingest.add_argument("--promote", action="store_true")

    status = sub.add_parser("status", help="Print workspace status")

    register = sub.add_parser("register-default-experts", help="Register the initial Hermes experts")
    register.add_argument("--overwrite", action="store_true")

    tick = sub.add_parser("supervisor-tick", help="Run deterministic supervisor tick")

    enqueue = sub.add_parser("notify-enqueue", help="Create a Feishu notification payload in outbox")
    enqueue.add_argument("--goal-id", required=True)
    enqueue.add_argument("--message-type", required=True)
    enqueue.add_argument("--content", required=True)
    target = enqueue.add_mutually_exclusive_group(required=True)
    target.add_argument("--chat-id")
    target.add_argument("--user-id")
    enqueue.add_argument("--task-id")

    send = sub.add_parser("notify-send-outbox", help="Send queued Feishu notification payloads")
    send.add_argument("--profile", default="delivery-supervisor")
    send.add_argument("--dry-run", action="store_true")
    send.add_argument("--limit", type=int)

    run = sub.add_parser("run-workflow-task", help="Execute a Task through a controlled Hermes workflow adapter")
    run.add_argument("--task-id", required=True)
    run.add_argument("--workflow", required=True)
    run.add_argument("--trigger", default="agent-delivery-loop")
    run.add_argument("--mode", default="production", choices=["shadow", "production"])
    run.add_argument("--max-ticks", default="8")

    args = parser.parse_args(argv)
    state_root = Path(args.state_root)
    if args.command == "feishu-ingest":
        return _cmd_feishu_ingest(args, state_root)
    if args.command == "status":
        print(json.dumps(FilesystemStore(state_root).summary(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "register-default-experts":
        return _cmd_register_default_experts(args, state_root)
    if args.command == "supervisor-tick":
        return _cmd_supervisor_tick(state_root)
    if args.command == "notify-enqueue":
        return _cmd_notify_enqueue(args, state_root)
    if args.command == "notify-send-outbox":
        return _cmd_notify_send_outbox(args, state_root)
    if args.command == "run-workflow-task":
        return _cmd_run_workflow_task(args, state_root)
    raise AssertionError(args.command)


def _cmd_feishu_ingest(args, state_root: Path) -> int:
    store = FilesystemStore(state_root).init()
    text = _strip_known_prefix(args.text)
    preferred = args.preferred_expert or _expert_from_prefix(args.text)
    assessment = classify_intake(
        text,
        requester={"kind": args.requester_kind, "id": args.requester_id},
        source=args.source,
        preferred_expert=preferred,
    )
    store.save(assessment)
    output = {"ok": True, "assessment": assessment, "saved": {"kind": "IntakeAssessment", "id": assessment["metadata"]["id"]}}
    if args.promote and assessment["spec"]["classification"] == "loop_candidate":
        demand = promote_intake_to_demand(assessment)
        goal = create_goal_from_demand(demand)
        store.save(demand)
        store.save(goal)
        output["promoted"] = {"demand_id": demand["metadata"]["id"], "goal_id": goal["metadata"]["id"]}
    elif args.promote:
        output["promoted"] = None
        output["promotion_error"] = f"intake is {assessment['spec']['classification']}"
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _cmd_register_default_experts(args, state_root: Path) -> int:
    store = FilesystemStore(state_root).init()
    registered = []
    skipped = []
    for expert in _default_experts():
        path = state_root / "experts" / f"{expert['metadata']['id']}.json"
        if path.exists() and not args.overwrite:
            skipped.append(expert["metadata"]["id"])
            continue
        store.save(expert)
        registered.append(expert["metadata"]["id"])
    print(json.dumps({"ok": True, "registered": registered, "skipped": skipped}, ensure_ascii=False, indent=2))
    return 0


def _cmd_supervisor_tick(state_root: Path) -> int:
    adl = FRAMEWORK_ROOT / "scripts" / "adl.py"
    completed = subprocess.run([sys.executable, str(adl), "supervisor-tick", str(state_root)], text=True, capture_output=True)
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode


def _cmd_notify_enqueue(args, state_root: Path) -> int:
    store = FilesystemStore(state_root).init()
    goal = store.load("Goal", args.goal_id)
    task = store.load("Task", args.task_id) if args.task_id else None
    target = {"type": "feishu"}
    if args.chat_id:
        target["chat_id"] = args.chat_id
    if args.user_id:
        target["user_id"] = args.user_id
    payload = create_notification_payload(goal, args.message_type, args.content, target, task=task)
    outbox = state_root / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    out_id = _stable_outbox_id(payload)
    path = outbox / f"{out_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "outbox_id": out_id, "path": str(path)}, ensure_ascii=False, indent=2))
    return 0


def _cmd_notify_send_outbox(args, state_root: Path) -> int:
    outbox = state_root / "outbox"
    sent = state_root / "outbox-sent"
    failed = state_root / "outbox-failed"
    sent.mkdir(parents=True, exist_ok=True)
    failed.mkdir(parents=True, exist_ok=True)
    paths = sorted(outbox.glob("*.json"))
    if args.limit is not None:
        paths = paths[: args.limit]
    results = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = _send_feishu_payload(payload, profile=args.profile, dry_run=args.dry_run)
        results.append({"path": str(path), **result})
        if result["ok"] and not args.dry_run:
            shutil.move(str(path), str(sent / path.name))
        elif not result["ok"]:
            shutil.move(str(path), str(failed / path.name))
    print(json.dumps({"ok": all(item["ok"] for item in results), "results": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in results) else 1


def _cmd_run_workflow_task(args, state_root: Path) -> int:
    store = FilesystemStore(state_root).init()
    task = store.load("Task", args.task_id)
    permissions = task["spec"].get("permissions") or {}
    high_risk = [key for key, value in permissions.items() if value and key in SYSTEM_RISK_PERMISSIONS]
    if high_risk:
        print(json.dumps({"ok": False, "error": "task requests high-risk system permissions", "permissions": high_risk}, ensure_ascii=False, indent=2))
        return 2
    workflow_script = [
        "/opt/hermes/.venv/bin/python",
        "/opt/data/scripts/workflow_runtime.py",
        "run",
        "--workflow",
        args.workflow,
        "--trigger",
        args.trigger,
        "--mode",
        args.mode,
        "--max-ticks",
        str(args.max_ticks),
    ]
    task = _ensure_submitted_after_run_transition(task)
    completed = subprocess.run(workflow_script, cwd="/opt/data", text=True, capture_output=True, timeout=1200)
    status = "succeeded" if completed.returncode == 0 else "failed"
    summary = _workflow_summary(args.workflow, completed)
    evidence = [{"kind": "workflow_result", "path": _write_workflow_evidence(state_root, args.task_id, args.workflow, completed)}]
    attempt = create_attempt(
        task,
        executor={"kind": "hermes_workflow", "id": args.workflow},
        status=status,
        summary=summary,
        evidence=evidence,
        budget_used={"token_used_estimate": 0},
        error=None if completed.returncode == 0 else (completed.stderr or completed.stdout)[-1000:],
    )
    task["spec"]["state"]["latest_attempt_id"] = attempt["metadata"]["id"]
    store.save(task)
    store.save(attempt)
    print(json.dumps({"ok": completed.returncode == 0, "task_id": args.task_id, "attempt_id": attempt["metadata"]["id"], "status": status}, ensure_ascii=False, indent=2))
    return 0 if completed.returncode == 0 else 1


def _send_feishu_payload(payload: dict, profile: str, dry_run: bool) -> dict:
    target = payload.get("target") or {}
    cmd = ["/opt/data/bin/lark-cli", "--profile", profile, "im", "+messages-send", "--as", "bot"]
    if target.get("chat_id"):
        cmd.extend(["--chat-id", target["chat_id"]])
    elif target.get("user_id"):
        cmd.extend(["--user-id", target["user_id"]])
    else:
        return {"ok": False, "error": "missing chat_id or user_id target"}
    cmd.extend(["--text", _notification_text(payload)])
    if dry_run:
        cmd.append("--dry-run")
    completed = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_tail": (completed.stdout or "")[-1000:],
        "stderr_tail": (completed.stderr or "")[-1000:],
        "dry_run": dry_run,
    }


def _notification_text(payload: dict) -> str:
    lines = [
        f"[ADL] {payload.get('message_type')}",
        f"goal: {payload.get('goal_id')}",
    ]
    if payload.get("task_id"):
        lines.append(f"task: {payload.get('task_id')}")
    lines.append(str(payload.get("content") or ""))
    return "\n".join(lines)


def _default_experts() -> list[dict]:
    return [
        {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "mind-palace", "title": "Mind Palace"},
            "spec": {
                "expert_kind": "hermes_profile",
                "capabilities": [
                    {"id": "wiki_survey", "description": "Survey Mind Palace wiki state", "priority": 90, "cost_class": "low", "reliability": "high", "default_owner": True},
                    {"id": "wiki_lint", "description": "Run wiki lint and report warnings", "priority": 95, "cost_class": "low", "reliability": "high", "default_owner": True},
                    {"id": "wiki_index_plan", "description": "Create wiki index plan", "priority": 80, "cost_class": "low", "reliability": "high", "default_owner": True},
                ],
                "invocation": {"adapter": "hermes_workflow", "profile": "mind-palace", "workflows": ["mind-palace-survey-smoke", "mind-palace-lint", "mind-palace-index-plan"]},
            },
        },
        {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "ops-auditor", "title": "Ops Auditor"},
            "spec": {
                "expert_kind": "hermes_profile",
                "capabilities": [
                    {"id": "system_health", "description": "Report runtime system health", "priority": 85, "cost_class": "low", "reliability": "high", "default_owner": True},
                    {"id": "skill_health", "description": "Report Hermes skill health", "priority": 80, "cost_class": "low", "reliability": "high", "default_owner": True},
                    {"id": "cron_health", "description": "Report cron health", "priority": 75, "cost_class": "low", "reliability": "high", "default_owner": True},
                ],
                "invocation": {"adapter": "hermes_workflow", "profile": "ops-auditor", "workflows": ["system-health-check", "skill-health-scanner"]},
            },
        },
        {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "lark-operator", "title": "Lark Operator"},
            "spec": {
                "expert_kind": "feishu_operator",
                "capabilities": [
                    {"id": "feishu_message_send", "description": "Send Feishu messages for delegated business tasks", "priority": 75, "cost_class": "low", "reliability": "medium", "default_owner": True},
                    {"id": "feishu_status_notify", "description": "Send ADL supervision notifications", "priority": 80, "cost_class": "low", "reliability": "medium", "default_owner": True},
                ],
                "invocation": {"adapter": "feishu_notification", "profile": "delivery-supervisor"},
            },
        },
        {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "model-maintainer", "title": "Model Maintainer"},
            "spec": {
                "expert_kind": "hermes_profile",
                "capabilities": [
                    {"id": "model_registry_check", "description": "Check model registry state", "priority": 65, "cost_class": "low", "reliability": "medium", "default_owner": True},
                    {"id": "model_smoke", "description": "Run model smoke checks", "priority": 65, "cost_class": "low", "reliability": "medium", "default_owner": True},
                ],
                "invocation": {"adapter": "proposal_only", "profile": "model-maintainer"},
            },
        },
    ]


def _strip_known_prefix(text: str) -> str:
    stripped = text.strip()
    for prefix in ["#loop", "#wiki", "#ops", "#model", "#adl"]:
        if stripped.lower().startswith(prefix):
            return stripped[len(prefix):].strip()
    return stripped


def _expert_from_prefix(text: str) -> str | None:
    lowered = text.strip().lower()
    if lowered.startswith("#wiki"):
        return "mind-palace"
    if lowered.startswith("#ops"):
        return "ops-auditor"
    if lowered.startswith("#model"):
        return "model-maintainer"
    return None


def _stable_outbox_id(payload: dict) -> str:
    import hashlib

    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return "outbox-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _ensure_submitted_after_run_transition(task: dict) -> dict:
    status = task["spec"]["state"]["status"]
    if status == "pending":
        task = transition_task(task, "running")
        return transition_task(task, "submitted")
    if status == "running":
        return transition_task(task, "submitted")
    if status == "submitted":
        return task
    raise ValueError(f"task cannot be executed from status: {status}")


def _workflow_summary(workflow: str, completed: subprocess.CompletedProcess[str]) -> str:
    if completed.returncode == 0:
        return f"Workflow {workflow} completed."
    return f"Workflow {workflow} failed with exit code {completed.returncode}."


def _write_workflow_evidence(state_root: Path, task_id: str, workflow: str, completed: subprocess.CompletedProcess[str]) -> str:
    evidence_dir = state_root / "evidence" / task_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"{workflow}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    payload = {
        "workflow": workflow,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
