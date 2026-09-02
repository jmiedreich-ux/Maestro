# M1-01 — Load and Record a Real Project Authority Bundle

**Status:** Corrected draft for targeted Decision Fidelity Review; not yet released
**Packet ID:** `maestro-m1-01-real-project-authority-loader`
**Graph node:** `MAESTRO-M1-01-REAL-PROJECT-AUTHORITY-LOADER`
**Graph revision:** `maestro-m1-m4-real-r1`
**Planning authority:** `c6eb7d83082a1ac75eb9b7798b6f2bdce74341c4`
**Implementation base:** `c6eb7d83082a1ac75eb9b7798b6f2bdce74341c4`
**Expected implementation branch:** `implementation/m1-01-real-project-authority-loader`
**Expected worktree:** `/home/jeremy/Development/Maestro-m1-01-implementation`
**Decision authority:** [M0-D02](../decisions/m0-d02-project-registration.md),
[M0-D06](../decisions/m0-d06-project-manifest-contract.md), and
[M0-D15](../decisions/m0-d15-real-m1-m4-implementation-path.md)
**Roadmap authority:** `sources/planning/maestro-alpha-1-handoff.md`, M1
**Implementation role:** dedicated Maestro Developer
**Execution route:** cloud collaboration worktree / dedicated Maestro
Developer / `codex-cloud-maestro-developer` / session-inherited Codex model;
factual model/runtime identity is recorded at dispatch preflight
**Role/SOP versions:** `docs/agents/maestro-developer.md`,
`docs/agents/coding-agent-sop.md`, `docs/agents/integration-agent.md`, and
`docs/agents/independent-review-agent.md` at planning authority
`c6eb7d83082a1ac75eb9b7798b6f2bdce74341c4`; bootstrap Coordinator authority
is M0-D15 plus `sources/planning/current-handoff.md` at the same revision
**Bootstrap coordinator:** Maestro Coordinator
**Decision Fidelity route:** fresh independent Decision Fidelity Reviewer
**Integration route:** Integration Agent, `validate-only` unless integration
changes are required
**Independent implementation-review route:** fresh Independent Implementation
Reviewer
**Routine acceptance authority:** Project Architect under M0-D15

## Exact dispatch controls

- Use one isolated worktree at the exact implementation base and the expected
  branch above. Do not share it with another writer.
- Acquire `path:maestro-registration-core`, `shared:sqlite-schema`, and
  `file:services-maestro-pyproject` before implementation. No parallel packet
  may write these domains until handoff or cancellation releases the locks.
- One initial Developer attempt is allowed. One M0-D05 correction attempt is
  available only after committed in-scope work fails a named gate. There is no
  automatic retry; infrastructure failure or a new failure class stops to the
  Coordinator and Project Architect respectively.
- The implementation attempt has a 90-minute ceiling. After 10 minutes with no
  visible update, the Coordinator may request one bounded factual status; later
  requests must be at least 10 minutes apart and allow a 2-minute response
  window. No role invents an ETA.
- Preflight requires at least 32,768 available context tokens with an 8,192
  token output/handoff reserve. Record the actual model, runtime, context
  capacity, and available usage counters. Checkpoint at 16,384 remaining,
  prepare handoff at 12,288, and stop new implementation work at 8,192.
  Unsupported counters are recorded as `unavailable`; do not scrape provider
  state, convert weekly quotas, or treat an unavailable counter as a budget.
- Handoff must state the exact base and head, changed paths, commands and full
  outcomes, repository non-mutation evidence, migration/rollback/idempotency/
  restart/concurrency evidence, model/runtime/context and honest usage facts,
  released locks, and every known gap or untested item.

## Outcome

Add the production foundation shared by `maestro project create` and
`maestro project register`.

Given a local non-live Git repository, an exact commit, an expected repository
identity, and a checked-in `maestro.project.yaml`, Maestro reads the manifest
and its declared authority files from Git objects at that exact commit,
validates the complete M0-D06 binding, records one candidate registration run
atomically, and reports every missing or conflicting binding fact without
guessing.

This packet does not expose `project create` or `project register`, change the
project repository, open a PR, run declared project checks, dispatch an agent,
or mark a project registered.

## Existing foundations to preserve

