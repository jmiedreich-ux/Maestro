# M1-03 — Connect Real Repository and GitHub Operations

**Status:** Materialized candidate pending Decision Fidelity review; dependency
blocked on integrated M1-02C acceptance; not released and never itself runtime
`Dispatchable`
**Packet ID:** `maestro-m1-03-real-repository-github-adapter`
**Graph node:** `MAESTRO-M1-03-REAL-REPOSITORY-GITHUB-ADAPTER`
**Graph revision:** `maestro-m1-m4-real-r1`
**Planning source base:** `8a126be0a0fd57ff918954c6d5faeb10b0aab71d`
**Implementation base:** unresolved until routine Project Architect acceptance
of the exact integrated M1-02C implementation head
**Implementation shape:** two serial, independently reviewed slices M1-03A
and M1-03B; the umbrella node is never leased
**Decision authority:** [M0-D01](../decisions/m0-d01-operational-database.md),
[M0-D02](../decisions/m0-d02-project-registration.md),
[M0-D03](../decisions/m0-d03-access-and-secrets.md),
[M0-D05](../decisions/m0-d05-rework-review-and-escalation.md),
[M0-D06](../decisions/m0-d06-project-manifest-contract.md),
[M0-D11](../decisions/m0-d11-linux-runtime-filesystem-boundary.md),
[M0-D12](../decisions/m0-d12-bounded-quality-contracts.md),
[M0-D14](../decisions/m0-d14-context-and-token-reporting.md), and
[M0-D15](../decisions/m0-d15-real-m1-m4-implementation-path.md)
**Active current handoff:** `ai/handoffs/current.md` at the planning source
base; it controls current status and restart direction under M0-D15
**Roadmap/planning authority:** `sources/planning/maestro-alpha-1-handoff.md`, M1;
`docs/planning/maestro-master-plan.md`;
`docs/planning/agent-workforce-control-plane.md`. The older
`sources/planning/current-handoff.md` is historical planning input only, not
active handoff or dispatch authority. M0-D15 and `ai/handoffs/current.md`
control any conflict with that historical source.
**Typed hard dependency:**
`MAESTRO-M1-02C-CUMULATIVE-INTEGRATION-PROOF @ ProjectArchitectAccepted`,
with exact final implementation head, schema/API inventory, Integration PASS,
and complete independent-review coverage; currently unsatisfied
**Implementation role:** dedicated Maestro Developer
**Execution route:** cloud collaboration worktree / dedicated Maestro
Developer / `codex-cloud-maestro-developer` / session-inherited Codex model;
factual model/runtime identity is recorded at each dispatch preflight
**Role/SOP versions:** `docs/agents/maestro-developer.md`,
`docs/agents/coding-agent-sop.md`, `docs/agents/integration-agent.md`,
`docs/agents/independent-review-agent.md`, and
`docs/agents/maestro-development-manager.md` at the planning source base;
bootstrap Coordinator authority is M0-D15 plus `ai/handoffs/current.md`
**Decision Fidelity route:** fresh independent Decision Fidelity Reviewer
**Integration route:** Integration Agent, `validate-only` unless assembly is
required
**Independent implementation-review route:** fresh Independent Implementation
Reviewer over each exact slice range and any correction-only range
**Routine acceptance authority:** Project Architect under M0-D15

## Candidate, dependency, and external-activation boundary

This packet materializes the known M1-03 design. It does not release either
slice, provision a repository or credential, activate external access, or
authorize a network call. It remains both `DependencyBlocked` and
`PendingDecisionFidelity` until:

1. integrated M1-02C has routine Project Architect acceptance at an exact head;
2. this packet is reconciled to that accepted schema/API inventory and receives
   Decision Fidelity `APPROVE` over its exact planning range;
3. the Project Architect releases the reviewed M1-03A candidate from that exact
   accepted base; and
4. the Coordinator completes exact preflight and atomically acquires the current
   slice's declared locks.

M1-03B code may be implemented, reviewed, and routinely accepted by the
Project Architect without a credential. Its networked qualification may begin
only after the Project Architect stores an active `ExternalSetupAuthority`
through the exact API below, backed by Owner acceptance evidence for the
reserved repository, identity, provider/reference, capability, lifetime, and
spending facts. Missing, stale, expired, revoked, superseded, broader, live,
personal, or ambiguous setup blocks before DNS, socket, Git remote, or GitHub
API activity. Routine code acceptance remains Project Architect-owned and
never grants external authority.

That pre-activation decision records code-readiness evidence at the exact
reviewed head; it is not a new packet lifecycle state. It does not mark the B
slice, umbrella M1-03, or a downstream dependency accepted. After the real
qualification, Integration/review validate the same head plus external
evidence and the Project Architect records the routine integrated B/M1-03
acceptance. The Owner supplies acceptance evidence for the reserved setup
facts only; the Owner is not the code or packet acceptor.

The following are intentionally unresolved setup values, not choices an
implementer may fill in: GitHub organization/repository, service identity or
App installation, secret provider, secret reference, reviewer identity,
approved Git author/committer identity references, credential lifetime, and
any paid plan. Selecting or expanding any of them returns through the Project
Architect to the Owner under M0-D15.

The closed, non-secret `ExternalSetupAuthority` is never caller-supplied to an
operation. Both adapters receive an authoritative lookup at construction and
resolve the exact `external_setup_record_id` from durable state:

```text
external_setup_record_id; revision; supersedes_setup_record_id NULL;
record_digest; reserved_facts_digest; owner_decision_reference;
owner_acceptance_evidence_id;
project_architect_reference; project_id; binding_id;
repository_identity; repository_classification = DedicatedNonLive;
github_repository_reference; push_remote_reference;
service_identity_kind CHECK GitHubApp|EquivalentRepositoryScopedService;
service_identity_reference; credential_provider; credential_reference_name;
git_author_identity_reference; git_committer_identity_reference;
capability_names; reviewer_references; valid_from; expires_at NULL;
spending_disposition CHECK NoNewSpend|OwnerApprovedSpend;
state CHECK Active|Expired|Revoked|Superseded;
recorded_at; updated_at; version
```

Capabilities are a subset of `RepositoryMetadataRead`, `ContentsRead`,
`FeatureBranchWrite`, `PullRequestsRead`, `DraftPullRequestWrite`,
`ChecksRead`, `ReviewsRead`, and `ReviewRequestWrite`. Each operation requires
only its named subset. Unknown/admin/default-branch/protection/merge/workflow/
deployment/secret capabilities are rejected even if the external identity has
them. The record/API stores accepted authority facts only; it does not create a
repository or identity, retrieve a secret, provision/rotate a credential, or
expand an external grant.

`record_external_setup_authority` is owned by the Project Architect role and
requires a referenced immutable M1-02 evidence row containing the Owner's
acceptance of every reserved external fact. Revision 1 has no superseded ID.
Each later revision is exactly the latest revision plus one and names that
latest record. If the latest row is `Active`, one transaction marks it
`Superseded`; an already `Expired` or `Revoked` latest row remains terminal.
The transaction inserts the new `Active` row and appends one supersession event
whose closed before/after payload names both records. An unchanged
`reserved_facts_digest` returns the existing latest record as idempotent and is
not a new revision. No API edits accepted immutable facts in place.

`expire_external_setup_authority` is a clock-driven recovery API that changes
`Active -> Expired` only when `expires_at IS NOT NULL AND now >= expires_at`.
`revoke_external_setup_authority` changes `Active -> Revoked` only from an
authoritative provider/security evidence reference and cannot broaden facts.
Expiration/revocation does not wait for Owner action because it only removes
authority. `Expired`, `Revoked`, and `Superseded` are terminal. Re-enabling,
changing, or expanding setup requires a new Project Architect-recorded revision
with new Owner acceptance evidence.

The injected `ExternalSetupAuthorityLookup.get(external_setup_record_id,
expected_revision, expected_digest, project_id, binding_id,
repository_identity)` reads only the durable record and uses its constructor
clock. It returns `Active` only when ID/revision/digest/project/binding/
repository all match, `valid_from <= now`, expiry is absent or later than
`now`, there is no newer revision, and state is `Active`; it never substitutes
the latest record.
At startup, M1-02 recovery expires due rows before reconciling M1-03 actions and
reconstructs this lookup from the accepted `OperationalStateStore`; no
process-memory cache is authority after restart.

## Exact dispatch controls

- Each slice uses its exact clean branch/worktree and the exact routinely
  accepted predecessor head. No rebase, merge, or unaccepted predecessor is a
  valid base.
- Acquire every declared path/shared/external lock before work. Only the
  current serial slice may write an owned path. External locks are acquired
  only for the attended B qualification and never by planning or offline tests.
