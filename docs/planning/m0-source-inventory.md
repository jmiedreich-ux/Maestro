# Maestro M0 — Source Inventory and Capture Register

**Status:** active M0 record. This register preserves the source material and atomic agreements reconciled into Maestro planning. It is a capture and traceability record, not authorization to implement a runner.

## Source inventory

| ID | Source | Role in M0 | Capture status |
|---|---|---|---|
| S-01 | Maestro Alpha 1 planning capture | Original project-neutral coordinator, wrapper, Linux-first, and staged-delivery direction | Reconciled into the master plan and this register |
| S-02 | VennueSign's proposed `maestro-dev-lead-agent-framework.md` | Earlier dev-lead lifecycle, worker qualification, integration, and staged-delivery design | Reconciled; project-specific rules remain in VennueSign |
| S-03 | Packet lifecycle / wrapper record | Concrete packet compile, dispatch, grading, targeted-rework, and evidence loop | Reconciled into the Worker Wrapper and Coding Agent SOP |
| S-04 | Local-agent qualification notes | Routing evidence, worktree, verification, and serialized-resource safeguards | Reconciled; initial limits remain conservative |
| S-05 | `jmiedreich-ux/Atlas` at `48fb14f` | Existing planning/reporting record surface and write-back behavior | Assessed in [Atlas Transition Assessment](atlas-transition-assessment.md) |
| S-06 | Foundry control-library, agent-guide, and design-to-skin records | Reference for structured agent instructions; not Maestro product scope | Captured as reference only |
| S-07 | VennueSign Architecture Renewal handoff and approved project records | Example adapter authority, preservation rules, and current project-policy constraints | Referenced only; not moved into Maestro as VennueSign authority |
| S-08 | [Agent-workforce planning conversation, 2026-08-29](../../sources/planning/2026-08-29-agent-workforce-conversation.md) | Architecture Agent, Maestro manager, specialist queues, Atlas control plane, parallelism, SOP, integration, review, and handoff requirements | Source-preserved and reconciled into the Control Plane and this register |

## Original M0 agreements retained

| ID | Agreement | Destination / status |
|---|---|---|
| C-01 | Maestro is a separate, project-neutral development-operations system, not part of Foundry or Vennue. | Master Plan §1 |
| C-02 | Maestro starts on the Linux AI box. | Master Plan §2 / Control Plane §4 |
| C-03 | Initial durable operational state is SQLite on the AI box. | Master Plan §3; exact schema/backup remains open |
| C-04 | Atlas moves from a live GitHub-polled dashboard to a local operational surface over Maestro state. | Amended by C-30: reporting plus audited command requests, never direct write-back |
| C-05 | Repository plans, code, PRs, reviews, and CI remain versioned engineering authority. | Master Plan §2 / Control Plane §3 |
| C-06 | Maestro's database holds observed execution state, ownership, attempts, evidence, retries, notifications, and waits. | Master Plan §3–4 / Control Plane §3 |
| C-07 | No two independently writable truths exist for one fact; repository/GitHub facts are projected, not copied as authority. | Control Plane §3 |
| C-08 | Each project supplies an adapter: repo, branch policy, commands, environments, credential references, architecture rules, and exceptions. | Master Plan §3 / Control Plane §12 |
| C-09 | Maestro supplies common lifecycle, evidence, review, retry, locks, notifications, performance records, and process rules. | Master Plan §§3–7 |
| C-10 | New projects use a first-class bootstrap flow; existing projects use a register flow that preserves existing rules. | Master Plan §5 / implementation design remains open |
| C-11 | A project foundation is approved before feature planning. | Master Plan §5 |
| C-12 | Plans, questions, decisions, milestones, packets, and coverage use one versioned schema, not free-form agent prose. | Master Plan §5 |
| C-13 | A planning conversation is registered, atomically captured, and checkpointed; an unstructured summary alone is insufficient. | Master Plan §5 / this register |
| C-14 | Every intake item traces to a requirement, decision, task, question, explicit deferral, or N/A record. | M0 acceptance gate / capture audit |
| C-15 | Every roadmap task has a short, plain, action-oriented subject. | Master Plan §6 |
| C-16 | Every task records planned execution location, agent role/type, intended model/class, reviewer route, and later factual run details. | Master Plan §6 / Control Plane §§6 and 11 |
| C-17 | Cloud coordination delegates suitable bounded implementation, test, indexing, and documentation work to local agents. | Master Plan §2 / Control Plane §11 |
| C-18 | Cloud models handle intake, planning, contracts, integration, high-judgment fixes, and independent review. | Master Plan §2 / Control Plane §11 |
| C-19 | Known pending work immediately records worker, start, expected result, next allowed action, timeout/retry policy, and blocking gate. | Master Plan §§3–4 |
| C-20 | Completion advances through polling first; webhooks are a later optimization. | Master Plan §4 / Control Plane §12 |
| C-21 | Transitions are idempotent and recoverable after restart, duplicate poll, timeout, or stale completion. | Master Plan §4 / Control Plane §7.4 |
| C-22 | One milestone is the initial boundary; a run stops for owner acceptance/merge. Multi-milestone autonomy requires later explicit approval. | Master Plan §9 / Control Plane §13 |
| C-23 | Murphy is a distinct Azure/deployed-environment QA capability, manually triggered under project policy. | Master Plan §8 / Control Plane §4 |
| C-24 | Murphy receives environment, deployed version, and scoped credentials; it returns report, issues, and structured run result. | Master Plan §8 |
| C-25 | M0 is planning/consolidation only; it does not build the runner. | Master Plan §9 / Control Plane §13 |

