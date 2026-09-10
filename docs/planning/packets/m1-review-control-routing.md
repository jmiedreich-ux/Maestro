# M1 Review Control Routing

**Slice ID:** `MB-SLICE-M1-REVIEW-ROUTING-01`
**Status:** `Pending Targeted Decision Fidelity`
**Base:** `3574bf2b2c3730f167cec553439d0f08bdc85568`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-REVIEW-ROUTING-01` |
| `phase` | `PendingTargetedDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:3574bf2b2c3730f167cec553439d0f08bdc85568","git:full-planning-review-head:58fef6263422d317d6b511fc7bdde4669d1d2137","review:decision-fidelity:request-changes","finding:DF-01:correct-now","finding:DF-02:correct-now"]` |

The carrier has exactly the canonical v1 keys. Counts never reset.

## Outcome and authority

Using current master, the Master Plan, Agent Workforce Control Plane, M0-D01,
M0-D05, M0-D11, M0-D12, the accepted review record, and the merged execution
finish behavior, implement one trusted-caller review-routing command. It
atomically persists an immutable review and routes its packet through the
current validate-only single-worker path. It does not launch a reviewer,
decide a review result, correct code, integrate, merge, or perform an external
action. Returned slices remain non-authority.

## Exact command and closed routes

```text
OperationalStateStore.record_and_route_review(
  packet_id, expected_packet_version, review, reason_payload,
  idempotency_key, actor, now
) -> result
```

The closed route table is:

| Packet source | Review kind | Review result | Packet target |
|---|---|---|---|
| `AwaitingIntegration` | `Integration` | `ValidateOnly` | `AwaitingReview` |
| `AwaitingIntegration` | `Integration` | `NeedsReplan` | `NeedsReplan` |
| `AwaitingReview` | `IndependentImplementation` | `Approve` | `MergeReady` |
| `AwaitingReview` | `IndependentImplementation` | `RequestChanges` | `AwaitingArchitect` |

All other source/kind/result combinations are prohibited and raise
`InvalidTransition`. In particular `Assemble` and `Comment` require a later
workflow, and this slice does not resume a correction. `RequestChanges` records
reviewer advice and enters the explicit disposition-pending state; it does not
authorize correction, replan, return, or developer dispatch. A later command
must persist the Project Architect's one risk disposition before any such
action.

The supplied review is the exact existing closed review record. It must name
the supplied packet, its one latest `Succeeded` Initial attempt and that
attempt's `result_commit` as `head_commit`; use correction number 0; and use
`created_at=now`. `base_commit` must equal the packet base commit and differ
from head. Integration must be the first Integration review for the packet.
Independent review requires exactly one prior `Integration/ValidateOnly`
review for the same packet, attempt, base, and head, and must be the first
IndependentImplementation review.

`coverage_json` has exactly these two keys:

```text
coverage_json := {
  "kind": "review-readiness-coverage",
  "result": <the complete maestro.review-readiness.result/v1 object>
}
```

No additional outer key is permitted. `result` is the complete, unmodified
review-readiness result, including its request, check records, blockers,
callback, and `record_digest`. Validate it with the existing
`review_readiness.validate_result`; require `ready=true`, an empty blocker
list, and every validation and reconstruction check `Passed`. Its request must
use `review_kind=IndependentImplementation`. Its resolved base, request base,
review base, and packet base must be identical; its resolved head, request
head, both checked-out heads, review head, latest attempt result commit, and
current packet head must be identical. Its changed paths must be nonempty,
UTF-8-byte sorted, and identical to the paths derived and sealed by that result;
its request allowlist must equal the packet's canonical
`owned_paths_json`. Both clean observations must be true. These relationships
make the successful gate result and digest durable review coverage rather than
caller prose. Because this slice accepts only correction number 0 and the
Initial attempt, the exact full base/head range is the complete current
correction chain.

Integration requires `reviewer_role=IntegrationAgent`; IndependentImplementation
requires `reviewer_role=IndependentImplementationReviewer`. In both cases,
`reviewer_instance` must differ from the attempt's `model_identity` and
`runtime_identity` and from its lease `holder_id`. The independent reviewer
instance must also differ from the prior Integration reviewer instance. These
are exact durable independence checks; role or instance convention alone is
not accepted.

Every state value below is the existing five-key state payload. The result has
exactly:

```json
{
  "packet":{"entity_id":"packet-id","entity_type":"Packet","kind":"state","state":"AwaitingReview","version":9},
  "review":{"base_commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","correction_number":0,"created_at":"now","head_commit":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","kind":"review-result","packet_id":"packet-id","result":"ValidateOnly","review_id":"review-id","review_kind":"Integration"}
}
```

