# M1-02B — Lifecycle, Claims, and Recovery

**Status:** `PendingDecisionFidelity`; `NotDispatchable`; rematerialized
planning candidate only
**Packet ID:** `maestro-m1-02b-lifecycle-claims-recovery`
**Stable node ID:** `MAESTRO-M1-02B-LIFECYCLE-CLAIMS-RECOVERY`
**Graph revision:** `maestro-m1-m4-real-r1`
**Planning source authority:** current accepted M0-D05/M0-D12/M0-D15/M0-D16/
M0-D17 records and active handoff; this candidate is not an authority release
**Implementation base:** `d82164c2f3be2164ad6e66b022f645be5f61844b`
**Typed dependency:** `hard: MAESTRO-M1-02A-SCHEMA-RECORDS-VALIDATION @
ProjectArchitectAccepted`, satisfied only by routine combined M1-02A+AR
Project Architect acceptance at the exact implementation base above
**Closed-completion authority:** [M0-D16](../decisions/m0-d16-closed-completion-and-learning-loop.md)
and [M0-D17](../decisions/m0-d17-discretionary-final-correction.md), which
amends the correction lifecycle for this later packet
**Roles:** Coordinator dispatches; dedicated Maestro Developer implements;
Integration validates; fresh Independent Reviewer reviews; Project Architect
accepts and routes only an M0-D15 reserved choice to Owner.

## Candidate and authority boundary

This packet materializes only M1-02B from the approved
[M1-02 umbrella](m1-02-operational-state-and-recovery-primitives.md) and graph
row. It owns proof groups 7–22/30–31, the B remainder of 23, and proof 24's
packet-policy binding before `Running`. Accepted M1-02AR and Alpha/M1-01 proofs
remain gates; C remains separate.

The M1-02A+AR acceptance record fixes this exact base. This candidate is still
not dispatchable: Decision Fidelity must approve its complete current-authority
contract and the Project Architect must release that exact reviewed packet. Any
base/schema/API/review-coverage difference returns to the Project Architect;
the Coordinator does not translate it.

Controls: M0-D01..D06/D11/D12/D14/D15/D16/D17, umbrella packet, Master Plan,
control plane, active `ai/handoffs/current.md`, plan B row, and
`docs/agents/{maestro-developer,coding-agent-sop,integration-agent,
independent-review-agent,decision-fidelity-reviewer,
maestro-development-manager}.md`. M0-D15/current handoff control conflicts.

## Dispatch contract

| Field | Fixed value |
|---|---|
| Outcome | Atomic transitions/events, claims/leases/locks, rollback, notification/acceptance/merge guards, stale/restart recovery, and durable M0-D16/M0-D17 completion/correction/return/learning records |
| Non-goals | C/docs; scheduler/worker; Git/GitHub; create/register; Atlas; delivery; merge execution/deploy; USB/network/credentials/live projects; any product/authority-policy redesign beyond the fixed schema-5 correction carrier |
| Priority / order | `P0`; serial after accepted AR only |
| Branch / worktree | `implementation/m1-02b-lifecycle-claims-recovery` / `/home/jeremy/Development/Maestro-m1-02b-implementation`, clean from resolved accepted AR head |
| Route | `codex-cloud-maestro-developer`; Integration `validate-only`; fresh high-risk state/concurrency review |
| Envelope | one 150-minute initial attempt; one normal combined-finding correction and only one M0-D17 Project-Architect-authorized final correction when every closed eligibility fact passes; never a third |
| Context | minimum 32,768 + 8,192 reserve; capacity >=40,960; warn 16,384, checkpoint 12,288, stop 8,192; dispatch-only |
| Locks | `shared:sqlite-schema`, `path:maestro-operational-state`, `path:maestro-recovery`, `file:services-maestro-storage`, `path:tests-m1-02` |
| Downstream | routine B acceptance opens only C from the exact B head |

Release requires this resolved base, Decision Fidelity `APPROVE`, Project
Architect release, supported environment, and atomic locks. No overlapping
writer may hold a declared domain.

