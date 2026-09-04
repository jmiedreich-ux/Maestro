# M1 Packet Eligibility Transitions

**Slice ID:** `MB-SLICE-M1-PACKET-ELIGIBILITY-01`
**Status:** `Pending Decision Fidelity`
**Base:** `bcf93a45fb03aed566b372d55b6e428c17bef39a`

## Authority and outcome

This independent bootstrap slice implements the smallest remaining M1
operational-core behavior after the merged run lifecycle: one internal,
trusted-caller storage primitive for guarded packet eligibility transitions.
Authority is the current master handoffs and status ledger, the Bootstrap
Convergence Policy, M0-D01, M0-D05, M0-D12, the Master Plan, and the Agent
Workforce Control Plane sections 7.1, 7.4, and 8.4.

Terminal `MB-SLICE-M1-02B-REPLACEMENT-01` is neither reopened nor used as
authority. This slice does not replace it and receives its own immutable
identity and allowances.

Add this internal method:

```text
OperationalStateStore.transition_packet_eligibility(
  packet_id, expected_version, target_state, reason_payload,
  idempotency_key, actor, now
) -> state_payload
```

The return is exactly the existing state-payload shape:

```json
{"entity_id":"...","entity_type":"Packet","kind":"state","state":"...","version":2}
```

The method validates all inputs before mutation, opens one `BEGIN IMMEDIATE`
transaction, resolves exact idempotent replay before mutable-state checks,
compares `expected_version`, applies exactly one edge below, increments version
once, updates `updated_at`, appends exactly one `PacketStateChanged` event with
exact before/after state and the validated reason, commits, and returns the
after payload.

## Complete edge graph

Only these edges are permitted:

```text
Planned      -> Waiting | Blocked | Cancelled
Waiting      -> Ready | Blocked | Cancelled
Blocked      -> Waiting | Ready | Cancelled
Ready        -> Waiting | Blocked | Dispatchable | Cancelled
Dispatchable -> Ready | Waiting | Blocked | Cancelled
```

Every other source/target pair among the sixteen packet states is rejected
without mutation. In particular, this primitive cannot enter or leave
`Leased`, `Running`, `AwaitingIntegration`, `AwaitingReview`, `MergeReady`,
`AwaitingArchitect`, `AwaitingOwner`, `Merged`, `Complete`, or
`NeedsReplan`. Those transitions require later companion claim, attempt,
review, acceptance, merge-observation, or recovery evidence. `Cancelled` is
terminal here.

The caller must already have recomputed dependency, route, source, WIP, and
resource eligibility. This method records that prevalidated choice; it does
not calculate eligibility, select work, acquire a lease/lock, create an
attempt, infer authority, or dispatch an agent. `actor` is an audit identity,
not authorization.

Unknown packet raises `InvalidRecord`; stale version raises `StaleState`;
unlisted/self edge raises `InvalidTransition`; same idempotency key with
changed immutable facts raises `IdempotencyConflict`; exhausted SQLite busy
raises `ResourceBusy`.

## Replay and reconstruction contract

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

Canonical JSON uses the existing `canonical_json` rules. `now` is observation
time and is excluded. A same-key retry with a later valid `now` returns the
original after payload and retains the original event time. Changing actor,
packet ID, expected version, target state, or reason conflicts.

