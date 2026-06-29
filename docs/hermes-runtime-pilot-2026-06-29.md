# Hermes Runtime Pilot - 2026-06-29

This note records the first Hermes-side Agent Delivery Loop skeleton rollout.

## Runtime Surfaces

- Delivery Supervisor profile: `/opt/data/profiles/delivery-supervisor`
- ADL state root: `/opt/data/agent-delivery-loop`
- Expert registry: `/opt/data/agent-delivery-loop/experts`
- Initial registered expert: `mind-palace`

## Delivery Supervisor Boundary

The Hermes profile is a supervisory proxy, not a business implementer.

Enabled:
- decompose approved goals into tasks
- route tasks to registered experts
- review evidence
- create loop decisions
- create approval requests
- maintain ADL state

Disabled by default:
- live Docs writeback
- cron mutation
- workflow mutation
- profile mutation
- skill mutation
- secret mutation
- unrestricted shell execution
- Feishu delivery

Feishu delivery remains disabled until a target chat is approved and credentials are configured in the runtime lark-cli profile. Secrets must not be stored in this repository.

## Pilot Evidence

The pilot workspace contains one complete dry-run flow:

- `Demand`: 1
- `Goal`: 1
- `Task`: 1
- `Attempt`: 1
- `LoopDecision`: 1
- `Approval`: 1
- `Expert`: 1
- `Events`: 7

The pilot task was assigned to `mind-palace` and reached `accepted`.

The pilot approval is intentionally still pending:

- approval type: `docs_writeback`
- status: `pending`
- meaning: live Docs mutation remains blocked until explicit user approval

## Acceptance Result

Accepted for skeleton rollout:
- Hermes can see the new Delivery Supervisor profile.
- Hermes can see the ADL workspace.
- The Hermes runtime user can write the workspace.
- The Mind Palace expert registry is present and valid JSON.
- The dry-run flow proves task routing and evidence decision recording.
- The pending approval proves high-risk writeback is gated.

Not enabled yet:
- cron-driven Delivery Supervisor loops
- Feishu notifications
- automatic workflow mutation
- business-domain restoration
