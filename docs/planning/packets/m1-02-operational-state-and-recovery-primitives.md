# M1-02 — Complete Operational State and Recovery Primitives

**Status:** Materialized candidate for Project Architect and Decision Fidelity review; dependency-blocked and not released
**Packet ID:** `maestro-m1-02-operational-state-recovery`
**Graph node:** `MAESTRO-M1-02-OPERATIONAL-STATE-RECOVERY`
**Graph revision:** `maestro-m1-m4-real-r1`
**Planning source base:** `ed3d6cb2d2da03fbc5864f1727defcb2417f6e84`
**Implementation base:** unresolved until M1-01 has complete implementation-review coverage and routine Project Architect acceptance; before release the Coordinator must replace this field with that exact accepted M1-01 final head
**Expected implementation branch:** `implementation/m1-02-operational-state-recovery`
**Expected worktree:** `/home/jeremy/Development/Maestro-m1-02-implementation`
**Decision authority:** [M0-D01](../decisions/m0-d01-operational-database.md),
[M0-D02](../decisions/m0-d02-project-registration.md),
[M0-D03](../decisions/m0-d03-access-and-secrets.md),
[M0-D04](../decisions/m0-d04-notifications-and-escalation.md),
[M0-D05](../decisions/m0-d05-rework-review-and-escalation.md),
[M0-D06](../decisions/m0-d06-project-manifest-contract.md),
[M0-D11](../decisions/m0-d11-linux-runtime-filesystem-boundary.md),
[M0-D12](../decisions/m0-d12-bounded-quality-contracts.md),
[M0-D14](../decisions/m0-d14-context-and-token-reporting.md), and
[M0-D15](../decisions/m0-d15-real-m1-m4-implementation-path.md)
**Roadmap authority:** `sources/planning/maestro-alpha-1-handoff.md`, M1; `docs/planning/maestro-master-plan.md`; and `docs/planning/agent-workforce-control-plane.md`
**Typed hard dependency:** `MAESTRO-M1-01-REAL-PROJECT-AUTHORITY-LOADER @
ProjectArchitectAccepted`, with exact final implementation head and complete
implementation-review coverage; packet planning or Decision Fidelity review
does not satisfy this dependency
**Implementation role:** dedicated Maestro Developer
**Execution route:** cloud collaboration worktree / dedicated Maestro Developer / `codex-cloud-maestro-developer` / session-inherited Codex model; factual model/runtime identity is recorded at dispatch preflight
**Role/SOP versions:** `docs/agents/maestro-developer.md`, `docs/agents/coding-agent-sop.md`, `docs/agents/integration-agent.md`, `docs/agents/independent-review-agent.md`, and `docs/agents/maestro-development-manager.md` at planning source base `ed3d6cb2d2da03fbc5864f1727defcb2417f6e84`; bootstrap Coordinator authority is M0-D15 plus `ai/handoffs/current.md` at the same revision
**Bootstrap coordinator:** Maestro Coordinator
**Decision Fidelity route:** fresh independent Decision Fidelity Reviewer
**Integration route:** Integration Agent, `validate-only` unless integration changes are required
**Independent implementation-review route:** fresh Independent Implementation Reviewer; this shared-schema packet is reviewed as a high-risk dependency boundary
**Routine acceptance authority:** Project Architect under M0-D15

## Candidate and dispatch boundary

This packet completely defines M1-02, but it is not runtime `Dispatchable`. It may be reviewed while M1-01 is being implemented. It may not be released, leased, or implemented until:

1. M1-01 has one exact accepted final implementation head with complete independent-review coverage;
2. the Project Architect records that SHA as this packet's implementation base and confirms that accepted M1-01 produced schema version `3` with the `projects`, `project_registration_runs`, and `events` contract named by M1-01;
3. the resulting packet-only correction receives targeted Decision Fidelity verification when required; and
4. the Coordinator completes the exact preflight and atomically acquires every declared resource lock.

If accepted M1-01 changes a table, state, migration, or API assumed here, do not translate it silently. Return the exact difference to the Project Architect for reconciliation before release.

## Exact dispatch controls

- Use one clean isolated worktree at the accepted M1-01 final head and expected branch. No other writer may use it.
- Acquire `shared:sqlite-schema`, `path:maestro-operational-state`, and `file:services-maestro-storage`. No parallel packet may write the schema, storage core, operational-state modules, or `tests/m1_02/` until handoff/cancellation releases them.
- One initial Developer attempt is allowed. One M0-D05 correction is available only for committed, in-scope work failing a named gate. No automatic retry is permitted. Infrastructure failure stops to the Coordinator; a missing/infeasible contract returns to the Project Architect.
- The attempt ceiling is 120 minutes. After 10 minutes without visible update, the Coordinator may request one bounded factual status; later requests are at least 10 minutes apart with a 2-minute reply window. No role invents an ETA.
- Preflight sets packet minimum context to 32,768 plus a separate 8,192-token
  output/handoff reserve, requiring configured capacity of at least 40,960.
  Record model, runtime, configured context, counting method, source/time, and
  available usage counters. Warn at 16,384 remaining, prepare handoff at
  12,288, and stop new work at 8,192. Unsupported counters are `unavailable`;
  do not scrape a provider, convert tokens into weekly allowance, or enforce an
  unapproved budget.
- Handoff states exact base/head, paths, commands/full results, schema-before/after inventories, migration rollback and existing-row preservation proof, transition/idempotency/concurrency/restart evidence, model/runtime/context and honest usage facts, released locks, and every `UNTESTED` item or gap.

## Outcome

Advance the accepted M1-01 SQLite database additively from schema version `3` to `4` and add the production operational records and service-owned primitives required by later M1-M4 packets.

M1-02 records projects/bindings, exact graph/work projections, milestone runs, materialized packets, leases, attempts, immutable evidence, waits, resource locks, durable notification state, review results, worker progress, context/usage and allowance observations, usage reconciliation, acceptance, and ordered events. It supplies atomic compare-and-transition, idempotent command replay, packet claim with all locks, heartbeat/release, stale-observation rejection, and startup/expired-lease reconciliation.

It implements storage and recovery primitives only. It does not select work, contact Git/GitHub, create/register a project, start a worker, deliver a notification, expose Atlas, approve work, merge, deploy, or perform an external next action.

## Existing foundations to preserve

- Preserve M0-D11 through every new entry route. `OperationalStateStore`
  accepts only a `RuntimeConfig`, reconstructs it as
  `RuntimeConfig(config.runtime_dir)`, and obtains every connection through
  `RuntimeConfig.open_runtime_dir_fd()` plus `SQLiteFoundation._connect()`.
  `RecoveryService` accepts only an already validated
  `OperationalStateStore`; it accepts no path, connection, or database file.
  No new constructor, factory, read, write, snapshot, event, or recovery API
  accepts a caller-supplied runtime/database path. Runtime artifacts remain
  only beneath the repository's physical `var/` tree.
