# Alpha-04 — Execute Synthetic Control-Loop Qualification

**Status:** CORRECTION IN PROGRESS — initial Decision Fidelity review returned
`REQUEST_CHANGES`; not approved, released, or authorized for implementation

**Owner:** Jeremy Miedreich

**Packet ID:** `maestro-alpha-04-control-loop-qualification`

**Graph node:** `MAESTRO-ALPHA-04-CONTROL-LOOP-QUALIFICATION`

**Graph revision:** `maestro-alpha-04-plan-r2`

**Architecture plan:** [Alpha-04 synthetic control-loop qualification](../proposed/alpha-04-synthetic-control-loop-qualification.md), merged through PR #12 at `b2594d9ab4cad528cd6272622f68162850a0584e`

**Decision authority:** [M0-D13](../decisions/m0-d13-synthetic-control-loop-qualification.md) and [M0-D14](../decisions/m0-d14-context-and-token-reporting.md)

**Readiness direction:** [2026-09-01 Alpha-04 readiness direction](../../../sources/planning/2026-09-01-alpha-04-readiness-direction.md)

**Initial Decision Fidelity review:** [review record](../../../sources/planning/2026-09-01-alpha-04-decision-fidelity-review.md) for exact range `8aa4cb517dcb902060cf5acd1d58806787e03841..f0bf2889b28eb78e2b98b239f5ad7d82d4a7ba15` returned `REQUEST_CHANGES`; findings DF-01 through DF-05 are corrected by the next correction-only commit and require targeted verification

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

The complete Alpha-04 packet is a strict JSON object with exactly these root
keys; no other key is permitted:

```text
packet_id, title, authority, owned_paths, gates, executor,
control_loop_fixture, independent_review_route, owner_stop_boundary
```

The exact non-scenario values are:

```json
{
  "packet_id": "maestro-alpha-04-control-loop-qualification",
  "title": "Alpha-04 Synthetic Control-Loop Qualification",
  "authority": {
    "approval_reference": "Alpha-04 approved execution packet",
    "fidelity_reference": "Alpha-04 Decision Fidelity review coverage"
  },
  "owned_paths": [
    "docs/architecture/alpha-04-synthetic-control-loop-qualification.md",
    "docs/operations/alpha-04-synthetic-control-loop-qualification.md",
    "fixtures/alpha/alpha-04-*-packet.json",
    "fixtures/alpha/control-loop/**",
    "services/maestro/maestro/control_loop.py",
    "services/maestro/maestro/control_loop_contract.py",
    "services/maestro/maestro/lifecycle.py",
    "services/maestro/maestro/packet_contract.py",
    "services/maestro/maestro/packet_wrapper.py",
    "services/maestro/maestro/storage.py",
    "tests/alpha_04/test_control_loop_qualification.py"
  ],
  "gates": [
    "python -m unittest discover -s ../../tests/alpha_01 -v",
    "python -m unittest discover -s ../../tests/alpha_02 -v",
    "python -m unittest discover -s ../../tests/alpha_03 -v",
    "python -m unittest discover -s ../../tests/alpha_04 -v"
  ],
  "independent_review_route": "Independent Implementation Reviewer",
  "owner_stop_boundary": "Stop at AwaitingOwner or ProjectArchitectReturn; no merge or successor action."
}
```

`authority` has exactly the two shown keys and values. `owned_paths` and
`gates` are ordered arrays equal byte-for-byte after JSON decoding to the arrays
above. `executor` has exactly `kind` and `scenario`; `kind` is always
`synthetic-local`, and `scenario` plus `control_loop_fixture` must be exactly
one row from this table:

| Packet fixture | `executor.scenario` | `control_loop_fixture` |
| --- | --- | --- |
| `alpha-04-happy-path-packet.json` | `control-loop-happy` | `happy-path.json` |
| `alpha-04-correction-packet.json` | `control-loop-correction` | `one-correction.json` |
| `alpha-04-assemble-packet.json` | `control-loop-assemble` | `integration-assemble.json` |
| `alpha-04-replan-packet.json` | `control-loop-replan` | `integration-replan.json` |

