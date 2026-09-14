# ARC — Architecture Loop Milestone Declaration

## Declaration identity

| Field | Value |
|---|---|
| Project | Maestro |
| Declaration | ARC — Architecture loop |
| Declaration version | 2 |
| Status | Draft outcomes; unresolved contracts identified; no implementation completion or registration-readiness claim |
| Architecture source | `docs/maestro-architecture.md` |

## Capability and scope

This declaration delivers the manually started architecture loop after confirmed registration: initial code investigation, lasting project structure and specialist guidance, a work-packet-first breakdown, independent review, and exact-version Owner confirmation.

The [Runtime Service declaration](maestro-runtime-service-project-milestones.md) owns shared storage, APIs, supervised agents, and process-definition handling. The [CLI declaration](maestro-cli-project-milestones.md) owns the terminal workspace and question controls. This declaration owns architecture-specific commands/actions and their service handlers, persistent architect-session continuation using the adapters, output schemas and publication rules, and connected loop behavior. The [registration declaration](maestro-registration-project-milestones.md) supplies confirmed registration.

Scheduling, source implementation, worker dispatch, automatic execution start, command center, and mobile UI are excluded. General replanning and Execution policy are not defined by these outcomes. An architecture-loop milestone declaration describes Maestro delivery; the development milestones produced by the loop are project data.

### Dependencies and evidence

Runtime and CLI interfaces are implemented before architecture-loop integration. A real confirmed registration supplies the input. Final shared-runtime acceptance can use this loop's connected evidence without requiring that same evidence before implementation starts.

The [project overview](maestro-project-overview.md) records existing-code evidence and its limits. No installed capability is assumed ready. Relevant source is inspected during development preparation. Each outcome needs the implementation revision, reproducible setup, actual observations, and required reviews. Apply `docs/planning-guide/README.md#verification-expectations`: main journeys and essential failures, real data where possible, and explained necessary simulation. Live verification is deferred to development.

The ordered outcomes build the loop progressively. Foundation or breakdown completion alone does not mean the loop can be confirmed. Unresolved behavioral contracts must be resolved before affected development breakdown; writing executable validators and performing installed checks are implementation work. General implementation-review and acceptance authority remain provisional for separate Execution design.

## Milestones and order

| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |
|---|---|---|---|
| 1 | ARC-PM1 — Establish the project's architectural foundations | 2 | `docs/maestro-architecture-loop-project-milestones.md#arc-pm1--establish-the-projects-architectural-foundations` |
| 2 | ARC-PM2 — Produce a bounded and parallel-ready work breakdown | 2 | `docs/maestro-architecture-loop-project-milestones.md#arc-pm2--produce-a-bounded-and-parallel-ready-work-breakdown` |
| 3 | ARC-PM3 — Review and confirm the development breakdown | 2 | `docs/maestro-architecture-loop-project-milestones.md#arc-pm3--review-and-confirm-the-development-breakdown` |

## ARC-PM1 — Establish the project's architectural foundations

**Outcome:** A manual CLI request starts a persistent architect session from a confirmed registration and produces a saved code investigation, project structure, and specialist guidance.

**Included:** Architecture entry/status integration, persistent-session continuation and isolation, relevant code investigation, evidence-based code direction, source-local role/context creation, and lasting foundation records.

**Excluded:** Source-code modification or retirement, launching specialist workers, scheduling, and claiming that source inspection proves operation.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Entry and persistent session | `docs/maestro-architecture.md#entry-and-responsibility`; `docs/maestro-architecture.md#persistent-architect-session` |
| Code investigation and lasting foundations | `docs/maestro-architecture.md#initial-code-investigation`; `docs/maestro-architecture.md#lasting-project-structure-and-specialist-guidance` |
| Session limits, cancellation, and replacement | `docs/maestro-architecture.md#publication-recovery-and-cancellation` |
| Exact document locations and ownership | `docs/maestro-architecture.md#architecture-output-locations-and-records` |
| Whole-product evaluation and shared output handling | `docs/maestro-architecture.md#whole-product-architectural-evaluation`; `docs/maestro-architecture.md#shared-output-handling-and-process-boundaries` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Confirmed registration | REG-PM1 — Register and confirm a project through the CLI | Required real input; registration confirmation does not start this loop. |
| Runtime and process definitions | SVC-PM4 — Run and recover assigned agents; SVC-PM5 — Apply shared process definitions | Runtime supplies launch/supervision and common handling. This outcome owns persistent architecture-session integration, which fresh registration runs do not establish. |
| Terminal workspace | CLI-PM1 — Connected multi-project CLI workspace | Supplies the implemented client foundation; architecture-specific entry and status are delivered here. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| A manual request targets a project | `/architecture start` requires a selected, registered project with no unfinished work and reserves it atomically. Repeated start opens the existing activity; `/architecture` only views it. Execution/re-registration for that project are blocked while reserved; other projects continue. Registration confirmation alone starts nothing. | Actual CLI/service/agent journey and essential unconfirmed-input rejection. | None |
| The architect investigates existing source | Findings identify supported reuse, amendment, replacement, retirement, or missing work with reasons and relevant connections. Evaluate effects across the product. | Real repository revision, findings and cited source; distinguish observed code from operational claims. | None |
| Foundations are created | Saved structure maps current and intended locations. Specialist files follow the exact manifest paths under their source area, including `role-<role-title>.md`, `context.md`, and optional `memory.md`. The architect owns the role and starting context; verified specialist knowledge updates cannot alter authority or overwrite another current version. | Actual saved files and repository references; no worker launch or source implementation. | None |
| Work continues after clarification or interruption | Retain established findings, structure, and specialist records. Keep the same session across answers and corrections; when unavailable, use the same role and exact model in a replacement from verified records or pause on uncertainty. Enforce separate active-run deadlines without charging waiting for the Owner; do not silently recreate foundations. | Basic real continuation and necessary interruption evidence with preserved record identities. | None |

