# Maestro Registration-Ready Planning — Architect One-Sheet

**Audience:** Project architects preparing a new or existing software project for Maestro  
**Purpose:** Define the minimum planning and design output Maestro must be able to discover before it can propose a project binding.  
**Authority:** [M0-D02 — Project Registration and Bootstrap](../planning/decisions/m0-d02-project-registration.md), [M0-D06 — Project Manifest Contract](../planning/decisions/m0-d06-project-manifest-contract.md), and the [Project Architecture Agent contract](../agents/architecture-agent.md)

## The required handoff

The architect hands Maestro an **owner-approved, versioned project foundation bundle at an exact repository revision**. The bundle may span several project files; it does not need to be one document or follow a Maestro folder layout.

The bundle must let Maestro discover the project without guessing. It is the authoritative answer to:

> What is being built, what governs it, how is work safely divided and verified, and where are those facts recorded?

The architect does **not** create Maestro operational state, dispatch workers, or manually maintain Maestro's database. For an existing repository, Maestro performs read-only discovery and proposes the thin `maestro.project.yaml` binding. For a new repository, Maestro generates the same binding in its bootstrap PR.

## What the planning output must contain

| Output | Minimum content |
|---|---|
| **1. Project foundation** | Project name and purpose; users and protected outcomes; current lifecycle stage; approved scope; explicit non-goals; platform/runtime constraints; release path such as foundation → discovery/design → approved milestone → implementation; owner and acceptance authority. The foundation is approved before feature implementation planning. |
| **2. Architecture and design authority** | Authoritative architecture/design paths; system boundaries and separation of concerns; component and data ownership; interfaces and integrations; security/privacy constraints; environments; deployment and rollback approach; UI/design-system authority where applicable; accepted invariants and behavior paths that implementation must preserve. |
| **3. Decisions, questions, and traceability** | Stable IDs for requirements, decisions, genuine open questions, deferrals, and N/A dispositions. Every source or intake item maps to one of those records or to a task. Planning conversations are captured and checkpointed; a free-form summary alone is insufficient. Conflicts and proposed-only authority remain visible. |
| **4. Approved work graph** | Versioned graph revision and source SHA; milestones and bounded task candidates with short action-oriented subjects; typed dependencies; planned order/rank; change domains or shared locks; integration points; owners/roles; safe parallel work; explicit stop and owner-acceptance gates. Material changes supersede records rather than silently expanding active scope. |
| **5. Verification and quality contracts** | Declared build, test, integration, UI/QA, and deployed-environment checks; required evidence; each behavior path mapped to a concrete check or honestly marked `UNTESTED` with reason and consequence. Every material quality requirement records: protected outcome, operating/threat/failure model, exclusions, assurance level, acceptance proof, permitted implementation boundary, proportionality ceiling, and stop/escalation rule. |
| **6. Project operating contract** | Repository and default branch; project rules/SOP and current handoff paths; task/issue conventions; branch/PR/merge policy; owner acceptance policy; worker eligibility and specialist overlays; independent reviewer route; QA/Murphy policy; named environment and secret references; resource locks; notifications; stricter rules and explicit exceptions. Record secret references only—never credentials or secret values. |

## Registration-ready gate

The architect may label the graph **ready to release to Maestro** only when all of the following are true:

- The project foundation and graph revision have explicit owner approval.
- Each authoritative fact has a stable repository path, record ID where applicable, and exact source revision.
- Accepted behavior is separated from proposals, unresolved questions, and deferrals.
- No unresolved question changes the project boundary, data ownership, security posture, delivery policy, or first approved milestone.
- Required binding facts in Identity, Authority, Delivery, Verification, Roles/Routing, Operations, and Exceptions are present.
- Commands and evidence expectations are exact, or the gap is marked `UNTESTED`; missing facts are not filled with convenient defaults.
- Dependencies, shared locks, integration gates, reviewer routes, and safe parallelism are explicit.
- Material quality requirements have complete, feasible, proportionate quality contracts.
- Existing project rules are preserved. A project binding may be stricter, but it cannot weaken project or Maestro safety, review, or approval requirements.
- The handoff identifies the exact point where Maestro must stop for owner acceptance.

If any item fails, the architect records the gap, owner-readable impact, and next decision. The project is **not registration-ready**.

## What Maestro does next

| Project state | Maestro onboarding path |
|---|---|
| Existing repository | `maestro project register`: read-only discovery → fact/missing/conflict inventory → proposed binding → owner-reviewed binding PR → non-dispatching dry run → registered only after merge and successful dry run. |
| New repository | `maestro project create`: create the project record → generate the minimum repository-side binding in a bootstrap PR → run the same non-dispatching dry run → registered only after merge and success. |

Registration is not implementation approval. The project repository remains authoritative for architecture, plans, rules, code, PRs, reviews, and CI. Maestro stores only the operational binding and observed execution state needed to coordinate safely; Atlas reports that state but does not edit policy or route work.

## Recommended architect handoff line

> **[Project] graph [revision] at [source SHA] is owner-approved and ready for Maestro registration discovery.** Authority paths: [paths]. Binding facts: complete / gaps listed. Open questions affecting registration: none / [IDs]. First implementation milestone remains unreleased until registration, dry run, and separate owner approval.