The two authority strings are fixed fixture authority labels. They do not claim
that approval or review occurred; implementation remains barred until the
release gate records the exact released packet commit and review coverage.

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
available_locks, available_resources, allowance_window, attempt_preflights,
assignment, correction_assignment, observations, expected
```

`schema_version` is the integer `1`. Stable identifiers are lowercase ASCII
`[a-z][a-z0-9-]{2,63}`. Timestamps are UTC RFC 3339 strings ending in `Z` and
must be nondecreasing within an observation sequence. Finite numbers are JSON
integers or decimals, never strings, NaN, or infinity. Unknown keys, duplicate
IDs other than the one later-defined literal event occurrence, invalid enums,
inconsistent arithmetic, or references to absent objects are malformed and
rejected before mutation.

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

`actors` is an ordered array of exactly four objects with the exact values
below:

```json
[
  {"actor_id": "fixture-coordinator-01", "role": "Coordinator", "route": "synthetic-coordinator", "may_change_result": false, "synthetic": true},
  {"actor_id": "fixture-worker-01", "role": "Worker", "route": "scripted-local-adapter", "may_change_result": true, "synthetic": true},
  {"actor_id": "fixture-integration-01", "role": "Integration", "route": "validate-only", "may_change_result": false, "synthetic": true},
  {"actor_id": "fixture-reviewer-01", "role": "IndependentReviewer", "route": "scripted-independent-review", "may_change_result": false, "synthetic": true}
]
```

The Integration object varies only by fixture: the happy and correction
fixtures use `validate-only`/`false`, the assemble fixture uses
`assemble`/`true`, and the replan fixture uses `replan`/`false`. No other
role-to-route or `may_change_result` combination is valid. All IDs differ. The
reviewer differs from every result-changing actor. `synthetic` is true. No provider
credential, executable command, prompt, transcript, network endpoint, real
repository identity, or arbitrary route is allowed.

The Coordinator owns requests, boundaries, assignment decisions, and recovery
decisions. The Worker owns status reports, checkpoints, usage observations,
and worker/correction completions. Integration owns `integration_completed`.
IndependentReviewer owns `review_completed`. Any event whose `actor_id` does
not match that exact ownership is invalid before mutation.

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
  "expected_reasons": ["all_dispatchability_conditions_satisfied"]
}
```

Projection is mechanical and uses this precedence; every applicable reason in
the first matching state is retained in the listed order:

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
The only reason codes, in precedence order, are
`not_released`, `same_role_predecessor_incomplete`,
`hard_dependency_incomplete`, `review_gate_incomplete`,
`contract_unavailable`, `route_contract_unavailable`,
`route_currently_ineligible`, `base_incompatible`, `active_hold`, followed by
`lock_unavailable:<lock-id>` sorted by lock ID and
`resource_unavailable:<resource-id>` sorted by resource ID. A fully eligible
candidate has only `all_dispatchability_conditions_satisfied`. No prose or
additional reason code is permitted.
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
  "window_id": "allowance-window-01",
  "reconciliation_id": "allowance-reconciliation-01",
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

`attempt_preflights` is an ordered array with one entry for the primary attempt
and, in the correction fixture only, a second entry for the correction attempt.
Each entry contains exactly:

