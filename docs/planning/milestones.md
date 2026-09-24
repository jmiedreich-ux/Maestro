# Maestro development milestones

Milestones here are checkpoints for building Maestro, distinct from milestones the product may create for registered projects. Only the next checkpoint is detailed.

## Closed checkpoint: reliable project questions and answers

**Accepted 2026-09-24 under the autopilot's delegated authority; tagged `passed/reliable-project-questions-and-answers`, merge revision `ced2ec2`.** The installed terminal answered real service-held questions: choice and information, explicit send, a lost acknowledgment with one saved answer, a cancelled question, follow-up, switch, exit and reopen. Fixes: wrapped status text, a plain closed-question message, cleared error on project switch. The [accepted exceptions](../outcomes/cli.md#acceptance-criteria-2) are listed in the Result column. Feature: [Close the gaps in answering project questions](features/reliable-answers-gaps.md).

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
