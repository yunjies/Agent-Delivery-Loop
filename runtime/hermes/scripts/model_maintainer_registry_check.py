#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - Hermes runtime has PyYAML.
    yaml = None


OUT_DIR = Path("/opt/data/workflows/outputs/model-registry-check")
CONFIG_PATHS = [
    Path("/opt/data/config.yaml"),
    *sorted(Path("/opt/data/profiles").glob("*/config.yaml")),
]
WORKFLOW_SPEC_DIR = Path("/opt/data/workflows/specs")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = collect()
    (OUT_DIR / "model-registry-report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "model-registry-report.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(OUT_DIR / "model-registry-report.md"), "warnings": payload["warnings"]}, ensure_ascii=False))
    return 0 if payload["ok"] else 1


def collect() -> dict:
    configs = [_read_config(path) for path in CONFIG_PATHS if path.exists()]
    workflow_refs = _workflow_model_refs()
    analytics = _analytics_models()
    warnings = []
    for item in configs:
        if item.get("error"):
            warnings.append(f"config_read_failed:{item['path']}")
        for provider in item.get("providers", []):
            key_env = provider.get("key_env")
            if key_env and not os.environ.get(key_env):
                warnings.append(f"missing_env:{key_env}:{item['profile']}")
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "configs": configs,
        "workflow_model_refs": workflow_refs,
        "analytics": analytics,
        "warnings": sorted(set(warnings)),
    }


def _read_config(path: Path) -> dict:
    profile = "default" if path == Path("/opt/data/config.yaml") else path.parent.name
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) if yaml else {}
    except Exception as exc:
        return {"path": str(path), "profile": profile, "error": str(exc)}
    model = data.get("model") or {}
    providers = []
    for provider_id, provider in (data.get("providers") or {}).items():
        providers.append(
            {
                "id": provider_id,
                "default_model": provider.get("default_model"),
                "base_url": provider.get("base_url"),
                "key_env": provider.get("key_env"),
                "models": provider.get("models") or [],
                "key_present": bool(os.environ.get(str(provider.get("key_env") or ""))),
            }
        )
    return {
        "path": str(path),
        "profile": profile,
        "default_provider": model.get("provider"),
        "default_model": model.get("default"),
        "openai_runtime": model.get("openai_runtime"),
        "providers": providers,
    }


def _workflow_model_refs() -> list[dict]:
    refs = []
    for path in sorted(WORKFLOW_SPEC_DIR.glob("*.workflow.yaml")):
        text = path.read_text(encoding="utf-8", errors="replace")
        providers = sorted(set(re.findall(r"provider:\s*([A-Za-z0-9_.\-/]+)", text)))
        models = sorted(set(re.findall(r"model:\s*([A-Za-z0-9_.\-/]+)", text)))
        if providers or models:
            refs.append({"workflow": path.name, "providers": providers, "models": models})
    return refs


def _analytics_models() -> dict:
    url = "http://127.0.0.1:9119/api/analytics/models?days=7"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
        return {"ok": True, "url": url, "data": json.loads(body)}
    except Exception as exc:
        return {"ok": False, "url": url, "error": str(exc)}


def render_markdown(payload: dict) -> str:
    lines = [
        "# Model Registry Check",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- warnings: `{len(payload['warnings'])}`",
        "",
        "## Profiles",
    ]
    for item in payload["configs"]:
        lines.append(f"- `{item['profile']}`: provider=`{item.get('default_provider')}` model=`{item.get('default_model')}` openai_runtime=`{item.get('openai_runtime')}`")
        for provider in item.get("providers", []):
            lines.append(f"  - provider `{provider['id']}` default=`{provider.get('default_model')}` models={provider.get('models')} key_env=`{provider.get('key_env')}` key_present=`{provider.get('key_present')}`")
    lines.extend(["", "## Workflow Model References"])
    for ref in payload["workflow_model_refs"]:
        lines.append(f"- `{ref['workflow']}` providers={ref['providers']} models={ref['models']}")
    lines.extend(["", "## Dashboard Analytics"])
    analytics = payload["analytics"]
    lines.append(f"- ok: `{analytics.get('ok')}`")
    if analytics.get("error"):
        lines.append(f"- error: `{analytics['error']}`")
    lines.extend(["", "## Warnings"])
    if payload["warnings"]:
        lines.extend(f"- `{warning}`" for warning in payload["warnings"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
