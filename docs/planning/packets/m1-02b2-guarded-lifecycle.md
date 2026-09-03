# M1-02B2 — Guarded Lifecycle

**Status:** `PendingDependency`; `NotDispatchable`
**Stable ID:** `MAESTRO-M1-02B2-GUARDED-LIFECYCLE`
**Contract:** [M1-02B canonical contract](../contracts/m1-02b-contract.json),
slice and proof IDs for B2 at the exact reviewed planning head
**Hard dependency:** `MAESTRO-M1-02B1-SCHEMA5-CARRIERS @
ProjectArchitectAccepted`; release records that exact accepted head as base
**Role chain:** Coordinator -> dedicated Maestro Developer -> Integration ->
fresh Independent Implementation Reviewer -> Project Architect

## Outcome and boundary

Implement the canonical graph, run, packet, attempt, wait, notification,
review, acceptance, and merge lifecycle APIs, their finite transitions and
authority/head/context guards. Every successful first mutation writes exactly
the one composite event named by its API record. Replay returns the original
result; invalid or stale commands write no state or event.

This slice does not implement claims, lease recovery, completion aggregation,
correction/return/learning actions, C, M1-03, delivery, merge execution,
external access, or live work.

## Owned implementation paths

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_lifecycle_transitions.py
tests/m1_02/test_acceptance_and_notifications.py
```

## Closed work and proof

- Implement only B2 APIs/events/transitions and referenced guards. Full
  prohibited complements and terminal states are test-generated from the
  canonical state/edge sets.
- Run `B2-P01..B2-P03` and satisfy `B2-Q1`, including M0-D11 coverage of every
  B2 route, replay-before-stale, rollback seams, exact event cardinality, and
  exact acceptance/ReservedChoice/merge/Run-completion authority behavior.
- Run all accepted predecessor and regression suites, compileall, ten fresh B2
  processes, and exact path/diff/artifact/sensitive-value scans.
- Handoff records exact accepted-B1 base/head, matrix and API/event coverage,
  commands/results, context/usage facts, gaps, and released locks.

## Dispatch, correction, and stop

Before release, resolve the exact accepted B1 head, renew Decision Fidelity for
that resolved base, and obtain Project Architect release. Acquire
`path:maestro-operational-state` and `path:tests-m1-02` atomically.

One initial attempt is bounded to 120 minutes, with M0-D05's normal correction
and only an eligible M0-D17 final correction; no third correction or general
review restart.

Stop on dependency/base drift, any new state/API/event/authority meaning,
multiple events for one command, a path/dependency outside the packet,
unavailable exact-head evidence, or exhausted correction. Acceptance opens
only B3 from the exact accepted B2 head.
