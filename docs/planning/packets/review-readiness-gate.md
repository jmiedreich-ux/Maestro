# Bootstrap Review-Readiness Gate

**Slice ID:** `MB-SLICE-REVIEW-READINESS-GATE-01`
**Status:** `PendingTargetedDecisionFidelity`
**Authority:** Owner direction dated 2026-09-03, the
[Bootstrap Convergence Policy](../bootstrap-convergence-policy.md),
[M0-D05](../decisions/m0-d05-rework-review-and-escalation.md), and
[M0-D12](../decisions/m0-d12-bounded-quality-contracts.md)
**Planning base:** `e3c0b71a7a282389f12a4620caf32e5552623720`
**Planning review range:** this base through the commit containing only this
contract

## Durable slice status

This section in this file is the sole durable bootstrap status carrier for
`MB-SLICE-REVIEW-READINESS-GATE-01`; chat, an agent assignment, and a branch
name are not status. Its current value is:

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-REVIEW-READINESS-GATE-01` |
| `phase` | `PendingTargetedDecisionFidelity` |
| `current_actor` | `ProjectArchitect` |
| `live_execution_evidence` | `null` (the slice is not `Running`) |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:e3c0b71a7a282389f12a4620caf32e5552623720..ffb1e1675941052a9b9ce32fee8b447330145b01"]` |

The carrier has exactly those keys and no others. `schema` and `slice_id` are
the literals shown. `evidence_refs` is a UTF-8-byte-sorted array of unique,
nonempty immutable Git ranges or review-record IDs supporting the current
values. The allowed `phase` values are `PendingDecisionFidelity`,
`PlanningCorrection`, `PendingTargetedDecisionFidelity`, `Frozen`, `Running`,
`ImplementationReview`, `ImplementationCorrection`,
`TargetedImplementationVerification`, `MergeReady`, and `Terminal`.
`terminal_state` is `null` unless `phase` is `Terminal`, when it is exactly one
of `Merged`, `Returned`, `Cancelled`, or `OwnerStopped`. `current_actor` is
exactly one of `ProjectArchitect`, `DecisionFidelityReviewer`,
`MaestroDeveloper`, `MaestroDevelopmentManager`, `Coordinator`,
`IndependentImplementationReviewer`, or `None`. A `Running` phase requires
`live_execution_evidence` with exact keys `kind`, `handle`, `packet_item`, and
`observed_at`; all are nonempty strings, `kind` is `Agent` or `Process`, and
`observed_at` is an RFC 3339 UTC timestamp. A non-`Running` phase records
`live_execution_evidence: null`.

The Project Architect updates this carrier when the planning review or its one
correction is consumed, when the contract freezes, and on a Project
Architect-returned terminal result. The Maestro Development Manager updates
the actor, phase, and live evidence on implementation dispatch/check-in and
consumes the implementation-correction count when that correction is
authorized. The Independent Implementation Reviewer returns immutable review
evidence; the Development Manager records it here and increments the
implementation-review or targeted-verification count exactly once. The
Coordinator records `Merged`, `Cancelled`, or `OwnerStopped` after the
corresponding authority action. Every update is one repository commit that
changes only this section, cites its evidence, preserves all counts, and occurs
outside the implementation candidate range; replacement, reassignment, and
takeover continue the same carrier and never reset a count.

## One outcome

Add one executable, local review-readiness gate. No Decision Fidelity or
implementation-review launcher using this gate may run, or consume a review
allowance, unless the gate proves that the supplied Git candidate is a clean,
nonempty, committed, in-scope range with every named validation and
reconstruction check passing.

The gate evaluates facts and controls a supplied launch callback. It does not
select reviewers, contact a model or service, implement scheduling, or decide
whether a review result approves work.

## Exact interface and wire contract

Add `maestro review-readiness --request REQUEST.json`. Unknown keys, duplicate
JSON object keys, wrong JSON types, invalid UTF-8, and non-finite JSON numbers
are malformed requests. The request is the closed object below; every listed
key is required and the object has no others.

| Key | Exact value |
|---|---|
| `schema` | literal `maestro.review-readiness.request/v1` |
| `slice_id` | nonempty string |
| `review_kind` | `DecisionFidelity`, `TargetedDecisionFidelity`, `IndependentImplementation`, or `TargetedImplementation` |
| `repository` | nonempty absolute path string naming one Git worktree |
| `base`, `head` | nonempty revision strings |
| `allowed_paths` | nonempty array of unique valid repository-relative path strings, sorted by UTF-8 bytes |
| `validation_commands` | nonempty array of command objects in execution order |
| `reconstruction_commands` | nonempty array of command objects in execution order |
| `timeout_seconds` | integer `1..3600` (JSON booleans are not integers) applied separately to every command |

