# Hermes Delivery Supervisor Profile Spec

This is the planned Hermes-side profile for Agent Delivery Loop.

It is a supervisory profile. It does not implement business work.

## Profile

Recommended profile id:

```text
delivery-supervisor
```

Purpose:

- receive approved demands from the Requester;
- create and update local Agent Delivery Loop state;
- route tasks to registered Experts;
- request human approval for high-risk work;
- verify evidence;
- generate status reports;
- send supervision notifications to approved channels.

## Files

Recommended runtime files:

```text
/opt/data/profiles/delivery-supervisor/
  PROFILE_STATUS.md
  SOUL.md
  config.yaml
  skills/
  scripts/
```

Recommended state root:

```text
/opt/data/agent-delivery-loop/
  demands/
  goals/
  tasks/
  attempts/
  approvals/
  decisions/
  experts/
  events/
  evidence/
  outbox/
```

Recommended Docs evidence mirror:

```text
/mnt/user/Docs/AgentDeliveryLoop/
  reports/
  evidence/
```

## Permission Defaults

Allowed:

- read Agent Delivery Loop state;
- write supervisory state;
- create Task proposals;
- create Approval records;
- send supervision notifications to allowlisted channels;
- read Expert registry;
- read evidence paths linked by Tasks.

Denied by default:

- Docs writeback;
- code write;
- cron mutation;
- workflow mutation;
- profile mutation;
- skill mutation;
- delete, move, archive;
- unrestricted shell execution;
- Feishu business data mutation.

## Feishu Bot

Recommended lark-cli profile:

```text
delivery-supervisor
```

The Feishu app secret must be stored only in runtime configuration, not in this repository.

Allowed message types:

- `status_report`
- `acceptance_result`
- `approval_request`
- `blocked_notice`
- `budget_stop`
- `next_step_proposal`

Allowed target:

- one supervision group approved by the Requester.

The bot must not:

- create groups;
- modify group membership;
- read unrelated chat history;
- send business-domain messages as a domain Expert;
- mutate Feishu business records.

## Expert Registry

Initial Hermes Experts:

```yaml
experts:
  - id: mind-palace
    kind: hermes_profile
    capabilities:
      - wiki_survey
      - wiki_lint
      - wiki_index_plan
    invocation:
      adapter: hermes_workflow
      workflows:
        - mind-palace-survey-smoke
        - mind-palace-lint
        - mind-palace-index-plan

  - id: ops-auditor
    kind: hermes_profile
    capabilities:
      - runtime_health_report
      - skill_health_report
    invocation:
      adapter: hermes_workflow
```

## First Pilot

Goal:

```text
Maintain Mind Palace wiki health.
```

Flow:

```text
Demand
  -> Goal
  -> Task: mind-palace-survey-smoke
  -> Task: mind-palace-lint
  -> LoopDecision: propose or skip mind-palace-index-plan
  -> Approval: required before fix/archive/writeback
```

Pilot rules:

- no live Docs writeback;
- no delete/move/archive;
- no cron mutation;
- no workflow mutation;
- optional Feishu supervision notification only;
- all business work is performed by registered Experts, not by `delivery-supervisor`.

## Acceptance

The Hermes profile pilot is accepted when:

- `delivery-supervisor` profile exists;
- Expert registry includes `mind-palace`;
- a filesystem-backed Agent Delivery Loop workspace exists;
- a manual Mind Palace Goal can produce at least one Task and one LoopDecision;
- high-risk permissions create Approval records instead of Tasks;
- optional Feishu notification smoke sends only a supervision message to the approved group.