## Owned paths

```text
services/maestro/maestro/storage.py
services/maestro/maestro/operational_state.py
services/maestro/maestro/recovery.py
tests/m1_02/test_transitions_and_claims.py
tests/m1_02/test_recovery.py
tests/m1_02/test_acceptance_and_notifications.py
```

No other path may change, including planning/roles, docs, predecessor tests,
CLI, project/manifest/Git modules, packaging, workers, Atlas, or adapters.

## Closed APIs and command semantics

```text
transition_graph_projection(id,expected_state,expected_version,next_state,source_reference,key,actor,now)
transition_run(id,expected_state,expected_version,next_state,reason,key,actor,now)
transition_packet(id,expected_state,expected_version,next_state,reason,correction_reference,key,actor,now)
claim_packet(id,expected_version,lease,lock_requests,key,actor,now)
heartbeat_lease(id,expected_version,heartbeat_at,expires_at,key,actor)
release_lease(id,expected_version,disposition,reason,key,actor,now)
transition_attempt(id,expected_state,expected_version,next_state,result_commit,reason,evidence_reference,lease_id,key,actor,now)
transition_wait(id,expected_state,expected_version,next_state,reason,evidence_reference,key,actor,now)
record_review(review,key,actor,now)
transition_notification(id,expected_state,expected_version,next_state,delivery_facts,key,actor,now)
record_acceptance(record,key,actor,now)
record_merge_observation(record,key,actor,now)
record_completion_manifest(evidence,actor)
record_standard_correction(correction,evidence,actor,now)
record_final_correction_gate_review(review,key,actor,now)
authorize_discretionary_final_correction(correction,pa_authorization,evidence,actor,now)
create_final_correction_attempt(correction_id,attempt,key,actor,now)
transition_final_correction_attempt(id,expected_state,expected_version,next_state,result_commit,reason,evidence_reference,key,actor,now)
record_return(evidence,expected_state,expected_version,wait,actor,now)
record_resolution(evidence,wait_id,expected_wait_version,actor,now)
record_learning(evidence,actor)
snapshot(entity_type,entity_id)
events_after(event_id,limit)
RecoveryService(store)
RecoveryService.reconcile_startup(recovery_run_id,now,actor)
RecoveryService.record_attempt_observation(attempt_id,lease_id,observation,key,actor,now)
```

The store accepts only `RuntimeConfig` and reconstructs it; RecoveryService
accepts only that validated store. No route accepts a path/connection/database.
Connections retain directory-FD containment, WAL, foreign keys, 5,000 ms busy
timeout, and physical repository `var/`.

Mutations validate before `BEGIN IMMEDIATE`, resolve exact replay before stale
checks, apply expected state/version, write one atomic result and ordered event,
then commit once. A correction record is created before, and is the only route
that can authorize a correction attempt. Only normal correction #1 increments
the accepted schema-4 `packets.correction_count`; schema-5 correction records
are authoritative for the two-correction maximum.
The final-correction API accepts only `ProjectArchitect` acting under recorded
routine authority, and only after it validates every frozen M0-D17 eligibility
fact. Same-key/different-facts -> `IdempotencyConflict`; stale ->
`StaleState`; collision -> `ResourceConflict`; exhausted busy timeout ->
`ResourceBusy`; none retries or mutates. Test seams `after_entity_write` and
`after_event_write` cover ordinary/non-claim commands; claim also exposes
`after_lease`, `after_lock:<ordered-index>`, and `after_event`.

## Frozen transitions and guards

The matrix is the finite allowed-edge carrier. Same-state and each ordered pair
absent from it are prohibited.

