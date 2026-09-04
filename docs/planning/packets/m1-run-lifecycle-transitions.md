# M1 Run Lifecycle Transitions

**Slice ID:** `MB-SLICE-M1-RUN-LIFECYCLE-01`
**Status:** `Pending Decision Fidelity review`
**Planning and implementation base:**
`07cb48123bdc0d94ebe656fa93a17a3d1309581b`
**Outcome authority:** the Owner's direction to complete M1; the current
development status and both handoffs; the Bootstrap Convergence Policy; the
Master Plan; M0-D01, M0-D05, and M0-D12; and the Agent Workforce Control
Plane. The accepted real M1-M4 direction in repository history is recovery
evidence for milestone order, not a file-import source.

Terminal `MB-SLICE-M1-02B-REPLACEMENT-01` is not reopened, replaced, renamed,
corrected, or used as authority. This is a new independent slice derived from
the integrated schema-4 `runs`, `events`, and public store contracts on current
master.

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-RUN-LIFECYCLE-01` |
| `phase` | `PendingDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:07cb48123bdc0d94ebe656fa93a17a3d1309581b"]` |

Counts never reset. A reviewer is launched only after a successful mechanical
readiness result. Status-only commits outside the frozen implementation range
may update this table.

## Project Architect selection

The smallest executable continuation is one guarded, durable run transition.
Current master can create and read a `Planned` run but cannot change its state;
therefore it cannot truthfully record that coordination started, blocked,
waited for authority, completed, or was cancelled. Implementing packet claims,
leases, recovery, notifications, repository operations, or project
create/register before this primitive would depend on an absent state-change
boundary.

## One executable outcome

Add this public service-owned method:

```text
OperationalStateStore.transition_run(
  run_id, expected_version, target_state, reason_payload,
  idempotency_key, actor, now
) -> state_payload
```

`state_payload` is exactly:

```json
{"entity_id":"...","entity_type":"Run","kind":"state","state":"...","version":2}
```

The method validates all inputs before writing, opens one `BEGIN IMMEDIATE`
transaction, resolves an exact idempotent replay before checking mutable state,
compares `expected_version`, applies exactly one permitted edge, increments the
version once, sets `updated_at`, appends exactly one `RunStateChanged` event
with exact before/after state payloads and the caller's validated closed
`reason` payload, commits, and returns the after payload.

The permitted directed edges are the complete graph for this slice:

```text
Planned -> Running | Blocked | Cancelled
Running -> Blocked | AwaitingArchitect | AwaitingOwner | Complete | Cancelled
Blocked -> Running | AwaitingArchitect | AwaitingOwner | Cancelled
AwaitingArchitect -> Running | Blocked | AwaitingOwner | Cancelled
AwaitingOwner -> Running | Blocked | Complete | Cancelled
Complete -> no state
Cancelled -> no state
```

Self-transitions and every unlisted edge raise `InvalidTransition`. A missing
run raises `InvalidRecord`. A version mismatch raises `StaleState`. Reuse of an
idempotency key with different immutable command facts raises
`IdempotencyConflict`. SQLite busy exhaustion remains `ResourceBusy`.

