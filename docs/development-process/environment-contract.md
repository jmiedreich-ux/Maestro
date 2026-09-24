# Maestro development environment contract

One preflight command applies this contract to a selected development feature. It reports every category as pass, fail, excluded with reason, or unverified. A category is never silently omitted. The baseline environment may pass before the Maestro service exists; service-dependent checks become applicable for features that require it. Preflight reports all failures together and blocks only affected work.

| Category | Evidence and required check |
|---|---|
| Host and tools | Actual Linux host identity, versions of Git, Python, agent tools and baseline runner, resource and filesystem availability. |
| Source and workspace | Accessible repository at an exact revision, clean isolated workspace, allowed mounts, read/write permissions and reusable known-good reset. |
| Identity and credentials | Non-secret Owner and service account status; selected tool authentication, including Claude OAuth expiry if Claude is selected. Never print tokens. |
| Agent routes | Read actual `agents.toml`; verify selected role, exact tool/model, credential and settings profiles, egress destinations, capabilities, launch, observed identity, output and clean exit. |
| GitHub and test targets | Required read/write access to the actual repository and test destination; verify GitHub app permissions including Administration: read only where an operation requires it. Prove write access separately from permission flags with a real write that leaves no lasting change. |
| Service and network | When applicable, installed revision, service state, ports, persistent store and dependencies. Before service delivery, report these checks as excluded with reason. |
| Install and upgrade | Installation and version procedure for the selected feature; exact revision, preservation of settings, upgrade and rollback path when applicable. The automatic upgrade in `deploy/upgrade.py` installs only a passed `master` revision, keeps settings, runs post-install checks and restores the backup on failure. |
| Data and migration | Realistic isolated test data, migration and schema compatibility when applicable, known reset of run-owned data, and protection of unrelated records. |
| Observability and smoke | Logs and receipts sufficient to diagnose start, failure and clean exit; a small real smoke check and its repeat at milestone start. Inspect any existing host-local Claude Code task runner and Slack progress route; record command, credentials status, stop/restart behavior and an actual delivered receipt before treating them as available. A local durable notification row is not a Slack delivery. |

The preflight entry point, output shape and any missing checks are implementation work in [Verify the Maestro development environment](../planning/features/verify-development-environment.md). For a milestone that changes the installed service or CLI, the delivery rules require an installation of the verified master revision and post-install smoke checks, which the automatic upgrade performs for a `master` commit tagged `passed/*`. Never turn an unverified external permission or route into a passing result.
