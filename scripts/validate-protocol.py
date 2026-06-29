#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    schema_paths = sorted((ROOT / "protocol" / "schemas").glob("*.json"))
    fixture_paths = sorted((ROOT / "protocol" / "fixtures").glob("*.json"))
    for path in [*schema_paths, *fixture_paths]:
        json.loads(path.read_text(encoding="utf-8"))
    print(f"protocol json ok: schemas={len(schema_paths)} fixtures={len(fixture_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
