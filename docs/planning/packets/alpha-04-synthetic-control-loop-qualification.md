# Alpha-04 — Execute Synthetic Control-Loop Qualification

**Status:** DRAFT READINESS PACKET — not Decision-Fidelity reviewed, approved,
released, or authorized for implementation  
**Owner:** Jeremy Miedreich  
**Packet ID:** `maestro-alpha-04-control-loop-qualification`  
**Graph node:** `MAESTRO-ALPHA-04-CONTROL-LOOP-QUALIFICATION`  
**Graph revision:** `maestro-alpha-04-plan-r2`  
**Architecture plan:** [Alpha-04 synthetic control-loop qualification](../proposed/alpha-04-synthetic-control-loop-qualification.md), merged through PR #12 at `b2594d9ab4cad528cd6272622f68162850a0584e`  
**Decision authority:** [M0-D13](../decisions/m0-d13-synthetic-control-loop-qualification.md) and [M0-D14](../decisions/m0-d14-context-and-token-reporting.md)  
**Readiness direction:** [2026-09-01 Alpha-04 readiness direction](../../../sources/planning/2026-09-01-alpha-04-readiness-direction.md)  
**Exact source base:** `8aa4cb517dcb902060cf5acd1d58806787e03841` (`origin/master`)  
**Execution class:** one fixture-only, single-process implementation in a clean isolated worktree  
**Worker route after release:** Local Qwen  
**Independent implementation-review route:** GPT-5.6 Terra at high reasoning  
**Decision Fidelity route:** GPT-5.6 Sol at high reasoning  
**Safe parallelism:** none; one exclusive Alpha control-loop/schema lock

**Owner packet-review approval:** On 2026-09-01 the Owner approved this draft
to be committed and routed to fresh independent Decision Fidelity Review. This
approval does not accept the packet as implementation authority and does not
release implementation.

## Release gate and current non-authorization

This draft is readiness work only. Before implementation, this exact packet must:

1. receive independent Decision Fidelity `APPROVE` over an exact base/head range;
2. record explicit Owner packet acceptance;
3. merge as a planning-only release; and
4. receive a separate explicit Owner implementation release naming the exact
   packet revision and implementation base.

Until all four conditions are recorded, do not dispatch Local Qwen, change
application code, create operational queue state, invoke a model/provider,
access a real project, or perform implementation review.

## Predecessor reconciliation

Alpha-03 is complete at Owner-accepted corrected head
`f21e4a2ff25cead8b972b4433da33f0e9910efc5` and merged to `master` through
`8aa4cb517dcb902060cf5acd1d58806787e03841`. Its full and targeted independent
implementation reviews returned `REQUEST_CHANGES`; the Owner then accepted the
exact result with one trusted-fixture-only limitation. This packet treats the
predecessor as satisfied by that explicit Owner closeout and does **not** claim
an independent-review approval.

Alpha-04 must create its own valid, repository-owned binding fixture from the
confirmed values in `fixtures/alpha/project-discovery/complete-snapshot.json`.
It may not use the malformed conflict case accepted as an Alpha-03 limitation
and may not claim complete rejection of empty required arrays inside conflict
observations.

## Outcome

Extend the existing `maestro run-packet` synthetic-only path so one fully
validated Alpha-04 fixture sequence proves that Maestro can:

1. project an approved synthetic graph into honest queue states;
2. select only the highest-ranked `Dispatchable` candidate and record every
   higher-ranked skip reason;
3. atomically create one attempt/lease and one complete lock set;
4. preserve allowance, model, context, token, cost, and local-capacity facts
   without inventing unavailable precision;
5. ask a non-terminal worker for bounded status before assuming a stall;
6. request one safe-boundary checkpoint at declared context pressure;
7. route a scripted worker result through the declared Integration mode and a
   genuinely separate synthetic reviewer identity;
8. permit no more than one exact targeted correction;
9. recover idempotently from duplicates, restart, timeout, expiry, contention,
   and stale observations; and
10. move an approved result to `MergeReady`, then `AwaitingOwner`, and stop.

All worker, Integration, review, usage, account-window, and executor facts are
fixed JSON observations. Maestro makes the next-action decisions but does not
generate the judgments represented by those observations.

## Exact command surface

`maestro run-packet` remains the only packet execution command. Alpha-04 adds no
daemon, scheduler command, direct database command, Atlas command, model
command, provider command, or second control surface.

An Alpha-04 packet adds one required safe-basename field:

```json
"control_loop_fixture": "happy-path.json"
```

The referenced file must resolve beneath `fixtures/alpha/control-loop/` without
absolute paths, separators, traversal, missing files, or symlink escape. The
complete packet and control-loop fixture must validate before a packet claim,
SQLite mutation, fixture-worktree creation, or executor action.

## Exact packet fixtures

Implementation creates these repository-owned packet inputs:

| Packet fixture | Control-loop fixture | Required terminal result |
| --- | --- | --- |
| `fixtures/alpha/alpha-04-happy-path-packet.json` | `happy-path.json` | `AwaitingOwner` |
| `fixtures/alpha/alpha-04-correction-packet.json` | `one-correction.json` | `AwaitingOwner` after one targeted correction and targeted review |
| `fixtures/alpha/alpha-04-assemble-packet.json` | `integration-assemble.json` | `AwaitingOwner` with distinct Integration result lineage |
| `fixtures/alpha/alpha-04-replan-packet.json` | `integration-replan.json` | `NeedsReplan` / `ProjectArchitectReturn` |

The first fixture carries the complete happy path, patient-status sequence,
context checkpoint, allowance reconciliation, and recovery observations. The
other three vary only the bounded branch needed to prove correction and
Integration routing.

## Exact control-loop fixture contract