```text
Graph: Active->Stale|NeedsReplan|Superseded;
  Stale->Active|NeedsReplan|Superseded; NeedsReplan->Superseded
Run: Planned->Running|Blocked|Cancelled;
  Running->Blocked|AwaitingArchitect|AwaitingOwner|Cancelled;
  Blocked->Running|AwaitingArchitect|AwaitingOwner|Cancelled;
  AwaitingArchitect->Complete|Blocked; AwaitingOwner->Complete|Blocked
Packet: Planned->Waiting|Blocked|Ready|NeedsReplan|Cancelled;
  Waiting->Blocked|Ready|NeedsReplan|Cancelled;
  Blocked->Waiting|Ready|NeedsReplan|Cancelled;
  Ready->Dispatchable|Waiting|Blocked|NeedsReplan|Cancelled;
  Dispatchable->Leased|Ready|Blocked|NeedsReplan|Cancelled;
  Leased->Running|Blocked|Cancelled;
  Running->AwaitingIntegration|Blocked|NeedsReplan|Cancelled;
  AwaitingIntegration->AwaitingReview|Blocked|NeedsReplan;
  AwaitingReview->MergeReady|Running|Blocked|NeedsReplan;
  MergeReady->AwaitingArchitect|AwaitingOwner|Blocked;
  AwaitingArchitect->AwaitingOwner|Blocked; AwaitingOwner->Blocked;
  Merged->Complete|Blocked; NeedsReplan->Planned|Cancelled
Attempt: Planned->Running|Cancelled;
  Running->Succeeded|Failed|Cancelled|TimedOut|Stale
Wait: Open->Resolved|Expired|Cancelled
Notification: Pending->Delivered|Failed; Failed->Pending;
  Delivered->Acknowledged
```

Terminal: Graph `Superseded`; Run `Complete|Cancelled`; Packet
`Complete|Cancelled`; Attempt `Succeeded|Failed|Cancelled|TimedOut|Stale`;
Wait `Resolved|Expired|Cancelled`; Notification `Acknowledged`.

```text
B-G01 transition matches expected state/version, actor, reason, key, injected now
B-G02 Graph: newer observation for Stale; changed source for NeedsReplan;
  current hash for Stale->Active; successor revision for Superseded
B-G03 Run AwaitingArchitect: required packets Complete; snapshot non-null head/source
B-G04 Packet/Run AwaitingOwner: same-subject/head sequence-1 PA ReservedChoice
B-G05 Run Complete: packets Complete; candidate=current head; same-head Run
  acceptance; authoritative merges; post-merge gates
B-G06 correction lifecycle: initial review results create exactly one StandardCorrection
  record before correction #1; only that record authorizes `AwaitingReview->Running`/
  schema-4 attempt #2. A DiscretionaryFinalCorrection record requires the complete
  immutable Project Architect M0-D17 authorization before it authorizes its schema-5
  final-correction attempt; no generic packet transition can create either record.
B-G07 generic packet transition never enters Merged; Merged->Complete needs post-merge gate
B-G08 Attempt Running: current active lease, packet Leased|Running, committed matching context
B-G09 Attempt exit: finished_at; success commit+evidence; fail/cancel reason+evidence;
  timeout after expiry; stale non-current lease; non-success has no result commit
B-G10 Wait: resolution/evidence; expiry after timeout; cancellation authority reason
B-G11 Notification: delivery reference/time; failure error+next-at; retry due+grouping;
  each delivery/failure increments once; acknowledgement actor/time only
B-G12 acceptance and merge rules in their section
B-G13 stale/prohibited/terminal/wrong-lease/time/policy/head/coverage -> closed error,
  unchanged state/version/event history
```

## Claims, leases, and recovery

Claim resolves replay, then requires `Dispatchable`, expected version, no
active packet lease, and each sorted-unique resource key free. One transaction
inserts one Active lease and complete lock set, moves packet to `Leased`, and
appends `PacketClaimed` naming packet/lease/lock IDs. Each claim seam rolls back
the set. Same-packet concurrency yields one lease; shared-resource concurrency
yields one holder and no loser residue.

Heartbeat requires Active lease and monotonic heartbeat/expiry. Release changes
the lease and its Active locks once and does not infer packet state.

Startup reads one snapshot and processes Active leases by `lease_id`:

