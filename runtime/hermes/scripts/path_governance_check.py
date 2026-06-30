#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STATE_ROOT = Path(os.environ.get("ADL_STATE_ROOT", "/opt/data/agent-delivery-loop"))
DEFAULT_CONFIG = DEFAULT_STATE_ROOT / "config" / "path-governance.json"
BUNDLED_CONFIG = Path(__file__).resolve().parents[1] / "config" / "path-governance.json"
DEFAULT_OUT_DIR = Path("/opt/data/workflows/outputs/path-governance-check")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check whether changed paths are owned by the acting Hermes profile.")
    parser.add_argument("--actor-profile", required=True)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--changed-paths-file")
    parser.add_argument("--check-mode", default="planned", choices=["planned", "observed", "cron", "health"])
    parser.add_argument("--session-id")
    parser.add_argument("--reason")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--strict-unowned", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args(argv)

    changed_paths = list(args.changed_path)
    if args.changed_paths_file:
        changed_paths.extend(_read_changed_paths(Path(args.changed_paths_file)))
    payload = check_paths(
        actor_profile=args.actor_profile,
        changed_paths=changed_paths,
        config_path=Path(args.config),
        strict_unowned=args.strict_unowned,
        check_mode=args.check_mode,
        session_id=args.session_id,
        reason=args.reason,
    )
    if args.write_report:
        write_reports(payload, Path(args.out_dir))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 2


def check_paths(
    actor_profile: str,
    changed_paths: list[str],
    config_path: Path = DEFAULT_CONFIG,
    strict_unowned: bool = False,
    check_mode: str = "planned",
    session_id: str | None = None,
    reason: str | None = None,
) -> dict:
    config = load_config(config_path)
    results = [check_one_path(actor_profile, changed_path, config, strict_unowned) for changed_path in changed_paths]
    violations = [item for item in results if item["status"] == "violation"]
    warnings = [item for item in results if item["status"] == "warning"]
    return {
        "ok": not violations,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actor_profile": actor_profile,
        "check_mode": check_mode,
        "session_id": session_id,
        "reason": reason,
        "config_path": str(config_path if config_path.exists() else BUNDLED_CONFIG),
        "changed_path_count": len(changed_paths),
        "violations": violations,
        "warnings": warnings,
        "results": results,
    }


def check_one_path(actor_profile: str, changed_path: str, config: dict, strict_unowned: bool = False) -> dict:
    normalized = normalize_path(changed_path)
    rule = best_rule_for_path(normalized, config.get("rules") or [])
    if not rule:
        status = "violation" if strict_unowned else "ok"
        return {"path": normalized, "status": status, "rule_id": None, "message": "unowned path"}

    allowed_profiles = rule.get("allowed_profiles") or [rule.get("owner_profile")]
    if actor_profile in allowed_profiles:
        return {
            "path": normalized,
            "status": "ok",
            "rule_id": rule.get("id"),
            "owner_profile": rule.get("owner_profile"),
            "allowed_profiles": allowed_profiles,
        }

    decision = rule.get("decision", "block")
    status = "warning" if decision == "warn" else "violation"
    return {
        "path": normalized,
        "status": status,
        "rule_id": rule.get("id"),
        "owner_profile": rule.get("owner_profile"),
        "allowed_profiles": allowed_profiles,
        "actor_profile": actor_profile,
        "message": f"path is owned by {rule.get('owner_profile')}",
    }


def best_rule_for_path(path: str, rules: list[dict]) -> dict | None:
    matches = []
    for rule in rules:
        for pattern in rule.get("match") or []:
            normalized_pattern = normalize_path(pattern)
            if fnmatch.fnmatch(path, normalized_pattern):
                matches.append((len(normalized_pattern), rule))
    if not matches:
        return None
    return sorted(matches, key=lambda item: item[0], reverse=True)[0][1]


def normalize_path(path: str) -> str:
    value = path.replace("\\", "/")
    while "//" in value:
        value = value.replace("//", "/")
    return value.rstrip("/") if value != "/" else value


def load_config(config_path: Path) -> dict:
    path = config_path if config_path.exists() else BUNDLED_CONFIG
    return json.loads(path.read_text(encoding="utf-8"))


def _read_changed_paths(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_reports(payload: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "path-governance-check.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "path-governance-check.md").write_text(render_markdown(payload), encoding="utf-8")


def render_markdown(payload: dict) -> str:
    lines = [
        "# Path Governance Check",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- actor_profile: `{payload['actor_profile']}`",
        f"- check_mode: `{payload['check_mode']}`",
        f"- session_id: `{payload['session_id'] or 'none'}`",
        f"- reason: `{payload['reason'] or 'none'}`",
        f"- ok: `{payload['ok']}`",
        f"- changed_path_count: `{payload['changed_path_count']}`",
        "",
        "## Violations",
        "",
    ]
    if payload["violations"]:
        for item in payload["violations"]:
            lines.append(f"- `{item['path']}`: {item.get('message', 'violation')} (rule `{item.get('rule_id')}`)")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if payload["warnings"]:
        for item in payload["warnings"]:
            lines.append(f"- `{item['path']}`: {item.get('message', 'warning')} (rule `{item.get('rule_id')}`)")
    else:
        lines.append("- none")
    lines.extend(["", "## Results", ""])
    for item in payload["results"]:
        lines.append(f"- `{item['path']}`: `{item['status']}` rule=`{item.get('rule_id')}` owner=`{item.get('owner_profile')}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