- Preserve WAL, foreign keys, short transactions, canonical JSON, and every Alpha-01 through Alpha-03 table and behavior.
- Preserve accepted M1-01 authority loading, exact-commit behavior, candidate/blocked persistence, replay, and rows.
- The Linux Maestro service is the only SQLite writer. Add no direct listener, Atlas writer, ORM, or second database.
- Repository/GitHub remain authoritative for approved plans, code, PRs, reviews, and CI. These are observed projections and operational consequences, not another editable backlog.
- M0-D02 and M0-D06 control binding meaning: M1-02 stores the proposed
  operational binding and exact source references, but cannot activate it,
  register a project, weaken a project rule, or substitute a database-authored
  binding for the checked-in manifest.
- M0-D03 controls every provider/reference carrier: provider identity and
  secret-reference name may be stored, never a secret value. Provider
  selection remains a later implementation choice and no credential is
  authorized here.
- M0-D04 controls notification records: store-before-send, audience, severity,
  attempts/outcome, acknowledgement, grouping/rate-limit references, and
  escalation timeout are durable; Slack delivery and destination setup remain
  excluded.

## Canonical storage rules

- IDs/references are non-empty UTF-8 text up to 512 bytes with no NUL/control character. Git commits are lowercase full 40-hex; SHA-256 digests lowercase 64-hex.
- Service timestamps are injected UTC values serialized `YYYY-MM-DDTHH:MM:SS.ffffffZ`. Tests inject the clock; no hidden second clock runs inside a transaction.
- Structured values use canonical UTF-8 JSON: required root type, sorted keys, compact separators, no NaN/infinity, maximum 1 MiB per row. Sets are sorted unique arrays unless authority declares order meaningful.
- Every mutating command has a non-empty idempotency key and canonical command fingerprint. Same key/fingerprint returns the original result; same key/different facts raises `IdempotencyConflict` without mutation.
- Every mutation uses one short `BEGIN IMMEDIATE` transaction and appends its event before commit. Every connection uses WAL, foreign keys, and 5,000 ms busy timeout. Busy exhaustion returns `ResourceBusy`; it does not retry or partially mutate.
- Optimistic mutations carry `expected_state` and `expected_version`. A stale precondition returns `StaleState` without a success event. Exact committed replay is resolved before stale checking.
- Foreign keys, uniqueness, state values, positive counters, and
  one-active-record rules are database constraints as well as application
  validation. Canonical ID, digest, timestamp, and JSON shapes are validated
  before the transaction; database length/check constraints provide the
  practical final guard where SQLite can express them without a custom
  extension.

## Schema version 4

The migration is additive. It may add columns to M1-01 `events`, add indexes/triggers, and create the tables below. It may not drop, rename, rebuild, truncate, or rewrite an Alpha/M1-01 table. It inserts version `4` only after all DDL succeeds in the same transaction.

### Existing `events` extension

Retain M1-01 columns and add nullable `correlation_id TEXT`,
`causation_event_id INTEGER REFERENCES events(event_id)`, `actor_type TEXT`,
`actor_id TEXT`, `command_fingerprint TEXT`, and `observed_at TEXT`. Existing
rows remain unchanged. `event_id` remains the monotonic local cursor and
`idempotency_key` globally unique.

M1-01's accepted writer is explicitly grandfathered: only an event with
`entity_type = ProjectRegistrationRun` and `event_type = AuthorityLoaded` may
insert null values in the six new columns. This preserves authority-load
regressions after schema version 4. A `BEFORE INSERT` trigger rejects null
`correlation_id`, actor, fingerprint, or `observed_at` for every other event
shape; `causation_event_id` alone may be null. The M1-02 event writer enforces
the same rule before SQL. Triggers reject all event `UPDATE`/`DELETE`. If the final
accepted M1-01 head uses a different exact legacy event shape, that difference
returns for dependency reconciliation before M1-02 release.

Closed production event types are:

```text
ProjectBindingRecorded, SecretReferenceObserved, GraphProjectionRecorded,
GraphProjectionStateChanged,
WorkItemProjected, RunCreated, RunStateChanged, PacketMaterialized,
PacketStateChanged, PacketClaimed, LeaseHeartbeatRecorded, LeaseReleased,
LeaseExpired, AttemptRecorded, AttemptStateChanged, StaleObservationIgnored,
EvidenceAppended, WaitOpened, WaitStateChanged, NotificationRecorded,
NotificationStateChanged, ReviewRecorded, WorkerProgressRecorded,
AttemptContextUsageRecorded, AllowanceWindowObserved,
UsageReconciliationRecorded, AcceptanceRecorded, MergeObserved,
StartupReconciliationRecorded
```

One event represents one complete atomic command; a claim event's `after_json`
includes packet, lease, and all lock IDs.

### Exact table contracts

In the compact definitions below, an untyped field is `TEXT NOT NULL`, `PK` is
`TEXT PRIMARY KEY`, `FK table` is `TEXT NOT NULL REFERENCES table` and a field
marked `NULL` is nullable `TEXT`. Explicit integer declarations override that
default. All timestamp/ID/JSON columns follow the canonical rules. Every
`version` starts at `1` and increments once per successful mutation. Triggers
reject `UPDATE` and `DELETE` on `evidence`, `reviews`,
`secret_reference_observations`, `worker_progress_observations`,
`provider_allowance_windows`, `usage_reconciliations`, `acceptance_records`,
and `merge_observations` as well as `events`.

`project_bindings`

```text
binding_id PK; project_id FK projects; binding_revision; source_commit;
manifest_digest; adapter_version; process_version; authority_reference;
merge_policy; acceptance_authority CHECK ProjectArchitect|Owner;
merge_execution_authority CHECK OwnerPerformed|PolicyDelegated;
merge_delegation_reference NULL;
binding_json; state CHECK Candidate|Active|Superseded|Blocked;
created_at; activated_at NULL; superseded_at NULL;
UNIQUE(project_id,binding_revision); partial UNIQUE project_id WHERE Active
```

The M1-02 `record_binding` primitive accepts `Candidate` and `Blocked` only.
The table reserves `Active` and `Superseded` for the later reviewed
create/register workflow. M1-02 exposes no activation and does not change
`projects.registration_state` or `active_binding_revision`.
`OwnerPerformed` requires null `merge_delegation_reference`;
`PolicyDelegated` requires the exact project-authored, independently reviewed
delegation-policy reference. These fields record the checked-in binding's
authority boundary; they do not grant Maestro an ability to perform a merge.

`secret_reference_observations`

```text
secret_reference_observation_id PK; project_id FK projects;
binding_id FK project_bindings; provider; reference_name; owner_reference;
rotation_at NULL; expires_at NULL;
status CHECK Active|Stale|Revoked|Unavailable; observed_at;
UNIQUE(binding_id,provider,reference_name,observed_at)
```

Rows are append-only. `provider` is a non-secret identifier matching
`[a-z][a-z0-9-]{1,63}` and does not select or configure a provider.
`reference_name` matches M1-01's `[A-Z][A-Z0-9_]{2,127}` grammar. No column or
API accepts a secret value. A stale/revoked/unavailable latest observation is
an operational blocker for later policy code; M1-02 does not perform fallback
or credential injection.

