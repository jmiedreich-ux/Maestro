# Development environment outcome

This outcome prepares the environment used to build Maestro itself. It does not define an environment policy for projects later run by Maestro.

## Prepare a verified development environment

**Outcome:** A developer or assigned agent can start in a clean workspace, read the assigned source, write an output, run a baseline check and exit cleanly. One [environment contract](../development-process/environment-contract.md) and preflight report every category and every unmet applicable requirement for the selected feature before dispatch or assembled QA. The baseline environment can pass before the service is built; service checks become required when later features depend on it.

**Included:** Linux host and tools, service revision when the service is available, repository access, owner and service credentials, selected model routes, sandbox mounts and permissions, ports and running dependencies, realistic test targets and data, a reusable known-good workspace, and a documented reset of run-owned data.

**Completion evidence:** Exact host and tool versions, non-secret credential and route status, one preflight with all applicable checks passing, actual agent launch/output/exit, baseline check, and failure reports for deliberately absent prerequisites. No code outcome is claimed complete from mock routes or file presence.

**Failure behavior:** Preflight blocks only affected work and reports all missing items together. Environment failures are fixed and rechecked outside the coder's review count. Unknown access or installed state remains unverified; the developer does not improvise a substitute.

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception | Result |
|---|---|---|---|---|
| Host, tools and access are known | Exact host and tool versions, non-secret credential and route status, repository and GitHub access. | One preflight report with every applicable check. | None | Done 2026-09-23, revision `827740c`. Versions, credential status (contents never printed), three model routes and GitHub write access are listed in the [prerequisite pass](../planning/prerequisite-pass.md). |
| A real agent runs in a clean workspace | Agent reads the assigned source, writes an output and exits cleanly, on every route. | Real Codex, Claude and Qwen runs; output matched a random input value and the pinned revision. | None | Done 2026-09-23, revisions `827740c` and `ebbb1a1`. Two runs per route on the baseline revision and one per route through the installed package. All exited 0. See the prerequisite pass, "Logs, smoke and failure report". |
| Baseline check passes | The baseline check runs from the clean workspace. | Harness baseline check result. | None | Done 2026-09-23, revision `827740c`. 128 tests passed (agents 50, foundation 7, service 49 with 1 skipped, terminal 22). |
| Isolation and egress hold | Sandbox mounts, permissions and network reach are limited to what each route needs. | Real launches through the installed isolation and egress guard. | None | Done 2026-09-23, revision `ebbb1a1`. Each route reached only its own model host. See "Mounts, permissions and egress". |
| Reset and repeat | Run-owned data is removed by a documented reset and a second run repeats from a clean start. | Real removal by the service user, then a repeat run. | None | Done 2026-09-23, revision `827740c`. See "Data migration and reset". |
| Missing prerequisite is reported and blocks dispatch | Preflight names every missing item together; no workspace is created. | Qwen runtime removed in a test configuration, then restored. | None | Done 2026-09-23, revision `ebbb1a1`. Preflight named it, dispatch was refused, restoring it passed. |
| Service is installed and answering | Service revision, state, port and store are checked when the service exists. | Authenticated and unauthenticated reads. | None | Done 2026-09-23, revision `3b3e1ec`. Authenticated read 200, unauthenticated 401; see "Service installation, ports and store". |
| Upgrade and rollback work | Only a passed, master revision is installed; a failed check restores the backup. | Real upgrade, forced failure and timer-driven install. | None | Done 2026-09-23, revision `bee22c9`. Receipts under `/var/lib/maestro/upgrades/`. Owner accepted the outcome 2026-09-24. |
| Autopilot runner is verified | The runner that drives outcomes runs unattended. | Observed running. | Not verified at acceptance; this run is the first unattended use. Progress updates through the Slack loop are proved. | Accepted exception, as stated. |

See [the development delivery rules](../development-process/delivery-rules.md) and [the roadmap](../planning/outcomes.md).