- Each slice permits one initial Developer attempt and at most one M0-D05
  correction for committed in-scope work failing a named gate. Infrastructure
  failure stops to the Coordinator. A missing or infeasible contract returns to
  the Project Architect. A new credential, security, external-access, spending,
  merge, deployment, or production choice returns through the Project
  Architect to the Owner.
- M0-D05 is exact: absent/corrupt delivery, prohibited scope/security effect,
  or missing traceability rejects immediately with no correction; a delivered
  in-scope implementation that fails a named test/check may receive one
  correction containing only that failure; a second failure or new failure
  class returns to the Project Architect. An architecture-contract defect is
  `NeedsReplan`, not implementer rework.
- Each implementation slice has a 150-minute ceiling. After 10 minutes without
  visible progress, the Coordinator may request one factual status; later
  requests remain at least 10 minutes apart and allow a 2-minute reply window.
  The attended external qualification has a separate 90-minute ceiling and
  performs no implementation unless a named gate fails and the one correction
  is authorized.
- This packet's implementation dispatch policy requires 32,768 input/context
  tokens plus an independent 8,192-token output/handoff reserve, so configured
  capacity is at least 40,960. Warn at 16,384 remaining, prepare handoff at
  12,288, and stop new work at 8,192. Record actual model, runtime, configured
  capacity, counting method, source/time, and available counters; unsupported
  values are `unavailable`. These values govern these Developer dispatches
  only and are not production adapter constants.
- A slice handoff records exact base/head, changed paths, full command outcomes,
  schema/API inventory, local and external side effects, action IDs and
  redacted evidence references, exact setup ID/revision/digest and Owner-
  acceptance evidence reference when used, non-secret runtime-session metadata,
  idempotency/concurrency/restart proof, model/runtime/context facts, released
  locks, and every `UNTESTED` item. Raw headers, credentials, prompts, command
  traces, and unredacted Git/GitHub output never enter handoff text or durable
  state.

## Outcome

Add a repository/GitHub adapter that observes authoritative repository facts
and performs only explicitly authorized branch, commit, push, draft-pull-
request, reviewer-request, check-observation, and review-observation actions.
It records intent before an external effect, reconciles an uncertain outcome
from authoritative Git/GitHub facts, and stores a closed redacted outcome.

The adapter never chooses work, grants authority, creates or registers a
project, changes an approved binding, merges, approves a review, bypasses
branch protection, writes the default branch, force-pushes, deploys, contacts a
live project, or silently substitutes a personal credential.

## Foundations and authority to preserve

- Repository/GitHub remain authoritative for code, refs, pull requests,
  checks, reviews, and CI. SQLite stores commanded intent and observed
  projections; it is not a second writable repository or review system.
- Preserve M1-01's strict manifest and exact-commit loader. Extend its
  argument-array, closed-stdin, no-shell Git boundary; do not weaken its
  read-only behavior or reuse a mutating adapter inside authority loading.
- Preserve the accepted M1-02 schema, transactions, event ordering, closed
  payloads, idempotency, locks, recovery, context/usage, acceptance, and
  M0-D11 store-construction boundary. M1-03 uses its public APIs rather than
  opening SQLite directly through an alternate path.
- M0-D02/D06 binding facts control repository identity, default branch,
  branch/PR/merge policy, checks, secret references, locks, and acceptance
  authority. The adapter rejects missing or conflicting facts and never
  supplies a default.
- M0-D03 permits a repository-scoped service identity. Secret values are
  injected only at runtime by the separately selected provider. Durable state
  carries `provider` and `reference_name` only. Stale/revoked/unavailable
  observations block; no personal or environment fallback exists.
- M0-D15 permits real proof only against a dedicated non-live repository. A
  `LiveProduct` or `Unknown` classification is rejected before repository
  access. Temporary repositories created by the test process are
  `EphemeralTest`; the Owner-approved proving repository is `DedicatedNonLive`.
- Polling and reconciliation are the V1 recovery authority. No webhook or
  callback creates dispatch authority.

## Authority and policy inputs

Every public operation receives an immutable `RepositoryOperationAuthority`
constructed by the already validated project/binding layer. The adapter cannot
construct, load, approve, or broaden one.

```text
project_id; binding_id; authority_reference; authority_source_type
  CHECK ActiveBinding|ProjectArchitectApprovedCandidateBinding;
repository_identity; repository_path; repository_classification
  CHECK EphemeralTest|DedicatedNonLive;
default_branch; branch_policy; pull_request_policy; merge_policy;
allowed_path_prefixes; declared_check_names; resource_lock_ids;
github_repository_reference NULL; credential_provider NULL;
credential_reference_name NULL; external_setup_record_id NULL;
external_setup_revision NULL; external_setup_digest NULL;
push_remote_reference NULL;
git_author_identity_reference; git_committer_identity_reference;
accepted_at; source_commit; binding_digest
```

`ProjectArchitectApprovedCandidateBinding` is accepted only with a Project
Architect authority reference supplied by the later M1-04/M1-05 create or
register workflow. It does not activate or register a project. Networked
operations additionally require all nullable GitHub/setup fields,
`push_remote_reference`, an active latest secret-reference observation, and
the exact Project Architect-recorded active setup ID/revision/digest carrying
Owner acceptance evidence. A method's logical remote reference must equal that
authority value; the injected transport resolves it to a credential-free
locator. Local ephemeral tests may carry an exact test-only filesystem remote
reference and require none of the credential/setup fields.

The closed policy for this packet accepts only:

```text
branch_policy = feature-branch
pull_request_policy = draft-required
merge_policy = no-automatic-merge
```

Any other value is `UnsupportedRepositoryPolicy`, not an inferred equivalent.
Every mutating target is a full `refs/heads/<feature>` ref accepted by
`git check-ref-format`; it must differ from the observed
`refs/heads/<default_branch>`. Symbolic refs, tags, remote-tracking refs,
revision expressions, abbreviated SHAs, ref deletion, and refspec wildcards
are rejected.

Every operation also receives this closed `RepositoryOperationContext`:

```text
run_id; packet_id NULL; actor_type; actor_id; purpose_reference;
correlation_id; causation_event_id NULL; expected_binding_version;
resource_lock_ids
```

`run_id` names the owning M1-02 run. If present, `packet_id` must belong to
that run. `purpose_reference`, project/binding identity, action kind, and—once
known—external object reference are durably recorded for M0-D03. Actor,
correlation, causation, and sorted unique locks use the accepted M1-02
validators; event time comes only from the adapter's constructor clock.
Malformed/missing context fields fail structural validation before intent.
Existence/currentness of the run/binding, packet/run relation, binding version,
and declared lock ownership are mutable operational lookups performed after
`Prepared`; their failure records `Prepared -> Blocked`.

Commit identity is a closed non-secret
`GitIdentity(authority_reference, name, email)`. `authority_reference` must
equal the corresponding authority field; name/email are the explicitly
approved values that will be public in the Git commit, each is bounded to 254
UTF-8 bytes, and NUL/control/newline or malformed email values are rejected.
They are never read from repository/global/system Git configuration.

## Additive operational schema

M1-03A advances the accepted integrated M1-02 schema version `4` to version
`5`. Before release, the packet must be reconciled if accepted M1-02C is not
exactly schema `4` with the assumed event/idempotency/store API. The migration
is additive, preserves every existing row, and inserts version `5` only after
all DDL succeeds in one transaction. It creates these tables without
dropping, renaming, rebuilding, or rewriting an earlier table.

### `external_setup_authorities`

```text
external_setup_record_id TEXT PRIMARY KEY;
revision INTEGER NOT NULL CHECK revision > 0;
supersedes_setup_record_id TEXT NULL
  REFERENCES external_setup_authorities(external_setup_record_id);
record_digest TEXT NOT NULL;
reserved_facts_digest TEXT NOT NULL;
owner_decision_reference TEXT NOT NULL;
owner_acceptance_evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id);
project_architect_reference TEXT NOT NULL;
project_id TEXT NOT NULL REFERENCES projects(project_id);
binding_id TEXT NOT NULL REFERENCES project_bindings(binding_id);
repository_identity TEXT NOT NULL;
repository_classification TEXT NOT NULL CHECK repository_classification = 'DedicatedNonLive';
github_repository_reference TEXT NOT NULL;
push_remote_reference TEXT NOT NULL;
service_identity_kind TEXT NOT NULL CHECK service_identity_kind IN
  ('GitHubApp','EquivalentRepositoryScopedService');
service_identity_reference TEXT NOT NULL;
credential_provider TEXT NOT NULL; credential_reference_name TEXT NOT NULL;
git_author_identity_reference TEXT NOT NULL;
git_committer_identity_reference TEXT NOT NULL;
capability_names_json TEXT NOT NULL; reviewer_references_json TEXT NOT NULL;
valid_from TEXT NOT NULL; expires_at TEXT NULL;
spending_disposition TEXT NOT NULL CHECK spending_disposition IN
  ('NoNewSpend','OwnerApprovedSpend');
state TEXT NOT NULL CHECK state IN ('Active','Expired','Revoked','Superseded');
recorded_at TEXT NOT NULL; updated_at TEXT NOT NULL;
version INTEGER NOT NULL CHECK version > 0;
UNIQUE(project_id,binding_id,revision);
UNIQUE(project_id,binding_id,record_digest);
UNIQUE(project_id,binding_id,reserved_facts_digest)
```

