# M1-01 Current-Master Integration

**Slice ID:** `MB-SLICE-M1-01-INTEGRATION-01`
**Status:** `PendingDecisionFidelity`
**Planning and implementation base:**
`b47592cfa417fd39daddef46ff691697969b51f0`
**Accepted behavior source:**
`56b4dfb5e4d4bef860616cde93d172affb0e4210`
**Outcome authority:** the Owner's current M1 recovery direction; the current
development status and both current handoffs at the planning base; the
[Bootstrap Convergence Policy](../bootstrap-convergence-policy.md); the
[Master Plan](../maestro-master-plan.md); [M0-D02](../decisions/m0-d02-project-registration.md),
[M0-D05](../decisions/m0-d05-rework-review-and-escalation.md),
[M0-D06](../decisions/m0-d06-project-manifest-contract.md), and
[M0-D12](../decisions/m0-d12-bounded-quality-contracts.md).
**Recovery evidence only:** the M1-01 and M1-01R packet records and accepted
M1-M4 direction present in the local Git history through the accepted behavior
source. They explain the accepted result but are not files to import.

## Durable slice status

This table is the slice's sole durable bootstrap status carrier. Assignments,
chat, branches, and stale process observations are not status.

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-01-INTEGRATION-01` |
| `phase` | `MergeReady` |
| `current_actor` | `None` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `1` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["digest:9ec223e90df8324e2ff7ef30b6537f0dbd55f64439dfe8b887e15471c89bbc3b", "execution:/root/maestro_developer:2026-09-04T01:22:07Z", "git:05b11b3b66243ed05c2aa7b7b35e82cf75502108..cf36927243e782e2b4adc3e36ab696087cff5697", "git:4e213b10d2bfd709e43a9073c41cc986e78a0fcd..56b4dfb5e4d4bef860616cde93d172affb0e4210", "git:b47592cfa417fd39daddef46ff691697969b51f0", "git:source-accepted:56b4dfb5e4d4bef860616cde93d172affb0e4210", "readiness:671a5ccedf40d389cc13f2fb30b38dca2e162140b73bf04ade674d29c89828b1", "readiness:b9f48a997f6294208c9bbb7a2c029a5047bbd2d8812c72fb8b06f7ce1ba03858", "review:M1-01-INT-DFR-01-APPROVE", "review:M1-01-INT-IIR-01-APPROVE"]` |

The allowed phases are `PendingDecisionFidelity`, `PlanningCorrection`,
`Frozen`, `Running`, `ImplementationReview`, `ImplementationCorrection`,
`TargetedImplementationVerification`, `MergeReady`, and `Terminal`.
`terminal_state` is `null` unless the phase is `Terminal`, when it is exactly
`Merged`, `Returned`, `Cancelled`, or `OwnerStopped`. Counts never reset.
Only repository commits outside the reviewed implementation range may update
this table after the contract freezes.

## Project Architect selection decision

Rematerializing M1-01 is the smallest executable post-readiness roadmap
behavior.

- Current master contains Alpha-01 through Alpha-03 and the review-readiness
  gate, but no production project-authority loader.
- M1-01 is the first M1 behavior and is a dependency of accepted M1-02A
  evidence. Later operational-state work cannot be integrated first.
- Both local M1-01 evidence worktrees are clean. The accepted source passes
  Alpha-01 (11), Alpha-02 (7), Alpha-03 (56), and M1-01 (27) tests under its
  declared dependency ranges.
- None of the ten executable M1-01 source/test paths changed on current master
  after their common base. Exact-blob rematerialization therefore requires no
  product redesign or conflict resolution.

This is M1 recovery and continuation. It does not close M1, select M1-02 work,
or change the terminal M1-02B result.

## One executable outcome

Add the accepted internal M1-01 authority-loading foundation to current master.
Given a local non-live Git repository, a full commit SHA, an expected repository
identity, and a checked-in `maestro.project.yaml`, the internal loader:

1. reads the manifest and declared authority files from Git objects at that
   exact commit without mutating or contacting the repository;
2. strictly validates the accepted manifest, including the closed
   `project-architect|owner` acceptance-authority set;
3. reports missing and conflicting facts without guessing; and
4. atomically records one reviewable candidate or one blocked registration run
   with idempotent SQLite persistence.

