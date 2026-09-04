# M1 Packet Eligibility Transitions — Independent Slice 02

**Slice ID:** `MB-SLICE-M1-PACKET-ELIGIBILITY-02`
**Status:** `Decision Fidelity approved; implementation released`
**Base:** `81280f70b5bf8257d981824b32b47741879b01ce`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-PACKET-ELIGIBILITY-02` |
| `phase` | `Frozen` |
| `current_actor` | `None` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:81280f70b5bf8257d981824b32b47741879b01ce", "git:planning-review:81280f70b5bf8257d981824b32b47741879b01ce..91e4e85a4e7285ffd6377d35facd40a53b93972c", "readiness:167d718e5c0f6ac5ad8aff814bfb5d5d746606542b0ca45a7b1e0434f2dc2b50", "review:M1-PACKET-ELIGIBILITY-02-DFR-01-APPROVE"]` |

The carrier has exactly the canonical v1 keys. Counts never reset.

## Authority and outcome

This new independent slice is derived from current master, the Bootstrap
Convergence Policy, M0-D01, M0-D05, M0-D12, the Master Plan, and Agent
Workforce Control Plane sections 7.1, 7.4, and 8.4. Terminal slices
`MB-SLICE-M1-02B-REPLACEMENT-01` and
`MB-SLICE-M1-PACKET-ELIGIBILITY-01` remain immutable history and are not used
as authority, reopened, corrected, renamed, replaced, or given new allowances.

Implement one internal trusted-caller primitive:

```text
OperationalStateStore.transition_packet_eligibility(
  packet_id, expected_version, target_state, reason_payload,
  idempotency_key, actor, now
) -> state_payload
```

The returned state payload is exactly:

```json
{"entity_id":"...","entity_type":"Packet","kind":"state","state":"...","version":2}
```

The method validates inputs before mutation, opens one `BEGIN IMMEDIATE`
transaction, resolves exact idempotent replay before mutable-state checks,
compares `expected_version`, applies exactly one permitted edge, increments
version once, updates `updated_at`, appends one `PacketStateChanged` event with
exact before/after state and the validated reason, commits, and returns the
after payload.

## Complete graph for this primitive

```text
Planned      -> Waiting | Blocked | Cancelled
Waiting      -> Ready | Blocked | Cancelled
Blocked      -> Waiting | Ready | Cancelled
Ready        -> Waiting | Blocked | Dispatchable | Cancelled
Dispatchable -> Ready | Waiting | Blocked | Cancelled
```

These are the complete seventeen allowed edges. Every other source/target pair
among the sixteen packet states is rejected without mutation. The method may
not enter or leave `Leased`, `Running`, `AwaitingIntegration`,
`AwaitingReview`, `MergeReady`, `AwaitingArchitect`, `AwaitingOwner`,
`Merged`, `Complete`, or `NeedsReplan`; those require later companion claim,
attempt, review, acceptance, merge-observation, or recovery evidence.
`Cancelled` is terminal here.

The caller must already have recomputed dependency, route, source, WIP, and
resource eligibility. The method records a prevalidated choice; it does not
calculate eligibility, select work, lease/lock resources, create an attempt,
infer approval, or dispatch. `actor` is audit identity, not authorization.

Unknown packet raises `InvalidRecord`; stale version raises `StaleState`;
unlisted/self edge raises `InvalidTransition`; conflicting key reuse raises
`IdempotencyConflict`; exhausted SQLite busy raises `ResourceBusy`.

## Replay and reconstruction

The command fingerprint is SHA-256 over UTF-8 canonical JSON for this closed
object:

```json
{
  "actor": {
    "actor_id": "...",
    "actor_type": "...",
    "causation_event_id": null,
    "correlation_id": "..."
  },
  "operation": "transition_packet_eligibility",
  "payload": {
    "expected_version": 1,
    "packet_id": "...",
    "reason": {"detail_reference": null, "kind": "reason", "reason_code": "..."},
    "target_state": "Waiting"
  }
}
```

