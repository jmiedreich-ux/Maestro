# Maestro — Current Project Handoff

**Status:** Alpha-01 and Alpha-02 are complete and merged. Alpha-02's exact independently approved implementation head is `4a0ccc7d8bdaad6a8ac58fc9e3e6cd6e208a00fe` on verified base `06c81b8030140cca6001bc1514aabb8152c77dca`. No Alpha-03, real worker, API/UI, Foundry, VennueSign, project registration, project-adapter, GitHub automation, or USB-recovery implementation is authorized by this handoff.

**Alpha-03 planning only:** On 2026-08-31, the Owner approved the fixture-only
[Alpha-03 — Synthetic Project Discovery and Binding Proposal](../../docs/planning/proposed/alpha-03-synthetic-project-discovery.md)
for independent Decision Fidelity Review. The initial review returned a
correction-only request to carry every exact M0-D02 binding fact and prove Q2
completeness against that fact set. It remains non-executable and does not
authorize implementation, real repository discovery, Foundry/VennueSign
contact, registration, a project binding, or any other successor work.

**Alpha pre-build review:** [Maestro Alpha Decision-Fidelity Review](../../docs/planning/maestro-alpha-decision-fidelity-review.md) records the owner-approved synthetic-only Alpha layout and mandatory `maestro run-packet` boundary. M0-D01 now explicitly removes Atlas command requests: Atlas is strictly read-only and never a command caller. M0-D07 records an approved USB physical-provisioning deferral: Alpha may build backup-health support, but Alpha recovery acceptance remains blocked until the documented mount convention and real backup/restore evidence exist. The review itself authorizes no application code.

## What is now established

Maestro remains a standalone, project-neutral development-operations system. It will coordinate an agent-driven specialist workforce from project-approved architecture/work graphs, while keeping repository/GitHub as the project’s design/code/task authority and Maestro’s database as operational state.

The current M0 expansion is captured in:

- [Master Plan](../../docs/planning/maestro-master-plan.md)
- [Agent Workforce Control Plane](../../docs/planning/agent-workforce-control-plane.md)
- [M0 Source Inventory and Capture Register](../../docs/planning/m0-source-inventory.md)
- [Agent-workforce planning source capture](../../sources/planning/2026-08-29-agent-workforce-conversation.md)
- [Independent planning capture audit](../../docs/planning/agent-workforce-capture-audit.md)
- [Atlas Transition Assessment](../../docs/planning/atlas-transition-assessment.md)
- [Agent Role Library](../../docs/agents/)

## Decisions to preserve

1. A fresh project Architecture Agent reads a project handoff and approved authority, proposes a versioned work-graph release, and never directly dispatches or implements work.
2. Maestro is the development manager. It projects approved graph nodes into specialist planned queues, calculates the dispatchable subset, leases compatible work, and moves results through Integration, independent review, and the project’s acceptance/merge policy.
3. The planned queue is visible even when entries are future, blocked, or waiting. A later item may run before a blocked earlier one only when the approved graph and locks explicitly permit it.
4. Integration is a first-class queue and may be promoted when it safely unlocks capacity. If it changes code, a different reviewer reviews the integrated result.
5. Atlas is a live read/projection interface—not a controller, editable plan, task tracker, code editor, or direct database client.
6. Every coding agent follows the project-bound Maestro SOP. Independent review is proportional to risk but required for every mergeable PR and high-risk shared boundaries before downstream use.
7. V1 remains one approved milestone, one hosted worker, one draft PR, and owner acceptance/merge. Agent-workforce queues and limited parallel dispatch begin no earlier than V2.
8. Before Maestro executes a plan, milestone, packet, or build instruction, a separate Maestro Decision Fidelity Reviewer must trace every accepted governing choice into that proposal. Missing, changed, assumed, conflicting, or unapproved-deferred choices block execution. This review occurs before plan approval, before build instructions, and before milestone acceptance; it does not replace independent code review.
9. Every material quality requirement must be bounded before dispatch under [M0-D12](../../docs/planning/decisions/m0-d12-bounded-quality-contracts.md): protected outcome, operating/threat/failure model, explicit exclusions, practical assurance level, sufficient acceptance proof, permitted implementation boundary and complexity, proportionality ceiling, and exact stop/escalation rule. Passing the named proof is enough. A materially incomplete quality contract is an Architecture/Owner issue, not an unlimited worker-correction loop.
10. Independent review is full once. After a correction, the same independent reviewer normally performs a targeted follow-up limited to the named findings, correction-only diff, and directly affected consistency. Full review restarts only for a recorded base/range, unrelated-scope, shared-contract, evidence, or independence change.
11. Every default-branch merge must have complete current review coverage: one exact full reviewed range plus every targeted-reviewed correction-only diff covering the exact final head. Uncovered or materially stale changes block merge.