It does not expose `maestro project create` or `maestro project register`, mark
a project registered, activate a binding, dispatch work, contact GitHub or any
external service, access a live project, merge, deploy, or authorize successor
work.

## Exact implementation boundary

The Maestro Developer may change only these paths:

```text
docs/schemas/maestro-project-v1.schema.json
services/maestro/pyproject.toml
services/maestro/maestro/git_repository.py
services/maestro/maestro/project_authority.py
services/maestro/maestro/project_manifest.py
services/maestro/maestro/storage.py
tests/m1_01/support.py
tests/m1_01/test_project_authority_loader.py
tests/m1_01/test_project_authority_storage.py
tests/m1_01/test_project_manifest.py
```

Each final path must have the exact Git blob recorded at the accepted source:

| Path | Required Git blob |
|---|---|
| `docs/schemas/maestro-project-v1.schema.json` | `30091e54efcf338121f406dd2617ea3ebe070e42` |
| `services/maestro/pyproject.toml` | `e33062b2836fcc7a64f817fe725d115534ae7bf1` |
| `services/maestro/maestro/git_repository.py` | `9e2be2c578073649d9def9640f958aefaa9fe782` |
| `services/maestro/maestro/project_authority.py` | `b77fcfc003784dc2288cd9d9c3f93e30c266ec18` |
| `services/maestro/maestro/project_manifest.py` | `5b8834abd82a90569c7c8699e6362c059887c02a` |
| `services/maestro/maestro/storage.py` | `44b73a66d24f3984eace0b9e1cbde7f827e69c8a` |
| `tests/m1_01/support.py` | `429929c79286745a45a553c520ded01b03633a55` |
| `tests/m1_01/test_project_authority_loader.py` | `1133f4ead4bb51780ffb605978b2fc44a16f1bb8` |
| `tests/m1_01/test_project_authority_storage.py` | `2301a13b13a18730f019cffbb69a70aacd41de32` |
| `tests/m1_01/test_project_manifest.py` | `6249cb3fa56ef193a2e0048e2d3e382f15400fd2` |

No planning, handoff, agent-role, architecture, operations, Alpha-04, M1-02,
or unrelated side-branch file may be copied. The contract file may receive
status-only commits outside the implementation range.

## Named sufficient proof

Use Python `>=3.12` in an environment outside the worktree with
`PyYAML>=6.0.2,<7` and `jsonschema>=4.10,<5`; record exact versions. Generated
bytecode and caches remain outside the worktree.

From `services/maestro/`, run:

```text
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m unittest discover -s ../../tests/review_readiness -v
python -m compileall -q maestro ../../tests/m1_01
```

The proof is sufficient when:

1. results are Alpha-01 11/11, Alpha-02 7/7, Alpha-03 56/56, M1-01 27/27,
   and review-readiness 27/27;
2. every required blob equals the table above;
3. the exact candidate contains only the ten implementation paths;
4. staged, unstaged, and untracked candidate state is empty;
5. `git diff --check` passes for the exact base/head range;
6. schema parsing and the existing M1-01 real-temporary-repository,
   non-mutation, malformed-input, rollback, restart, idempotency, and
   concurrency tests all pass; and
7. the executable review-readiness gate returns `ready: true` for the exact
   candidate before an implementation reviewer is launched.

## Bounded quality contracts

### Q1 — Accepted-behavior fidelity

- **Protected outcome:** current master receives the exact accepted M1-01
  behavior without side-branch policy or planning drift.
- **Operating/failure model:** accidental omission, edit, stale-file import,
  path expansion, or conflict resolution while moving the ten files is in
  scope.
- **Exclusions:** redesign, refactoring, documentation modernization, M1-02,
  public create/register commands, and later roadmap behavior.
- **Assurance level:** exact Git-blob equality plus complete named regression
  proof on current master.
- **Acceptance proof:** required blob table, path allowlist, clean candidate,
  diff hygiene, and all 128 named tests pass.
- **Implementation boundary:** copy only the ten accepted blobs; no semantic
  implementation change is permitted.
- **Proportionality ceiling:** one rematerialization commit and no adjacent
  cleanup.
- **Stop rule:** any required blob cannot run on current master, any product
  conflict exists, or another path is necessary returns the slice to the
  Project Architect before review.

