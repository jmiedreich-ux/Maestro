# M1 Packet Acceptance Routing — Candidate 01

**Slice ID:** `MB-SLICE-M1-ACCEPTANCE-ROUTING-01`
**Status:** `Pending Implementation` (frozen at `70f6c9ed1940d5ca92782addf76c5dba20e73e0a`, approved with zero findings and zero corrections)
**Base:** `c732eb41fcc6664446358a119f28e4ba8bca7352` (`origin/master`)

## Scope, deliberately minimal

This slice adds exactly one new guarded transition,
`record_and_accept_packet`, covering exactly one route:
`MergeReady → AwaitingOwner`, for exactly the routine first-time,
`Accepted` decision path. It does not implement `Returned`, `ReservedChoice`,
a superseding sequence-2 acceptance, run-level acceptance or completion, or
the subsequent `AwaitingOwner → Merged` transition (a separate slice,
`MB-SLICE-M1-MERGE-OBSERVATION-01`, not yet authored). Per this project's
own sizing lesson (`MB-SLICE-M1-02B-REPLACEMENT-01` failed twice for being
oversized), this slice is deliberately cut to the smallest unit that has its
own complete, independently provable acceptance proof — bundling more paths
in would repeat that mistake, not avoid it.

Controlling authority is the Bootstrap Convergence Policy (which controls
over any older, heavier design — see below), `docs/planning/maestro-master-plan.md`,
and M0-D01, M0-D05, and M0-D12, read from current `origin/master`. A prior,
much larger design for this area exists on the unmerged
`architecture/m1-m4-packets` branch (`MB-SLICE-M1-02B-REPLACEMENT-01`,
terminally returned, non-authoritative) proposing 27 new APIs, a schema-5
migration, and a two-tier M0-D17 correction model; none of it was ever
reviewed or implemented, and its M0-D17 two-tier correction concept is
itself superseded by the Bootstrap Convergence Policy's single-correction
model. This slice takes only its acceptance-sequence design idea (sequence-1
routine decision, terminal for `Accepted`/`Returned`; sequence-2 is a
superseding Owner override) as non-binding reference, re-derived and
independently reviewed fresh against current schema.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-ACCEPTANCE-ROUTING-01` |
| `phase` | `PendingImplementation` |
| `current_actor` | `MaestroDeveloper` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:c732eb41fcc6664446358a119f28e4ba8bca7352","git:full-planning-review-head:70f6c9ed1940d5ca92782addf76c5dba20e73e0a","review:decision-fidelity:approve:no-findings"]` |

## Candidate authority

Unchanged from `record_and_route_review`: the reviewed candidate commit is
`attempts.result_commit` for the packet's `Succeeded`, `Initial` attempt
(`attempt_number=1`, `correction_for_review_id IS NULL`). This slice does
not cover a packet whose accepted candidate came from a `TargetedCorrection`
attempt (`attempt_number=2`) — that is explicitly out of scope, matching
`record_and_route_review`'s own `review.correction_number == 0` restriction,
since no route exists yet for a corrected candidate to reach `MergeReady`.

## Closed command and route

```text
record_and_accept_packet(
  packet_id, expected_packet_version, acceptance, reason_payload,
  idempotency_key, actor, now
) -> {"packet": <five-key state>, "acceptance": <validated acceptance row>}
```

The one route, and only this route, transitions the packet:

| From | To |
|---|---|
| `MergeReady` | `AwaitingOwner` |

Every other packet state raises `InvalidTransition`. The target is
`AwaitingOwner` regardless of `acceptance.required_authority`
(`ProjectArchitect` or `Owner`): accepting a candidate is a distinct act
from performing the actual git merge, which a later, separate
merge-observation slice records. `AwaitingOwner` is simply "accepted,
awaiting whoever holds merge authority for this run" — it does not imply
the Owner personally decided.

This slice does not implement `acceptance.decision` values `Returned` or
`ReservedChoice`, does not implement `sequence_number=2` (a superseding
acceptance), and does not touch `runs.state` or any run-level completion.
Only `record_and_accept_packet` exists; the shared `_acceptance()` row
validator (`operational_state.py`) is not modified, so a future slice
remains free to add `Returned`/`ReservedChoice`/sequence-2 handling without
this slice's guards needing to change.

## Guards, before the route is taken

1. Packet exists and `version == expected_packet_version`, else `StaleState`.
2. Packet has exactly one attempt with `state='Succeeded'`,
   `attempt_kind='Initial'`, `attempt_number=1`, non-null `result_commit`;
   otherwise `InvalidRecord`.