`graph_projections`

```text
graph_projection_id PK; project_id FK projects; binding_id FK project_bindings;
graph_revision; authority_reference; source_base_sha; source_hash;
state CHECK Active|Stale|NeedsReplan|Superseded;
observed_at; updated_at; version;
UNIQUE(project_id,graph_revision,source_hash);
partial UNIQUE project_id WHERE Active
```

Graph-projection transitions are exactly
`Active -> Stale|NeedsReplan|Superseded`,
`Stale -> Active|NeedsReplan|Superseded`, and
`NeedsReplan -> Superseded`; `Superseded` is terminal. `Active -> Stale`
requires a newer exact observation, `Active|Stale -> NeedsReplan` requires the
changed source/contract reference, and returning `Stale -> Active` requires a
matching current source hash. Replanning creates a new projection; it never
mutates a `NeedsReplan` projection back to `Active`. Every transition requires
the expected state/version and a non-empty authoritative source reference;
entry to `Superseded` additionally requires that reference to name the
superseding graph revision. `record_graph_projection` creates only `Active`
projections and rejects a second active projection rather than implicitly
superseding one.

`work_items`

```text
work_item_id PK; graph_projection_id FK graph_projections;
architecture_node_id; task_reference; workstream_ref; milestone_ref; title;
priority; planned_rank INTEGER CHECK >=0; specialist_role;
execution_classes_json; dependencies_json; change_domains_json;
input_contract_json; output_contract_json;
planning_state CHECK Active|NeedsReplan|Superseded;
created_at; updated_at; version;
UNIQUE(graph_projection_id,architecture_node_id)
```

The joined project graph owns meaning/rank/dependencies. Maestro stores the observed projection; it does not author a replacement backlog.

`runs`

```text
run_id PK; run_fingerprint UNIQUE; project_id FK projects;
binding_id FK project_bindings; graph_projection_id FK graph_projections;
milestone_ref; approved_authority_reference; branch_name NULL;
pull_request_reference NULL;
state CHECK Planned|Running|Blocked|AwaitingArchitect|AwaitingOwner|Complete|Cancelled;
acceptance_boundary CHECK ProjectArchitect|Owner;
created_at; updated_at; version
```

Run transitions are exactly `Planned -> Running|Blocked|Cancelled`,
`Running -> Blocked|AwaitingArchitect|AwaitingOwner|Cancelled`,
`Blocked -> Running|AwaitingArchitect|AwaitingOwner|Cancelled`, and
`AwaitingArchitect|AwaitingOwner -> Complete|Blocked`. `Complete` requires all
run packets to be `Complete`, the matching acceptance record or exact reviewed
binding delegation that authorized a direct merge observation, and every
required authoritative merge observation/post-merge gate. `Complete` and
`Cancelled` are terminal, and no transition starts a successor milestone.

`packets`

```text
packet_id PK; run_id FK runs; work_item_id FK work_items; packet_revision;
authority_reference; base_commit; current_head NULL; expected_branch;
role_contract_reference;
sop_reference; executor_class; integration_route; reviewer_route;
owned_paths_json; forbidden_paths_json; checks_json; resource_claims_json;
context_policy_json;
state CHECK Planned|Waiting|Blocked|Ready|Dispatchable|Leased|Running|AwaitingIntegration|AwaitingReview|MergeReady|AwaitingArchitect|AwaitingOwner|Merged|Complete|NeedsReplan|Cancelled;
correction_count INTEGER DEFAULT 0 CHECK IN(0,1);
created_at; updated_at; version;
UNIQUE(run_id,work_item_id,packet_revision)
```

Production names map the master plan's small diagram as `Claimed = Leased`, `Executing = Running`, and `Verified = AwaitingIntegration`. Architect/Owner decisions are acceptance rows, not another packet state.

Packet transitions are exactly:

```text
Planned -> Waiting|Blocked|Ready|NeedsReplan|Cancelled
Waiting -> Blocked|Ready|NeedsReplan|Cancelled
Blocked -> Waiting|Ready|NeedsReplan|Cancelled
Ready -> Dispatchable|Waiting|Blocked|NeedsReplan|Cancelled
Dispatchable -> Leased|Ready|Blocked|NeedsReplan|Cancelled
Leased -> Running|Blocked|Cancelled
Running -> AwaitingIntegration|Blocked|NeedsReplan|Cancelled
AwaitingIntegration -> AwaitingReview|Blocked|NeedsReplan
AwaitingReview -> MergeReady|Running|Blocked|NeedsReplan
MergeReady -> AwaitingArchitect|AwaitingOwner|Blocked
AwaitingArchitect -> AwaitingOwner|Blocked
AwaitingOwner -> Blocked
Merged -> Complete|Blocked
NeedsReplan -> Planned|Cancelled
```

`AwaitingReview -> Running` requires correction count `0 -> 1`, a named failed
gate, and review reference. No other transition increments it. Entry to
`Merged` is reserved to the authoritative merge-observation command below;
entry to `Complete` requires that observation and the declared post-merge
gate. `Complete`/`Cancelled` are terminal.

`leases`

```text
lease_id PK; packet_id FK packets; run_id FK runs; claim_key UNIQUE;
run_fingerprint; base_commit; worktree_path; executor_route; holder_id;
state CHECK Active|Released|Expired|Cancelled;
acquired_at; expires_at; heartbeat_at; released_at NULL; version;
partial UNIQUE packet_id WHERE Active;
partial UNIQUE worktree_path WHERE Active
```

Expiry is later than acquisition; heartbeat is monotonic and cannot pass an existing release.

`attempts`

```text
attempt_id PK; packet_id FK packets; lease_id FK leases;
attempt_number INTEGER CHECK IN(1,2);
attempt_kind CHECK Initial|TargetedCorrection;
executor_class; model_identity; runtime_identity;
state CHECK Planned|Running|Succeeded|Failed|Cancelled|TimedOut|Stale;
result_commit NULL; correction_for_review_id NULL FK reviews DEFERRABLE;
started_at NULL; finished_at NULL; created_at; updated_at; version;
UNIQUE(packet_id,attempt_number)
```

Attempt transitions are exactly `Planned -> Running|Cancelled` and
`Running -> Succeeded|Failed|Cancelled|TimedOut|Stale`; all other states are
terminal. `Planned -> Running` requires the matching active lease, packet in
`Leased|Running`, and the valid preflight context record defined below.
`Planned -> Cancelled` requires an authority reason. Every transition out of
`Running` requires `finished_at`; `Succeeded` requires a full result commit and
evidence reference, `Failed|Cancelled` require a reason and evidence reference,
`TimedOut` additionally requires `now >= lease.expires_at`, and `Stale`
requires that the named lease is no longer the attempt's current active lease.
No non-success outcome accepts `result_commit`. Attempt 1 is initial; attempt 2
requires the one correction gate. M1-02 records but does not invoke/grade an
executor.