### Definition of done

A real confirmed project reaches saved, inspectable foundations through the CLI and persistent architect session. Context exists outside session memory, source-local files are actually saved, and code-direction choices consider the whole product. Generic agent launch alone is insufficient.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Tool continuation contract | Persistent continuity needs exact adapter operations. | Specify tool resume and active/waiting event mapping under the agreed session behavior; idle entry, selections, cancellation, and limits are settled. |
| Executable validation | Fixed paths and source-local publication are defined in the architecture. | Implement validators and adapter response schemas for those contracts; do not reopen names, ownership, or publication behavior. |

## ARC-PM2 — Produce a bounded and parallel-ready work breakdown

**Outcome:** The architect turns confirmed outcomes and investigated foundations into the smallest bounded work packets, organized into development milestones with explicit dependencies and parallel opportunities.

**Included:** Information sufficiency, recorded questions and follow-ups, packet/milestone records and outcome links, integration requirements, architectural quality decisions, and persistent amendments.

**Excluded:** Work scheduling, worker assignment or dispatch, source implementation, and changing confirmed outcomes without the required authority.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Packet-first breakdown and parallelism | `docs/maestro-architecture.md#work-packet-first-breakdown` |
| Questions and answers | `docs/maestro-architecture.md#information-sufficiency-and-clarification` |
| Ongoing product coherence | `docs/maestro-architecture.md#whole-product-architectural-evaluation` |
| Fixed packet and milestone fields | `docs/maestro-architecture.md#architecture-record-contract` |
| Wrapper validation and bounded corrections | `docs/maestro-architecture.md#deterministic-packet-checks-and-correction` |
| Saved identities | `docs/maestro-architecture.md#identity-declarations-and-ordering`; `docs/maestro-architecture.md#shared-output-handling-and-process-boundaries` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Persistent session and foundations | ARC-PM1 — Establish the project's architectural foundations | Required preceding capability; use its saved findings and structure. |
| Linked question controls | CLI-PM2 — Reliable project questions and answers | Supplies client interaction; architecture-specific routing into the persistent session is delivered here. |
| Shared persistence and definition handling | SVC-PM5 — Apply shared process definitions | Shared validation/saving mechanics; architecture owns record meaning and schema. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| The architect derives work | Packets are designed first with bounded scope, expected results, and completion criteria; milestone grouping preserves all confirmed outcomes without assuming one-to-one correspondence. | Actual saved breakdown and traceable source-outcome links. | None |
| Work can run independently or shares dependencies | Record dependencies, shared-code boundaries, integration points, and justified parallel opportunities without scheduling workers. | A real project's dependency structure and code-area references; no artificial requirement to parallelize inherently dependent work. | None |
| Information is missing | Routine technical choices are resolved and recorded. Material questions reach the CLI, answers and follow-ups return to the same architect context, and affected work is amended. | Real linked clarification and updated outputs with preserved unrelated decisions. | None |
| A local design affects shared capabilities | The breakdown incorporates necessary setup, integration, appropriate architectural patterns, and shared code without unsupported readiness claims or unnecessary duplication. | Investigation-to-packet links, recorded tradeoffs, and completion evidence that establishes usable outcomes. | None |
| Outputs are validated before review | Required fields, paths, identities, dependencies, input versions, and required commits pass deterministic checks. The architect corrects precise errors within its separate allowance; unchanged errors pause early, and checks alone consume no correction or fidelity round. | Actual output correction and recheck, with assigned counts and one essential stale/misnamed-output rejection. | None |
| Inputs or reviewed records change | Manifest and SQL references prevent stale overwrite. Mark affected dependencies and coverage for revision while retaining valid unaffected work. | Exact versions and hashes before/after a relevant change; no reliance on session memory as authority. | None |