- `config.py` retains the accepted M0-D11 bounded runtime-directory contract.
- `storage.py` retains WAL, foreign keys, short transactions, canonical JSON,
  and all Alpha-01 through Alpha-03 tables and behavior.
- Alpha-03's seven binding areas inform the production manifest, but
  `synthetic_discovery.py` is not reused as the production loader. Its accepted
  malformed authority-array limitation must not enter M1.
- `maestro health` and synthetic `maestro run-packet` remain behaviorally
  unchanged and continue to pass their regression suites.

## Exact production manifest contract

The project-owned file is named `maestro.project.yaml`. It is UTF-8 and uses a
strict YAML subset: one mapping document, string keys only, no duplicate keys,
aliases, anchors, merge keys, custom tags, or additional fields. Parsing uses
`PyYAML >=6.0.2,<7` through a custom `SafeLoader` that rejects duplicate keys
and the prohibited YAML features before constructing application values.

The normalized manifest has exactly this shape:

```yaml
schema_version: 1
identity:
  project_id: example-project
  name: Example Project
  repository: owner/example-project
  default_branch: main
  adapter_version: maestro-project-v1
  process_version: maestro-m1
authority:
  architecture_paths:
    - docs/architecture/project-foundation.md
  plan_paths:
    - docs/planning/work-graph.yaml
  work_graph_path: docs/planning/work-graph.yaml
  handoff_path: ai/handoffs/current.md
  rules_sop_path: AGENTS.md
  task_issue_convention: github-issues
delivery:
  branch_policy: feature-branch
  pull_request_policy: draft-required
  merge_policy: no-automatic-merge
  acceptance_authority: project-architect
  deployment_policy: none
  rollback_policy: revert-commit
verification:
  build_commands: []
  test_commands: []
  integration_commands: []
  ui_qa_commands: []
  evidence_rules: record-command-output
  untested_handling: explicit-untested-with-impact
routing:
  specialist_overlays: []
  worker_routes: []
  integration_route: integration-agent
  independent_reviewer_route: independent-implementation-reviewer
  qa_murphy_policy: disabled
operations:
  environment_references: []
  secret_references: []
  resource_locks: []
  notification_policy: local-durable-only
exceptions:
  disposition: none
  items: []
```

### Field rules

- Mapping keys and scalar strings are exact after surrounding whitespace is
  rejected; the loader does not silently trim a value into validity.
- `schema_version` is the integer `1`.
- `project_id` matches `[a-z][a-z0-9-]{2,63}`.
- All other required scalar fields are non-empty strings of at most 512 UTF-8
  bytes. `name` may contain spaces; repository/path/policy fields may not
  contain control characters.
- Every list is an ordered list of unique non-empty strings. Empty lists are
  allowed only where shown as route/command/reference declarations; they mean
  explicitly none, not missing.
- `architecture_paths` and `plan_paths` each contain at least one path.
  `work_graph_path` must also occur in `plan_paths`.
- All authority paths are repository-relative POSIX paths. Absolute paths,
  empty/dot components, `..`, backslashes, NUL/control characters, `.git`, and
  duplicate normalized paths are rejected.
- `repository` is the caller-supplied expected repository identity in
  `owner/name` form. Mismatch is a conflict, never a default.
- `acceptance_authority` is `project-architect` for the M1–M4 proving project.
  A manifest requiring `owner` is valid only when the candidate explicitly
  records the corresponding M0-D15 reserved policy; this packet records that
  as a blocked material return and does not resolve it.
- `exceptions.disposition` is `none` or `declared`. `none` requires an empty
  `items`; `declared` requires at least one unique item.
- `secret_references` stores reference identifiers only. Each list member must
  match `[A-Z][A-Z0-9_]{2,127}`; for example `GITHUB_APP_PRIVATE_KEY` and
  `SLACK_BOT_TOKEN` are valid identifiers, not secret values. Mappings,
  multiline strings, control characters, values over 128 characters, and
  strings outside that grammar are rejected. The closed schema rejects
  `secret_values` and every other unknown field. Representative credential
  payloads beginning `ghp_` or `xoxb-`, and PEM material beginning
  `-----BEGIN`, are therefore rejected structurally. Words such as `TOKEN`,
  `PASSWORD`, or `KEY` inside a valid reference identifier are not themselves
  evidence of secret material.

