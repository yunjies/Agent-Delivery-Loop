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
- `lark-operator`
- `model-maintainer`

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
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_feishu_intake_listener.py \
  --profile delivery-supervisor
```

## Notifications

Create a notification payload:

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py notify-enqueue \
  --goal-id <goal-id> \
  --message-type status_report \
  --content "<short status>" \
  --chat-id <oc_chat_id>
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

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py run-workflow-task \
  --task-id <task-id> \
  --workflow <workflow-name> \
  --mode production \
  --max-ticks 8
```

The adapter writes workflow evidence under:

```text
/opt/data/agent-delivery-loop/evidence/<task-id>/
```
