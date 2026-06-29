# v0 Completion Audit - 2026-06-29

This audit defines the Agent Delivery Loop v0 completion boundary and the evidence proving that boundary.

## Completion Boundary

v0 is complete as a framework baseline when it can:

- define durable protocol objects for supervised delivery;
- validate protocol objects and fixtures;
- create Demand, Goal, Task, Attempt, Approval, Expert, Evidence, and LoopDecision records;
- classify raw requester input before creating a loop;
- select experts by capability;
- enforce explicit permission and budget gates;
- review expert attempts deterministically;
- produce next-step decisions and rework prompts;
- run a deterministic filesystem supervisor tick over submitted attempts;
- expose the framework through a local CLI;
- provide adapter payloads for target runtimes without embedding credentials;
- prove a Hermes skeleton pilot with Delivery Supervisor and Mind Palace expert state;
- document the v0 boundary and excluded runtime responsibilities.

## Requirement Evidence

| Requirement | Evidence | Status |
| --- | --- | --- |
| Protocol schemas exist for all core objects | `protocol/schemas/*.schema.json`; `python scripts/adl.py validate` | Complete |
| Fixtures validate | `protocol/fixtures/*.json`; `python scripts/adl.py validate` | Complete |
| Core lifecycle, permission, budget, routing, and store helpers exist | `packages/delivery-core/agent_delivery_loop/` | Complete |
| Requester SDK creates Demand and Goal | `packages/requester-sdk/`; `tests/test_sdks.py` | Complete |
| Requester SDK classifies raw intake before loop creation | `classify_intake`; `test_requester_classifies_simple_prompt_outside_loop`; `test_requester_clarifies_loop_candidate_with_missing_fields` | Complete |
| Requester SDK promotes loop candidates to Demand and Goal | `promote_intake_to_demand`; `test_requester_promotes_complete_loop_intake_to_demand` | Complete |
| Supervisor SDK creates Task and LoopDecision | `packages/delivery-supervisor-sdk/`; `tests/test_sdks.py` | Complete |
| Expert SDK creates Attempt records | `packages/expert-adapter-sdk/`; `tests/test_sdks.py` | Complete |
| Human approval flow exists | `adapters/human-approval/`; `tests/test_human_approval_adapter.py` | Complete |
| Filesystem workspace persists loop state | `adapters/filesystem/`; `tests/test_filesystem_adapter.py` | Complete |
| Supervisor attempt review accepts valid evidence | `review_attempt`; `test_delivery_supervisor_accepts_successful_attempt_with_evidence` | Complete |
| Supervisor attempt review rejects missing evidence and creates rework prompt | `review_attempt`; `test_delivery_supervisor_rejects_missing_evidence_and_prompts_rework` | Complete |
| Supervisor attempt review requests human acceptance | `review_attempt`; `test_delivery_supervisor_requests_human_acceptance_when_required` | Complete |
| Supervisor attempt review handles blocked attempts | `review_attempt`; `test_delivery_supervisor_marks_blocked_attempt` | Complete |
| Supervisor attempt review stops on budget threshold | `review_attempt`; `test_delivery_supervisor_stops_review_when_budget_exhausted` | Complete |
| LoopDecision IDs do not collide across reviewed attempts | `test_delivery_supervisor_review_decisions_do_not_collide_between_attempts` | Complete |
| Filesystem supervisor runner consumes submitted attempts once | `supervisor_tick`; `test_supervisor_tick_reviews_submitted_attempt_once` | Complete |
| CLI exposes validation, workspace, review, and tick commands | `packages/delivery-cli/`; `tests/test_cli.py` | Complete |
| Release check exists | `scripts/release-check.py`; `python scripts/adl.py release-check` | Complete |
| Runtime payload adapters do not execute privileged work directly | Hermes, Codex, Claude Code, and Feishu payload adapters; adapter tests | Complete |
| Notification adapter stores no secrets | `tests/test_feishu_notification_adapter.py`; repository secret scan | Complete |
| Hermes skeleton pilot exists | `docs/hermes-runtime-pilot-2026-06-29.md`; runtime profile and ADL workspace evidence | Complete |
| Writeback, cron mutation, and archive actions remain approval-gated | `docs/hermes-runtime-pilot-2026-06-29.md`; pending `docs_writeback` approval | Complete |

## Verification Commands

Run from the repository root:

```bash
python scripts/adl.py validate
python scripts/adl.py release-check
python -m unittest discover -s tests -v
python scripts/adl.py intake "整理 Mind Palace wiki，先巡检再输出修复计划，不要直接写回，今天完成。" --preferred-expert mind-palace
python scripts/adl.py demo --reset
```

Additional smoke checks used for completion:

```bash
python scripts/adl.py review-attempt <workspace> <goal-id> <task-id> <attempt-id>
python scripts/adl.py supervisor-tick <workspace>
```

## Explicit Non-Goals

The following are intentionally outside v0:

- no daemon;
- no long-running worker;
- no automatic queue service;
- no direct execution inside Codex, Claude Code, or Hermes;
- no Feishu/Lark delivery;
- no live cron mutation;
- no live workflow mutation;
- no business-domain implementation by the Delivery Supervisor.

These exclusions preserve the framework boundary: Agent Delivery Loop supervises delivery and produces controlled state, decisions, prompts, and adapter payloads. External runtimes execute work only through explicit adapters and approval gates.

## Audit Result

Agent Delivery Loop v0 is complete as a framework baseline.

The next work is runtime adoption, not framework completion:

- bind `supervisor-tick` to a runtime scheduler if desired;
- configure optional Feishu supervision notification delivery;
- register more experts;
- add live execution adapters behind approval gates.
