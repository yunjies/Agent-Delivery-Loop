# Concept

Agent Delivery Loop coordinates long-running delivery across multiple execution systems.

Traditional agent prompts are good at one session of work. Agent Delivery Loop adds durable supervision:

```text
Demand -> Goal -> Task -> Attempt -> Evidence -> Review -> Next Decision
```

The Delivery Supervisor represents the Requester during the loop. It does not perform business implementation. It supervises experts, checks evidence, manages permission gates, and stops when budgets or risks require escalation.

## Responsibilities

The Requester:

- states the demand;
- defines success criteria;
- sets budget and risk boundaries;
- approves high-risk work;
- performs final acceptance when required.

The Delivery Supervisor:

- turns a demand into a Goal;
- decomposes the Goal into Tasks;
- selects Experts by capability and routing policy;
- monitors Attempts;
- collects Evidence;
- verifies acceptance criteria;
- creates the next decision;
- requests approval when required.

The Expert:

- executes an assigned Task;
- stays within Task permissions;
- reports Attempt results;
- attaches Evidence;
- does not self-approve final delivery.

