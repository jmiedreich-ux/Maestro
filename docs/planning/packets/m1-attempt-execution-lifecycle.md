# M1 Attempt Execution Lifecycle

**Slice ID:** `MB-SLICE-M1-ATTEMPT-EXECUTION-01`
**Status:** `Pending targeted Decision Fidelity`
**Base:** `0b00c26c396216d293ba8f09b780c2bc07630066`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-ATTEMPT-EXECUTION-01` |
| `phase` | `PendingTargetedDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:0b00c26c396216d293ba8f09b780c2bc07630066", "git:planning-review:0b00c26c396216d293ba8f09b780c2bc07630066..02bd185b4cc001f073a27a106006579ce957aefd", "readiness:86737b3f04a89abdb02b5b284451725048b5836e67ea65e398cb8550c7290f87", "review:M1-ATTEMPT-EXECUTION-DFR-01-REQUEST_CHANGES"]` |

The carrier has exactly the canonical v1 keys. Counts never reset.

## Authority and outcome

This independent continuation uses the current Master Plan, Agent Workforce
Control Plane, M0-D01, M0-D05, M0-D11, M0-D12, M0-D14, the integrated schema-4
records, packet eligibility, and atomic assignment claim. Returned M1-02B
slices remain immutable history and are not authority.

Implement one honest, local attempt-execution lifecycle. A trusted caller can:

1. start the Planned attempt created by the atomic claim only after it has a
   non-empty external execution handle and exact expected result;
2. heartbeat that exact Running execution while renewing its active lease; and
3. finish that exact execution once, atomically routing the packet to its next
   operational state and releasing its lease and locks.

Assignment, intent, a lease, or a lock never creates `Running`. This slice
records an externally obtained handle; it does not launch or contact a worker.

## Additive schema 5

Advance schema version 4 to 5 in one transaction. Add only these nullable
columns to `attempts`, preserving every existing row byte-for-byte across its
original columns:

```text
execution_handle TEXT
expected_result TEXT
heartbeat_at TEXT
completion_evidence_reference TEXT
```

Each text carrier is canonical non-empty UTF-8 text up to 512 bytes when
non-null. Add one unique partial index over non-null `execution_handle` and
insert/update validation triggers enforcing:

- `Planned`: all four new carriers and existing start/finish/result carriers
  are null;
- `Running`: handle, expected result, `started_at`, and `heartbeat_at` are
  non-null while `finished_at`, `result_commit`, and completion evidence are
  null;
- `Succeeded`: all execution carriers are non-null, including full-40-hex
  `result_commit`;
- `Failed|Cancelled|TimedOut|Stale`: handle, expected result, start, heartbeat,
  finish, and completion evidence are non-null and `result_commit` is null.

The migration accepts supported histories ending at 2, 3, 4, or 5, applies
only missing migrations, inserts version 5 last, is a no-op after completion,
and rolls back every schema/data/version change on failure. It does not rebuild,
drop, rename, truncate, or rewrite an accepted table.

## Closed commands

```text
OperationalStateStore.start_attempt_execution(
  attempt_id, expected_attempt_version, expected_packet_version,
  execution_handle, expected_result, reason_payload,
  idempotency_key, actor, now
) -> result

OperationalStateStore.heartbeat_attempt_execution(
  attempt_id, expected_attempt_version, expected_lease_version,
  execution_handle, new_expires_at, reason_payload,
  idempotency_key, actor, now
) -> result

OperationalStateStore.finish_attempt_execution(
  attempt_id, expected_attempt_version, expected_packet_version,
  execution_handle, outcome, result_commit,
  completion_evidence_reference, reason_payload,
  idempotency_key, actor, now
) -> result
```

All inputs are validated before writing. Every command uses one
`BEGIN IMMEDIATE` transaction, resolves exact replay before mutable-state
checks, compares every supplied version, writes one composite event before
commit, and returns the exact canonical object below. Same key and same
immutable facts replays the original result and time; same key with changed
facts raises `IdempotencyConflict`. Busy exhaustion is not retried.

Every state object below is exactly:

```json
{"entity_id":"id","entity_type":"Attempt|Packet|Lease|ResourceLock","kind":"state","state":"state","version":1}
```

Arrays of locks are ordered by `entity_id`. No key beyond those shown is
allowed in a result or composite event envelope.

### Start

Start requires a `Planned` attempt, its packet in `Leased`, and the referenced
lease `Active` and unexpired at `now`. It writes attempt `Running` with the
exact handle, expected result, start and heartbeat time; writes packet
`Running`; increments each changed version once; and emits one
`AttemptStateChanged` event. The handle must not occur on any other attempt.
The exact result and event payloads are:

```json
{
  "attempt":{"entity_id":"attempt-id","entity_type":"Attempt","kind":"state","state":"Running","version":2},
  "execution":{"attempt_id":"attempt-id","execution_handle":"provider-job-id","expected_result":"committed-candidate","heartbeat_at":"now","started_at":"now"},
  "lease":{"entity_id":"lease-id","entity_type":"Lease","kind":"state","state":"Active","version":1},
  "packet":{"entity_id":"packet-id","entity_type":"Packet","kind":"state","state":"Running","version":7}
}
```

