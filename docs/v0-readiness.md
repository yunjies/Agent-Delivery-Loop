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
  - Delivery Supervisor SDK with task proposal and deterministic attempt review;
  - Expert Adapter SDK.
- Adapters:
  - filesystem;
  - human approval;
  - Hermes profile payload;
  - Hermes workflow payload;
  - Codex thread payload;
  - Claude Code payload.
  - Feishu notification payload.
- CLI:
  - `validate`;
  - `demo`;
  - `init-workspace`;
  - `status`;
  - `list`;
  - `show`;
  - `review-attempt`;
  - `supervisor-tick`.
- Hermes skeleton pilot:
  - Delivery Supervisor profile created in Hermes runtime;
  - ADL runtime workspace created in Hermes runtime;
  - Mind Palace expert registered;
  - dry-run Demand, Goal, Task, Attempt, LoopDecision, and pending Approval recorded.

## Not Included

- No daemon.
- No automatic queue consumer.
- No long-running worker process.
- No direct Codex, Claude Code, or Hermes execution.
- No Feishu/Lark notification delivery.
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
- demo creates a workspace with Goal, Task, Attempt, LoopDecision, Expert, and event records;
- `review-attempt` can append a supervisor acceptance decision for the demo attempt.
- `supervisor-tick` can scan submitted tasks and review unreviewed latest attempts.

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

## Runtime Integration State

Hermes skeleton integration has started:

- Hermes `delivery-supervisor` profile exists;
- Hermes ADL state root exists;
- Mind Palace is registered as the first expert;
- live writeback and mutation are still approval-gated.

Remaining runtime work:

- bind and test an optional supervision Feishu bot;
- bind `supervisor-tick` to cron or another queue driver;
- add live execution adapters only behind explicit approval gates.
