# M1 Review Control Routing — Final Candidate

**Slice ID:** `MB-SLICE-M1-REVIEW-ROUTING-03`
**Status:** `Pending Decision Fidelity`
**Base:** `eaa524b01cb8527b8cf611850e4dbb2eebc39afb`

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-REVIEW-ROUTING-03` |
| `phase` | `PendingDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:eaa524b01cb8527b8cf611850e4dbb2eebc39afb"]` |

Counts are monotonic. After full planning review, the carrier records
`planning_review_count=1`; after an authorized correction it records
`phase=PendingTargetedDecisionFidelity` and `planning_correction_count=1`;
targeted verification then records its result. A failed targeted verification
records terminal `returned` and no further allowance. The returned slices 01
and 02 are history only and supply no authority.

Controlling authority is the Bootstrap Convergence Policy,
`docs/planning/maestro-master-plan.md`, `docs/planning/agent-workforce-control-plane.md`
§§8.3–8.4, and M0-D01, M0-D05, and M0-D12, read from current `origin/master`.

## Closed command and routes

Implement exactly:

```text
record_and_route_review(
  packet_id, expected_packet_version, review, reason_payload,
  idempotency_key, actor, now
) -> {"packet": <five-key state>, "review": <validated review row>}
```

The four routes are `AwaitingIntegration + Integration + ValidateOnly →
AwaitingReview`, `AwaitingIntegration + Integration + NeedsReplan → NeedsReplan`,
`AwaitingReview + IndependentImplementation + Approve → MergeReady`, and
`AwaitingReview + IndependentImplementation + RequestChanges →
AwaitingArchitect`. Every other combination is `InvalidTransition`.
`RequestChanges` never authorizes correction or replan; a later Project
Architect disposition is required.

The latest attempt must be `Succeeded`, `Initial`, and have non-null
`result_commit`; correction number is 0. Review base equals packet base and
differs from head; review head equals that `attempts.result_commit`. Packet
`current_head` is deliberately excluded because materialization requires null.

`coverage_json` is a closed object with exactly `kind` and `result` keys:
`kind="review-readiness-coverage"`; `result` is the complete unmodified
`maestro.review-readiness.result/v1` object. Validate it with
`review_readiness.validate_result`; require `ready=true`, no blockers, all
checks `Passed`, request `review_kind=IndependentImplementation`, exact
request/resolved base and head, both checked-out heads equal to head, clean
before/after, nonempty sorted changed paths, and request allowlist equal to the
packet owned paths. The result's record digest covers all of these facts.

Integration uses role `IntegrationAgent`; independent review uses
`IndependentImplementationReviewer`. The reviewer instance must differ from
attempt `model_identity`, `runtime_identity`, lease `holder_id`, and (for an
independent review) the prior Integration reviewer instance.

The exact canonical fingerprint input is:

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_route_review","payload":{"expected_packet_version":8,"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."},"review":<fully validated closed review row>}}
```

The literal keys, nesting, operation value, and canonical UTF-8 JSON ordering
are part of the contract; `now` is only the review `created_at` and no hidden
clock is included. Replay occurs before mutable checks and returns the identical
stored result; changed facts raise `IdempotencyConflict`. In one
`BEGIN IMMEDIATE` transaction the order is replay/conflict, packet existence
and version, route, latest attempt/result commit, closed coverage,
independence, prior-review cardinality, review insert, packet update, event
insert, commit. Event/update failure rolls back all writes. One concurrent
winner remains; restart preserves exact replay and reconstruction. Errors are
`InvalidRecord` for malformed/missing/mismatched facts or integrity failure,
`StaleState` for version mismatch, `InvalidTransition` for route/order,
`IdempotencyConflict` for changed-key reuse, and `ResourceBusy` after busy
exhaustion.

## Boundary, proof, and M0-D12

Writable paths are exactly `services/maestro/maestro/operational_state.py` and
`tests/m1_02/test_review_control_routing.py`. The thirteen named tests are:

1. each of the four routes records the exact result/state;
2. every unlisted route rejects;
3. packet/version/attempt/result-commit/base/head/time/correction guards reject;
4. closed readiness coverage accepts only a complete matching result;
5. malformed, failed, stale, dirty, path, and digest coverage rejects;
6. exact reviewer roles and all independence relationships reject mismatches;
7. exactly one prior matching Integration ValidateOnly review is required;
8. missing records, duplicate kinds, and wrong states reject;
9. canonical fingerprint replay is exact and changed facts conflict;
10. review/event/update failures roll back atomically;
11. concurrent commands have one winner and no residue;
12. restart preserves review/event/result and exact replay; and
13. compact result, review row, event, fingerprint, and coverage reconstruct.

Run the existing 235 tests plus these 13 (248 total), tests 10–12 in ten fresh
processes, compileall with external pycache, and exact candidate hygiene.

1. **Protected outcome:** only an exact mechanically ready candidate and an
   independent reviewer can advance review state; Architect controls changes.
2. **Operating/threat model:** trusted local SQLite writer, stale/duplicate/
   concurrent commands, crash, and restart.
3. **Exclusions:** reviewer launch/quality, correction execution, acceptance,
   merge, schema/execution changes, external access, Atlas, and M1-03.
4. **Assurance:** closed four-route atomic/idempotent persistence with exact
   coverage, independence, rollback, contention, and restart proof.
5. **Acceptance proof:** the 13 tests, 248 inventory, stress, compile, hygiene.
6. **Implementation boundary:** exactly the two writable paths and existing
   standard-library/helpers only.
7. **Proportionality ceiling:** one command and one test module; no redesign.
8. **Stop/escalation:** return on a new route/record/dependency/path, reserved
   decision, or unprovable outcome; one planning and one implementation
   correction maximum, with merge only after exact readiness and approval.
