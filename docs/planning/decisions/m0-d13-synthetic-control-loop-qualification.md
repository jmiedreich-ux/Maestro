# M0-D13 — Synthetic Control-Loop Qualification Before Foundry V1

- **Status:** Accepted by the Owner on 2026-08-31
- **Scope:** Pre-V1 qualification order and the boundary between synthetic
  Alpha proof, live Foundry V1, and controlled-agent V2

## Context

Maestro's central promise is a governed control loop: derive eligible work from
approved authority, assign the correct role, preserve durable ownership and
evidence, route results through Integration and independent review, apply the
bounded correction rule, and stop at the Owner's acceptance boundary.

Alpha-02 proves a synthetic wrapper only through its review-handoff stop.
Alpha-03 proposes a synthetic project binding and explicitly excludes queues,
scheduling, and dispatch. The prior roadmap therefore made a real Foundry
packet the first whole-loop proving subject while reserving the full agent
workforce for V2.

## Decision

Add **Alpha-04 — Synthetic Control-Loop Qualification** after accepted
Alpha-03 implementation and before any live Foundry V1 execution.

Alpha-04 will use one approved synthetic binding, one fixed synthetic work
graph, and scripted local actor results/observations to qualify the decision and
state-transition logic. It must prove:

1. planned, blocked, ready, and dispatchable work remain distinct;
2. only the highest-ranked eligible packet is selected, with durable reasons
   for skipped candidates;
3. one assignment atomically records its lease, role, resource/path locks,
   base, and attempt identity;
4. worker completion routes through the declared Integration mode and then to
   a different independent reviewer when required;
5. one eligible targeted correction is permitted under M0-D05, while a second
   round or a new failure class escalates;
6. duplicate polls/events, restart, stale completion, contention, and lease
   expiry cannot double-dispatch or overwrite accepted evidence; and
7. an approved synthetic result reaches `AwaitingOwner` and stops without
   merge or successor selection.

All actors are fixture identities and all outcomes are scripted local data.
Alpha-04 performs no real model/agent invocation, repository or GitHub access,
network call, credential use, project registration, deployment, merge, or
automatic next-work selection.

For Alpha-04 only, `maestro run-packet` may consume an approved scripted
sequence containing worker, Integration, and independent-review observations so
the coordinator's later next-action decisions can be qualified. Maestro does
not generate or claim any review judgment. This is a fixture-harness exception
to the earlier Alpha-02/Alpha-03 review-handoff stop, not authority for runtime
review execution or a second command surface.

## Boundary amendment

This decision prospectively narrows the earlier Alpha deferral of
queue/scheduler, Integration, and post-review-handoff transition behavior:
Alpha may implement only the bounded single-run synthetic qualification
described here. It does not authorize a production scheduler, daemon, external
completion listener, real worker route, review execution, multi-project
operation, or parallel execution.

Alpha-03 remains unchanged. Its implementation still requires explicit Owner
release and its own review/acceptance path. Alpha-04 requires a separate
architecture release, Decision Fidelity review, execution packet, Owner
implementation release, and independent implementation review.

## Roadmap consequence

- **Alpha-04:** qualify one fixture-only control loop and its failure/recovery
  branches.
- **V1:** after that qualification, register Foundry and prove one real,
  explicitly released packet through one hosted worker, draft PR, verification,
  independent review, and Owner acceptance. No automatic merge.
- **V2:** add production specialist planned queues, real local-model routing,
  first-class Integration operation, and limited parallel dispatch for
  explicitly independent packets.

## Non-authorization

This accepted decision authorizes planning only. It does not release Alpha-03,
authorize an Alpha-04 build packet, contact Foundry, create operational queue
state, dispatch an agent, or merge code.
