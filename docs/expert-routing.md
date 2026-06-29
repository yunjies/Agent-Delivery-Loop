# Expert Routing

Experts are selected by capability, not only by identity.

An Expert registry records:

- capabilities;
- scope;
- default ownership;
- permissions;
- cost class;
- reliability;
- evidence quality;
- freshness;
- invocation method.

Routing policy should prefer:

1. best scope fit;
2. lowest sufficient permission;
3. strongest evidence quality;
4. lower cost;
5. higher reliability;
6. recently verified availability;
7. default owner for the capability.

When multiple Experts are close matches, the Delivery Supervisor may:

- choose the default owner;
- split execution and review across two Experts;
- request Requester confirmation;
- mark the Task blocked if no safe route exists.

