# M1 Execution Start

**Slice ID:** `MB-SLICE-M1-EXECUTION-START-01`
**Status:** `Pending Decision Fidelity`
**Base:** `7f81b42c3bd0b853dcd10b1b6a75208d5866f141`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-EXECUTION-START-01` |
| `phase` | `PendingDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:7f81b42c3bd0b853dcd10b1b6a75208d5866f141"]` |

The carrier has exactly the canonical v1 keys. Counts never reset.

## Authority, outcome, and independence

This new independent slice uses the current Master Plan, Agent Workforce
Control Plane, M0-D01, M0-D05, M0-D11, M0-D12, M0-D14, schema-4 operational
records, and the merged atomic assignment claim. All returned slices,
including `MB-SLICE-M1-ATTEMPT-EXECUTION-01`, remain immutable history and are
not authority or reusable review allowance.

Implement one vertical behavior: a trusted caller records an externally
obtained execution handle and exact expected result, then atomically changes
the claimed attempt from `Planned` to `Running` and its packet from `Leased` to
`Running`. Assignment, intent, a lease, or a lock never creates `Running`.
This slice records a supplied handle; it does not launch or contact a worker.

## Additive schema 5

Advance schema version 4 to 5 in one transaction. Add only these nullable
columns to `attempts`, preserving all original columns and rows:

```text
execution_handle TEXT
expected_result TEXT
heartbeat_at TEXT
completion_evidence_reference TEXT
```

When non-null, each text carrier is canonical non-empty UTF-8 text of at most
512 bytes. Add a unique partial index over non-null `execution_handle` and the
minimum insert/update triggers enforcing these exact row shapes:

- `Planned`: all four new carriers, `started_at`, `finished_at`, and
  `result_commit` are null.
- `Running`: `execution_handle`, `expected_result`, `started_at`, and
  `heartbeat_at` are non-null; `finished_at`, `result_commit`, and
  `completion_evidence_reference` are null.
- `Succeeded`: all execution carriers are non-null and `result_commit` is full
  lowercase 40-hex.
- `Failed|Cancelled|TimedOut|Stale`: handle, expected result, start, heartbeat,
  finish, and completion evidence are non-null; `result_commit` is null.

The migration accepts supported histories ending at 2, 3, 4, or 5, applies
only missing migrations, inserts version 5 last, is a no-op after completion,
and rolls back schema, version, and data on any injected failure. It never
rebuilds, drops, renames, truncates, or rewrites an accepted table. It changes
no existing event type or existing schema-4 object's meaning.

## Exact command protocol

```text
OperationalStateStore.start_attempt_execution(
  attempt_id, expected_attempt_version, expected_packet_version,
  execution_handle, expected_result, reason_payload,
  idempotency_key, actor, now
) -> result
```

Each state value in this section is exactly the existing five-key state
payload: `entity_id`, `entity_type`, `kind="state"`, `state`, and `version`.
The exact result has only these four top-level keys:

```json
{
  "attempt":{"entity_id":"attempt-id","entity_type":"Attempt","kind":"state","state":"Running","version":2},
  "execution":{"attempt_id":"attempt-id","execution_handle":"provider-job-id","expected_result":"committed-candidate","heartbeat_at":"2026-09-04T12:00:00.000000Z","started_at":"2026-09-04T12:00:00.000000Z"},
  "lease":{"entity_id":"lease-id","entity_type":"Lease","kind":"state","state":"Active","version":1},
  "packet":{"entity_id":"packet-id","entity_type":"Packet","kind":"state","state":"Running","version":7}
}
```

The attempt/packet versions are their supplied expected versions plus one;
lease version is its unchanged stored version. The execution timestamps are
the validated `now` exactly. No additional key is permitted.

The command validates all supplied values before writing, uses one
`BEGIN IMMEDIATE` transaction, changes attempt and packet once, and inserts
one event before commit:

```text
entity_type = Attempt
entity_id = attempt_id
event_type = AttemptStateChanged
before_json = {"attempt": <Planned five-key state>, "packet": <Leased five-key state>}
after_json = <exact result above>
reason = <validated supplied reason payload>
```

