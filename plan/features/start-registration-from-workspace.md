# Start registration from the connected workspace

## Outcome and result
Advance [initial project registration](../../docs/outcomes/registration.md#register-and-confirm-a-project-through-the-cli). From the installed terminal workspace, the Owner selects real project sources, an overview, destination and distinct architect and reviewer routes. The service validates and pins the source revision, saves a registration activity, runs the assigned architect, and presents a source-backed scope assessment and any Owner questions after reconnect. This feature stops before independent review or publication.

## Existing implementation to use
`project_authority.py`, `project_manifest.py`, `git_repository.py` and `project_onboarding.py` already read and validate repository material. Adapt that loader and binding path. The legacy `register-project` path also creates graph work and a run; registration must no longer cause those effects. Connect through the existing service request, activity, process and terminal extension mechanisms; use supervised agent routes and persistent sessions. Inspect their actual contracts and tests before editing. New code is limited to the missing registration handler and assessment wiring.

## Connected path
1. CLI submits a uniquely identified start request with source revision, overview, publication destination and route choices.
2. Service validates reachable sources, authority, writable destination, distinct available routes and installed registration process limits. It records the exact input snapshot and receipt before agent work.
3. Real architect receives that snapshot, reports evidence and scope fit, and saves its assessment. Questions use the existing durable question path.
4. CLI shows saved state and resumes it after restart. A repeated request returns its prior receipt; conflicting or invalid input is rejected with a visible correction path.

## Dependencies and ownership
Depends on environment, service, durable records, CLI, agent supervision and process definitions (roadmap outcomes 1–8). Before dispatch, prove Linux host, Owner credentials, GitHub read/write access, selected model routes, workspace mounts, test repository and reset, service install and logs. Mark unknowns unverified. Assign one feature owner at dispatch.

Permitted implementation area: `services/maestro/maestro/project_authority.py`, `project_manifest.py`, `git_repository.py`, `project_onboarding.py`, `cli.py`, `service/`, `terminal/`, `agents/` and corresponding `tests/maestro/` tests, narrowed to exact files by the owner before coding. No architecture or Execution run is started. Record bounded implementation packets inside this feature plan during implementation, not as separate inventory files.

## Verification and stop
On the installed target, start from a real test repository and inspect the saved source SHA, agent identity, assessment, questions and replay after reconnect. Exercise invalid sources, unavailable routes, duplicate requests and a service restart. Stop if route identity or source authority cannot be established; report the blocker without simulated acceptance.