The event has `entity_type=Attempt`, `entity_id=attempt-id`,
`event_type=AttemptStateChanged`, `before_json={"attempt": planned-state,
"packet": leased-state}`, and `after_json` equal to the result.

### Heartbeat

Heartbeat requires the exact stored handle, a `Running` attempt and packet,
and its `Active` lease. `now` must be strictly later than the stored attempt
and lease heartbeat; `new_expires_at` must be later than `now` and the current
lease expiry. It advances attempt heartbeat/version and lease heartbeat,
expiry, and version once and emits one composite `LeaseHeartbeatRecorded`
event. It neither changes packet state nor invents worker progress. Its exact
result is:

```json
{
  "attempt":{"entity_id":"attempt-id","entity_type":"Attempt","kind":"state","state":"Running","version":3},
  "execution":{"attempt_id":"attempt-id","execution_handle":"provider-job-id","expected_result":"committed-candidate","heartbeat_at":"now"},
  "lease":{"entity_id":"lease-id","entity_type":"Lease","expires_at":"new-expires-at","heartbeat_at":"now","kind":"state","state":"Active","version":2}
}
```

The event has `entity_type=Lease`, `entity_id=lease-id`,
`event_type=LeaseHeartbeatRecorded`. Its `before_json` has exact keys
`attempt`, `execution`, and `lease`: the attempt state, an execution object
containing `attempt_id`, `execution_handle`, and the prior `heartbeat_at`, and
a lease object shaped as above with the prior expiry, heartbeat, and version.
Its `after_json` equals the result.

### Finish

Finish requires the exact stored handle and a `Running` attempt and packet.
The closed outcome mapping is:

| Attempt outcome | Packet state | Lease state | Lock state | Result commit |
|---|---|---|---|---|
| `Succeeded` | `AwaitingIntegration` | `Released` | `Released` | required |
| `Failed` | `NeedsReplan` | `Released` | `Released` | prohibited |
| `Cancelled` | `Cancelled` | `Cancelled` | `Released` | prohibited |
| `TimedOut` | `NeedsReplan` | `Expired` | `Expired` | prohibited |
| `Stale` | `NeedsReplan` | `Released` | `Released` | prohibited |

Normal success/failure/cancellation/stale completion requires `now` no later
than lease expiry; `TimedOut` requires `now` later than lease expiry. Finish
sets attempt finish and evidence facts, updates packet, closes the lease and
every active lock owned by it, increments every changed version once, and emits
one composite `AttemptStateChanged` event. It performs no integration, review,
correction, merge, redispatch, or external action.

The exact finish result is:

```json
{
  "attempt":{"entity_id":"attempt-id","entity_type":"Attempt","kind":"state","state":"Succeeded","version":4},
  "completion":{"attempt_id":"attempt-id","completion_evidence_reference":"evidence-ref","execution_handle":"provider-job-id","finished_at":"now","result_commit":"40-hex-or-null"},
  "lease":{"entity_id":"lease-id","entity_type":"Lease","kind":"state","state":"Released","version":3},
  "locks":[{"entity_id":"lock-id","entity_type":"ResourceLock","kind":"state","state":"Released","version":2}],
  "packet":{"entity_id":"packet-id","entity_type":"Packet","kind":"state","state":"AwaitingIntegration","version":8}
}
```

The state values follow the outcome table. The event has
`entity_type=Attempt`, `entity_id=attempt-id`,
`event_type=AttemptStateChanged`. Its `before_json` has exact keys `attempt`,
`execution`, `lease`, `locks`, and `packet`: pre-change state objects plus an
execution object with `attempt_id`, `execution_handle`, `expected_result`, and
the stored `heartbeat_at`. Its `after_json` equals the result.

### Exact fingerprints

Each fingerprint is SHA-256 of the UTF-8 canonical JSON for its exact object.
`actor` has exact keys `actor_id`, `actor_type`, `causation_event_id`, and
`correlation_id`; `reason` is the validated closed reason payload. `now` is
observation time and is excluded.

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"start_attempt_execution","payload":{"attempt_id":"...","execution_handle":"...","expected_attempt_version":1,"expected_packet_version":6,"expected_result":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."}}}
```

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"heartbeat_attempt_execution","payload":{"attempt_id":"...","execution_handle":"...","expected_attempt_version":2,"expected_lease_version":1,"new_expires_at":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."}}}
```

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"finish_attempt_execution","payload":{"attempt_id":"...","completion_evidence_reference":"...","execution_handle":"...","expected_attempt_version":3,"expected_packet_version":7,"outcome":"Succeeded","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."},"result_commit":"40-hex-or-null"}}
```

### Closed errors and check precedence

Before opening the transaction, validate arguments in signature order, then
the command-specific enum/commit/time relationships, reason, idempotency key,
actor, and canonical fingerprint. Malformed or out-of-range input raises
`InvalidRecord`. Inside the transaction, the order is always: exact replay or
`IdempotencyConflict`; attempt existence; attempt version; attempt state;
execution-handle match when already Running; packet existence/relationship;
packet version when supplied; packet state; lease existence/relationship;
lease version when supplied; lease state; time/expiry rules; execution-handle
uniqueness for start; active locks ordered by ID for finish; mutation; event;
commit.

A missing or structurally mismatched entity raises `InvalidRecord`; a supplied
version or Running handle mismatch raises `StaleState`; an unavailable source
state or violated lease/time transition raises `InvalidTransition`; an
execution handle already bound to another attempt raises `ResourceConflict`;
changed-fact key reuse raises `IdempotencyConflict`; and SQLite busy exhaustion
raises `ResourceBusy`. A concurrent constraint collision is mapped to the same
domain error its precheck names. Every other integrity violation is
`InvalidRecord`. No rejected command writes state or an event.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/storage.py
services/maestro/maestro/operational_state.py
tests/m1_01/test_project_authority_storage.py
tests/m1_02/test_schema_and_records.py
tests/m1_02/test_attempt_execution.py
```

