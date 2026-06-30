#!/usr/bin/env python3
from __future__ import annotations

import subprocess


def main() -> int:
    return subprocess.call(
        [
            "python3",
            "/opt/data/profiles/delivery-supervisor/scripts/adl_registry_health_run_workflow.py",
            "--workflow",
            "adl-registry-health",
            "--trigger",
            "cron:adl-registry-health-daily",
            "--mode",
            "production",
            "--max-ticks",
            "8",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
