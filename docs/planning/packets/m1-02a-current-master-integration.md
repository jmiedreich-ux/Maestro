# M1-02A Current-Master Integration

**Slice ID:** `MB-SLICE-M1-02A-INTEGRATION-01`
**Status:** `Frozen for implementation`
**Planning and implementation base:**
`438bfc5b1b6315fa66be3af7b63184c2b9bbc8a7`
**Accepted behavior source:**
`d82164c2f3be2164ad6e66b022f645be5f61844b`
**Accepted-result record:**
`docs/planning/done/m1-02a-ar-accepted.md` at `03ce591`
**Outcome authority:** the Owner's current M1 recovery direction; the current
development status and handoffs at the planning base; the Bootstrap
Convergence Policy; the Master Plan; and the applicable accepted M0 decisions.
Historical M1-02A and M1-02AR records explain the accepted result but are not
files to import. M1-02B is terminally returned and is neither authority nor a
source for this slice.

## Durable slice status

This table is the slice's sole durable bootstrap status carrier. Assignments,
chat, branches, and stale observations are not status.

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M1-02A-INTEGRATION-01` |
| `phase` | `Frozen` |
| `current_actor` | `MaestroDeveloper` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:438bfc5b1b6315fa66be3af7b63184c2b9bbc8a7", "git:planning-review:438bfc5b1b6315fa66be3af7b63184c2b9bbc8a7..7dbfa741d2c38880557e75e1cca1e0c02492888e", "git:source-accepted:d82164c2f3be2164ad6e66b022f645be5f61844b", "readiness:a8071b537544d10bda49f343b0bc48a2579d0f534b34285be44ce0b330c1c3ec", "record:03ce591:docs/planning/done/m1-02a-ar-accepted.md", "review:M1-02A-INT-DFR-01-APPROVE"]` |

Counts never reset. Status-only commits outside a frozen implementation range
may update this table. A review allowance is consumed only when a reviewer is
actually launched after a successful mechanical readiness result.

## Project Architect selection decision

Rematerializing accepted M1-02A plus its accepted M1-02AR proof correction is
the smallest executable continuation of M1 after integrated M1-01.

- Current master contains exact accepted M1-01 blobs, satisfying M1-02A's
  executable dependency.
- The accepted M1-02A result differs from accepted M1-01 in exactly five
  coupled source/test paths. Those paths implement and prove one schema-4
  operational-record behavior.
- A clean detached checkout of the accepted source passes Alpha-01 (11),
  Alpha-02 (7), Alpha-03 (56), M1-01 (27), and M1-02 (35) tests.
- Splitting the five paths would alter the already accepted migration,
  validation, public-route wiring, or proof boundary. Importing anything else
  would add stale or unrelated side-branch material.

This is M1 recovery and continuation. It does not reopen M1-02B, select M1-02B
or M1-02C behavior, or close M1.

## One executable outcome

Add the accepted M1-02A schema-4 operational-state foundation to current
master. The integrated behavior defines, validates, and durably persists the
accepted operational records and constraints, including their accepted public
route wiring and rejection behavior, on top of the exact integrated M1-01
authority-loading foundation.

This slice does not repair or reuse M1-02B, add later routing or recovery
behavior, dispatch agents, use external access, operate on live projects,
change Atlas or UI behavior, schedule work, merge, deploy, or authorize a
successor slice.

## Exact implementation boundary

The Maestro Developer may change only these paths, and each final path must
equal the Git blob recorded at the accepted source:

| Path | Required Git blob |
|---|---|
| `services/maestro/maestro/operational_state.py` | `963e5be3c3110dce98264b82546728248f6accfa` |
| `services/maestro/maestro/storage.py` | `498cb4c9125e9c72961f6f7f90aa378a3296c352` |
| `tests/m1_01/test_project_authority_storage.py` | `ecce155cd80d12cc882da23c80e2d89729d95250` |
| `tests/m1_02/test_context_and_payloads.py` | `d1f5370b013e968a4fda2fd368a701455fb48765` |
| `tests/m1_02/test_schema_and_records.py` | `f0ec9fd1dad232e641d1328a7e4573e58fb96360` |

No planning, handoff, SOP, architecture, M1-02B, or unrelated side-branch file
may be copied. The contract file may receive status-only commits outside the
implementation range.

## Named sufficient proof

