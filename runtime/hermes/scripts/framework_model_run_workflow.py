#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a framework model workflow")
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--trigger", required=True)
    parser.add_argument("--mode", default="production", choices=["shadow", "production"])
    parser.add_argument("--max-ticks", default="8")
    args = parser.parse_args()
    cmd = [
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
        args.max_ticks,
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, timeout=1200)
    payload = {
        "ok": completed.returncode == 0,
        "workflow": args.workflow,
        "trigger": args.trigger,
        "mode": args.mode,
        "exit_code": completed.returncode,
    }
    if completed.stdout.strip():
        try:
            payload["workflow_result"] = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload["stdout_tail"] = completed.stdout[-2000:]
    if completed.stderr.strip():
        payload["stderr_tail"] = completed.stderr[-2000:]
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
