# M1 Merge Observation Routing — Candidate 01

**Slice ID:** `MB-SLICE-M1-MERGE-OBSERVATION-01`
**Status:** `Pending Implementation` (frozen at `4f490dbb9ff4b09ad3db1ecec2c65cdce0e57dbd`, approved with zero findings and zero corrections)
**Base:** `1ebafcd4da96d7d563f8b2c671c7150a57510101` (`origin/master`)

## Scope, deliberately minimal

Adds exactly one new guarded transition, `record_and_observe_merge`,
covering exactly one route: `AwaitingOwner → Merged`, requiring a prior
`Accepted` acceptance record (the one `MB-SLICE-M1-ACCEPTANCE-ROUTING-01`
produces). It does not implement the "direct `MergeReady`, null-acceptance,
delegated-policy" bypass path (no project binding currently delegates merge
authority, so that path has no real caller today), does not cross-check
`repository_reference`/`default_branch` against the project's active
binding (deferred — this slice only proves the accepted candidate and the
observed merge commit are the same fact, twice recorded), does not touch
run-level completion, and does not implement `packets.state="Complete"`
(a later, separate post-merge-gate transition). Kept to the smallest unit
with its own complete, independently provable acceptance proof, per this
project's sizing lesson.

Controlling authority is the Bootstrap Convergence Policy,
`docs/planning/maestro-master-plan.md`, and M0-D01, M0-D05, and M0-D12,
read from current `origin/master`.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-MERGE-OBSERVATION-01` |
| `phase` | `MergeReady` |
| `current_actor` | `none` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `1` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:1ebafcd4da96d7d563f8b2c671c7150a57510101","git:full-planning-review-head:4f490dbb9ff4b09ad3db1ecec2c65cdce0e57dbd","review:decision-fidelity:approve:no-findings","git:implementation-head:372d17b01f61425afba000134ad726cac2ab38d0","review:independent-implementation:approve:no-findings","tests:263-of-263-passing:1-pre-existing-unrelated-pyyaml-environment-failure"]` |

## Closed command and route

```text
record_and_observe_merge(
  packet_id, expected_packet_version, merge_observation, reason_payload,
  idempotency_key, actor, now
) -> {"packet": <five-key state>, "merge_observation": <validated row>}
```

| From | To |
|---|---|
| `AwaitingOwner` | `Merged` |

Every other packet state raises `InvalidTransition`.

## Guards, before the route is taken

