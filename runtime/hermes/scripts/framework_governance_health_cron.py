#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    completed = subprocess.run(
        ["python3", "/opt/data/profiles/framework-maintainer/scripts/framework_governance_health.py"],
        text=True,
        capture_output=False,
        timeout=120,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