### Q2 — Exact-commit read-only authority observation

- **Protected outcome:** M1-01 observes only the requested commit and never
  mutates or contacts the supplied repository.
- **Operating/failure model:** mutable worktree/index/refs, invalid or noncommit
  revisions, missing/non-blob authority entries, symlinks, submodules, path
  escape, and bounded payload overflow in a trusted local Linux process are in
  scope.
- **Exclusions:** malicious same-UID/root races after Git opens an object,
  malicious Git replacement, network consistency, live repositories, and
  hosting credentials.
- **Assurance level:** deterministic argument-array Git reads pinned to a full
  commit with before/after mutation evidence.
- **Acceptance proof:** the unchanged accepted M1-01 loader and manifest tests,
  exact blobs, and all named suites pass.
- **Implementation boundary:** standard library, PyYAML, JSON Schema test
  validation, SQLite, and read-only Git subprocesses; no shell, checkout,
  fetch, or repository write.
- **Proportionality ceiling:** one local repository, one manifest, at most
  2 MiB per authority blob and 16 MiB total.
- **Stop rule:** any required repository write, network access, stronger
  containment, or live-project access returns the slice before review.

### Q3 — Strict binding and durable candidate persistence

- **Protected outcome:** malformed, missing, conflicting, duplicated, or
  unauthorized authority facts cannot become a reviewable candidate, while a
  valid repeated request creates at most one consistent result and event.
- **Operating/failure model:** the accepted closed manifest schema; secret
  reference identifiers versus payloads; schema migration; transaction
  failure; restart; repeated/conflicting requests; and two concurrent identical
  loads are in scope.
- **Exclusions:** semantic interpretation of architecture prose, activation,
  final registration, distributed databases, USB recovery, retention, and
  later queue transitions.
- **Assurance level:** closed schema and Python validation plus additive SQLite
  migration, constraints, `BEGIN IMMEDIATE`, canonical JSON, and atomic tests.
- **Acceptance proof:** exact accepted blobs and all 27 M1-01 tests pass on the
  current base with all Alpha and review-readiness regressions green.
- **Implementation boundary:** the listed parser, loader, storage, schema,
  dependency, and test files only; no ORM or new framework.
- **Proportionality ceiling:** the accepted M1-01 candidate/run/event model only.
- **Stop rule:** data loss, a non-additive migration, an undefined binding
  choice, or inability to preserve idempotency returns the slice before review.

### Q4 — External-effect and authority confinement

- **Protected outcome:** this slice cannot register a project, dispatch work,
  use credentials, contact an external system, or cross approval/merge
  authority.
- **Operating/failure model:** accidental CLI exposure, repository mutation,
  remote Git, credential lookup, active-binding or `Registered` transition,
  worker launch, notification, PR, merge, or deployment is in scope.
- **Exclusions:** later separately reviewed implementation of those behaviors.
- **Assurance level:** no implementation path for excluded effects, exact path
  confinement, and the accepted negative/non-mutation tests.
- **Acceptance proof:** exact blobs, complete diff review, all named tests, and
  the readiness gate pass.
- **Implementation boundary:** internal M1-01 APIs only.
- **Proportionality ceiling:** no new operation beyond accepted authority load
  and candidate persistence.
- **Stop rule:** any external credential, action, registration, deployment, or
  merge need returns the slice; a reserved risk returns through the Project
  Architect to the Owner.

## Review, disposition, and terminal behavior

The review-readiness gate must return `ready: true` before either reviewer is
launched; a blocked gate launches nobody and consumes no allowance. The slice
receives one complete pre-execution Decision Fidelity review, at most one
planning correction and targeted verification, one complete independent
implementation review, and at most one implementation correction and targeted
verification.

After implementation review, the Project Architect records one disposition for
every finding: `correct now`, `accept known limitation`, `reject finding`, or
`return slice`. Only `correct now` reaches the Maestro Developer and consumes
the implementation correction. A known limitation requires its linked backlog
issue and truthful risk record. Critical exceptions, unverifiable coverage,
primary-outcome failure, and reserved Owner risk cannot be deferred.

Passing the named proof is enough. No role may reopen M1-02B, import its files,
repeat a completed review, expand architecture, select successor work, or merge
without current merge authority. A failed targeted verification terminally
returns this slice.