```json
{
  "attempt_id": "attempt-primary",
  "observation_id": "usage-preflight-01",
  "measurement_period_id": "period-attempt-01",
  "revision": 0,
  "period_started_at": "2026-09-01T12:00:00Z",
  "period_ended_at": null,
  "measurement_type": "estimated",
  "confidence": "medium",
  "pressure_state": "normal",
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
  "elapsed": {"state": "unavailable", "milliseconds": null, "measured_from": null},
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

The primary preflight object is durable usage revision zero for
`period-attempt-01`; it exists before any event may reference it. Measurement
types are `estimated` or `runtime_reported`, and confidence is
`none|low|medium|high`. Pressure states are `normal|warning|checkpoint|stop`.
Elapsed time is independent from tokens and cost and is exactly
`{"state":"exact|estimated","milliseconds":<nonnegative integer>,
"measured_from":"attempt_start|period_start"}` or
`{"state":"unavailable","milliseconds":null,"measured_from":null}`.
The correction preflight uses `attempt-correction`, `usage-preflight-02`, and
`period-attempt-02`, occurs before correction lease/claim acquisition, and
otherwise obeys the identical strict schema and fit rules. Every attempt thus
has its own preflight and through-completion measurement period.

### Assignment, identity, time, lease, and claim contract

`assignment` contains exactly:

```json
{
  "attempt_id": "attempt-primary",
  "attempt_number": 1,
  "actor_id": "fixture-worker-01",
  "role": "Worker",
  "base_identity": "fixture-base-001",
  "lease_id": "lease-primary",
  "lease_acquired_at": "2026-09-01T12:00:00Z",
  "lease_expires_at": "2026-09-01T12:15:00Z",
  "lock_claims": {
    "path:services-maestro": "claim-primary-path",
    "shared:sqlite-schema": "claim-primary-schema"
  },
  "resource_claims": {"synthetic-worker-slot": "claim-primary-worker-slot"}
}
```

The happy, assemble, and replan fixtures set `correction_assignment` to null.
The correction fixture supplies exactly:

```json
{
  "attempt_id": "attempt-correction",
  "attempt_number": 2,
  "actor_id": "fixture-worker-01",
  "role": "Worker",
  "original_attempt_id": "attempt-primary",
  "base_identity": "fixture-result-primary",
  "lease_id": "lease-correction",
  "lease_acquired_at": "2026-09-01T12:12:00Z",
  "lease_expires_at": "2026-09-01T12:27:00Z",
  "lock_claims": {
    "path:services-maestro": "claim-correction-path",
    "shared:sqlite-schema": "claim-correction-schema"
  },
  "resource_claims": {"synthetic-worker-slot": "claim-correction-worker-slot"}
}
```

These are assertions of fixture facts, not permission to assign. The primary
claim keys and units equal the selected candidate's complete required lock and
resource set. The correction claim keys and units equal the primary set. Every
attempt, lease, claim, request, checkpoint, usage observation, measurement
period, event, reconciliation, and handoff ID is supplied by the strict fixture
and validated before mutation. No runtime-generated ID is used in this
qualification. Every lifecycle timestamp is supplied by the fixture, is UTC,
and is checked against the event sequence and fixed 900-second lease. The
durable attempt captures both `role` and the canonical full actor object at the
instant of claim so later actor-table changes cannot alter its identity.

### Observation script

`observations` is an ordered array. Each observation has exactly
`event_id`, `event_type`, `attempt_id`, `actor_id`, `observed_at`, `received_at`,
`idempotency_key`, and `payload`. IDs and idempotency keys are unique except one
intentional literal duplicate occurrence, which repeats the original event
object byte-for-byte in canonical JSON, including the same `event_id` and
`idempotency_key`. There is no `duplicate_event` event type.
The attempt ID must match the active attempt unless the event is an explicitly
expected stale/wrong-attempt test.

The only event types and exact payload key sets are:

| Event type | Exact payload keys |
| --- | --- |
| `worker_status_requested` | `request_id`, `questions` |
| `worker_status_reported` | `request_id`, `plan_steps`, `current_step_id`, `actively_progressing`, `blocker`, `eta`, `context_usage`, `worker_observed_at` |
| `status_response_boundary` | `request_id`, `durable_attempt_state`, `executor_state`, `lease_state`, `decision` |
| `checkpoint_requested` | `checkpoint_id`, `pressure`, `safe_boundary` |
| `checkpoint_reported` | `checkpoint_id`, `completed_work`, `plan_steps`, `current_step_id`, `changed_artifacts`, `checks`, `evidence_references`, `blocker`, `next_action` |
| `usage_observed` | `observation_id`, `measurement_period_id`, `revision`, `period_started_at`, `period_ended_at`, `context_limit_tokens`, `context_used_tokens`, `context_remaining_tokens`, `output_reserve_tokens`, `measurement_type`, `confidence`, `tokens`, `cost`, `elapsed`, `pressure_state` |
| `worker_completed` | `base_identity`, `result_identity`, `commit_identity`, `scoped_diff`, `violation_codes`, `changed_paths`, `checks`, `evidence_references`, `token_cost_observation_id`, `correction_round` |
| `integration_completed` | `mode`, `input_result_identity`, `result_identity`, `changed_paths`, `checks`, `evidence_references`, `disposition` |
| `review_completed` | `reviewed_result_identity`, `outcome`, `finding_ids`, `evidence_references`, `correction_round` |
| `correction_assigned` | `finding_ids`, `original_attempt_id`, `original_result_identity`, `correction_attempt_id`, `correction_lease_id`, `released_claim_ids`, `acquired_claim_ids`, `correction_round` |
| `correction_completed` | `finding_ids`, `original_attempt_id`, `original_result_identity`, `result_identity`, `commit_identity`, `scoped_diff`, `violation_codes`, `changed_paths`, `checks`, `evidence_references`, `token_cost_observation_id`, `correction_round` |
| recovery event types | `durable_state`, `observed_state`, `referenced_attempt_id`, `referenced_event_id`, `decision`, `reason` |

Recovery event types are exactly `lease_expired`, `competing_claim`,
`stale_completion`, and `restart_reconcile`. Event ownership is exact:

| Owner | Event types |
| --- | --- |
| `fixture-coordinator-01` | `worker_status_requested`, `status_response_boundary`, `checkpoint_requested`, `correction_assigned`, all recovery event types |
| `fixture-worker-01` | `worker_status_reported`, `checkpoint_reported`, `usage_observed`, `worker_completed`, `correction_completed` |
| `fixture-integration-01` | `integration_completed` |
| `fixture-reviewer-01` | `review_completed` |

Nested shapes are also closed. `questions` is exactly the ordered array
`["ordered_plan","current_step","actively_progressing","blocker","eta"]`.
`plan_steps` contains one through eight exact objects
`{"step_id":"<stable-id>","position":<positive integer>,
"status":"pending|current|complete","summary":"<non-empty text>"}` with
unique contiguous positions and exactly one `current` step matching
`current_step_id` until completion. `checks` contains one through eight exact
objects `{"gate":"<declared packet gate>","result":"pass|fail",
"evidence_reference":"<non-empty reference>"}`. Changed paths/artifacts are
ordered unique arrays of zero through sixteen non-empty strings; completed work
and evidence references contain one through sixteen; finding IDs contain zero
through eight. Changed paths must be covered by the outer packet `owned_paths`
allowlist. `pressure` is exactly
`{"usage_observation_id":"<accepted observation>",
"measurement_period_id":"<same period>","revision":<same revision>,
"pressure_state":"warning|checkpoint|stop"}`; `safe_boundary` must be true.
`next_action` is `continue|complete|stop`.

`commit_identity` is a stable non-empty fixture string or null. `scoped_diff`
is exactly `{"present":<boolean>,"paths":["<ordered unique path>"]}` and its
paths equal `changed_paths` when present. `violation_codes` is an ordered unique
subset of `ScopeViolation`, `DependencyViolation`, `ConfigurationViolation`,
and `PlaceholderViolation`. A reviewable completion has a non-null commit,
`present: true`, at least one changed path, and no violation code. Rejection
classification uses this exact precedence: null commit -> `MissingCommit`;
otherwise absent/empty scoped diff -> `MissingScopedDiff`; otherwise the first
present violation in the enum order above. The chosen code is stored as the
single canonical rejection reason; all supplied evidence remains durable.

An `integration_completed.mode` equals the declared Integration route.
`validate-only` requires unchanged input/result identity, no changed paths, and
`validated`; `assemble` requires a new result identity, non-empty changed
paths, and `assembled`; `replan` requires unchanged identity, no changed paths,
and `needs_replan`. Review `APPROVE` requires an empty finding array; review
`REQUEST_CHANGES` requires one through eight stable finding IDs. A committed,
in-scope completion with one or more failed named checks is
`CorrectionEligible` under M0-D05 without pretending it passed review;
non-delivery/violation evidence uses `CoordinatorRejection`, and architecture
ambiguity uses `ProjectArchitectReturn`. `correction_assigned` is the
only non-stale event whose outer `attempt_id` names the original active attempt
while its payload names the next attempt. Every other non-recovery event names
the active attempt owned by its actor.

Status-boundary states are closed enums: `durable_attempt_state` is
`Running|AwaitingIntegration|AwaitingReview`, `executor_state` is
`healthy|completed|unavailable`, `lease_state` is `active|expired|closed`, and
`decision` is `remain_running|accept_completion|reconcile_expiry`. Recovery
`durable_state` is exactly `{"run_state":"<declared lifecycle state>",
"active_attempt_id":"<stable ID or null>","lease_id":"<stable ID or null>",
"lease_state":"active|expired|closed","claim_ids":["<sorted ID>"],
"last_accepted_event_id":"<stable ID or null>"}`. `observed_state` is exactly
`{"attempt_id":"<stable ID>","lease_id":"<stable ID or null>",
"executor_state":"healthy|completed|unavailable",
"event_id":"<stable ID>"}`. Recovery reasons are
`duplicate_idempotency`, `stale_attempt`, `active_claim_conflict`,
`healthy_before_timeout`, `expired_lease`, or `ambiguous_facts`.
`ambiguous_facts` alone requires `project_architect_return`.

`blocker` is exactly `{"state": "none", "details": null}` or
`{"state": "reported", "details": "<non-empty text>"}`. `eta` is exactly
`{"state": "reliable", "value": <positive integer>, "unit": "seconds",
"confidence": "low|medium|high"}` or `{"state": "unknown", "value": null,
"unit": null, "confidence": "none"}`. `context_usage` is exactly
`{"usage_observation_id":"<accepted observation>",
"measurement_period_id":"<same period>","revision":<same revision>}`.
It references either preflight revision zero or an earlier accepted
`usage_observed` event for the same attempt; it does not repeat or invent usage
facts. A completion's `token_cost_observation_id` similarly references an
already accepted usage observation for that attempt.

`tokens` and `cost` inside `usage_observed` use the exact preflight token/cost
shapes. Context arithmetic must satisfy `used + remaining = limit` and
`remaining >= 0`. A measurement period starts at preflight and ends no later
than its completion observation. Revisions start at zero and increase by one.
A higher `runtime_reported` revision supersedes an `estimated` revision only
for the same `measurement_period_id`; both remain durable, exactly one is
marked effective, and no later estimate may supersede a runtime report. Usage
observations occur at preflight, at the status or checkpoint boundary that
changes pressure, and before every completion. Thus tokens, cost, context, and
elapsed time are represented through completion.

Review outcomes are `APPROVE` or `REQUEST_CHANGES`; Integration dispositions
are `validated`, `assembled`, or `needs_replan`. Correction round is zero for
the original result and one for the only permitted correction. Recovery
decisions are `ignore_duplicate`, `ignore_stale`, `remain_running`,
`preserve_terminal`, or `project_architect_return`; they cannot directly create
an attempt or release a lock.

For the one literal duplicate occurrence, the first occurrence index is
accepted and the later identical occurrence index is ignored. It creates no
second event row and cannot change state. Event IDs alone are therefore not
used to account for the script; the expected result accounts for observation
array indexes.

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

One or more failed named gates, including a Review `REQUEST_CHANGES`, may create
one correction only when every finding belongs to a committed, in-scope
result. The correction retains the original
attempt lineage, increments correction count from zero to one, names the exact
finding IDs, and receives targeted review of the correction-only diff. The
original attempt follows:

```text
Dispatchable -> Leased -> Running -> AwaitingIntegration -> AwaitingReview
-> CorrectionEligible
```

The accepted `correction_assigned` event performs one `BEGIN IMMEDIATE`
transaction that closes the original lease, releases every original claim,
inserts correction attempt two with its original-attempt/result lineage,
inserts its already validated preflight revision zero, acquires its declared
lease and exactly the same complete lock/resource set, and advances the active
attempt. Any failed release, insert, or reacquisition
rolls back the whole transaction. The correction then follows:

```text
CorrectionEligible -> Leased -> Running -> AwaitingIntegration
-> AwaitingReview -> MergeReady -> AwaitingOwner -> STOP
```

It passes through Integration again and only a review of its exact correction
result/diff may approve it. Success or any terminal return closes the active
lease and releases only that active attempt's claims in the same transaction.
A stale or wrong-attempt event can never close a lease or release claims. A
second correction, new failure class, missing architecture contract, or
unrelated change records `ProjectArchitectReturn` and stops without another
assignment. Scope, dependency, configuration, placeholder, commit, and diff
failures instead use the Coordinator rejection contract below.

## Exact Coordinator rejection contract

M0-D05 keeps initial non-delivery and eligibility failures with the
Coordinator. Missing commit, missing scoped diff, scope violation, dependency
violation, configuration violation, and placeholder violation are rejected
immediately before review and never receive a correction or
`ProjectArchitectReturn`. Alpha-04 records exactly:

```json
{
  "handoff_id": "handoff-coordinator-rejection",
  "status": "Rejected",
  "handoff_kind": "CoordinatorRejection",
  "reason_code": "MissingCommit",
  "reason": "The exact rejected evidence condition.",
  "evidence_references": ["event:event-worker-completed"],
  "required_decision": "Coordinator routes the rejected packet under M0-D05.",
  "owner_decision_required": false,
  "safe_stop": "NoCorrectionOrFurtherAssignment",
  "created_at": "<causing event received_at>"
}
```

The only rejection reason codes are `MissingCommit`, `MissingScopedDiff`,
`ScopeViolation`, `DependencyViolation`, `ConfigurationViolation`, and
`PlaceholderViolation`. The scripted qualification records Coordinator
ownership and stops; it does not actually reassign Local Qwen. A correction
that makes no source change, lacks its required commit, or remains out of scope
uses the same exact rejection and stop. Only an actual ambiguity or defect in
project architecture/packet authority uses `ProjectArchitectReturn`.

## Explicit Project Architect return contract

Alpha-04 must never emit a bare `escalate` result. When operational rules cannot
determine one safe next action because the project authority or packet is
insufficient, it records:

```json
{
  "handoff_id": "handoff-project-architect-return",
  "status": "NeedsReplan",
  "handoff_kind": "ProjectArchitectReturn",
  "reason_code": "IntegrationReplan",
  "reason": "The exact missing boundary or conflict.",
  "evidence_references": ["event:event-integration-replan"],
  "required_decision": "The exact architecture clarification or superseding packet needed.",
  "owner_decision_required": false,
  "safe_stop": "NoFurtherAssignmentOrMutation",
  "created_at": "<causing event received_at>"
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
Its exact successful handoff is:

```json
{
  "handoff_id": "handoff-awaiting-owner",
  "status": "AwaitingOwner",
  "handoff_kind": "AwaitingOwner",
  "reason_code": "IndependentReviewApproved",
  "reason": "The separately reviewed synthetic result passed the packet gates.",
  "evidence_references": ["event:<accepted review event>"],
  "required_decision": "Owner acceptance or rejection; no implied merge.",
  "owner_decision_required": true,
  "safe_stop": "NoMergeOrSuccessorAction",
  "created_at": "<accepted review event received_at>"
}
```

## Durable storage and transition requirements

Increase `SCHEMA_VERSION` from `2` to `3` and add only these Alpha-04 records
through the existing `SQLiteFoundation` service-owned writer:

| Record | Exact logical columns |
| --- | --- |
| `control_loop_runs` | `packet_id`, `fixture_id`, `fixture_digest`, `graph_revision`, `authority_reference`, `source_base`, `selected_candidate_id`, `state`, `correction_count`, `created_at`, `updated_at` |
| `control_loop_queue_entries` | `packet_id`, `candidate_id`, `rank`, `derived_state`, `dispatchable`, `reasons_json`, `selected` |
| `control_loop_attempts` | `packet_id`, `attempt_id`, `attempt_number`, `actor_id`, `role`, `actor_snapshot_json`, `base_identity`, `result_identity`, `state`, `lease_id`, `lease_acquired_at`, `lease_expires_at`, `lease_closed_at`, `context_fingerprint_json`, `original_attempt_id`, `correction_round` |
| `control_loop_locks` | `packet_id`, `attempt_id`, `lease_id`, `claim_id`, `claim_kind`, `claim_target`, `units`, `state`, `acquired_at`, `released_at` |
| `control_loop_events` | `packet_id`, `attempt_id`, `event_id`, `event_type`, `idempotency_key`, `actor_id`, `prior_state`, `new_state`, `observed_at`, `received_at`, `payload_json`, `decision`, `reason` |
| `worker_status_records` | `packet_id`, `attempt_id`, `request_id`, `request_state`, `plan_json`, `current_step_id`, `actively_progressing`, `blocker_json`, `eta_json`, `context_usage_json`, `observed_at`, `received_at`, `next_permitted_action` |
| `allowance_windows` | `packet_id`, `window_id`, `provider`, `account_reference`, `window_type`, `unit`, `before_json`, `after_json`, `reset_at`, `precision`, `measurement_quality`, `freshness`, `raw_fixture_json` |
| `attempt_usage` | `packet_id`, `attempt_id`, `observation_id`, `measurement_period_id`, `revision`, `effective`, `measurement_type`, `confidence`, `model_id`, `runtime_id`, `context_limit`, `context_used`, `context_remaining`, `quantization`, `packet_minimum`, `output_reserve`, `thresholds_json`, `tokens_json`, `cost_json`, `elapsed_state`, `elapsed_milliseconds`, `elapsed_measured_from`, `pressure_state`, `period_started_at`, `period_ended_at`, `observed_at` |
| `usage_reconciliations` | `packet_id`, `attempt_id`, `reconciliation_id`, `window_id`, `observed_change`, `tracked_usage`, `coarse_usage`, `unattributed_remainder`, `reconciles`, `local_capacity_json`, `pace_json` |
| `control_loop_handoffs` | `packet_id`, `attempt_id`, `handoff_id`, `status`, `handoff_kind`, `reason_code`, `reason`, `evidence_references_json`, `required_decision`, `owner_decision_required`, `safe_stop`, `created_at` |

Identifiers, enums, booleans, counts, and timestamps use `TEXT`/`INTEGER` with
`NOT NULL` and `CHECK` constraints matching the fixture contract; decimal
allowance values use canonical decimal strings so binary floating-point cannot
change reconciliation. JSON columns contain canonical sorted-key compact JSON
that has already passed the relevant strict schema. `released_at`,
`lease_closed_at`, `period_ended_at`, `result_identity`,
`original_attempt_id`, elapsed detail fields, and successful-handoff
architecture fields may be null only in the lifecycle states where the earlier
contract says they do not yet apply. No other nullability is inferred.

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

The atomic assignment transaction must insert the selected attempt, its already
validated preflight usage revision, and lease; reserve every path/shared/
resource lock; record the dispatch decision and skip reasons; and transition
the selected queue entry together. If any insert or reservation fails, the
whole transaction rolls back. No partial attempt, usage row, or lock set may
remain.

The exact fixture owns all IDs and time values described above. `created_at`
for a terminal handoff equals the `received_at` of the accepted event that
caused it; the successful handoff ID is `handoff-awaiting-owner`, the replan or
architecture handoff ID is `handoff-project-architect-return`, and the
M0-D05 rejection handoff ID is `handoff-coordinator-rejection`. A fixture may
contain only the one terminal handoff ID applicable to its asserted route.

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
  "terminal_handoff_id": "handoff-awaiting-owner | handoff-project-architect-return",
  "integration_mode": "validate-only | assemble | replan",
  "correction_count": 0,
  "accepted_event_indexes": [0],
  "ignored_event_indexes": [],
  "external_call_count": 0
}
```

`queue_states` accounts for every candidate exactly once. The union of accepted
and ignored indexes equals every zero-based `observations` array index exactly
once, with no overlap or duplicate index. This remains unambiguous when two
occurrences carry the same event ID. `external_call_count` must be integer zero.
The Coordinator recomputes
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
   allowance, preflights, observations, expectations, cross-references,
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

1. strict outer packet and fixture key/value allowlists, scenario mapping,
   safe-basename and pre-mutation validation, including unknown fields, absent
   authority, invalid role/route/result-change combinations, malformed
   IDs/times/enums, inconsistent references/arithmetic, secret/external route
   fields, and a valid Alpha-03 binding with non-empty authority arrays;
2. exact `Planned`, `Waiting`, `Blocked`, `Ready`, and `Dispatchable`
   projection plus recorded skip reasons and highest-ranked selection;
3. blocked, unreleased, review-gate-incomplete, route-ineligible,
   base-incompatible, held, lock-conflicting, and resource-conflicting
   candidates cannot be assigned;
4. assignment, attempt, preflight usage revision, lease, path/shared/resource
   locks, dispatch decision, and queue transition are one atomic idempotent
   transaction;
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
    remain distinct for every token and elapsed-time field; every referenced
    usage observation exists, same-period runtime data supersedes but does not
    erase its estimate, and zero/unavailable reasoning never erases other
    context use;
13. billed, estimated, `not_billed`, and `unknown` cost states enforce their
    exact amount/currency contracts;
14. warning/checkpoint pressure produces one safe-boundary checkpoint and the
    declared stop behavior without truncation, summary invention, or session
    replacement;
15. `validate-only`, `assemble`, and `replan` have distinct result lineage and
    handoffs; `replan` records the complete Project Architect return;
16. a worker or Integration actor cannot review its own changed result;
17. one eligible correction atomically closes the original lease/claims,
    creates attempt two, reacquires its exact complete claim set, preserves
    role/actor/result lineage, repeats Integration, and gets exact targeted
    review; initial missing commit/diff, scope, dependency, configuration, and
    placeholder failures record `CoordinatorRejection`; a second round, new
    failure class, unrelated change, or architecture-contract defect records
    `ProjectArchitectReturn` and no new assignment;
18. restart, one literal duplicate occurrence, competing claim, stale/wrong
    completion, timeout, and lease expiry cannot double-dispatch, release
    another attempt's locks, or overwrite accepted/terminal evidence; every
    observation occurrence index is accounted for exactly once;
19. every Project Architect reason code produces the exact reason/evidence/
    decision/Owner-flag/safe-stop shape and never a bare escalation; and
20. successful CLI execution records the complete path through Integration and
    independent review to `AwaitingOwner`, including preflight-through-
    completion context/token/cost/elapsed observations and the exact terminal
    handoff time/ID, with zero external calls and no merge, `Complete`,
    successor, Atlas, provider, Git, GitHub, credential, or real-project action.

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
| M0-D14 preflight-through-completion reporting | Exact allowance/context/token/cost/elapsed/local-capacity lifecycle and tests 8–14 and 20 |
| M0-D05 rejection/correction routing | Coordinator-owned initial rejection plus one eligible correction with atomic attempt/lease/claim lineage in test 17; architecture ambiguity alone returns to the Project Architect |
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
  dispatchable candidates; invalid outer packet/fixture keys, actor roles,
  IDs, authority, bases, routes, holds, locks, and resources are in scope.
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
  zero reasoning, all cost/elapsed states, same-period runtime supersession,
  malformed thresholds, and pressure crossing through completion are in scope.
- **Exclusions:** UI scraping, unsupported allowance formulas, billing
  reconciliation, real tokenizer/provider calls, budget enforcement/rerouting,
  universal prediction, raw content, compaction, and replacement sessions.
- **Assurance:** strict preflight, exact fixture arithmetic, labeled measurement
  states, local/hosted separation, and one deterministic checkpoint action.
- **Sufficient proof:** required tests 8–14 and 20 pass.
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
  missing evidence, Coordinator-owned initial rejection, one named-gate
  correction with atomic lease/claim turnover, second correction, new failure,
  unrelated work, and architecture contract defect are in scope.
- **Exclusions:** real code quality, GitHub reviews, automatic repair, general
  workflow engines, and production multi-result Integration.
- **Assurance:** exact actor/result lineage and explicit gated transitions for
  all fixture outcomes.
- **Sufficient proof:** required tests 15–17 pass.
- **Implementation boundary:** structured synthetic records and transition
  functions only.
- **Proportionality ceiling:** one worker result, at most one Integration result,
  one review chain, and one correction.
- **Stop/return:** initial non-delivery/scope/dependency/configuration/
  placeholder violations record `CoordinatorRejection`; `replan`, self-review,
  missing architecture contract, required scope expansion, exhausted
  correction, or new failure records the exact `ProjectArchitectReturn`; no
  second correction is assigned.

### Q5 — Durable idempotency and recovery

- **Protected outcome:** duplicates, restart, contention, timeout, expiry, and
  stale/wrong observations cannot duplicate work or corrupt evidence/locks.
- **Operating/failure model:** one local SQLite writer receives a literal
  duplicate occurrence or reordered scripted observation around one active
  attempt, including restart between durable transitions and atomic correction
  claim turnover.
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
a named packet gate. Missing commit/diff, scope, dependency, configuration, or
placeholder violations receive the exact Coordinator rejection and stop.
Missing or contradictory authority, a required scope expansion, an
architecture contract defect, or a new failure class receives the exact
Project Architect return. If the one correction is used, the same independent
reviewer verifies only the named correction diff and directly affected
consistency; any uncovered final-head change blocks merge coverage.
