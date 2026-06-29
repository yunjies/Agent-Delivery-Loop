# Agent Delivery Loop

Agent Delivery Loop is a framework-neutral protocol and runtime pattern for turning user requests into supervised delivery loops across expert agents, workflows, scripts, and humans.

It does not replace execution agents such as Codex, Claude Code, Hermes profiles, OpenClaw agents, workflows, or cron jobs. It coordinates them.

## Core Model

```text
Requester -> Delivery Supervisor -> Experts
```

- `Requester`: the demand owner. Defines goals, success criteria, budgets, and approval gates.
- `Delivery Supervisor`: the requester's supervisory proxy. It decomposes work, routes tasks, manages budgets and gates, verifies evidence, and decides the next supervisory step.
- `Expert`: an execution target such as an agent, profile, workflow, script, cron job, or human.

The Delivery Supervisor does not implement business work. It supervises delivery loops and dispatches implementation work to Experts.

## Key Objects

- `Demand`: the original user request.
- `Goal`: a durable objective derived from a demand.
- `Task`: a bounded unit of work assigned to an Expert.
- `Attempt`: one execution attempt for a Task.
- `Evidence`: artifacts used for acceptance.
- `Budget`: token, time, attempt, and iteration limits.
- `Gate`: permission and approval boundary.
- `Approval`: a human or authorized actor decision for gated work.
- `Expert`: registered capability provider.
- `LoopDecision`: the Delivery Supervisor's next-step decision.

## Repository Layout

```text
docs/                 Concept and user-facing guides
protocol/             Versioned schemas and fixtures
packages/             Core libraries and SDK placeholders
adapters/             Runtime adapter placeholders
examples/             Minimal and integration examples
tests/                Protocol and compatibility tests
```

## v0 Scope

v0 defines the protocol surface only:

- schemas for Demand, Goal, Task, Attempt, Evidence, Budget, Expert, and LoopDecision;
- minimal fixtures;
- repository structure for future SDKs and adapters;
- no daemon;
- no automatic task consumer;
- no live production integration.

## Validate

```bash
python scripts/validate-protocol.py
```

The script uses only the Python standard library and verifies that protocol schemas and fixtures are valid JSON.

Run core tests without external dependencies:

```bash
python -m unittest discover -s tests
```

Run the minimal filesystem loop demo:

```bash
python examples/minimal/run_minimal_loop.py --reset
```

Or use the local CLI:

```bash
python scripts/adl.py validate
python scripts/adl.py demo --reset
python scripts/adl.py init-workspace /tmp/adl-workspace
python scripts/adl.py status /tmp/adl-workspace
python scripts/adl.py list /tmp/adl-workspace Goal
```

## Design Rules

- Execution and supervision are separate.
- Every Task declares permissions.
- Unspecified permissions are denied.
- High-risk actions require Requester approval.
- Every acceptance decision needs Evidence.
- Budgets are first-class constraints.
- Expert routing is capability-based, not identity-based.
- Framework-specific agents are adapter targets, not protocol roles.

## Readiness

See [docs/v0-readiness.md](docs/v0-readiness.md) for the current local framework readiness boundary and verification commands.