### Definition of done

The saved breakdown covers the confirmed scope and provides bounded, assessable work with meaningful parallelism and explicit dependencies. It incorporates code findings and product-wide decisions. Merely listing tasks, generating tiny fragments, or declaring disconnected components complete is insufficient.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Executable record schemas | Required fields, references, names, and version rules are defined. | Implement JSON Schemas and canonical inventory serialization against the architecture record contract. |
| General replanning | Later changes must respect existing work and authority. | Separate replanning design remains; changed-registration invalidation and manual resumption rules are already defined. |

## ARC-PM3 — Review and confirm the development breakdown

**Outcome:** Independent review and bounded amendments lead to exact-version Owner confirmation, with the completed loop saved and execution left unstarted.

**Included:** Independent assignments, configured review accounting, amendments and escalation, CLI summary/full-output access, confirmation, and preservation across interruption.

**Excluded:** Automatic execution, general implementation-review policy, unlimited review, and redesign based solely on reviewer preference.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Review and amendments | `docs/maestro-architecture.md#independent-review-and-amendments` |
| Current versus confirmed data and invalidation | `docs/maestro-architecture.md#current-versions-and-stale-data-prevention` |
| Publication, cancellation, and restart | `docs/maestro-architecture.md#publication-recovery-and-cancellation` |
| Exact-version confirmation | `docs/maestro-architecture.md#confirmation-and-completion` |
| Shared process behavior | `docs/maestro-architecture.md#shared-process-definitions`; `docs/maestro-architecture.md#architecture-loop-interactions` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Later registration update | REG-PM2 — Update a registration without losing approved history | Supplies the real update for shared changed-registration/invalidation evidence. Implemented interfaces support integration; prior final acceptance of that shared evidence is not a prerequisite to development. |
| Saved breakdown | ARC-PM2 — Produce a bounded and parallel-ready work breakdown | Required preceding output. |
| Common review/output/confirmation handling | SVC-PM5 — Apply shared process definitions | Runtime mechanics; architecture-specific eligibility and confirmation records are delivered here. |
| Independent reviewer | `docs/agents/decision-fidelity-reviewer.md` | Defined responsibility; installed separate-session operation requires development evidence. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Review begins | A separate reviewer receives the exact confirmed sources, findings, foundations, and breakdown; checks outcome coverage, bounds, dependencies, parallelism, setup, and usable integration. | Real independent assignment, input references, review output, and justified architect amendments. | None |
| Findings or clarification arrive | Apply the separate review budget; one passing review is sufficient. Only outcome-blocking omissions, contradictions, or requirement violations justify rework. Check necessary corrections and affected dependencies without reopening unchanged reviewed work. Route material disagreement at the limit to the Owner. | Main passing journey and a necessary controlled review-limit/duplicate-delivery case; do not demand every failure combination. | None |
| Confirmation is requested | CLI summary and full outputs identify the exact version, outcome coverage, dependencies, parallel opportunities, and limitations requiring acceptance. Show review validity and compare the expected version/hash on submission. A changed version is rejected and redisplayed; only explicit eligible Owner confirmation completes that exact version. | Actual CLI interaction and saved confirmation referencing the reviewed outputs. | None |
| The loop completes or is interrupted | Completion does not schedule or start execution. Interruption reconciles the same publication/confirmation operation without a new version, repeated completed agent work, or another Owner confirmation already recorded. Advance SQL references only after verified publication; unknown outcomes pause. | Saved before/after records and observed service state, including one necessary confirmation/recovery case. | None |
| The loop is cancelled or later restarted | Preserve saved work and prior confirmation; retain the project reservation until agents and pending operations resolve. A new activity reuses valid work and carries the same unresolved-work budgets rather than resetting them. | Actual cancellation/restart and linked accounting records, with no automatic execution. | None |
| A later registration changes outcomes | Preserve the prior breakdown as history, mark affected work ineligible pending architectural reconciliation, and retain unaffected records and valid review coverage. | Version and dependency evidence across a real registration update; architecture restarts only manually. | None |

### Definition of done

A real registration-to-architecture journey reaches independently reviewed and explicitly confirmed outputs without starting execution. Findings, foundations, packets, milestones, review records, and confirmation remain traceable. A review pass or generated summary alone does not complete this outcome.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Exact request and response schemas | The confirmation comparison, receipt, publication journal, and recovery behavior are defined. | Specify executable API/agent schemas and tool continuation without changing the agreed process. |
| General replanning | Prior confirmation cannot silently authorize changed work. | Complete separate replanning design; preserve the already defined invalidation of affected work and retained unaffected coverage. |

## Partial-registration boundary

No narrower portion is selected. Registering a subset requires explicit selected outcomes, outside dependencies and evidence, exclusions, and acceptance coverage. The unresolved contracts above prevent a claim that the complete loop is registration-ready merely because its milestones are documented.
