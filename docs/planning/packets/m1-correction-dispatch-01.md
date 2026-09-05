# M1 Architect-Disposition Correction Dispatch — Candidate 01

**Slice ID:** `MB-SLICE-M1-CORRECTION-DISPATCH-01`
**Status:** `Pending Implementation` (frozen at `4b6e5e2e9f0d2166e8c8298be37e9d9aa02f0bf8`, approved with zero findings and zero corrections)
**Base:** `9c78fdbd7ec7668c8dbfeeb13edf573e7be946e6` (`origin/master`)

## Scope, deliberately minimal

Adds exactly one new guarded transition, `record_and_dispatch_correction`,
covering exactly one route: `AwaitingArchitect → Leased`, for a packet
whose blocking `RequestChanges` review carries at least one
`review-finding` dispositioned `CorrectNow` and none dispositioned
`ReturnSlice`. It creates the packet's `TargetedCorrection` attempt
(`attempt_number=2`) and its lease/locks — the identical shape of
operation `MB-SLICE-M1-ASSIGNMENT-CLAIM-01`'s `claim_packet_assignment`
already performs for the `Initial` attempt, mirrored for the second. It
does **not** implement `start_attempt_execution` for the correction attempt
(the existing, unmodified function already handles any `Leased→Running`
transition regardless of attempt number — no new code needed there), does
not implement `ReturnSlice`/`RejectFinding`/`AcceptKnownLimitation`
disposition handling beyond the one guard needed to refuse dispatch when
`ReturnSlice` is present, and does not implement a "return the slice"
counterpart transition (a separate, later concern). Kept to the smallest
unit with its own complete, independently provable acceptance proof.

Controlling authority is the Bootstrap Convergence Policy (specifically its
risk-based finding disposition, which defines the four disposition values
this slice reads), `docs/planning/maestro-master-plan.md`, and M0-D01,
M0-D05, and M0-D12, read from current `origin/master`.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-CORRECTION-DISPATCH-01` |
| `phase` | `PendingImplementation` |
| `current_actor` | `MaestroDeveloper` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:9c78fdbd7ec7668c8dbfeeb13edf573e7be946e6","git:full-planning-review-head:4b6e5e2e9f0d2166e8c8298be37e9d9aa02f0bf8","review:decision-fidelity:approve:no-findings"]` |

## Closed command and route

```text
record_and_dispatch_correction(
  packet_id, expected_packet_version, review_id, lease_request,
  lock_requests, attempt_request, reason_payload, idempotency_key,
  actor, now
) -> {"packet": <five-key state>, "lease": <five-key state>,
      "locks": [<five-key state>], "attempt": <five-key state>,
      "claim": <claim payload>}
```

| From | To |
|---|---|
| `AwaitingArchitect` | `Leased` |

Every other packet state raises `InvalidTransition`. `lease_request`,
`lock_requests`, and `attempt_request` are validated by the existing,
unmodified `_assignment_lease_request`, `_assignment_lock_requests`, and
`_assignment_attempt_request` helpers — the same input shapes
`claim_packet_assignment` already accepts; this slice adds no new input
shape.

## Guards, before the route is taken

1. Packet exists and `version == expected_packet_version`, else `StaleState`.
2. Packet state is `AwaitingArchitect`, else `InvalidTransition`.
3. `packet.correction_count == 0`, else `InvalidRecord` (the one normal
   correction is already used).
4. `review_id` names a `reviews` row with `packet_id` equal to this
   packet, `review_kind == "IndependentImplementation"`,
   `result == "RequestChanges"`, `correction_number == 0`. A missing or
   mismatched review is `InvalidRecord`.
5. That review's `findings_json` contains at least one item whose
   `disposition.reason_code == "CorrectNow"`, and no item whose
   `disposition.reason_code == "ReturnSlice"`. Neither condition holding is
   `InvalidRecord`.
