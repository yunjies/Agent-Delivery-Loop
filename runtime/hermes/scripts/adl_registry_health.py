#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


STATE_ROOT = Path("/opt/data/agent-delivery-loop")
FRAMEWORK = STATE_ROOT / "framework"
OUT_DIR = Path("/opt/data/workflows/outputs/adl-registry-health")
PROFILES_DIR = Path("/opt/data/profiles")
WORKFLOW_SPEC_DIR = Path("/opt/data/workflows/specs")

EXPECTED_EXPERTS = {
    "mind-palace",
    "ops-auditor",
    "home-media",
    "framework-maintainer",
    "lark-operator",
}
NON_EXPERT_PROFILES = {"default", "delivery-supervisor"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    register_result = _register_known_experts()
    payload = collect(register_result)
    (OUT_DIR / "adl-registry-health.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "adl-registry-health.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(OUT_DIR / "adl-registry-health.md"), "warnings": payload["warnings"]}, ensure_ascii=False))
    return 0 if payload["ok"] else 1


def _register_known_experts() -> dict:
    cmd = [
        "python3",
        str(FRAMEWORK / "runtime" / "hermes" / "adl_runtime.py"),
        "register-default-experts",
        "--overwrite",
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    result = {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_tail": (completed.stdout or "")[-2000:],
        "stderr_tail": (completed.stderr or "")[-2000:],
    }
    try:
        result["payload"] = json.loads(completed.stdout)
    except json.JSONDecodeError:
        pass
    return result


def collect(register_result: dict) -> dict:
    profiles = sorted(path.name for path in PROFILES_DIR.iterdir() if path.is_dir())
    expert_files = sorted(path.name for path in (STATE_ROOT / "experts").glob("*.json"))
    experts = {}
    for path in sorted((STATE_ROOT / "experts").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            experts[data["metadata"]["id"]] = data
        except Exception as exc:
            experts[path.stem] = {"error": str(exc)}
    workflows = sorted(path.stem.replace(".workflow", "") for path in WORKFLOW_SPEC_DIR.glob("*.workflow.yaml"))
    missing_expected = sorted(EXPECTED_EXPERTS - set(experts))
    unknown_experts = sorted(set(experts) - EXPECTED_EXPERTS)
    candidate_profiles = sorted(set(profiles) - NON_EXPERT_PROFILES - set(experts))
    workflow_gaps = {}
    for expert_id, expert in experts.items():
        invocation = (expert.get("spec") or {}).get("invocation") or {}
        missing = [workflow for workflow in invocation.get("workflows", []) if workflow not in workflows]
        if missing:
            workflow_gaps[expert_id] = missing
    warnings = []
    if not register_result["ok"]:
        warnings.append("register_known_experts_failed")
    if missing_expected:
        warnings.append("missing_expected_experts")
    if candidate_profiles:
        warnings.append("unregistered_profile_candidates")
    if workflow_gaps:
        warnings.append("expert_workflow_gaps")
    return {
        "ok": not missing_expected and not workflow_gaps and register_result["ok"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "register_result": register_result,
        "profiles": profiles,
        "experts": sorted(experts),
        "expert_files": expert_files,
        "workflows": workflows,
        "missing_expected_experts": missing_expected,
        "unknown_experts": unknown_experts,
        "unregistered_profile_candidates": candidate_profiles,
        "expert_workflow_gaps": workflow_gaps,
        "warnings": warnings,
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# ADL Registry Health",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- ok: `{payload['ok']}`",
        f"- warnings: `{', '.join(payload['warnings']) if payload['warnings'] else 'none'}`",
        "",
        "## Register Known Experts",
        "",
        f"- ok: `{payload['register_result']['ok']}`",
        f"- returncode: `{payload['register_result']['returncode']}`",
        "",
        "## Experts",
        "",
    ]
    lines.extend(f"- `{expert}`" for expert in payload["experts"])
    lines.extend(["", "## Profiles", ""])
    lines.extend(f"- `{profile}`" for profile in payload["profiles"])
    lines.extend(["", "## Unregistered Profile Candidates", ""])
    if payload["unregistered_profile_candidates"]:
        lines.extend(f"- `{profile}`" for profile in payload["unregistered_profile_candidates"])
    else:
        lines.append("- none")
    lines.extend(["", "## Missing Expected Experts", ""])
    if payload["missing_expected_experts"]:
        lines.extend(f"- `{expert}`" for expert in payload["missing_expected_experts"])
    else:
        lines.append("- none")
    lines.extend(["", "## Expert Workflow Gaps", ""])
    if payload["expert_workflow_gaps"]:
        for expert, workflows in payload["expert_workflow_gaps"].items():
            lines.append(f"- `{expert}`: {', '.join(f'`{workflow}`' for workflow in workflows)}")
    else:
        lines.append("- none")
    lines.extend(["", "## Workflow Specs", ""])
    lines.extend(f"- `{workflow}`" for workflow in payload["workflows"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
