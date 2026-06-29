# v0 Readiness

Agent Delivery Loop v0 is ready as a local framework baseline when the checks below pass.

## Included

- Protocol schemas for Demand, Goal, Task, Attempt, Evidence, Budget, Expert, LoopDecision, and Approval.
- Minimal fixtures.
- Delivery core:
  - object validation;
  - lifecycle transitions;
  - permission checks;
  - budget checks;
  - expert routing;
  - filesystem store;
  - workspace summary and object listing.
- SDKs:
  - Requester SDK;
  - Delivery Supervisor SDK;
  - Expert Adapter SDK.
- Adapters:
  - filesystem;
  - human approval;
  - Hermes profile payload;
  - Hermes workflow payload;
  - Codex thread payload;
  - Claude Code payload.
- CLI:
  - `validate`;
  - `demo`;
  - `init-workspace`;
  - `status`;
  - `list`;
  - `show`.

## Not Included

- No daemon.
- No automatic queue consumer.
- No direct Codex, Claude Code, or Hermes execution.
- No Feishu/Lark notification delivery.
- No production Hermes profile creation.
- No live cron or workflow mutation.

## Verification

Run:

```bash
python scripts/adl.py validate
python -m unittest discover -s tests -v
python scripts/adl.py demo --reset
```

Expected:

- protocol validation succeeds;
- all tests pass;
- demo returns `ok: true`;
- demo creates a workspace with Goal, Task, Attempt, LoopDecision, Expert, and event records.

## Framework Boundary

The framework supervises delivery. It does not execute business work directly.

Execution adapters produce controlled payloads unless explicitly implemented as local filesystem operations.

High-risk permissions remain gated:

- Docs writeback;
- delete, move, archive;
- cron mutation;
- workflow mutation;
- profile mutation;
- unrestricted shell execution;
- unapproved external send.

## Next Stage

The next stage is runtime integration:

- create a Hermes `delivery-supervisor` profile;
- bind an optional supervision Feishu bot;
- register Hermes expert profiles;
- run a Mind Palace dry-run pilot;
- keep writeback and mutation approval-gated.
