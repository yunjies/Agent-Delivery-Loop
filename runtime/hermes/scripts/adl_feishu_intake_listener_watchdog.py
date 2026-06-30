#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path


STATE_ROOT = Path("/opt/data/agent-delivery-loop")
PID_FILE = STATE_ROOT / "run" / "feishu-intake-listener.pid"
LOG_FILE = STATE_ROOT / "logs" / "feishu-intake-listener.log"
LISTENER = "/opt/data/agent-delivery-loop/framework/runtime/hermes/adl_feishu_intake_listener.py"


def main() -> int:
    STATE_ROOT.joinpath("run").mkdir(parents=True, exist_ok=True)
    STATE_ROOT.joinpath("logs").mkdir(parents=True, exist_ok=True)
    current = _read_pid()
    if current and _pid_alive(current):
        print(json.dumps({"ok": True, "status": "already_running", "pid": current}, ensure_ascii=False))
        return 0
    cmd = [
        "python3",
        LISTENER,
        "--profile",
        "delivery-supervisor",
        "--state-root",
        str(STATE_ROOT),
    ]
    with LOG_FILE.open("ab") as log:
        log.write(f"\n--- start {datetime.now(timezone.utc).isoformat()} ---\n".encode("utf-8"))
        process = subprocess.Popen(cmd, stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
    PID_FILE.write_text(str(process.pid) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": "started", "pid": process.pid, "log": str(LOG_FILE)}, ensure_ascii=False))
    return 0


def _read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


if __name__ == "__main__":
    raise SystemExit(main())
