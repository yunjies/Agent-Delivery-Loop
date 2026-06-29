# Requester SDK

Helpers for requester-side intake and Demand/Goal creation.

Core helpers:

- `classify_intake`: classify raw natural-language input before creating a loop.
- `promote_intake_to_demand`: convert a `loop_candidate` IntakeAssessment into a Demand.
- `create_demand`: create a Demand directly when the caller already has structured input.
- `create_goal_from_demand`: create a Goal from an accepted Demand.

Use intake for lightweight requester surfaces such as Duoduo skills, Codex handoff prompts, and Feishu private-message commands.

Helpers for creating Demand and Goal payloads.

The Requester SDK does not execute delivery work.
