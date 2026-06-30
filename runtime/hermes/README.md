# Hermes Runtime Helpers

These scripts adapt the framework baseline to the Hermes runtime.

They are intentionally separate from protocol and SDK code.

## Commands

```bash
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py status
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py feishu-ingest "#wiki inspect wiki, produce report, finish today" --requester-id ou_xxx --promote
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py register-default-experts --overwrite
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py supervisor-tick
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py notify-enqueue --goal-id <goal-id> --message-type status_report --content "..." --chat-id oc_xxx
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py notify-send-outbox --profile delivery-supervisor --dry-run
python3 /opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py run-workflow-task --task-id <task-id> --workflow mind-palace-lint
python3 /opt/data/profiles/framework-maintainer/scripts/path_governance_check.py --actor-profile framework-maintainer --changed-path /opt/data/workflows/specs/example.workflow.yaml
```

## Experts

`register-default-experts --overwrite` registers:

- `mind-palace`
- `ops-auditor`
- `home-media`
- `lark-operator`
- `framework-maintainer`
- `model-maintainer`

## Feishu Intake

Production Feishu intake is cron polling:

```bash
python3 /opt/data/profiles/delivery-supervisor/scripts/adl_feishu_intake_listener_poll.py
```

Supported prefixes:

- `#loop`
- `#wiki`
- `#ops`
- `#model`
- `#media`
- `#home`
- `#mteam`
- `#adl`

## Safety

- `feishu-ingest` only creates intake and optional Demand/Goal.
- `supervisor-tick` only reviews submitted attempts.
- `notify-send-outbox` requires a configured lark-cli profile.
- `run-workflow-task` rejects tasks requesting high-risk system permissions.
- Home Media active skills are intentionally limited to `home-media*`; broad restored skills are archived outside the active skill root.
- Framework-level model/profile/skill/workflow/cron changes should pass `path_governance_check.py` as `framework-maintainer`.