`resource_locks`

```text
lock_id PK; resource_key; lock_kind CHECK Path|SharedBoundary|FiniteResource;
packet_id FK packets; lease_id FK leases;
state CHECK Active|Released|Expired;
acquired_at; expires_at; released_at NULL; version;
partial UNIQUE resource_key WHERE Active
```

Claiming acquires lease/all sorted unique locks, changes `Dispatchable -> Leased`, and appends `PacketClaimed` atomically. Any conflict rolls the whole claim back.

`evidence`

```text
evidence_id PK; idempotency_key UNIQUE; run_id FK runs; packet_id FK packets;
attempt_id NULL FK attempts; evidence_kind; payload_json; content_digest;
source_reference NULL; redaction_state CHECK Redacted|NotRequired; created_at
```

Evidence is append-only and its digest covers canonical JSON. Every retained
payload is one closed tagged variant; arbitrary mappings, arbitrary scalar
roots, and extra fields are invalid:

```text
StatePayload = {kind:"state", entity_type, entity_id, state, version}
ClaimPayload = {kind:"claim", packet_id, lease_id, lock_ids[]}
ReferencePayload = {kind:"reference", provider, reference_name}
EvidenceReferencePayload = {kind:"evidence-reference", evidence_id, digest, source_reference}
MeasurementReferencePayload = {kind:"measurement-reference", record_id, measurement_kind}
RedactedTextPayload = {kind:"redacted-text", text, redaction_status:"Redacted", redaction_receipt_reference}
NotificationPayload = {kind:"notification", event_id, audience, severity, subject_reference, evidence_references[], next_action_reference}
ReasonPayload = {kind:"reason", reason_code, detail_reference NULL}
```

All named IDs/references use the canonical text rules above; `event_id` and
`version` are positive integers; `lock_ids` and `evidence_references` are
sorted unique arrays; states, audiences, and severities must be values already
declared by their owning table/packet contract. `RedactedTextPayload.text` is
bounded by the row limit; no other variant accepts free text.

`provider` and `reference_name` use the exact provider/reference grammars
above. `RedactedTextPayload` is the only prose carrier and requires a
non-secret receipt reference proving redaction occurred before persistence;
M1-02 does not inspect prose semantically. Event before/after/reason,
notification payload/error, worker-progress text, review findings, and
acceptance reasons are composed only from these variants or exact closed
record fields.

Because the schemas are closed, fields named `prompt`, `raw_prompt`, `trace`,
`raw_trace`, `secret`, `secret_value`, `password`, `private_key`,
`credential_value`, `authorization_header`, `cookie_value`, or any unknown key
are rejected structurally. A reference carrying `ghp_`, `github_pat_`,
`xoxb-`, `Bearer `, cookie text, or `-----BEGIN` fails the uppercase-reference
grammar. Valid examples are syntactic provider `secret-provider` with reference
`GITHUB_APP_PRIVATE_KEY` and provider `slack` with reference
`SLACK_BOT_TOKEN`. No heuristic searches ordinary prose for words such as
token/key/password, and no semantic secret detector is claimed.

`waits`

```text
wait_id PK; run_id FK runs; packet_id NULL FK packets; gate_type;
awaited_role; awaited_reference; expected_result; timeout_at NULL;
next_permitted_action; state CHECK Open|Resolved|Expired|Cancelled;
resolution_reason_payload_json NULL; created_at; updated_at; version;
partial UNIQUE(packet_id,gate_type) WHERE Open
```

Unknown ETA is literal `unknown`, never inferred from silence.
Wait transitions are exactly `Open -> Resolved|Expired|Cancelled`; all three
outcomes are terminal. `Resolved` requires a resolution/evidence reference,
`Expired` requires `now >= timeout_at`, and `Cancelled` requires a recorded
authority/recovery reason. A wait transition does not itself advance a packet.

`reviews`

```text
review_id PK; packet_id FK packets; attempt_id NULL FK attempts;
review_kind CHECK Integration|IndependentImplementation;
reviewer_role; reviewer_instance; base_commit; head_commit;
result CHECK ValidateOnly|Assemble|NeedsReplan|Approve|RequestChanges|Comment;
findings_json; coverage_json; correction_number CHECK IN(0,1); created_at;
UNIQUE(packet_id,review_kind,reviewer_instance,head_commit,correction_number)
```

Reviews are append-only; storage does not fabricate/decide outcomes.

`notifications`

```text
notification_id PK; event_id INTEGER FK events; run_id FK runs;
packet_id NULL FK packets; channel CHECK LocalDurable|Slack;
destination_reference; audience;
severity CHECK Informational|ActionNeeded|CompletionReady|CompletionSummary;
message_type; grouping_key; escalation_at NULL; payload_json;
state CHECK Pending|Delivered|Failed|Acknowledged;
attempt_count INTEGER DEFAULT 0 CHECK >=0; last_error_payload_json NULL;
next_attempt_at NULL; created_at; updated_at; version
```

Notification transitions are exactly `Pending -> Delivered|Failed`,
`Failed -> Pending`, and `Delivered -> Acknowledged`; `Acknowledged` is
terminal. `Pending -> Delivered` requires a non-secret external delivery
reference and delivery time; `Pending -> Failed` requires a closed error
payload and `next_attempt_at`; both increment `attempt_count` once.
`Failed -> Pending` requires the declared grouping/rate-limit key and `now` at
or after `next_attempt_at`, clears only the retry scheduling fields, and does
not increment the attempt count. `Delivered -> Acknowledged` requires the
acknowledging actor reference and acknowledgement time and cannot change an
acceptance record or packet state. `Slack` is M0-D04's required first V1
external channel and
`LocalDurable` is the always-present database record; neither value configures
or contacts a destination. M1-02 supplies store-before-send and transitions
only, no external delivery. `Acknowledged` never means approved.

`acceptance_records`

```text
acceptance_id PK; run_id FK runs; packet_id NULL FK packets;
sequence_number INTEGER CHECK IN(1,2);
supersedes_acceptance_id NULL FK acceptance_records;
required_authority CHECK ProjectArchitect|Owner;
decision CHECK Accepted|Returned|ReservedChoice;
authority_reference; exact_head; review_coverage_json; reason_payload_json;
created_at; UNIQUE(packet_id,sequence_number)
```

Acceptance is append-only. The matrix is exactly: no prior record permits one
sequence-1 Project Architect `Accepted|Returned|ReservedChoice`; `Accepted` or
`Returned` is terminal; `ReservedChoice` permits exactly one sequence-2 Owner
`Accepted|Returned` that names the sequence-1 record in
`supersedes_acceptance_id`. `ReservedChoice` may be recorded only by the
Project Architect for a named M0-D15 reserved choice, requires
`required_authority = Owner`, does not accept work, and is the sole guard for
`AwaitingArchitect -> AwaitingOwner`. `Accepted` requires the packet in its matching
`AwaitingArchitect|AwaitingOwner` state, the decision actor to match
`required_authority`, and `exact_head` to equal the packet's current head.
For `Accepted`, `review_coverage_json` is the following closed object (extra or
missing keys are invalid):

