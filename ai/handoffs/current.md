# Maestro — Current Project Handoff

**Status:** M0 planning expansion captured on 2026-08-29. No Maestro runtime, worker, queue database, Atlas migration, VennueSign code change, or product-code merge is authorized by this handoff.

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

## VennueSign adapter guardrails

- The current VennueSign handoff summarizes Architecture Renewal Sessions 1–2; its complete versioned renewal authority must be landed in VennueSign before related implementation nodes become dispatchable.
- GitHub Issues/PRs remain its actual task and delivery records. The graph uses stable node links; Maestro does not create a competing backlog.
- Current policy permits parallelism only among independent packets within one active milestone. Shared contracts, DI, migrations, fixtures, workflows, tracker/status, and handoff retain their declared ownership/locks.
- An AI-friendly source-affordance refactor may be proposed as planning work first. M0 does not change VennueSign source to make it agent-friendly.

## Exact next action

The owner approved the resolved Alpha decision-fidelity review and deliberately small layout on 2026-08-30. A fresh, separate Decision Fidelity Reviewer approved the current review at `5fc4b61`. [Alpha-01 — Establish Local Foundation](../../docs/planning/packets/alpha-01-local-foundation.md) remains paused. Its first packet-contract amendment exposed a second missing Linux-first rule: a runtime path that passed validation could be symlink-swapped before SQLite mutation. [M0-D11 — Linux Runtime Filesystem Boundary](../../docs/planning/decisions/m0-d11-linux-runtime-filesystem-boundary.md) is owner-approved and now controls: Maestro writes only under the repository's real physical `var/` tree, rejects symlink traversal, and must prevent validation-to-mutation escape. This is not a worker/model delivery failure or hard escalation. Run fresh Decision Fidelity Review on the amended packet; only an APPROVE authorizes a new bounded repair packet and then renewed independent implementation review.

## Open implementation decisions

- SQLite schema, backup, recovery, retention, and project registration/bootstrap mechanics.
- Atlas read-only presentation and service-mediated API implementation.
- Least-privilege service-account/GitHub App/cloud-provider credential and webhook-security policy.
- Notification/acknowledgement model and measurable concurrency/cost thresholds.
- Future delegation boundary for auto-merge and autonomous selection of subsequent approved work.