The compact result intentionally excludes reviewer identity, findings, and
coverage, which remain in the immutable `reviews` row and the command
fingerprint. It adds no unlisted keys.

One `ReviewRecorded` event has `entity_type=Packet`, `entity_id=packet-id`,
`before_json={"packet": <source state>}`, `after_json=<exact result>`, and the
supplied reason/actor facts. The fingerprint is SHA-256 over canonical JSON:

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_route_review","payload":{"expected_packet_version":8,"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."},"review":<fully validated closed review row>}}
```

`now` appears inside the review's immutable `created_at` and is therefore
covered by the fingerprint; there is no second hidden clock.

Validate packet ID, expected version, full review, its closed readiness result,
review/packet/time/base-head/coverage/independence relationships, reason, key,
and actor before writing. Then use one
`BEGIN IMMEDIATE` transaction in this exact order: replay/conflict; packet
existence; packet version; route-table match; latest Succeeded attempt
existence and attempt/packet/head/lease relationships; coverage-result and
reviewer-independence checks; prior-review cardinality and exact facts; insert
review; update packet once; insert event; commit.

Malformed or mismatched facts and missing required records raise
`InvalidRecord`; version mismatch raises `StaleState`; prohibited route/order
raises `InvalidTransition`; changed-fact key reuse raises
`IdempotencyConflict`; busy exhaustion raises `ResourceBusy`; integrity
failure raises `InvalidRecord`. Replay occurs before mutable checks. Event or
row failure rolls back review, packet, and event. Concurrent commands from one
packet version have one winner.

## Exact implementation boundary

The Maestro Developer may change only:

```text
services/maestro/maestro/operational_state.py
tests/m1_02/test_review_control_routing.py
```

No schema, existing review writer, execution/lease/lock behavior, integration
worker, review launcher, correction attempt, acceptance/merge command,
recovery loop, CLI, Git/GitHub, Atlas, notification, external/live project, or
M1-03 work is allowed.

## Named sufficient proof

The new module contains exactly thirteen tests:

1. Integration ValidateOnly records one review and enters AwaitingReview;
2. Integration NeedsReplan records one review and enters NeedsReplan;
3. independent Approve records one review and enters MergeReady;
4. independent RequestChanges records one review and enters AwaitingArchitect
   without authorizing correction, replan, return, or dispatch;
5. the complete source/kind/result complement rejects every unlisted route;
6. packet/Initial-attempt/base/head/time/correction and the complete closed
   readiness result, digest, clean state, paths, checks, and allowlist
   relationships are guarded;
7. exact reviewer roles and instance independence from the attempt executor,
   lease holder, and prior integrator are guarded, and independent review
   requires one exact prior validate-only Integration review;
8. stale version, wrong state, duplicate review kind, and missing records reject;
9. replay is exact and every changed immutable fact conflicts;
10. review/event/update failure rolls back the whole command;
11. concurrent review commands have one winner and no loser residue;
12. restart preserves route/review/event and exact replay; and
13. independent fingerprint, compact result, review row, and event reconstruct.

Run the existing 235 tests plus the thirteen new tests; run tests 10, 11, and
12 in ten fresh processes; compile with external pycache; and run exact diff,
allowlist, staged, tracked/untracked, artifact, and sensitive-value checks.

## M0-D12 quality contract

1. **Protected outcome:** a review result cannot be fabricated, reordered,
   duplicated, detached from the exact mechanically ready succeeded candidate,
   made authoritative by a non-independent reviewer, or route
   `RequestChanges` around Project Architect disposition.
2. **Operating and threat model:** one trusted local writer/SQLite database,
   pre-obtained review judgment, concurrent commands, crash before commit,
   duplicate/stale input, and service restart.
3. **Explicit exclusions:** reviewer quality, review launch, integration edits,
   correction execution, acceptance/merge, external truth, distributed writers,
   database corruption, and hostile same-UID/root mutation.
4. **Assurance level:** closed four-route local atomic/idempotent persistence
   with exact readiness coverage, reviewer independence, disposition-pending
   routing, failure seams, contention, and restart proof.
5. **Acceptance proof:** the thirteen named tests, total 248-test inventory,
   ten-run stress group, compilation, candidate-union, allowlist, staged
   hygiene, artifact, and sensitive-value checks are sufficient.
6. **Implementation boundary:** only the two named paths, Python standard
   library, and existing Maestro record/event helpers; no dependency/process.
7. **Proportionality ceiling:** one method and one thirteen-test module; no
   schema, generic review framework, correction, executor, or policy redesign.
8. **Stop and escalation rule:** return on any need for another route, record,
   command, path, carrier, event, dependency, or external fact. At most one
   planning and one implementation correction. Merge uses standing point-1
   authority only after exact-candidate readiness and independent approval.