## VennueSign adapter guardrails

- The current VennueSign handoff summarizes Architecture Renewal Sessions 1–2; its complete versioned renewal authority must be landed in VennueSign before related implementation nodes become dispatchable.
- GitHub Issues/PRs remain its actual task and delivery records. The graph uses stable node links; Maestro does not create a competing backlog.
- Current policy permits parallelism only among independent packets within one active milestone. Shared contracts, DI, migrations, fixtures, workflows, tracker/status, and handoff retain their declared ownership/locks.
- An AI-friendly source-affordance refactor may be proposed as planning work first. M0 does not change VennueSign source to make it agent-friendly.

## Alpha-01 and Alpha-02 completion

[Alpha-01 — Establish Local Foundation](../../docs/planning/packets/alpha-01-local-foundation.md)
is complete and merged to `master` at
`4cc8e6fa899574e27515f225be1976c9f9f1a6ff`. The accepted implementation is branch
`alpha-01-r2-complete-foundation` at exact head
`3124378f3ba885cb066d1426b1a0ed5a5d0ccb6f`, based on verified R1 commit
`e2c8a08f06fc887abc07e2dc5341f88346b9b8f9`. Its R2 diff changed only
`services/maestro/maestro/storage.py` and
`tests/alpha_01/test_local_foundation.py`. Fresh Independent Implementation
Review returned **APPROVE** for that exact head. All 11 tests and both repeated
health checks passed with foreign keys enabled, WAL active, and schema version
`1`. Generated runtime/test artifacts were cleaned only inside the isolated R2
worktree afterward.

The [Alpha-01 Done Record](../../docs/planning/done/alpha-01-local-foundation.md)
preserves the acceptance evidence and bounded exclusions. In particular, Alpha
makes no post-directory-FD same-UID/root containment claim under M0-D11/M0-D12.

[Alpha-02 — Establish Synthetic `maestro run-packet` Lifecycle Wrapper](../../docs/planning/packets/alpha-02-run-packet-lifecycle-wrapper.md)
is complete and merged through exact implementation head
`4a0ccc7d8bdaad6a8ac58fc9e3e6cd6e208a00fe` on verified base
`06c81b8030140cca6001bc1514aabb8152c77dca`. Fresh Independent
Implementation Review returned **APPROVE** for that complete exact range and
confirmed all 16 changed paths were packet-owned. All 11 Alpha-01 tests, all 7
Alpha-02 tests, and the required successful `maestro run-packet` command
passed. Review artifacts were cleaned inside the isolated implementation
worktree and the branch remained clean.

The [Alpha-02 Done Record](../../docs/planning/done/alpha-02-run-packet-lifecycle-wrapper.md)
preserves the exact review, scope, check, and exclusion evidence. The wrapper
records its independent-review handoff and stops; it does not perform review,
merge, automatic correction, or successor selection.

There is no executable successor packet. Alpha-03 and all other implementation
increments require their own Architecture, Owner, Decision Fidelity, and
implementation authority. Do not start Alpha-03, real worker dispatch,
Atlas/API/UI, project registration or integration, GitHub automation, or USB
recovery work from this handoff.

## Open implementation decisions

- SQLite schema, backup, recovery, and retention mechanics.
- Post-Alpha project registration/bootstrap mechanics.
- Atlas read-only presentation and service-mediated API implementation.
- Least-privilege service-account/GitHub App/cloud-provider credential and webhook-security policy.
- Notification/acknowledgement model and measurable concurrency/cost thresholds.
- Future delegation boundary for auto-merge and autonomous selection of subsequent approved work.