No CLI, worker launcher, provider adapter, scheduler, recovery service,
completion/review controller, learning record, Git/GitHub operation, Atlas,
notification delivery, live project, external access, or M1-03 work is allowed.

## Named sufficient proof

`tests/m1_02/test_attempt_execution.py` contains exactly 22 tests proving:

1. schema 4 upgrades additively to exact schema 5 while preserving rows;
2. injected schema-5 failure rolls back schema, version, and data;
3. reopen and concurrent migrators produce one version-5 row;
4. valid start changes attempt and packet with one exact event;
5. missing/invalid/duplicate handles and expected results cannot create Running;
6. wrong attempt, packet, lease state, or expired lease blocks start;
7. stale start versions leave all state unchanged;
8. start replay is exact and changed-fact key reuse conflicts;
9. forced start-event failure rolls back both states;
10. concurrent starts have exactly one winner and no loser residue;
11. valid heartbeat renews attempt and lease with one exact event;
12. wrong handle, stale versions, or non-monotonic times block heartbeat;
13. heartbeat replay is exact and changed-fact key reuse conflicts;
14. heartbeat event failure and contention cannot partially renew;
15. every closed finish outcome produces exactly its mapped durable state;
16. success requires one valid result commit and other outcomes prohibit it;
17. handle, evidence, state, lease, and timeout-time guards block invalid finish;
18. finish replay is exact and changed-fact key reuse conflicts;
19. finish event failure and contention cannot partially terminate;
20. restart preserves terminal state and replay without active ownership;
21. independently built fingerprints and composite events match exactly; and
22. existing attempt-bound progress recording remains valid and separate from
    heartbeat evidence.

Run all existing Alpha-01, Alpha-02, Alpha-03, M1-01, M1-02, and
review-readiness tests plus the new 22 tests; run the start/heartbeat/finish
concurrency and restart group in ten fresh processes; run compileall with an
external pycache; and run exact diff, allowlist, staged, tracked/untracked,
artifact, and sensitive-value checks.

## M0-D12 quality contract

1. **Protected outcome:** no attempt or packet is `Running` without a unique
   current execution handle, and duplicate, stale, interrupted, expired, or
   restarted observations cannot duplicate or split execution state from
   ownership.
2. **Operating and threat model:** one trusted local Maestro writer, one SQLite
   database, concurrent threads/processes, validated trusted-caller commands,
   provider handles already obtained externally, crashes before commit,
   duplicate/stale observations, lease expiry, and service restart.
3. **Explicit exclusions:** a lying or compromised provider, database
   corruption, hostile same-UID/root mutation, multi-host writers, actual
   worker launch or termination, network truth, distributed consensus, and
   physical machine-reboot proof.
4. **Assurance level:** exact local SQLite transactions and schema constraints,
   finite state/outcome complements, idempotent reconstruction, injected
   failure seams, contention, reopen, and fresh-process restart proof.
5. **Acceptance proof:** the 22 tests and complete regression/stress,
   compilation, candidate-union, allowlist, staged-hygiene, artifact, and
   sensitive-value checks named in `Named sufficient proof` are sufficient.
6. **Implementation boundary:** only the five paths in `Exact implementation
   boundary`, Python standard library, existing Maestro SQLite/config/value
   helpers, and no new dependency or process are permitted.
7. **Proportionality ceiling:** one additive four-column schema migration, one
   uniqueness index, only the minimum insert/update validation triggers, three
   storage methods, one new 22-test module, and the minimum compatibility edits
   to the two named existing test modules. No general transition framework,
   executor abstraction, ORM, background process, or policy redesign.
8. **Stop and escalation rule:** stop and return to the Project Architect on
   any need for an undeclared state, route, schema carrier, path, dependency,
   external fact, more than one event per command, or work beyond this ceiling.
   One planning correction and one implementation correction are the maximum
   allowed by the Bootstrap Convergence Policy. Final merge uses the Owner's
   standing point-1 merge authority only after exact-candidate readiness and
   independent implementation approval.