1. consistent/unexpired -> `ObserveActiveAttempt`, no mutation;
2. expired -> expire lease/locks, block `Leased|Running` packet, open one
   Recovery wait with `RereadAuthorityAndExecutor`, append `LeaseExpired`;
3. `Leased|Running` without matching Active lease -> block/open wait and append
   `StartupReconciliationRecorded`;
4. packet/run/base/worktree conflict -> preserve evidence, block, open
   `RecoveryConflict`, return `ReturnToCoordinator`, no replacement.

`recovery_run_id` plus entity ID derives idempotency. Repeat/reopen adds no row,
wait, lease, attempt, or event. Late observation from a non-current lease emits
one `StaleObservationIgnored` and changes no outcome. Recovery performs no Git,
worker, notification, network, selection, or redispatch.

## Notification, acceptance, merge, and completion

Sequence-1 acceptance is Project Architect `Accepted|Returned|ReservedChoice`;
Accepted/Returned are terminal. ReservedChoice requires Owner authority, named
M0-D15 choice, same-subject non-null head, and AwaitingOwner-eligible state.
Sequence 2 is Owner Accepted/Returned, supersedes sequence 1, and preserves
subject/head. Packet subject means `packet_id=subject_id,run_id=NULL`; Run is
the converse. Accepted coverage contains exact base/full review, ordered
contiguous correction ranges, final head, reviewer identity/result, and fresh
source/time. Wrong/stale/uncovered authority/subject/head facts fail.

Only `record_merge_observation` enters Packet `Merged`. Normal path requires
same-packet/head Accepted evidence. Only direct `MergeReady` permits null
acceptance and requires the active binding's reviewed `PolicyDelegated`
reference plus fresh exact-head coverage. OwnerPerformed never omits
acceptance. Repository/default branch must match active binding; caller-supplied
authoritative Git/GitHub observation must say merge commit contains accepted
head. B stores but never queries/performs the merge. Run head/completion obey
B-G05. Notification transitions obey B-G11; Slack is only stored state and
acknowledgement is not acceptance.

## M0-D16/M0-D17 records in additive schema version 5

Schema 4 cannot represent correction #2, its Project Architect authorization,
or its immutable eligibility facts. B therefore migrates additively from the
accepted schema 4 to schema 5. It neither rebuilds nor changes the meaning of
accepted rows. The migration preserves every schema-4 row/event and adds only:

```text
correction_records(
 correction_id PK, packet_id FK, correction_number CHECK 1|2,
 correction_type CHECK StandardCorrection|DiscretionaryFinalCorrection,
 initial_head, base_head, finding_ids_json, proof_ids_json, classification,
 initial_integration_review_id NULL FK reviews,
 initial_independent_review_id NULL FK reviews,
 targeted_integration_gate_review_id NULL FK correction_gate_reviews,
 targeted_independent_gate_review_id NULL FK correction_gate_reviews,
 targeted_coverage_json NULL, pa_authorization_evidence_id NULL FK evidence,
 eligibility_facts_json NULL, bounded_expected_diff_json NULL, created_at,
 UNIQUE(packet_id,correction_number)
)
final_correction_attempts(
 final_attempt_id PK, correction_id UNIQUE FK correction_records, packet_id FK,
 lease_id FK, executor_class, model_identity, runtime_identity,
 state CHECK Planned|Running|Succeeded|Failed|Cancelled|TimedOut|Stale,
 result_commit NULL, started_at NULL, finished_at NULL, version, created_at
)
correction_gate_reviews(
 correction_gate_review_id PK, correction_id FK correction_records,
 gate_kind CHECK Integration|IndependentReview, reviewer_instance,
 base_head, head_commit, result, findings_json, coverage_json, created_at,
 UNIQUE(correction_id,gate_kind,reviewer_instance,head_commit)
)
```

Schema-4 `packets.correction_count`, `attempts`, and `reviews` remain unchanged
and retain their accepted one-normal-correction constraints. They preserve the
initial attempt and normal correction exactly. The new tables are the schema-5
authoritative carrier for the second correction, its targeted gate results, and
its final attempt; no accepted table is rebuilt, reinterpreted, or widened.