A partial unique index permits one `Active` row per `(project_id,binding_id)`.
Checks require revision 1 with null `supersedes_setup_record_id`, later
revisions with a non-null different predecessor, `valid_from < expires_at`
when expiry exists, sorted-unique closed capability/reviewer arrays, and the
M0-D03 provider/reference grammars. `reserved_facts_digest` is SHA-256 over the
reserved facts enumerated for Owner evidence below. `record_digest` is SHA-256
over the canonical immutable record fields from ID/revision/supersedes through
spending disposition, including `reserved_facts_digest` and both acceptance
references but excluding mutable state/timestamps/version. Triggers reject
`DELETE` and any update except the
guarded `Active -> Expired|Revoked|Superseded` APIs. Each insert or state
transition command appends one M1-02 event atomically. Closed event types are
`ExternalSetupAuthorityRecorded`, `ExternalSetupAuthorityExpired`,
`ExternalSetupAuthorityRevoked`, and `ExternalSetupAuthoritySuperseded`.
Record/supersede may insert `Active` only; no caller may insert a terminal
state or transition a terminal row.

The store surface is exact:

```python
ExternalSetupAuthorityStore(store, clock)

ExternalSetupAuthorityLookup(store, clock)

ExternalSetupAuthorityStore.record_external_setup_authority(
    record, idempotency_key, actor
) -> ExternalSetupAuthority

ExternalSetupAuthorityStore.supersede_external_setup_authority(
    expected_latest_id, expected_version, replacement, idempotency_key, actor
) -> ExternalSetupAuthority

ExternalSetupAuthorityStore.revoke_external_setup_authority(
    external_setup_record_id, expected_version,
    authoritative_revocation_evidence_id, idempotency_key, actor
) -> ExternalSetupAuthority

ExternalSetupAuthorityStore.expire_external_setup_authority(
    external_setup_record_id, expected_version, idempotency_key, actor
) -> ExternalSetupAuthority

ExternalSetupAuthorityLookup.get(
    external_setup_record_id, expected_revision, expected_digest,
    project_id, binding_id, repository_identity
) -> ExternalSetupAuthority
```

The production composition root passes the identical `Clock` instance to the
store, lookup, and both adapters. Constructors reject a lookup/store wired to a
different clock object, and no component constructs or consults another system
clock. None of these calls accepts `now`. Record/supersede require
`actor = ProjectArchitect`
and immutable Owner-acceptance evidence. Revoke accepts the Project Architect
recording authoritative revocation; expiry is a mechanical recovery action
available to the Development Manager. The adapter and Developer cannot call
record/supersede/revoke and cannot treat lookup failure as permission. Startup
enumerates due active IDs read-only and calls expiry once per row with
deterministic key `external-setup-expire:<record-id>:<expires-at>`; replay is
the original terminal result.

These store mutations use the accepted M1-02 closed failures only:
`InvalidRecord` for wrong role/evidence/digest/revision/state,
`StaleState` for expected-version mismatch, `IdempotencyConflict` for reused
key/different facts, `ResourceConflict` for a conflicting active row, and
`ResourceBusy` for busy exhaustion. Each fails before commit with no partial
row/event; exact replay returns the original record.

The required evidence row has
`evidence_kind = OwnerExternalSetupAcceptance`, an exact
`OwnerExternalSetupAcceptancePayload` below, and a `source_reference` equal to
`owner_decision_reference`. Its reserved-facts digest covers repository/
classification, remote references, service and Git identities,
provider/reference, capabilities/reviewers, validity/expiry, and spending
disposition. The setup store rejects a missing/different digest, non-Owner
acceptance reference, or evidence recorded outside the Project Architect
route. This evidence authorizes only those external facts; it does not accept
M1-03 code or its qualification result.

### `repository_actions`

```text
action_id TEXT PRIMARY KEY;
project_id TEXT NOT NULL REFERENCES projects(project_id);
binding_id TEXT NOT NULL REFERENCES project_bindings(binding_id);
run_id TEXT NOT NULL REFERENCES runs(run_id);
packet_id TEXT NULL REFERENCES packets(packet_id);
action_kind TEXT NOT NULL CHECK action_kind IN
  (ObserveLocalRepository,EnsureFeatureBranch,CreateCommit,PushFeatureBranch,
   ObserveGitHubRepository,EnsureDraftPullRequest,RequestReviewers,
   ObservePullRequest,ObserveChecks,ObserveReviews);
target_kind TEXT NOT NULL CHECK target_kind IN
  (Repository,Branch,Commit,PullRequest,Checks,Reviews);
target_reference TEXT NOT NULL;
authority_reference TEXT NOT NULL;
purpose_reference TEXT NOT NULL;
external_setup_record_id TEXT NULL;
external_setup_revision INTEGER NULL CHECK external_setup_revision > 0;
external_setup_digest TEXT NULL;
idempotency_key TEXT NOT NULL UNIQUE;
command_fingerprint TEXT NOT NULL;
request_payload_json TEXT NOT NULL;
state TEXT NOT NULL CHECK state IN
  (Prepared,InFlight,ObservedSucceeded,ObservedFailed,OutcomeUnknown,Blocked);
external_object_reference TEXT NULL;
result_payload_json TEXT NULL;
failure_payload_json TEXT NULL;
prepared_at TEXT NOT NULL; started_at TEXT NULL; observed_at TEXT NULL;
updated_at TEXT NOT NULL; version INTEGER NOT NULL CHECK version > 0;
UNIQUE(project_id,action_kind,target_reference,idempotency_key)
```

A partial unique index on `(project_id, target_kind, target_reference)` while
`state IN ('InFlight','OutcomeUnknown')` prevents two active/uncertain effects
against one logical target while still allowing a competing structurally valid
request to record `Prepared -> Blocked`. A trigger rejects a non-null packet
whose run does not equal `run_id`. The three external-setup columns are all null or all
non-null; every GitHub action and non-file push requires all three, while local
operations require all null. Request/result/failure values use only the closed
payload variants below. Triggers reject `DELETE`; state changes use the exact
API and append an event in the same transaction.

Database checks enforce: `Prepared` has null start/observation/result/failure/
external-object fields; `InFlight` has `started_at` and null observation/result/
failure; `OutcomeUnknown` has `started_at`, an ambiguity failure payload, and
null observation/result; `ObservedSucceeded` has start/observation/result,
null failure, and an external object reference for every GitHub action;
`ObservedFailed` has start/observation/failure and null result; `Blocked` has
observation/failure, null result, and may have null start only when blocked
before effect. Terminal rows cannot transition. Every successful state change
increments `version` exactly once and `updated_at` is the injected event time.

### `repository_observations`

```text
observation_id TEXT PRIMARY KEY;
action_id TEXT NOT NULL REFERENCES repository_actions(action_id);
project_id TEXT NOT NULL REFERENCES projects(project_id);
binding_id TEXT NOT NULL REFERENCES project_bindings(binding_id);
observation_kind TEXT NOT NULL CHECK observation_kind IN
  (LocalRepository,Branch,Commit,Push,GitHubRepository,PullRequest,
   ReviewerRequest,Check,Review);
source TEXT NOT NULL CHECK source IN (LocalGit,BareRemote,GitHub);
source_object_reference TEXT NOT NULL;
source_version TEXT NOT NULL;
payload_json TEXT NOT NULL;
observed_at TEXT NOT NULL;
observation_fingerprint TEXT NOT NULL UNIQUE
```

Rows are append-only. The fingerprint is the SHA-256 of kind, source, source
project/binding, source object/version, and canonical closed payload; local
observation time is not a deduplication input. Re-observing identical source
facts returns the existing row. A changed authoritative fact or source version
appends a new row; it does not rewrite history.

M1-03 adds the closed event types
`RepositoryActionPrepared`, `RepositoryActionStarted`,
`RepositoryActionOutcomeUnknown`, `RepositoryActionBlocked`,
`RepositoryActionFailed`, `RepositoryObserved`, `FeatureBranchObserved`,
`CommitObserved`, `PushObserved`, `DraftPullRequestObserved`,
`ReviewersRequested`, `ChecksObserved`, and `ReviewsObserved`. All use the
accepted M1-02 event writer and its required correlation, causation, actor,
fingerprint, time, safe-payload, and append-only rules.

## Closed payload and secret boundary

