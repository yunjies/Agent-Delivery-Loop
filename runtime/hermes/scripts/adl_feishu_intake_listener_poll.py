#!/usr/bin/env python3
from __future__ import annotations

import subprocess


def main() -> int:
    return subprocess.call(
        [
            "python3",
            "/opt/data/agent-delivery-loop/framework/runtime/hermes/adl_feishu_intake_listener.py",
            "--profile",
            "delivery-supervisor",
            "--state-root",
            "/opt/data/agent-delivery-loop",
            "--timeout",
            "90s",
            "--max-events",
            "20",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
