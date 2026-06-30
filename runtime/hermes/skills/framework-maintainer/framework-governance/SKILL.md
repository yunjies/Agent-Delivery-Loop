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

Manual session rule:

1. Before writing files, list the planned changed paths and run this check with `--check-mode planned`.
2. If the check fails, stop and route the work to the owning profile or request approval to switch actor profile.
3. After writing files, run the same check on the actually changed paths with `--check-mode observed`.
4. Keep the report as evidence when the task is part of an ADL loop.

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/path_governance_check.py \
  --actor-profile framework-maintainer \
  --changed-path /opt/data/profiles/home-media/config.yaml \
  --changed-path /opt/data/workflows/specs/media-wishlist.workflow.yaml \
  --check-mode planned \
  --session-id <session-or-goal-id> \
  --reason "prepare approved workflow/profile change" \
  --write-report
```

Check another actor:

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/path_governance_check.py \
  --actor-profile home-media \
  --changed-path /opt/data/workflows/specs/media-wishlist.workflow.yaml \
  --check-mode planned
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

## Manual Write Boundary

For manual Hermes/Codex sessions, this guard is advisory plus procedural. The agent must run it before write tools or shell commands that create, edit, move, or delete governed files.

For framework-level paths, use `framework-maintainer` as the actor profile. For business-owned paths, use the business profile only when the registry explicitly allows it.

If the actual changed path set differs from the planned set, run an observed check before reporting completion.
