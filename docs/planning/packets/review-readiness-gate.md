# Bootstrap Review-Readiness Gate

**Slice ID:** `MB-SLICE-REVIEW-READINESS-GATE-01`
**Status:** `PendingDecisionFidelity`
**Authority:** Owner direction dated 2026-09-03, the
[Bootstrap Convergence Policy](../bootstrap-convergence-policy.md),
[M0-D05](../decisions/m0-d05-rework-review-and-escalation.md), and
[M0-D12](../decisions/m0-d12-bounded-quality-contracts.md)
**Planning base:** `e3c0b71a7a282389f12a4620caf32e5552623720`
**Planning review range:** this base through the commit containing only this
contract

## One outcome

Add one executable, local review-readiness gate. No Decision Fidelity or
implementation-review launcher using this gate may run, or consume a review
allowance, unless the gate proves that the supplied Git candidate is a clean,
nonempty, committed, in-scope range with every named validation and
reconstruction check passing.

The gate evaluates facts and controls a supplied launch callback. It does not
select reviewers, contact a model or service, implement scheduling, or decide
whether a review result approves work.

## Exact interface and result

Add `maestro review-readiness --request REQUEST.json`. The request is a closed
JSON object containing:

- `slice_id`, `review_kind`, `repository`, `base`, and `head`;
- nonempty `allowed_paths`, where a trailing `/` denotes a directory prefix
  and every other value denotes one exact repository-relative path;
- nonempty `validation_commands` and `reconstruction_commands`, each an array
  of unique objects with `check_id` and a nonempty `argv` string array; and
- `timeout_seconds`, a positive integer applied separately to every command.

Commands run directly without a shell from the repository root. The result is
canonical JSON containing the supplied identity, resolved base/head commit
SHAs when available, sorted changed paths, pre-check and post-check cleanliness,
each named command and its exit result, a stable ordered blocker list, and a
SHA-256 `record_digest` over the result excluding that digest.

`ready` is `true` if and only if all requirements below pass. The CLI exits
zero only for `ready: true`; every blocked result exits nonzero and prints the
complete machine-readable result. The library launch boundary accepts this
result and a reviewer-launch callback. It invokes that callback exactly once
only for `ready: true`; for every blocked result it invokes nothing, so neither
reviewer launch nor allowance consumption can occur through the boundary.

## Closed requirements

| ID | Required behavior |
|---|---|
| `RRG-R01` | Resolve `base^{commit}` and `head^{commit}` in the supplied repository; nonexistent or non-commit objects block. |
| `RRG-R02` | Resolved head differs from resolved base and `base..head` contains at least one commit and at least one changed path. |
| `RRG-R03` | `git status --porcelain=v1 -z --untracked-files=all` is empty before and after all checks; staged, unstaged, and untracked paths block. |
| `RRG-R04` | Every `git diff --name-only -z base..head` path matches the exact supplied allowlist semantics; any disallowed path blocks. |
| `RRG-R05` | Every named validation command completes within its timeout and exits zero. |
| `RRG-R06` | Every named digest/reconstruction command completes within its timeout and exits zero. |
| `RRG-R07` | The result records the immutable request identity, resolved base/head, sorted changed paths, commands, outcomes, cleanliness facts, and content digest. |
| `RRG-R08` | `ready: true` is emitted only when `RRG-R01` through `RRG-R07` all pass. |
| `RRG-R09` | Any failure emits nonzero CLI status and stable blocker objects containing `code`, `check_id` where applicable, and exact detail. |
| `RRG-R10` | A blocked result cannot invoke the reviewer-launch/allowance-consumption callback. |

All applicable blockers are accumulated in one run. A command timeout, launch
exception after readiness, or malformed request is reported without claiming
readiness. Outputs may be bounded for storage, but exit code, timeout, command
identity, and blocker detail may not be omitted.

## M0-D12 bounded quality contract

1. **Protected outcome:** a reviewer and its allowance cannot be spent on a
   missing, mutable, empty, unscoped, or mechanically failing candidate.
2. **Operating/failure model:** one local Linux process, one ordinary Git
   worktree, concurrent repository reads only, missing/replaced revisions,
   staged/unstaged/untracked changes, disallowed committed paths, failed or
   timed-out local commands, and a check that dirties the candidate.
3. **Exclusions:** M1-02B repair, review routing or reviewer selection, actual
   agent/model transport, learning records, Atlas, UI, scheduler work, external
   access, live projects, merges, deployments, and general policy changes.
4. **Assurance level:** deterministic standard-library behavior with real
   temporary Git repositories and subprocesses; no synthetic Git-result
   fixtures for acceptance.
5. **Sufficient proof:** the named focused test command passes every case in
   the acceptance matrix, the full existing suite passes, and an independent
   implementation reviewer verifies the exact clean candidate range.
6. **Implementation boundary:** the exact writable paths below, Python standard
   library, Git CLI, and existing Maestro CLI conventions. No database or
   network dependency.
7. **Proportionality ceiling:** one request schema, one evaluator/result model,
   one guarded callback seam, one CLI subcommand, and one focused test module;
   no generalized workflow engine, policy language, plugin system, or daemon.
8. **Stop/escalation:** inability to prove a clean nonempty commit range,
   deterministic allowlist behavior, complete command outcomes, content-addressed
   evidence, or zero blocked launches returns the slice. Passing the named proof
   is enough; other improvements become later learning candidates.

## Exact writable paths

Planning may change only this contract. After Decision Fidelity approval, the
implementation agent may change only:

- `services/maestro/maestro/review_readiness.py`
- `services/maestro/maestro/cli.py`
- `tests/review_readiness/test_review_readiness.py`

No fixture, handoff, status, policy, M1-02B, database, or other source path is
writable in this slice.

## Named acceptance proof

Run from repository root:

```text
PYTHONPATH=services/maestro python -m unittest tests.review_readiness.test_review_readiness -v
PYTHONPATH=services/maestro python -m unittest discover -s tests -v
python -m compileall -q services/maestro/maestro tests/review_readiness
git diff --check
```

The focused suite uses real temporary Git repositories and proves at minimum:

1. base equals head is blocked;
2. either commit is nonexistent is blocked;
3. a range with no committed file diff is blocked;
4. a staged, unstaged, or untracked candidate is blocked;
5. a disallowed committed path is blocked;
6. a failed validation command is blocked;
7. a failed digest/reconstruction command is blocked;
8. a completely valid committed candidate returns `ready: true`, zero exit,
   exact evidence, and a reproducible `record_digest`; and
9. the launch callback and its simulated allowance consumption remain zero for
   every blocked result and occur exactly once for the valid result.

## Review and stopping sequence

The planning candidate receives one complete pre-execution Decision Fidelity
review. Any authorized planning correction is limited to that review's complete
finding set and one targeted verification. After approval, one coding agent
implements the exact contract. The final implementation candidate receives one
independent implementation review and at most one targeted correction and
verification. The slice stops before merge with exact review coverage and a
merge-readiness decision.