Every control-loop fixture is a strict JSON object with exactly these root
fields; unknown fields are invalid:

```text
schema_version, fixture_id, binding, authority, policy, actors, candidates,
available_locks, available_resources, allowance_window, attempt_preflight,
observations, expected
```

`schema_version` is the integer `1`. Stable identifiers are lowercase ASCII
`[a-z][a-z0-9-]{2,63}`. Timestamps are UTC RFC 3339 strings ending in `Z` and
must be nondecreasing within an observation sequence. Finite numbers are JSON
integers or decimals, never strings, NaN, or infinity. Unknown keys, duplicate
IDs, invalid enums, inconsistent arithmetic, or references to absent objects
are malformed and rejected before mutation.

### Binding and authority

`binding` contains exactly:

```json
{
  "binding_id": "alpha-04-valid-binding",
  "alpha_03_result_head": "f21e4a2ff25cead8b972b4433da33f0e9910efc5",
  "source_fixture": "complete-snapshot.json",
  "fixture_sha256": "fd6b71dfbda5c0a38565ba12c6e2925c55a82a96a33e50afe30bd01a72e6d086",
  "areas": {"<the exact seven normalized Alpha-03 binding areas>": {}}
}
```

The implementation fixture must contain the complete normalized values, not an
ellipsis. `areas` must pass the corrected Alpha-03 confirmed-value validation
for Identity, Authority, Delivery, Verification, Roles, Operations, and
Exceptions. `authority.architecture_paths` and `authority.plan_paths` must each
be non-empty. No `conflicts`, inventory statuses, secret values, external
repository path, or real account credential is permitted.

`authority` contains exactly:

```json
{
  "graph_revision": "maestro-alpha-04-fixture-r1",
  "authority_reference": "M0-D13+M0-D14+alpha-04-packet",
  "source_base": "8aa4cb517dcb902060cf5acd1d58806787e03841",
  "approved": true,
  "project": "Maestro"
}
```

Changing any fixed authority value, supplying `approved: false`, or omitting
the binding makes the fixture invalid before mutation.

### Policy

`policy` contains exactly:

```json
{
  "status_min_interval_seconds": 60,
  "status_response_timeout_seconds": 30,
  "lease_timeout_seconds": 900,
  "max_targeted_corrections": 1,
  "owner_stop_status": "AwaitingOwner",
  "status_transport": "non_interrupting_fixture_adapter",
  "timeout_reconciliation": "durable_plus_executor_facts",
  "context_pressure_action": "request_one_checkpoint_then_follow_stop_threshold"
}
```

The implementation supports these fixed qualification values only; it does not
introduce configurable production scheduling policy.

### Actors

`actors` is a non-empty array of exact objects:

```json
{
  "actor_id": "fixture-worker-01",
  "role": "Worker | Integration | IndependentReviewer",
  "route": "scripted-local-adapter | validate-only | assemble | replan | scripted-independent-review",
  "may_change_result": true,
  "synthetic": true
}
```

There is exactly one Worker, one Integration actor, and one
IndependentReviewer. All IDs differ. The reviewer must differ from every actor
whose `may_change_result` is true. `synthetic` must be true. No provider
credential, executable command, prompt, transcript, network endpoint, real
repository identity, or arbitrary route is allowed.

### Candidates and queue projection

`candidates` is an array of two through eight objects ordered by unique positive
integer `rank`:

```json
{
  "candidate_id": "candidate-ready",
  "rank": 3,
  "released": true,
  "same_role_predecessor_complete": true,
  "hard_dependencies_complete": true,
  "review_gates_complete": true,
  "required_contracts_available": true,
  "required_route_available": true,
  "route_currently_eligible": true,
  "base_compatible": true,
  "hold_clear": true,
  "required_locks": ["path:services-maestro", "shared:sqlite-schema"],
  "required_resources": {"synthetic-worker-slot": 1},
  "expected_state": "Dispatchable",
  "expected_reason": "all dispatchability conditions satisfied"
}
```

Projection is mechanical and uses this precedence:

1. `released: false` -> `Planned`.
2. Released with an incomplete same-role predecessor -> `Waiting`.
3. Released with any incomplete hard dependency or review gate, unavailable
   contract, or absent required route contract -> `Blocked`.
4. Otherwise -> `Ready`.
5. `Ready` becomes `Dispatchable` only when its current route is eligible, base
   and hold are compatible/clear, and every declared lock and resource unit is
   available.

A base mismatch, active hold, lock conflict, or finite-resource shortage stays
`Ready` but is not `Dispatchable`, with the exact failed condition recorded.
The chosen candidate is the lowest-rank-number `Dispatchable` candidate. The
fixture must contain at least one higher-ranked non-dispatchable candidate and
exactly one expected selected candidate. The selected candidate declares at
least one `path:` lock, one `shared:` boundary lock, and one finite resource.
Maestro records all candidate states, all higher-ranked skip reasons, and the
selection inputs without rewriting rank, dependencies, or authority.

`available_locks` is an object whose unique stable lock IDs map to exactly
`{"available": <boolean>, "holder": <stable attempt ID or null>}`. Available
locks require a null holder; unavailable locks require a non-null fixture
holder. `available_resources` maps stable resource IDs to nonnegative integer
available capacity. Every required lock/resource name must be declared and must
not contain a filesystem path outside the fixed synthetic namespace.

### Allowance window and reconciliation

`allowance_window` contains exactly:

```json
{
  "provider": "openai",
  "account_reference": "fixture-workspace",
  "window_type": "chatgpt-codex-weekly",
  "unit": "percentage_points",
  "before": {"used": 40.0, "remaining": 60.0, "observed_at": "2026-09-01T12:00:00Z"},
  "after": {"used": 45.0, "remaining": 55.0, "observed_at": "2026-09-01T12:10:00Z"},
  "reset_at": "2026-09-07T00:00:00Z",
  "precision": "coarse",
  "measurement_quality": "fixture-supported",
  "freshness": "fresh",
  "tracked_controlled_usage": 2.0,
  "registered_coarse_usage": 1.0,
  "unattributed_remainder": 2.0,
  "pace": {"state": "estimated", "value": 0.5, "unit": "percentage_points_per_minute"}
}
```

The exact fixture arithmetic is:

```text
observed change = 45.0 - 40.0 = 5.0 percentage points
2.0 tracked + 1.0 coarse + 2.0 unattributed = 5.0
```

The raw before/after facts are retained. Used plus remaining must equal `100.0`
within exact decimal normalization. Pace is permitted only for fresh supported
observations with usable timing and is reporting-only. An unsupported fixture
uses `measurement_quality: unavailable`, sets before/after/reset/pace and all
three reconciliation components to `null`, and causes no routing decision.

Attempt tokens are never inserted into this percentage equation. Local Qwen
capacity is recorded under attempt preflight and never subtracted from this
window. Negative reconciliation, forced attribution, token-to-percentage
conversion, stale pace, or parent/child double counting is invalid or retained
as an explicit unavailable/stale result according to the test case; it never
changes routing in Alpha-04.

### Attempt preflight

`attempt_preflight` contains exactly:

```json
{
  "model": {
    "provider": "openai",
    "model_id": "fixture-hosted-model",
    "runtime_id": "scripted-local-adapter-v1",
    "context_limit_tokens": 32768,
    "quantization": "not_applicable"
  },
  "context": {
    "packet_minimum_tokens": 24576,
    "known_input": {"value": 8000, "measurement_type": "runtime_reported", "confidence": "high"},
    "future_growth": {"minimum": 2000, "maximum": 4000, "measurement_type": "estimated_range", "confidence": "medium"},
    "output_reserve_tokens": 4096,
    "warning_remaining_tokens": 8192,
    "checkpoint_remaining_tokens": 6144,
    "stop_remaining_tokens": 4096,
    "counting_method": "fixture_runtime_measurement"
  },
  "tokens": {
    "input": {"state": "exact", "value": 8000},
    "cached_input": {"state": "unavailable", "value": null},
    "output": {"state": "unavailable", "value": null},
    "reasoning": {"state": "unavailable", "value": null},
    "total": {"state": "unavailable", "value": null}
  },
  "cost": {"state": "unknown", "amount": null, "currency": null},
  "local_capacity": {
    "provider": "local-qwen",
    "state": "available",
    "capacity_unit": "serialized_fixture_slot",
    "capacity": 1,
    "observed_at": "2026-09-01T12:00:00Z"
  }
}
```

Preflight passes only if the configured context is at least the packet minimum
and `known_input.value + future_growth.maximum + output_reserve_tokens` is no
greater than the configured limit. Thresholds must satisfy:

```text
context limit > warning > checkpoint > stop >= output reserve > 0
```

An undersized context, oversized starting upper bound, malformed fingerprint,
invalid thresholds, unsupported claim of exactness, or cost state inconsistent
with amount/currency fails before assignment or mutation. Cost states are
`billed`, `estimated`, `not_billed`, or `unknown`; only the first two require a
nonnegative amount and three-letter currency, while the latter two require
both fields to be null.

Token fields are distinct. Their states are `exact`, `estimated`, or
`unavailable`; unavailable requires null and the other states require a
nonnegative integer. A later valid `runtime_reported` observation supersedes an
estimate only for the same period. Zero reasoning tokens never sets input,
output, total, or context use to zero.

### Observation script

`observations` is an ordered array. Each observation has exactly
`event_id`, `event_type`, `attempt_id`, `actor_id`, `observed_at`, `received_at`,
`idempotency_key`, and `payload`. IDs and idempotency keys are unique except an
intentional duplicate case, which must repeat the original event byte-for-byte.
The attempt ID must match the active attempt unless the event is an explicitly
expected stale/wrong-attempt test.

Permitted event types and payloads are:

- `worker_status_requested`: request ID and the five required question fields;
- `worker_status_reported`: request ID, ordered plan, current step,
  `actively_progressing`, blocker disposition/details, ETA state/value/unit/
  confidence, context/usage snapshot, and worker observation time;
- `status_response_boundary`: request ID plus durable attempt state, executor
  state, lease state, and expected next action;
- `checkpoint_requested`: one checkpoint ID and the pressure observation;
- `checkpoint_reported`: completed work, current plan/step, changed synthetic
  artifacts, checks/evidence, blocker, and next action;
- `worker_completed`: attempt/base/result identity, changed synthetic paths,
  named checks, evidence references, token/cost snapshot, and correction round;
- `integration_completed`: mode, Integration actor, input/result identity,
  changed paths, checks, evidence, and disposition;
- `review_completed`: reviewer actor, reviewed result, outcome, named findings,
  evidence, and correction round;
- `correction_assigned` and `correction_completed`: exact finding IDs, original
  lineage, correction result/diff/evidence, and correction count;
- `lease_expired`, `competing_claim`, `duplicate_event`, `stale_completion`, and
  `restart_reconcile`: the durable facts and expected no-corruption decision.

The exact payload key sets are:

