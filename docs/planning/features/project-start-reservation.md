# Reserve a project start atomically

## Outcome and result
Closes the one gap in [Preserve project activity and requests](../../outcomes/runtime-service.md#preserve-project-activity-and-requests): a project start or re-registration checks that the project is idle and reserves it in one write transaction, so simultaneous starts cannot both succeed. Unknown run state counts as not idle, and other projects stay available.

## Existing implementation assessment
Storage, project and activity identities, questions, request replay, pending delivery and restart recovery were already built and were proved on a disposable copy of the installed service (two projects, repeated and conflicting requests, cross-project refusal, `kill -9` restart). Only the reservation was missing.

## Implementation notes
`services/maestro/maestro/service/reservations.py` with `tests/maestro/service/test_reservations.py`. Ten real processes raced for one project: one won, nine were refused, another project stayed available. Codex reviewed the diff once; its one finding (agent-run status is not yet checked) is an accepted exception because no run store exists until Run and recover assigned agents. Results are in the outcome's Result column.
