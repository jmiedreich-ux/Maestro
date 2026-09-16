# Common Coding Agent Instructions

These shared rules apply to every coder. Follow [AGENTS.md](../../AGENTS.md), the project's engineering policy and the exact work packet. A specialist role adds source-area knowledge and constraints; it references these rules without duplicating or weakening them.

## Before changing files

Read the packet, applicable specialist role and context, exact source revision, permitted paths, dependencies, resources and required checks. Use the assigned workspace and authorized Git delivery method.

Return the [implementation plan](../architecture.md#returned-implementation-plan) through the service before changing files. The service saves it and makes it available to the CLI and Development Manager. Continue without a separate plan-approval gate unless a material conflict or missing prerequisite blocks the work; report that blocker.

## Implementation

- Change only the assigned scope; preserve architecture, conventions and required behavior.
- Follow the assigned quality boundary without strengthening requirements or adding adjacent work.
- Use basic, meaningful checks under the [verification expectations](../planning-guide/README.md#verification-expectations).
- Do not merge, deploy, expose credentials, bypass controls or assume an Owner decision.

## Result and handoff

Return a structured result through the service containing:

- What changed and how it meets the packet's expected outcome.
- Exact source and result revisions, with changed files.
- Verification commands, results and supporting evidence.
- Known limitations, blockers, unfinished work and downstream effects.

Report required outcomes honestly as `PASS`, `N/A` with a reason, or `UNTESTED` with its consequence. The service validates the result and referenced artifacts, records them and notifies the Development Manager.

A completion claim means ready for the next review step. It does not complete the packet, approve the coder's own work or authorize merging.

## Corrections

Apply only authorized corrections within the packet's scope. Follow [independent implementation review](../architecture.md#independent-implementation-review) and the configured accounting under [packet and integration-change review limits](../architecture.md#packet-and-integration-change-review-limits). This file adds no separate allowance. Report conflicting instructions, insufficient scope or missing authority rather than inventing a rule.
