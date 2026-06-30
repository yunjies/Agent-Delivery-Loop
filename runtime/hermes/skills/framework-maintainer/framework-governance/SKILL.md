---
name: framework-governance
description: Govern Hermes framework-level capability changes from the framework-maintainer profile: model, profile, skill, workflow, cron, gateway, and path ownership checks.
---

# Framework Governance

Use this skill only from the `framework-maintainer` profile or a trusted operator shell.

This profile governs Hermes platform capabilities. It is not a business implementation profile.

Governed domains:

- model registry and model routing
- profile creation and profile registration
- skill creation, format, ownership, and exposure
- workflow specs and orchestration
- cron binding
- gateway service boundaries
- ADL framework runtime config

## Path Governance Check

Use this check before or after changing framework-level paths.

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/path_governance_check.py \
  --actor-profile framework-maintainer \
  --changed-path /opt/data/profiles/home-media/config.yaml \
  --changed-path /opt/data/workflows/specs/media-wishlist.workflow.yaml \
  --write-report
```

Check another actor:

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/path_governance_check.py \
  --actor-profile home-media \
  --changed-path /opt/data/workflows/specs/media-wishlist.workflow.yaml
```

The check exits non-zero when a blocked path is owned by another profile.

Reports are written under:

```text
/opt/data/workflows/outputs/path-governance-check/
```

## Rule Registry

Runtime path rules live at:

```text
/opt/data/agent-delivery-loop/config/path-governance.json
```

Default ownership:

- framework-level model/profile/skill/workflow/cron/ADL config: `framework-maintainer`
- Mind Palace wiki content: `mind-palace` warning-level ownership

Unknown paths are allowed in the first layer. Use `--strict-unowned` when a workflow needs a hard allowlist.