The implementation adds
`docs/schemas/maestro-project-v1.schema.json` as the canonical normalized JSON
shape. The Python validator and schema must agree; a consistency test validates
all accepted/rejected examples through both carriers where applicable.

## Exact read-only Git contract

Add an internal entry point:

```python
ProjectAuthorityLoader.load(
    repository_path: Path,
    source_revision: str,
    expected_repository: str,
    manifest_path: str = "maestro.project.yaml",
) -> ProjectAuthorityLoadResult
```

The loader:

1. verifies `repository_path` is an existing Git worktree and never writes it;
2. requires `source_revision` to be a full 40-hex object ID, resolves it to
   exactly one commit object, rejects symbolic, abbreviated, ambiguous,
   missing, malformed, tag, tree, and blob inputs, and records its lowercase
   full SHA;
3. reads the manifest and every authority path from that commit's Git tree,
   not from the index or mutable working tree;
4. verifies the declared default-branch ref exists locally and contains the
   source commit at observation time;
5. rejects submodules, Git symlink entries, missing blobs, non-blob authority
   entries, oversized files above 2 MiB each, and a total authority payload
   above 16 MiB before application parsing;
6. records each authority path's Git object ID, SHA-256 content digest, and
   byte length without copying the complete authority content into SQLite;
7. returns a closed structured result with exact source commit, normalized
   manifest, inventory, authority descriptors, and `Reviewable` or `Blocked`;
8. leaves repository files, refs, index, configuration, and worktree state
   unchanged.

Git is invoked only with argument arrays and read-only commands. No shell,
checkout, reset, clean, fetch, commit, branch, worktree creation, remote write,
credential lookup, or network operation is permitted.

## Inventory and result contract

The result contains exactly:

```text
request_id
repository_path
expected_repository
source_revision
source_commit
manifest_path
manifest_digest
normalized_manifest
authority_files[]: path, git_object_id, sha256, byte_length
facts[]: dotted_path, status, observed_value|observed_values|reason
summary: confirmed, missing, conflicting
disposition: Reviewable|Blocked
```

Every required manifest leaf and authority path produces one fact. A missing
leaf/path is `missing`. A mismatch between expected repository/Git observation
and the manifest is `conflicting`. Invalid YAML, invalid types, prohibited
paths/entries, or secret-bearing fields are malformed input and fail before
database mutation. No fact is defaulted.

## Durable storage contract

Advance the database through one ordered migration without dropping or
rewriting Alpha records. Add:

### `projects`

```text
project_id PRIMARY KEY
repository_identity UNIQUE NOT NULL
default_branch NOT NULL
adapter_version NOT NULL
process_version NOT NULL
registration_state CHECK Candidate|Registered|Blocked
active_binding_revision NULL
created_at NOT NULL
updated_at NOT NULL
```

M1-01 may create only `Candidate`; it cannot create `Registered` or an active
binding revision.

### `project_registration_runs`

```text
request_id PRIMARY KEY
idempotency_key UNIQUE NOT NULL
mode CHECK AuthorityLoad
project_id NULL REFERENCES projects
repository_identity NOT NULL
repository_path NOT NULL
source_commit NOT NULL
manifest_path NOT NULL
manifest_digest NOT NULL
inventory_json NOT NULL
candidate_binding_json NULL
authority_files_json NOT NULL
result CHECK Reviewable|Blocked
created_at NOT NULL
```

### `events`

```text
event_id INTEGER PRIMARY KEY
idempotency_key UNIQUE NOT NULL
entity_type NOT NULL
entity_id NOT NULL
event_type NOT NULL
before_json NOT NULL
after_json NOT NULL
reason NOT NULL
created_at NOT NULL
```

Persistence uses `BEGIN IMMEDIATE` and one short transaction. A reviewable
load inserts the candidate project, registration run, and event atomically. A
well-formed missing/conflicting load inserts a blocked registration run and
event but no active/candidate project. Malformed input inserts nothing.

The idempotency key is derived from the normalized repository identity, exact
source commit, manifest path, and manifest digest. Repeating an identical
request returns the original durable result without a second project, run, or
event. Reusing a request ID or idempotency key for different facts is rejected.

## Owned implementation paths

