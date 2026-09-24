# Run and record assigned agents in the service

## Outcome and result
Closes the gap for [Run and recover assigned agents](../../outcomes/runtime-service.md#run-and-recover-assigned-agents): the service runs a selected architect or reviewer through the installed launch path, records the run in SQL, returns a validated result, stops it completely, and recovers without duplicate runs or reset limits.

## Existing implementation assessment
Reused as built and unit-tested: route selection (`agents/routes.py`, `agents/preflight.py`), isolated workspaces and egress launch (`agents/workspaces.py`, the root egress launcher), the Codex and Claude Code transports and response validation (`agents/transport.py`), supervision by systemd unit with an identity-checked journal (`agents/supervisor.py`), restart reconciliation (`agents/recovery.py`). Missing: nothing in the service called them. There were no SQL run records, no real installed-tool inspection (only test doubles), no event copy to SQL, no recovery accounting, and stopping a run left the agent's root-supervised system unit running.

## Implementation notes
New: `service/agent_runs.py` (assignments, runs, events, artifacts; one-transaction reservation; recovery limit of two; manual retry; one-time duration exception; restart `recover()`), `agents/inspectors.py` (real Codex model catalog and version checks, Claude Code version and exact-model enforcement), `service/projections.py` (runs shown in activity detail), `supervisor.send`. Fix: `maestro-agent-egress` stops its system unit on SIGTERM and the supervisor counts a run as stopped only when that unit is gone. Tests: `tests/maestro/service/test_agent_runs.py`. Live evidence and the driver are in `var/qa/runs-live/`. Results are in the outcome's Result column.
