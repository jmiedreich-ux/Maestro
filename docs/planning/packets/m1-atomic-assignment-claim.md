# M1 Atomic Assignment Claim

**Slice ID:** `MB-SLICE-M1-ASSIGNMENT-CLAIM-01`
**Status:** `Decision Fidelity approved; implementation released`
**Base:** `55a1f3a5a36c9bf3b79480639b0c6de2a14f4241`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-ASSIGNMENT-CLAIM-01` |
| `phase` | `Frozen` |
| `current_actor` | `None` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:55a1f3a5a36c9bf3b79480639b0c6de2a14f4241", "git:planning-review:55a1f3a5a36c9bf3b79480639b0c6de2a14f4241..1a544a17c1e0c4b8edcc1e649867d32a3488ff35", "readiness:7a39e50f22e96a22a7b042a36a5ce24fa3c5a05d0841c0a27f8d0b9137c4cfea", "review:M1-ASSIGNMENT-CLAIM-DFR-01-APPROVE"]` |

The carrier has exactly the canonical v1 keys. Counts never reset.

## Authority and outcome

This independent slice is derived from current master, the Bootstrap
Convergence Policy, M0-D01, M0-D05, M0-D12, the Master Plan, the Agent
Workforce Control Plane sections 7.1, 7.4, and 8, and the merged packet
eligibility behavior. All terminal slices remain immutable history and are
not authority for this slice.

Implement one trusted-caller compound storage command:

```text
OperationalStateStore.claim_packet_assignment(
  packet_id, expected_version, lease_request, lock_requests,
  attempt_request, reason_payload, idempotency_key, actor, now
) -> assignment_result
```

It atomically changes one `Dispatchable` packet to `Leased`, creates one
Active lease, creates exactly the packet's complete declared lock set, creates
one Planned Initial attempt, and appends one composite `PacketClaimed` event.
It does not start an agent or mark work Running.

## Closed request and result

```json
{
  "lease_request": {
    "executor_route": "text",
    "expires_at": "YYYY-MM-DDTHH:MM:SS.ffffffZ",
    "holder_id": "text",
    "lease_id": "text",
    "worktree_path": "text"
  },
  "lock_requests": [
    {
      "lock_id": "text",
      "lock_kind": "Path|SharedBoundary|FiniteResource",
      "resource_key": "text"
    }
  ],
  "attempt_request": {
    "attempt_id": "text",
    "model_identity": "text",
    "runtime_identity": "text"
  }
}
```

`lock_requests` is ordered by `resource_key`; resource keys are unique and
exactly equal the packet's already sorted `resource_claims_json`. Empty
declarations require an empty request. Lock IDs are unique. Current authority
does not map resource-key prefixes to lock kinds, so the trusted caller
supplies one of the closed lock-kind values; Maestro does not infer a prefix
rule.

The store derives `run_id` and `run_fingerprint` from the packet's run; lease
`base_commit` from the packet; lease `claim_key` from `idempotency_key`;
attempt packet/lease IDs, number `1`, kind `Initial`, and `executor_class` from
the packet; and all initial states, timestamps, null fields, and versions.

The result is exactly:

```json
{
  "attempt": {"entity_id":"attempt-id","entity_type":"Attempt","kind":"state","state":"Planned","version":1},
  "claim": {"kind":"claim","lease_id":"lease-id","lock_ids":["lock-id"],"packet_id":"packet-id"},
  "lease": {"entity_id":"lease-id","entity_type":"Lease","kind":"state","state":"Active","version":1},
  "locks": [{"entity_id":"lock-id","entity_type":"ResourceLock","kind":"state","state":"Active","version":1}],
  "packet": {"entity_id":"packet-id","entity_type":"Packet","kind":"state","state":"Leased","version":2}
}
```

`locks` and `claim.lock_ids` are sorted by lock ID. This is a private aggregate
result, not a new public `validate_payload` variant.

## Validation, precedence, and atomic mutation

The exact order is:

1. validate all closed request shapes and scalar types;
2. normalize reason, actor, idempotency key, and timestamps;
3. open `BEGIN IMMEDIATE`;
4. resolve exact replay before mutable-state checks;
5. for a new command, require `expires_at > now`;
6. require the packet exists;
7. compare `expected_version`, raising `StaleState` on mismatch;
8. require packet state `Dispatchable`, otherwise `InvalidTransition`;
9. require its run exists and is `Running`, raising `InvalidRecord` or
   `InvalidTransition` respectively;
10. require requested resource keys exactly equal the declared set;
11. reject reused lease, lock, or attempt IDs and an existing Initial attempt
    as `InvalidRecord`;
12. check Active conflicts in order: packet lease, worktree lease, then the
    lexicographically smallest conflicting resource key, raising
    `ResourceConflict`;
13. apply the guarded packet update and all inserts; and
14. map exhausted SQLite busy to `ResourceBusy` and an unexpected integrity
    failure to `InvalidRecord`.

An exact replay may occur after the original expiry: timestamp syntax is
validated before replay, while `expires_at > now` applies only to a new
command.

In one transaction the packet becomes `Leased`, version increases once, and
`updated_at=now`; the lease is Active/version 1 with
`acquired_at=heartbeat_at=now`, supplied expiry, and null `released_at`; every
lock is Active/version 1 with common acquisition/expiry and null release; the
attempt is Initial/number 1/Planned/version 1 with null result, correction,
start, and finish; and exactly one `PacketClaimed` event is written. Its
`before_json` is the packet state before the claim, `after_json` is the exact
aggregate result, and its reason/actor/fingerprint are exact. No separate
packet-state or attempt-recorded event is added. Any failure rolls back all
five record categories.