6. The packet's run has `state == "Running"`, else `InvalidTransition`
   (identical to `claim_packet_assignment`'s own run guard).
7. `lock_requests`' resource keys exactly equal the packet's
   `resource_claims_json`, in the same order, else `InvalidRecord`
   (identical to `claim_packet_assignment`).
8. None of `lease_request.lease_id`, the `idempotency_key` as `claim_key`,
   any `lock_requests[].lock_id`, or `attempt_request.attempt_id` already
   exists, else `InvalidRecord` (identical duplicate-ID checks to
   `claim_packet_assignment`).
9. The packet has no existing `attempt_number=2` row, else `InvalidRecord`
   ("packet already has a TargetedCorrection attempt" — the direct analog
   of `claim_packet_assignment`'s "packet already has an Initial attempt").
10. The packet has no existing `Active` lease and the requested
    `worktree_path` has no existing `Active` lease, else `ResourceConflict`
    (identical to `claim_packet_assignment`).
11. No requested resource key has an existing `Active` lock, else
    `ResourceConflict` (identical to `claim_packet_assignment`).

Any guard failure raises the stated error before any write occurs.

## Exact canonical fingerprint input

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_dispatch_correction","payload":{"attempt":{"attempt_id":"...","model_identity":"...","runtime_identity":"..."},"expected_packet_version":8,"lease":{"executor_route":"...","expires_at":"...","holder_id":"...","lease_id":"...","worktree_path":"..."},"locks":[{"lock_id":"...","lock_kind":"...","resource_key":"..."}],"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."},"review_id":"..."}}
```

Literal keys, nesting, `"operation"` value, and canonical UTF-8 JSON key
ordering are part of the contract — this is `claim_packet_assignment`'s
own `facts` shape with `review_id` added as one more top-level key. `now`
supplies only the attempt/lease `created_at`/`acquired_at`/`heartbeat_at`
timestamps; no other clock value is read. Replay: a repeated
`idempotency_key` with a matching recomputed fingerprint returns the
identical stored result without re-executing guards; a changed fact under
the same key raises `IdempotencyConflict`.

## Transaction precedence, rollback, concurrency, restart

One `BEGIN IMMEDIATE` transaction, in this exact order: (1) idempotency
replay/conflict check; (2) packet existence, version, and route check; (3)
correction-count guard; (4) review lookup and disposition guards; (5) run
state guard; (6) resource-claim match guard; (7) duplicate-ID guards; (8)
active-lease/worktree conflict guard; (9) active-lock conflict guard; (10)
`packets` row update (`state='Leased'`, `correction_count=1`; every other
column, including `current_head`, is untouched); (11) `leases` row insert;
(12) `resource_locks` row inserts; (13) `attempts` row insert; (14) event
insert; (15) commit — the identical write order `claim_packet_assignment`
uses (packet update via a conditional `UPDATE ... WHERE state=...` guarding
the race, then lease, then locks, then attempt, then event). A write-step
failure rolls back the entire transaction. Exactly one concurrent caller
wins the write lock under contention; the loser retries or surfaces
`ResourceBusy` or `ResourceConflict` per the specific guard that fails.
After a crash or restart, re-invoking the identical command with the same
`idempotency_key` reconstructs the same stored result via replay.

Errors: `InvalidRecord` for malformed/missing/mismatched facts or a
guard-3/4/5/7/8/9 failure; `StaleState` for a packet-version mismatch;
`InvalidTransition` for a non-`AwaitingArchitect` source state or a
non-`Running` run; `ResourceConflict` for an active lease/worktree/lock
collision; `IdempotencyConflict` for a reused key with changed facts;
`ResourceBusy` after write-lock contention exhausts the retry policy.

## Exact persisted event envelope

Reuses the existing closed `"PacketClaimed"` event type
(`_insert_packet_claim_event`) — the same event type
`claim_packet_assignment` already emits for the `Initial` claim; this
slice does not invent a new event type or modify the closed event-type
trigger:

```text
entity_type="Packet"
entity_id=<packet_id>
event_type="PacketClaimed"
before_json={"packet": <exact five-key source packet state>}
after_json={"attempt": <exact five-key state>, "claim": <claim payload>, "lease": <exact five-key state>, "locks": [<exact five-key state>], "packet": <exact five-key resulting packet state>}
reason=<the supplied reason payload, kind="reason">
actor=<the supplied actor object>
```

## Boundary, proof, and M0-D12

Writable paths are exactly `services/maestro/maestro/operational_state.py`
and `tests/m1_02/test_correction_dispatch.py` (new file). No other file
changes. `_assignment_lease_request`, `_assignment_lock_requests`,
`_assignment_attempt_request`, `_attempt`, `_insert_packet_claim_event`,
and `claim_packet_assignment` are read and reused, not modified.

The eleven named tests, in `tests/m1_02/test_correction_dispatch.py`
following the repository's `test_NN_<description>` convention:

1. `test_01_awaitingarchitect_with_correctnow_finding_transitions_to_leased`
   — a valid dispatch creates the lease, locks, `TargetedCorrection`
   attempt, sets `correction_count=1`, and routes to `Leased`.
2. `test_02_every_other_source_state_raises_invalid_transition` — every
   packet state other than `AwaitingArchitect` rejects.
3. `test_03_correction_already_used_rejects` — `correction_count=1` on
   entry rejects regardless of other facts.
4. `test_04_review_lookup_guards_reject` — a missing review, one for a
   different packet, wrong `review_kind`, wrong `result`, and nonzero
   `correction_number` each reject; the exact matching review succeeds.
5. `test_05_disposition_guards_reject` — findings with no `CorrectNow`
   item, and findings containing a `ReturnSlice` item alongside a
   `CorrectNow` item, each reject; a `CorrectNow` item alongside an
   `AcceptKnownLimitation` or `RejectFinding` item succeeds.
6. `test_06_run_not_running_raises_invalid_transition` — a non-`Running`
   run rejects.
7. `test_07_resource_claim_mismatch_rejects` — requested lock resource
   keys not exactly equal to the packet's declared `resource_claims_json`
   rejects.
8. `test_08_duplicate_ids_reject` — an existing `lease_id`, `claim_key`,
   `lock_id`, `attempt_id`, or an existing `attempt_number=2` row each
   reject.
9. `test_09_active_lease_or_worktree_conflict_raises_resource_conflict` —
   an existing `Active` lease on the same packet, and on the same
   worktree, each raise `ResourceConflict`.
10. `test_10_active_resource_lock_conflict_raises_resource_conflict` — an
    existing `Active` lock on a requested resource key raises
    `ResourceConflict`.
11. `test_11_fingerprint_replay_rollback_concurrency_and_restart_reconstruct_exactly`
    — replay/conflict, a forced failure at each write step, one winner
    under concurrency, and exact restart reconstruction.

Run the existing 263 named tests plus these 11 (274 total); run test 11 in
ten fresh processes; run `python -m compileall -q maestro ../../tests/m1_02`
from `services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`;
and run exact candidate hygiene before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** only a packet with a genuine `RequestChanges`
   review carrying an Architect-recorded `CorrectNow` disposition, and no
   `ReturnSlice` disposition, and an unused correction allowance, can be
   dispatched for its one permitted correction attempt.
2. **Operating and threat model:** a trusted local single-writer SQLite
   process; stale, duplicate, and concurrent command submission; process
   crash and restart between steps; the identical resource-contention
   model `claim_packet_assignment` already operates under.
3. **Explicit exclusions:** `ReturnSlice`/`RejectFinding`/
   `AcceptKnownLimitation`-only dispositions producing any transition
   (only `CorrectNow` presence dispatches; the others are read but not
   acted on by this slice), a "return the slice" transition, correction
   attempt #2 onward (M0-D05 permits exactly one), `start_attempt_execution`
   changes (none needed), and any M1-03 or later behavior.
4. **Assurance level:** closed single-route atomic, idempotent persistence
   with exact review/disposition/resource validation, rollback,
   contention, and restart proof — proportionate to, and reusing the exact
   pattern of, the already-accepted `claim_packet_assignment`.
5. **Acceptance proof:** the 11 named tests, the 274-test full inventory,
   the one ten-fresh-process stress group, `compileall`, and exact
   candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above;
   reuse of `claim_packet_assignment`'s existing helpers; only the Python
   standard library otherwise. No new dependency, table, or column.
7. **Proportionality ceiling:** one new function, mirroring an
   already-accepted pattern, and one new test module; no redesign of
   `packets`, `attempts`, `leases`, `resource_locks`, or `reviews`; no
   change to `claim_packet_assignment` or its helpers.
8. **Stop and escalation rule:** if a fact needed to close a guard is
   missing, if a second route proves necessary, or if a reserved
   product/security/data decision surfaces, stop and return to the
   Project Architect rather than widening this contract in place — a
   discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