| Event type | Exact payload keys |
| --- | --- |
| `worker_status_requested` | `request_id`, `questions` |
| `worker_status_reported` | `request_id`, `plan_steps`, `current_step_id`, `actively_progressing`, `blocker`, `eta`, `context_usage`, `worker_observed_at` |
| `status_response_boundary` | `request_id`, `durable_attempt_state`, `executor_state`, `lease_state`, `decision` |
| `checkpoint_requested` | `checkpoint_id`, `pressure`, `safe_boundary` |
| `checkpoint_reported` | `checkpoint_id`, `completed_work`, `plan_steps`, `current_step_id`, `changed_artifacts`, `checks`, `evidence_references`, `blocker`, `next_action` |
| `worker_completed` | `base_identity`, `result_identity`, `changed_paths`, `checks`, `evidence_references`, `token_cost_observation_id`, `correction_round` |
| `integration_completed` | `mode`, `input_result_identity`, `result_identity`, `changed_paths`, `checks`, `evidence_references`, `disposition` |
| `review_completed` | `reviewed_result_identity`, `outcome`, `finding_ids`, `evidence_references`, `correction_round` |
| `correction_assigned` | `finding_ids`, `original_attempt_id`, `original_result_identity`, `correction_round` |
| `correction_completed` | `finding_ids`, `original_attempt_id`, `original_result_identity`, `result_identity`, `changed_paths`, `checks`, `evidence_references`, `correction_round` |
| recovery event types | `durable_state`, `observed_state`, `referenced_attempt_id`, `referenced_event_id`, `decision`, `reason` |

`questions` must equal the ordered array `ordered_plan`, `current_step`,
`actively_progressing`, `blocker`, `eta`. `plan_steps`, changed paths/artifacts,
checks, findings, and evidence references are bounded arrays of unique non-empty
strings. `blocker` is exactly `{"state": "none", "details": null}` or
`{"state": "reported", "details": "<non-empty text>"}`. `eta` is exactly
`{"state": "reliable", "value": <positive integer>, "unit": "seconds",
"confidence": "low|medium|high"}` or `{"state": "unknown", "value": null,
"unit": null, "confidence": "none"}`. `context_usage` references one valid
attempt-usage observation and repeats only its bounded limit/used/remaining/
reserve/measurement/confidence/pressure facts.

Review outcomes are `APPROVE` or `REQUEST_CHANGES`; Integration dispositions
are `validated`, `assembled`, or `needs_replan`. Correction round is zero for
the original result and one for the only permitted correction. Recovery
decisions are `ignore_duplicate`, `ignore_stale`, `remain_running`,
`preserve_terminal`, or `project_architect_return`; they cannot directly create
an attempt or release a lock.

The happy fixture uses this deterministic patient-status sequence:

1. one status request receives a reliable ETA;
2. a later request receives explicit ETA `unknown`;
3. a later request receives no immediate response;
4. at 30 seconds the response-boundary observation reports a healthy executor
   and unexpired lease, so the attempt remains `Running` with no interrupt,
   retry, expiry, or duplicate assignment;
5. the context remaining value later crosses `6144`, causing one checkpoint
   request at the next safe boundary; and
6. the checkpoint is recorded before the scripted completion continues.

Only one status request may be outstanding. A new request before 60 seconds,
duplicate outstanding request, stale reply, or wrong-attempt reply cannot
replace current evidence or change the attempt. Worker status never exposes a
prompt, transcript, trace, or hidden reasoning.

### Integration, review, correction, and Owner stop

The active attempt moves through this bounded state sequence:

```text
Dispatchable -> Leased -> Running -> AwaitingIntegration
-> AwaitingReview -> MergeReady -> AwaitingOwner -> STOP
```

Integration behavior is exact:

- `validate-only` records verification without changing result identity;
- `assemble` requires the distinct Integration actor, records a new result
  identity and its changed synthetic paths, and then routes that result;
- `replan` records `NeedsReplan` and `ProjectArchitectReturn`, then stops.

Review `APPROVE` is accepted only from the declared IndependentReviewer whose
identity differs from every result-changing actor. It moves the result to
`MergeReady`, then immediately records `AwaitingOwner` and stops. There is no
`Merged`, `Complete`, successor-selection, or external action transition.

Review `REQUEST_CHANGES` may create one correction only when every finding is a
named, committed, in-scope gate failure. The correction retains the original
attempt lineage, increments correction count from zero to one, names the exact
finding IDs, and receives targeted review of the correction-only diff. A second
correction, new failure class, scope breach, missing architecture contract, or
unrelated change records `ProjectArchitectReturn` and stops without another
assignment.

## Explicit Project Architect return contract

Alpha-04 must never emit a bare `escalate` result. When operational rules cannot
determine one safe next action because the project authority or packet is
insufficient, it records:

```json
{
  "status": "NeedsReplan",
  "handoff_kind": "ProjectArchitectReturn",
  "reason_code": "IntegrationReplan",
  "reason": "The exact missing boundary or conflict.",
  "evidence_references": ["event:event-integration-replan"],
  "required_decision": "The exact architecture clarification or superseding packet needed.",
  "owner_decision_required": false,
  "safe_stop": "NoFurtherAssignmentOrMutation"
}
```

Permitted `reason_code` values are:

```text
AuthorityMissing
AuthorityConflict
EligibilityAmbiguous
NoUniqueNextAction
IntegrationReplan
ArchitectureContractDefect
ScopeChangeRequired
CorrectionExhausted
NewFailureClass
UnsupportedExternalAccess
ContinuationPolicyMissing
StrongerIsolationRequired
```

The Coordinator retains routine cases whose next action is already specified:
valid waiting/blocked/lock reasons, ordinary pre-timeout silence, a healthy
timeout reconciliation, one eligible targeted correction, duplicate/stale
event rejection, and the normal Integration/review routes.

`owner_decision_required` is true only when resolution changes a material
product/architecture/public contract, security/data/credential/external-access
boundary, accepted risk, spending/budget policy, production/release/merge
authority, priority, or infeasible quality contract. Maestro still returns the
record to the Project Architect, who prepares the facts, options,
recommendation, impact, and safe no-response action for the Owner. Alpha-04 does
not contact the Owner or treat no response as approval.

