# Maestro manual architecture — project structure

Draft version 2, based on [the pinned investigation](investigation.md). This is the manual counterpart of the runtime project-structure record. It changes no product behavior and moves no source.

## Current and intended locations

The current executable code is a mostly flat Python package at `services/maestro/maestro/`. Keep that package root and establish the following internal areas during implementation. Only source-local specialist documents are created now.

| Intended source area | Responsibility and current material to assess | Specialist |
|---|---|---|
| `services/maestro/maestro/foundation/` | Validated installed settings, safe paths, SQLite transactions/migrations, canonical records and credential references. Assess `config.py`, `storage.py`, generic parts of `operational_state.py` and `secrets.py` | Runtime foundations |
| `services/maestro/maestro/service/` | Service boot/shutdown, authenticated API, receipts, project/activity/question projections, events and shared process binding. Assess public portions of `read_api.py` | Service and transport |
| `services/maestro/maestro/terminal/` | Connected terminal workspace, history, answers, connection recovery and process views. Replace public `cli.py` dispatch | Terminal workspace |
| `services/maestro/maestro/agents/` | Tool transports, exact selections, workspaces, supervision, persistent sessions, deadlines/context/usage and validated responses. Assess `executor.py`, `dispatch_orchestrator.py` and relevant monitoring helpers | Agent integration |
| `services/maestro/maestro/planning/` | Registration and architecture handlers, source assessment, published packages, confirmation/reconciliation. Assess exact-commit reader and replace old onboarding/authority assumptions | Planning processes |
| `services/maestro/maestro/execution/` | Development/Integration Managers, reservations, real independent review, Git journals, dependencies, architectural support, lifecycle and completion. Replace old development-manager/acceptance/merge/re-dispatch orchestration | Execution coordination |
| `services/maestro/maestro/quality/` | Test-resource catalog, isolated setup/support processes, milestone QA, data lineage, artifacts, cleanup and reset | Milestone quality |

Each area's specialist role is `<area>/.maestro/role-<plain-title>.md`, with one owned `context.md`. Optional `memory.md` is not created empty. These are project expertise overlays; they do not replace Maestro's runtime process roles in `docs/agents/`.

## Shared boundaries

- The foundation owns physical database access and migrations. Domain handlers specify their records and invariants through that boundary; clients and agents never open the store. One short write transaction owns each documented atomic transition and its events.
- The service owns verified request authority, routing, durable receipts and committed-event delivery. Domain processes own their permitted transitions. An HTTP caller cannot supply its own Owner identity.
- Agents owns tool transport and OS supervision; processes own semantic assignment/result validation and their separately configured budgets. Shared machinery cannot turn one process's completion into another's start.
- Planning owns exact registration and breakdown references. Execution consumes only validated confirmed inputs; it cannot rewrite approved source or plan to make work pass.
- Execution owns journaled repository writes. Planning publication uses the same bounded Git-operation infrastructure but its own authorization and state transition. Source reads stay side-effect free.
- Quality owns QA mechanics and evidence. It neither invents missing environments nor approves code. Required unavailable checks remain UNTESTED.
- Terminal consumes API records and renders available actions. Status, auth, input validation, idempotency and process decisions remain service-owned.

No shared module is extracted merely because two names look similar. Extract only a demonstrated shared primitive with both callers, tests and contract named in the assigned packet. Shared-file changes require one explicit owner and dependencies; disjoint domains may proceed in parallel after their common contract is integrated.

## Planned ancillary paths

`services/maestro/pyproject.toml` retains packaging ownership; installed schema resources are added through explicit packets alongside their authoritative source definitions (`docs/schemas/` for Registration/Architecture; `schemas/execution.schema.json` for Execution). Proposed deployment files belong in `services/maestro/deploy/`; QA scripts in `services/maestro/qa/`; new tests in `tests/maestro/<area>/`. None of those scripts/tests/units is claimed to exist.

Top-level historical modules remain current until their consuming packet supplies replacement entry points and caller/import verification. No history, installed database or old code is silently deleted. New production entry points must not call synthetic execution or the historical mechanical-approval loop.

## Specialist record ownership

The architect owns each role and its starting context. During separately authorized Execution, that specialist may maintain only its assigned context and optional memory, using the expected current version and recorded evidence. A conflict returns for reconciliation rather than overwriting another role's knowledge. Role creation dispatches no worker.

Each context uses `Verified facts`, `Source references` and `Knowledge gaps`, with evidence limits stated explicitly. Each role uses the required template headings, governing repository rules, exact assigned paths, verification and escalation boundaries. An implementation assignment supplies the source revision, allowed files, returned plan, route and deadlines; this document supplies none of those operational authorizations.

## Review and continuation

These foundations and the draft work map will be included in the required full architecture-breakdown reviews. No full breakdown, QA catalog or Owner-confirmed architecture version is declared here. [Packet specifications](work-breakdown.md) and [milestone integration requirements](development-milestones.md) now define the draft delivery allocation. Finish catalog-bound QA plans before the full-content review/confirmation checkpoint.
