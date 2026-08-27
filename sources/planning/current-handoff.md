# Maestro — Current Handoff

**Date:** 2026-08-27  
**Repository:** `jmiedreich-ux/Maestro`  
**Branch:** `master`  
**Current stage:** M0 — Approve the foundation plan  
**Implementation authorization:** Not granted

## Outcome of this session

The original planning transcript, VennueSign Maestro design, local-model findings, existing Atlas repository, and worked packet lifecycle have been brought into one layered Maestro planning record.

The main correction made during this session was separating planning milestones from product releases:

- M0 is the current planning-and-approval milestone.
- V1 is built by implementation milestones M1–M4.
- V2 adds controlled multi-packet delegation.
- V3 adds mature operations and integrations.

No Maestro runner or Atlas migration has been implemented.

## Canonical reading order

1. `sources/planning/current-handoff.md` — current state and restart instructions.
2. `sources/planning/maestro-alpha-1-source-inventory.md` — numbered source coverage and unresolved capture work.
3. `sources/planning/maestro-alpha-1-handoff.md` — consolidated design direction and layered M0/V1/V2/V3 roadmap.
4. `sources/planning/packet-lifecycle-example.md` — normative worked example for V1 M3.
5. `sources/planning/maestro-alpha-1-session.txt` — original planning-session source.
6. `sources/planning/local-agent-notes.md` — wrapper, model evidence, and future research source.
7. VennueSign `docs/design/proposed/maestro-dev-lead-agent-framework.md` — prior framework source to be migrated out of the product repository.
8. `jmiedreich-ux/Atlas` — existing reporting implementation to inventory and merge into Maestro.

## Locked owner decisions

- Maestro is a project-neutral development-operations system, separate from VennueSign and Foundry.
- Maestro runs on the Linux AI box from the first implementation milestone.
- Coordinator, SQLite, Atlas, local workers, wrapper, worktrees, builds, tests, browser tooling, and verification are Linux-native in V1.
- Windows is not a Maestro infrastructure dependency.
- SQLite is the initial operational database; Postgres is a future option only if distribution creates a real need.
- GitHub/project repositories remain authoritative for plans, code, PRs, reviews, and CI.
- Maestro's database owns execution state, assignments, attempts, evidence, events, recovery, and notifications.
- Atlas becomes Maestro's local reporting application and reads the database projection.
- The existing Atlas repository must be inventoried and merged into Maestro; it is not merely a reference.
- Task subjects are short and plain. Planned execution location, agent type/model class, reviewer, validation, dependencies, and risk are visible when roadmap tasks are created.
- Cloud coordinators must delegate suitable bounded implementation and test work to local agents.
- Every local packet uses the enforcement wrapper and seven-phase packet lifecycle.
- One exact rework cycle is allowed; a second failure escalates to cloud takeover.
- Mechanically catchable failures become permanent project invariant checks for future packet compilation.
- One approved milestone runs at a time and stops for owner acceptance during V1.
- Murphy remains a separate remote Azure QA capability and follows the project's manual/owner-approved trigger policy.
- Planning requires numbered source capture, structured checkpoints, traceability, and independent completeness review.

## M0 status

| Milestone | Status | Remaining work |
|---|---|---|
| M0-01 · Establish Maestro planning records | In progress | Charter, decision register, question register, and controlled repository structure are not yet formalized |
| M0-02 · Inventory every planning source | In progress | Owner review, exact Murphy source files, deeper Atlas inventory, and independent coverage audit remain |
| M0-03 · Define the shared process | Not started | Produce versioned schemas, templates, planning checkpoints, process binding, and plan-validator contract |
| M0-04 · Define the system architecture | Partially outlined | Convert the report into formal architecture, data, event, recovery, security, project-bootstrap, worker, wrapper, and adapter records |
| M0-05 · Design the Atlas migration | Not started | File/dependency inventory, database adapter boundary, migration packets, history plan, and standalone-repository decision |
| M0-06 · Audit and accept the plan | Not started | Independent source-to-plan audit and owner authorization |

M0 is not complete. V1 implementation must not begin until M0-06 passes.

## V1 build path after authorization

| Milestone | Outcome |
|---|---|
| M1 · Build the core and register projects | Linux service foundation, SQLite, project create/register, profiles, manifests, leases, events, and restart recovery |
| M2 · Merge Atlas into Maestro reporting | Existing Atlas capability moved into Maestro and backed by SQLite operational projections |
| M3 · Build packet dispatch and enforcement | One local route, packet compiler, fresh worktrees, wrapper grading, one rework, evidence, and invariant learning loop |
| M4 · Complete the persistent control loop | One real approved milestone reaches draft PR, independent review, verification, visible status, notification, and owner stop |

V1 is complete only when this full path runs on Linux without requiring an open chat turn or Windows machine.

## Open items needing decisions or source work

1. Locate and register Murphy's exact contract/source files.
2. Inventory Atlas below the top-level directory and map reusable versus replaced components.
3. Reconcile Qwen 3.6 27B evidence with older `qwen3-coder:30b`, `gpt-oss:20b`, and fallback routing names.
4. Run Muse Glimmer 30B against the same six packets and gates.
5. Choose the final Atlas destination inside Maestro and the standalone Atlas repository retirement/compatibility policy.
6. Define SQLite backup and restore policy.
7. Define maximum review/escalation limits.
8. Define resource scheduling for inference, builds, browsers, and database containers.
9. Select the first notification destination beyond local Atlas.

## Exact restart sequence

1. Read this handoff, the source inventory, and the main Alpha 1 report.
2. Present the numbered source inventory to the owner for correction or confirmation.
3. Find the exact Murphy source documents and add them to the inventory.
4. Perform the Atlas file, dependency, behavior, fixture, test, and data-source inventory.
5. Produce M0-03 shared-process schemas and examples.
6. Produce M0-04 formal architecture and decision records, using the packet lifecycle example as the normative M3 behavior.
7. Produce M0-05 Atlas migration design and bounded future packets.
8. Run an independent completeness audit against every registered source.
9. Request owner authorization before M1 begins.

## Do not do yet

- Do not implement the coordinator or worker service.
- Do not copy Atlas wholesale into Maestro before its migration inventory is approved.
- Do not archive or delete the Atlas repository.
- Do not change VennueSign or Foundry process rules yet.
- Do not contact Azure, run Murphy, or alter Murphy's trigger policy.
- Do not introduce a Windows dependency.
- Do not enable automatic multi-milestone progression.
- Do not treat this handoff as owner approval of implementation.

## Recommended restart instruction

> Continue Maestro M0 from `sources/planning/current-handoff.md`. Review the source inventory with the owner first. Do not implement V1 until M0-06 passes and the owner explicitly authorizes it.
