---
name: adl-runtime-ops
description: Operate Agent Delivery Loop inside Hermes as the delivery-supervisor profile: register experts, run supervisor ticks, enqueue notifications, consume Feishu intake events, and execute approved workflow tasks.
---

# ADL Runtime Ops

Use this skill only from the `delivery-supervisor` profile or a trusted operator shell.

## Status

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py status
```

## Register Experts

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py register-default-experts --overwrite
```

This registers:

- `mind-palace`
- `ops-auditor`
- `home-media`
- `lark-operator`
- `framework-maintainer`

## Framework Governance

Framework-level model, profile, skill, workflow, cron, gateway, or ADL config changes should be delegated to `framework-maintainer`.

Path ownership guard. Use it for cron/workflow execution and for manual sessions before file writes:

```bash
python3 /opt/data/profiles/framework-maintainer/scripts/path_governance_check.py \
  --actor-profile <profile> \
  --changed-path <absolute-path> \
  --check-mode planned \
  --session-id <session-or-goal-id>
```

Use `framework-maintainer` as the actor for approved framework capability changes. Other actors should not write owned paths directly; they should delegate the write request to the owning profile shown by the path governance result.

After manual writes, rerun the guard with `--check-mode observed` for the actual changed paths before accepting the task.

## Registry Health

Daily registry health replays known expert registration and reports drift. It does not auto-register unknown profiles.

Manual script:

```bash
python3 /opt/data/profiles/delivery-supervisor/scripts/adl_registry_health.py
```

Workflow:

```bash
/opt/hermes/.venv/bin/python /opt/data/scripts/workflow_runtime.py run \
  --workflow adl-registry-health \
  --trigger manual:adl-registry-health \
  --mode production \
  --max-ticks 8
```

## Supervisor Tick

Manual tick:

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py supervisor-tick
```

Cron wrapper:

```bash
python3 /opt/data/profiles/delivery-supervisor/scripts/adl_supervisor_tick_cron.py
```

## Feishu Keyword Intake

The listener consumes `im.message.receive_v1` and routes messages starting with:

- `#loop`
- `#wiki`
- `#ops`
- `#model`
- `#media`
- `#home`
- `#mteam`
- `#adl`

Smoke without waiting for real messages:

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_feishu_intake_listener.py \
  --profile delivery-supervisor \
  --timeout 3s \
  --max-events 0 \
  --dry-run
```

Production listener command:

```bash
python3 /opt/data/profiles/delivery-supervisor/scripts/adl_feishu_intake_listener_poll.py
```

The production path is cron polling, not an unbounded daemon. The poller runs every five minutes and listens for 90 seconds, which stays below the Hermes cron script timeout.

## Notifications

Default notification target config:

```text
/opt/data/agent-delivery-loop/config/notification-targets.json
```

When a target has `thread_per_goal: true`, the first notification for a goal creates a root message in the configured chat, and later notifications for the same goal are sent as `--reply-in-thread` replies to that root message.

Create a notification payload:

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py notify-enqueue \
  --goal-id <goal-id> \
  --message-type status_report \
  --content "<short status>"
```

Dry-run send:

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py notify-send-outbox \
  --profile delivery-supervisor \
  --dry-run \
  --limit 1
```

Real send:

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py notify-send-outbox \
  --profile delivery-supervisor \
  --limit 1
```

## Workflow Task Adapter

Only run workflow tasks after the task is approved and does not request high-risk permissions.

Preferred order for governed paths:

1. Run path governance during task proposal before creating the task.
2. If the selected profile does not own the planned paths, reroute the task to the owning profile before creating it.
3. Keep the accepted `spec.path_governance` on the task.
4. Let `run-workflow-task` repeat the preflight as the last guard before execution.

If a task may write governed paths, include `spec.path_governance` before task creation:

```json
{
  "path_governance": {
    "actor_profile": "framework-maintainer",
    "planned_paths": [
      "/opt/data/workflows/specs/example.workflow.yaml"
    ],
    "strict_unowned": false
  }
}
```

The workflow adapter repeats a planned path-governance preflight before launching the workflow. If the preflight fails, the workflow is not executed.

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py run-workflow-task \
  --task-id <task-id> \
  --workflow <workflow-name> \
  --mode production \
  --max-ticks 8 \
  --actor-profile framework-maintainer \
  --changed-path /opt/data/workflows/specs/example.workflow.yaml
```

The adapter writes workflow evidence under:

```text
/opt/data/agent-delivery-loop/evidence/<task-id>/
```
