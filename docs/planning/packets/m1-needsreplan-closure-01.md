# M1 NeedsReplan Closure — Candidate 01

**Slice ID:** `MB-SLICE-M1-NEEDSREPLAN-CLOSURE-01`
**Status:** `Pending Decision Fidelity`
**Base:** `2436aca58ceb1385d0c3214123a9c025dcc91add` (`origin/master`)

## Scope, deliberately minimal

A fresh full milestone inspection (every packet state's inbound and
outbound edges checked, not just the obvious path) found that
`NeedsReplan` has a real, working way *in* — four different routes reach
it (`finish_attempt_execution`'s `Failed`/`TimedOut`/`Stale` outcomes,
`record_and_route_review`'s `Integration`+`NeedsReplan` route, and, once
`MB-SLICE-M1-CORRECTION-REVIEW-ROUTING-01` merges, its own
`Integration`+`NeedsReplan` and `RequestChanges` routes) — but no way
*out*. A packet that lands there is stuck forever.

This slice adds exactly one small guarded transition,
`record_and_close_needs_replan`, covering exactly one route:
`NeedsReplan → Cancelled`, an explicit Architect-authorized closure. It
does **not** implement an actual replan/retry path (materializing a
successor packet, re-entering the pre-claim eligibility pipeline, or
reusing the same `packet_id` for a new attempt — the schema's
`UNIQUE(packet_id,attempt_number)` constraint makes that a genuinely
bigger, separate design question, not a small fix). Closing to
`Cancelled` is the smallest correct action available today: it gives a
stuck packet a deliberate, recorded end state instead of leaving it
silently stranded, without inventing new schema or a real replanning
capability.

Controlling authority is the Bootstrap Convergence Policy,
`docs/planning/maestro-master-plan.md`, and M0-D01, M0-D05, and M0-D12,
read from current `origin/master`.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-NEEDSREPLAN-CLOSURE-01` |
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

## Closed command and route

```text
record_and_close_needs_replan(
  packet_id, expected_packet_version, reason_payload,
  idempotency_key, actor, now
) -> <five-key packet state>
```

| From | To |
|---|---|
| `NeedsReplan` | `Cancelled` |

Every other packet state raises `InvalidTransition`. This is a new,
standalone function — it does **not** add `NeedsReplan` as a key to the
existing `_PACKET_ELIGIBILITY_TRANSITIONS` dict used by
`transition_packet_eligibility`. That dict is documented and scoped to
pre-claim graph eligibility (`Planned`/`Waiting`/`Blocked`/`Ready`/
`Dispatchable`); `NeedsReplan` is a post-execution/post-review state with
a materially different meaning, and reusing that dict would stretch an
already-accepted function beyond its reviewed scope for a superficial code
saving. This slice instead mirrors `transition_packet_eligibility`'s exact
shape (fingerprint, transaction structure, and its reused
`_insert_packet_state_event`/`"PacketStateChanged"` event) in a new,
independently-scoped function with its own single-entry route table.

## Guards, before the route is taken

1. Packet exists and `version == expected_packet_version`, else `StaleState`.
2. Packet state is `NeedsReplan`, else `InvalidTransition`.
3. `reason_payload` is validated by the existing, unmodified
   `validate_payload` and must have `kind="reason"` — the same generic
   requirement every other guarded transition in this module already
   enforces; this slice adds no new reason-shape rule.

Any guard failure raises `InvalidRecord` or `StaleState` (version mismatch
only) before any write occurs.

## Exact canonical fingerprint input

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_close_needs_replan","payload":{"expected_version":8,"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."}}}
```

Identical key-naming convention to `transition_packet_eligibility`'s own
fingerprint facts (`expected_version`, not `expected_packet_version` —
matching that function's exact parameter name, since this slice mirrors
it directly). Literal keys, nesting, `"operation"` value, and canonical
UTF-8 JSON key ordering are part of the contract. `now` supplies only the
event's `observed_at`/packet `updated_at`; no other clock value is read.
Replay: a repeated `idempotency_key` with a matching recomputed
fingerprint returns the identical stored result; a changed fact under the
same key raises `IdempotencyConflict`.

## Transaction precedence, rollback, concurrency, restart