For correction #1, `correction_type=StandardCorrection`, both initial terminal
review IDs are required and both targeted-review IDs are null; the finding/proof arrays are their exact sorted unique
union, and all Project-Architect-only fields are null. For correction #2,
`correction_type=DiscretionaryFinalCorrection`; it requires correction #1,
both terminal targeted gate-review IDs, a non-null immutable Project Architect
authorization evidence reference, and a closed `eligibility_facts_json` that
records each M0-D17 condition: same frozen finding/proof IDs and class; committed
in-scope normal correction; localized same-path/no-boundary change; terminal
Integration/review evidence; and the Project Architect's IDs/range/expected
diff/proportionality decision. The row rejects any absent/false fact. It also
records the exact first-correction range and intended second-correction base.

The migration adds only the event types `CorrectionRecorded`,
`DiscretionaryFinalCorrectionAuthorized`, `FinalCorrectionAttemptRecorded`, and
`FinalCorrectionAttemptStateChanged`; each correction API writes its row,
matching append-only evidence, and event in one transaction. The existing
packet count changes only for normal correction #1; the correction-record count
is authoritative for the M0-D17 maximum. `CorrectionRecorded` never grants #2;
the separate authorization event is emitted only with the valid #2 row. Existing
`CompletionManifest`, `ControlReturn`, `ControlResolution`, and
`PacketLearning` continue to use append-only evidence/events as below.

Every control API uses the accepted Evidence wrapper: `attempt_id=NULL`, the
subject packet/run, canonical payload digest, non-null source reference,
`NotRequired` redaction, matching terminal timestamp, and command idempotency
key. Return also atomically creates the matching ControlReturn wait. All new
objects are canonical JSON/1-MiB bounded, non-secret, append-only where
applicable, foreign-key safe, replay-safe, and closed to missing/extra fields.

```text
CompletionManifest={kind:"completion-manifest",packet_id,packet_revision,
 implementation_base,items:[ManifestItem],coverage:[Coverage],manifest_digest,created_at}
ManifestItem={requirement_id,proof_id,assertion_id,authority_reference,
 claim_reference,owner_role,proof_command,expected_result,evidence_format,
 allowed_states[],na_authority:null|text,na_reason:null|text,slice_id,
 owned_paths[],locks[],dependencies[],review_route}
Coverage={requirement_id,proof_ids[]}
Finding={kind:"finding",finding_id,proof_ids[],classification,summary_reference,
 evidence_references[],discovered_at}
GateCoverage={kind:"gate-coverage",manifest_digest,base_commit,head_commit,
 proof_results:[{proof_id,result,evidence_references[]}],finding_ids[],
 freshness:{status:"Fresh",observed_at,source_reference}}
StandardCorrectionEvidence={kind:"standard-correction",correction_id,packet_id,
 correction_number:1,initial_head,base_head,initial_integration_review_id,
 initial_independent_review_id,finding_ids[],proof_ids[],classification,owned_paths[],created_at}
FinalCorrectionAuthorization={kind:"discretionary-final-correction-authorization",
 correction_id,packet_id,correction_number:2,project_architect_authority_reference,
 remaining_finding_ids[],remaining_proof_ids[],classification,normal_correction_range,
 targeted_integration_review_id,targeted_independent_review_id,
 eligibility_facts,bounded_expected_diff,proportionality_reason,created_at}
ControlReturn={kind:"control-return",return_id,packet_id,exact_head,
 failed_proof_ids[],classification,responsible_authority,next_permitted_action,
 evidence_references[],observed_at}
ControlResolution={kind:"control-resolution",resolution_id,return_evidence_id,
 resolving_authority,authority_reference,resolution_reference,
 next_permitted_action,observed_at}
PacketLearning={kind:"packet-learning",packet_id,initial_head,final_head,
 elapsed_seconds,active_seconds,queue_seconds,wait_seconds,gate_seconds[],
 first_pass_result,review_count,correction_count,corrections:[{correction_id,
 correction_type,finding_ids[],proof_ids[],classification,range,coverage_reference,
 pa_authorization_evidence_id:null|text,eligibility_outcome:null|object}],
 hard_escalation,findings:[{finding_id,classification,compiler_discoverable}],
 late_requirement:null|text,absence_reason:null|text,reusable_change_kind,
 reusable_change_reference,no_general_change_reason:null|text,
 terminal_return_evidence_id:null|text,recorded_at}
```

