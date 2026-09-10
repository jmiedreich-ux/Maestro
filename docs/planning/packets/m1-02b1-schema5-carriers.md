# M1-02B1 — Schema-5 Carriers

**Status:** `PendingDecisionFidelity`; `NotDispatchable`
**Stable ID:** `MAESTRO-M1-02B1-SCHEMA5-CARRIERS`
**Contract:** [M1-02B canonical contract](../contracts/m1-02b-contract.json),
slice and proof IDs for B1 at the exact reviewed planning head
**Implementation base:** exact accepted M1-02A+AR head
`d82164c2f3be2164ad6e66b022f645be5f61844b`
**Role chain:** Coordinator -> dedicated Maestro Developer -> Integration ->
fresh Independent Implementation Reviewer -> Project Architect

## Outcome and boundary

Implement only the additive schema-4-to-5 correction carriers declared by the
canonical contract. Preserve every accepted schema-4 row and object; only the
closed event-type trigger may be replaced. The contract's field registry and
relations are the sole source for columns, carrier validation, enums,
conditional rules, schema inventory, APIs, events, and proof obligations.

This slice does not implement lifecycle transitions, claims, recovery,
completion aggregation, either correction action, C, M1-03, an external call,
or a live-project action.

## Owned implementation paths

```text
services/maestro/maestro/storage.py
services/maestro/maestro/operational_state.py
tests/m1_02/test_schema5_contract.py
```

No other path may change. The contract JSON is immutable implementation input,
not an implementation-owned path.

## Closed work and proof

- Implement only the B1 records, relations, schema objects, enum members, and
  composite event types referenced by B1 in the canonical contract.
- Run `B1-P01..B1-P03` and satisfy `B1-Q1`. Tests derive expected fields,
  conditions, object inventory, API/event declarations, and digests from the
  canonical JSON; they may not reproduce those tables as handwritten fixtures.
- From `services/maestro/`, run all Alpha-01/02/03, M1-01 and M1-02 tests plus
  `python -m compileall -q maestro`. Run the B1 test module in ten fresh
  processes and perform exact path, diff, artifact, and sensitive-value scans.
- Handoff records exact base/head, migration/object evidence, canonical
  crosswalk, commands/results, context/usage facts, gaps, and released locks.

## Dispatch, correction, and stop

Release requires exact contract validation, Decision Fidelity `APPROVE`,
Project Architect release, a clean exact-base worktree, supported environment,
and atomic locks `shared:sqlite-schema`, `file:services-maestro-storage`,
`path:maestro-operational-state`, and `path:tests-m1-02`.

One initial attempt is bounded to 90 minutes. M0-D05 permits one normal
targeted correction; M0-D17 permits one final correction only when every
eligibility fact passes. Follow-up review is limited to named findings.

Stop and return on base drift, any schema-4 change beyond the declared trigger,
field/rule drift from the JSON, a second source of schema truth, an outside
path/dependency, migration data loss, an unexpressible condition, or exhausted
correction. Project Architect acceptance opens only B2 from this exact head.