## Agent-workforce agreements added by S-08

| ID | Agreement | Destination / status |
|---|---|---|
| C-26 | The development organization is agent-driven; roles are fresh-agent contracts rather than permanent chat personas. | Control Plane §§1–2 / Role Library |
| C-27 | A project Architecture Agent reads its handoff and approved authority, resolves/plans a stated subject, and updates versioned project planning records only after required approval. | Control Plane §§5–6 / Architecture Agent contract |
| C-28 | Maestro is the development manager: a cloud-reasoning-capable coordinator paired with a local service-account runtime, polling first and later able to observe webhooks. | Control Plane §§4, 7.4, 11 / Manager contract |
| C-29 | Specialist roles are tied to architectural boundaries; generic contracts live in Maestro and project overlays name their specific authority, paths, invariants, and gates. | Control Plane §5 / `docs/agents/` |
| C-30 | Atlas is the operational control-plane interface. It projects Maestro state and submits authenticated, audited, policy-checked command requests; it does not directly edit the DB, architecture, GitHub, code, or branch state. | Control Plane §§3, 10 / Atlas assessment |
| C-31 | A specialist queue is an owner-visible planned ordered workload, including future, blocked, and waiting work. Its dispatchable queue is a calculated subset, not a blind FIFO. | Control Plane §7 |
| C-32 | Later independent work may bypass a blocked earlier item only when the approved graph explicitly proves it has no hard/serial dependency and no conflicting lock. | Control Plane §§6–8 |
| C-33 | Parallelism is the default for independent packets; declared dependencies, shared boundaries, integration, and finite resources serialize work. | Control Plane §8 |
| C-34 | Integration is a first-class queue. It validates/assembles worker results, is promoted when it safely unlocks downstream capacity, and routes changed integration work to a different independent reviewer. | Control Plane §8 / Integration contract |
| C-35 | Every coding agent follows a common SOP bound to the joined project's stricter engineering rules. Specialist overlays can add requirements, never weaken them. | Control Plane §9 / Coding Agent SOP |
| C-36 | Independent review is proportionate: no full review for every internal micro-step, but every mergeable PR is independently reviewed and high-risk shared outputs are reviewed before downstream consumption. | Control Plane §9 / Review contract |
| C-37 | Atlas may show and request an allowed actual agent/model route, capacity, and temporary override. Durable policy remains versioned and actual run selection stays an operational fact. | Control Plane §§10–11 |
| C-38 | Before specialist execution, an Architecture Agent may propose an AI-friendly source-affordance refactor: clear module boundaries, smaller cohesive units, accurate area maps, stable contracts, and explicit ownership. | Control Plane §12; M0 plans only |
| C-39 | VennueSign must supply a versioned renewal-authority bundle before renewal implementation nodes are dispatchable; a handoff summary or Library-only record is not enough. | Control Plane §12 |
| C-40 | Current VennueSign policy permits only one active milestone. Parallelism is limited to independent packets inside that milestone until its project policy changes. | Control Plane §12 |
| C-41 | Actual VennueSign work remains GitHub Issues/PRs. Architecture graph nodes link by stable ID; Maestro and Atlas never maintain a competing task tracker. | Control Plane §§3, 6, 12 |
| C-42 | Eventual Maestro merge and autonomous next-work selection require a separately reviewed delegation policy. This document merge does not grant product-code merge authority. | Control Plane §13 |

## Required diagram concepts retained

| Source concept | Current representation |
|---|---|
| Coordinator loop: observation → durable coordinator → queue/ledger → worker → verify/review → Atlas | Master Plan §3 and Control Plane §4 |
| Authority flow: project/GitHub facts → operational projection ← worker execution state; Atlas reads/control-requests | Control Plane §§3–4 and §10 |
| Planning gate: foundation → feature discovery/design → approved milestone/packet → implementation | Master Plan §5 |
| Wrapper loop: author → compile constraints → dispatch → grade → one targeted rework → evidence → invariant improvement | Master Plan §7 / Coding Agent SOP |
| Planned specialist queue versus dispatchable subset and integration unblocking | Control Plane §7 |
| Full target packet lifecycle | Control Plane §8.4 |

## Conversation-to-record traceability

| Planning requirement | Recorded in |
|---|---|
| Architecture Agent reads a handoff and discusses the designated subject before approved project updates | `docs/agents/architecture-agent.md`; Control Plane §5.2 |
| Maestro assigns specialists, tracks completion, routes Integration → Review → merge policy | `docs/agents/maestro-development-manager.md`; Control Plane §§5, 8 |
| Per-specialist queues reveal four Theme Studio jobs, one Screens job, and Integration backlog even while some are blocked | Control Plane §7 |
| Independent later queue work may run while a prior item awaits Integration | Control Plane §§7.2–7.4 |
| Atlas provides top-level routing/model/control visibility without becoming an authority fork | Control Plane §10; Atlas Transition Assessment |
| SOP and proportionate independent review govern every coding packet | Control Plane §9; `docs/agents/coding-agent-sop.md`; `docs/agents/independent-review-agent.md` |
| M0 remains design-only and V1 remains a deliberately narrow, owner-gated loop | Master Plan §9; Control Plane §13 |

## Current M0 next action

The independent [planning capture audit](agent-workforce-capture-audit.md) has passed. Resolve or explicitly defer every remaining open implementation decision, prepare the M0 acceptance record, then obtain the project’s required M0 implementation authorization. Do not implement coordinator, database, worker, Atlas migration, VennueSign adapter, or specialist dispatch merely because this record is complete.
