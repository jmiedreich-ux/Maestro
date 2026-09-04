# M1 Review Control Routing — Independent Candidate 05

**Slice ID:** `MB-SLICE-M1-REVIEW-ROUTING-05`
**Status:** `Pending Decision Fidelity`
**Base:** `45b50165dc66c527ab47397cbe3f7320cdd3f93a` (`origin/master`)

## Relationship to prior attempts

`MB-SLICE-M1-REVIEW-ROUTING-01` through `-04` are each terminally `returned`.
None was implemented. This slice is independent: it receives a new
identity, inherits no review or correction allowance from any of the four,
and does not reopen, correct, replace, rename, or cite them as authority.
It is written from `origin/master`'s current schema and governing decisions
only. For traceability: `-01` failed because it required candidate equality
to `packets.current_head`, which stays null after execution finish; `-02`
failed because its status carrier under-reported consumed
review/correction counts and its fingerprint was prose, not a literal
object; `-03` failed only because `findings_json` had no exact, closed item
shape, so the result/findings complement could not be mechanically
enforced; `-04` closed that gap and passed a full planning review plus one
targeted planning correction and verification, but its declared
writable-path boundary omitted one fact discovered only during
implementation dispatch: `tests/m1_02/test_schema_and_records.py`'s
`test_ar_p05_app_map_01_through_21_have_exact_per_route_mock_traces`
hard-codes exactly the permissive `findings_json` behavior this contract
closes (a `reason`-kind, non-empty finding accepted alongside
`result="ValidateOnly"`), making the 248-test acceptance proof impossible
under `-04`'s original two-path boundary. `-04`'s attempt to fix this with
an in-place "architecture-contract amendment" after freeze was independently
reviewed and correctly rejected: the Bootstrap Convergence Policy's
terminal-correction section requires a proof/contract defect discovered
against a frozen slice to terminate that slice, not receive a post-freeze
patch. `-04` is terminally returned as a result. The diagnosis and fix were
sound on their technical merits (the reviewer confirmed this); this slice
carries them forward correctly, by declaring the one-line test-fixture
substitution as an originally owned writable path from the start, subject
to this contract's own fresh, full Decision Fidelity review.

Controlling authority is the Bootstrap Convergence Policy,
`docs/planning/maestro-master-plan.md`, `docs/planning/agent-workforce-control-plane.md`
§§8.3–8.4, and M0-D01, M0-D05, and M0-D12, read from current `origin/master`.
Schema facts below are quoted from `services/maestro/maestro/storage.py` and
`services/maestro/maestro/operational_state.py` at the base commit above.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-REVIEW-ROUTING-05` |
| `phase` | `PendingImplementation` |
| `current_actor` | `MaestroDeveloper` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:45b50165dc66c527ab47397cbe3f7320cdd3f93a","git:full-planning-review-head:c2ede3e72fce6cf2c94b02d18a527b67bdeb642e","review:decision-fidelity:approve:no-findings","history:MB-SLICE-M1-REVIEW-ROUTING-01:returned:non-authoritative","history:MB-SLICE-M1-REVIEW-ROUTING-02:returned:non-authoritative","history:MB-SLICE-M1-REVIEW-ROUTING-03:returned:non-authoritative","history:MB-SLICE-M1-REVIEW-ROUTING-04:returned:non-authoritative:app-map-11-boundary-gap"]` |

The planning contract is now frozen at `c2ede3e72fce6cf2c94b02d18a527b67bdeb642e`, approved with zero findings and zero corrections. Passing its named acceptance proof is enough; implementation may not silently strengthen it.

Counts are monotonic and start at zero because no review of this slice's
contract has occurred yet. `phase` advances only on a recorded event: a
complete Decision Fidelity review sets `planning_review_count=1`; an
authorized correction sets `phase=PendingTargetedDecisionFidelity` and
`planning_correction_count=1`; a passed targeted verification sets
`phase=PendingImplementation`; a failed one sets `terminal_state=returned`
and stops. No later transition may report a nonzero count for a review or
correction that has not actually occurred.

