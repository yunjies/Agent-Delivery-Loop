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

## Model Governance

Model registry checks and model smoke checks are framework-level operations.
They write local evidence under `/opt/data/workflows/outputs/model-registry-check/` and `/opt/data/workflows/outputs/model-smoke/`.

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/framework_model_registry_check.py
python3 /opt/data/profiles/framework-maintainer/scripts/framework_model_smoke.py
```

Workflows:

```bash
/opt/hermes/.venv/bin/python /opt/data/scripts/workflow_runtime.py run \
  --workflow model-registry-check \
  --trigger manual:framework-maintainer-model-registry \
  --mode production \
  --max-ticks 8

/opt/hermes/.venv/bin/python /opt/data/scripts/workflow_runtime.py run \
  --workflow model-smoke \
  --trigger manual:framework-maintainer-model-smoke \
  --mode production \
  --max-ticks 8
```

## Operation Plan

Use an operation plan before changing model, profile, skill, workflow, cron, gateway, or ADL runtime files.

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/framework_operation_plan.py \
  --operation workflow:update \
  --title "Update media wishlist workflow" \
  --intent "Route media wishlist through the current home-media workflow contract." \
  --target-workflow media-wishlist \
  --session-id <session-or-goal-id> \
  --write-report
```

The plan derives expected paths, runs path governance as `framework-maintainer`, and writes activation checks. Do not make framework changes without a passing plan.

## Governance Health

Run this after framework changes and from scheduled health checks:

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/framework_governance_health.py
```

Workflow:

```bash
/opt/hermes/.venv/bin/python /opt/data/scripts/workflow_runtime.py run \
  --workflow framework-governance-health \
  --trigger manual:framework-governance-health \
  --mode production \
  --max-ticks 8
```

Cron wrapper:

```bash
python3 /opt/data/scripts/framework_governance_health_cron.py
```

Live cron job:

```text
framework-governance-health-daily
35 8 * * *
```

## Path Governance Check

Use this check before or after changing framework-level paths.

Manual session rule:

1. Before writing files, list the planned changed paths and run this check with `--check-mode planned`.
2. If the check identifies another owner, reroute the task to that owner before creating work for the wrong profile.
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

The check exits non-zero when the actor profile does not own a governed path. In ADL routing, the supervisor should use the returned `reroute_profile` instead of continuing with the wrong actor.

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
- Mind Palace wiki content: direct writes are owned by `mind-palace`; other profiles must be rerouted to `mind-palace` before task creation.

Unknown paths are allowed in the first layer. Use `--strict-unowned` when a workflow needs a hard allowlist.

## Manual Write Boundary

For manual Hermes/Codex sessions, this guard is advisory plus procedural. The agent must run it before write tools or shell commands that create, edit, move, or delete governed files.

For framework-level paths, use `framework-maintainer` as the actor profile. For business-owned paths, use the business profile only when the registry explicitly allows it.

If the actual changed path set differs from the planned set, run an observed check before reporting completion.

## Workflow Execution Boundary

For ADL-managed workflow tasks, declare planned writes on the task before execution:

```json
{
  "path_governance": {
    "actor_profile": "framework-maintainer",
    "planned_paths": [
      "/opt/data/profiles/home-media/config.yaml"
    ],
    "strict_unowned": false
  }
}
```

`run-workflow-task` performs this planned check before it launches the workflow. A failed path governance check stops execution because task creation should already have rerouted to the correct owner.
