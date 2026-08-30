# Maestro — Current Project Handoff

**Status:** M0 planning expansion captured on 2026-08-29. No Maestro runtime, worker, queue database, Atlas migration, VennueSign code change, or product-code merge is authorized by this handoff.

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

## VennueSign adapter guardrails

- The current VennueSign handoff summarizes Architecture Renewal Sessions 1–2; its complete versioned renewal authority must be landed in VennueSign before related implementation nodes become dispatchable.
- GitHub Issues/PRs remain its actual task and delivery records. The graph uses stable node links; Maestro does not create a competing backlog.
- Current policy permits parallelism only among independent packets within one active milestone. Shared contracts, DI, migrations, fixtures, workflows, tracker/status, and handoff retain their declared ownership/locks.
- An AI-friendly source-affordance refactor may be proposed as planning work first. M0 does not change VennueSign source to make it agent-friendly.

## Exact next action

The independent capture audit has passed. The next Maestro planning session should resolve or explicitly defer the remaining implementation decisions and prepare the M0 acceptance record. Only after the appropriate project approval may V1 design/implementation begin.

## Open implementation decisions

- SQLite schema, backup, recovery, retention, and project registration/bootstrap mechanics.
- Atlas command API, authentication/authorization, and presentation implementation.
- Least-privilege service-account/GitHub App/cloud-provider credential and webhook-security policy.
- Review-round escalation cap, notification/acknowledgement model, and measurable concurrency/cost thresholds.
- Future delegation boundary for auto-merge and autonomous selection of subsequent approved work.