One `BEGIN IMMEDIATE` transaction, in this exact order — identical to
`transition_packet_eligibility`'s own: (1) idempotency replay/conflict
check; (2) packet existence and version; (3) route check (`state ==
"NeedsReplan"`); (4) `packets` row update (state only — every other
column, including `current_head` and `correction_count`, is untouched);
(5) event insert via the existing, unmodified `_insert_packet_state_event`
helper; (6) commit. A failure at step 4 or 5 rolls back the entire
transaction. Exactly one concurrent caller wins the write lock under
contention. After a crash or restart, re-invoking the identical command
with the same `idempotency_key` reconstructs the same stored result via
replay.

Errors: `InvalidRecord` for malformed/missing facts; `StaleState` for a
packet-version mismatch; `InvalidTransition` for any packet state other
than `NeedsReplan`; `IdempotencyConflict` for a reused key with changed
facts; `ResourceBusy` after write-lock contention exhausts the retry
policy.

## Exact persisted event envelope

Reuses the existing `_insert_packet_state_event` helper and its
`"PacketStateChanged"` event type unmodified — the same envelope
`transition_packet_eligibility` already produces:

```text
entity_type="Packet"
entity_id=<packet_id>
event_type="PacketStateChanged"
before_json={"packet": <exact five-key source packet state>}
after_json={"packet": <exact five-key resulting packet state>}
reason=<the supplied reason payload, kind="reason">
actor=<the supplied actor object>
```

## Boundary, proof, and M0-D12

Writable paths are exactly `services/maestro/maestro/operational_state.py`
and `tests/m1_02/test_needsreplan_closure.py` (new file). No other file
changes. `transition_packet_eligibility`, `_PACKET_ELIGIBILITY_TRANSITIONS`,
and `_insert_packet_state_event` are read and (for the event helper) reused,
not modified.

The six named tests, in `tests/m1_02/test_needsreplan_closure.py`
following the repository's `test_NN_<description>` convention:

1. `test_01_needsreplan_transitions_to_cancelled` — a valid call on a
   `NeedsReplan` packet routes to `Cancelled` and records the exact event.
2. `test_02_every_other_source_state_raises_invalid_transition` — every
   packet state other than `NeedsReplan` rejects.
3. `test_03_version_mismatch_raises_stale_state` — an `expected_version`
   not matching the packet's current version rejects.
4. `test_04_malformed_reason_payload_rejects` — a non-`reason`-kind or
   malformed payload rejects.
5. `test_05_fingerprint_replay_is_exact_and_changed_facts_conflict` — a
   repeated call with the same `idempotency_key` and identical facts
   returns the identical stored result; a changed fact under the same key
   raises `IdempotencyConflict`.
6. `test_06_event_rollback_concurrency_and_restart_reconstruct_exactly` —
   a forced failure at each write step leaves no partial row; concurrent
   calls on the same packet have exactly one winner; a simulated restart
   replaying the same command reconstructs the identical packet state,
   event, and fingerprint from stored facts alone.

Run the existing 274 named tests plus these 6 (280 total); run test 6 in
ten fresh processes; run `python -m compileall -q maestro ../../tests/m1_02`
from `services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`;
and run exact candidate hygiene before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** a packet that reaches `NeedsReplan` gets a
   deliberate, recorded, Architect-authorized end state instead of being
   silently stranded forever.
2. **Operating and threat model:** a trusted local single-writer SQLite
   process; stale, duplicate, and concurrent command submission; process
   crash and restart between steps.
3. **Explicit exclusions:** any actual replan/retry/successor-packet
   capability, any change to `_PACKET_ELIGIBILITY_TRANSITIONS` or
   `transition_packet_eligibility`, run-level completion, and any M1-03 or
   later behavior.
4. **Assurance level:** closed single-route atomic, idempotent persistence
   with exact rollback, contention, and restart proof — proportionate to
   an internal trusted-caller primitive, mirroring
   `transition_packet_eligibility`'s already-accepted shape.
5. **Acceptance proof:** the 6 named tests, the 280-test full inventory,
   the one ten-fresh-process stress group, `compileall`, and exact
   candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above;
   reuse of `_insert_packet_state_event`; only the Python standard library
   otherwise. No new dependency, table, or column.
7. **Proportionality ceiling:** one new function and one new test module;
   no redesign of `packets`; no change to `transition_packet_eligibility`
   or its route table.
8. **Stop and escalation rule:** if an actual replan/retry capability is
   later needed, that is a separate, larger, new slice — not an extension
   of this one. A discovered proof/contract defect against a frozen slice
   terminally returns that slice. One planning correction and one
   implementation correction are the maximum available.