M1-03 accepts and persists only these bounded, canonical payloads in addition
to M1-02's accepted safe variants:

```text
OwnerExternalSetupAcceptancePayload(owner_reference,
  owner_decision_reference, reserved_facts_digest, accepted_at)
ExternalSetupAuthorityPayload(external_setup_record_id, revision,
  supersedes_setup_record_id NULL, record_digest, reserved_facts_digest,
  owner_decision_reference, owner_acceptance_evidence_id,
  project_architect_reference, project_id, binding_id,
  repository_identity, service_identity_reference, credential_provider,
  credential_reference_name, capability_names, reviewer_references,
  valid_from, expires_at NULL, state)
ObserveRepositoryRequestPayload(expected_head, authority_digest)
EnsureBranchRequestPayload(full_ref, base_commit, authority_digest)
CreateCommitRequestPayload(full_ref, expected_parent, changed_paths,
  changed_path_input_digests, author_reference, committer_reference,
  message_digest, redaction_receipt_reference, authority_digest)
PushRequestPayload(full_ref, local_commit, expected_remote_commit NULL,
  remote_reference, authority_digest)
DraftPullRequestRequestPayload(head_ref, head_commit, base_ref,
  title_digest, body_digest, title_redaction_receipt_reference,
  body_redaction_receipt_reference, authority_digest)
ReviewerRequestPayload(pull_request_number, head_commit,
  reviewer_references, authority_digest)
ObserveExternalObjectRequestPayload(object_kind
  GitHubRepository|PullRequest|Checks|Reviews, object_reference,
  expected_head NULL, declared_check_names, authority_digest)
RepositoryObservationPayload(repository_identity, default_branch,
  head_commit, worktree_state Clean|Dirty, observed_ref_digest)
GitHubRepositoryObservationPayload(repository_identity, default_branch,
  default_head_commit, visibility Public|Private|Internal|Unknown,
  default_branch_protected, protection_digest, archived, disabled,
  permissions_digest, observed_ref_digest)
BranchObservationPayload(full_ref, commit, default_branch=False,
  relation_to_expected Exact|Ahead|Behind|Diverged|Absent)
CommitObservationPayload(commit, parent_commit, tree_object, author_reference,
  committer_reference, message_digest, changed_path_digests)
PushObservationPayload(full_ref, local_commit, remote_before NULL,
  remote_after, result Created|FastForwarded|AlreadyExact)
PullRequestObservationPayload(repository_identity, number, node_reference,
  base_ref, head_ref, head_commit, state Open|Closed|Merged,
  draft, title_digest, body_digest, url_reference)
ReviewerRequestObservationPayload(pull_request_number, head_commit,
  reviewer_references, result Added|AlreadyPresent)
CheckObservationPayload(external_id, name, head_commit,
  status Queued|InProgress|Completed|Unknown, source_status,
  conclusion NULL|Success|Failure|Neutral|Cancelled|Skipped|TimedOut|
  ActionRequired|Stale|StartupFailure|Unknown, source_conclusion NULL,
  details_url_reference NULL, started_at NULL, completed_at NULL)
ReviewObservationPayload(external_id, pull_request_number,
  reviewer_reference, commit NULL, state
  Pending|Commented|Approved|ChangesRequested|Dismissed,
  submitted_at NULL)
CheckObservationBatchPayload(head_commit, checks)
ReviewObservationBatchPayload(pull_request_number, head_commit, reviews)
ExternalFailurePayload(error_code, retry_class Never|AfterReconcile,
  redacted_message, redaction_receipt, provider NULL, reference_name NULL)
```

`OwnerExternalSetupAcceptancePayload` is allowed only for its matching M1-02
evidence kind, and `ExternalSetupAuthorityPayload` only for setup-authority
events. The request variants are the only values allowed in
`repository_actions.request_payload_json`; the observation variants are the
only values allowed in successful result JSON and
`repository_observations.payload_json`; `ExternalFailurePayload` is the only
failure JSON. Extra keys, a request/action-kind mismatch, and any other root
shape fail before SQL.

IDs, URLs, refs, timestamps, commits, digests, canonical JSON, and size limits
reuse M1-02 validation. `source_status` and `source_conclusion` are lowercase
GitHub enum tokens matching `[a-z][a-z0-9_]{0,63}` and retained without
interpretation; `Unknown` is an honest normalization for a source token outside
the closed known set, not a success or failure. `url_reference` permits only canonical
`https://github.com/<owner>/<repo>/...` with no userinfo, query, fragment, or
credential material. `changed_path_digests` contains normalized repository-
relative paths and blob digests, not file content. Titles, bodies, and commit
messages cross the adapter only as an already validated M1-02
`RedactedTextPayload(text, redaction_receipt_reference)` and persist only as
digest plus receipt reference; raw text is discarded after the call.

The runtime credential carrier is an opaque `ExternalAccessSession` with only
`session_id`, `external_setup_record_id`, `setup_revision`, `setup_digest`,
`project_id`, `repository_identity`, `service_identity_reference`, `provider`,
`reference_name`, `capability_names`, `issued_at`, `expires_at`, and `status`
(`Active|Stale|Revoked|Expired|Unavailable`) visible to this layer. The injected
`ExternalAccessSessionProvider.acquire(active_setup, required_capabilities)`
returns it; no operation accepts a caller-supplied session.

The session's setup ID/revision/digest, project, repository, service identity,
provider, and reference must exactly equal the active lookup record and latest
active secret-reference observation. Status must be `Active`; `issued_at` must
be at or after setup `valid_from`; `expires_at` is required, later than the one
adapter-clock `now`, and no later than setup expiry when setup expiry exists.
Session capabilities must be a subset of setup capabilities while containing
every capability required by the current action. Any extra, missing, or
mismatched fact is `ExternalSessionMismatch`/`CredentialScopeInsufficient` and
blocks before transport. The session offers transport execution without a
serializable secret getter. The adapter rejects mappings, strings, URLs,
headers, command arguments, environment snapshots, prompts, traces, or payload
fields offered as a credential. GitHub authorization headers, Git askpass
responses, private keys, and token values are never logged, returned, placed
in argv, embedded in URLs, or persisted. Raw subprocess/HTTP output exists
only in memory until the structural redactor returns a receipt; only the
closed redacted failure payload can cross into events, evidence, handoffs, or
Atlas-facing state.

No semantic prose scanner is claimed. Structural validation proves that every
durable/API carrier is one of the closed variants, every credential position
is provider plus reference, raw transport fields have no persistence path,
and representative PAT, bearer, private-key, query-string credential, and
userinfo carriers are rejected before an action enters `Prepared`.

Every adapter method returns exactly one `RepositoryOperationResult`:

```text
RepositoryOperationResult(
  status RejectedBeforeIntent|Blocked|Failed|OutcomeUnknown|Succeeded,
  action_id NULL only when RejectedBeforeIntent,
  observation NULL or exactly one closed observation/batch payload,
  error NULL or exactly one ExternalFailurePayload
)
```

`Succeeded` requires one observation and null error. Every other status
requires null observation and one error. `Blocked`, `Failed`, and
`OutcomeUnknown` require the durable action ID. A structurally invalid request
returns `RejectedBeforeIntent` with no action ID because no intent row/event was
written. Expected operational failures are returned, not raised as unstructured
exceptions; corruption/programming exceptions stop the caller and remain
outside this closed product-result contract.

## Action state, idempotency, and recovery

The exact state transitions are:

```text
Prepared -> InFlight | Blocked
InFlight -> ObservedSucceeded | ObservedFailed | OutcomeUnknown
OutcomeUnknown -> ObservedSucceeded | ObservedFailed | Blocked
ObservedSucceeded, ObservedFailed, Blocked -> terminal
```

Every new request follows one unambiguous sequence:

1. Perform **structural pre-intent validation** only: closed request/authority/
   context/result carrier shape, required fields, ID/ref/SHA/digest/timestamp/
   path grammar, size, action/request match, forbidden live/default/tag/force/
   shell/secret carrier, idempotency-key grammar, and existing-key replay or
   conflict. Failure returns `RejectedBeforeIntent`, the mapped structural
   error, `action_id = NULL`, and writes no action/event. Same-key/same-
   fingerprint replay returns the original result and creates nothing.
2. For a new structurally valid request, atomically insert `Prepared` and
   `RepositoryActionPrepared` before consulting mutable operational facts.
3. Read the current binding/policy/version, run/packet relation, M1-02 locks,
   expected Git/GitHub source facts and, for network operations, the exact
   setup lookup, latest secret-reference observation, and runtime session.
   Missing/stale/conflicting/unavailable dynamic facts atomically change
   `Prepared -> Blocked`, append `RepositoryActionBlocked`, return `Blocked`
   with that action ID, and invoke no Git mutation/network transport.