## Candidate authority

The reviewed candidate commit is always `attempts.result_commit` for the
packet's current `Succeeded`, `Initial` attempt (`attempt_number=1`,
`correction_for_review_id IS NULL`). `packets.current_head` is out of scope:
it has no writer in the current schema and remains `NULL` through this
slice. No command in this slice reads, writes, or gates on
`packets.current_head`. A review's `head_commit` must equal that attempt's
`result_commit`; `base_commit` must equal the packet's `base_commit`.

## Closed command and routes

Implement exactly one new function in `operational_state.py`:

```text
record_and_route_review(
  packet_id, expected_packet_version, review, reason_payload,
  idempotency_key, actor, now
) -> {"packet": <five-key state>, "review": <validated review row>}
```

The four routes, and only these four, transition the packet:

| From | Review kind | Result | To |
|---|---|---|---|
| `AwaitingIntegration` | `Integration` | `ValidateOnly` | `AwaitingReview` |
| `AwaitingIntegration` | `Integration` | `NeedsReplan` | `NeedsReplan` |
| `AwaitingReview` | `IndependentImplementation` | `Approve` | `MergeReady` |
| `AwaitingReview` | `IndependentImplementation` | `RequestChanges` | `AwaitingArchitect` |

Every other `(packet.state, review_kind, result)` combination raises
`InvalidTransition`. `RequestChanges` never itself authorizes a correction or
a replan; the Project Architect's disposition (recorded in the finding, see
below) is what a later correction-dispatch command reads. This slice does
not dispatch a worker, open a correction attempt, or perform acceptance.

An `Approve` route requires the packet's `correction_count` to already be
`0` or `1` (both are legal packet states going into review; this slice does
not increment or reset `correction_count`). An `Approve` on a review whose
`findings_json` is non-empty is `InvalidRecord`, not routed and not silently
accepted with limitations — that composite command does not exist in this
slice.

## Guards, before any route is taken

1. Packet exists and `version == expected_packet_version`, else `StaleState`.
2. Packet has exactly one attempt with `state='Succeeded'`,
   `attempt_kind='Initial'`, `attempt_number=1`, non-null `result_commit`;
   otherwise `InvalidRecord`.
3. `review.base_commit == packet.base_commit` and
   `review.head_commit == attempt.result_commit` and
   `review.head_commit != review.base_commit`.
4. `review.correction_number == 0` (this slice does not cover a
   correction-review pass; that is a separate later slice).
5. `review.reviewer_role` is exactly `IntegrationAgent` for an `Integration`
   review or `IndependentImplementationReviewer` for an
   `IndependentImplementation` review.
6. Reviewer independence: `review.reviewer_instance` differs from the
   attempt's `model_identity`, `runtime_identity`, and the packet's lease
   `holder_id`. For an `IndependentImplementation` review, it also differs
   from the `reviewer_instance` of the prior matching `Integration` review.
7. Exactly one prior `Integration` review with `result='ValidateOnly'` on the
   same `packet_id` and `head_commit` exists before an
   `IndependentImplementation` review for that packet/head may route.
