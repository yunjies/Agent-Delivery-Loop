# Permissions And Budget

Agent Delivery Loop separates supervisory permissions from business execution permissions.

## Supervisory Permissions

The Delivery Supervisor may:

- read loop state;
- write supervisory decisions;
- create task proposals;
- request approval;
- send notifications to approved targets;
- mark blocked, complete, aborted, or budget-stopped states.

## Business Execution Permissions

The Delivery Supervisor does not own business execution permissions by default.

High-risk actions require explicit Task permissions and usually Requester approval:

- write documents or wiki;
- modify code;
- mutate cron;
- mutate workflow;
- mutate profiles or skills;
- delete, move, or archive;
- unrestricted shell execution;
- send external messages to unapproved targets.

## Budget

Budgets may be declared at Demand, Goal, and Task levels.

Supported budget dimensions:

- token limit;
- token used estimate;
- max iterations;
- max tasks;
- max attempts;
- max LLM nodes per iteration;
- stop threshold;
- time limit;
- escalation policy.

When remaining budget is below threshold, the Delivery Supervisor must stop and produce a handoff or approval request.

