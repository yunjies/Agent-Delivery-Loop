---
name: model-maintainer-ops
description: Operate the Hermes model-maintainer profile: inspect model registry, run low-cost model smoke checks, and publish report-only findings.
---

# Model Maintainer Ops

Use this skill only from the `model-maintainer` profile or a trusted operator shell.

This profile is report-only by default. Do not edit model config, provider secrets, workflow specs, profiles, skills, or cron unless an explicit approval gate authorizes it.

## Registry Check

```bash
python3 /opt/data/profiles/model-maintainer/scripts/model_maintainer_registry_check.py
```

Workflow:

```bash
/opt/hermes/.venv/bin/python /opt/data/scripts/workflow_runtime.py run \
  --workflow model-registry-check \
  --trigger manual:model-maintainer \
  --mode production \
  --max-ticks 8
```

## Model Smoke

```bash
python3 /opt/data/profiles/model-maintainer/scripts/model_maintainer_smoke.py
```

Workflow:

```bash
/opt/hermes/.venv/bin/python /opt/data/scripts/workflow_runtime.py run \
  --workflow model-smoke \
  --trigger manual:model-maintainer \
  --mode production \
  --max-ticks 8
```

## Outputs

Reports are written under:

```text
/opt/data/workflows/outputs/model-registry-check/
/opt/data/workflows/outputs/model-smoke/
```

## Notification Target

Model maintainer notifications go to:

```text
oc_ae34ba7aa73f0b988872a4b578e1028e
```