`AwaitingOwner` is reserved for the successful final acceptance stop. It is not
used as a substitute for an under-specified Project Architect return.

## Durable storage and transition requirements

Increase `SCHEMA_VERSION` from `2` to `3` and add only these Alpha-04 records
through the existing `SQLiteFoundation` service-owned writer:

| Record | Exact logical columns |
| --- | --- |
| `control_loop_runs` | `packet_id`, `fixture_id`, `fixture_digest`, `graph_revision`, `authority_reference`, `source_base`, `selected_candidate_id`, `state`, `correction_count`, `created_at`, `updated_at` |
| `control_loop_queue_entries` | `packet_id`, `candidate_id`, `rank`, `derived_state`, `dispatchable`, `reason`, `selected` |
| `control_loop_attempts` | `packet_id`, `attempt_id`, `attempt_number`, `actor_id`, `base_identity`, `result_identity`, `state`, `lease_acquired_at`, `lease_expires_at`, `context_fingerprint_json`, `original_attempt_id`, `correction_round` |
| `control_loop_locks` | `packet_id`, `attempt_id`, `claim_id`, `claim_kind`, `units`, `state`, `acquired_at`, `released_at` |
| `control_loop_events` | `packet_id`, `attempt_id`, `event_id`, `event_type`, `idempotency_key`, `actor_id`, `prior_state`, `new_state`, `observed_at`, `received_at`, `payload_json`, `decision`, `reason` |
| `worker_status_records` | `packet_id`, `attempt_id`, `request_id`, `request_state`, `plan_json`, `current_step_id`, `actively_progressing`, `blocker_json`, `eta_json`, `context_usage_json`, `observed_at`, `received_at`, `next_permitted_action` |
| `allowance_windows` | `packet_id`, `window_id`, `provider`, `account_reference`, `window_type`, `unit`, `before_json`, `after_json`, `reset_at`, `precision`, `measurement_quality`, `freshness`, `raw_fixture_json` |
| `attempt_usage` | `packet_id`, `attempt_id`, `observation_id`, `model_id`, `runtime_id`, `context_limit`, `quantization`, `packet_minimum`, `output_reserve`, `thresholds_json`, `tokens_json`, `cost_json`, `pressure_state`, `observed_at` |
| `usage_reconciliations` | `packet_id`, `attempt_id`, `reconciliation_id`, `window_id`, `observed_change`, `tracked_usage`, `coarse_usage`, `unattributed_remainder`, `reconciles`, `local_capacity_json`, `pace_json` |
| `control_loop_handoffs` | `packet_id`, `attempt_id`, `handoff_id`, `handoff_kind`, `reason_code`, `reason`, `evidence_references_json`, `required_decision`, `owner_decision_required`, `safe_stop`, `created_at` |

Identifiers, enums, booleans, counts, and timestamps use `TEXT`/`INTEGER` with
`NOT NULL` and `CHECK` constraints matching the fixture contract; decimal
allowance values use canonical decimal strings so binary floating-point cannot
change reconciliation. JSON columns contain canonical sorted-key compact JSON
that has already passed the relevant strict schema. `released_at`,
`result_identity`, `original_attempt_id`, and successful-handoff architecture
fields may be null only in the lifecycle states where the earlier contract says
they do not yet apply. No other nullability is inferred.

Primary keys are, respectively: `packet_id`; `(packet_id, candidate_id)`;
`(packet_id, attempt_id)`; `(packet_id, claim_id)`;
`(packet_id, event_id)` plus unique `(packet_id, idempotency_key)`;
`(packet_id, request_id)`; `(packet_id, window_id)`;
`(packet_id, observation_id)`; `(packet_id, reconciliation_id)`; and
`(packet_id, handoff_id)`. Every child record has a foreign key to its run and,
where present, its active attempt.

Primary/unique keys must make one packet/fixture run, candidate projection,
attempt, lock owner, event idempotency key, status request, usage observation,
and terminal handoff immutable on replay. Foreign keys remain enabled and all
multi-record state transitions use `BEGIN IMMEDIATE` transactions.

The atomic assignment transaction must insert the selected attempt and lease,
reserve every path/shared/resource lock, record the dispatch decision and skip
reasons, and transition the selected queue entry together. If any insert or
reservation fails, the whole transaction rolls back. No partial attempt or lock
set may remain.

Before processing a duplicate, restart, timeout, expiry, competing claim, stale
completion, or wrong-attempt observation, reread the durable run, attempt,
lease, lock, and last accepted event. Such observations must not create a second
active attempt, release another attempt's lock, overwrite terminal evidence, or
advance from a mismatched state.

The stored projection is Atlas-ready but has no Atlas/API/UI writer or reader in
this packet.

## Expected-result assertion contract

`expected` contains exactly:

```json
{
  "queue_states": {"<candidate_id>": "Planned | Waiting | Blocked | Ready | Dispatchable"},
  "selected_candidate_id": "candidate-ready",
  "terminal_status": "AwaitingOwner | NeedsReplan",
  "terminal_handoff": "AwaitingOwner | ProjectArchitectReturn",
  "integration_mode": "validate-only | assemble | replan",
  "correction_count": 0,
  "accepted_event_ids": ["event-001"],
  "ignored_event_ids": [],
  "external_call_count": 0
}
```

The maps and arrays must account for every candidate and scripted event exactly
once. `external_call_count` must be integer zero. The Coordinator recomputes
each value in a pure, non-mutating transition evaluation before assignment; any
mismatch between that computed result and this assertion is an inconsistent
fixture and fails validation before the initial mutation. Expected values never
instruct or override a transition. If later durable runtime facts unexpectedly
diverge from the already validated sequence, Maestro preserves those facts and
records `ProjectArchitectReturn` / `NoUniqueNextAction` rather than guessing.

