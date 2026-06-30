#!/usr/bin/env python3
from __future__ import annotations

import subprocess


def main() -> int:
    return subprocess.call(
        [
            "python3",
            "/opt/data/profiles/model-maintainer/scripts/model_maintainer_run_workflow.py",
            "--workflow",
            "model-registry-check",
            "--trigger",
            "cron:model-maintainer-registry-daily",
            "--mode",
            "production",
            "--max-ticks",
            "8",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
