# M1 Correction-Pass Review Routing — Candidate 01

**Slice ID:** `MB-SLICE-M1-CORRECTION-REVIEW-ROUTING-01`
**Status:** `Pending Decision Fidelity`
**Base:** `2436aca58ceb1385d0c3214123a9c025dcc91add` (`origin/master`)

## Scope, deliberately minimal

`MB-SLICE-M1-REVIEW-ROUTING-05`'s `record_and_route_review` explicitly and
deliberately excluded `review.correction_number != 0`: "this slice does not
cover a correction-review pass; that is a separate later slice." Once
`MB-SLICE-M1-CORRECTION-DISPATCH-01`'s `record_and_dispatch_correction`
attempt finishes, its review (`correction_number=1`) has no route at all —
`record_and_route_review` and `record_and_accept_packet` both explicitly
reject it. This slice closes exactly that gap: a fresh full milestone
inspection (systematically checking every packet state's inbound and
outbound edges, not just the obvious path) found it, alongside a second,
unrelated dead end (`NeedsReplan` has no exit anywhere), which
`MB-SLICE-M1-NEEDSREPLAN-CLOSURE-01` closes separately.

Adds exactly one new guarded transition, `record_and_route_correction_review`,
mirroring `record_and_route_review`'s exact structure and reusing its
`_validate_review_coverage`, `_REVIEW_REVIEWER_ROLES`, and `_review()` calls
unmodified. It does not implement a second correction (M0-D05 permits
exactly one), does not modify `record_and_route_review` itself, and does
not implement `Assemble`/`Comment` results, matching the original slice's
own exclusions.

Controlling authority is the Bootstrap Convergence Policy,
`docs/planning/maestro-master-plan.md`, and M0-D01, M0-D05, and M0-D12,
read from current `origin/master`.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-CORRECTION-REVIEW-ROUTING-01` |
| `phase` | `PendingDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:2436aca58ceb1385d0c3214123a9c025dcc91add"]` |

## Closed command and routes

```text
record_and_route_correction_review(
  packet_id, expected_packet_version, review, reason_payload,
  idempotency_key, actor, now
) -> {"packet": <five-key state>, "review": <validated review row>}
```

The four routes, and only these four:

| From | Review kind | Result | To |
|---|---|---|---|
| `AwaitingIntegration` | `Integration` | `ValidateOnly` | `AwaitingReview` |
| `AwaitingIntegration` | `Integration` | `NeedsReplan` | `NeedsReplan` |
| `AwaitingReview` | `IndependentImplementation` | `Approve` | `MergeReady` |
| `AwaitingReview` | `IndependentImplementation` | `RequestChanges` | `NeedsReplan` |

Identical to `record_and_route_review`'s own table except the last row:
`RequestChanges` routes to `NeedsReplan`, never `AwaitingArchitect` — the
one correction is already used, so there is nothing left to dispatch
another one for. Every other `(packet.state, review_kind, result)`
combination raises `InvalidTransition`.

## Guards, before any route is taken

1. Packet exists and `version == expected_packet_version`, else `StaleState`.
2. `review_row["correction_number"] == 1`, else `InvalidRecord` — the direct
   inverse of `record_and_route_review`'s own `== 0` requirement; this
   function handles only the correction pass.
3. `packet.correction_count == 1`, else `InvalidRecord` (defensive parity;
   structurally guaranteed by `record_and_dispatch_correction`, but checked
   explicitly rather than assumed).
4. Packet has exactly one attempt with `state='Succeeded'`,
   `attempt_kind='TargetedCorrection'`, `attempt_number=2`, non-null
   `result_commit`; otherwise `InvalidRecord`.
5. `review.base_commit` equals the packet's `attempt_number=1` attempt's
   `result_commit` (the correction range is `I0..I1`, not the packet's
   original `base_commit` — the same `I0..I1` range
   `record_and_dispatch_correction`'s own contract and M0-D05 both use for
   "the correction-only diff"). `review.head_commit` equals the
   `attempt_number=2` attempt's `result_commit`. `head_commit` must differ
   from `base_commit`.
