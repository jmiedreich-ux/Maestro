# Recover a registration through the service and CLI

## Outcome and result
Closes the gap for [Recover registration without losing decisions or exceeding limits](../../outcomes/registration.md#recover-registration-without-losing-decisions-or-exceeding-limits): an interrupted registration resumes from its last verified step or pauses visibly, keeping decisions, findings, versions and review budgets, and the Owner can retry or decide from the CLI.

## Existing implementation assessment
Reused as built: the agent run service with its supervisor recovery after a restart, automatic recovery limit, manual run kind and run timeout; the registration step machine, which is repeatable from saved rows; the publication journal with byte-exact reconciliation (`publish` returns the head that already holds the bytes) and idempotent activation; the shared review counter. Gaps found: a paused registration offered only Cancel and forgot which step it paused at; there was no `registration.retry` and no `owner.decision` handler; a review grant could not raise the shared allowance; a launch that failed after its run was reserved lost the failed run's identity.

## Implementation notes
- Every technical pause saves the step to resume (`paused`) and offers Retry activity (agent) or Retry publication, plus Cancel; the CLI states what to fix and takes `/registration retry <what you changed>`.
- `registration.retry` validates the failed run or paused publication, records the intervention, then starts one manual run (the runtime enforces confirmed termination) or reopens the publication for reconciliation. Counters and review counts are not reset.
- `owner.decision` (target `fidelity_review`) grants one extra review attempt to the exact next review assignment once, or leaves the registration paused. The grant is recorded beside the snapshotted limit.
- The activity view exposes the paused step, grants and the assignment's recovery counters.

## Verification
Unit tests in `tests/maestro/service/test_registration.py`; real proof on a disposable service under `var/qa/registration-live/recover-evidence.json`.
