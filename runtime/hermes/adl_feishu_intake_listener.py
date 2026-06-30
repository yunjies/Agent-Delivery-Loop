#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


RUNTIME = Path(__file__).resolve().with_name("adl_runtime.py")
LOOP_PREFIXES = ("#loop", "#wiki", "#ops", "#model", "#media", "#home", "#mteam", "#adl")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Route Feishu private/group messages into ADL intake")
    parser.add_argument("--profile", default="delivery-supervisor")
    parser.add_argument("--max-events", default="0")
    parser.add_argument("--timeout", default="0")
    parser.add_argument("--state-root", default="/opt/data/agent-delivery-loop")
    parser.add_argument("--promote", action="store_true", default=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    cmd = [
        "/opt/data/bin/lark-cli",
        "--profile",
        args.profile,
        "event",
        "consume",
        "im.message.receive_v1",
        "--as",
        "bot",
        "--quiet",
        "--max-events",
        str(args.max_events),
        "--timeout",
        str(args.timeout),
    ]
    completed = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert completed.stdout is not None
    processed = 0
    skipped = 0
    failed = 0
    for line in completed.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        decision = build_intake_command(event, state_root=args.state_root)
        if decision is None:
            skipped += 1
            continue
        processed += 1
        if args.dry_run:
            print(json.dumps({"ok": True, "dry_run": True, "command": decision}, ensure_ascii=False))
            continue
        result = subprocess.run(decision, text=True, capture_output=True)
        print(result.stdout, end="")
        if result.returncode != 0:
            failed += 1
            sys.stderr.write(result.stderr)
    returncode = completed.wait()
    stderr = completed.stderr.read() if completed.stderr else ""
    if stderr:
        sys.stderr.write(stderr)
    summary = {"ok": failed == 0 and returncode == 0, "processed": processed, "skipped": skipped, "failed": failed, "event_returncode": returncode}
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["ok"] else 1


def build_intake_command(event: dict, state_root: str) -> list[str] | None:
    content = str(event.get("content") or "").strip()
    if not _has_loop_prefix(content):
        return None
    requester_id = str(event.get("sender_id") or event.get("open_id") or "unknown_feishu_sender")
    source = "feishu_dm"
    if event.get("chat_id"):
        source = f"feishu:{event.get('chat_id')}"
    return [
        sys.executable,
        str(RUNTIME),
        "--state-root",
        state_root,
        "feishu-ingest",
        content,
        "--source",
        source,
        "--requester-kind",
        "feishu_user",
        "--requester-id",
        requester_id,
        "--promote",
    ]


def _has_loop_prefix(content: str) -> bool:
    lowered = content.lower().strip()
    return any(lowered.startswith(prefix) for prefix in LOOP_PREFIXES)


if __name__ == "__main__":
    raise SystemExit(main())