8. `review.coverage_json` is a closed object with exactly the keys `kind`
   and `result`: `kind="review-readiness-coverage"`; `result` is the
   complete, unmodified `maestro.review-readiness.result/v1` object as
   produced by `review_readiness.evaluate_review_readiness`. Validate it
   with the existing `review_readiness` result parser and additionally
   require: `ready=true`; `blockers=[]`; every entry in `checks` has
   `outcome="Passed"`; `request.review_kind` equals `"IndependentImplementation"`
   for both review kinds this slice covers. The review-readiness gate's
   closed `review_kind` enum (`DecisionFidelity`, `TargetedDecisionFidelity`,
   `IndependentImplementation`, `TargetedImplementation`, per
   `review_readiness._REVIEW_KINDS`) has no `"Integration"` value and no
   separate phase for an `Integration`-kind `reviews` row — it is a
   different, gate-invocation-phase enum, not the `reviews.review_kind`
   column's `('Integration','IndependentImplementation')` enum, and the two
   must not be conflated. Both operational review kinds this slice routes
   independently prove the same thing (the implementation candidate at
   `review.head_commit` is clean and fully tested), so both require coverage
   tagged `request.review_kind="IndependentImplementation"`;
   `resolved_base`/`resolved_head` equal `review.base_commit`/`review.head_commit`;
   `checked_out_head_before` and `checked_out_head_after` both equal
   `review.head_commit`; `clean_before`/`clean_after` are both true;
   `changed_paths` is nonempty and sorted; `request.allowed_paths` equals
   the packet's `owned_paths_json`, sorted. Any mismatch is `InvalidRecord`,
   not a route.
9. Every item of `review.findings_json` validates against the closed finding
   shape below. The result/findings complement (also below) holds exactly.

Any guard failure raises `InvalidRecord` (malformed/missing/mismatched
facts, closed-coverage failure, independence failure, missing prior
`ValidateOnly`) or `StaleState` (version mismatch) before any write occurs.

## Closed finding payload

`reviews.findings_json` is already a schema-level JSON array
(`storage.py`, `CREATE TABLE reviews`); today `_review()` validates each
item only as *some* existing closed `validate_payload` kind. This slice adds
one new closed kind, `review-finding`, to the `shapes` mapping in
`validate_payload()` (`operational_state.py`), and tightens `_review()` to
require every `findings_json` item to have `kind == "review-finding"`
specifically — a well-formed item of any other existing closed kind
(`state`, `claim`, `reference`, `evidence-reference`,
`measurement-reference`, `redacted-text`, `notification`, `reason`) is
rejected exactly like a malformed one.

Exact shape (closed keys: `kind`, `finding_id`, `criterion_reference`,
`evidence`, `disposition`):

```json
{
  "kind": "review-finding",
  "finding_id": "DF-01",
  "criterion_reference": "M0-D05#worker-routing",
  "evidence": {
    "kind": "evidence-reference",
    "evidence_id": "...",
    "digest": "<64-hex>",
    "source_reference": null
  },
  "disposition": {
    "kind": "reason",
    "reason_code": "CorrectNow",
    "detail_reference": null
  }
}
```

Validation, reusing existing primitives rather than duplicating them:

- `finding_id` and `criterion_reference`: `_text`, 1–512 UTF-8 bytes.
- `evidence`: recursively validated by the existing `validate_payload`; its
  `kind` must equal `"evidence-reference"` exactly, else `InvalidRecord`.
  This is the evidence context — it points at a durable `evidence` row or
  external reproduction reference; it does not embed prose.
- `disposition`: recursively validated by the existing `validate_payload`;
  its `kind` must equal `"reason"` exactly. Layered on top of the generic
  `reason` shape (which this slice does not change for its other callers),
  `disposition.reason_code` must be exactly one of `CorrectNow`,
  `AcceptKnownLimitation`, `RejectFinding`, `ReturnSlice` — the four
  dispositions in the Bootstrap Convergence Policy's risk-based finding
  disposition. When `reason_code == "AcceptKnownLimitation"`,
  `detail_reference` (the linked backlog issue) must be non-null; for the
  other three it is optional.
- No other keys are permitted on the finding object itself, on `evidence`,
  or on `disposition` beyond what `validate_payload` already closes for
  `evidence-reference` and `reason`.

## Result/findings complement

Enforced in `_review()`, for every `review_kind`:

- `result in {"Approve", "ValidateOnly"}` requires `findings_json == []`.
  A single well-formed `review-finding` present with either result is
  `InvalidRecord`.
- `result in {"RequestChanges", "NeedsReplan"}` requires
  `len(findings_json) >= 1`, every item well-formed per the shape above.
  An empty array with either result is `InvalidRecord`.