4. Atomically change `Prepared -> InFlight` and append its event, then invoke
   exactly one listed Git or GitHub operation. No database transaction remains
   open across Git, network, session acquisition, or redaction work.
5. Authoritatively observe the target and atomically append the observation,
   terminal action transition, and terminal event. Transaction failure rolls
   back the whole local write. Failure after the effect can have occurred
   leaves `InFlight`/`OutcomeUnknown` for read-only reconciliation, never a
   second mutation.

The exact failure-phase mapping is:

| Phase | Examples | Result / durable state |
|---|---|---|
| Structural pre-intent | malformed/extra field; invalid ID/ref/SHA/path; live/default/force target; raw secret carrier; idempotency conflict | `RejectedBeforeIntent`; no row/event; structural error code |
| Dynamic after `Prepared`, before effect | stale/missing binding or policy; absent/mismatched lock; missing/expired/revoked/superseded setup; stale secret observation; missing/broader/mismatched session; stale source ref | `Blocked`; `Prepared -> Blocked`; mapped authority/resource/credential/source error |
| Definite invocation failure before an effect | transport construction, DNS/connect/auth/permission/rate-limit response proving no mutation | `Failed`; `InFlight -> ObservedFailed`; mapped Git/GitHub error |
| Effect may have occurred | lost response, timeout after send, process death after invocation | `OutcomeUnknown`; `InFlight -> OutcomeUnknown` now or on restart |
| Authoritative post-effect fact matches | exact branch/commit/push/PR/reviewer observation | `Succeeded`; `InFlight|OutcomeUnknown -> ObservedSucceeded` |
| Authoritative post-effect fact proves no effect | exact ref/object absence after bounded authoritative reconciliation | `Failed`; `OutcomeUnknown -> ObservedFailed` |
| Bounded reconciliation remains inconclusive | unavailable/eventually inconsistent source with no safe conclusion | `Blocked`; `OutcomeUnknown -> Blocked`; `ExternalReconciliationRequired` |

Only authoritative observation resolves `OutcomeUnknown`; it never repeats the
mutation. Every transition requires exact expected state/version and one
event. `ObservedSucceeded` requires its append-only observation and, for
GitHub, exact external object reference. `ObservedFailed` requires the closed
failure plus an authoritative or transport fact proving no effect occurred.
`OutcomeUnknown` requires a named effect-before-observation seam. `Blocked`
requires a closed reason/evidence reference. Result, failure, and observed time
nullability are constrained consistently with those states.

Every command has an idempotency key and fingerprint over authority digest,
expected binding version, external setup ID/revision/digest when present, kind,
target, expected-before facts, and closed request payload. Same key and
fingerprint returns the original row/result; same key with different facts is
`IdempotencyConflict`. A terminal failed/blocked action is not retried by
changing state. A later attempt requires Project Architect or calling-policy
authority, a new idempotency key, and a fresh authoritative observation.

After process restart, an `InFlight` row is first changed to `OutcomeUnknown`
in one M1-02 transaction. Startup reconciliation then observes Git/GitHub and
records exactly one terminal transition/event. It first expires due setup rows,
then retrieves the original action's exact setup ID/revision/digest through the
durable injected lookup and acquires a current session no broader than that
record. Missing/stale setup or session resolves to `Blocked`, never a fallback.
Reconciliation never invokes a mutating API for the row. M1-02 resource locks
plus the active-target unique index serialize concurrent calls. Dynamic lock
conflict maps to a durable `Blocked/ResourceBusy`; stale expected refs/versions
map to durable `Blocked/RepositoryStateConflict`, both without an effect.

## Exact adapter APIs and side effects

The Development Manager is the eventual runtime caller under a released
packet/run; the project adapter supplies authority. The bootstrap Coordinator
only dispatches M1-03 implementation slices, and M1-03 itself provides no
clock/tick, scheduler, worker, or automatic-next-action loop.

The constructors are exact and receive the sole clock used for preparation,
start, lookup freshness, session validity, observation, expiry, and recovery:

```python
RepositoryAdapter(store, git_transport, clock,
    external_setup_lookup=None, external_access_session_provider=None)

GitHubAdapter(store, github_transport, external_setup_lookup,
    external_access_session_provider, clock)
```

Tests inject one deterministic clock object. Public methods do not accept
`now`, another clock, a caller-supplied setup record, or a caller-supplied
session. They accept a `RepositoryOperationAuthority`,
`RepositoryOperationContext`, idempotency key, expected-before values, and the
typed inputs shown. Every method returns the one `RepositoryOperationResult`.
No method accepts an arbitrary database path, credential value, shell command,
raw HTTP request, default branch override, or merge flag.

### Local Git adapter

```python
RepositoryAdapter.observe_repository(authority, context, expected_head,
    idempotency_key) -> RepositoryOperationResult

RepositoryAdapter.ensure_feature_branch(authority, context, full_ref,
    base_commit, idempotency_key) -> RepositoryOperationResult

RepositoryAdapter.create_commit(authority, context, full_ref,
    expected_parent, changed_paths, changed_path_input_digests,
    author: GitIdentity, committer: GitIdentity,
    message: RedactedTextPayload, idempotency_key) -> RepositoryOperationResult

RepositoryAdapter.push_feature_branch(authority, context, full_ref,
    local_commit, expected_remote_commit, remote_reference,
    idempotency_key) -> RepositoryOperationResult

RepositoryAdapter.reconcile(action_id, authority, context)
    -> RepositoryOperationResult
```

Exact behavior:

- `observe_repository` reads repository identity, worktree status, default ref,
  exact full-40-hex head, and requested refs. It performs no fetch and changes
  no file, index, object, config, ref, reflog, or remote.
- `ensure_feature_branch` creates only the requested local feature ref by
  compare-and-set at the exact base. Existing exact state is
  `AlreadyExact`; a different state conflicts. It never checks out a branch,
  changes `HEAD`, creates a worktree, or touches the default ref.
- `create_commit` includes only the sorted unique approved `changed_paths`,
  requires every path to be in the authority's allowed prefixes, and advances
  only the feature ref from `expected_parent` by compare-and-set. It does not
  change the caller's worktree, index, `HEAD`, config, or default ref. A failed
  attempt may leave unreachable Git objects but no visible ref/index/worktree
  mutation. The new tree is the expected parent's tree plus only those exact
  create/modify/delete entries. Each input is a regular file or the closed
  deletion marker `Absent`; Git symlinks, filesystem symlinks, submodules,
  directories, special files, and a digest changed between validation and
  object creation are rejected. Author/committer identities are explicit approved non-secret
  `GitIdentity` values matching the authority references; Git config or a
  personal identity is never fallback authority.
- `push_feature_branch` sends only
  `<local_commit>:<same refs/heads/feature>` to the explicit remote. It permits
  initial creation or fast-forward from the observed expected remote commit;
  it uses no force, deletion, wildcard, tag, mirror, default-ref, config write,
  or credential-bearing URL. `expected_remote_commit = None` means the
  authoritative remote observation was absent, not unknown. A remote with the
  same commit is idempotent. A different/non-fast-forward result conflicts.
- Local proof uses an explicit filesystem bare remote and no access session.
  A non-file/network remote requires the approved external setup and active
  session before Git is invoked. It resolves the authority's exact setup
  ID/revision/digest through the injected lookup and acquires an exact/narrower
  session with `ContentsRead` and `FeatureBranchWrite`; mismatch records
  `Prepared -> Blocked` before resolving or contacting the remote.

Git uses argument arrays, closed stdin except bounded message/content input,
`shell=False`, `GIT_CONFIG_NOSYSTEM=1`, a disabled global config,
`GIT_TERMINAL_PROMPT=0`, literal pathspecs, bounded timeout/output, and a
minimal allowlisted environment. No inherited credential helper or interactive
prompt is accepted. The implementation may use standard-library and Git
plumbing, but its observable guarantees above are mandatory.

### GitHub adapter

```python
GitHubAdapter.observe_repository(authority, context,
    idempotency_key) -> RepositoryOperationResult

GitHubAdapter.ensure_draft_pull_request(authority, context,
    head_ref, head_commit, base_ref, title: RedactedTextPayload,
    body: RedactedTextPayload, idempotency_key)
    -> RepositoryOperationResult

GitHubAdapter.request_reviewers(authority, context,
    pull_request_number, head_commit, reviewer_references,
    idempotency_key) -> RepositoryOperationResult

GitHubAdapter.observe_pull_request(authority, context,
    pull_request_number, expected_head, idempotency_key)
    -> RepositoryOperationResult

GitHubAdapter.observe_checks(authority, context,
    head_commit, declared_check_names, idempotency_key)
    -> RepositoryOperationResult

GitHubAdapter.observe_reviews(authority, context,
    pull_request_number, expected_head, idempotency_key)
    -> RepositoryOperationResult

GitHubAdapter.reconcile(action_id, authority, context)
    -> RepositoryOperationResult
```