Sets are sorted/unique. The manifest sorts by requirement/proof/assertion and
has exact two-way requirement/proof equality; a proof shared by requirements is
valid only when each `assertion_id` has its own expected result and evidence
format. `PacketLearning.wait_seconds` is null or a nonnegative integer; unknown
timing is null, never zero. A correction entry records `StandardCorrection` or
`DiscretionaryFinalCorrection`; a #2 entry must reference its authorization and
all eligibility facts. Metrics cannot alter authority, routing, quality, model,
or acceptance.

Return authority is `Coordinator|ProjectArchitect|Owner`; return classification
is `Infrastructure|ImmediateM0D05Rejection|ImplementationDefect|
ArchitectureContractDefect|NewPostCorrectionFailureClass|ExhaustedCorrection|
ReservedChoice|Complete`; next action is `Reassign|CoordinatorTakeover|
AwaitResolution|TargetedCorrection|RenewDecisionFidelity|RenewReview|
ProjectArchitectAcceptance|Stop`. A no-diff/no-commit, scope, dependency,
configuration, placeholder, unapproved #2, failed eligibility fact, or third
correction cannot mutate a correction record/count/attempt and returns through
the applicable M0-D05/M0-D17 authority route.

If an additive schema-5 migration cannot preserve schema-4 rows/events; if the
existing records cannot carry the immutable authorization/eligibility/range
facts; or if lifecycle mutation cannot stay atomic and idempotent, status is
`ArchitectureContractBlocked`. Return the exact mismatch to the Project
Architect. Do not silently weaken M0-D17 or substitute a mutable evidence blob.

## Frozen requirement/proof manifest

All proof rows share the dispatch facts above and allow only `PASS|FAIL`; no
`N/A`/`UNTESTED`. Each row below has exactly one requirement, assertion, expected
result, and evidence format. That one-to-one assertion ledger replaces the
candidate’s invalid shared mappings.

```text
B-R01 base/authority/environment/locks/scope
B-R02 additive schema-5 migration and closed public APIs
B-R03 transition/attempt/correction lifecycle guards
B-R04 atomic claim, heartbeat, release, rollback, contention
B-R05 deterministic restart reconciliation and stale observation
B-R06 notification, acceptance, merge, and Run completion authority
B-R07 M0-D11 containment and packet-context pre-Running gate
B-R08 manifest/gate/finding/normal-correction persistence
B-R09 M0-D17 final-correction authorization and lifecycle persistence
B-R10 return/resolution/learning persistence and restart
B-R11 predecessor/regression/stress and clean handoff
B-R12 terminal gates and Project Architect routine B acceptance
```

