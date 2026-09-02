# M1-01R — Constrain the Acceptance Authority Enum

**Status:** Superseding remediation candidate for Decision Fidelity review;
not released
**Packet ID:** `maestro-m1-01r-acceptance-authority-enum`
**Parent graph node:** `MAESTRO-M1-01-REAL-PROJECT-AUTHORITY-LOADER`
**Superseding graph revision:** `maestro-m1-m4-real-r2-remediation-1`; this
scoped overlay supersedes only the failed M1-01 acceptance path in revision
`maestro-m1-m4-real-r1` and leaves every other node unchanged
**Planning source base:** `a80179bf98a751bd8f0c5e19a388b866ad52071a`
**Implementation base:** `4e213b10d2bfd709e43a9073c41cc986e78a0fcd`
**Expected branch:** `implementation/m1-01r-acceptance-authority-enum`
**Expected worktree:**
`/home/jeremy/Development/Maestro-m1-01r-implementation`
**Authority:** [M0-D05](../decisions/m0-d05-rework-review-and-escalation.md),
[M0-D06](../decisions/m0-d06-project-manifest-contract.md),
[M0-D12](../decisions/m0-d12-bounded-quality-contracts.md), and
[M0-D15](../decisions/m0-d15-real-m1-m4-implementation-path.md)
**Implementation role:** dedicated Maestro Developer
**Execution class:** `codex-cloud-maestro-developer`
**Role/SOP versions:** `docs/agents/maestro-developer.md`,
`docs/agents/coding-agent-sop.md`, `docs/agents/integration-agent.md`, and
`docs/agents/independent-review-agent.md` at planning source base
`a80179bf98a751bd8f0c5e19a388b866ad52071a`
**Coordinator authority:** M0-D15 and `ai/handoffs/current.md` at planning
source base `a80179bf98a751bd8f0c5e19a388b866ad52071a`
**Decision Fidelity route:** fresh independent Decision Fidelity Reviewer over
the exact planning base/head and any targeted planning correction
**Integration route:** separate Integration Agent, `validate-only`
**Review route:** fresh Independent Implementation Reviewer over the exact
base/head; any correction-only diff must also be covered
**Routine acceptance authority:** Project Architect

## Reason and authority boundary

The complete M1-01 implementation review found a new failure class after its
single correction was used. At final head
`4e213b10d2bfd709e43a9073c41cc986e78a0fcd`, a manifest with
`delivery.acceptance_authority: unrecognized-approver` is confirmed and stored
as a `Reviewable` candidate. The approved M1-01 contract permits exactly:

- `project-architect`, which may be `Reviewable`; and
- `owner`, which is a valid reserved value but must produce a `Blocked`
  material return under M0-D15.

Every other value is malformed and must fail before database mutation. M0-D05
prohibits another correction under the exhausted M1-01 attempt, so this exact
superseding packet is required. It changes no architecture and requires no
Owner choice.

## Complete remediation node