3. `acceptance.subject_type == "Packet"`, `acceptance.packet_id ==
   acceptance.subject_id == packet_id` (the function's own argument, not
   merely internally consistent), and `acceptance.run_id is None` — already
   enforced generically by `_acceptance()`, restated here because this
   guard is what ties the acceptance record to the exact packet argument
   the caller is transitioning, which `_acceptance()` alone cannot know.
4. `acceptance.exact_head == attempt.result_commit`.
5. `acceptance.sequence_number == 1` and `acceptance.supersedes_acceptance_id
   is None`. A `sequence_number=2` or non-null `supersedes_acceptance_id` is
   `InvalidRecord` in this slice — out of scope, not a route.
6. `acceptance.decision == "Accepted"`. `Returned` or `ReservedChoice` is
   `InvalidRecord` in this slice — out of scope, not a route.
7. `acceptance.required_authority` equals the packet's run's
   `acceptance_boundary` (`runs.acceptance_boundary`, looked up by the
   packet's `run_id`) exactly. A mismatch is `InvalidRecord`.
8. `acceptance.review_coverage_json` is a closed object with exactly the
   keys `kind` and `review_id`: `kind="acceptance-review-coverage"`;
   `review_id` names a `reviews` row with `packet_id` equal to this
   packet, `review_kind="IndependentImplementation"`, `result="Approve"`,
   `head_commit` equal to `acceptance.exact_head`, and `correction_number=0`.
   A missing, mismatched, or wrong-result/kind/correction-number review is
   `InvalidRecord`.
9. `acceptance.reason_payload_json` is validated by the existing
   `validate_payload` and must have `kind="reason"` (already enforced by
   `_acceptance()`; restated for completeness of this guard list).

Any guard failure raises `InvalidRecord` or `StaleState` (version mismatch
only) before any write occurs.

## Exact canonical fingerprint input

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_accept_packet","payload":{"acceptance":<fully validated closed acceptance row>,"expected_packet_version":8,"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."}}}
```

Literal keys, nesting, `"operation"` value, and canonical UTF-8 JSON key
ordering (`canonical_json`, sort_keys, no whitespace) are part of the
contract. `now` supplies only the acceptance row's `created_at`; no other
clock value is read. Replay: a repeated `idempotency_key` with a matching
recomputed fingerprint returns the identical stored result without
re-executing guards; a changed fact under the same key raises
`IdempotencyConflict`.

## Transaction precedence, rollback, concurrency, restart

One `BEGIN IMMEDIATE` transaction, in this exact order: (1) idempotency
replay/conflict check; (2) packet existence and version; (3) route check
(`state == "MergeReady"`); (4) latest-attempt and `result_commit` guard;
(5) acceptance relation/sequence/decision/authority-boundary guards; (6)
closed review-coverage validation; (7) `acceptance_records` row insert; (8)
`packets` row update (state only — every other packet column, including
`current_head` and `correction_count`, is untouched); (9) event insert;
(10) commit. A failure at step 7, 8, or 9 rolls back the entire
transaction. Exactly one concurrent caller wins the `BEGIN IMMEDIATE` write
lock under contention; the loser retries or surfaces `ResourceBusy` after
the existing busy-timeout policy, with no residue. After a crash or
restart, re-invoking the identical command with the same `idempotency_key`
reconstructs the same stored result via replay.

Errors: `InvalidRecord` for malformed/missing/mismatched facts or a
guard-7/8 failure; `StaleState` for a packet-version mismatch;
`InvalidTransition` for any packet state other than `MergeReady`;
`IdempotencyConflict` for a reused key with changed facts; `ResourceBusy`
after write-lock contention exhausts the retry policy.

## Exact persisted event envelope

```text
entity_type="Packet"
entity_id=<packet_id>
event_type="AcceptanceRecorded"
before_json={"packet": <exact five-key source packet state>}
after_json={"packet": <exact five-key resulting packet state>, "acceptance": <exact stored acceptance row>}
reason=<the supplied reason payload, kind="reason">
actor=<the supplied actor object>
```

The event's idempotency key, fingerprint, `correlation_id`, and
`causation_event_id` are exactly the command's own facts; no alternate
envelope shape is produced. This is the reconstruction oracle for tests 6
and 8 below.

## Boundary, proof, and M0-D12

Writable paths are exactly `services/maestro/maestro/operational_state.py`
and `tests/m1_02/test_acceptance_routing.py` (new file). No other file
changes — this slice's guards live entirely inside the new function; the
shared `_acceptance()` validator is not modified, so no pre-existing test
is affected.

The eight named tests, in `tests/m1_02/test_acceptance_routing.py`
following the repository's `test_NN_<description>` convention:

1. `test_01_mergeready_accepted_transitions_to_awaiting_owner` — a valid
   `Accepted` acceptance on a `MergeReady` packet routes to `AwaitingOwner`
   and records the exact acceptance row.
2. `test_02_every_other_source_state_raises_invalid_transition` — every
   packet state other than `MergeReady` rejects.
3. `test_03_attempt_and_head_guards_reject` — version mismatch, no
   `Succeeded` initial attempt, and `exact_head != result_commit` each
   reject.
4. `test_04_relation_sequence_and_decision_guards_reject` — wrong
   `subject_type`/`packet_id`/`subject_id` mismatch, non-null `run_id`,
   `sequence_number=2`, non-null `supersedes_acceptance_id`, and
   `decision` in `{"Returned","ReservedChoice"}` each reject.
5. `test_05_required_authority_must_equal_run_acceptance_boundary` — a
   mismatch between `acceptance.required_authority` and the packet's run's
   `acceptance_boundary` rejects; a match with either enum value succeeds.
6. `test_06_closed_review_coverage_accepts_only_the_matching_approve_review`
   — a `review_coverage_json` naming a review with the wrong `packet_id`,
   `review_kind`, `result`, `head_commit`, or nonzero `correction_number`
   each reject; the exact matching `Approve` review succeeds.
7. `test_07_fingerprint_replay_is_exact_and_changed_facts_conflict` — a
   repeated call with the same `idempotency_key` and identical facts
   returns the identical stored result; a changed fact under the same key
   raises `IdempotencyConflict`.
8. `test_08_event_rollback_concurrency_and_restart_reconstruct_exactly` —
   a forced failure at each write step leaves no partial row; concurrent
   calls on the same packet have exactly one winner; a simulated restart
   replaying the same command reconstructs the identical acceptance row,
   packet state, event, and fingerprint from stored facts alone.

Run the existing 248 named tests plus these 8 (256 total); run test 8 in
ten fresh processes; run `python -m compileall -q maestro ../../tests/m1_02`
from `services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`;
and run exact candidate hygiene (tracked-plus-untracked path enumeration
against the two-path allowlist above, `git diff --cached --check`, and
exact commit-range verification) before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** only a packet with a genuine, matching `Approve`
   review and an authority-consistent acceptance record can move from
   `MergeReady` to `AwaitingOwner`.
2. **Operating and threat model:** a trusted local single-writer SQLite
   process; stale, duplicate, and concurrent command submission; process
   crash and restart between steps.
3. **Explicit exclusions:** `Returned`/`ReservedChoice` decisions,
   sequence-2 superseding acceptance, run-level acceptance/completion, the
   subsequent `AwaitingOwner→Merged` transition, a corrected
   (`attempt_number=2`) candidate, any schema or execution-runtime change,
   external/network access, Atlas, and any M1-03 or later behavior.
4. **Assurance level:** closed single-route atomic, idempotent persistence
   with exact relation/authority/coverage validation, rollback,
   contention, and restart proof — proportionate to an internal
   trusted-caller primitive.
5. **Acceptance proof:** the 8 named tests, the 256-test full inventory,
   the one ten-fresh-process stress group, `compileall`, and exact
   candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above; only
   the Python standard library and this module's existing helpers
   (`validate_payload`, `canonical_json`, `canonical_digest`,
   `_fingerprint`, `_closed_mapping`, `_text`, `_commit`). No new
   dependency, table, or column.
7. **Proportionality ceiling:** one new function and one new test module;
   no redesign of `packets`, `attempts`, `reviews`, `acceptance`, or
   `merge_observation`; no change to the shared `_acceptance()` validator.
8. **Stop and escalation rule:** if a fact needed to close a guard is
   missing from the current schema, if a second route proves necessary, or
   if a reserved product/security/data decision surfaces, stop and return
   to the Project Architect rather than widening this contract in place —
   per the Bootstrap Convergence Policy, a discovered proof/contract
   defect against a frozen slice terminally returns that slice. One
   planning correction and one implementation correction are the maximum
   available to this slice.