| Proof ID | Requirement / assertion | Owner | Fixed passing evidence |
|---|---|---|---|
| `B-P01` | B-R01 / exact accepted base and current authorities | Coordinator | preflight records `d82164c...`, D05/D12/D15/D16/D17, environment, locks, paths |
| `B-P02` | B-R02 / schema-4 to schema-5 migration | Developer | preserve all schema-4 rows/events, add only declared schema-5 objects, close/reopen/FK/WAL proof |
| `B-P03` | B-R02 / API replay and conflict | Developer | every listed B mutator replays exact result/event; same key/different facts leaves no mutation |
| `B-P04` | B-R03 / finite matrix guards | Developer | each listed edge passes once; all complement/terminal/stale guards fail with unchanged reopened state |
| `B-P05` | B-R03 / normal correction lifecycle | Developer | terminal initial gates create one StandardCorrection #1; it alone permits attempt #2/count 1; duplicates fail unchanged |
| `B-P06` | B-R09 / five final eligibility facts | Developer | isolated pass/fail case for each M0-D17 fact; a false/missing fact creates no #2 record/final attempt/event |
| `B-P07` | B-R09 / PA final authorization | Developer | only Project Architect with immutable authority/range/IDs/diff/proportionality evidence creates #2 authorization; wrong role/head/reference fails unchanged |
| `B-P08` | B-R09 / final correction hard limit | Developer | valid #2 alone permits one schema-5 final-correction attempt and correction-record count 2; targeted coverage is recorded; third, new class, scope breach, or unapproved #2 returns without mutation |
| `B-P09` | B-R04 / claim atomicity and contention | Developer | claim/seams/concurrent same-packet/shared-resource cases preserve one holder and no loser residue |
| `B-P10` | B-R04 / lease heartbeat and release | Developer | monotonic heartbeat and one-time release/free-lock behavior reopen correctly |
| `B-P11` | B-R05 / recovery outcomes | Developer | unexpired, expired, missing lease, conflict, repeat, and stale observation yield only the named finite outcomes |
| `B-P12` | B-R06 / notification and acceptance/merge guards | Developer | notification edges plus subject/sequence/head/coverage/ReservedChoice/merge/Run-completion pass/fail exactly |
| `B-P13` | B-R07 / containment and context gate | Developer | listed 23 constructor/API entries and two context policies prove closed rejection/pre-Running binding |
| `B-P14` | B-R08 / manifest and gate records | Developer | deterministic manifest/coverage/digest and gate arrival orders/four outcomes; missing/duplicate/orphan/stale facts reject |
| `B-P15` | B-R10 / return and resolution | Developer | return blocks/opens one wait/event; matching resolution resolves once; seams/replay/wrong authority reopen correctly |
| `B-P16` | B-R10 / complete learning carrier | Developer | Pass, immediate reject, normal correction, final correction, architecture return, and exhausted cases persist/reopen `wait_seconds`, correction types/ranges/coverage, PA authorization/eligibility outcome, terminal return, timing/cause/discoverability/late/reusable fields |
| `B-P17` | B-R11 / regression and stress | Developer + Integration | Alpha-01/02/03, M1-01/M1-02, compileall, ten fresh B processes, diff/path/artifact/secret scans all pass |
| `B-P18` | B-R11 / handoff | Developer | exact base/head, commands, proof ledger, schema migration/reopen, correction/return/learning evidence, context/usage/gaps, locks released |
| `B-P19` | B-R12 / terminal Integration | Integration | one terminal full exact-head manifest crosswalk and complete finding set |
| `B-P20` | B-R12 / terminal independent review | fresh reviewer | one full `d82164c..I0` crosswalk; each correction-only range targeted-reviewed |
| `B-P21` | B-R12 / governed follow-up | Coordinator + gates | all initial findings unioned before #1; #2 only with P06--P08 authorization; no general restart/third correction |
| `B-P22` | B-R12 / routine acceptance | Project Architect | final exact head has all proofs, Integration PASS, full coverage, clean handoff/learning, released locks, then records `Accepted` |

The finite mutator inventory is the 17 listed store mutations before `snapshot`,
the five correction/final-attempt APIs, and the two RecoveryService methods. The finite
containment inventory is those mutators, both reads, and both constructors.
No source discovery enlarges any proof member.

Coverage is exact: `B-R01->B-P01`; `B-R02->B-P02,B-P03`;
`B-R03->B-P04,B-P05`; `B-R04->B-P09,B-P10`; `B-R05->B-P11`;
`B-R06->B-P12`; `B-R07->B-P13`; `B-R08->B-P14`; `B-R09->B-P06,B-P07,B-P08`;
`B-R10->B-P15,B-P16`; `B-R11->B-P17,B-P18`; `B-R12->B-P19,B-P20,B-P21,B-P22`.
Missing, extra, orphan, or shared-without-distinct-assertion IDs are packet
errors. A later suggestion cannot change this frozen set.