Exact behavior:

- Every GitHub call first resolves the authority's exact setup ID/revision/
  digest through the injected durable lookup, then acquires and compares the
  runtime session. Required capabilities are: observe repository
  `RepositoryMetadataRead`; observe PR `PullRequestsRead`; ensure draft PR
  `PullRequestsRead + DraftPullRequestWrite`; request reviewers
  `PullRequestsRead + ReviewsRead + ReviewRequestWrite`; observe checks
  `ChecksRead`; and observe reviews `ReviewsRead`. Reconciliation uses only the
  read capabilities of its target kind and never acquires a write capability.
  No call or restart caches/substitutes a setup revision or session.
- The adapter uses the official GitHub API through an injected, authenticated
  provider transport. Endpoint/version/media-header mapping is isolated in that
  transport and must be verified against official GitHub documentation at
  implementation time; it is not accepted from arbitrary caller URLs.
- Before creating a draft PR, observe open PRs for the exact repository,
  head ref/commit, and base ref. One exact draft with matching title/body
  digests is `AlreadyExact`; zero permits one create; any conflicting or
  multiple match blocks. The method never converts an existing non-draft PR,
  edits an existing PR, closes one, or retries create after an unknown outcome.
- `request_reviewers` accepts sorted unique references from the approved setup,
  observes current requests first, and adds only missing approved reviewers.
  It does not submit, approve, dismiss, or alter a review. Unknown-outcome
  reconciliation observes the current requested-reviewer set before any later
  new action is considered.
- Pull-request, check, and review methods observe GitHub facts and preserve
  GitHub external IDs, head SHA, timestamps, status/conclusion, and redacted
  URLs. They do not infer approval, check success, coverage, or acceptance.
  M4-04 owns those policy decisions.
- Responses are bounded and paginated with explicit maximums. Exceeding the
  configured approved bound returns `ExternalResultTooLarge` and records no
  incomplete fact as complete. Rate limit, authentication, permission, and
  server failures remain visible typed failures; they are never success or an
  authorization fallback.

The public surface deliberately contains no merge, update-default-ref,
force-push, branch-protection, repository-admin, workflow-write, deployment,
secret-management, issue mutation, PR edit/close, review-submit, or review-
dismiss method.

## Error contract

Closed error codes are:

```text
InvalidRepositoryAuthority, InvalidOperationContext,
UnsupportedRepositoryPolicy,
LiveRepositoryRejected, DefaultBranchWriteRejected, PathOutsideAuthority,
InvalidGitReference, InvalidCommit, RepositoryStateConflict,
RemoteStateConflict, RepositoryNotFound, RepositoryDirty,
UnapprovedExternalAccess, ExternalSetupUnavailable, ExternalSetupExpired,
ExternalSetupRevoked, ExternalSetupSuperseded, ExternalSessionMismatch,
CredentialUnavailable, CredentialStale,
CredentialRevoked, CredentialExpired, CredentialScopeInsufficient,
SensitiveCarrierRejected, IdempotencyConflict, ResourceBusy,
GitOperationFailed, GitHubAuthenticationFailed, GitHubPermissionDenied,
GitHubRateLimited, GitHubRequestFailed, ExternalResultTooLarge,
OutcomeUnknown, ExternalReconciliationRequired
```

Dynamic pre-effect mapping is exact: missing/no accepted setup ->
`ExternalSetupUnavailable`; wrong ID/project/binding/repository/digest ->
`UnapprovedExternalAccess`; time-expired -> `ExternalSetupExpired`; terminal
revocation -> `ExternalSetupRevoked`; superseded or non-current revision ->
`ExternalSetupSuperseded`; runtime identity/provider/reference/setup mismatch or
capabilities broader than the setup -> `ExternalSessionMismatch`; unavailable,
stale, revoked, or expired session/secret observation -> the corresponding
`Credential*` code; missing required capability ->
`CredentialScopeInsufficient`; stale/missing current binding/policy ->
`InvalidRepositoryAuthority`/`UnsupportedRepositoryPolicy`; absent/conflicting
lock -> `ResourceBusy`; stale Git/GitHub target ->
`RepositoryStateConflict` or `RemoteStateConflict`. Each maps to durable
`Blocked` after `Prepared`. Structural forms of invalid context/authority/ref/
path/secret/idempotency map to `RejectedBeforeIntent` as defined above.

Errors expose code, safe subject reference, action ID if prepared, retry class,
and redacted receipt only. They do not expose command output, headers, response
bodies, environment, paths outside the approved repository, or secrets.

## Runtime and filesystem boundary

M0-D11 governs every Maestro-owned database, temporary file, redaction record,
cache, log, session, and transport artifact. New services accept an already
validated `OperationalStateStore` and injected adapters; they accept no caller-
supplied runtime/database/cache/log path. Any Maestro temporary file uses the
accepted `RuntimeConfig` directory-FD route beneath physical repository
`var/`, owner-only mode, no-follow semantics, and cleanup on success/failure.

The bound project worktree and explicitly approved remote are project
authority, not Maestro runtime storage. They are nevertheless confined to the
exact validated `RepositoryOperationAuthority`: no path discovery, parent
walk, sibling repository, symlink substitution, or arbitrary remote is
allowed. M1-03 writes only the approved repository facts described above and
never uses a project path as a place for Maestro logs, cache, credentials, or
temporary transport files.

## Real proof plan

All existing Alpha-01 through Alpha-03, accepted M1-01, and final accepted
M1-02 suites remain mandatory. No test is removed, skipped, weakened, made
order-dependent, or changed to accept a newer schema generically. Add these
named M1-03 proofs:

1. Schema 4 upgrades atomically to 5 with exact external-setup/action/
   observation tables; all prior rows/constraints/events survive; empty and
   populated migrations, reopen, duplicate migration, injected DDL failure
   rollback, foreign keys, WAL, and exact health version pass.
2. Every new store/service/factory/read/write/reconcile route reuses the M1-02
   store and M0-D11 boundary. Forged/outside/symlink/swapped runtime paths fail
   without artifacts; valid calls remain physically under `var/`.
3. Closed malformed authorities/contexts/requests/idempotency, unknown/live
   classification, symbolic/abbreviated SHA, invalid ref, default branch, tag,
   wildcard, ref deletion, raw secret, and outside path return
   `RejectedBeforeIntent` with null action ID and no row/event. Structurally
   valid requests with stale/missing current binding/policy, lock, source fact,
   or remote record `Prepared -> Blocked` with exact mapped code and no effect.
4. A real temporary worktree proves observation uses exact refs/objects, reports
   clean/dirty honestly, and makes byte-for-byte no repository change.
5. Real Git proves feature-branch creation is compare-and-set and idempotent;
   duplicate process/concurrent target attempts yield one ref, action, terminal
   event, and observation without touching `HEAD`, index, worktree, or default.
6. Real Git proves exact-path commit, explicit identities/message receipt,
   parent/tree/path digests, feature-ref CAS, unchanged worktree/index/default,
   rejection of extra/unapproved paths, stale parent, and rollback after every
   injected failure seam. Unreachable objects are the only permitted residue.
7. A real local bare remote proves absent-branch creation, fast-forward push,
   exact replay, non-fast-forward/concurrent rejection, bounded failure, and
   restart reconciliation after effect-before-record without duplicate push or
   default/tag/config mutation.
8. Same-key replay returns the original `RepositoryOperationResult` and action;
   same key/different facts rejects before a new intent. Separate processes and
   database reopen prove one active target and one terminal transition/event.
9. Structural carrier tests enumerate every new request/result/error/event/
   evidence/handoff route. Provider/reference succeeds; PAT, bearer header,
   private key, userinfo URL, credential query, environment snapshot, raw
   prompt, raw trace, raw Git/HTTP output, and unknown fields fail before
   durable state. Redacted receipts/digests persist; raw values do not appear in
   DB bytes, events, logs, exceptions, or returned objects.
10. One deterministic constructor clock supplies every timestamp/freshness/
    expiry comparison, and every local/GitHub/reconcile method returns exactly
    one discriminated `RepositoryOperationResult`. A local deterministic GitHub
    transport server proves exact repository/PR/reviewer/check/review request
    mapping, pagination bounds, typed failures, redaction, no credential in
    URL/log, and no unlisted endpoint or method.
11. Draft PR replay observes one exact existing PR. Mismatch/multiple candidate,
    non-draft, stale head/base, response loss, and process restart block or
    reconcile without a second create or edit.
12. Reviewer-request replay adds only missing approved reviewers. Concurrent
    duplicate and response-loss/restart paths observe before resolving and do
    not submit, approve, dismiss, or duplicate a request.
13. Check/review observations preserve external IDs, exact head, states,
    conclusions, and timestamps without inferring pass, approval, acceptance,
    or dispatchability. Changed facts append; identical facts deduplicate.