| Field | Value |
|---|---|
| Stable remediation ID | `MAESTRO-M1-01R-ACCEPTANCE-AUTHORITY-ENUM` |
| Graph revision | `maestro-m1-m4-real-r2-remediation-1` |
| Task record | `docs/planning/packets/m1-01r-acceptance-authority-enum-remediation.md` |
| History edge | `Remediates -> MAESTRO-M1-01-REAL-PROJECT-AUTHORITY-LOADER` at failed head `4e213b10d2bfd709e43a9073c41cc986e78a0fcd` |
| Typed upstream dependency | `hard` + `review-before-consume` on the exact failed M1-01 result and its complete independent-review disposition; no advisory dependency |
| Project / workstream / milestone | `maestro` / `project-registration` / `M1` |
| Title | Constrain the acceptance-authority enum |
| Outcome | Reject unrecognized acceptance authorities before persistence while preserving the two approved dispositions. |
| Non-goals | Any other manifest/schema change, authority redesign, storage migration, Git behavior, CLI, repository/network operation, registration, credential, merge, or deployment. |
| Priority / rank | `P0-remediation` / `1` |
| Allowed out of order | none; M1-01 remains unaccepted and every downstream M1-01 dependency remains blocked |
| Planned route | cloud collaboration worktree / dedicated Maestro Developer / `codex-cloud-maestro-developer` / session-inherited Codex model recorded factually at preflight |
| Eligible execution class | `codex-cloud-maestro-developer` only |
| Hard dependencies | final failed implementation head `4e213b10d2bfd709e43a9073c41cc986e78a0fcd`; this packet's Decision Fidelity approval; Project Architect release |
| Soft dependencies | none |
| Downstream unlock | routine combined Project Architect acceptance restores the original M1-01 downstream edges; each downstream packet remains governed by its own exact dependency and release gates |
| Owned domain / locks | acceptance-authority schema/parser/tests / `path:maestro-registration-core`, `file:maestro-project-schema` |
| Input / output contracts | `maestro-project-authority-load-v1` / same contract with the accepted two-value authority enum enforced |
| Required checks | Alpha-01, Alpha-02, Alpha-03, M1-01 suites; compileall; JSON Schema validation; exact changed-path review |
| Evidence contract | exact base/head and branch; changed paths; full gate outputs and dependency versions; Schema/Python/full-loader two-value proof; zero-row rejection proof; Integration disposition; complete review-coverage union; model/runtime/context/usage facts; gaps; clean status and released locks |
| Integration route | separate Integration Agent, `validate-only`; an Integration-authored change requires a different final reviewer |
| Reviewer route | fresh Independent Implementation Reviewer over `4e213b1..M1-01R-head` plus any single targeted M1-01R correction diff |
| Resource envelope | one isolated worktree; one 45-minute attempt; at most one eligible M0-D05 correction; no parallel writer in the locked domain |
| Approval state | `PendingDecisionFidelity`; not runtime `Dispatchable` |
| Dispatchable transition | exact packet `APPROVE`, Project Architect release, then Coordinator verification of base/worktree/route/context/locks |
| Acceptance boundary | Project Architect accepts routine proof; Owner only if implementation exposes a new reserved material choice |

## Exact implementation contract

Change only:

```text
docs/schemas/maestro-project-v1.schema.json
services/maestro/maestro/project_manifest.py
tests/m1_01/**
```

The canonical JSON Schema field
`delivery.acceptance_authority` must be an enum containing exactly
`project-architect` and `owner`. Python manifest validation must enforce the
same closed set during the loader's parsing phase, before authority inventory
proceeds and before any storage call or mutation.

Do not default, trim, alias, case-fold, or translate a value. Do not change the
existing disposition rule: `project-architect` follows the normal fact and may
be `Reviewable`; `owner` records the exact reserved-policy conflict and is
`Blocked`. Unknown strings and non-string values are malformed input and
insert no project, registration run, or event.

No other field, schema rule, parser behavior, Git operation, storage shape,
public API, dependency, or documentation meaning may change.

## Exact dispatch controls

- Use one clean isolated worktree at the exact implementation base and expected
  branch. Acquire both named locks before editing.
- Preflight requires 32,768 available context tokens including an 8,192-token
  handoff/output reserve. Record exposed model/runtime/context/usage facts;
  unsupported counters are `unavailable`. Checkpoint at 16,384, prepare
  handoff at 12,288, and stop new work at 8,192 remaining.
- The attempt ceiling is 45 minutes. The Coordinator may request bounded
  factual status after 10 minutes without visible progress, no more often than
  every 10 minutes, with a 2-minute response window. Do not invent an ETA.
- Resolve declared dependencies in an ephemeral environment only. The test
  environment must use `PyYAML>=6.0.2,<7`; record exact versions and leave no
  environment or bytecode artifact in the worktree.
- One initial remediation attempt and at most one named-gate correction are
  available. Infrastructure failure stops to the Coordinator. A new failure
  class, architecture conflict, unowned path, or exhausted correction returns
  to the Project Architect.
- Do not push, merge, create a PR, access a live project, mutate/read a project
  repository, provision credentials, or perform any external product action.

## Required proof and gates

Add tests that prove:

1. JSON Schema and Python both accept exactly `project-architect` and `owner`;
2. JSON Schema and Python both reject `unrecognized-approver`, empty, wrong
   case, surrounding whitespace, and non-string values;
3. a full real temporary-repository loader call with `project-architect`
   remains `Reviewable` and creates one candidate/run/event;