Each command object has exactly `check_id` and `argv`. `check_id` is a nonempty
string, unique across both command arrays. `argv` is a nonempty array of
nonempty strings. A valid allowed path is UTF-8, uses `/`, is not absolute,
contains no empty, `.` or `..` segment, and has no trailing slash unless it is
a directory rule. A directory rule `p/` matches only changed paths beginning
with the complete `p/` boundary and at least one following byte. Every other
rule matches one complete path exactly; `src/a` never matches `src/ab` or
`src/a/file`.

Commands run directly, without a shell, from the repository root and in the
declared array order: all validation commands, then all reconstruction
commands. Each command receives the supplied timeout. Capture stdout and stderr
as bytes, stream their SHA-256 over the complete output, and retain at most the
first 65,536 bytes of each stream. A captured-stream object has exactly
`bytes_total` (nonnegative integer), `sha256` (64 lowercase hex characters),
`truncated` (boolean), and `text_utf8` (the retained prefix decoded as UTF-8
with replacement). `truncated` is true exactly when `bytes_total > 65536`.

The result is one closed object with exactly these keys:

| Key | Exact value |
|---|---|
| `schema` | literal `maestro.review-readiness.result/v1` |
| `request` | the accepted request object unchanged, or `null` for a malformed request |
| `request_bytes_sha256` | SHA-256 of the exact request-file bytes |
| `resolved_base`, `resolved_head` | full lowercase commit SHA strings, or `null` when resolution failed |
| `checked_out_head_before`, `checked_out_head_after` | full lowercase `HEAD^{commit}` SHA strings, or `null` when unavailable |
| `changed_paths` | unique changed paths sorted by UTF-8 bytes, or `[]` when unavailable |
| `clean_before`, `clean_after` | booleans, or `null` when the corresponding check could not run |
| `checks` | one check-result object per named command when the request is valid, in execution order |
| `callback` | one callback-result object |
| `blockers` | all applicable blocker objects in the ordering defined below |
| `ready` | boolean |
| `record_digest` | SHA-256 of this result with only `record_digest` omitted |

A check-result object has exactly `check_id`, `category`, `argv`, `outcome`,
`exit_code`, `elapsed_milliseconds`, `stdout`, `stderr`, and `skip_reason`.
`category` is `Validation` or `Reconstruction`; `outcome` is `Passed`,
`Failed`, `TimedOut`, `LaunchError`, or `Skipped`; `exit_code` is an integer
only for `Passed` or `Failed` and otherwise `null`; `skip_reason` is nonempty
only for `Skipped` and otherwise `null`. Its allowed values are
`RepositoryInvalid`, `RevisionInvalid`, `HeadMismatchBefore`, `EmptyRange`,
`DirtyBefore`, or `PathNotAllowed`. `Passed` means exit zero and `Failed` means
a nonzero exit; a timeout records bytes emitted before termination;
`LaunchError` and `Skipped` use the SHA-256/byte count of empty output. Elapsed
time is a nonnegative integer, both streams use the bounded-stream schema
above, and skipped checks use zero elapsed time.

The callback-result object has exactly `outcome` and `detail`. `outcome` is
`NotRequested` for the CLI, `Suppressed` when a library request is gate-blocked,
`Succeeded` after one successful callback, or `Raised` after one callback
raises; `detail` is `null` except for `Raised`, where it is the exception class
name plus message with no traceback. The boundary never retries a raised
callback. A raised callback adds `CALLBACK_EXCEPTION`, produces `ready: false`
and nonzero status, but does not retroactively describe the pre-callback gate
as failed. The callback owns atomic reviewer-launch/allowance consumption; an
exception must mean it committed neither, and the boundary test proves that
contract.

A blocker object has exactly `code`, `check_id`, and `detail`; `check_id` is
nonempty only for a command blocker and is otherwise `null`, while `detail` is
a deterministic nonempty string. `code` is exactly one of, and blockers are
ordered first by this list and then by command execution order:

1. `MALFORMED_REQUEST`;
2. `REPOSITORY_INVALID`;
3. `BASE_NOT_COMMIT`;
4. `HEAD_NOT_COMMIT`;
5. `HEAD_NOT_CHECKED_OUT_BEFORE`;
6. `EMPTY_COMMIT_RANGE`;
7. `EMPTY_CHANGED_PATHS`;
8. `DIRTY_BEFORE`;
9. `PATH_NOT_ALLOWED` (then changed-path UTF-8 byte order);
10. `VALIDATION_FAILED`, `VALIDATION_TIMED_OUT`, or
    `VALIDATION_LAUNCH_ERROR` (request order);
11. `RECONSTRUCTION_FAILED`, `RECONSTRUCTION_TIMED_OUT`, or
    `RECONSTRUCTION_LAUNCH_ERROR` (request order);