Existing `canonical_json` rules apply. `now` is observation time and excluded
from the fingerprint. Same-key replay with a later valid `now` returns the
original after payload and retains the original event time. Changing actor,
packet, expected version, target, or reason conflicts. Event-insert failure
rolls back the update; concurrent commands at one version produce one winner;
restart replay adds no version or event. No companion table changes.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_packet_eligibility.py
```

No migration, CLI/API, scheduler, eligibility calculator, claim, lease/lock,
attempt, heartbeat, recovery, completion/review/correction, acceptance/merge,
notification, Git/GitHub, project create/register, Linux service, Atlas,
external access, live project, M1-03, deployment, or merge behavior is in
scope.

## Named sufficient proof

`tests/m1_02/test_packet_eligibility.py` contains exactly fourteen tests:

1. materialization starts Planned/version 1;
2. each forward eligibility edge succeeds;
3. each fallback, block, and cancel edge succeeds;
4. all 256 source/target pairs prove exactly seventeen edges succeed;
5. every companion-evidence lifecycle state is unreachable through this API;
6. stale version fails without mutation;
7. missing packet fails without an event;
8. same-key replay with later `now` is exact and single-event;
9. every immutable command-field change conflicts;
10. independent fingerprint reconstruction and exact event fields match;
11. forced event failure rolls back state and event;
12. simultaneous transitions from one version yield one winner;
13. restart preserves state/version/event and exact replay;
14. successful and rejected calls leave all companion tables unchanged.

Run all existing Alpha-01, Alpha-02, Alpha-03, M1-01, M1-02, and
review-readiness tests plus these fourteen tests: 191 total. Also run ten
fresh lifecycle stress repetitions, compileall, exact-path confinement,
staged/unstaged/untracked hygiene, independent fingerprint reconstruction,
and the mechanical implementation-review readiness gate. Passing this closed
inventory is enough.

## Bounded quality contracts

### Q1 — Exact packet eligibility state

- **Protected outcome:** a packet change cannot skip, invent, duplicate, or
  partially apply an approved eligibility edge.
- **Operating and failure model:** one Linux service writer; stale callers,
  invalid edges, event failure, SQLite contention, duplicates, and two threads.
- **Explicit exclusions:** hostile same-UID tampering, distributed writers,
  eligibility computation, claims, dispatch, and later lifecycle.
- **Assurance level:** closed 16×16 graph, version guard, immediate
  transaction, durable event, and real SQLite tests.
- **Acceptance proof:** named tests 1–7 and 10–12 plus regressions.
- **Implementation boundary:** one method/private helpers; no migration or
  dependency.
- **Proportionality ceiling:** no generic workflow engine or public surface.
- **Stop and escalation:** a companion-row edge, new state, schema change, or
  eligibility decision returns the slice.

### Q2 — Replay, restart, and isolation

- **Protected outcome:** retry, restart, rollback, or contention cannot produce
  contradictory state or mutate companion records.
- **Operating and failure model:** duplicates, conflicting keys, reopen,
  injected event failure, and concurrent writers.
- **Explicit exclusions:** multi-host consensus and automatic recovery action.
- **Assurance level:** durable fingerprint, serialized transaction, exact
  replay, and companion-table snapshots.
- **Acceptance proof:** named tests 8–14 and ten fresh stress runs.
- **Implementation boundary:** existing event/idempotency facilities only.
- **Proportionality ceiling:** one packet row and one event per success.
- **Stop and escalation:** process-memory replay, duplicate event, or companion
  mutation returns the slice.

### Q3 — Authority and scope confinement

- **Protected outcome:** the method cannot claim, dispatch, infer policy, or
  cross a companion-evidence lifecycle boundary.
- **Operating and failure model:** accidental public/caller expansion or entry
  into a reserved state.
- **Explicit exclusions:** later authorized companion-evidence methods.
- **Assurance level:** no caller/public exposure, two-path allowlist, complete
  graph rejection, and regression proof.
- **Acceptance proof:** tests 4, 5, and 14; exact diff; 191 tests; compile; and
  readiness.
- **Implementation boundary:** local SQLite service boundary only.
- **Proportionality ceiling:** no scheduler, evaluator, or new entity.
- **Stop and escalation:** credentials, external action, M1-03, terminal-slice
  dependency, or product-boundary change returns before review.

## Bounded review sequence

One complete Decision Fidelity review may authorize at most one planning
correction and targeted verification. Implementation then receives one
complete independent review and at most one targeted correction/verification.
Mechanical readiness must return `ready: true` before either reviewer launch;
a blocked check consumes no allowance. The Project Architect dispositions
implementation findings under the risk-based policy. No successor begins
until this slice is terminally merged or returned.
