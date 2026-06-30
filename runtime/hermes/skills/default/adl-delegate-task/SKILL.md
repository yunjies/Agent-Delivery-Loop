---
name: adl-delegate-task
description: Start an Agent Delivery Loop from the default Duoduo profile when a request is long-running, multi-step, needs verification, or should be delegated to registered experts.
---

# ADL Delegate Task

Use this skill when the user asks for durable work that should continue through planning, delegation, execution, verification, and reporting.

Do not use ADL for one-shot chat answers, trivial command output, or requests that do not need follow-up supervision.

## Intake Rule

Before starting a loop, make sure the request has enough LIFT fields:

- Goal: what outcome should be delivered.
- Acceptance: how completion will be verified.
- Scope: target repo, service, workflow, profile, wiki area, or business domain.
- Constraints: deadline, permissions, write boundaries, model/tool preferences, and token budget if any.

If key fields are missing, ask a short clarification instead of starting ADL.

## Start A Loop

Use the Hermes runtime intake command:

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py feishu-ingest \
  "<request text>" \
  --source duoduo_default \
  --requester-kind profile \
  --requester-id default \
  --preferred-expert <expert-id> \
  --promote
```

Known expert ids:

- `mind-palace`: wiki, Obsidian, index, survey, lint.
- `ops-auditor`: runtime health, cron, skill health, system checks.
- `home-media`: home media wishlist, pipeline survey, missing media, and M-Team nurture report tasks.
- `framework-maintainer`: framework-level model, profile, skill, workflow, cron, gateway, path governance, model registry, and model smoke checks.
- `lark-operator`: Feishu message and notification operations.

Omit `--preferred-expert` when routing is unclear.

## Feishu Prefixes

When the task comes from Feishu, these prefixes are routed by the intake poller:

- `#wiki` -> `mind-palace`
- `#ops` -> `ops-auditor`
- `#media`, `#home`, `#mteam` -> `home-media`
- `#model` -> `framework-maintainer`
- `#loop` or `#adl` -> no forced expert

## Check Status

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py status
```

Report the created intake id, demand id, and goal id back to the user.