## Owned implementation paths

Only these paths may change during implementation:

```text
docs/architecture/alpha-04-synthetic-control-loop-qualification.md
docs/operations/alpha-04-synthetic-control-loop-qualification.md
fixtures/alpha/alpha-04-*-packet.json
fixtures/alpha/control-loop/**
services/maestro/maestro/control_loop.py
services/maestro/maestro/control_loop_contract.py
services/maestro/maestro/lifecycle.py
services/maestro/maestro/packet_contract.py
services/maestro/maestro/packet_wrapper.py
services/maestro/maestro/storage.py
tests/alpha_04/test_control_loop_qualification.py
```

`services/maestro/maestro/cli.py`, dependency files, prior fixtures/tests, and
all other paths are forbidden. `run-packet` already exists; if its CLI must
change, or if passing proof requires another path, dependency, service, daemon,
provider SDK, subprocess, network client, Git library, or general scheduler,
stop with `ProjectArchitectReturn` / `ScopeChangeRequired` before making that
change.

## Required implementation behavior

1. Strictly validate the packet, binding, fixture, actors, candidates, policy,
   allowance, preflight, observations, expectations, cross-references,
   arithmetic, and sequence with a pure transition evaluation before mutation.
2. Recompute every expected queue state and expected result; fixture-provided
   `expected` values are assertions, never instructions that override the
   coordinator logic.
3. Perform context/allowance preflight before assignment; unavailable reporting
   remains honest and cannot route work.
4. Atomically select and lease exactly one highest-ranked dispatchable
   candidate with all locks/resources.
5. Replay only the approved fixed observation sequence through explicit
   transition functions; never execute arbitrary fixture commands.
6. Preserve one outstanding status request, patient response-window behavior,
   source/time labels, ETA `unknown`, and one pressure checkpoint.
7. Enforce result lineage, all three Integration routes, independent reviewer
   identity, and one correction maximum.
8. Reconcile duplicates/restarts/stale/timeout/expiry facts from SQLite before
   transition.
9. Record exact `ProjectArchitectReturn` details whenever that route applies.
10. Stop every successful route at `AwaitingOwner`; expose no merge or successor
    action.

## Required tests and sufficient proof

`tests/alpha_04/test_control_loop_qualification.py` must contain named,
independently readable tests proving at least:

1. strict packet/fixture safe-basename and pre-mutation validation, including
   unknown fields, absent authority, malformed IDs/times/enums, inconsistent
   references/arithmetic, secret/external route fields, and a valid Alpha-03
   binding with non-empty required authority arrays;
2. exact `Planned`, `Waiting`, `Blocked`, `Ready`, and `Dispatchable`
   projection plus recorded skip reasons and highest-ranked selection;
3. blocked, unreleased, review-gate-incomplete, route-ineligible,
   base-incompatible, held, lock-conflicting, and resource-conflicting
   candidates cannot be assigned;
4. assignment, attempt, lease, path/shared/resource locks, dispatch decision,
   and queue transition are one atomic idempotent transaction;
5. reliable ETA and explicit `unknown` status records preserve exact worker
   facts and timestamps without interruption/restart/scope change;
6. no immediate reply remains `Running` before the response/lease boundary,
   then reconciles durable plus healthy executor facts without assuming failure
   or creating another attempt;
7. duplicate outstanding requests, too-frequent requests, stale/wrong-attempt
   replies, and duplicate replies cannot replace accepted status evidence;
8. undersized context, oversized known-start upper bound, invalid thresholds,
   and false exact measurements reject before assignment;
9. supported and unavailable OpenAI windows preserve used/remaining/reset,
   precision, quality, freshness, and raw observation without scraping or
   token-to-percentage conversion;
10. `tracked + coarse + unattributed = observed change`, including visible
    unattributed remainder and no parent/child double count;
11. local Qwen capacity remains separate and stale/unknown pace cannot route or
    stop work;
12. exact, estimated, runtime-superseded, unavailable, and confidence states
    remain distinct for every token field; zero/unavailable reasoning never
    erases other context use;
13. billed, estimated, `not_billed`, and `unknown` cost states enforce their
    exact amount/currency contracts;
14. warning/checkpoint pressure produces one safe-boundary checkpoint and the
    declared stop behavior without truncation, summary invention, or session
    replacement;
15. `validate-only`, `assemble`, and `replan` have distinct result lineage and
    handoffs; `replan` records the complete Project Architect return;
16. a worker or Integration actor cannot review its own changed result;
17. one eligible correction retains lineage and gets exact targeted review,
    while a second round, new failure class, scope breach, unrelated change, or
    architecture-contract defect records `ProjectArchitectReturn` and no new
    assignment;
18. restart, duplicate event, competing claim, stale/wrong completion, timeout,
    and lease expiry cannot double-dispatch, release another attempt's locks, or
    overwrite accepted/terminal evidence;
19. every Project Architect reason code produces the exact reason/evidence/
    decision/Owner-flag/safe-stop shape and never a bare escalation; and
20. successful CLI execution records the complete path through Integration and
    independent review to `AwaitingOwner`, with zero external calls and no
    merge, `Complete`, successor, Atlas, provider, Git, GitHub, credential, or
    real-project action.

Passing the named proof is sufficient. Tests must verify coordinator outcomes
from inputs and durable records, not merely repeat constants from the
implementation. No broader production-scheduler, distributed-consensus,
provider, UI, billing, or adversarial same-UID/root proof may be added as a
blocking requirement.

## Required checks

Run from `services/maestro` in the isolated implementation worktree:

```bash
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/alpha_04 -v
python -m maestro.cli run-packet \
  --packet ../../fixtures/alpha/alpha-04-happy-path-packet.json \
  --runtime-dir ../../var/alpha-04-check
```