The exact fingerprint is SHA-256 of UTF-8 canonical JSON for:

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"start_attempt_execution","payload":{"attempt_id":"...","execution_handle":"...","expected_attempt_version":1,"expected_packet_version":6,"expected_result":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."}}}
```

`now` is observation time and is excluded from the fingerprint. Same key and
same immutable facts returns the originally stored result and timestamps before
any mutable check. Same key with changed facts raises `IdempotencyConflict`.

Input validation order is signature order, then reason kind, idempotency key,
actor, `now`, and fingerprint construction. Malformed input raises
`InvalidRecord`. Inside the transaction the exact order is: replay/conflict;
attempt existence; attempt version; attempt state `Planned`; packet existence
and attempt/packet relationship; packet version; packet state `Leased`; lease
existence and attempt/packet relationship; lease state `Active`; lease expiry
strictly after `now`; execution-handle uniqueness; attempt update; packet
update; event insert; commit.

A missing or mismatched entity raises `InvalidRecord`; a version mismatch
raises `StaleState`; an unavailable state or expired lease raises
`InvalidTransition`; a handle bound to another attempt raises
`ResourceConflict`; changed-fact key reuse raises `IdempotencyConflict`; and
SQLite busy exhaustion raises `ResourceBusy`. A concurrent unique-handle
collision maps to `ResourceConflict`; any other integrity failure maps to
`InvalidRecord`. Every rejection and injected event failure leaves attempt,
packet, lease, locks, and events unchanged.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/storage.py
services/maestro/maestro/operational_state.py
tests/m1_01/test_project_authority_storage.py
tests/m1_02/test_schema_and_records.py
tests/m1_02/test_execution_start.py
```

No heartbeat/finish command, CLI, worker launcher, provider adapter, scheduler,
recovery service, completion/review controller, learning record, Git/GitHub
operation, Atlas, notification delivery, live project, external access, or
M1-03 work is permitted.

## Named sufficient proof

`tests/m1_02/test_execution_start.py` contains exactly eleven tests proving:

1. schema 4 upgrades additively to exact schema 5 and preserves original rows;
2. an injected schema-5 failure rolls back schema, version, and data;
3. reopen and two concurrent migrators produce exactly one version-5 row;
4. valid start returns the exact result and changes attempt/packet once;
5. malformed, empty, reused, and concurrently duplicated handles are blocked;
6. missing/mismatched records, wrong states, and expired lease are blocked;
7. stale attempt or packet version leaves all state unchanged;
8. same-key replay is exact and changed immutable facts conflict;
9. event failure rolls back both updates and concurrency has one winner;
10. restart preserves Running identity and exact replay without duplication;
11. an independently built fingerprint and event envelope match every field.

Compatibility edits in the two named existing test modules prove version
2/3/4-to-5 preservation, exact columns/index/triggers, failure rollback, and
schema-history behavior. Run all existing Alpha-01, Alpha-02, Alpha-03, M1-01,
M1-02, and review-readiness tests plus the eleven new tests; run tests 5, 9,
and 10 in ten fresh processes; run compileall with an external pycache; and run
exact diff, allowlist, staged, tracked/untracked, artifact, and sensitive-value
checks.

## M0-D12 quality contract

1. **Protected outcome:** an attempt and packet cannot be recorded `Running`
   without one unique current external execution handle and exact expected
   result, and replay, contention, failure, or restart cannot split them.
2. **Operating and threat model:** one trusted local Maestro writer, one SQLite
   database, validated trusted-caller commands, concurrent threads/processes,
   provider handles already obtained externally, crash before commit,
   duplicate/stale commands, lease expiry, and service restart.
3. **Explicit exclusions:** lying/compromised providers, database corruption,
   hostile same-UID/root mutation, multi-host writers, actual worker launch or
   termination, network truth, distributed consensus, and machine reboot.
4. **Assurance level:** exact additive migration, SQLite transaction and
   constraints, closed protocol/error precedence, idempotent reconstruction,
   failure seam, contention, reopen, and fresh-process restart proof.
5. **Acceptance proof:** the eleven named tests, compatibility tests, complete
   regression suite, ten-run stress group, compilation, candidate-union,
   allowlist, staged-hygiene, artifact, and sensitive-value checks above.
6. **Implementation boundary:** only the five named paths, Python standard
   library, and existing Maestro SQLite/config/value/event helpers; no new
   dependency or process.
7. **Proportionality ceiling:** four additive attempt columns, one partial
   unique index, minimum row-shape triggers, one storage command, one new
   eleven-test module, and minimum compatibility edits. No general lifecycle
   framework, executor abstraction, ORM, background process, or redesign.
8. **Stop and escalation rule:** return to the Project Architect on any need
   for another state, command, envelope, carrier, path, dependency, external
   fact, event, or work beyond this ceiling. One planning correction and one
   implementation correction are the maximum. Merge uses the Owner's standing
   point-1 authority only after exact-candidate readiness and independent
   implementation approval.
