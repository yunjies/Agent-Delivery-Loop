# Hermes Integration Plan

This plan describes how Hermes can implement Agent Delivery Loop without changing the protocol into a Hermes-only system.

## Integration Goal

Hermes acts as one runtime that can host:

- requester-side delegation skills for Duoduo, Codex handoff, and Feishu private messages;
- a Delivery Supervisor profile;
- expert profiles;
- workflow experts;
- script experts;
- Feishu/Lark notification adapters.

The Delivery Supervisor remains supervisory. It does not implement business work directly.

## Required Hermes Profiles

### delivery-supervisor

Purpose:
- receive loop-candidate demands after intake;
- maintain Goal and Task state;
- run objective-loop review;
- select experts through the expert registry;
- request approval for high-risk system work;
- send supervision reports and notifications.

Default permissions:
- read Agent Delivery Loop state;
- write supervisory state;
- create Task proposals;
- send notifications to approved channels;
- read Expert registry;
- no business writeback by default.

Denied by default:
- Docs write;
- code write;
- cron mutation;
- workflow mutation;
- profile mutation;
- delete/move/archive;
- unrestricted shell execution.

### Expert profiles

Existing and future Hermes profiles can register as Experts.

Initial candidates:
- `mind-palace`: wiki and knowledge maintenance;
- `ops-auditor`: runtime health and report-only audits;
- `model-maintainer`: model registry and smoke tests;
- `lark-operator`: Feishu operations.

The profile name is not the protocol role. It is an expert implementation behind the Hermes adapter.

## Feishu/Lark Bot Requirement

A dedicated Feishu bot is recommended for the Delivery Supervisor.

Reason:
- supervision notifications should be separate from business-domain bots;
- approval requests and blocked notices need a stable channel;
- notification permission is supervisory, not business execution.

Recommended bot:
- app name: `Delivery Supervisor` or a Chinese equivalent chosen by the user;
- lark-cli profile: `delivery-supervisor`;
- allowed chats:
  - one AgentOps supervision group;
  - optional domain-specific groups, explicitly allowlisted.

Allowed message types:
- status report;
- acceptance result;
- approval request;
- blocked notice;
- budget stop;
- next-step proposal.

Disallowed bot actions:
- create or modify groups;
- read unrelated chat history;
- send business-domain content as if it were the domain expert;
- operate Feishu business data unless a Task explicitly delegates that to a Feishu expert.

Feishu business actions do not require a separate approval by default. They require a Task delegated to a Feishu-capable expert with the right capability and permission declaration. Approval is reserved for high-risk system actions such as cron mutation, workflow mutation, profile or skill mutation, destructive archive/delete/move, unrestricted shell, or privileged writeback.

If the user does not create a new bot, the first pilot can run without Feishu delivery and write reports to filesystem evidence only.

Credential rule:
- the app id and secret must be configured only in the Hermes runtime or lark-cli profile;
- credentials must not be written to Agent Delivery Loop protocol objects, fixtures, docs, tests, or git history;
- framework adapters may create notification payloads, but sending is a runtime responsibility.

## Hermes Runtime Surfaces

Recommended state roots:

```text
/opt/data/agent-delivery-loop/
  intake/
  inbox/
  goals/
  tasks/
  attempts/
  evidence/
  decisions/
  experts/
  events/
  outbox/
```

Recommended NAS mirror:

```text
/mnt/user/Docs/AgentDeliveryLoop/
  goals/
  tasks/
  attempts/
  evidence/
  decisions/
  reports/
```

The first implementation should choose one canonical state source and treat the other as a mirror or evidence archive.

## Workflows

Initial Hermes workflow candidates:

- `delivery-loop-review`: advisory objective-loop review;
- `delivery-loop-route`: expert selection and Task proposal;
- `delivery-loop-report`: supervision report generation;
- `delivery-loop-notify`: approved notification delivery.

A0-A2 should not enable cron or daemons.

## Hermes Skills

Runtime adoption should add small skills so Duoduo and other requester agents do not need to handwrite protocol JSON.

### adl-delegate-task

Purpose:
- accept a raw request from Duoduo, Codex, or Feishu;
- create an IntakeAssessment;
- ask clarification when LIFT or minimum fields fail;
- promote only `loop_candidate` intake to Demand and Goal;
- optionally set `preferred_expert`.

Suggested call shape:

```text
delegate_task(
  request="整理 Mind Palace wiki，先巡检再输出修复计划，不要直接写回，今天完成。",
  preferred_expert="mind-palace",
  source="duoduo"
)
```

### adl-register-expert

Purpose:
- create or update Expert registry entries;
- record capabilities, permissions, invocation adapter, priority, and evidence contract;
- validate that registered Hermes profiles, workflows, or scripts exist before enabling them.

### adl-query-status

Purpose:
- query intake, goal, task, approval, and attempt state;
- support Feishu private-message commands such as `#status <goal_id>`.

### adl-approval

Purpose:
- resolve approval records for system-risk gates;
- keep Feishu business operations outside approval unless the Task itself declares a high-risk system permission.

### adl-supervisor-admin

Purpose:
- run `supervisor-tick`;
- inspect runner output;
- prepare cron binding;
- keep runtime adoption separate from framework code.

## First Pilot

Pilot demand:
- Maintain Mind Palace wiki health.

Pilot flow:

```text
Demand
  -> Goal
  -> Task: run mind-palace-survey-smoke
  -> Task: run mind-palace-lint
  -> LoopDecision: propose or skip mind-palace-index-plan
  -> Requester approval before fix/archive work
```

Pilot boundaries:
- no live Docs writeback;
- no archive/delete/move;
- no cron mutation;
- no workflow mutation;
- notifications only to approved channel if a Delivery Supervisor bot exists.

## Gate Checklist

G0:
- protocol skeleton exists;
- Hermes integration plan approved.

G1:
- create `delivery-supervisor` profile skeleton;
- no active cron;
- no daemon.
- profile details are defined in `examples/integrations/hermes-delivery-supervisor-profile.md`.

G2:
- create expert registry with existing profiles;
- validate routing metadata.

G3:
- configure optional Feishu bot;
- send one notification smoke if bot exists.

G4:
- create `delivery-loop-review` workflow in dry-run/proposal-only mode.

G5:
- run Mind Palace pilot manually.

G6:
- decide whether low-risk recurring supervision reports may go on cron.
