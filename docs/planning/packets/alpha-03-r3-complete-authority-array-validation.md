# Alpha-03-R3 — Complete Required Authority-Array Validation

- **Status:** Architecture-issued superseding completion packet under the
  Owner's 2026-08-31 non-material-completion delegation; pending fresh full
  Decision Fidelity Review and planning merge; not executable
- **Owner:** Jeremy Miedreich
- **Architecture authority:**
  [Alpha-03 proposal](../proposed/alpha-03-synthetic-project-discovery.md) and
  the exact required-facts contract in the merged
  [Alpha-03-R2 packet](alpha-03-synthetic-project-discovery.md)
- **Delegation source:**
  [Non-material completion delegation](../../../sources/planning/2026-08-31-non-material-completion-delegation.md)
- **Planning branch base:** `master` merge
  `b2594d9ab4cad528cd6272622f68162850a0584e`
- **Original implementation base:**
  `dcca2174dd919aa204707961f1b33ad15de9af41`
- **Exact failed candidate base:**
  `f21e4a2ff25cead8b972b4433da33f0e9910efc5`
- **Predecessor review:** targeted follow-up `REQUEST_CHANGES` for exact range
  `e3929c46882dbd0512bac377bdef1440d4e17cff..f21e4a2ff25cead8b972b4433da33f0e9910efc5`
- **Execution class:** one fixture-only completion attempt in a clean isolated
  worktree
- **Worker route:** Local Qwen after this exact packet receives Decision
  Fidelity APPROVE, merges, and the Coordinator verifies every eligibility gate
- **Implementation reviewer route:** fresh independent GPT-5.6 Terra reviewer
  at high reasoning over the complete cumulative Alpha-03 range
- **Planning fidelity route:** fresh independent GPT-5.6 Sol reviewer at high
  reasoning

## Why Architecture may issue this packet

The merged Alpha-03-R2 packet already says that
`authority.architecture_paths` and `authority.plan_paths` are non-empty arrays
of non-empty strings and that every conflict observation must itself be valid
for its leaf. The failed implementation permits `[]` for the generic array
type. Completing the two existing minimum-cardinality rules changes no product,
architecture, schema meaning, scope, security boundary, or external authority.

This is the single Architecture-delegated superseding completion permitted
after the R2 implementation exhausted its correction allowance. It is not a
second correction under R2 and does not weaken M0-D05.

## Outcome

Complete the existing Alpha-03 validation contract so an empty confirmed or
conflicting value for either required authority-path array is rejected before
claim, executor activity, worktree creation, SQLite mutation, evidence, or
handoff, while arrays explicitly allowed to represent “none” remain valid when
empty.

## Required behavior

1. `authority.architecture_paths` and `authority.plan_paths` each require at
   least one unique, non-empty string after trimming.
2. The requirement applies both to a confirmed leaf value and to every
   individual value inside that leaf's `conflicts` observation.
3. `[]` for either required authority array is malformed input, not a missing
   fact, conflict, reviewable binding, or coordinator escalation result.
4. Malformed input is rejected before packet claim, worktree/executor activity,
   SQLite mutation, evidence, or handoff.
5. Existing empty-array meanings remain unchanged:
   - verification command arrays may be empty;
   - `roles.specialist_overlays` may be empty;
   - operations reference/lock arrays may be empty; and
   - `exceptions.items` remains empty when disposition is `none` and non-empty
     when disposition is `declared`.
6. All other Alpha-03 normalization, conflict, idempotency, evidence, fixture,
   synthetic-confinement, and terminal-handoff behavior remains unchanged.
7. No test, check, invariant, validation case, or evidence requirement may be
   removed or weakened to obtain a pass.

## Owned implementation paths

```text
services/maestro/maestro/synthetic_discovery.py
tests/alpha_03/test_synthetic_project_discovery.py
```

No other implementation path may change. Stop if the requirement cannot be
completed inside these two files using the standard library and existing
Alpha-03 design.

## Q1 — Exact completion of the existing array contract

- **Protected outcome:** no synthetic inventory or proposed binding can treat
  an empty required authority-path array as confirmed or as a valid conflict
  observation.
- **Operating/threat/failure model:** trusted fixture JSON may supply `[]` as a
  confirmed `authority.architecture_paths`/`authority.plan_paths` value or as
  one observation among at least two conflict values; generic array validation
  currently permits it. Optional arrays must continue accepting their explicit
  empty/none disposition.
- **Explicit exclusions:** any new leaf, schema redesign, real-project policy,
  repository discovery, adapter/registration flow, external access, dependency,
  UI/API, migration, or stronger filesystem assurance.
- **Practical assurance level:** one explicit minimum-cardinality rule for the
  two named authority leaves, applied through both confirmed and conflict
  validation paths before lifecycle mutation.
- **Sufficient acceptance proof:** focused parameterized tests reject `[]` for
  each named leaf in confirmed and conflicting forms; wrapper-level tests prove
  rejection before claim/SQLite mutation; positive regression tests prove every
  explicitly optional array still accepts `[]`; all existing Alpha-01,
  Alpha-02, and Alpha-03 tests plus the required CLI and `git diff --check`
  pass.
- **Permitted implementation boundary and complexity:** a small declarative or
  explicit minimum-cardinality check in `synthetic_discovery.py` and focused
  table-driven tests in the existing Alpha-03 test module; standard library
  only, no refactor beyond what the check requires.
- **Proportionality ceiling:** two production/test paths, two required leaves,
  their confirmed/conflict validation routes, and optional-array regression
  coverage; no general schema framework.
- **Exact stop/escalation rule:** stop for any required path outside the owned
  files, new contract meaning, security/external authority, test weakening, or
  infeasible guarantee. If this packet and its one permitted targeted
  correction do not pass, return to the Owner; Architecture may not issue a
  second delegated superseding completion.

## Required checks

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m maestro.cli run-packet \
  --packet ../../fixtures/alpha/alpha-03-complete-discovery-packet.json \
  --runtime-dir ../../var/alpha-03-r3-check
git diff --check f21e4a2ff25cead8b972b4433da33f0e9910efc5..HEAD
```

Passing is sufficient only when the focused negative and positive regressions,
all existing suites, required CLI result, scope check, and diff check pass. The
CLI must remain `AwaitingReview` with complete evidence. Runtime artifacts stay
inside the ignored isolated runtime directory.

## Review and handoff

The implementation handoff records the exact base/head, changed paths, commands
and results, focused cases, CLI evidence, and confirmation of no external
access. Because both earlier implementation reviews ended in
`REQUEST_CHANGES`, final independent implementation review is fresh and full
from original base `dcca2174dd919aa204707961f1b33ad15de9af41` through the
exact future R3 head recorded in the implementation handoff.

The reviewer must also confirm that the R3-only diff is confined to the two
owned paths and that no prior test or behavior was weakened. Approval stops at
the current Owner acceptance/merge gate; it does not merge or release Alpha-04.

## Non-authorization

This packet does not authorize real repository/project access, registration,
Git/GitHub/CI/network use by the worker, credentials/secrets, provider access,
Atlas/API/UI, a second Architecture-issued superseding completion, automatic
merge, Owner acceptance, Alpha-04 implementation, or successor selection.
