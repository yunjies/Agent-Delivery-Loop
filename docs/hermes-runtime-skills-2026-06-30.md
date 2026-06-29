# Hermes Runtime Skills - 2026-06-30

This note records the first Hermes runtime skill deployment for Agent Delivery Loop.

## Deployed Runtime Bundle

- Framework bundle: `/opt/data/agent-delivery-loop/framework`
- CLI entrypoint: `/opt/data/agent-delivery-loop/framework/scripts/adl.py`
- State root: `/opt/data/agent-delivery-loop`

The framework bundle is deployed from the Git repository with `git archive`.

## Default Profile Skill

Global skill for the active `default` Qian Duoduo profile:

- `/opt/data/.agents/skills/adl-delegate-task/SKILL.md`

Purpose:

- run intake before loop creation;
- keep normal one-shot prompts outside ADL;
- promote only `loop_candidate` requests to Demand and Goal;
- hand off loop ownership to `delivery-supervisor`.

## Delivery Supervisor Skills

Profile-local skills:

- `/opt/data/profiles/delivery-supervisor/skills/adl-supervisor-admin/SKILL.md`
- `/opt/data/profiles/delivery-supervisor/skills/adl-query-status/SKILL.md`
- `/opt/data/profiles/delivery-supervisor/skills/adl-register-expert/SKILL.md`
- `/opt/data/profiles/delivery-supervisor/skills/adl-approval/SKILL.md`

Purpose:

- run deterministic supervisor ticks;
- inspect ADL status;
- maintain expert registry;
- inspect and resolve high-risk system approval records.

## Verified Commands

Release check from inside the Hermes container:

```bash
python3 /opt/data/agent-delivery-loop/framework/scripts/adl.py release-check
```

Result:

- `ok: true`
- protocol validation passed with 11 schemas and 6 fixtures
- 33 tests passed, with 1 intentional recursive release-check skip

Default delegate smoke:

```bash
python3 /opt/data/agent-delivery-loop/framework/scripts/adl.py intake \
  "Inspect Mind Palace wiki, produce a fix plan, do not write back, finish today." \
  --source duoduo_default \
  --requester-kind profile \
  --requester-id default \
  --preferred-expert mind-palace \
  --workspace /opt/data/agent-delivery-loop \
  --promote
```

Result:

- classification: `loop_candidate`
- created `IntakeAssessment`
- created `Demand`
- created `Goal`

Supervisor tick smoke:

```bash
python3 /opt/data/agent-delivery-loop/framework/scripts/adl.py supervisor-tick /opt/data/agent-delivery-loop
```

Result:

- `reviewed`: `[]`
- skipped the existing accepted pilot task
- no business mutation occurred

## Current Boundary

Implemented:

- default profile can delegate ADL-suitable work;
- delivery-supervisor has local skills to operate ADL state;
- framework code is available in the Hermes container;
- runtime commands pass release checks.

Not enabled yet:

- Feishu private-message intake;
- Feishu notification delivery;
- cron binding for `supervisor-tick`;
- live Hermes workflow/profile execution adapters;
- additional expert registry entries beyond `mind-palace`.
