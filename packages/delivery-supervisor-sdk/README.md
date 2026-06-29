# Delivery Supervisor SDK

Helpers for creating Task proposals, reviewing Attempts, and writing LoopDecision records.

The Delivery Supervisor SDK supervises delivery. It does not execute business work.

Core helpers:

- `propose_next_task`: select a registered expert and create a task proposal, or request approval for high-risk permissions.
- `review_attempt`: deterministically inspect an expert attempt and return an updated task plus a supervisor decision.

`review_attempt` can:

- accept successful attempts with required evidence;
- reject missing evidence and produce a rework prompt;
- request human approval when acceptance requires it;
- mark blocked attempts as blocked;
- stop when the goal budget threshold is exhausted.
