# M1 Review Control Routing

**Slice ID:** `MB-SLICE-M1-REVIEW-ROUTING-01`
**Status:** `Pending Decision Fidelity`
**Base:** `3574bf2b2c3730f167cec553439d0f08bdc85568`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-REVIEW-ROUTING-01` |
| `phase` | `PendingDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:3574bf2b2c3730f167cec553439d0f08bdc85568"]` |

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
| `AwaitingReview` | `IndependentImplementation` | `RequestChanges` | `NeedsReplan` |

All other source/kind/result combinations are prohibited and raise
`InvalidTransition`. In particular `Assemble` and `Comment` require a later
workflow, and this slice does not resume a correction.

The supplied review is the exact existing closed review record. It must name
the supplied packet, its one latest `Succeeded` attempt and that attempt's
`result_commit` as `head_commit`; use correction number 0; and use
`created_at=now`. `base_commit` must equal the packet base commit and differ
from head. `coverage_json` must be nonempty. Integration must be the first
Integration review for the packet. Independent review requires exactly one
prior `Integration/ValidateOnly` review for the same packet, attempt, base,
and head, and must be the first IndependentImplementation review.

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

Validate packet ID, expected version, full review, review/packet/time/base-head
relationships, reason, key, and actor before writing. Then use one
`BEGIN IMMEDIATE` transaction in this exact order: replay/conflict; packet
existence; packet version; route-table match; latest Succeeded attempt
existence and attempt/packet/head relationships; prior-review cardinality and
exact facts; insert review; update packet once; insert event; commit.

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
4. independent RequestChanges records one review and enters NeedsReplan;
5. the complete source/kind/result complement rejects every unlisted route;
6. packet/attempt/base/head/time/coverage/correction relationships are guarded;
7. independent review requires one exact prior validate-only Integration review;
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
   duplicated, or detached from the exact succeeded candidate and packet route.
2. **Operating and threat model:** one trusted local writer/SQLite database,
   pre-obtained review judgment, concurrent commands, crash before commit,
   duplicate/stale input, and service restart.
3. **Explicit exclusions:** reviewer quality, review launch, integration edits,
   correction execution, acceptance/merge, external truth, distributed writers,
   database corruption, and hostile same-UID/root mutation.
4. **Assurance level:** closed four-route local atomic/idempotent persistence
   with exact relationships, failure seams, contention, and restart proof.
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