```text
docs/architecture/m1-01-real-project-authority-loader.md
docs/operations/m1-01-real-project-authority-loader.md
docs/schemas/maestro-project-v1.schema.json
services/maestro/pyproject.toml
services/maestro/maestro/git_repository.py
services/maestro/maestro/project_authority.py
services/maestro/maestro/project_manifest.py
services/maestro/maestro/storage.py
tests/m1_01/**
```

No other path may change. In particular, do not change `cli.py`, synthetic
packet/discovery behavior, role/planning authority, root tooling, or any live
project repository.

## Required implementation sequence

1. Add the strict manifest schema/parser and its isolated tests.
2. Add the read-only exact-commit Git object reader and mutation proof.
3. Add the production authority inventory/result model.
4. Add the ordered migration and atomic persistence methods.
5. Add the integrated real-temporary-repository tests and operations docs.
6. Run every named gate and hand the exact commit/evidence to Integration.

The Developer must stop if the existing schema cannot be migrated without data
loss, the Git boundary requires a write/network operation, a manifest choice is
not defined above, or an owned path outside this packet is required.

## Required gates and sufficient proof

From `services/maestro/`:

```text
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m compileall -q maestro
```

The M1-01 suite must prove:

1. a complete real temporary Git repository loads from its exact commit and
   records one candidate/run/event;
2. later committed, staged, and uncommitted changes cannot alter the pinned
   result;
3. every required missing manifest leaf reports its exact dotted path;
4. missing authority blobs block loading;
5. repository identity and default-branch containment conflicts block loading;
6. absolute/traversal/`.git` paths, Git symlinks, submodules, non-blobs, size
   overflow, unknown keys, duplicate YAML keys, aliases/anchors/merge/tags,
   invalid types, duplicate values, and malformed exceptions are rejected
   before mutation;
7. valid secret-reference identifiers are accepted; mappings, multiline or
   control-bearing strings, overlength/grammar-invalid identifiers,
   `secret_values`, unknown fields, and representative GitHub, Slack, and PEM
   credential payloads are rejected before mutation;
8. empty `architecture_paths` or `plan_paths`, including the Alpha-03 accepted
   malformed-array case, is rejected before mutation;
9. repeated identical invocation returns one durable result and event;
10. conflicting request/idempotency reuse is rejected;
11. a failed migration rolls back without changing schema version or records;
12. an existing schema-version-2 database upgrades without losing Alpha rows;
13. repository files, refs, index, config, and status are byte-for-byte or
    semantically unchanged after success and every failure class; and
14. all Alpha regression suites remain green.
15. missing, ambiguous, invalid, and non-commit `source_revision` inputs are
    rejected before mutation;
16. an injected failure between candidate, run, and event writes rolls the
    complete transaction back;
17. closing and reopening storage after a successful commit returns the exact
    original durable result without another project, run, or event; and
18. two concurrent identical loads produce one candidate, run, and event and
    both callers observe the same durable result.

## Complete M0-D12 quality contracts

### Q1 — Exact-commit, read-only repository observation

- **Protected outcome:** authority is loaded from the requested immutable Git
  commit without changing or contacting the project repository.
- **Operating/failure model:** one trusted local Linux service reads a local
  non-live Git worktree; mutable working-tree/index/ref state, invalid commits,
  symlinks, submodules, missing/non-blob entries, path escape, and payload size
  exhaustion are in scope.
- **Exclusions:** hostile same-UID/root mutation after an already opened Git
  object, malicious Git executable replacement, network/remote consistency,
  Git hosting credentials, and live product repositories.
- **Assurance level:** deterministic read-only Git object access at one full
  commit SHA with before/after repository mutation evidence.
- **Sufficient proof:** required tests 1, 2, 4, 5, 6, 13, and 15 pass using real
  temporary Git repositories and actual Git commands.
- **Implementation boundary:** standard library plus argument-array Git
  subprocesses; no shell, Git library, checkout, network, or repository write.
- **Proportionality ceiling:** one local repository, one manifest, one commit,
  at most 2 MiB per authority blob and 16 MiB total.
- **Stop/return:** any required write/network action, live-project access,
  stronger containment, or ambiguous Git fact returns to the Project Architect
  with no database mutation.

### Q2 — Complete, strict, and honest authority binding