```text
{
  base_commit,
  full_review: {review_id, reviewer_role, reviewer_instance, head_commit, result},
  targeted_corrections: [
    {review_id, correction_number, diff_base, diff_head,
     reviewer_role, reviewer_instance, result}
  ],
  final_head,
  freshness: {status:"Fresh", observed_at, source_reference}
}
```

The full review must be an approving independent review over
`base_commit..full_review.head_commit`; targeted corrections are ordered,
non-overlapping, approving verifications numbered exactly once, each
`diff_base` equals the preceding covered head, and `final_head` equals both the
last covered head and `exact_head`. An empty correction array requires
`full_review.head_commit = final_head`. Reviewer identities must meet the
declared independent-review route, and any stale result or uncovered commit
rejects the record. `Returned` requires a finding/authority reference and
cannot be treated as acceptance. Recording acceptance never merges, deploys,
or selects successor work.

`merge_observations`

```text
merge_observation_id PK; run_id FK runs; packet_id FK packets;
acceptance_id NULL FK acceptance_records; repository_reference; default_branch;
accepted_head; merge_commit; source_kind CHECK Git|GitHub;
source_reference; performed_by_authority CHECK Owner|DelegatedIdentity;
performed_by_reference; delegation_reference NULL;
review_coverage_json NULL; observed_at
```

Merge observations are append-only. The normal path requires an `Accepted`
record for the same exact head and complete fresh review coverage. The sole
alternative is the Control Plane's direct `MergeReady -> Merged` path: it
requires `acceptance_id` null, `merge_execution_authority = PolicyDelegated`,
the exact independently reviewed project delegation reference, and complete
fresh exact-head review coverage with the identical closed shape required for
acceptance in non-null `review_coverage_json`. The normal accepted path requires
that column null and follows its acceptance record's coverage instead. No
`OwnerPerformed` path may omit acceptance. Every observation must name the
authoritative project repository/default branch and the
Git/GitHub observation reference; repository/default branch must equal the
active binding, and that referenced observation must assert the authoritative
default branch is at `merge_commit` and contains `accepted_head`. M1-02 checks
the closed record and source identity but performs no Git ancestry query.
Under `OwnerPerformed`,
`performed_by_authority = Owner`, `performed_by_reference` names the
Owner-performed action, and `delegation_reference` is null. Under
`PolicyDelegated`, `performed_by_authority = DelegatedIdentity` and
`delegation_reference` must equal the active binding's exact independently
reviewed `merge_delegation_reference`; an arbitrary caller assertion is not a
delegation. `no-automatic-merge` maps only to `OwnerPerformed` and never grants
Maestro permission to merge.

M1-02 records a caller-supplied authoritative observation but contacts no
repository. Only `record_merge_observation` may atomically change a
`MergeReady|AwaitingArchitect|AwaitingOwner` packet to `Merged`; `MergeReady`
is permitted only by the direct reviewed-delegation guard above, while either
awaiting state requires its matching accepted record. Generic
`transition_packet` may not enter `Merged`. `Merged -> Complete` requires the
declared post-merge gate. No path infers a merge from acceptance, a PR state,
or a notification acknowledgement.

`worker_progress_observations`

```text
progress_id PK; attempt_id FK attempts; plan_payload_json;
current_step_payload_json; blocker_payload_json;
eta_text; confidence CHECK Reported|Unknown;
status_request_state CHECK NotRequested|Requested|Answered|Unavailable;
next_permitted_action; observed_at; received_at
```

The three payload fields are `RedactedTextPayload` values with receipts.
`eta_text` is only literal `unknown`, a canonical UTC timestamp, or an ISO-8601
duration supplied by the worker. Rows are append-only/worker-reported; missing
timing is `unknown`/`Unknown`.

`attempt_context_usage`

```text
context_usage_id PK; attempt_id UNIQUE FK attempts; model_identity;
runtime_identity; quantization NULL; configured_context_limit NULL CHECK >0;
packet_minimum_context CHECK >0; output_reserve CHECK >0;
warning_threshold CHECK >0; checkpoint_threshold CHECK >0;
stop_threshold CHECK >0;
counting_method CHECK Runtime|Tokenizer|Estimate|Unavailable;
starting_input_measurement_json; future_growth_estimate_json;
token_measurements_json; cost_measurement_json;
availability_state CHECK Available|Partial|Unavailable;
observed_at; updated_at; version
```

For this packet route, `packet_minimum_context = 32768` and
`output_reserve = 8192`, so the configured context limit must be at least
`32768 + 8192 = 40960`; the values are not alternatives and the reserve is not
included inside 32,768. Warning/checkpoint/stop are exactly
`16384/12288/8192` remaining tokens. Known starting input plus the 8,192 output
reserve must fit the configured limit. `future_growth_estimate_json` is an
explicit lower/upper range and never a false exact value. An attempt cannot
transition to `Running` until this valid record is committed.

`starting_input_measurement_json` is one measurement object.
`future_growth_estimate_json` is exactly
`{lower_bound: measurement, upper_bound: measurement}` and requires both
estimated bounds in the same unit/source/time with
`lower_bound.value <= upper_bound.value`. `token_measurements_json` is exactly
`{input, output, cached_input, reasoning, total}`, with each value one
measurement object; missing or extra categories are invalid. The measurement
object is closed:

```text
{value: non-negative integer|null,
 quality: RuntimeReported|TokenizerCounted|Estimated|Unavailable,
 confidence: Exact|High|Medium|Low|Unavailable,
 source_reference: string|null,
 observed_at: canonical UTC timestamp}
```

`Unavailable` requires null value/source and `Unavailable` confidence. Every
other quality requires a non-null value/source and non-`Unavailable`
confidence. `RuntimeReported` requires a runtime source and `Exact|High`
confidence and takes precedence for the same attempt/category/measurement
period over tokenizer or estimate. A lower-quality update is rejected rather
than replacing it. `TokenizerCounted` requires the selected model/tokenizer
reference and `Exact|High` confidence. `Estimated` requires
High/Medium/Low confidence. Runtime totals are preserved as reported and are
not forced to equal component sums when the runtime defines them differently.

`cost_measurement_json` is exactly:

```text
{status: Billed|Estimated|NotBilled|Unknown,
 amount: normalized non-negative decimal string|null,
 currency: three-uppercase-letter currency|null,
 quality: RuntimeReported|ProviderReported|Estimated|Unavailable,
 confidence: Exact|High|Medium|Low|Unavailable,
 source_reference: string|null,
 observed_at: canonical UTC timestamp}
```

`Billed` requires amount/currency/source, quality
`RuntimeReported|ProviderReported`, and `Exact|High` confidence. `Estimated`
requires amount/currency/source, `quality = Estimated`, and
`High|Medium|Low` confidence. `NotBilled` requires null amount/currency, a
runtime/provider source, quality `RuntimeReported|ProviderReported`, and
`Exact|High` confidence. `Unknown` requires null amount/currency/source and
unavailable quality/confidence. Local execution is not silently zero-cost.
Every update records its source/time and obeys runtime-reported precedence.

