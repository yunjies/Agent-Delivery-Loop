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
```

## Safety

- `feishu-ingest` only creates intake and optional Demand/Goal.
- `supervisor-tick` only reviews submitted attempts.
- `notify-send-outbox` requires a configured lark-cli profile.
- `run-workflow-task` rejects tasks requesting high-risk system permissions.
