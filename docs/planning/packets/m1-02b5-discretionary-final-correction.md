# M1-02B5 — Discretionary Final Correction

**Status:** `PendingDependency`; `NotDispatchable`
**Stable ID:** `MAESTRO-M1-02B5-DISCRETIONARY-FINAL-CORRECTION`
**Contract:** [M1-02B canonical contract](../contracts/m1-02b-contract.json),
slice and proof IDs for B5 at the exact reviewed planning head
**Hard dependency:** `MAESTRO-M1-02B4-CLOSED-COMPLETION-CONTROL @
ProjectArchitectAccepted`; release records that exact accepted head as base
**Role chain:** Coordinator -> dedicated Maestro Developer -> Integration ->
fresh Independent Implementation Reviewer -> Project Architect

## Outcome and boundary

Implement targeted correction-gate records, every M0-D17 eligibility test,
Project Architect authorization, atomic correction-number-2 resume with final
attempt/lease/locks, final-attempt transition back to Integration, and the hard
two-correction maximum. Then prove the cumulative B1-B5 contract and review
chain at one exact final B head.

This slice cannot grant an ineligible correction, create a third correction,
restart general review, change architecture/schema/API/product authority,
implement C/M1-03, perform external action, or touch a live project.

## Owned implementation paths

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_final_correction.py
tests/m1_02/test_b_cumulative_contract.py
```

## Closed work and proof

- Implement only B5 APIs/events/relations and reuse the already accepted B3
  lease/lock transaction behavior; do not create an alternate claim path.
- Run `B5-P01..B5-P04` and satisfy `B5-Q1`: isolate every eligibility fact,
  exact PA authority/range/IDs/diff/proportionality evidence, targeted gate
  roles/results, atomic resume seams/contention/replay/reopen, final outcome,
  and every unapproved/new-class/scope/third-correction rejection.
- Cumulative proof runs all B1-B5 tests, every Alpha/M1-01/M1-02 regression,
  compileall, ten fresh B processes, exact path/diff/artifact/sensitive-value
  scans, and exact reviewed-range union through the final head.
- Handoff records exact accepted-B4 base/final head, all proof results,
  corrections/returns/learning, review coverage, context/usage facts, gaps,
  and released locks.

## Dispatch, correction, stop, and acceptance

Resolve and review the exact accepted B4 base before Project Architect release.
Acquire `path:maestro-operational-state` and `path:tests-m1-02` atomically.

One initial attempt is bounded to 120 minutes. The packet itself follows
M0-D05/M0-D17: one normal correction and only one fully eligible final
correction, never a third. Each follow-up is limited to named findings and its
directly affected consistency.

Stop on any failed M0-D17 fact, dependency/base drift, missing or stale gate
evidence, duplicate/partial resume, alternate claim path, new failure class,
changed boundary, outside path/dependency, failed final correction, or exhausted
allowance. Exact-head Project Architect acceptance with complete contiguous
B1-B5 review coverage creates
`MAESTRO-M1-02B-LIFECYCLE-CLAIMS-RECOVERY @ ProjectArchitectAccepted` and opens
only M1-02C.