Use Python `>=3.12` with the accepted dependency ranges and keep generated
bytecode and caches outside the candidate worktree. From `services/maestro/`,
run:

```text
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m unittest discover -s ../../tests/m1_02 -v
python -m unittest discover -s ../../tests/review_readiness -v
python -m compileall -q maestro ../../tests/m1_01 ../../tests/m1_02
```

The proof is sufficient when:

1. results are Alpha-01 11/11, Alpha-02 7/7, Alpha-03 56/56, M1-01 27/27,
   M1-02 35/35, and review-readiness 27/27;
2. the accepted M1-02 fresh-process stress proof passes ten consecutive times
   for both M1-02 test modules;
3. every required blob equals the table above;
4. the exact candidate contains only the five implementation paths;
5. staged, unstaged, and untracked candidate state is empty;
6. `git diff --check` passes for the exact base/head range; and
7. the executable review-readiness gate returns `ready: true` for the exact
   committed candidate before an implementation reviewer is launched.

## Bounded quality contracts

### Q1 — Exact accepted-result integration

- **Protected outcome:** current master receives the exact accepted M1-02A+AR
  executable result without stale side-branch material.
- **Operating/failure model:** omission, edit, path expansion, dependency
  mismatch, or conflict during five-blob rematerialization is in scope.
- **Exclusions:** redesign, refactoring, policy updates, M1-02B/C, and later
  roadmap behavior.
- **Assurance level:** exact blob equality and all named regression proof on
  current master.
- **Acceptance proof:** the blob table, confined clean diff, diff hygiene, all
  163 named tests, and stress proof pass.
- **Implementation boundary:** copy only the five accepted blobs; no semantic
  change is permitted.
- **Proportionality ceiling:** one rematerialization commit and no adjacent
  cleanup.
- **Stop rule:** a required blob cannot run on current master, a product
  conflict exists, or another path is needed.

### Q2 — Schema-4 records and durable constraints

- **Protected outcome:** accepted operational records are valid, reconstructible,
  and durably constrained across creation, rejection, rollback, and restart.
- **Operating/failure model:** malformed payloads, invalid state combinations,
  transaction failure, restart, concurrency, and schema migration are in scope.
- **Exclusions:** distributed storage, later routing/recovery policy, live
  projects, and external systems.
- **Assurance level:** accepted validation and SQLite constraints plus complete
  M1-02 tests and ten-run fresh-process stress proof.
- **Acceptance proof:** exact blobs and all named tests pass without worktree
  residue.
- **Implementation boundary:** the listed operational-state, storage, and test
  files only.
- **Proportionality ceiling:** the accepted schema-4 model and no new record
  families.
- **Stop rule:** data loss, non-additive migration, nondeterministic validation,
  or inability to reconstruct the accepted state.

### Q3 — Authority and effect confinement

- **Protected outcome:** this integration cannot reopen M1-02B, dispatch work,
  contact external systems, operate on live projects, or cross merge authority.
- **Operating/failure model:** accidental stale-file import, external call,
  worker launch, registration expansion, PR/merge, or successor authorization
  is in scope.
- **Exclusions:** later separately selected and reviewed roadmap behavior.
- **Assurance level:** exact path/blob confinement, complete diff inspection,
  negative tests, and the mechanical readiness gate.
- **Acceptance proof:** only the five paths change and all required checks pass.
- **Implementation boundary:** accepted internal M1-02A behavior only.
- **Proportionality ceiling:** no operation beyond exact integration and proof.
- **Stop rule:** any external credential/action, live-project need, reserved
  Owner risk, or authority expansion returns the slice.

## Review, disposition, and terminal behavior

The review-readiness gate must return `ready: true` before either reviewer is
launched; a blocked result launches nobody and consumes no allowance. The slice
receives one complete pre-execution Decision Fidelity review, at most one
planning correction and targeted verification, one complete independent
implementation review, and at most one implementation correction and targeted
verification.

After implementation review, the Project Architect records exactly one
disposition for every finding: `correct now`, `accept known limitation`,
`reject finding`, or `return slice`. Only `correct now` reaches the Maestro
Developer. A known limitation requires its linked backlog issue and truthful
risk record. Critical exceptions, unverifiable coverage, primary-outcome
failure, and reserved Owner risk cannot be deferred.

Passing the named proof is enough. No role may reopen M1-02B, repeat a completed
review, expand architecture, select successor work, or merge without current
merge authority. A failed targeted verification terminally returns this slice.