`provider_allowance_windows`

```text
allowance_observation_id PK; provider; account_reference; native_window_type;
used_value NULL; remaining_value NULL; native_unit NULL; reset_at NULL;
precision CHECK Exact|Coarse|Unavailable;
measurement_quality CHECK RuntimeReported|ProviderReported|Estimated|Unavailable;
freshness CHECK Fresh|Stale|Unavailable; observed_at
```

Rows are append-only. Values are normalized non-negative decimal text, not float. Unsupported values are null/`Unavailable`. No token-to-weekly conversion.

`usage_reconciliations`

```text
usage_reconciliation_id PK; allowance_observation_id FK provider_allowance_windows;
window_change_value; tracked_controlled_value; registered_coarse_value;
unattributed_value; native_unit;
measurement_quality CHECK Exact|Coarse|Estimated; observed_at
```

Rows are append-only. Exact decimal arithmetic requires controlled + coarse + unattributed = window change in the allowance native unit. Local capacity is excluded.

## Exact service-owned APIs

Add `OperationalStateStore`, validated value objects, and closed errors with these internal entry points:

```python
record_binding(binding, idempotency_key, actor, now)
record_secret_reference(observation, idempotency_key, actor, now)
record_graph_projection(graph, work_items, idempotency_key, actor, now)
transition_graph_projection(graph_projection_id, expected_state, expected_version, next_state, source_reference, idempotency_key, actor, now)
create_run(run, idempotency_key, actor, now)
materialize_packet(packet, idempotency_key, actor, now)
transition_run(run_id, expected_state, expected_version, next_state, reason_payload, idempotency_key, actor, now)
transition_packet(packet_id, expected_state, expected_version, next_state, reason_payload, correction_reference, idempotency_key, actor, now)
claim_packet(packet_id, expected_version, lease, lock_requests, idempotency_key, actor, now)
heartbeat_lease(lease_id, expected_version, heartbeat_at, expires_at, idempotency_key, actor)
release_lease(lease_id, expected_version, disposition, reason_payload, idempotency_key, actor, now)
record_attempt(attempt, idempotency_key, actor, now)
transition_attempt(attempt_id, expected_state, expected_version, next_state, result_commit, reason_payload, evidence_reference, lease_id, idempotency_key, actor, now)
append_evidence(evidence, actor)
open_wait(wait, idempotency_key, actor, now)
transition_wait(wait_id, expected_state, expected_version, next_state, reason_payload, evidence_reference, idempotency_key, actor, now)
record_review(review, idempotency_key, actor, now)
record_notification(notification, idempotency_key, actor, now)
transition_notification(notification_id, expected_state, expected_version, next_state, delivery_facts_payload, idempotency_key, actor, now)
record_worker_progress(observation, idempotency_key, actor, now)
record_context_usage(record, idempotency_key, actor, now)
update_context_usage(attempt_id, expected_version, measurements, idempotency_key, actor, now)
record_allowance_window(observation, idempotency_key, actor, now)
record_usage_reconciliation(record, idempotency_key, actor, now)
record_acceptance(record, idempotency_key, actor, now)
record_merge_observation(observation, idempotency_key, actor, now)
snapshot(entity_type, entity_id)
events_after(event_id, limit)
reconcile_startup(recovery_run_id, now, actor)
record_attempt_observation(attempt_id, lease_id, observation, idempotency_key, actor, now)
```

`events_after` is an internal ordered read, not an M2 HTTP/event API; limit is 1-1,000. Snapshots do not mutate. Closed errors are `InvalidRecord`, `InvalidTransition`, `StaleState`, `IdempotencyConflict`, `ResourceConflict`, `ResourceBusy`, `SensitiveMaterialRejected`, and `RecoveryConflict`. Errors occur before commit and expose no secret payload.

Every ordinary record method and every non-claim transition uses the same
transaction helper with deterministic failure seams `after_entity_write` and
`after_event_write`. Failure at either seam rolls back entity/version/event
changes. Claim retains its additional per-lock seams. These seams are test-only
callables and are not a runtime retry facility.

## Claim, expiry, and restart semantics

### Atomic claim

`claim_packet` resolves exact replay first. Otherwise it requires `Dispatchable` at expected version, no active packet lease, and every sorted unique resource key free. In one transaction it inserts an `Active` lease/locks, changes the packet to `Leased`, increments its version, and appends one `PacketClaimed` event. A duplicate concurrent caller sees the original result only for the same key/fingerprint; other contenders receive `StaleState` or `ResourceConflict` without partial rows.

### Heartbeat and release

A heartbeat changes only its `Active` lease after version/monotonic-time checks and appends `LeaseHeartbeatRecorded`. Release changes lease and all active locks to `Released`, records one time, and appends `LeaseReleased`. It does not guess a packet next state; that is a separate transition after authority/executor reread.

### Startup reconciliation

`reconcile_startup` performs no Git, executor, notification, or network action. It reads one database snapshot and, in deterministic lease-ID order:

1. leaves a consistent unexpired `Active` lease untouched and returns `ObserveActiveAttempt` with exact IDs;
2. for expired `Active`, atomically marks lease/locks `Expired`, changes `Leased`/`Running` packet to `Blocked`, opens one `Recovery` wait with next action `RereadAuthorityAndExecutor`, and appends `LeaseExpired`;
3. for `Leased`/`Running` without a matching active lease, blocks the packet, opens that recovery wait, and appends `StartupReconciliationRecorded`; and
4. for active lease conflicting with packet/run/base/worktree, preserves evidence, blocks the packet, opens `RecoveryConflict`, and returns `ReturnToCoordinator`; it creates no replacement.

`recovery_run_id` plus entity ID derives event idempotency. Repeating reconciliation creates no duplicate event/wait. It never changes to `Ready`/`Dispatchable`, starts an attempt, invokes a worker, creates branch/PR, sends notification, or retries.

### Stale observations

`record_attempt_observation` may transition only when the supplied lease is the attempt's current active lease and expected state/version match. A late result for expired/released/replaced lease appends one `StaleObservationIgnored` keyed by observation identity and cannot change attempt, packet, evidence, review, or acceptance.

## Owned implementation paths

```text
docs/architecture/m1-02-operational-state-and-recovery-primitives.md
docs/operations/m1-02-operational-state-and-recovery-primitives.md
services/maestro/maestro/operational_state.py
services/maestro/maestro/recovery.py
services/maestro/maestro/storage.py
tests/m1_02/**
```

No other path may change. Do not change `cli.py`, project authority/manifest/Git modules, Alpha fixture behavior, planning/role records, GitHub adapters, executor code, Atlas, packaging dependencies, or any project repository.

## Required implementation sequence