1. Packet exists and `version == expected_packet_version`, else `StaleState`.
2. Packet state is `AwaitingOwner`, else `InvalidTransition`.
3. `merge_observation.packet_id == packet_id` (the function's own argument)
   and `merge_observation.run_id == packet.run_id`. `_merge_observation`
   alone cannot know the function's `packet_id` argument, so this is
   restated here.
4. `merge_observation.acceptance_id` is non-null and names an
   `acceptance_records` row with `packet_id == packet_id`,
   `subject_type == "Packet"`, `decision == "Accepted"`,
   `sequence_number == 1` — the exact row
   `MB-SLICE-M1-ACCEPTANCE-ROUTING-01`'s `record_and_accept_packet`
   produces. A missing, wrong-packet, or non-`Accepted`/non-sequence-1
   acceptance is `InvalidRecord`.
5. `merge_observation.accepted_head == that acceptance row's exact_head`.
   A mismatch is `InvalidRecord`.

Every other field of `merge_observation` (`repository_reference`,
`default_branch`, `merge_commit`, `source_kind`, `source_reference`,
`performed_by_authority`, `delegation_reference`, `review_coverage_json`)
is validated only by the existing, unmodified `_merge_observation()` row
validator — this slice adds no further cross-check on those fields.
`merge_commit == accepted_head` is explicitly legal (a fast-forward merge
creates no new commit); this slice does not require them to differ.

Any guard failure raises `InvalidRecord` or `StaleState` (version mismatch
only) before any write occurs.

## Exact canonical fingerprint input

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_observe_merge","payload":{"expected_packet_version":8,"merge_observation":<fully validated closed merge_observation row>,"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."}}}
```

Literal keys, nesting, `"operation"` value, and canonical UTF-8 JSON key
ordering (`canonical_json`, sort_keys, no whitespace) are part of the
contract. `now` supplies only the merge-observation row's `observed_at`;
no other clock value is read. Replay: a repeated `idempotency_key` with a
matching recomputed fingerprint returns the identical stored result
without re-executing guards; a changed fact under the same key raises
`IdempotencyConflict`.

## Transaction precedence, rollback, concurrency, restart

One `BEGIN IMMEDIATE` transaction, in this exact order: (1) idempotency
replay/conflict check; (2) packet existence and version; (3) route check
(`state == "AwaitingOwner"`); (4) acceptance-record lookup and
relation/decision/sequence/head-match guards; (5) `merge_observations` row
insert; (6) `packets` row update (state only — every other packet column,
including `current_head` and `correction_count`, is untouched); (7) event
insert; (8) commit. A failure at step 5, 6, or 7 rolls back the entire
transaction. Exactly one concurrent caller wins the write lock under
contention; the loser retries or surfaces `ResourceBusy` after the
existing busy-timeout policy, with no residue. After a crash or restart,
re-invoking the identical command with the same `idempotency_key`
reconstructs the same stored result via replay.

Errors: `InvalidRecord` for malformed/missing/mismatched facts or a
guard-4/5 failure; `StaleState` for a packet-version mismatch;
`InvalidTransition` for any packet state other than `AwaitingOwner`;
`IdempotencyConflict` for a reused key with changed facts; `ResourceBusy`
after write-lock contention exhausts the retry policy.

## Exact persisted event envelope

```text
entity_type="Packet"
entity_id=<packet_id>
event_type="MergeObserved"
before_json={"packet": <exact five-key source packet state>}
after_json={"packet": <exact five-key resulting packet state>, "merge_observation": <exact stored row>}
reason=<the supplied reason payload, kind="reason">
actor=<the supplied actor object>
```

`"MergeObserved"` is the same event type name the existing thin
`record_merge_observation` wrapper already declares — this slice reuses
it, it does not invent a new name.

## Boundary, proof, and M0-D12

Writable paths are exactly `services/maestro/maestro/operational_state.py`
and `tests/m1_02/test_merge_observation_routing.py` (new file). No other
file changes. `_merge_observation()` is not modified.

The seven named tests, in `tests/m1_02/test_merge_observation_routing.py`
following the repository's `test_NN_<description>` convention:

1. `test_01_awaitingowner_valid_observation_transitions_to_merged` — a
   valid observation on an `AwaitingOwner` packet routes to `Merged` and
   records the exact row.
2. `test_02_every_other_source_state_raises_invalid_transition` — every
   packet state other than `AwaitingOwner` rejects.
3. `test_03_version_and_relation_guards_reject` — version mismatch, wrong
   `merge_observation.packet_id`, and wrong `run_id` each reject.
4. `test_04_acceptance_lookup_guards_reject` — a missing acceptance record,
   one for a different packet, `decision != "Accepted"`, and
   `sequence_number == 2` each reject; the exact matching row succeeds.
5. `test_05_accepted_head_mismatch_rejects_fast_forward_is_legal` —
   `accepted_head != acceptance.exact_head` rejects; `merge_commit ==
   accepted_head` (a fast-forward) succeeds.
6. `test_06_fingerprint_replay_is_exact_and_changed_facts_conflict` — a
   repeated call with the same `idempotency_key` and identical facts
   returns the identical stored result; a changed fact under the same key
   raises `IdempotencyConflict`.
7. `test_07_event_rollback_concurrency_and_restart_reconstruct_exactly` —
   a forced failure at each write step leaves no partial row; concurrent
   calls on the same packet have exactly one winner; a simulated restart
   replaying the same command reconstructs the identical row, packet
   state, event, and fingerprint from stored facts alone.

Run the existing 256 named tests plus these 7 (263 total); run test 7 in
ten fresh processes; run `python -m compileall -q maestro ../../tests/m1_02`
from `services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`;
and run exact candidate hygiene (tracked-plus-untracked path enumeration
against the two-path allowlist above, `git diff --cached --check`, and
exact commit-range verification) before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** only a packet with a genuine, matching prior
   `Accepted` acceptance record can move from `AwaitingOwner` to `Merged`,
   and the recorded merge commit is provably tied to the accepted head.
2. **Operating and threat model:** a trusted local single-writer SQLite
   process; stale, duplicate, and concurrent command submission; process
   crash and restart between steps.
3. **Explicit exclusions:** the direct `MergeReady`/null-acceptance
   delegated-policy bypass, repository/binding consistency checks,
   run-level completion, `packets.state="Complete"`, and any M1-03 or
   later behavior.
4. **Assurance level:** closed single-route atomic, idempotent persistence
   with exact acceptance-relation validation, rollback, contention, and
   restart proof — proportionate to an internal trusted-caller primitive.
5. **Acceptance proof:** the 7 named tests, the 263-test full inventory,
   the one ten-fresh-process stress group, `compileall`, and exact
   candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above; only
   the Python standard library and this module's existing helpers. No new
   dependency, table, or column.
7. **Proportionality ceiling:** one new function and one new test module;
   no redesign of `packets`, `acceptance_records`, or `merge_observations`;
   no change to `_merge_observation()`.
8. **Stop and escalation rule:** if a fact needed to close a guard is
   missing, if a second route proves necessary, or if a reserved
   product/security/data decision surfaces, stop and return to the
   Project Architect rather than widening this contract in place — a
   discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
