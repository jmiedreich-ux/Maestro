# Pause, stop and recover Execution

## Outcome and result
Closes [Pause, stop and recover Execution](../../outcomes/execution.md#pause-stop-and-recover-execution): the Owner can pause, resume or gracefully stop a real Execution, and a restart, a failed agent or a lost Git response recovers from saved facts without repeated effects, lost work, reset allowances or a false completion.

## Existing implementation assessment
Reused as built: the Execution service's saved records and per-tick advance (a restart already reloads the packet, queue, review, milestone, journal and run records), automatic recovery within the configured allowance, the run supervisor's `manual` run kind, the Owner-decision route and the work-disposition stop (which already ends an Execution for replanning), the completion-record publication path and its journal, and the terminal Execution view. Missing and built here: the `execution.pause`, `execution.resume`, `execution.stop` and `execution.retry` operations, the saved in-progress set with its refusal rules, the stopped-closure record and `stopped` state, the typed manual-retry grant, and their terminal commands and display. No schema change: the set and the grants live in the activity's and packet's saved records, so no schema bundle changes.

## Features
1. Lifecycle control: accept pause or stop by recording the exact in-progress set in one transaction, refuse every new reservation and keep first-in-first-out order, settle only the permitted downstream stages, then pause (resumable) or publish a verified stopped-closure record and enter `stopped`, which frees the project.
2. Manual retry: an Owner `execution_manual_retry` decision creates one unconsumed grant per configured manual attempt; `execution.retry` reserves it once and the launch consumes it, keeping the same assignment, review counts and allowances.

## Decisions
- A stop published from `stopped` is never called completion: its record kind is `stopped`, it lists unfinished work, and the terminal says so.
- A held queue entry outside the set keeps its place; a member behind it is settled as blocked, not skipped to.
- A run in progress is never killed by a pause or a graceful stop; only the existing disposition stop terminates runs.
- Recovery after a restart is the existing reload of saved records; this outcome proves it with a real restart and adds no second mechanism.

## Verification
Unit tests in `tests/maestro/service/test_execution_lifecycle.py`; real proof on a disposable service under `var/qa/lifecycle-live/` with real agents, real Git and a real service restart.
