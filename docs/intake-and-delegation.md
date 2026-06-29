# Intake And Delegation

Agent Delivery Loop is for long-running supervised delivery, not every prompt.

Requester-side tools should accept simple natural language, but they must pass through an intake gate before creating a loop.

```text
raw request
  -> IntakeAssessment
  -> normal prompt | clarify | confirm delegation | create loop | reject
```

## LIFT Rule

A request is a loop candidate when it satisfies at least two LIFT dimensions:

- Long-running: multi-step, multi-turn, recurring, or time-spanning work.
- Interdependent: requires multiple experts, profiles, workflows, scripts, systems, or handoffs.
- Feedback-driven: requires review, acceptance, rework, approval, or follow-up decisions.
- Traceable: requires durable state, evidence, progress, reports, or auditability.

Requests that satisfy fewer than two dimensions stay in the normal prompt path.

## Minimum Fields

A loop candidate also needs enough information to be supervised:

- objective: what outcome should be delivered;
- scope: what target, domain, repo, wiki, or system is in scope;
- success criteria: how the supervisor can decide the work is complete;
- constraints: what must not happen or what remains read-only;
- budget or deadline: time, priority, or budget boundary.

If LIFT passes but minimum fields are missing, the result is `needs_clarification`, not a Goal.

## Classifications

- `simple_prompt`: handle as a normal prompt.
- `needs_clarification`: ask targeted questions before creating a loop.
- `draft_delegation`: enough to draft, but confirmation is still useful.
- `loop_candidate`: safe to create Demand and Goal.
- `rejected_for_loop`: not appropriate for ADL.

## Requester Skill Shape

A Duoduo, Codex, or Feishu entrypoint should expose a light requester skill such as:

```text
delegate_task(
  request="整理 Mind Palace wiki，先巡检再输出修复计划，不要直接写回，今天完成。",
  preferred_expert="mind-palace",
  source="feishu_dm"
)
```

The skill should create an `IntakeAssessment` first. It should only create a Demand and Goal when the assessment is `loop_candidate`.

## CLI

```bash
python scripts/adl.py intake "查一下今天的天气"
python scripts/adl.py intake "整理 Mind Palace wiki，先巡检再输出修复计划，不要直接写回，今天完成。" --preferred-expert mind-palace --workspace /tmp/adl --promote
```

The first command returns `simple_prompt`. The second can save an `IntakeAssessment` and promote it to Demand and Goal.
