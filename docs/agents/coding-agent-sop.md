# Common Coding Agent Instructions

Every implementation agent follows the repository-wide rules in [AGENTS.md](../../AGENTS.md), the joined project's engineering policy, and the exact approved work assignment.

## Before changing files

- Confirm the repository, exact source revision, approved work, role, allowed and prohibited paths, required checks, dependencies, resources, and handoff.
- Use the workspace and Git delivery method required by the project.
- Read the exact authority named by the work assignment.
- Stop if approval, authority, scope, dependencies, credentials, or verification requirements are missing or contradictory.

## Implementation

- Change only the approved scope.
- Preserve accepted architecture, conventions, and user behavior.
- Use real project verification rather than tests that only repeat implementation logic.
- Follow the approved quality boundary, including its operating model, exclusions, sufficient proof, implementation limit, and stop rule.
- Do not silently strengthen requirements or absorb adjacent work.
- Do not merge, deploy, expose credentials, bypass protections, or resolve an owner decision by assumption.

## Verification and handoff

Run the required checks without weakening them. Report changed files, commands and results, evidence, known gaps, downstream effects, and each required outcome as `PASS`, `N/A` with a reason, or `UNTESTED` with its consequence.

Hand the exact result to Integration. Do not approve your own work.

## Corrections

Perform at most one targeted correction for a work item, and only after the responsible authority approves the exact findings. Reassignment, replacement work, workspace movement, or takeover does not reset the allowance.

Limit the change and follow-up evidence to the approved findings and directly affected behavior. Stop and escalate when a new failure class, missing decision, shared-boundary conflict, unsafe condition, or exhausted correction allowance appears.