1. Inventory accepted M1-01 schema and stop unless it is exact version 3 input above.
2. Add typed records, state/event registries, canonical validators, and closed errors with no public side-effecting entry.
3. Add version-4 migration, constraints, indexes, append-only triggers, and failure injection.
4. Add idempotent transition/event and record-append primitives.
5. Add atomic lease/lock claim, heartbeat, release, and contention.
6. Add deterministic startup and stale-observation reconciliation.
7. Add architecture/operations docs and real SQLite tests.
8. Run every gate and hand one exact commit to Integration.

Stop if an accepted M1-01 row must be dropped/rewritten, an owned path is insufficient, a state/recovery meaning is absent or conflicting, external access is required, or bounded secret/SQLite assurance cannot be met.

## Required gates and sufficient proof

From `services/maestro/`:

```text
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m unittest discover -s ../../tests/m1_02 -v
python -m compileall -q maestro
```

Using real temporary SQLite files inside the physical test `var/` boundary, M1-02 must prove:

1. a schema-3 database with representative Alpha and M1-01 rows upgrades to 4 with every original row byte-equivalent;
2. injected DDL failure before version insertion rolls back tables/indexes/triggers/version/data exactly;
3. reopen is no-op and concurrent migration callers yield one valid schema/one version-4 row;
4. every FK/check/unique/partial-active/JSON/ID/digest/timestamp/size constraint rejects without event;
5. M1-01 `AuthorityLoaded` still writes/reads its exact nullable legacy event after version 4, while every non-legacy direct insert missing new event metadata is rejected;
6. event ordering is monotonic and all declared append-only tables reject update/delete;
7. every binding/secret-reference/graph/work/run/packet/attempt/evidence/wait/review/notification/progress/context/allowance/reconciliation/acceptance/merge API persists and reopens its exact record;
8. same idempotency key/fingerprint returns the original result and one event after reopen;
9. same key/different facts raises `IdempotencyConflict` with no mutation;
10. every allowed graph/run/packet/attempt/wait/notification transition satisfies its guards with one version increment and exact event;
11. every prohibited, stale, terminal, missing-context, wrong-lease, premature-time, or direct-to-`Merged` transition fails without mutation;
12. targeted correction is available once, requires a named review finding, and a second is rejected;
13. injected `after_entity_write` and `after_event_write` failures for representative ordinary record methods roll back row/event and remain absent after close/reopen;
14. the same injected seams for graph, packet, and notification non-claim transitions restore original state/version/event history after reopen;
15. claim creates one lease, all locks, one state change/event;
16. injected failure after lease/each lock/event insertion rolls back complete claim;
17. simultaneous same-packet claims yield one lease, and shared-resource claims yield one holder/no partial loser;
18. heartbeat/version are monotonic and release frees locks once without inferring next packet state;
19. reopen with consistent unexpired lease returns only `ObserveActiveAttempt` and no duplicate lease/attempt/event;
20. reopen after expiry atomically expires lease/locks, blocks packet, opens one recovery wait, and is idempotent on another restart;
21. orphan/conflict blocks and returns exact recovery action without replacement work;
22. stale completion after expiry records one ignored event and cannot alter outcome records;
23. `OperationalStateStore`, every constructor/factory and every public record/transition/claim/read/recovery entry point named above, and `RecoveryService` reject source-tree/outside/symlinked/forged/swapped runtime configurations before creating database/journal/WAL/SHM/log/socket or outside artifacts; parameterized valid calls all stay under physical `var/`;
24. exact context values `32768 + 8192 = 40960`, thresholds `16384/12288/8192`, starting-input fit, and growth range are enforced, and no attempt enters `Running` without that committed record;
25. every token category validates value/quality/confidence/source/time and runtime-reported values take precedence over tokenizer/estimate for the same period;
26. billed/estimated/not-billed/unknown cost shapes and unavailable token/cost/allowance facts remain honest, never implicit zero;
27. exact-decimal usage reconciliation balances native allowance units, rejects imbalance/token-to-weekly conversion, and excludes local capacity;
28. each closed safe payload variant accepts exact fields; arbitrary roots/extra fields/raw prompt/trace/value carriers and invalid provider/reference patterns are rejected, while redacted prose with receipt is accepted without semantic word detection;
29. provider plus secret-reference observations accept valid provider/reference/owner/rotation/expiry facts, reject GitHub/Slack/Bearer/cookie/PEM values structurally, and persist no value/fallback;
30. notifications store event/audience/severity/grouping/escalation and state before any delivery observation; retry/time/acknowledgement guards pass and acknowledgement never accepts work;
31. acceptance rejects wrong authority/head, stale/incomplete review coverage, and uncovered correction; normal merge rejects a missing acceptance and undelegated direct merge is rejected, while only a matching accepted exact head or the exact reviewed `PolicyDelegated` direct path plus an authoritative Git/GitHub observation can enter `Merged`; and
32. all Alpha/M1-01 suites stay green with no CLI, repo, network, worker, Atlas, external delivery, merge/deploy action, or live-project effect.

## Complete M0-D12 quality contracts

### Q1 — Additive migration and durable record integrity

- **Protected outcome:** upgrade cannot lose/rewrite/orphan accepted data or leave partially constrained new records.
- **Operating/failure model:** trusted Linux service, schema 3, real SQLite files, DDL failure, reopen, concurrent migration callers, invalid FK/check/unique values are in scope.
- **Explicit exclusions:** disk/media failure, hostile DB editing, backup/restore/USB, retention deletion, Postgres, distributed writers, and downgrade.
- **Assurance level:** transactional additive local migration with preserved rows, database constraints, WAL/foreign keys, deterministic reopen.
- **Sufficient proof:** tests 1-7 and 32, including injected DDL rollback,
  concurrent migration, legacy-event compatibility, and append-only guards.
- **Implementation boundary:** standard library/`sqlite3`, additive DDL/indexes/triggers, typed validation, owned files.
- **Proportionality ceiling:** one migration and named V1 records; no ORM/framework/second DB/backup/retention abstraction.
- **Stop/return:** required rewrite/loss, version mismatch, ambiguous M1-01 shape, or non-additive need returns to Project Architect.

### Q2 — Atomic, idempotent, ordered state changes

- **Protected outcome:** duplicate/stale/interrupted/contending commands cannot create two truths, skip a gate, partially claim, or detach state from event.
- **Operating/failure model:** one service with concurrent local callers; replay, conflicting keys, stale version/state, injected failure, busy timeout, lock contention are in scope.
- **Explicit exclusions:** multi-machine coordinators, distributed consensus, hostile same-UID mutation, filesystem/kernel failure after durable commit, unbounded throughput.
- **Assurance level:** serialized local writes, optimistic versions, unique idempotency, constraints, one ordered event per command.
- **Sufficient proof:** tests 8-18 with simultaneous callers, ordinary record
  and transition failure injection, exact reopen state, and claim contention.