The CLI proof passes only when it reports `AwaitingOwner`, one selected
candidate/attempt, the declared Integration and independent-review handoffs,
valid allowance/context/usage evidence, and no prohibited action. Also run:

```bash
git diff --check
git status --short
```

Runtime artifacts may exist only beneath the ignored
`var/alpha-04-check/` directory and must not be committed.

## Authority and evidence traceability

| Binding choice | Packet carrier and sufficient proof |
| --- | --- |
| M0-D13 fixed synthetic qualification | Strict repository fixtures, one serial attempt, scripted actors/observations, tests 1–7 and 15–20 |
| M0-D14 preflight-through-status reporting | Exact allowance/context/token/cost/local-capacity schemas and tests 8–14 |
| M0-D05 one correction maximum | Correction lineage and targeted review in test 17; all other contract/scope failures return to the Project Architect |
| M0-D01 service-only SQLite writer | Exact additive tables and transaction boundary; no other writer or direct client |
| M0-D11 bounded filesystem assurance | Existing runtime boundary is reused unchanged; hostile post-acquisition same-UID/root behavior remains excluded |
| M0-D12 bounded quality/proportionality | Q1–Q6 below contain all eight required fields; passing tests 1–20 is enough |
| `maestro run-packet` only | Exact unchanged CLI command and forbidden `cli.py`/second-command scope |
| Planned/Waiting/Blocked/Ready/Dispatchable distinction | Mechanical precedence, transparent skip reasons, tests 2–3 |
| Atomic lease and locks | One assignment transaction and test 4 |
| Patient worker communication | Fixed 60/30/900 policy and tests 5–7 |
| Integration as first-class routing | All three modes and result lineage in test 15 |
| Independent review | Actor separation and self-review rejection in test 16 |
| Recovery before action | Durable rereconciliation and test 18 |
| Explicit Project Architect return | Exact handoff schema/reason codes and test 19 |
| Owner acceptance stop/no implicit successor | `MergeReady -> AwaitingOwner -> STOP`, external-call count zero, test 20 |
| Atlas remains read-only and absent | Atlas-ready stored projection only; no Atlas/API/UI path or command |
| Alpha-03 accepted limitation | New valid non-conflicting binding fixture; no repaired-malformed-conflict claim |

The architecture plan's required evidence items map in order to packet tests:
`1->20`, `2->2`, `3->3`, `4->4`, `5->5`, `6->6/7`, `7->8`, `8->9`,
`9->10`, `10->11`, `11->12`, `12->12/13`, `13->14`, `14->15`, `15->16`,
`16->17`, `17->18`, and `18->20`. Test 1 proves the plan's pre-mutation
fixture boundary, while test 19 adds the Owner-required Project Architect
return proof.

## Complete bounded quality contracts

### Q1 — Authority-faithful eligibility and atomic assignment

- **Protected outcome:** only the highest-ranked genuinely dispatchable
  candidate receives one complete attempt/lease/lock set.
- **Operating/failure model:** one trusted process consumes one strict fixed
  graph with blocked, waiting, unreleased, ready-but-nondispatchable, and
  dispatchable candidates; invalid authority, bases, routes, holds, locks, and
  resources are in scope.
- **Exclusions:** real adapters, dynamic priority, multiple projects,
  production queues, parallel runs, remote scheduling, and policy inference.
- **Assurance:** deterministic projection plus one transactional claim and
  complete decision evidence.
- **Sufficient proof:** required tests 1–4 and 20 pass.
- **Implementation boundary:** standard-library Python and existing SQLite
  service with the exact modules/tables above; no new dependency or service.
- **Proportionality ceiling:** one project, graph, active attempt, finite
  candidate set, and serial execution.
- **Stop/return:** missing or contradictory authority, ambiguous eligibility,
  or no unique next action records `ProjectArchitectReturn` with
  `AuthorityMissing`, `AuthorityConflict`, `EligibilityAmbiguous`, or
  `NoUniqueNextAction` before further mutation.

### Q2 — Patient worker status and honest timing

- **Protected outcome:** a quiet healthy worker is not prematurely interrupted,
  retried, failed, or assigned an invented completion promise.
- **Operating/failure model:** reliable ETA, ETA `unknown`, no immediate reply,
  duplicate/early request, stale reply, wrong attempt, and timeout-boundary
  reconciliation are in scope.
- **Exclusions:** guaranteed ETA, token-level progress, arbitrary chat, raw
  prompts/traces/reasoning, hostile-worker truth proof, and infinite waiting.
- **Assurance:** one rate-limited outstanding request with exact source/time
  evidence and durable-plus-executor reconciliation before timeout action.
- **Sufficient proof:** required tests 5–7 pass.
- **Implementation boundary:** fixed executor-adapter fixture operation and
  bounded structured records; no chat daemon or provider SDK.
- **Proportionality ceiling:** one attempt, one outstanding request, 60-second
  minimum interval, 30-second response window, 900-second lease.
- **Stop/return:** a packet/architecture blocker or absent continuation policy
  records `ProjectArchitectReturn`; ordinary pre-timeout silence remains with
  the Coordinator and stays `Running`.

### Q3 — Honest allowance, context, usage, and checkpoint evidence

- **Protected outcome:** Maestro does not misstate account allowance, tokens,
  cost, local capacity, context fit, or preserved work at pressure.
- **Operating/failure model:** supported/unavailable/stale/coarse windows,
  tracked/coarse/unattributed arithmetic, exact/estimated/unavailable counters,
  zero reasoning, all cost states, malformed thresholds, and pressure crossing
  are in scope.