- **Protected outcome:** no candidate is reviewable when a required binding or
  authority fact is missing, conflicting, malformed, proposed-only, or filled
  by an unstated default.
- **Operating/failure model:** duplicate/unknown YAML fields, wrong types,
  aliases/tags, empty required arrays, invalid paths, conflicting
  repository/branch facts, malformed exceptions, and secret-bearing input are
  in scope.
- **Exclusions:** semantic interpretation of arbitrary architecture prose,
  product correctness, graph scheduling, binding PR approval, project check
  execution, and final registration.
- **Assurance level:** closed schema and deterministic leaf/path inventory with
  explicit confirmed/missing/conflicting disposition.
- **Sufficient proof:** required tests 3 through 8 and schema/parser consistency
  pass; every missing/conflict path and count matches expected evidence.
- **Implementation boundary:** PyYAML custom safe loader, JSON Schema carrier,
  typed Python validation, and no generic workflow/schema framework.
- **Proportionality ceiling:** manifest version 1 and the seven M0-D06 areas
  only; no compatibility aliases or inferred legacy layouts.
- **Stop/return:** any field/meaning absent from this packet returns to the
  Project Architect; the Developer does not invent or default it.

### Q3 — Durable idempotent candidate persistence

- **Protected outcome:** one authority-load request creates at most one
  consistent registration result/event and never loses existing Alpha data.
- **Operating/failure model:** schema-version-2 upgrade, repeated requests,
  conflicting key reuse, transaction failure, restart after commit, and
  concurrent local claims are in scope.
- **Exclusions:** multi-coordinator consensus, distributed databases, backup/
  USB restore, long-term retention, and later registration/queue transitions.
- **Assurance level:** ordered migration, foreign-key/unique/check constraints,
  `BEGIN IMMEDIATE`, canonical JSON, and transactionally atomic rows/events.
- **Sufficient proof:** required tests 1, 9 through 12, and 16 through 18 pass,
  including an upgrade database containing representative Alpha rows,
  transaction rollback, reopen-after-commit, and concurrent identical loads.
- **Implementation boundary:** additive SQLite schema and service-owned writer
  methods; no ORM, migration framework, database split, or direct client.
- **Proportionality ceiling:** three production tables and the minimal methods
  required by this packet.
- **Stop/return:** data loss, non-additive migration, ambiguous current version,
  or inability to establish one idempotent result rolls back and returns to the
  Project Architect.

### Q4 — Registration and external-side-effect confinement

- **Protected outcome:** M1-01 cannot claim registration, alter a project,
  dispatch work, contact an external system, or cross the delegated approval
  boundary.
- **Operating/failure model:** accidental CLI exposure, active-binding write,
  repository mutation, Git remote access, credential lookup, worker launch,
  notification, or `Registered` transition is in scope.
- **Exclusions:** later M1 `project create/register`, binding/bootstrap PR,
  GitHub adapter, declared-check dry run, Atlas, worker execution, and default-
  branch merge.
- **Assurance level:** no public command or implementation path for the
  excluded effects, plus negative tests and complete changed-path review.
- **Sufficient proof:** required tests 13 and 14 pass; review confirms no CLI,
  active binding, `Registered`, network, credential, worker, PR, or merge path.
- **Implementation boundary:** internal loader/result/storage APIs and owned
  docs/tests only.
- **Proportionality ceiling:** one candidate authority-load operation; no partial
  onboarding orchestration.
- **Stop/return:** any need for external credentials, repository write, active
  registration, worker dispatch, broader scope, or reserved material choice
  returns to the Project Architect before implementation continues.

## Handoff and acceptance

The Developer hands one exact commit with changed paths, complete command
output, repository non-mutation evidence, migration evidence, and known gaps to
Integration. Integration uses `validate-only` when it changes no code; any
Integration-authored code requires a different independent reviewer.

Independent Implementation Review checks the complete exact base/head range.
One M0-D05 targeted correction is available only for committed in-scope work
that fails a named gate. A new failure class, missing contract, scope change,
or exhausted correction returns to the Project Architect.

After independent approval and complete final-head coverage, routine M1-01
acceptance belongs to the Project Architect under M0-D15. Approval releases
M1-02 planning; it does not mark a project registered, activate credentials,
merge a default branch, dispatch a real project worker, or start a live-product
test.