## Commands, quality, return, and acceptance

From `services/maestro/`, run Alpha-01/02/03, M1-01, and M1-02 unittest
discovery, `python -m compileall -q maestro`, `git diff --check BASE..HEAD`,
and exact changed-path/artifact/secret scans. Run the three B test modules in
ten fresh processes. Use real temporary SQLite files under independently
derived test `var/`; every seam/negative case snapshots target/related rows,
versions, leases/locks/waits/corrections, event count/max ID, schema/FK/WAL, and
artifacts before the single invalid fact, then proves exact error and unchanged
reopened state. No predecessor test may be removed, skipped, renamed, weakened,
or broadened.

**Q1 — Atomic lifecycle/claims.** Protected: no duplicate state, partial claim,
or unauthorized correction attempt. Model: one SQLite service, finite matrices,
replay/conflict, seams, busy, contention, and three finite attempts. Excludes
distributed writers, retry policy, and executor behavior. Assurance: serialized
versioned transactions with one event/command. Proof: B-P03--P10. Boundary:
owned state/storage/recovery paths and standard library. Ceiling: declared
matrix/carriers only; no workflow framework. Stop: a new state/retry/distributed
requirement returns to Project Architect.

**Q2 — Durable M0-D17 authority.** Protected: no second correction is granted
by an optimistic label or mutable record. Model: one normal correction, every
closed M0-D17 fact, two terminal targeted gates, Project Architect authority,
and exact ranges. Excludes Owner decision creation, general re-review, and any
third correction. Assurance: immutable additive schema-5 record and atomic
authorization. Proof: B-P05--P08, P14, P16, P21. Boundary: declared
correction/evidence/review/wait/event APIs. Ceiling: maximum two corrections.
Stop: a missing carrier/fact, changed architecture/schema/API product contract,
or inability to preserve atomicity returns to Project Architect.

**Q3 — Recovery and closed completion.** Protected: restart/return/learning
cannot duplicate ownership or silently lose time/authority facts. Model: real
local reopen, return/resolution, finite recovery outcomes, terminal gates, and
exact coverage. Excludes reboot supervisor, Git/worker/network, corrupt DB,
and M1-02C acceptance. Assurance: deterministic durable records, targeted
coverage, and routine Project Architect acceptance. Proof: B-P11, P15--P22.
Boundary: this packet's paths and local SQLite. Ceiling: one B packet, one
initial/full review pair, governed corrections only. Stop: new failure class,
failed/out-of-scope correction, exhausted allowance, missing evidence, or
reserved material choice follows M0-D05/M0-D17/M0-D15.

Let `I0` be B's initial committed head, `I1` the normal correction head when
used, and `I2` the M0-D17-authorized final-correction head when used. For a
reviewable `I0`, the Coordinator obtains terminal Integration and full review
over `d82164c..I0`, unions their complete findings, then may record #1. Its
targeted follow-up covers only `I0..I1`, named findings, and directly affected
consistency. Only if all P06--P08 facts are then true may the Project Architect
authorize #2; its targeted follow-up covers only `I1..I2`. No-diff/no-commit,
scope, dependency, configuration, placeholder, unsafe review, or any failed
eligibility class is an immediate return under M0-D05/M0-D17. Chat is not a
wake mechanism; a terminal gate, committed resolution/authority change, poll,
expiry, or restart causes exact durable reread.

Technical completion is the exact final head `I0|I1|I2` with every frozen proof
passing, terminal Integration PASS, full+targeted coverage without gaps,
complete handoff/learning, released locks, and Project Architect `Accepted`.
It opens only M1-02C. The existing unreleased M1-03 schema-5 candidate must be
reconciled to the accepted B schema/version and APIs before it can be released;
this packet neither edits nor releases M1-03. It never authorizes C, merge,
deploy, external/live work, project registration, or a worker action.
