# Delivery Supervisor Model Policy

The Hermes `delivery-supervisor` profile should not run every action through a strong LLM.

Default policy:

- deterministic first;
- use GPT-class reasoning only for semantic judgment, decomposition, clarification, and human-facing explanations;
- keep state mutation, validation, registry checks, and runner ticks as scripts.

## Action Policy

| Action | Execution mode | Recommended model |
| --- | --- | --- |
| `intake_classify` | deterministic script | none |
| `intake_clarify_questions` | LLM reasoning | GPT-class |
| `delegate_task_promote` | deterministic script | none |
| `expert_registry_validate` | deterministic script | none |
| `task_decomposition` | LLM reasoning | GPT-class |
| `expert_routing_simple` | deterministic scoring | none |
| `expert_routing_conflict` | LLM reasoning | GPT-class |
| `supervisor_tick` | deterministic script | none |
| `attempt_review_structured` | deterministic script | none |
| `evidence_semantic_review` | LLM reasoning | GPT-class |
| `rework_prompt_generation` | LLM reasoning | GPT-class |
| `status_query` | deterministic script | none |
| `supervision_report` | LLM summarization | GPT-class or cost-controlled summary model |
| `feishu_notification_send` | deterministic delivery | none |
| `approval_resolution` | deterministic state update | none |

## Hermes Config Shape

The profile can keep a low-cost default model, while individual workflow nodes or skills select GPT-class reasoning when needed.

```yaml
delivery_supervisor:
  default_mode: deterministic
  model_policy:
    default_summary_model: deepseek-v4-flash
    reasoning_model: gpt-class
    deterministic_actions:
      - intake_classify
      - delegate_task_promote
      - expert_registry_validate
      - supervisor_tick
      - attempt_review_structured
      - status_query
      - feishu_notification_send
      - approval_resolution
    gpt_actions:
      - intake_clarify_questions
      - task_decomposition
      - expert_routing_conflict
      - evidence_semantic_review
      - rework_prompt_generation
      - supervision_report
```

## Boundary

The model may explain, classify, decompose, and review. It must not be the authority for privileged actions.

Privileged state changes still require explicit permissions, deterministic state updates, and any required approval gate.