- **Implementation boundary:** `BEGIN IMMEDIATE`, 5-second busy timeout, canonical fingerprints, constraints/indexes, no background retry.
- **Proportionality ceiling:** one box/one logical Development Manager; no workflow engine/distributed lock service.
- **Stop/return:** distributed coordination, auto-retry policy, new transition, or more than one correction returns to Project Architect.

### Q3 — Conservative lease expiry and restart recovery

- **Protected outcome:** restart/expiry/orphan/late completion cannot duplicate lease/attempt/lock or trigger external action without reread.
- **Operating/failure model:** orderly/killed service, commit boundaries, unexpired/expired leases, mismatched relations, duplicate startup, stale completion are in scope.
- **Explicit exclusions:** machine reboot proof, executor operations, Git/GitHub reconciliation, network partitions, clock rollback, supervision, corrupt database recovery.
- **Assurance level:** deterministic conservative DB reconciliation that blocks uncertainty, releases expired locks, returns observations, and launches nothing.
- **Sufficient proof:** tests 19-22 after actual close/reopen.
- **Implementation boundary:** injected UTC clock, recovery module, transactional state/wait/events, no external call.
- **Proportionality ceiling:** named local cases only; no supervisor/reboot harness/executor/redispatch.
- **Stop/return:** any case not safely reducible to observe/block/Coordinator return goes to Project Architect without invented fact/action.

### Q4 — Honest operational projection without authority inversion

- **Protected outcome:** storage cannot become another editable project plan or fabricate agent/review/acceptance facts/cross approval boundary.
- **Operating/failure model:** exact caller-supplied projections/lifecycle/role
  observations/review/acceptance/authoritative merge observations,
  unavailable values, binding merge policy, and reserved routing are in scope.
- **Explicit exclusions:** graph parsing, scheduling, role invocation, review
  judgment, registration, live Git/GitHub ingestion, Atlas, performing a
  merge/deploy, and successor selection.
- **Assurance level:** closed typed/source-linked records, append-only judgments, explicit unknown/unavailable, no controller entrypoint.
- **Sufficient proof:** tests 7, 10-12, 30-32 and changed-path review, including
  exact-head coverage and authoritative observation guards.
- **Implementation boundary:** storage/value/recovery/docs only; no CLI/HTTP/executor/GitHub/notification adapter.
- **Proportionality ceiling:** accepted V1 records/transitions only; no M2/M3/M4 policy implementation.
- **Stop/return:** missing source, fabricated outcome, new state, or reserved material choice returns to Project Architect.

### Q5 — Bounded evidence, secret, context, and usage handling

- **Protected outcome:** storage retains no direct credential/raw prompt/trace and never turns unavailable/estimated account facts into false exact/enforcement facts.
- **Operating/threat/failure model:** trusted callers, closed safe payload
  variants <=1 MiB, provider/reference observations, redacted prose receipts,
  direct invalid credential carriers, partial counters, source/quality/time,
  allowance, and decimal reconciliation are in scope.
- **Explicit exclusions:** semantic inspection of ordinary prose, malicious
  encoding/encryption, arbitrary artifact scanning, external log/file
  retention, provider scraping/billing correctness, universal tokenizer, and
  budget/routing enforcement.
- **Assurance level:** structural closed-schema rejection, reference-only
  credential records, pre-redacted prose receipts, honest measurement labels,
  runtime precedence, and exact native-unit arithmetic.
- **Sufficient proof:** tests 24-29 and 32 including exact context arithmetic,
  invalid raw fields/carriers, unavailable-not-zero, runtime precedence, and no
  quota conversion.
- **Implementation boundary:** standard-library structural validation/SHA-256/
  `decimal.Decimal`/canonical JSON; no provider/tokenizer call, semantic prose
  scanner, or general DLP.
- **Proportionality ceiling:** structured DB payloads/named credential classes; M3 owns executor capture/scanning.
- **Stop/return:** required raw secret/prompt/trace, scrape, unsupported conversion, budget policy, or stronger adversarial guarantee returns to Project Architect and Owner when reserved.

### Q6 — M0-D11 runtime-path containment for every new entry route

- **Protected outcome:** no new store, read, write, or recovery entry can open
  or create a database/runtime artifact outside the repository's physical
  `var/` tree through misconfiguration, a forged config, or a symlinked/swapped
  component.
- **Operating/threat/failure model:** trusted Linux service, ordinary caller
  mistakes, source-tree/outside paths, pre-existing symlinks, forged
  `RuntimeConfig`, and a component swap before final safe acquisition are in
  scope for every new constructor/factory/public callable.
- **Explicit exclusions:** M0-D11's hostile concurrent same-UID/root action
  after acquisition, mount/kernel compromise, custom VFS, multi-user hostile
  storage, backup/USB, and service-account provisioning.
- **Assurance level:** the exact practical trusted-local M0-D11 containment
  contract, reused without a weaker alternate connection/path entry.
- **Sufficient proof:** tests 23 and 32 parameterize every named constructor,
  factory, record, transition, claim, read, and recovery route; each rejects
  before artifacts and repeated valid calls stay beneath independently derived
  physical `var/`.
- **Implementation boundary:** existing `RuntimeConfig`, directory-FD
  acquisition, `SQLiteFoundation._connect`, standard library, and owned files;
  no new dependency, VFS, or privileged operation.
- **Proportionality ceiling:** parameterized negative coverage of all new entry
  routes and representative operations; no stronger host-security project.
- **Stop/return:** any new path/connection route or stronger actor guarantee
  that cannot reuse M0-D11 returns to the Project Architect before dispatch.

## Exclusions and required returns

M1-02 excludes:

- `maestro project create/register`, binding activation, and registration completion;
- Git mutation, GitHub, credential values/injection, branch/worktree/PR/check/merge operations,
  and review invocation or judgment (durable caller-supplied review records are
  still in scope);
- worker selection/submit/poll/status/cancel/grading/correction dispatch or agent invocation;
- Atlas snapshot/HTTP/event stream/direct DB access;
- notification delivery, Slack, webhooks, Murphy, deployment, or automatic next work;
- USB backup/restore, daily backup implementation, retention deletion, Postgres, multi-coordinator operation, or live projects; and
- machine reboot/service supervision proof, which belongs to M1-06.

Architecture/public-contract, security/data/credential/external-access, material-risk, spending, production/deployment/merge, or infeasible-contract choices return through Project Architect to Owner. Routine findings, rollback, contention, waiting, recovery, Integration/review, and one correction do not.

## Handoff and acceptance

The Developer hands one exact commit/evidence to Integration. Integration uses `validate-only` when unchanged; Integration-authored code requires a different reviewer.

Independent review covers the exact accepted-M1-01-base to M1-02-head range, every schema/state/API/quality proof and gate. One targeted correction is available under M0-D05. Uncovered commits, unrelated changes, missing contract, new failure class, or exhausted correction return to Project Architect.

After approval and complete final-head coverage, routine acceptance belongs to Project Architect. It releases M1-03, M3-01, and M4-01 dependencies only as their packets permit. It does not register a project, start the service, expose Atlas, dispatch a worker, contact an external system, merge/deploy, or test a live product.
