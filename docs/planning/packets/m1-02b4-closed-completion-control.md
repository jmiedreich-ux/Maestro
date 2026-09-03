# M1-02B4 — Closed Completion Control

**Status:** `PendingDependency`; `NotDispatchable`
**Stable ID:** `MAESTRO-M1-02B4-CLOSED-COMPLETION-CONTROL`
**Contract:** [M1-02B canonical contract](../contracts/m1-02b-contract.json),
slice and proof IDs for B4 at the exact reviewed planning head
**Hard dependency:** `MAESTRO-M1-02B3-CLAIMS-LEASES-RECOVERY @
ProjectArchitectAccepted`; release records that exact accepted head as base
**Role chain:** Coordinator -> dedicated Maestro Developer -> Integration ->
fresh Independent Implementation Reviewer -> Project Architect

## Outcome and boundary

Implement closed completion-manifest/gate/finding persistence, both-order
initial gate aggregation, StandardCorrection number 1, durable return with its
wait, resolution, and complete PacketLearning records. `record_return` writes
packet, wait, and evidence atomically and emits only its one composite return
event; resolution and learning likewise emit one event per command.

This slice does not authorize or execute correction number 2, restart general
review, infer policy from metrics, expose Atlas, implement C/M1-03, perform an
external action, or touch a live project.

## Owned implementation paths

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_completion_control.py
```

## Closed work and proof

- Implement only B4 records/APIs/events/relations. Runtime validation and tests
  consume canonical field and carrier IDs; they do not maintain a second field
  or conditional-rule list.
- Run `B4-P01..B4-P04` and satisfy `B4-Q1`: deterministic manifest reorder,
  two-way coverage, both gate arrival orders/four outcomes, restart/stale/
  duplicate handling, one finding union, exactly one normal correction,
  return/resolution seams, and every learning timing/correction/late/reusable
  conditional case.
- Run all accepted predecessor/regression suites, compileall, ten fresh B4
  processes, and exact path/diff/artifact/sensitive-value scans.
- Handoff records exact accepted-B3 base/head, manifest/gate/correction/return/
  learning evidence, commands/results, context/usage facts, gaps, and locks.

## Dispatch, correction, and stop

Resolve and review the exact accepted B3 base before Project Architect release.
Acquire `path:maestro-operational-state` and `path:tests-m1-02` atomically.

One initial attempt is bounded to 120 minutes, with one M0-D05 normal correction
and only an eligible M0-D17 final correction.

Stop on dependency/base drift, missing immutable gate/evidence facts, a new
failure class, carrier/field/event drift, inferred unknown timing, an outside
path/dependency, or exhausted correction. Acceptance opens only B5 from the
exact accepted B4 head.