12. `DIRTY_AFTER`;
13. `HEAD_NOT_CHECKED_OUT_AFTER`;
14. `CALLBACK_EXCEPTION`.

Blocker detail uses exactly these templates. Braced values are the exact
request value, resolved value, sorted comma-separated path list, integer exit
code, or exception class/message already carried elsewhere in the result:

| Code | Exact `detail` template |
|---|---|
| `MALFORMED_REQUEST` | `request does not conform to maestro.review-readiness.request/v1: {reason}` |
| `REPOSITORY_INVALID` | `repository is not a Git worktree: {repository}` |
| `BASE_NOT_COMMIT` | `base^{commit} did not resolve: {base}` |
| `HEAD_NOT_COMMIT` | `head^{commit} did not resolve: {head}` |
| `HEAD_NOT_CHECKED_OUT_BEFORE` | `checked-out HEAD before commands is {actual}, expected {resolved_head}` |
| `EMPTY_COMMIT_RANGE` | `base..head contains no commit` |
| `EMPTY_CHANGED_PATHS` | `base..head contains no changed path` |
| `DIRTY_BEFORE` | `worktree is dirty before commands: {paths}` |
| `PATH_NOT_ALLOWED` | `changed path is outside allowed_paths: {path}` |
| `VALIDATION_FAILED` | `validation check {check_id} exited {exit_code}` |
| `VALIDATION_TIMED_OUT` | `validation check {check_id} exceeded {timeout_seconds} seconds` |
| `VALIDATION_LAUNCH_ERROR` | `validation check {check_id} could not launch: {exception}` |
| `RECONSTRUCTION_FAILED` | `reconstruction check {check_id} exited {exit_code}` |
| `RECONSTRUCTION_TIMED_OUT` | `reconstruction check {check_id} exceeded {timeout_seconds} seconds` |
| `RECONSTRUCTION_LAUNCH_ERROR` | `reconstruction check {check_id} could not launch: {exception}` |
| `DIRTY_AFTER` | `worktree is dirty after commands: {paths}` |
| `HEAD_NOT_CHECKED_OUT_AFTER` | `checked-out HEAD after commands is {actual}, expected {resolved_head}` |
| `CALLBACK_EXCEPTION` | `review callback raised: {exception}` |

`reason` is the first schema violation in canonical object-key UTF-8 byte order;
duplicate-key and JSON parse errors precede field validation. Exception text is
`{class}: {message}` with control characters JSON-escaped. Git status paths are
decoded with UTF-8 replacement, deduplicated, and sorted by UTF-8 bytes before
joining with `,`. No command stdout or stderr is interpolated into a blocker.

Canonical JSON means UTF-8 encoding, object keys sorted by UTF-8 bytes, array
order preserved, no insignificant whitespace, no ASCII escaping, JSON
lowercase literals, shortest round-trippable integer spelling, and no trailing
newline. SHA-256 is lowercase hexadecimal. The same serializer produces the
printed result and `record_digest`; digest input is the exact canonical result
object with only its top-level `record_digest` key omitted. Reordering request
object keys is therefore equivalent, but array reordering is not.

The evaluator resolves the two requested revisions, resolves checked-out
`HEAD^{commit}`, and records and compares checked-out HEAD with resolved head
before any supplied command. It repeats that resolution and equality check
after every runnable command has finished. A mismatch at either point blocks.
Commands are skipped if the request/repository/revisions are invalid, the
initial HEAD does not equal the requested resolved head, the initial worktree
is dirty, the range is empty, or a changed path is out of scope. One command
failure does not skip later named commands. Post-command cleanliness and HEAD
checks still run after failures and timeouts.

`ready` is true exactly when no blocker exists and, when a library callback was
requested, it succeeded. The CLI exits `0` only for `ready: true`; every
blocked or malformed result exits `2` and prints the complete canonical result. The
library launch boundary invokes the supplied callback exactly once only after
the gate has no pre-callback blocker. A pre-callback blocked result invokes
nothing, so neither reviewer launch nor allowance consumption can occur
through the boundary.

## Closed requirements

