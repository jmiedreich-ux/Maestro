# M1 Execution Heartbeat and Finish

**Slice ID:** `MB-SLICE-M1-EXECUTION-FINISH-01`
**Status:** `Decision Fidelity approved; implementation released`
**Base:** `e7bc781747d7faf85e6724d9b26b0882735f1989`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-EXECUTION-FINISH-01` |
| `phase` | `Frozen` |
| `current_actor` | `None` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:e7bc781747d7faf85e6724d9b26b0882735f1989", "git:planning-review:e7bc781747d7faf85e6724d9b26b0882735f1989..ae41a0eaba3b1403d53c0c1258ea137dc57a514f", "readiness:5e67fa46188d84776f2e67832c4cc732904990033de579aa40cc10d4147e472d", "review:M1-EXECUTION-FINISH-DFR-01-APPROVE"]` |

The carrier has exactly the canonical v1 keys. Counts never reset.

## Authority and outcome

This independent slice uses current master, the Master Plan, Agent Workforce
Control Plane, M0-D01, M0-D05, M0-D11, M0-D12, M0-D14, and merged execution
start. Returned slices remain immutable non-authority.

Implement two trusted-caller storage commands for the exact Running execution:

1. record a fresh heartbeat while renewing its active lease; and
2. record one terminal worker outcome, route its packet, and close its lease
   and locks atomically.

Neither command polls, launches, terminates, redispatches, integrates, reviews,
merges, or contacts an external system.

## Exact commands

```text
OperationalStateStore.heartbeat_attempt_execution(
  attempt_id, expected_attempt_version, expected_lease_version,
  execution_handle, new_expires_at, reason_payload,
  idempotency_key, actor, now
) -> result

OperationalStateStore.finish_attempt_execution(
  attempt_id, expected_attempt_version, expected_packet_version,
  expected_lease_version, execution_handle, outcome, result_commit,
  completion_evidence_reference, reason_payload,
  idempotency_key, actor, now
) -> result
```

Every `attempt`, `packet`, `lease`, or lock value below is exactly the existing
five-key state payload. Timing facts use separately named objects and never add
keys to a state payload. Lock arrays are ordered by `entity_id`.

### Heartbeat result and event

Heartbeat requires the exact handle, Running attempt, Running packet, Running
parent run, and Active lease. `now` is strictly later than both stored attempt
and lease heartbeat. `new_expires_at` is strictly later than `now` and the
stored lease expiry. It advances attempt heartbeat/version and lease
heartbeat/expiry/version once; packet, run, and locks do not change.

Exact result, with versions derived from supplied expected versions plus one:

```json
{
  "attempt":{"entity_id":"attempt-id","entity_type":"Attempt","kind":"state","state":"Running","version":3},
  "execution":{"attempt_id":"attempt-id","execution_handle":"provider-job-id","heartbeat_at":"now"},
  "lease":{"entity_id":"lease-id","entity_type":"Lease","kind":"state","state":"Active","version":2},
  "renewal":{"expires_at":"new-expires-at","heartbeat_at":"now","lease_id":"lease-id"}
}
```

One event is inserted with `entity_type=Lease`, `entity_id=lease-id`, and
`event_type=LeaseHeartbeatRecorded`. Its `before_json` has exact keys
`attempt`, `execution`, `lease`, and `renewal`; execution contains
`attempt_id`, `execution_handle`, and the old attempt `heartbeat_at`; renewal
contains the old lease `expires_at`, old lease `heartbeat_at`, and `lease_id`.
Its `after_json` equals the exact result.

### Finish result and event

Finish requires the exact handle, Running attempt, Running packet, Running
parent run, and Active lease. Its closed mapping is:

| Outcome | Packet | Lease | Locks | Result commit | Time rule |
|---|---|---|---|---|---|
| `Succeeded` | `AwaitingIntegration` | `Released` | `Released` | required full lowercase 40-hex | `now <= expires_at` |
| `Failed` | `NeedsReplan` | `Released` | `Released` | null | `now <= expires_at` |
| `Cancelled` | `Cancelled` | `Cancelled` | `Released` | null | `now <= expires_at` |
| `TimedOut` | `NeedsReplan` | `Expired` | `Expired` | null | `now > expires_at` |
| `Stale` | `NeedsReplan` | `Released` | `Released` | null | `now <= expires_at` |

It sets attempt state, `finished_at=now`, `result_commit`, and the exact
completion evidence reference; updates packet state; closes the lease and all
its Active locks with `released_at=now`; increments each changed row once; and
returns only:

```json
{
  "attempt":{"entity_id":"attempt-id","entity_type":"Attempt","kind":"state","state":"Succeeded","version":4},
  "completion":{"attempt_id":"attempt-id","completion_evidence_reference":"evidence-ref","execution_handle":"provider-job-id","finished_at":"now","result_commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "lease":{"entity_id":"lease-id","entity_type":"Lease","kind":"state","state":"Released","version":3},
  "locks":[{"entity_id":"lock-id","entity_type":"ResourceLock","kind":"state","state":"Released","version":2}],
  "packet":{"entity_id":"packet-id","entity_type":"Packet","kind":"state","state":"AwaitingIntegration","version":8}
}
```