14. Project Architect-only record/supersede/revoke APIs, immutable Owner
    acceptance evidence, exact revision/digest/currentness, mechanical expiry,
    startup reload, and no-cache exact-ID lookup pass. Missing/wrong/stale/
    expired/revoked/superseded setup; missing provider/reference; inactive/
    stale/revoked/expired or broader/mismatched session; insufficient
    capability; personal identity; unknown/live repository; and missing
    external lock all record the exact blocked mapping before DNS, socket, Git
    remote, or GitHub transport invocation.
15. The public API and source scan prove no merge, force, default-ref update,
    branch-protection/admin, workflow/deploy, secret-management, PR-edit/close,
    review-submit/dismiss, arbitrary command, shell, personal fallback, or
    unapproved-network route exists.
16. Under one active setup record stored by the Project Architect with immutable
    Owner acceptance evidence, a real dedicated non-live GitHub repository
    proves service-identity repository observation, one
    unique feature branch and commit push, one exact draft PR, current check
    observations, one approved reviewer request, and observation of one real
    independent-review result. Repeat and fresh-process replay create no second
    branch/commit/push/PR/reviewer request. The default ref/protection, other
    refs, settings, secrets, deployments, and live repositories remain
    unchanged. Every action has purpose, scoped project, external ID, and
    redacted outcome evidence.
17. During real qualification, revoke or expire the proving credential after a
    successful observation through the separately authorized setup
    administrator (not through M1-03), then prove the next operation visibly
    blocks with no personal fallback or network effect. Restore requires a new
    Project Architect-recorded setup revision with Owner acceptance evidence;
    code does not self-heal authority.
18. Kill/restart at every durable-before-effect/effect-before-result seam for
    branch, commit, push, PR, and reviewer request. Startup expires due setup,
    reloads the exact recorded ID/revision/digest, requires a no-broader fresh
    session, and authoritative observation produces one safe terminal history
    without blindly replaying an uncertain mutation.
19. All Alpha-01, Alpha-02, Alpha-03, M1-01, accepted M1-02, M1-03A/B unit and
    integration tests, JSON/schema consistency if extended, Python compileall,
    exact changed-path review, and repository artifact scan pass from the exact
    final head.

The real GitHub tests are marked `credential-gated`, not skipped proof. They
are absent from ordinary offline execution by explicit selection, report
the external-setup gate unsatisfied rather than pass when the accepted setup is
missing, and must run successfully for M1-03B/integrated M1-03 acceptance. A
mock, recording, fixture, scripted actor, personal repository, or live product
cannot substitute for proof 16 or 17.
The proving branch and draft PR remain as named evidence; M1-03 does not close
the PR or delete the branch as cleanup. Any later cleanup is a separate
Project Architect/Owner-authorized external action.

## M0-D12 quality contracts

### Q1 — Exact local repository effects and default-branch protection

- **Protected outcome:** approved feature-ref/commit/push effects occur once;
  default ref, `HEAD`, worktree, index, configuration, tags, and unrelated refs
  are unchanged.
- **Operating/threat/failure model:** trusted Linux service; dirty/stale repos,
  malformed refs, concurrent processes, non-fast-forward remotes, command
  failure, response loss, and restart are in scope.
- **Exclusions:** hostile same-UID/root mutation after safe acquisition,
  corrupted Git executable/object database, distributed multi-coordinator use,
  and live repositories.
- **Assurance:** practical real-Git integration with CAS/authoritative reread;
  not formal Git verification.
- **Sufficient proof:** tests 3-8 and 18 plus source/API absence proof 15.
- **Implementation boundary:** accepted Git executable, standard library, owned
  files, explicit local/bare-remote repositories; no shell or new Git service.
- **Proportionality ceiling:** normal and injected seams plus two-process
  contention; no adversarial kernel/filesystem lab.
- **Stop/return:** a requirement to force, write default, change config, infer
  identity/policy, or touch live code returns to the Project Architect and,
  where reserved, Owner.

### Q2 — Durable external-action idempotency and reconciliation

- **Protected outcome:** a crash, timeout, duplicate poll, or lost response
  cannot blindly repeat a branch, push, PR, or reviewer-request mutation.
- **Operating/threat/failure model:** one Maestro writer, concurrent callers,
  SQLite restart, process kill, network ambiguity, GitHub eventual observation,
  rate limiting, and stale source facts.
- **Exclusions:** GitHub outage beyond the bounded qualification window,
  malicious upstream falsification, multi-region exactly-once guarantees, and
  automatic remediation.
- **Assurance:** durable intent plus conservative authoritative reconciliation;
  unknown remains blocked rather than claimed exactly-once.
- **Sufficient proof:** tests 3, 5, 7-8, 10-12, 14, and 18 prove the exact
  pre-intent/blocked/effect phases, one result shape, one action history, and no
  repeated unknown mutation.
- **Implementation boundary:** schema 5, accepted M1-02 APIs, Git, injected
  GitHub transport, and owned modules.
- **Proportionality ceiling:** deterministic seam injection, real process
  restart, and one real non-live replay; no distributed transaction system.
- **Stop/return:** inability to identify an authoritative post-effect fact or
  a demanded automatic retry from unknown returns to the Project Architect.

### Q3 — Least-privilege credential and redaction boundary

- **Protected outcome:** only an Owner-approved repository-scoped service
  capability from the exact active Project Architect-recorded setup revision
  reaches the exact non-live target, and the runtime session is never broader;
  no secret value survives in SQLite, output, logs, errors, evidence, handoff,
  URL, or argv.
- **Operating/threat/failure model:** missing/stale/revoked/expired credentials,
  over-broad or personal identities, malformed carriers, raw error responses,
  representative token/key/header/URL carriers, and caller mistakes.
- **Exclusions:** provider compromise, hostile root/same-UID memory inspection,
  side-channel analysis, GitHub compromise, and comprehensive arbitrary-secret
  semantic detection.
- **Assurance:** closed structural carriers, runtime injection, allowlisted
  capabilities, and redaction receipts; no claim of memory-zeroization.
- **Sufficient proof:** tests 9-10, 14, 16-18, exact setup lifecycle/restart
  proof, and DB/log byte scans.
- **Implementation boundary:** Project Architect-owned durable setup API,
  injected exact-ID lookup, provider-neutral opaque session provider, and the
  separately selected provider at qualification; none is provisioned here.
- **Proportionality ceiling:** enumerate all new carriers and representative
  high-risk secret shapes; M3 owns worker prompt/trace scanning.
- **Stop/return:** raw-secret API, personal fallback, new provider, expanded
  scope, or stronger adversarial guarantee returns through the Project
  Architect to the Owner.

### Q4 — GitHub authority fidelity and no policy inference

- **Protected outcome:** observed PR/check/review facts retain exact external
  IDs/head/status; the adapter never turns them into approval, acceptance,
  merge, dispatch, or changed project policy.
- **Operating/threat/failure model:** stale head/base, multiple PR candidates,
  pagination, reordered/duplicate observations, mixed review states, missing
  checks, and eventual consistency.
- **Exclusions:** M4-04 review-coverage judgment, check-policy aggregation,
  repository registration, branch protection administration, and merge.
- **Assurance:** closed factual projections with authoritative re-observation.
- **Sufficient proof:** tests 10-13 and 16; mismatches remain typed conflicts.
- **Implementation boundary:** approved binding, official GitHub API transport,
  schema 5 observations, no editable duplicate backlog.
- **Proportionality ceiling:** contracted actions and representative pagination;
  not every GitHub feature/object.
- **Stop/return:** missing exact head/object mapping, requested approval logic,
  merge, or inferred authority returns to the Project Architect.

### Q5 — M0-D11 and project-path containment

- **Protected outcome:** Maestro runtime artifacts remain physically beneath
  repository `var/`; project effects remain inside the exact validated non-live
  worktree/remote and approved paths.
- **Operating/threat/failure model:** forged configs, outside/symlink/swapped
  runtime components, wrong project path, parent/sibling traversal, arbitrary
  remotes, and caller mistakes at every new entry route.
- **Exclusions:** hostile concurrent same-UID/root replacement after acquisition,
  mount/kernel compromise, provider compromise, and live repositories.
- **Assurance:** accepted M0-D11 trusted-local containment plus explicit project
  authority validation; these are distinct boundaries.
- **Sufficient proof:** tests 2-4, 6, 10, and 14 parameterize every new store,
  clock, setup/session provider, adapter constructor, factory, action,
  observation, and reconciliation route.
- **Implementation boundary:** accepted `RuntimeConfig`,
  `OperationalStateStore`, directory-FD routines, Git worktree validation, and
  owned code only.
- **Proportionality ceiling:** all new entry routes and representative race seam;
  no stronger host sandbox.
