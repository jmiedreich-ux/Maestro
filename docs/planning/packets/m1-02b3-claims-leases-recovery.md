# M1-02B3 — Claims, Leases, and Recovery

**Status:** `PendingDependency`; `NotDispatchable`
**Stable ID:** `MAESTRO-M1-02B3-CLAIMS-LEASES-RECOVERY`
**Contract:** [M1-02B canonical contract](../contracts/m1-02b-contract.json),
slice and proof IDs for B3 at the exact reviewed planning head
**Hard dependency:** `MAESTRO-M1-02B2-GUARDED-LIFECYCLE @
ProjectArchitectAccepted`; release records that exact accepted head as base
**Role chain:** Coordinator -> dedicated Maestro Developer -> Integration ->
fresh Independent Implementation Reviewer -> Project Architect

## Outcome and boundary

Implement atomic packet claim, lease heartbeat/release, sorted resource locks,
failure seams, contention, startup reconciliation, expiry/orphan/conflict
handling, and stale attempt observation exactly as declared by the contract.
Each command has one composite event; startup reconciliation carries its full
ordered result set in one event and performs no external next action.

This slice does not implement completion/correction/return/learning control,
worker execution or redispatch, Git/GitHub, notification delivery, C, M1-03,
machine-reboot proof, network access, or live work.

## Owned implementation paths

```text
services/maestro/maestro/operational_state.py
services/maestro/maestro/recovery.py
tests/m1_02/test_claims_and_recovery.py
```

## Closed work and proof

- Implement only B3 APIs/events and the finite recovery outcomes referenced by
  the canonical contract.
- Run `B3-P01..B3-P03` and satisfy `B3-Q1`: all claim/recovery seams,
  same-packet and shared-resource contention, replay/reopen, unexpired,
  expired, missing-lease, conflict, repeat-startup, stale-observation,
  containment, and no-residue assertions.
- Run all accepted predecessor/regression suites, compileall, ten fresh B3
  processes, and exact path/diff/artifact/sensitive-value scans.
- Handoff records exact accepted-B2 base/head, lease/lock/wait/event snapshots,
  commands/results, context/usage facts, gaps, and released locks.

## Dispatch, correction, and stop

Resolve and review the exact accepted B2 base before Project Architect release.
Acquire `shared:sqlite-schema`, `path:maestro-operational-state`,
`path:maestro-recovery`, and `path:tests-m1-02` atomically.

One initial attempt is bounded to 120 minutes, with one M0-D05 normal correction
and only an eligible M0-D17 final correction.

Stop on dependency/base drift, partial claim/recovery state, duplicate action,
more than one event per command, an outcome outside observe/block/return, an
external or distributed requirement, an outside path/dependency, or exhausted
correction. Acceptance opens only B4 from the exact accepted B3 head.