- **Exclusions:** UI scraping, unsupported allowance formulas, billing
  reconciliation, real tokenizer/provider calls, budget enforcement/rerouting,
  universal prediction, raw content, compaction, and replacement sessions.
- **Assurance:** strict preflight, exact fixture arithmetic, labeled measurement
  states, local/hosted separation, and one deterministic checkpoint action.
- **Sufficient proof:** required tests 8–14 pass.
- **Implementation boundary:** explicit fixtures, bounded decimal arithmetic,
  additive SQLite evidence, and no external dependency.
- **Proportionality ceiling:** one OpenAI weekly window, one local-capacity
  observation, one attempt fingerprint, and one checkpoint.
- **Stop/return:** preserve unsupported facts as unavailable; malformed facts
  stop usage-driven action; any need for real account access, budget policy,
  compaction/continuation, or global thresholds records the corresponding
  `ProjectArchitectReturn`.

### Q4 — Role separation, Integration, review, and correction

- **Protected outcome:** result lineage, Integration ownership, reviewer
  independence, and the one-correction ceiling cannot be bypassed.
- **Operating/failure model:** validate-only, assemble, replan, self-review,
  missing evidence, one named-gate correction, second correction, new failure,
  unrelated work, scope breach, and contract defect are in scope.
- **Exclusions:** real code quality, GitHub reviews, automatic repair, general
  workflow engines, and production multi-result Integration.
- **Assurance:** exact actor/result lineage and explicit gated transitions for
  all fixture outcomes.
- **Sufficient proof:** required tests 15–17 pass.
- **Implementation boundary:** structured synthetic records and transition
  functions only.
- **Proportionality ceiling:** one worker result, at most one Integration result,
  one review chain, and one correction.
- **Stop/return:** `replan`, self-review, missing architecture contract, scope
  change, exhausted correction, or new failure records the exact
  `ProjectArchitectReturn`; no second correction is assigned.

### Q5 — Durable idempotency and recovery

- **Protected outcome:** duplicates, restart, contention, timeout, expiry, and
  stale/wrong observations cannot duplicate work or corrupt evidence/locks.
- **Operating/failure model:** one local SQLite writer receives repeated or
  reordered scripted observations around one active attempt, including restart
  between durable transitions.
- **Exclusions:** distributed consensus, hostile database writers, remote event
  guarantees, multiple coordinators, and real heartbeat transport.
- **Assurance:** transactional state/attempt guards, unique idempotency keys,
  immutable accepted evidence, and rereconciliation before action.
- **Sufficient proof:** required test 18 passes for every named case.
- **Implementation boundary:** existing SQLite transaction patterns and bounded
  additive records; no broker, daemon, distributed lock, or migration redesign.
- **Proportionality ceiling:** single-process recovery for one synthetic active
  assignment.
- **Stop/return:** if durable facts cannot identify one unambiguous next action,
  record `ProjectArchitectReturn` / `NoUniqueNextAction`; never guess or start a
  replacement.

### Q6 — Synthetic confinement and explicit authority stops

- **Protected outcome:** qualification cannot affect a real project/actor/
  provider or pass the Project Architect and Owner boundaries.
- **Operating/failure model:** fixtures attempt external paths/routes,
  credentials, Git/GitHub/network/provider actions, raw content, merge,
  successor selection, stronger isolation, or a bare escalation.
- **Exclusions:** hostile same-UID/root behavior beyond M0-D11, production
  sandboxing, provider security, and live repository containment.
- **Assurance:** strict allowlists, no executable external interface, exact
  Project Architect return schema, and successful stop at `AwaitingOwner`.
- **Sufficient proof:** required tests 1, 19, and 20 pass.
- **Implementation boundary:** repository fixtures and the existing local
  runtime only; no subprocess, Git, network, credential, provider, Atlas, merge,
  or successor implementation.
- **Proportionality ceiling:** bounded interfaces and focused tests, not a
  general OS sandbox.
- **Stop/return:** any need for external access, stronger isolation, broader
  authority, merge, or successor behavior records `ProjectArchitectReturn` and
  stops. Material Owner judgment is flagged but routed through the Project
  Architect; successful acceptance alone stops at `AwaitingOwner`.

## Explicit exclusions

- Real project registration, Foundry, VennueSign, or other repository access.
- Real local/cloud model invocation, real worker/reviewer/Integration dispatch,
  subprocess execution, Git/GitHub/CI, network, webhook, credentials, secrets,
  or notifications.
- Real provider-account access, UI scraping, billing, credit purchase, budget
  enforcement, provider rerouting, or unsupported allowance precision.
- Production scheduler/queues, multi-project operation, parallel execution,
  optimization, fairness/aging, or background polling.
- Atlas/API/UI, backup/recovery/USB, deployment, merge, automatic Owner
  acceptance, or successor selection.
- Changes to Alpha-01's M0-D11 assurance boundary or claims that Alpha-03's
  accepted malformed-conflict limitation was repaired.

## Worker completion and review handoff

A valid implementation result is one scoped commit on the released non-default
branch, based on the exact released implementation base, with all required
checks passing and no prohibited access/artifact. The worker reports exact
changed paths, commands/results, evidence, fixture identities/digests, schema
version, known limitations, and confirms no real action occurred.

Fresh independent implementation review then verifies the complete exact
base/head range against this packet. Approval advances only to the already
authorized Owner acceptance/merge decision. It does not merge, release a real
project, or select Alpha-05/Foundry work.

M0-D05 allows one targeted correction only for committed in-scope work failing
a named packet gate. Missing authority, scope breach, dependency/configuration/
placeholder violation, contract defect, or a new failure class returns to the
Project Architect immediately. If the one correction is used, the same
independent reviewer verifies only the named correction diff and directly
affected consistency; any uncovered final-head change blocks merge coverage.
