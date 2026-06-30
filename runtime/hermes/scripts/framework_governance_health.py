#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


OUT_DIR = Path("/opt/data/workflows/outputs/framework-governance-health")
STATE_ROOT = Path("/opt/data/agent-delivery-loop")
PATH_RULES = STATE_ROOT / "config" / "path-governance.json"
FRAMEWORK_PROFILE = Path("/opt/data/profiles/framework-maintainer/config.yaml")
FRAMEWORK_SKILL = Path("/opt/data/profiles/framework-maintainer/skills/framework-governance/SKILL.md")
FRAMEWORK_SCRIPTS = [
    Path("/opt/data/profiles/framework-maintainer/scripts/path_governance_check.py"),
    Path("/opt/data/profiles/framework-maintainer/scripts/framework_operation_plan.py"),
]
DELIVERY_SKILL = Path("/opt/data/profiles/delivery-supervisor/skills/adl-runtime-ops/SKILL.md")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = collect()
    (OUT_DIR / "framework-governance-health.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "framework-governance-health.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(OUT_DIR / "framework-governance-health.md"), "warnings": payload["warnings"]}, ensure_ascii=False))
    return 0 if payload["ok"] else 1


def collect() -> dict:
    checks = {
        "path_rules_exist": PATH_RULES.exists(),
        "framework_profile_exists": FRAMEWORK_PROFILE.exists(),
        "framework_skill_exists": FRAMEWORK_SKILL.exists(),
        "delivery_skill_exists": DELIVERY_SKILL.exists(),
        "framework_scripts_exist": all(path.exists() for path in FRAMEWORK_SCRIPTS),
    }
    rules = _load_rules()
    rule_ids = {rule.get("id") for rule in rules}
    checks["required_rule_ids"] = {"hermes-profiles", "hermes-skills", "hermes-workflows", "hermes-cron", "mind-palace-wiki"}.issubset(rule_ids)
    checks["workflow_owned_by_framework"] = _rule_owner(rules, "hermes-workflows") == "framework-maintainer"
    checks["wiki_owned_by_mind_palace"] = _rule_owner(rules, "mind-palace-wiki") == "mind-palace"
    checks["wiki_reroutes_to_mind_palace"] = _rule_delegate(rules, "mind-palace-wiki") == "mind-palace"
    warnings = [name for name, ok in checks.items() if not ok]
    return {
        "ok": not warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "warnings": warnings,
        "checks": checks,
        "rule_ids": sorted(rule_id for rule_id in rule_ids if rule_id),
    }


def _load_rules() -> list[dict]:
    if not PATH_RULES.exists():
        return []
    return (json.loads(PATH_RULES.read_text(encoding="utf-8")).get("rules") or [])


def _rule_owner(rules: list[dict], rule_id: str) -> str | None:
    for rule in rules:
        if rule.get("id") == rule_id:
            return rule.get("owner_profile")
    return None


def _rule_delegate(rules: list[dict], rule_id: str) -> str | None:
    for rule in rules:
        if rule.get("id") == rule_id:
            return rule.get("delegate_profile") or rule.get("owner_profile")
    return None


def render_markdown(payload: dict) -> str:
    lines = [
        "# Framework Governance Health",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- ok: `{payload['ok']}`",
        f"- warnings: `{', '.join(payload['warnings']) if payload['warnings'] else 'none'}`",
        "",
        "## Checks",
        "",
    ]
    for name, ok in payload["checks"].items():
        lines.append(f"- `{name}`: `{ok}`")
    lines.extend(["", "## Path Rule IDs", ""])
    lines.extend(f"- `{rule_id}`" for rule_id in payload["rule_ids"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
