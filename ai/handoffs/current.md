# Maestro — Current Project Handoff

**Status:** Alpha-01 through Alpha-03 are complete. Alpha-03's official Local
Qwen implementation is accepted at exact corrected head
`f21e4a2ff25cead8b972b4433da33f0e9910efc5` by explicit Owner closeout on
2026-09-01. The later Qwen rerun is benchmark evidence only. Alpha-04 planning
and its reporting amendment are merged, but Alpha-04 is paused by the Owner and
has no execution packet or implementation release. No real worker, API/UI,
provider-account access, Foundry, VennueSign, real project registration,
project-adapter, GitHub automation, or USB-recovery implementation is
authorized by this handoff.

**Alpha-03 complete:** The fixture-only [Alpha-03 architecture plan](../../docs/planning/proposed/alpha-03-synthetic-project-discovery.md)
and [R2 execution packet](../../docs/planning/packets/alpha-03-synthetic-project-discovery.md)
received their required planning approvals and merges. The official Local Qwen
implementation completed at `e3929c46882dbd0512bac377bdef1440d4e17cff`
with its targeted correction at
`f21e4a2ff25cead8b972b4433da33f0e9910efc5`. The full and targeted
implementation reviews returned `REQUEST_CHANGES`; all named commands passed,
but a conflicting empty required authority-path array remained accepted. On
2026-09-01 the Owner confirmed the official run was signed off and directed
closeout at `f21e4a2`. The [Alpha-03 done record](../../docs/planning/done/alpha-03-synthetic-project-discovery.md)
preserves that explicit Owner acceptance exception and the exact trusted-fixture
limitation. The benchmark head `e9a0a0196a019962f2f15095b8f492f62643e95e`
is not the accepted implementation.

**Alpha-04 paused:** On 2026-08-31, the Owner agreed that
Maestro must qualify its core assignment/control loop synthetically before a
real Foundry packet becomes the first whole-loop proving subject. Accepted
[M0-D13](../../docs/planning/decisions/m0-d13-synthetic-control-loop-qualification.md)
and the proposed
[Alpha-04 architecture plan](../../docs/planning/proposed/alpha-04-synthetic-control-loop-qualification.md)
preserve Alpha-03 unchanged and insert one fixture-only qualification after
Alpha-03 acceptance and before Foundry V1. The original plan received fresh
Decision Fidelity **APPROVE** at exact head
`0b416ac204a07285f2f5fe1f6e000c40a6f323b3` and merged in PR #11 at
`dcca2174dd919aa204707961f1b33ad15de9af41`.

The Owner then clarified that the Coordinator must make a patient bounded
request for a non-terminal worker's reported plan/current
step/blocker/ETA-or-unknown before assuming a stall or taking timeout/retry
action. Atlas may later report the durable status but never asks the worker.
The Owner also identified the earlier Usage & Observability proposal and
approved beginning its bounded allowance/context/usage subset under
[M0-D14](../../docs/planning/decisions/m0-d14-context-and-token-reporting.md):
record a supported ChatGPT/Codex weekly window when available, keep attempt
tokens distinct from allowance units, reconcile controlled/coarse/unattributed
usage, keep local Qwen capacity separate, and report unsupported facts as
`unavailable` without scraping. The combined amendment merged in PR #12 at
`b2594d9ab4cad528cd6272622f68162850a0584e`. The broader multi-provider,
live-adapter, UI, retention, threshold, and enforcement proposal remains
unresolved. No Alpha-04 execution packet exists. On 2026-09-01 the Owner
explicitly paused Alpha-04; do not draft, review, release, or implement it until
the Owner provides new direction.

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
- [Usage & Observability proposal](../../docs/planning/proposed/agent-usage-observability.md)
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
12. Before live Foundry V1 execution, Maestro must pass the M0-D13 fixture-only control-loop qualification. Alpha-04 may prove one synthetic assignment, patient worker-status inquiry, and role-separated handoffs, but production queues, real actor/model routing, and limited parallel dispatch remain V2 work. Atlas reports recorded worker status and never initiates the inquiry.
13. Under M0-D14, every attempt begins with honest context/usage preflight.
    Supported hosted weekly-window observations remain separate from tokens;
    controlled usage, coarse registered activity, and unattributed remainder
    reconcile visibly; local capacity stays separate; and Atlas only reports
    durable facts.

## VennueSign adapter guardrails

- The current VennueSign handoff summarizes Architecture Renewal Sessions 1–2; its complete versioned renewal authority must be landed in VennueSign before related implementation nodes become dispatchable.
- GitHub Issues/PRs remain its actual task and delivery records. The graph uses stable node links; Maestro does not create a competing backlog.
- Current policy permits parallelism only among independent packets within one active milestone. Shared contracts, DI, migrations, fixtures, workflows, tracker/status, and handoff retain their declared ownership/locks.
- An AI-friendly source-affordance refactor may be proposed as planning work first. M0 does not change VennueSign source to make it agent-friendly.

## Alpha-01 through Alpha-03 completion

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

[Alpha-03 — Synthetic Project Discovery and Binding Proposal](../../docs/planning/done/alpha-03-synthetic-project-discovery.md)
is complete by explicit Owner acceptance at exact official corrected head
`f21e4a2ff25cead8b972b4433da33f0e9910efc5`. Its fixture-only binding result is
available to the future Alpha-04 qualification. The done record preserves the
review outcomes and accepted malformed-conflict limitation without claiming an
independent-review approval.

There is no executable successor packet. Alpha-04 is explicitly paused and
requires new Owner direction before any packet drafting, review, release, or
implementation. Do not start Alpha-04, real worker dispatch, Atlas/API/UI,
project registration or integration, GitHub automation, or USB recovery work
from this handoff.

## Open implementation decisions

- SQLite schema, backup, recovery, and retention mechanics.
- Post-Alpha project registration/bootstrap mechanics.
- Atlas read-only presentation and service-mediated API implementation.
- Least-privilege service-account/GitHub App/cloud-provider credential and webhook-security policy.
- Notification/acknowledgement model and measurable concurrency/cost thresholds.
- Supported provider-account observation sources, usage retention, allowance
  warning thresholds, and any budget-enforcement policy.
- Future delegation boundary for auto-merge and autonomous selection of subsequent approved work.
