# M1 Review Control Routing — Candidate-Head Authority

**Slice ID:** `MB-SLICE-M1-REVIEW-ROUTING-02`
**Status:** `Pending Decision Fidelity`
**Base:** `e7f7f98374f11be76c3fff34e31162c52880409c`

## Durable slice status

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-REVIEW-ROUTING-02` |
| `phase` | `PendingDecisionFidelity` |
| `current_actor` | `DecisionFidelityReviewer` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:e7f7f98374f11be76c3fff34e31162c52880409c","readiness:9336a4af1e6f7dffb1e529b6fd6ab774f568685cd7c74f7e0e94e88230774b8e"]` |

Counts are monotonic and are never reset by a correction or branch change.

## Controlling authority

The controlling records are the Bootstrap Convergence Policy
(`docs/planning/bootstrap-convergence-policy.md`), Maestro Master Plan
(`docs/planning/maestro-master-plan.md`), Agent Workforce Control Plane
(`docs/planning/agent-workforce-control-plane.md`, §§8.3–8.4), M0-D01,
M0-D05, and M0-D12. Current status and handoff records are read from
`origin/master` at execution. The terminal
`MB-SLICE-M1-REVIEW-ROUTING-01` is history only and supplies no authority.

## Outcome

Add one trusted-caller `OperationalStateStore.record_and_route_review(...)`
command that durably records a validated Integration or independent
implementation review and atomically routes the packet. This is a new,
independent slice; the returned `MB-SLICE-M1-REVIEW-ROUTING-01` is immutable and
non-authoritative.

## Closed behavior

The four routes are:

| Source | Review | Result | Target |
|---|---|---|---|
| `AwaitingIntegration` | `Integration` | `ValidateOnly` | `AwaitingReview` |
| `AwaitingIntegration` | `Integration` | `NeedsReplan` | `NeedsReplan` |
| `AwaitingReview` | `IndependentImplementation` | `Approve` | `MergeReady` |
| `AwaitingReview` | `IndependentImplementation` | `RequestChanges` | `AwaitingArchitect` |

All other combinations are `InvalidTransition`. `RequestChanges` never
authorizes correction or replan; a later Project Architect disposition is
required.

The exact command is:

```text
record_and_route_review(
  packet_id, expected_packet_version, review, reason_payload,
  idempotency_key, actor, now
) -> {
  "packet": {"entity_id": <id>, "entity_type":"Packet", "kind":"state",
             "state": <target>, "version": <new integer>},
  "review": <the exact validated review row>
}
```

The returned object has exactly `packet` and `review` keys. The review row has
the closed review schema already enforced by `_review`, including findings and
coverage. The event has `event_type=ReviewRecorded`, the exact five-key packet
state before and after, the exact returned object as `after_json`, and supplied
reason/actor facts. The idempotency fingerprint is canonical SHA-256 over
operation, all supplied payload facts (including the fully validated review,
expected packet version, reason, and actor), and no hidden clock; `now` is the
review `created_at`. Replay precedes mutable checks and returns the identical
stored result; changed facts raise `IdempotencyConflict`.

Validation and error precedence are closed: malformed fields or payloads and
missing/mismatched records are `InvalidRecord`; stale packet version is
`StaleState`; prohibited state/kind/result/order is `InvalidTransition`; changed
key reuse is `IdempotencyConflict`; SQLite busy exhaustion is `ResourceBusy`;
integrity failure is `InvalidRecord`. Within one `BEGIN IMMEDIATE` transaction,
the order is replay/conflict, packet existence/version, route match, latest
Initial Succeeded attempt and its `result_commit`, readiness coverage and
reviewer independence, prior-review cardinality, review insert, packet update,
event insert, and commit. Any failure rolls back all three writes. Concurrent
commands from one packet version have exactly one winner and no loser residue;
restart preserves the committed row/event and exact replay.

The latest `Succeeded` attempt must be `Initial`, correction number must be 0,
and `review.head_commit` must equal that attempt's non-null `result_commit`.
`review.base_commit` must equal the packet base and differ from head. The
packet's `current_head` is not used: materialization deliberately requires it
to be null and execution finish records candidate authority in
`attempts.result_commit`.

`coverage_json` is closed to exactly `{ "kind": "review-readiness-coverage",
"result": <complete maestro.review-readiness.result/v1 object> }`. The result
must validate with `review_readiness.validate_result`, be ready with no
blockers, contain only passed checks, and bind request/resolved base and head,
checked-out heads, changed paths, clean observations, and allowlist to the
review and packet. The request review kind is
`IndependentImplementation`. Integration uses role `IntegrationAgent`;
independent review uses `IndependentImplementationReviewer`. The reviewer
instance must differ from attempt model/runtime identities, lease holder, and
(for independent review) the prior Integration reviewer instance.

Persist one immutable review, one packet update, and one `ReviewRecorded`
event in a single transaction with exact idempotent replay and rollback.

## Boundary and proof

Writable paths are exactly:

- `services/maestro/maestro/operational_state.py`
- `tests/m1_02/test_review_control_routing.py`

The new test module contains exactly these thirteen tests:

1. Integration ValidateOnly records one review and enters AwaitingReview;
2. Integration NeedsReplan records one review and enters NeedsReplan;
3. independent Approve records one review and enters MergeReady;
4. independent RequestChanges records one review and enters AwaitingArchitect;
5. every unlisted source/kind/result route is rejected;
6. packet/version/Initial-attempt/base/head/time/correction guards reject;
7. closed readiness result, digest, clean state, paths, checks, and allowlist
   are required and bound to the attempt candidate;
8. exact reviewer roles and instance independence from model/runtime/lease and
   prior Integration reviewer are required;
9. exactly one prior matching Integration ValidateOnly review is required;
10. stale state, wrong state, duplicate kind, missing records, and malformed
    review facts reject with no residue;
11. replay is exact and every changed immutable fact conflicts;
12. injected review/event/update failures roll back the whole command; and
13. concurrent commands and restart preserve one winner, event/result
    reconstruction, and exact replay.

Run the full current inventory plus these thirteen tests (248 total), tests
12–13 in ten fresh processes, compileall with external pycache, and exact
candidate hygiene.

Excluded: packet-current-head mutation, schema changes, execution/lease changes,
review launching, correction execution, acceptance/merge, external access,
Atlas, policy expansion, and M1-03.

## M0-D12 contract

1. **Protected outcome:** exact ready-candidate-bound review routing, with
   independent identity and Architect control over `RequestChanges`.
2. **Operating/threat model:** one trusted local SQLite writer; duplicate,
   stale, concurrent, crash, and restart conditions.
3. **Explicit exclusions:** reviewer launch/quality, correction execution,
   acceptance/merge, schema/execution changes, external access, Atlas, and
   M1-03.
4. **Assurance level:** closed four-route atomic/idempotent persistence with
   exact readiness coverage, independence, rollback, contention, and restart.
5. **Acceptance proof:** thirteen named tests, 248-test inventory, stress,
   compilation, and candidate hygiene.
6. **Implementation boundary:** exactly the two writable paths above, standard
   library and existing Maestro helpers only.
7. **Proportionality ceiling:** one command and one thirteen-test module; no
   schema, launcher, correction, or policy redesign.
8. **Stop/escalation:** return on a new route, record, dependency, path,
   reserved decision, or inability to prove the protected outcome; one planning
   and one implementation correction maximum. Merge requires exact readiness
   and independent approval under standing point-1 authority.
