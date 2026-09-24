# Apply process definitions in the installed service

## Outcome and result
Closes the gap for [Apply shared process definitions](../../outcomes/runtime-service.md#apply-shared-process-definitions): the installed service holds the schema bundles, reads the `registration` and `architecture_loop` sections of `/etc/maestro/agents.toml`, validates each with its installed bundle, reports the result to the Owner, and gives agent assignments their limits from the saved definition.

## Existing implementation assessment
Reused as built and unit-tested: `service/processes.py` (validation, saved snapshots, counters, handler registry) and `service/resources.py` (installed bundle resolution and hashes). Gap found on the host: `/opt/maestro/schemas` was empty because the package shipped no bundles, no provider was registered, the running service never read the process sections, and nothing applied a definition to an assignment.

## Implementation notes
New: packaged bundles `schemas/registration-process/1` and `schemas/architecture-loop/1` (byte copies of `docs/schemas`, checked by a test); `service/process_definitions.py` (providers for both processes, handlers that turn a snapshot into start operation, review limit and assignment terms, per-process report); `GET /api/v1/processes` (Owner-authenticated, re-reads the file each call, an invalid process is held alone). Registration package validation, publication, confirmation and Owner limit decisions stay with the registration and architecture-loop outcomes.

## Verification
Unit tests `tests/maestro/service/test_process_definitions.py`; installed proof under `var/qa/process-live/`.
