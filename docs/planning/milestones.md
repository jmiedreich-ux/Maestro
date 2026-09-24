# Maestro development milestones

Milestones here are checkpoints for building Maestro, distinct from milestones the product may create for registered projects. Only the next checkpoint is detailed.

## Closed checkpoint: establish the project's architectural foundations

**Accepted 2026-09-24 under the autopilot's delegated authority; merged to master and tagged `passed/establish-the-projects-architectural-foundations`; installed at `fff52cc` (upgrade timer, service active).** From the terminal, `/architecture start` on a confirmed real project reserved it and started a persistent architect session. A real Codex architect investigated real code and saved and published findings, project structure, a decisions snapshot and specialist role and context files; killed agents and service restarts resumed the same conversation, and a Claude Code architect resumed its session after rejected output. The [accepted exceptions](../outcomes/architecture-loop.md#establish-the-projects-architectural-foundations) (context-limit handling, a live Owner answer and replacement session, findings not named in decisions) are in the Result column. Feature: [Start the architecture loop and save project foundations](features/architecture-foundations.md).

## Closed checkpoint: recover a registration without losing decisions or exceeding limits

**Accepted 2026-09-24 under the autopilot's delegated authority; merged to master and tagged `passed/recover-registration-without-losing-decisions-or-exceeding-limits`.** With real agents on the installed service, three service restarts and a killed agent unit resumed or paused a registration with its decisions and review count kept; the two-attempt automatic limit, manual Retry activity, Retry publication after a refused branch, lost acknowledgments and the Owner's extra-review decision all worked. The [accepted exceptions](../outcomes/registration.md#recover-registration-without-losing-decisions-or-exceeding-limits) (context capacity, a registration-level timeout run, publication retries outside the attempt count, changed-path check) are in the Result column. Feature: [Recover a registration](features/recover-a-registration.md).

## Closed checkpoint: update a registration without losing approved history

**Accepted 2026-09-24 under the autopilot's delegated authority; merged to master and tagged `passed/update-a-registration-without-losing-approved-history`.** A real Codex architect and Claude reviewer re-registered an idle registered project: the update was refused while work was unfinished, inherited the earlier selections, showed a comparison before confirmation, could be cancelled with the earlier version kept, and confirmed only the exact candidate, with version 1 still in GitHub. The [accepted exceptions](../outcomes/registration.md#acceptance-criteria) are in the Result column. Feature: [Update a registration through the service and CLI](features/update-a-registration.md).

## Closed checkpoint: register and confirm a project through the CLI

**Accepted 2026-09-24 under the autopilot's delegated authority; merged to master and tagged `passed/register-and-confirm-a-project-through-the-cli`.** A real Codex architect and Claude reviewer assessed real repositories through the service; the Owner answered questions, confirmed scope, handled a planning-input change, cancelled, and confirmed in the terminal, and the package and receipt were published to GitHub. The [accepted exceptions](../outcomes/registration.md#acceptance-criteria) are in the Result column.

## Closed checkpoint: apply shared process definitions

**Accepted 2026-09-24 under the autopilot's delegated authority; code merged and installed at `ae62ddd`, outcome tagged `passed/apply-shared-process-definitions`.** The installed service had no schema bundles and never read the process sections; it now ships both bundles (added by the release upgrade), validates the registration and architecture sections, reports them to the Owner, holds an invalid process alone, saves the definition with each activity and gives assignments their limits from it. Proved with a real Codex run (45-second limit from the definition, timed out) and a real Claude Code run (1800 seconds, 2 recoveries), an edit between activity starts, and a missing and changed bundle. The [accepted exceptions](../outcomes/runtime-service.md#acceptance-criteria) (outputs, review, confirmation, Owner limit decisions) wait for the registration and architecture outcomes. Feature: [Apply process definitions in the installed service](features/apply-process-definitions.md).

## Closed checkpoint: run and recover assigned agents

**Accepted 2026-09-24 under the autopilot's delegated authority; code merged at `fc37e03` and installed (tag `passed/stop-agent-runs-completely`), outcome tagged `passed/run-and-recover-assigned-agents`.** On the installed service a real Codex architect and a real Claude Code reviewer ran, saved and validated results; an invalid review was rejected and recovered once; a real stop, a timeout and a killed service all ended with the agent's processes and system unit gone and no duplicate run. Stopping first left the agent's system unit running; that was fixed. The [accepted exceptions](../outcomes/runtime-service.md#acceptance-criteria) (context continuation, usage readings, late-result injection, reboot) are in the Result column. Feature: [Run and record assigned agents in the service](features/run-agents-from-the-service.md).

## Closed checkpoint: reliable project questions and answers

**Accepted 2026-09-24 under the autopilot's delegated authority; tagged `passed/reliable-project-questions-and-answers`, merge revision `ced2ec2`.** The installed terminal answered real service-held questions: choice and information, explicit send, a lost acknowledgment with one saved answer, a cancelled question, follow-up, switch, exit and reopen. Fixes: wrapped status text, a plain closed-question message, cleared error on project switch. The [accepted exceptions](../outcomes/cli.md#acceptance-criteria) are listed in the Result column. Feature: [Close the gaps in answering project questions](features/reliable-answers-gaps.md).

## Closed checkpoint: connected multi-project CLI workspace

**Accepted 2026-09-24 under the autopilot's delegated authority; tagged `passed/connected-multi-project-cli-workspace` and installed at `1d85486`.** The installed terminal was driven on a real pty against three real service-held projects: startup, unreachable and retry, overview ordering, selection, notices and attention navigation, history, inline findings, disconnect and automatic reconnect, resize, keyboard, credential failures and help. The [accepted exceptions](../outcomes/cli.md#acceptance-criteria) list what waits for registration and agent runs. Feature: [Close the gaps in the connected CLI workspace](features/cli-workspace-gaps.md).

## Closed checkpoint: connect the CLI to recorded service activity

**Accepted 2026-09-24 under the autopilot's delegated authority; no code changed.** The installed terminal and its connection client were run against a disposable copy of the installed service: empty and unreachable states, real activity, event replay after disconnect and `kill -9` restart, heartbeats, credential errors and automatic reconnection. The [accepted exceptions](../outcomes/runtime-service.md#connect-the-cli-to-recorded-service-activity) list what waits for registration and agent dispatch.

## Closed checkpoint: preserve project activity and requests

**Accepted 2026-09-24 under the autopilot's delegated authority.** Storage, identities, repeated and conflicting requests, cross-project refusal and restart recovery were observed working on a disposable copy of the installed service, and the atomic project start reservation was built and contention-proven. The [accepted exceptions](../outcomes/runtime-service.md#acceptance-criteria) list what waits for later outcomes: agent-run status in the idle check, real findings and allowances, and performance records. Feature: [Reserve a project start atomically](features/project-start-reservation.md).

## Closed checkpoint: operate the persistent Maestro service

**Accepted by the Owner on 2026-09-24 with recorded limitations.** The installed service, its accounts and permissions, startup failure reporting and Owner access were observed working. The [accepted exceptions](../outcomes/runtime-service.md#acceptance-criteria) list what is deferred: observing boot and crash restart, and validating agent routes at startup.

## Closed checkpoint: verified Maestro development environment

**Accepted by the Owner on 2026-09-24.** Evidence is in the [prerequisite pass](prerequisite-pass.md).

**Outcome:** On the actual Linux host, a developer can run one complete feature preflight and a real agent in a clean, repeatable workspace, with clear reports for missing prerequisites. This closes [Prepare a verified development environment](outcomes.md#ordered-outcomes) only after installed evidence is captured.

**Feature:** [Verify the Maestro development environment](features/verify-development-environment.md).

**Entry:** Use the [prerequisite pass](prerequisite-pass.md) and [single environment contract](../development-process/environment-contract.md). Assess existing deployment, route, workspace and test code for reuse before editing. Confirm actual host and repository access and choose a real agent route and baseline check. Unknowns are unverified; expose blockers without claiming acceptance.

**Assembled QA:** At milestone start, rerun the full applicable preflight and record the smoke result. From a clean workspace, record the one preflight's full applicable check set, host/tool versions and non-secret access status. Launch the agent against a pinned source, inspect its real output and clean exit, run the baseline check, reset run-owned data and repeat. In a safe test setup, remove an applicable prerequisite and verify the preflight reports it and blocks dispatch, then restore it. A mock agent or file-presence check cannot pass.

**Integration and close:** Work on a feature branch, integrate to `milestone/verified-development-environment`, run assembled QA and outcome review, and promote the passed checkpoint to master under the [delivery rules](../development-process/delivery-rules.md). The Owner directed features to be merged straight to master, so no milestone branch was published. After closing, assess [Operate the persistent Maestro service](../outcomes/runtime-service.md#operate-the-persistent-maestro-service), against existing code and installed behavior and plan the next needed checkpoint. Continue in roadmap order; previously implemented code is considered for reuse, not accepted without evidence.