- **Stop/return:** an alternate store/path constructor or unbound project/remote
  returns to the Project Architect before implementation.

### Q6 — Real non-live external qualification

- **Protected outcome:** the actual adapter, actual service identity, and actual
  GitHub repository perform and reconcile the bounded M1-03 actions without a
  live-project, personal-credential, default-branch, merge, or protection
  effect.
- **Operating/threat/failure model:** approved dedicated proving repository,
  protected default branch, least-privilege identity, real push/API/check/
  reviewer records, credential expiry/revocation, replay, and process restart.
- **Exclusions:** production/live repositories, repository creation, billing or
  organization administration, merge/deploy, webhooks, and full E2E actors.
- **Assurance:** one attended real proving run with independently inspectable Git
  and GitHub evidence; offline doubles do not satisfy it.
- **Sufficient proof:** tests 16-17 plus exact external object IDs, before/after
  default/protection/ref inventory, and redacted action evidence.
- **Implementation boundary:** reviewed B code at an exact head, one active
  Project Architect-recorded setup ID/revision/digest with immutable Owner
  acceptance evidence, one dedicated non-live repo, service identity, and
  approved reviewer.
- **Proportionality ceiling:** one unique branch/commit/draft PR/check/reviewer
  chain and replay/credential-loss observations; no broad GitHub certification.
- **Stop/return:** missing or expanded setup, unexpected cost/scope, live target,
  inadequate isolation, or required destructive cleanup returns through the
  Project Architect to the Owner.

## Serial implementation slices

The slices divide implementation and review; they do not change the umbrella
outcome or downstream gate. Neither slice is independently a downstream
release. Only routine Project Architect acceptance of the integrated B result,
including real external qualification, creates accepted M1-03.

### M1-03A — Offline repository actions and durable recovery

- **Stable ID:** `MAESTRO-M1-03A-LOCAL-GIT-RECOVERY`.
- **Dependency:** `hard:
  MAESTRO-M1-02C-CUMULATIVE-INTEGRATION-PROOF @ ProjectArchitectAccepted` at an
  exact unresolved head.
- **Branch/worktree/base:**
  `implementation/m1-03a-local-git-recovery` at
  `/home/jeremy/Development/Maestro-m1-03a-implementation`, created only from
  the exact accepted M1-02C head after packet reconciliation.
- **Outcome:** additive schema-4-to-5 setup-authority/action/observation ledger,
  Project Architect-owned setup record API and injected lookup, one clock/
  result contract, closed payloads, local observe/branch/commit/push adapter,
  local bare-remote proof, and restart/concurrency reconciliation.
- **Non-goals:** GitHub HTTP/API code, credential selection/injection,
  networked remote, setup/credential provisioning or activation, project
  create/register, or any umbrella exclusion.
- **Owned paths:** `services/maestro/maestro/storage.py` only for additive
  migration/factory integration;
  `services/maestro/maestro/operational_state.py` only for registered safe
  payload/event integration;
  `services/maestro/maestro/recovery.py` only for setup-expiry and M1-03 action
  startup ordering;
  `services/maestro/maestro/git_repository.py` only for preserving/extending
  shared Git primitives;
  `services/maestro/maestro/repository_adapter.py`;
  `tests/m1_01/test_project_authority_storage.py` only for the exact cumulative
  schema-history/health expectation from 4 to 5, preserving all other proof;
  `tests/m1_03/test_action_storage.py`;
  `tests/m1_03/test_repository_adapter.py`; and
  `tests/m1_03/test_repository_recovery.py`.
- **Proof group:** proofs 1-10, proof 14 for durable setup API/lookup and
  no-network routes, proof 15, proof 18 for local/startup recovery, and all
  prior regressions/compileall.
- **Locks/envelope/routes:** `shared:sqlite-schema`,
  `file:services-maestro-storage`, `path:maestro-operational-state`,
  `path:maestro-recovery`, `path:maestro-git-adapter`, and `path:tests-m1-03`;
  one 150-minute attempt and at most one correction; Developer -> Integration
  validate-only unless assembly -> fresh exact-range independent review ->
  routine Project Architect A acceptance. A acceptance opens only B code.

### M1-03B — Credential-gated non-live GitHub integration

- **Stable ID:** `MAESTRO-M1-03B-NONLIVE-GITHUB-INTEGRATION`.
- **Dependency:** `hard: MAESTRO-M1-03A-LOCAL-GIT-RECOVERY @
  ProjectArchitectAccepted`; real qualification also requires `hard:
  M1-03-EXTERNAL-SETUP-AUTHORITY @ ProjectArchitectRecorded` with immutable
  Owner acceptance evidence for the reserved external facts.
- **Branch/worktree/base:**
  `implementation/m1-03b-nonlive-github-integration` at
  `/home/jeremy/Development/Maestro-m1-03b-implementation`, created only from
  the exact accepted A head. External setup changes no code base.
- **Outcome:** provider-neutral GitHub transport and session provider, exact
  active-setup/session comparison, PR/reviewer/check/review operations,
  structural credential/redaction boundary, offline contract proof, then real
  dedicated non-live qualification and cumulative M1-03 evidence.
- **Non-goals:** selecting/provisioning credentials or repositories, accepting
  costs/scopes, merge/default-write/protection/admin, webhooks, live projects,
  or any umbrella exclusion.
- **Owned paths:** `services/maestro/maestro/repository_adapter.py` only for B
  integration; `services/maestro/maestro/github_adapter.py`;
  `tests/m1_03/test_github_adapter.py`;
  `tests/m1_03/test_nonlive_github_integration.py`;
  `tests/m1_03/test_cumulative_contract.py`;
  `docs/architecture/m1-03-real-repository-and-github-adapter.md`; and
  `docs/operations/m1-03-real-repository-and-github-adapter.md`.
- **Proof group:** proofs 9-19 and all A/prior regressions. Offline code proof
  precedes external activation. The credential-gated suite and proofs 16-17
  are mandatory before final acceptance.
- **Locks/envelope/routes:** `path:maestro-repository-adapter`,
  `path:maestro-github-adapter`, `path:tests-m1-03`,
  `file:m1-03-architecture-doc`, and `file:m1-03-operations-doc`; one
  150-minute code attempt and at most one correction. The attended 90-minute
  qualification additionally acquires
  `external:owner-approved-m1-03-nonlive-github-repository` and
  `finite:owner-approved-m1-03-credential-session`. Developer -> Integration
  cumulative validate/assemble -> fresh exact-range independent review ->
  Project Architect records the Owner-evidenced active setup -> attended proof
  -> Integration validates exact final head/evidence -> reviewer confirms
  coverage/evidence -> routine Project Architect integrated acceptance.

## Status, stop, handoff, and acceptance

The Coordinator reports `DependencyBlocked` while M1-02C is unaccepted,
`PendingDecisionFidelity` until this planning range is approved,
runtime packet state `Waiting` with an open `ExternalSetup` gate when reviewed
B code lacks an active Project Architect-recorded setup ID/revision/digest with
Owner evidence, and the exact typed failure/action state during qualification.
Waiting is not failure and does not authorize polling more frequently,
credential substitution, or another action.

Stop immediately on dirty/wrong base, missing lock, changed accepted M1-02 API,
outside-path diff, raw secret carrier, personal identity, unknown/live target,
default-ref or force request, ambiguous prior effect, unexpected permission or
cost, protected-branch conflict, merge/deploy request, or evidence that a
quality contract is infeasible. Preserve the exact redacted facts. Routine
implementation defects follow Integration/review and the one correction route;
architecture/public-contract or reserved choices return through the Project
Architect as stated above.

Independent implementation review covers A base/head, B base/head, any
correction-only range, and cumulative accepted M1-02C-through-final-B coverage.
Integration PASS alone does not accept a slice. The Project Architect accepts
routine A and integrated B results. Only integrated B acceptance after the real
credential-gated proof satisfies
`MAESTRO-M1-03-REAL-REPOSITORY-GITHUB-ADAPTER @ ProjectArchitectAccepted` and
may unlock M1-04, M1-05, M3-02, or M4-04 dependencies. No M1-03 role merges,
deploys, accesses a live project, or starts downstream work.

## Explicit exclusions

- USB backup/restore, retention deletion, service installation, or host reboot;
- public `maestro project create/register`, binding activation, or registration;
- worktree preparation/permission enforcement and worker dispatch (M3);
- graph scheduling/control loop, Atlas, Slack, webhooks, workers, or Murphy;
- repository/GitHub provisioning, credential/provider selection, personal
  authentication, organization or billing administration;
- PR update/close, review submission/approval/dismissal, issue mutation,
  automatic merge, default-branch write, force push, protection bypass,
  deployment, or production/live-project access; and
- synthetic or fixture evidence as a substitute for the real dedicated
  non-live GitHub qualification.
