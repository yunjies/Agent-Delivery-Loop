#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from path_governance_check import check_paths


DEFAULT_STATE_ROOT = Path(os.environ.get("ADL_STATE_ROOT", "/opt/data/agent-delivery-loop"))
DEFAULT_OUT_DIR = Path("/opt/data/workflows/outputs/framework-operation-plan")

OPERATIONS = {
    "profile:create": "Create a Hermes profile.",
    "profile:update": "Update a Hermes profile.",
    "skill:create": "Create or expose a Hermes skill.",
    "skill:update": "Update a Hermes skill.",
    "workflow:create": "Create a Hermes workflow spec or script.",
    "workflow:update": "Update a Hermes workflow spec or script.",
    "cron:create": "Create a cron binding.",
    "cron:update": "Update a cron binding.",
    "model:update": "Update model registry or routing.",
    "gateway:update": "Update gateway service config.",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a guarded framework operation plan.")
    parser.add_argument("--operation", required=True, choices=sorted(OPERATIONS))
    parser.add_argument("--title", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--actor-profile", default="framework-maintainer")
    parser.add_argument("--target-profile")
    parser.add_argument("--target-skill")
    parser.add_argument("--target-workflow")
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT))
    parser.add_argument("--session-id")
    parser.add_argument("--strict-unowned", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args(argv)

    payload = create_plan(args)
    if args.write_report:
        write_reports(payload, Path(args.out_dir))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 2


def create_plan(args) -> dict:
    state_root = Path(args.state_root)
    changed_paths = sorted(set([*args.changed_path, *derived_paths(args)]))
    validation = validate_request(args, changed_paths)
    preflight = check_paths(
        actor_profile=args.actor_profile,
        changed_paths=changed_paths,
        config_path=state_root / "config" / "path-governance.json",
        strict_unowned=args.strict_unowned,
        check_mode="planned",
        session_id=args.session_id,
        reason=f"framework-operation:{args.operation}",
    )
    ok = validation["ok"] and preflight["ok"]
    return {
        "ok": ok,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "operation": args.operation,
        "title": args.title,
        "intent": args.intent,
        "actor_profile": args.actor_profile,
        "targets": {
            "profile": args.target_profile,
            "skill": args.target_skill,
            "workflow": args.target_workflow,
        },
        "changed_paths": changed_paths,
        "validation": validation,
        "path_governance": preflight,
        "activation": activation_plan(args.operation),
    }


def derived_paths(args) -> list[str]:
    paths = []
    if args.target_profile and args.operation.startswith("profile:"):
        paths.append(f"/opt/data/profiles/{args.target_profile}/config.yaml")
    if args.target_profile and args.target_skill and args.operation.startswith("skill:"):
        paths.append(f"/opt/data/profiles/{args.target_profile}/skills/{args.target_skill}/SKILL.md")
    if args.target_workflow and args.operation.startswith("workflow:"):
        paths.append(f"/opt/data/workflows/specs/{args.target_workflow}.workflow.yaml")
    if args.operation.startswith("cron:"):
        paths.append("/opt/data/cron/jobs.json")
    if args.operation == "model:update":
        paths.append("/opt/data/config.yaml")
    if args.operation == "gateway:update" and args.target_profile:
        paths.append(f"/opt/data/profiles/{args.target_profile}/config.yaml")
    return paths


def validate_request(args, changed_paths: list[str]) -> dict:
    errors = []
    if args.actor_profile != "framework-maintainer":
        errors.append("framework operations must use actor_profile=framework-maintainer")
    if args.target_profile and not _valid_slug(args.target_profile):
        errors.append("target_profile must be a lowercase slug")
    if args.target_skill and not _valid_slug(args.target_skill):
        errors.append("target_skill must be a lowercase slug")
    if args.target_workflow and not _valid_slug(args.target_workflow):
        errors.append("target_workflow must be a lowercase slug")
    if args.operation.startswith("profile:") and not args.target_profile:
        errors.append("profile operations require --target-profile")
    if args.operation.startswith("skill:") and not (args.target_profile and args.target_skill):
        errors.append("skill operations require --target-profile and --target-skill")
    if args.operation.startswith("workflow:") and not args.target_workflow:
        errors.append("workflow operations require --target-workflow")
    if args.operation == "gateway:update" and not args.target_profile:
        errors.append("gateway operations require --target-profile")
    if not changed_paths:
        errors.append("operation has no changed paths")
    return {"ok": not errors, "errors": errors}


def activation_plan(operation: str) -> dict:
    checks = [
        "path_governance_planned_ok",
        "make_change_only_after_plan_acceptance",
        "path_governance_observed_ok",
        "release_check_ok",
    ]
    if operation.startswith("workflow:"):
        checks.append("workflow_smoke_ok")
    if operation.startswith("cron:"):
        checks.append("cron_binding_reviewed")
    if operation.startswith("profile:"):
        checks.append("profile_config_loads")
    if operation.startswith("skill:"):
        checks.append("skill_format_valid")
    if operation == "gateway:update":
        checks.extend(["gateway_process_isolated", "feishu_private_message_smoke_ok"])
    return {
        "mode": "plan_then_apply",
        "checks_required_before_active": checks,
        "do_not_activate_on_failed_check": True,
    }


def write_reports(payload: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "framework-operation-plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "framework-operation-plan.md").write_text(render_markdown(payload), encoding="utf-8")


def render_markdown(payload: dict) -> str:
    lines = [
        "# Framework Operation Plan",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- operation: `{payload['operation']}`",
        f"- title: `{payload['title']}`",
        f"- actor_profile: `{payload['actor_profile']}`",
        f"- ok: `{payload['ok']}`",
        "",
        "## Intent",
        "",
        payload["intent"],
        "",
        "## Changed Paths",
        "",
    ]
    lines.extend(f"- `{path}`" for path in payload["changed_paths"])
    lines.extend(["", "## Validation", "", f"- ok: `{payload['validation']['ok']}`"])
    if payload["validation"]["errors"]:
        lines.extend(f"- {error}" for error in payload["validation"]["errors"])
    lines.extend(["", "## Path Governance", "", f"- ok: `{payload['path_governance']['ok']}`"])
    for item in payload["path_governance"].get("violations", []):
        lines.append(f"- violation `{item.get('path')}` owner=`{item.get('owner_profile')}` reroute=`{item.get('reroute_profile')}`")
    lines.extend(["", "## Activation Checks", ""])
    lines.extend(f"- `{check}`" for check in payload["activation"]["checks_required_before_active"])
    lines.append("")
    return "\n".join(lines)


def _valid_slug(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", value or ""))


if __name__ == "__main__":
    raise SystemExit(main())
