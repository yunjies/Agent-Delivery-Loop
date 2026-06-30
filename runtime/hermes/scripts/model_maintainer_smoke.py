#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


OUT_DIR = Path("/opt/data/workflows/outputs/model-smoke")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks = [
        _run_check(
            "deepseek-default",
            [
                "/opt/hermes/.venv/bin/hermes",
                "--ignore-rules",
                "--oneshot",
                "Return exactly: MODEL_SMOKE_OK",
                "--provider",
                "deepseek",
                "--model",
                "deepseek-v4-flash",
            ],
        )
    ]
    payload = {
        "ok": all(item["ok"] for item in checks),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
    (OUT_DIR / "model-smoke-report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "model-smoke-report.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(OUT_DIR / "model-smoke-report.md")}, ensure_ascii=False))
    return 0 if payload["ok"] else 1


def _run_check(name: str, cmd: list[str]) -> dict:
    try:
        completed = subprocess.run(cmd, cwd="/opt/data", text=True, capture_output=True, timeout=180)
    except subprocess.TimeoutExpired as exc:
        return {"name": name, "ok": False, "error": f"timeout:{exc.timeout}"}
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "name": name,
        "ok": completed.returncode == 0 and "MODEL_SMOKE_OK" in stdout,
        "returncode": completed.returncode,
        "stdout_tail": stdout[-1000:],
        "stderr_tail": stderr[-1000:],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Model Smoke",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- ok: `{payload['ok']}`",
        "",
        "## Checks",
    ]
    for item in payload["checks"]:
        lines.append(f"- `{item['name']}` ok=`{item['ok']}` returncode=`{item.get('returncode')}`")
        if item.get("stderr_tail"):
            lines.append(f"  - stderr_tail: `{item['stderr_tail'][-300:]}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
