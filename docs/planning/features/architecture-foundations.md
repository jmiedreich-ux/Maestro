# Start the architecture loop and save project foundations

## Outcome and result
Closes [Establish the project's architectural foundations](../../outcomes/architecture-loop.md#establish-the-projects-architectural-foundations): `/architecture start` on a project with a confirmed registration reserves the project, starts a persistent architect session, and ends with a saved, published code investigation, project structure, specialist role and context files, and a decisions snapshot, without launching a worker or changing source.

## Existing implementation assessment
Reused as built: the registration step machine pattern, agent run service (launch, supervision, recovery limit, run timeout, stop), the GitHub destination (byte-exact journaled publication), atomic project reservation, linked questions and answers, process definitions (the `architecture_loop` section, its bundle and start route already existed), the terminal extension registry and activity actions. Gaps found: no architecture service, records or CLI; the run service had no continuing session (each run got an empty home) and a registration-only response contract; the transports could not resume a conversation; the start reservation ignored unresolved agent runs.

## Decisions
- One new service (`service/architecture.py`) with its own tables; pure record validation and building in `service/architecture_records.py`; the architecture response contract in `agents/architecture_contract.py`.
- Persistent session without changing the root launcher: each run's isolated home is seeded with the saved tool history (`agents/session_state.py`) and the history is saved when the run ends. Claude Code resumes with `--resume <id>` (history re-keyed to the run's working directory); Codex resumes with `thread/resume`. Both were checked by hand against the installed tools first. A missing saved history creates a linked replacement session with the same role and model.
- The architect writes investigation and structure in small documented shapes with local keys; the service allocates finding identities, expands outcome ids into exact published references, builds `decisions.json`, the structure's specialist references, the manifest and the discovery index, and validates them against the installed `architecture-loop@1` schema. Cited source paths are checked against the source tree at the assigned commit.
- Publication is three journaled commits on the registration's publication branch: specialist files (source-local), the version set, then the discovery index (which needs the version's commit).
- The activity ends at "foundations saved" and stays open, holding the project's reservation, until the later breakdown stages exist or the Owner cancels. The view reports state `running` with stage `foundations_saved` and an explaining blocking reason.
- Not built here (later outcomes): allocation exchange, output-correction budget, independent review, confirmation, replanning, restart reuse, Owner limit decisions.

## Verification
Unit tests in `tests/maestro/service/test_architecture_records.py`, `test_session_state.py` and the transport tests; real proof on a disposable service (real Codex/Claude architects, real repository, real GitHub publication) under `var/qa/architecture-live/`.