- `result in {"Assemble", "Comment"}` is unchanged by this slice: no
  complement is enforced, and no route exists for either result in the
  table above (out of scope; a future slice may cover them).

This makes the four positive/negative cases mechanical: `Approve` and
`ValidateOnly` cannot carry a finding; `RequestChanges` and `NeedsReplan`
cannot omit one; a finding of the wrong `kind`, or missing a required key,
never reaches storage regardless of `result`.

## Pre-existing fixture made consistent (owned from the start)

`tests/m1_02/test_schema_and_records.py`,
`test_ar_p05_app_map_01_through_21_have_exact_per_route_mock_traces`,
currently contains (as of the base commit above):

```python
review = dict(valid["_review"], findings_json=[{"kind": "reason", "reason_code": "NONE", "detail_reference": None}])
trace("APP-MAP-11", lambda: OperationalStateStore._review(review))
```

where `valid["_review"]["result"] == "ValidateOnly"` (captured from the
fixture at that test's own `review = {...}` literal, `result: "ValidateOnly"`).
This is unconditionally incompatible with the result/findings complement
above (`ValidateOnly` cannot carry a finding) and with the closed-kind
requirement (`reason` is not `review-finding`) — it asserts exactly the
permissive behavior this slice closes. This is a real, named, in-scope
fact of this contract, not a later discovery: this file is a third owned
writable path, for exactly one substitution:

```python
review = dict(
    valid["_review"],
    result="RequestChanges",
    findings_json=[{
        "kind": "review-finding", "finding_id": "test-app-map-11",
        "criterion_reference": "test-fixture",
        "evidence": {
            "kind": "evidence-reference", "evidence_id": "test-evidence",
            "digest": "0" * 64, "source_reference": None,
        },
        "disposition": {
            "kind": "reason", "reason_code": "CorrectNow",
            "detail_reference": None,
        },
    }],
)
```

No other line of that file, and no other test anywhere in the suite, may
change. The `("APP-MAP-11", "R09")` relation check (same file) already
accepts any of the six `result` values and only requires `findings_json`
to be a list, so this substitution preserves that test's original coverage
intent — it still proves `_review()` validates and iterates
`findings_json` items — without asserting the now-superseded permissive
behavior. This is a one-line, mechanical, pre-specified substitution, not
open-ended license to edit that file.

## Exact canonical fingerprint input

```json
{"actor":{"actor_id":"...","actor_type":"...","causation_event_id":null,"correlation_id":"..."},"operation":"record_and_route_review","payload":{"expected_packet_version":8,"packet_id":"...","reason":{"detail_reference":null,"kind":"reason","reason_code":"..."},"review":<fully validated closed review row>}}
```

The literal keys, nesting, `"operation"` value, and canonical UTF-8 JSON key
ordering (`canonical_json`, sort_keys, no whitespace) are part of the
contract. `now` supplies only the review's `created_at`; no other clock
value is read. Replay: on a repeated `idempotency_key`, if the recomputed
fingerprint matches the stored one, return the identical stored result
without re-executing guards; if it differs, raise `IdempotencyConflict`.

## Transaction precedence, rollback, concurrency, restart

One `BEGIN IMMEDIATE` transaction, in this exact order: (1) idempotency
replay/conflict check; (2) packet existence and version; (3) route lookup;
(4) latest-attempt and `result_commit` guard; (5) closed coverage
validation; (6) reviewer-role and independence checks; (7) prior-review
cardinality check; (8) `reviews` row insert; (9) `packets` row update
(state only — `current_head`, `correction_count`, and all other columns are
untouched by this slice); (10) event insert; (11) commit. A failure at
step 8, 9, or 10 rolls back the entire transaction; no partial write is
observable. Under `SQLite` `BEGIN IMMEDIATE` contention, exactly one
concurrent caller wins the write lock; the loser retries or surfaces
`ResourceBusy` after the existing busy-timeout policy, with no residue.
After a crash or restart, re-invoking the identical command with the same
`idempotency_key` reconstructs the same stored result via replay; no
duplicate `reviews` row, packet update, or event is created.

Errors: `InvalidRecord` for malformed/missing/mismatched facts, closed
finding/coverage failure, or complement violation; `StaleState` for a
packet-version mismatch; `InvalidTransition` for a route outside the four
listed; `IdempotencyConflict` for a reused key with changed facts;
`ResourceBusy` after write-lock contention exhausts the retry policy.

## Exact persisted event envelope

```text
entity_type="Packet"
entity_id=<packet_id>
event_type="ReviewRecorded"
before_json={"packet": <exact five-key source packet state>}
after_json={"packet": <exact five-key resulting packet state>, "review": <exact stored review row>}
reason=<the supplied reason payload, kind="reason">
actor=<the supplied actor object>
```

The event's idempotency key, fingerprint, `correlation_id`, and
`causation_event_id` are exactly the command's own facts; no alternate
envelope shape is produced. This is the reconstruction oracle for tests 10,
12, and 13 below.

## Boundary, proof, and M0-D12

Writable paths are exactly `services/maestro/maestro/operational_state.py`,
`tests/m1_02/test_review_control_routing.py` (new file), and
`tests/m1_02/test_schema_and_records.py` (solely for the one substitution
specified above, in `test_ar_p05_app_map_01_through_21_have_exact_per_route_mock_traces`).
No other file changes.

The thirteen named tests, in
`tests/m1_02/test_review_control_routing.py` following the repository's
`test_NN_<description>` convention:

1. `test_01_each_of_the_four_routes_records_the_exact_result_and_state` —
   each listed route, given valid guards, produces exactly its listed
   packet state and a stored review row matching the input.
2. `test_02_every_route_outside_the_closed_table_raises_invalid_transition` —
   every other `(state, review_kind, result)` combination rejects.
3. `test_03_approve_and_validate_only_require_empty_findings` — `Approve`
   and `ValidateOnly` succeed only with `findings_json=[]`; either with one
   well-formed finding present is `InvalidRecord`.
4. `test_04_request_changes_and_needs_replan_require_at_least_one_finding` —
   `RequestChanges` and `NeedsReplan` succeed only with one or more
   well-formed findings; either with `findings_json=[]` is `InvalidRecord`.
5. `test_05_malformed_or_unrelated_finding_variants_are_rejected` — a
   finding missing a required key, an unknown `kind`, a nested `evidence`
   or `disposition` of the wrong sub-kind, an `AcceptKnownLimitation`
   disposition with a null `detail_reference`, and a well-formed item of an
   existing unrelated closed kind (for example `kind="state"`) each reject.
6. `test_06_packet_attempt_commit_base_head_and_correction_guards_reject` —
   version mismatch, no `Succeeded` initial attempt, wrong `base_commit`,
   `head_commit` not equal to `result_commit`, equal base/head, and
   nonzero `correction_number` each reject.
7. `test_07_closed_coverage_accepts_only_a_complete_matching_ready_result` —
   a `ready=true`, zero-blocker, all-`Passed` coverage object matching the
   review's kind/base/head/paths is accepted; malformed, `ready=false`,
   nonempty `blockers`, mismatched base/head/paths, dirty, or digest-altered
   coverage each reject.
8. `test_08_reviewer_role_and_independence_relationships_reject_mismatches` —
   wrong `reviewer_role` for the review kind, and each independence
   relationship (model identity, runtime identity, lease holder, prior
   Integration reviewer) collapsing to the same instance, each reject.
9. `test_09_independent_implementation_requires_one_prior_validate_only` —
   an `IndependentImplementation` review routes only with exactly one prior
   matching `Integration` `ValidateOnly` review on the same packet/head;
   zero or more than one rejects.
10. `test_10_fingerprint_replay_is_exact_and_changed_facts_conflict` — a
    repeated call with the same `idempotency_key` and identical facts
    returns the identical stored result without re-inserting; a changed
    fact under the same key raises `IdempotencyConflict`.
11. `test_11_review_event_or_packet_update_failure_rolls_back_atomically` —
    a forced failure at each of the three write steps leaves no partial
    row in `reviews`, `packets`, or `events`.
12. `test_12_concurrent_routing_calls_have_one_winner_and_no_residue` — run
    in ten fresh processes; concurrent calls on the same packet/head produce
    exactly one committed result and no orphaned rows.
13. `test_13_restart_preserves_exact_replay_and_reconstruction` — run in
    ten fresh processes; after a simulated restart, replaying the same
    command reconstructs the identical review row, packet state, event, and
    fingerprint from stored facts alone.

Run the existing 235 named tests plus these 13 (248 total, unchanged in
count by the one-line fixture substitution above, which edits an existing
test rather than adding or removing one); run tests 10–12 in ten fresh
processes each; run `python -m compileall -q maestro ../../tests/m1_01
../../tests/m1_02 ../../tests/review_readiness` from `services/maestro`
with an external, isolated `PYCACHEPREFIX`; and run exact candidate hygiene
(tracked-plus-untracked path enumeration against the three-path allowlist
above, `git diff --cached --check`, and exact commit-range verification)
before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** only a mechanically ready, independently reviewed
   candidate can move a packet toward `MergeReady` or `AwaitingArchitect`;
   every finding that blocks or defers a packet carries closed evidence and
   disposition context an Architect can act on without re-deriving it from
   prose.
2. **Operating and threat model:** a trusted local single-writer SQLite
   process; stale, duplicate, and concurrent command submission; process
   crash and restart between steps.
3. **Explicit exclusions:** reviewer competence/judgment quality,
   correction-attempt dispatch, Project Architect disposition execution,
   `acceptance`/`merge_observation` recording, `Assemble`/`Comment` review
   results, any schema or execution-runtime change, external/network
   access, Atlas, and any M1-03 or later behavior. Also excluded: any
   change to `test_schema_and_records.py` beyond the one specified
   substitution — its other 20 `APP-MAP` traces, all `APP-REL` and
   `APP-FK` cases, and every other test in that file are untouched and
   remain this slice's regression baseline, not its scope.
4. **Assurance level:** closed four-route atomic, idempotent persistence
   with exact coverage validation, reviewer independence, rollback,
   contention, and restart proof — proportionate to an internal
   trusted-caller primitive, not an externally adversarial boundary.
5. **Acceptance proof:** the 13 named tests, the 248-test full inventory,
   the two ten-fresh-process stress groups, `compileall`, and exact
   candidate hygiene, all passing.
6. **Implementation boundary:** exactly the three writable paths listed
   above; only the Python standard library and this module's existing
   helpers (`validate_payload`, `canonical_json`, `canonical_digest`,
   `_fingerprint`, `_closed_mapping`, `_text`, `_commit`, existing
   `review_readiness` parsing). No new dependency, table, or column.
7. **Proportionality ceiling:** one new function, one new closed payload
   kind, one tightened validator, one new test module, and one pre-specified
   one-line fixture substitution in an existing test; no redesign of
   `packets`, `attempts`, `reviews`, `acceptance`, `merge_observation`, or
   any other existing test.
8. **Stop and escalation rule:** if a fact needed to close a guard is
   missing from the current schema, if a route beyond the four listed
   proves necessary, if any writable-path edit beyond the three named above
   proves necessary, or if a reserved product/security/data decision
   surfaces, stop and return to the Project Architect rather than widening
   this contract in place — per the Bootstrap Convergence Policy, a
   discovered proof/contract defect against a frozen slice terminally
   returns that slice; it is not patched in place. One planning correction
   and one implementation correction are the maximum available to this
   slice; a second failure of either follows the same terminal-return rule.
