# M1 Review Control Routing — Candidate-Head Authority

**Slice ID:** `MB-SLICE-M1-REVIEW-ROUTING-02`
**Status:** `Pending Decision Fidelity`
**Base:** `e7f7f98374f11be76c3fff34e31162c52880409c`

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

The thirteen existing named tests are retained, with coverage and independence
cases closed as subcases. Run the full current inventory (including review
readiness), focused tests, ten fresh-process runs for rollback/concurrency/
restart, compileall with external pycache, and exact candidate hygiene.

Excluded: packet-current-head mutation, schema changes, execution/lease changes,
review launching, correction execution, acceptance/merge, external access,
Atlas, policy expansion, and M1-03.

## M0-D12 contract

Protected outcome is exact candidate-bound, independent, idempotent review
routing with Architect control over `RequestChanges`. Threat model is the
existing trusted local SQLite writer, duplicate/stale/concurrent commands,
crash, and restart. Acceptance is the named thirteen-test proof plus existing
regressions, stress, compilation, and hygiene. One implementation review and
at most one implementation correction are allowed; no planning correction is
authorized until the complete Decision Fidelity review returns findings.