4. the same full loader with `owner` is `Blocked`, creates one blocked run/event
   and no candidate project, and records the reserved-policy conflict;
5. the same full loader with every unrecognized representative fails before
   persistence and leaves all three table counts at zero; and
6. all previous M1-01 and Alpha behavior remains green.

From `services/maestro/`, run in the supported ephemeral environment:

```text
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m compileall -q maestro
```

Also run JSON parsing/validation of the canonical schema and `git diff --check`.
Remove generated caches before the clean committed handoff.

## Complete M0-D12 quality contracts

### Q1 — Closed acceptance-authority semantics

- **Protected outcome:** no undefined acceptance authority can become a fact,
  candidate, run, or event.
- **Operating/failure model:** trusted local loader; approved values, arbitrary
  strings, wrong types/case/whitespace, replay, and real temporary repositories
  are in scope.
- **Exclusions:** changing which roles hold authority, interpreting project
  prose, external identity verification, registration, merge, and deployment.
- **Assurance level:** the same explicit two-value enum at Schema, Python, full
  loader, and persistence boundaries.
- **Sufficient proof:** required proofs 1 through 5 pass in the supported
  environment and reproduce the original failing value as rejected.
- **Implementation boundary:** one Schema enum, one Python closed-set check,
  and bounded M1-01 tests in the three owned path areas.
- **Proportionality ceiling:** no generic policy engine, compatibility aliases,
  new role, storage migration, or redesign.
- **Stop/return:** any third value or changed disposition meaning returns to the
  Project Architect before implementation continues.

### Q2 — Remediation confinement and regression preservation

- **Protected outcome:** fixing the enum cannot alter accepted Git, manifest,
  persistence, CLI, external-effect, or M0-D15 approval behavior.
- **Operating/failure model:** accidental scope expansion, generated artifacts,
  unsupported dependency runtime, and regression are in scope.
- **Exclusions:** performance, service/machine restart, GitHub, create/register,
  worker dispatch, Atlas, notification delivery, USB recovery, and live work.
- **Assurance level:** exact three-area changed-path review, all Alpha/M1-01
  regression gates, supported dependency versions, and clean committed head.
- **Sufficient proof:** required proof 6, all named gates, schema validation,
  diff hygiene, and Integration plus independent final-head review pass.
- **Implementation boundary:** packet-owned files only; no production operation
  beyond existing parser behavior.
- **Proportionality ceiling:** one narrowly reproduced failure class and its
  carrier/loader regressions.
- **Stop/return:** any unowned path, new failure class, infeasible proof, or
  external/reserved choice returns to the Project Architect.

## Handoff and acceptance

The Developer commits one exact result and reports base/head, paths, full gate
outcomes, the six proofs, exact dependency versions, context/usage facts,
known gaps, clean status, and lock release. Integration validates without
changing code. A fresh Independent Implementation Reviewer covers the exact
base/head and any one correction diff.

The combined review-coverage record is exact:

1. original implementation range
   `c6eb7d83082a1ac75eb9b7798b6f2bdce74341c4..f44518c3144ae5bdc95fc73607cde7e9d58b8a5c`;
2. exhausted M1-01 correction range
   `f44518c3144ae5bdc95fc73607cde7e9d58b8a5c..4e213b10d2bfd709e43a9073c41cc986e78a0fcd`;
3. the complete independent review at `4e213b1`, which covered both prior
   ranges and returned `REQUEST_CHANGES` for the new acceptance-authority
   failure class after the M1-01 correction was exhausted;
4. the new full remediation review range
   `4e213b10d2bfd709e43a9073c41cc986e78a0fcd..M1-01R-final-head`; and
5. if used, the single M1-01R correction-only diff from its initial committed
   head to its corrected final head.

The Developer and Integration handoffs and final acceptance record must list
that union, the disposition for each review, and mechanically confirm that
every commit from `c6eb7d8` through the exact combined final head is covered
with no uncovered change after the final reviewer observation.

After complete review coverage and `APPROVE`, the Project Architect may accept
the remediation and M1-01 together. That acceptance releases only dependencies
whose own exact packets permit release; it does not merge, register a project,
activate credentials, or authorize external work.
