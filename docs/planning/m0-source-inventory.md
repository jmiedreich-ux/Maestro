# Maestro M0 — Source Inventory and Capture Register

**Purpose:** Preserve the inputs and agreements that must be reconciled before the Maestro master plan is approved. This is a capture register, not authorization to implement Maestro.

## Source inventory

| ID | Source | Role in M0 | Status |
|---|---|---|---|
| S-01 | `meastro alpah 1 plan.txt` | Primary planning conversation; contains the newer system direction and staged M0 plan | Captured |
| S-02 | Vennue `maestro-dev-lead-agent-framework.md` | Earlier dev-lead lifecycle and staged-delivery design | Captured; reconcile |
| S-03 | `packet-lifecycle-example.md` | Concrete wrapper/packet lifecycle and enforcement loop | Captured |
| S-04 | `local-agent-notes.md` | Qualification evidence and wrapper safeguards | Captured |
| S-05 | `jmiedreich-ux/Atlas` at `48fb14f` | Existing planning/reporting implementation to assess and migrate | Captured; assessment pending |
| S-06 | Foundry control-library, agent-guide, and design-to-skin documents | Project-specific reference for structured agent instructions; not Maestro product scope | Captured as reference only |

## Captured agreements

| ID | Agreement | Type | Planned destination |
|---|---|---|---|
| C-01 | Maestro is a separate, project-neutral development-operations system, not part of Foundry or Vennue. | Decision | Charter |
| C-02 | Maestro runs first on the Linux AI box. | Constraint | Architecture |
| C-03 | Initial durable operational state is SQLite on the AI box. | Decision | Architecture / data model |
| C-04 | Atlas becomes a local reporting UI that reads Maestro operational state, not a live GitHub-polled dashboard. | Decision | Architecture / Atlas transition |
| C-05 | Repository plans, code, PRs, reviews, and CI remain the versioned engineering authority. | Boundary | Source-of-truth model |
| C-06 | Maestro's database holds observed execution state, ownership, attempts, evidence, retries, notifications, and waiting state. | Decision | Data model |
| C-07 | Do not create two writable truths for the same fact; GitHub/repository facts are ingested and projected rather than duplicated. | Constraint | Sync model |
| C-08 | Each project supplies adapters/configuration: repo, branch policy, commands, environments, credentials references, architecture rules, and project exceptions. | Requirement | Project-adapter contract |
| C-09 | Maestro supplies the common lifecycle, evidence, review, retry, locks, notifications, performance records, and process rules. | Requirement | Shared process |
| C-10 | New projects use a first-class bootstrap flow; existing projects use a register flow that preserves their existing rules. | Requirement | Bootstrap/register design |
| C-11 | A project foundation must be approved before feature implementation planning. | Gate | Planning lifecycle |
| C-12 | Plans, questions, decisions, milestones, packets, and coverage use one versioned schema rather than free-form agent prose. | Requirement | Planning schema |
| C-13 | A planning conversation is registered as input, atomically captured, and checkpointed; it is never trusted as an unstructured summary alone. | Requirement | Planning intake |
| C-14 | Every intake item must trace to a requirement, decision, task, question, explicit deferral, or not-applicable record. | Gate | Traceability validator |
| C-15 | Every roadmap task has a short, plain, action-oriented subject line. | Owner requirement | Task schema / Atlas UI |
| C-16 | Every task has planned execution location, agent role/type, intended model/class, independent reviewer route, and later factual run details. | Requirement | Task-routing model |
| C-17 | Cloud coordination delegates suitable bounded implementation, test, indexing, and documentation work to local agents. | Routing rule | Worker-routing policy |
| C-18 | Cloud models handle intake interpretation, planning, contracts, integration, high-judgment fixes, and independent review. | Routing rule | Worker-routing policy |
| C-19 | The system records known pending work immediately: worker, start, expected result, next allowed action, timeout/retry policy, and blocking gate. | Requirement | Execution state model |
| C-20 | Worker completion must advance from durable state via polling first; webhooks are an optional later optimization. | Decision | Coordinator design |
| C-21 | All transitions are idempotent and recoverable after restart, duplicate poll, timeout, or stale completion. | Requirement | Coordinator design |
| C-22 | One milestone remains the initial operating boundary; a run stops for owner acceptance/merge. Multi-milestone autonomy is a later, explicitly approved mode. | Guardrail | V1 operating boundary |
| C-23 | Murphy is a distinct Azure/deployed-environment QA capability, manually triggered under its current project policy. | Constraint | Murphy adapter |
| C-24 | Murphy receives environment, deployed version, and scoped credentials; it returns a report, issues, and structured run result. | Requirement | Murphy adapter |
| C-25 | M0 is planning/consolidation only; it does not build the runner. | Scope boundary | M0 roadmap |

## Diagrams that must be retained as source concepts

1. **Coordinator loop:** events or polling -> durable coordinator -> queue/task ledger -> worker -> verify/review -> update Atlas.
2. **Authority flow:** repository/GitHub facts -> Maestro database projection <- worker execution state; local Atlas reads the operational projection.
3. **Planning gate:** project foundation -> feature discovery/design -> approved milestone/packet plan -> implementation.
4. **Wrapper loop:** author packet -> compile permissions/checks -> dispatch -> grade -> one targeted rework -> record -> improve invariants.

## M0 roadmap agreed in the Alpha 1 source

| M0 item | Plain subject | Intended route |
|---|---|---|
| M0-01 | Create private Maestro repo and records | Cloud coordinator |
| M0-02 | Capture sources into traceability inventory | Cloud planning lead |
| M0-03 | Define shared process and planning schema | Cloud architecture/planning lead |
| M0-04 | Define Maestro, Atlas, worker, and Murphy architecture | Cloud architecture/planning lead |
| M0-05 | Audit plan completeness and accept M0 | Independent cloud planning auditor |

## Current next action

Use this inventory as the checklist for the Maestro master plan. Before approval, assess the current Atlas repository against C-04, C-06, C-07, C-12, C-15, and C-16, then make every captured item visible in the plan or explicitly defer it.