For non-success outcomes `result_commit` is JSON null and all states follow the
table. One event has `entity_type=Attempt`, `entity_id=attempt-id`, and
`event_type=AttemptStateChanged`. Its `before_json` has exact keys `attempt`,
`execution`, `lease`, `locks`, and `packet`; execution contains `attempt_id`,
`execution_handle`, `expected_result`, and the stored attempt `heartbeat_at`.
Its `after_json` equals the exact result.

## Fingerprints, precedence, and errors

Fingerprints are SHA-256 over UTF-8 canonical JSON of these exact objects;
`actor` has exact keys `actor_id`, `actor_type`, `causation_event_id`, and
`correlation_id`. `reason` is the validated reason payload. `now` is excluded.

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"heartbeat_attempt_execution","payload":{"attempt_id":"...","execution_handle":"...","expected_attempt_version":2,"expected_lease_version":1,"new_expires_at":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."}}}
```

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"finish_attempt_execution","payload":{"attempt_id":"...","completion_evidence_reference":"...","execution_handle":"...","expected_attempt_version":3,"expected_lease_version":2,"expected_packet_version":7,"outcome":"Succeeded","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."},"result_commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}
```

Validate signature-order values, outcome/commit and timestamp relationships,
reason, key, actor, and fingerprint before writing. Malformed input raises
`InvalidRecord`. Then use one `BEGIN IMMEDIATE` transaction with this exact
order: replay/conflict; attempt existence; attempt version; attempt state;
handle match; packet existence/relationship; packet version when finish;
packet state; lease existence/relationship; lease version; lease state; parent
run existence/relationship; parent run state; heartbeat/expiry time rules;
load Active lease locks ordered by ID when finish; update rows; event; commit.

Exact replay is resolved before mutable/time checks and returns the original
result/time. Changed-fact key reuse raises `IdempotencyConflict`. Missing or
mismatched entities raise `InvalidRecord`; stale versions or handle mismatch
raise `StaleState`; wrong states or time rules raise `InvalidTransition`;
SQLite busy exhaustion raises `ResourceBusy`; all integrity failures raise
`InvalidRecord`. Rejected commands and event failures leave all rows/events
unchanged. Concurrent commands from one version have one winner.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_execution_heartbeat_and_finish.py
```

No schema migration, execution start, new state/event type, progress writer,
CLI, launcher, provider adapter, scheduler, recovery service, review/completion
aggregator, learning record, Git/GitHub, Atlas, notification delivery,
external/live project action, or M1-03 is allowed.

## Named sufficient proof

The new test module contains exactly fifteen tests proving:

1. valid heartbeat returns the exact result and renews only attempt/lease;
2. heartbeat wrong handle, missing relationships, wrong states, or stopped run blocks;
3. heartbeat stale versions and non-monotonic/invalid expiry block;
4. heartbeat replay/conflict is exact;
5. heartbeat event failure and concurrent heartbeat cannot partially renew;
6. each of five finish outcomes exactly follows the closed mapping;
7. success requires a full commit and other outcomes prohibit one;
8. finish wrong handle, missing relationship, wrong states, or stopped run blocks;
9. finish stale versions and outcome time rules block;
10. finish closes exactly the active lease lock set in sorted order;
11. finish replay/conflict is exact;
12. finish event failure rolls back every attempt/packet/lease/lock update;
13. concurrent finishes have one winner and no loser residue;
14. restart preserves terminal state and replay without active ownership; and
15. independent heartbeat/finish fingerprints and event envelopes match exactly.

Run the complete existing 220-test inventory plus the fifteen new tests; run
tests 5, 12, 13, and 14 in ten fresh processes; compile with external pycache;
and run exact diff, allowlist, staged, tracked/untracked, artifact, and
sensitive-value checks.

## M0-D12 quality contract

1. **Protected outcome:** only the exact live execution can extend ownership or
   finish, and no duplicate, stale, interrupted, expired, or restarted command
   can split attempt, packet, lease, lock, and event truth.
2. **Operating and threat model:** one trusted local writer and SQLite database,
   validated observations, concurrent threads/processes, crash before commit,
   duplicate/stale events, lease expiry, and service restart.
3. **Explicit exclusions:** provider truthfulness, database corruption, hostile
   same-UID/root mutation, multi-host writers, launch/termination, network
   truth, distributed consensus, and physical machine reboot.
4. **Assurance level:** closed finite mapping and local atomic/idempotent proof
   with failure seams, contention, restart, and independent reconstruction.
5. **Acceptance proof:** the fifteen named tests, complete 235-test inventory,
   ten-run stress group, compile, candidate-union, allowlist, staged hygiene,
   artifact, and sensitive-value checks are sufficient.
6. **Implementation boundary:** only the two named paths, Python standard
   library, and existing Maestro helpers; no dependency or process.
7. **Proportionality ceiling:** two methods and one fifteen-test module; no
   schema, generic lifecycle framework, executor abstraction, background
   service, policy change, or other command.
8. **Stop and escalation rule:** return to the Project Architect on any need
   for another state, command, carrier, path, event, dependency, external fact,
   or work beyond this ceiling. At most one planning and one implementation
   correction. Merge uses standing point-1 authority only after exact-candidate
   readiness and independent approval.