6. `target_state == "MergeReady"` requires `packet.correction_count == 1`
   (trivially true given guard 3, restated for parity with
   `record_and_route_review`'s own approval-route check).
7. Closed coverage validation via the existing, unmodified
   `_validate_review_coverage(review_row, owned_paths)` — identical
   requirements to `record_and_route_review`'s: `ready=true`, no blockers,
   every check `Passed`, `request.review_kind="IndependentImplementation"`,
   resolved/checked-out base and head matching, clean before/after,
   nonempty sorted changed paths, allowed paths matching the packet's
   owned paths.
8. `review.reviewer_role` matches the existing `_REVIEW_REVIEWER_ROLES`
   mapping for `review.review_kind`, unmodified.
9. Reviewer independence: `review.reviewer_instance` differs from the
   `attempt_number=2` attempt's `model_identity`, `runtime_identity`, and
   its lease's `holder_id`.
10. For `IndependentImplementation`: exactly one prior `Integration`
    review with `result='ValidateOnly'`, `correction_number=1`, on the same
    `packet_id` and `head_commit` (the `correction_number=1` filter is the
    one place this guard differs in substance from
    `record_and_route_review`'s own — its prior-`ValidateOnly` lookup has
    no `correction_number` filter because it only ever runs at
    `correction_number=0`); its `reviewer_instance` must differ from this
    review's.
11. Every item of `review.findings_json` is validated by the existing,
    unmodified `_review()` row builder — the same closed `review-finding`
    kind and result/findings complement rule
    `MB-SLICE-M1-REVIEW-ROUTING-05` already established apply here
    unchanged; this slice adds no new finding-shape rule.

Any guard failure raises `InvalidRecord`, or `StaleState` (version
mismatch only), before any write occurs.

## Exact canonical fingerprint input

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_route_correction_review","payload":{"expected_packet_version":8,"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."},"review":<fully validated closed review row>}}
```

Identical shape to `record_and_route_review`'s own fingerprint, with
`"operation"` naming this new function. `now` supplies only the review's
`created_at`. Replay: a repeated `idempotency_key` with a matching
recomputed fingerprint returns the identical stored result; a changed fact
under the same key raises `IdempotencyConflict`.

## Transaction precedence, rollback, concurrency, restart

Identical structure and order to `record_and_route_review`'s own: (1)
idempotency replay/conflict; (2) packet existence/version; (3) route
lookup; (4) `attempt_number=2` and `result_commit` guard, plus the
`attempt_number=1` lookup for `base_commit`; (5) closed coverage
validation; (6) reviewer-role and independence checks; (7)
correction_number=1 prior-review cardinality check; (8) `reviews` row
insert; (9) `packets` row update (state only); (10) event insert; (11)
commit. A failure at step 8, 9, or 10 rolls back the entire transaction.
Exactly one concurrent caller wins under contention. Restart replay
reconstructs the identical result from the same `idempotency_key`.

Errors: `InvalidRecord` for malformed/missing/mismatched facts or a
guard-2/3/4/5/6/7/8/9/10 failure; `StaleState` for a packet-version
mismatch; `InvalidTransition` for a route outside the four listed;
`IdempotencyConflict` for a reused key with changed facts; `ResourceBusy`
after write-lock contention exhausts the retry policy.

## Exact persisted event envelope

Reuses the existing `_insert_review_route_event` helper and its
`"ReviewRecorded"` event type unmodified — the same envelope
`record_and_route_review` already produces:

```text
entity_type="Packet"
entity_id=<packet_id>
event_type="ReviewRecorded"
before_json={"packet": <exact five-key source packet state>}
after_json={"packet": <exact five-key resulting packet state>, "review": <exact stored review row>}
reason=<the supplied reason payload, kind="reason">
actor=<the supplied actor object>
```

## Boundary, proof, and M0-D12

Writable paths are exactly `services/maestro/maestro/operational_state.py`
and `tests/m1_02/test_correction_review_routing.py` (new file). No other
file changes. `record_and_route_review`, `_validate_review_coverage`,
`_REVIEW_REVIEWER_ROLES`, `_review()`, and `_insert_review_route_event`
are read and reused, not modified.

The ten named tests, in `tests/m1_02/test_correction_review_routing.py`
following the repository's `test_NN_<description>` convention:

1. `test_01_each_of_the_four_routes_records_the_exact_result_and_state` —
   each listed route, given valid guards, produces exactly its listed
   packet state and stored review row; `RequestChanges` specifically
   confirmed to land on `NeedsReplan`, not `AwaitingArchitect`.
2. `test_02_every_route_outside_the_closed_table_raises_invalid_transition`
   — every other `(state, review_kind, result)` combination rejects.
3. `test_03_correction_number_zero_is_rejected` — a well-formed
   `correction_number=0` review is rejected by this function (it is
   `record_and_route_review`'s job, not this one's).
4. `test_04_attempt_and_commit_range_guards_reject` — no `Succeeded`
   `TargetedCorrection` attempt, `base_commit` not equal to the
   `attempt_number=1` result_commit, `head_commit` not equal to the
   `attempt_number=2` result_commit, and equal base/head each reject.
5. `test_05_correction_count_guard_rejects` — `packet.correction_count=0`
   rejects even with an otherwise valid `correction_number=1` review.
6. `test_06_closed_coverage_accepts_only_a_complete_matching_ready_result`
   — mismatched/incomplete coverage rejects; the exact matching result
   succeeds.
7. `test_07_reviewer_role_and_independence_relationships_reject_mismatches`
   — wrong role, and each independence relationship collapsing, reject.
8. `test_08_independent_implementation_requires_one_prior_correction_pass_validate_only`
   — the prior-`ValidateOnly` lookup requires `correction_number=1`
   specifically; a `correction_number=0` `ValidateOnly` review on the same
   head does not satisfy it.
9. `test_09_findings_complement_and_closed_kind_are_enforced_unchanged` —
   `Approve` with a finding, and `RequestChanges` with empty findings,
   each reject via the existing, unmodified `_review()` validator.
10. `test_10_fingerprint_replay_rollback_concurrency_and_restart_reconstruct_exactly`
    — replay/conflict, per-step rollback, one winner under concurrency,
    and exact restart reconstruction.

Run the existing 274 named tests plus these 10 (284 total); run test 10 in
ten fresh processes; run `python -m compileall -q maestro ../../tests/m1_02`
from `services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`;
and run exact candidate hygiene before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** the one permitted correction's own review can
   still route the packet to `MergeReady` or (on failure) to `NeedsReplan`
   — closing the previously-dead-ended correction pass — without ever
   re-authorizing a second correction.
2. **Operating and threat model:** identical to
   `MB-SLICE-M1-REVIEW-ROUTING-05`'s own: a trusted local single-writer
   SQLite process; stale, duplicate, concurrent commands; crash/restart.
3. **Explicit exclusions:** a second correction, `Assemble`/`Comment`
   results, any change to `record_and_route_review` or the shared
   validators it reuses, and any M1-03 or later behavior.
4. **Assurance level:** closed four-route atomic, idempotent persistence,
   proportionate to and reusing the already-accepted
   `record_and_route_review` pattern exactly.
5. **Acceptance proof:** the 10 named tests, the 284-test full inventory,
   the one ten-fresh-process stress group, `compileall`, and exact
   candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above;
   reuse of `record_and_route_review`'s existing helpers; only the Python
   standard library otherwise. No new dependency, table, or column.
7. **Proportionality ceiling:** one new function, mirroring an
   already-accepted pattern, and one new test module; no redesign of
   `packets`, `attempts`, or `reviews`; no change to `record_and_route_review`.
8. **Stop and escalation rule:** if a fact needed to close a guard is
   missing, if a route beyond the four listed proves necessary, or if a
   reserved decision surfaces, stop and return to the Project Architect —
   a discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
