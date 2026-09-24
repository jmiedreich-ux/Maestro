# Maestro development milestones

Milestones here are checkpoints for building Maestro. They are distinct from milestones the product may create for a registered project. Only the next assembled checkpoint is detailed.

## Planned checkpoint: connected initial project registration

**Outcome:** In an installed terminal workspace, the Owner can submit real project sources, inspect an independently reviewed and published candidate, explicitly confirm its exact revision, and retrieve the active package after reconnect. This advances [roadmap outcome 9](outcomes.md) and does not mark earlier foundations delivered without their connected evidence.

**Features in dependency order:**
1. [Start registration from the connected workspace](features/start-registration-from-workspace.md).
2. [Review and publish a registration candidate](features/review-and-publish-registration-candidate.md).
3. [Confirm and activate the exact registration](features/confirm-project-registration.md).

**Entry gate:** Assigned feature owners first run the applicable [environment preflight](../docs/outcomes/development-environment.md), inspect current source and tests, and record exact reusable and adapted paths. Prove installed Linux service, persistent database, Owner identity, real architect and distinct reviewer routes, sandbox mounts, authorized test GitHub read/write access, test repository and reset, and log visibility. Unknowns remain blockers to affected claims. The three features may progress only in dependency order; an assembled QA gate follows them.

**Assembled QA:** On an isolated installed target, use real routes and a real test repository and publication destination. Start and resume registration through CLI and service; compare pinned source and assessment with the reviewer evidence, published commit, confirmation receipt, SQL active reference and retrievable package. Exercise invalid input, unavailable route, duplicate request, bounded correction exhaustion, changed source or destination, cancellation, interrupted publication, uncertain confirmation acknowledgment and restart. Confirm no registration action starts architecture, graph work or Execution. Capture command output, service events, route identities, source and published revisions, persistent records and correction outcomes. An unproved external effect fails the checkpoint.

**Integration and close:** Feature branches integrate in order to `milestone/connected-initial-registration` under the [delivery rules](../docs/planning/manual-architecture/packet-rules.md). Run assembled QA and outcome review on that branch; promote the passed checkpoint to master and record the result. The branch is a planned integration target, not evidence that it exists or QA has passed. After close, detail the next dependent registration update/recovery or architectural foundation feature based on verified gaps; do not preallocate another milestone.