An event-insert failure rolls back the state update. Two concurrent commands
from one expected version produce one committed winner and one stale result;
they never create two transitions. After restart, replay of the winning command
returns its original after payload without another version or event.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_run_lifecycle.py
```

No schema migration or change to an existing table, trigger, state vocabulary,
CLI, packet/attempt/lease/lock/wait/notification/review/acceptance behavior,
recovery loop, repository operation, registration flow, external access,
live-project behavior, Atlas, scheduler, service, deployment, or merge is
permitted.

## Named sufficient proof

`tests/m1_02/test_run_lifecycle.py` contains exactly fourteen named tests that
prove:

1. accepted creation produces the required Planned/version-1 baseline;
2. Planned to Running succeeds;
3. Running to Complete succeeds;
4. Blocked and authority-wait paths resume only through listed edges;
5. Complete and Cancelled are terminal;
6. every representative unlisted or self edge is rejected without mutation;
7. stale expected version is rejected without mutation;
8. a missing run is rejected without an event;
9. same-key/same-command replay returns the original result exactly once;
10. same-key/different-command reuse is rejected;
11. one transition writes exactly one event with exact before, after, reason,
    actor, correlation, causation, fingerprint, entity, and event type;
12. forced event insertion failure rolls back the run update and event;
13. two concurrent transitions at one version have exactly one winner; and
14. restart preserves state/version/event and makes replay nonduplicating.

Run the existing Alpha-01 11, Alpha-02 7, Alpha-03 56, M1-01 27, M1-02 35,
and review-readiness 27 tests, the new 14-test suite, and:

```text
python -m compileall -q services/maestro/maestro tests/m1_02
git diff --check BASE..HEAD
```

All 177 tests, compilation, exact two-path confinement, clean staged/unstaged/
untracked state, and the mechanical implementation-review readiness gate must
pass. Passing this inventory is enough.

## Bounded quality contracts

### Q1 — Atomic run lifecycle

- **Protected outcome:** every accepted run transition changes state/version
  and appends its one audit event atomically.
- **Operating/failure model:** stale callers, invalid edges, event failure,
  transaction rollback, and SQLite busy exhaustion on one Linux service writer.
- **Exclusions:** packet or worker lifecycle, distributed writers, hostile
  same-UID database tampering, and recovery orchestration.
- **Assurance level:** closed graph, optimistic version comparison, immediate
  transaction, durable event, and real SQLite tests.
- **Acceptance proof:** named tests 1–8 and 11–13 plus all regressions pass.
- **Implementation boundary:** one store method and private helpers in the
  existing operational-state module; no migration.
- **Proportionality ceiling:** no generic workflow engine or new abstraction
  outside the two allowed files.
- **Stop rule:** any new state, schema change, cross-entity mutation, or
  undefined edge returns to the Project Architect.

### Q2 — Idempotent restart and contention behavior

- **Protected outcome:** retry, restart, and simultaneous callers cannot
  duplicate or contradict one logical transition.
- **Operating/failure model:** duplicate delivery, conflicting key reuse,
  process reopen, and two threads using the same expected version.
- **Exclusions:** multi-host consensus, network partitions, and automatic
  redispatch.
- **Assurance level:** durable command fingerprint plus SQLite serialization
  and exact replay result.
- **Acceptance proof:** named tests 9, 10, 13, and 14 pass repeatedly with one
  final row and one event.
- **Implementation boundary:** reuse existing event/idempotency and connection
  facilities; no in-memory authority or cache.
- **Proportionality ceiling:** one-run transitions only.
- **Stop rule:** any replay requires inferred mutable state, creates another
  event, or depends on process memory returns the slice.

### Q3 — Authority and scope confinement

- **Protected outcome:** the method records only an already-authorized run
  state choice and cannot select work or create an external effect.
- **Operating/failure model:** accidental expansion into packet control,
  dispatch, claims, notifications, registration, repository/network, or merge.
- **Exclusions:** every later M1 capability requiring those effects.
- **Assurance level:** two-path allowlist, complete diff inspection, and
  regression proof.
- **Acceptance proof:** exact changed paths, no imports or calls for excluded
  effects, 177 tests, compile, and readiness pass.
- **Implementation boundary:** existing local SQLite service boundary only.
- **Proportionality ceiling:** no public CLI or additional lifecycle entity.
- **Stop rule:** any external authority, credential, live-project access,
  product redesign, or terminal M1-02B dependency returns before review.

## Review and terminal behavior

The slice receives one complete pre-execution Decision Fidelity review, at
most one planning correction and targeted verification, one independent
implementation review, and at most one implementation correction and targeted
verification. The readiness gate must return `ready: true` before either
reviewer is launched; a blocked gate launches nobody and consumes no allowance.

The Project Architect dispositions every implementation finding as `correct
now`, `accept known limitation`, `reject finding`, or `return slice`. Only
`correct now` reaches the Developer. Critical exceptions, primary-outcome
failure, unverifiable coverage, and reserved Owner risk cannot be deferred.
No role may reopen terminal M1-02B, add new scope after the frozen proof passes,
repeat a completed review, select successor work, or merge without current
authority. A failed targeted verification terminally returns this slice.
