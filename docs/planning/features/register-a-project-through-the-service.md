# Register and confirm a project through the service and CLI

## Outcome and result
Closes the gap for [Register and confirm a project through the CLI](../../outcomes/registration.md#register-and-confirm-a-project-through-the-cli): from `/register` in the installed terminal, a real Codex architect and a real Claude Code reviewer assess a real repository's project sources, the Owner answers questions and confirms the exact candidate, and the package and confirmation receipt are published to and verified in the project's GitHub repository before the project shows Registered.

## Existing implementation assessment
Reused as built: shared process definitions (`service/process_definitions.py`, `service/processes.py`), agent runs and response validation (`service/agent_runs.py`, `agents/transport.py`), linked questions and answer delivery (`service/questions.py`), activity, finding and action records (`service/activities.py`), project start reservation (`service/reservations.py`), the request path and event stream, the terminal extension boundary (`terminal/extensions.py`) and the GitHub App token code (`github_client.py`). Not reused: the older manifest-based registration modules (`project_onboarding.py`, `project_discovery.py`, `project_manifest.py`); they read a YAML manifest and create graph work, which the Planning Guide format and this outcome do not use. Gap found: nothing accepts `registration.start`, validates a repository binding or the Markdown sources, runs the architect and reviewer as a registration, builds or publishes a package, confirms it or cancels it, and the terminal has no `/register` command or registration actions.

## Implementation notes
- `service/registration_github.py`: the GitHub destination provider (App token, permissions, branch rules, ref resolution, source and commit reads, one-commit publication with expected-head check, byte verification).
- `service/registration_source.py`: Planning Guide source validation with specific missing-field errors.
- `service/registration.py`: records, the `registration.start`, `registration.confirm` and `registration.cancel` operations, the step machine that runs intake questions, scope confirmation, architect and reviewer runs, findings and questions, package build, publication, confirmation and activation.
- The service reads `repositories`, `repository_bindings` and `registration` from its configuration and starts the step machine with the installed agent run layer.
- Terminal: `/register`, registration actions, and rendering of the registration step.
- Decision recorded: the QA GitHub App identity from the prerequisite pass is the destination authorization; the private key for the disposable proof service is provided in that service's own directory.

## Verification
Unit tests under `tests/maestro/service/` and `tests/maestro/terminal/`; installed proof under `var/qa/registration-live/`.