An Active lease or lock conflicts even when its timestamp has passed; expiry
must be durably reconciled later. Released and Expired locks do not conflict.
Same-packet concurrent claims yield one success and one stale result.
Different packets racing for one resource yield one success and one
`ResourceConflict`.

## Fingerprint and restart

The fingerprint is SHA-256 over UTF-8 existing canonical JSON for:

```json
{
  "actor": {"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},
  "operation": "claim_packet_assignment",
  "payload": {
    "attempt": {"attempt_id":"...","model_identity":"...","runtime_identity":"..."},
    "expected_version": 4,
    "lease": {"executor_route":"...","expires_at":"...","holder_id":"...","lease_id":"...","worktree_path":"..."},
    "locks": [{"lock_id":"...","lock_kind":"SharedBoundary","resource_key":"shared:operational-state"}],
    "packet_id": "...",
    "reason": {"detail_reference":null,"kind":"reason","reason_code":"..."}
  }
}
```

`now` is excluded; every caller-controlled immutable fact is included. Exact
retry and restart replay return the originally stored aggregate result without
new rows or events.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_assignment_claim.py
```

No migration, API/CLI, agent launch, `Running` transition, context/evidence or
progress record, lock release/expiry/recovery, scheduler/eligibility
calculation, Git/GitHub, project create/register, Linux service, Atlas,
external/live-project access, M1-03, deployment, or merge behavior is allowed.

## Named sufficient proof

`tests/m1_02/test_assignment_claim.py` contains exactly eighteen tests:

1. valid claim creates the exact compound result atomically;
2. an empty declared lock set creates no locks;
3. run fingerprint, base, run ID, and executor facts are derived;
4. closed inputs follow the deterministic first-error precedence;
5. requested locks exactly cover declared resources;
6. new expiry follows observation while late exact replay succeeds;
7. missing, stale, nondispatchable, and nonrunning precedence is exact;
8. Active packet-lease conflict makes no mutation;
9. Active worktree conflict makes no mutation;
10. Active resource conflicts while Released/Expired locks do not;
11. reused IDs and an existing Initial attempt are rejected;
12. same-key same-command replay occurs exactly once;
13. every changed immutable command fact conflicts;
14. independent fingerprint and exact `PacketClaimed` event match;
15. event failure rolls back packet, lease, locks, and attempt;
16. each intermediate write failure rolls back every table;
17. concurrent same-packet and shared-resource claims each have one winner;
18. restart replay is exact and has no execution side effect.

Run these 18 plus all current 191 tests for 209 total. Also run ten fresh
concurrency/restart stress repetitions, compileall, exact two-path
confinement, staged/unstaged/untracked hygiene, independent fingerprint
reconstruction, and the mechanical implementation-review readiness gate.
Passing this closed inventory is enough.

## Bounded quality contracts

### Q1 — Atomic complete claim

- **Protected outcome:** a packet cannot become Leased without exactly one
  matching lease, full declared lock set, Planned Initial attempt, and event.
- **Operating and failure model:** one Linux service writer; malformed/stale
  commands, insert/event failure, duplicate delivery, and SQLite contention.
- **Explicit exclusions:** agent start, executor handle, distributed writers,
  hostile same-UID tampering, and later lifecycle/recovery.
- **Assurance level:** one immediate transaction, guarded version/state,
  failure injection after each mutation, and real SQLite tests.
- **Acceptance proof:** named tests 1–7 and 14–16 plus regressions.
- **Implementation boundary:** one store method/private helpers; no migration
  or dependency.
- **Proportionality ceiling:** no generalized transaction framework.
- **Stop and escalation:** any schema change, partial durable claim, or need to
  mark Running returns the slice.

### Q2 — Exclusive resources and idempotent recovery

- **Protected outcome:** duplicate, competing, or restarted claims cannot own
  the same packet, worktree, or Active resource twice.
- **Operating and failure model:** same/different packet races, expired-time
  but unreconciled Active rows, duplicate keys, ID collision, and reopen.
- **Explicit exclusions:** expiry/release mutation, automatic redispatch,
  multi-host consensus, and scheduler selection.
- **Assurance level:** existing partial unique indexes, explicit conflict
  reads, immediate transaction, durable fingerprint, and stress tests.
- **Acceptance proof:** named tests 8–13 and 17–18 plus ten stress repetitions.
- **Implementation boundary:** existing schema/event/idempotency facilities.
- **Proportionality ceiling:** one assignment command only.
- **Stop and escalation:** a double owner, duplicate event, inferred expiry,
  or process-memory replay returns the slice.

### Q3 — Honest execution and authority boundary

- **Protected outcome:** a durable claim cannot be reported as a running agent
  or create authority beyond the trusted caller's prevalidated choice.
- **Operating and failure model:** accidental execution side effect, public
  exposure, undeclared locks, or caller-supplied authoritative derived facts.
- **Explicit exclusions:** the later start/heartbeat/progress/recovery command.
- **Assurance level:** no public call site, exact two-path allowlist, derived
  durable facts, aggregate event, and companion-table inspection.
- **Acceptance proof:** named tests 2–5, 14, and 18; 209 tests; compile; exact
  diff; and readiness.
- **Implementation boundary:** local SQLite service boundary only.
- **Proportionality ceiling:** no executor, scheduler, or public interface.
- **Stop and escalation:** credentials, external action, M1-03, terminal-slice
  dependency, or product/authority-boundary change returns before review.

## Bounded review sequence

One complete Decision Fidelity review may authorize at most one planning
correction and targeted verification. Implementation then receives one
complete independent review and at most one targeted correction/verification.
Mechanical readiness must return `ready: true` before either reviewer launch;
a blocked check consumes no allowance. The Project Architect dispositions all
implementation findings under the risk policy. No successor begins until this
slice is terminally merged or returned.