| ID | Required behavior |
|---|---|
| `RRG-R01` | Resolve `base^{commit}` and `head^{commit}` in the supplied repository; nonexistent or non-commit objects block. Resolve and record checked-out `HEAD^{commit}` before and after supplied commands; each must equal resolved requested head. |
| `RRG-R02` | Resolved head differs from resolved base and `base..head` contains at least one commit and at least one changed path. |
| `RRG-R03` | `git status --porcelain=v1 -z --untracked-files=all` is empty before and after all checks; staged, unstaged, and untracked paths block. |
| `RRG-R04` | Every `git diff --name-only -z base..head` path matches the exact supplied allowlist semantics; any disallowed path blocks. |
| `RRG-R05` | Every named validation command completes within its timeout and exits zero. |
| `RRG-R06` | Every named digest/reconstruction command completes within its timeout and exits zero. |
| `RRG-R07` | The result conforms to the exact closed schema and records the immutable request, exact request-byte digest, resolved and checked-out heads, sorted changed paths, bounded complete-output evidence, command outcomes, cleanliness facts, callback outcome, blockers, and reproducible content digest. |
| `RRG-R08` | `ready: true` is emitted only when `RRG-R01` through `RRG-R07` all pass. |
| `RRG-R09` | Any failure emits nonzero CLI status and stable blocker objects containing `code`, `check_id` where applicable, and exact detail. |
| `RRG-R10` | A result blocked before callback eligibility cannot invoke the reviewer-launch/allowance-consumption callback; an eligible callback is invoked at most once and a raised callback is recorded without retry or consumption. |

All applicable blockers are accumulated in one run using the declared
dependency and ordering rules. A command timeout, callback exception, or
malformed request is reported without claiming readiness. The bounded retained
output never removes total byte count, full-stream digest, exit code, timeout,
command identity, or blocker detail.

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

The focused suite uses real temporary Git repositories and implements exactly
this finite matrix (one test may cover adjacent assertions, but none may be
omitted):

1. a valid committed candidate whose checked-out `HEAD^{commit}` equals the
   requested resolved head records that equality before and after commands;
2. a requested head different from checked-out HEAD blocks before commands,
   records both SHAs, and invokes no callback;
3. a command that changes checked-out HEAD is blocked by the post-command HEAD
   comparison even when the resulting worktree is clean;
4. base equals head is blocked;
5. a nonexistent base and a nonexistent head are each blocked;
6. a base or head naming an existing tree/blob/tag that cannot peel to a commit
   is blocked as `BASE_NOT_COMMIT` or `HEAD_NOT_COMMIT` respectively;
7. a commit range with no committed file diff is blocked;
8. staged, unstaged, and untracked pre-existing paths are separately blocked;
9. an exact-file allowlist accepts only that file and rejects descendants and
   a longer prefix-collision name;
10. a trailing-slash directory allowlist accepts a descendant and rejects the
    directory-name prefix collision (for example `src/a/` versus `src/ab/x`);
11. each malformed-path form (absolute, empty/`.`/`..` segment, wrong slash,
    and invalid directory terminator) is rejected with `MALFORMED_REQUEST`;
12. a validation nonzero exit is blocked with its exact command result and
    later named checks still run;
13. a reconstruction nonzero exit is blocked with its exact command result;
14. validation and reconstruction timeouts are separately blocked, record
    `TimedOut`, preserve bounded output evidence, and do not run through a
    shell;
15. validation and reconstruction launch errors are separately classified;
16. a successful command that creates a staged, unstaged, or untracked change
    is caught by the post-command clean check and cannot launch review;
17. stdout or stderr larger than 65,536 bytes is truncated only in retained
    text while exact total bytes and the complete-stream digest remain valid;
18. simultaneous validation failure, reconstruction timeout, dirty-after, and
    changed-HEAD facts emit every blocker once in the exact declared order;
19. invalid JSON, a duplicate key, an unknown key, each wrong type, an invalid
    enum, duplicate `check_id`, unsorted/duplicate allowlist entries, empty
    command arrays/argv, and out-of-range/boolean timeouts are malformed,
    execute no command, and invoke no callback;
20. every result and nested request/check/stream/callback/blocker rejects a
    missing or extra key and every value outside its closed enum;
21. request object-key reorder produces the same semantic canonical request;
    allowlist array reorder is malformed, while command-array reorder is valid
    but changes execution order and therefore the canonical result;
22. identical evidence reproduces `record_digest`; changing any included
    scalar or array order changes it, and changing only supplied
    `record_digest` cannot validate;
23. a pre-callback blocked result keeps callback and simulated allowance counts
    at zero; a valid result calls once and consumes once; and
24. a callback exception calls once, consumes zero, is not retried, emits
    `Raised` plus `CALLBACK_EXCEPTION`, returns nonzero, and does not claim
    readiness.

The valid case additionally asserts `ready: true`, zero CLI status, exact
request/result schema equality, exact evidence, stable blocker order, and a
reproducible `record_digest`.

## Review and stopping sequence

The planning candidate receives one complete pre-execution Decision Fidelity
review. Any authorized planning correction is limited to that review's complete
finding set and one targeted verification. After approval, one coding agent
implements the exact contract. The final implementation candidate receives one
independent implementation review and at most one targeted correction and
verification. The slice stops before merge with exact review coverage and a
merge-readiness decision.