Event insertion failure rolls back the packet update. Two concurrent commands
from one version produce one winner and one stale result. Restart replay does
not add a version or event. No lease, lock, attempt, wait, review, acceptance,
merge observation, or notification row changes.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_packet_eligibility.py
```

No schema migration, CLI/API, scheduler, eligibility calculator, claim,
lease/lock, attempt, heartbeat, recovery, completion/review/correction,
acceptance/merge, notification, repository/GitHub, project create/register,
service, Atlas, external access, live project, M1-03, deployment, or merge
behavior is permitted.

## Named sufficient proof

`tests/m1_02/test_packet_eligibility.py` contains exactly fourteen tests:

1. materialization produces Planned/version-1 baseline;
2. each listed forward eligibility edge succeeds;
3. each listed fallback/block/cancel edge succeeds;
4. a Cartesian check over all 256 source/target pairs proves exactly the
   listed edges succeed and every other pair fails without mutation;
5. every companion-evidence lifecycle state is unreachable through this API;
6. stale version fails without mutation;
7. missing packet fails without an event;
8. same-key/same-command replay with later `now` is exact and single-event;
9. changing any immutable command field conflicts;
10. independent documented-fingerprint reconstruction matches the stored
    digest and the event has exact before/after/reason/actor fields;
11. forced event insertion failure rolls back state and event;
12. simultaneous transitions from one version yield one winner;
13. restart preserves state/version/event and exact replay;
14. successful and rejected calls leave every companion table unchanged.

Run all existing Alpha-01, Alpha-02, Alpha-03, M1-01, M1-02, and
review-readiness tests plus the new fourteen tests, compileall, exact-path
confinement, staged/unstaged/untracked hygiene, independent fingerprint
reconstruction, and ten fresh lifecycle stress runs. Expected total after the
new suite is 191 tests. Passing this closed inventory is enough.

## Bounded quality contracts

### Q1 — Exact packet eligibility state

- **Protected outcome:** a recorded packet eligibility change cannot skip,
  invent, duplicate, or partially apply an approved edge.
- **Operating/threat/failure model:** one Linux service writer, stale callers,
  invalid edges, failed event insertion, SQLite contention, duplicate delivery,
  and two threads at one expected version.
- **Explicit exclusions:** hostile same-UID database tampering, distributed
  writers, eligibility computation, claims, dispatch, and later lifecycle.
- **Assurance level:** closed 16×16 graph proof, optimistic version guard,
  immediate transaction, durable event, and real SQLite tests.
- **Acceptance proof:** named tests 1–7 and 10–12 plus regressions pass.
- **Implementation boundary:** one store method and private helpers in the
  existing module; no migration or new dependency.
- **Proportionality ceiling:** no generic workflow engine or public surface.
- **Stop and escalation rule:** any required edge that needs a companion row,
  new state, schema change, or eligibility decision returns the slice.

### Q2 — Replay, restart, and isolation

- **Protected outcome:** retry, restart, rollback, or contention cannot produce
  contradictory packet state or mutate companion operational records.
- **Operating/threat/failure model:** duplicate key delivery, conflicting key
  reuse, process reopen, injected event failure, and concurrent writers.
- **Explicit exclusions:** multi-host consensus and automatic recovery action.
- **Assurance level:** durable fingerprint, SQLite transaction serialization,
  exact replay, and companion-table snapshots.
- **Acceptance proof:** named tests 8–14 and ten fresh stress runs pass.
- **Implementation boundary:** reuse existing event/idempotency facilities.
- **Proportionality ceiling:** one packet state row and one event per success.
- **Stop and escalation rule:** any replay depends on process memory, creates
  another event, or changes a companion row returns the slice.

### Q3 — Authority and scope confinement

- **Protected outcome:** the method cannot claim work, dispatch, infer policy,
  or cross the explicitly reserved lifecycle boundaries.
- **Operating/threat/failure model:** accidental API expansion or an attempted
  transition into a state requiring durable companion evidence.
- **Explicit exclusions:** the later authorized methods that create and verify
  that companion evidence.
- **Assurance level:** no call site or public exposure, two-path allowlist,
  complete graph rejection, and full regression proof.
- **Acceptance proof:** named tests 4, 5, and 14; exact diff inspection; 191
  tests; compile; and mechanical review-readiness pass.
- **Implementation boundary:** local SQLite service boundary only.
- **Proportionality ceiling:** no scheduler, policy evaluator, or new entity.
- **Stop and escalation rule:** external authority, credentials, M1-03,
  terminal M1-02B dependency, or product-boundary change returns before review.

## Review sequence and counters

The slice receives one complete pre-execution Decision Fidelity review, at
most one planning correction and its sole targeted verification, one complete
independent implementation review, and at most one implementation correction
and its sole targeted verification. The mechanical readiness gate must return
`ready: true` before either reviewer launch. A blocked gate consumes no review
allowance. Project Architect risk disposition controls any implementation
finding. No successor slice begins until this slice is terminally merged or
returned.

| Counter | Value |
|---|---:|
| Complete Decision Fidelity review | 0 |
| Planning correction | 0 |
| Targeted planning verification | 0 |
| Implementation review | 0 |
| Implementation correction | 0 |
| Targeted implementation verification | 0 |
