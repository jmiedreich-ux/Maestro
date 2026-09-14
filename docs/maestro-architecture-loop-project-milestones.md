# ARC — Architecture Loop Milestone Declaration

## Declaration identity

| Field | Value |
|---|---|
| Project | Maestro |
| Declaration | ARC — Architecture loop |
| Declaration version | 1 |
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
| 1 | ARC-PM1 — Establish the project's architectural foundations | 1 | `docs/maestro-architecture-loop-project-milestones.md#arc-pm1--establish-the-projects-architectural-foundations` |
| 2 | ARC-PM2 — Produce a bounded and parallel-ready work breakdown | 1 | `docs/maestro-architecture-loop-project-milestones.md#arc-pm2--produce-a-bounded-and-parallel-ready-work-breakdown` |
| 3 | ARC-PM3 — Review and confirm the development breakdown | 1 | `docs/maestro-architecture-loop-project-milestones.md#arc-pm3--review-and-confirm-the-development-breakdown` |

## ARC-PM1 — Establish the project's architectural foundations

**Outcome:** A manual CLI request starts a persistent architect session from a confirmed registration and produces a saved code investigation, project structure, and specialist guidance.

**Included:** Architecture entry/status integration, persistent-session continuation and isolation, relevant code investigation, evidence-based code direction, source-local role/context creation, and lasting foundation records.

**Excluded:** Source-code modification or retirement, launching specialist workers, scheduling, and claiming that source inspection proves operation.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Entry and persistent session | `docs/maestro-architecture.md#entry-and-responsibility`; `docs/maestro-architecture.md#persistent-architect-session` |
| Code investigation and lasting foundations | `docs/maestro-architecture.md#initial-code-investigation`; `docs/maestro-architecture.md#lasting-project-structure-and-specialist-guidance` |
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
| A manual request targets a project | Only eligible confirmed registration starts the loop. Record its exact input and session; show real progress. Registration confirmation alone starts nothing. | Actual CLI/service/agent journey and essential unconfirmed-input rejection. | None |
| The architect investigates existing source | Findings identify supported reuse, amendment, replacement, retirement, or missing work with reasons and relevant connections. Evaluate effects across the product. | Real repository revision, findings and cited source; distinguish observed code from operational claims. | None |
| Foundations are created | Saved structure maps current and intended locations. Specialist role and starting-context files reside near their source area and identify responsibility and knowledge gaps. | Actual saved files and repository references; no worker launch or source implementation. | None |
| Work continues after clarification or interruption | Retain established findings, structure, and specialist records. Continue from verified state or visibly pause when continuation is uncertain; do not silently recreate them. | Basic real continuation and necessary interruption evidence with preserved record identities. | None |

### Definition of done

A real confirmed project reaches saved, inspectable foundations through the CLI and persistent architect session. Context exists outside session memory, source-local files are actually saved, and code-direction choices consider the whole product. Generic agent launch alone is insufficient.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Entry eligibility and persistent-session contract | Starting and resuming cannot be implemented without assuming behavior. | Resolve the architecture's concurrent-work, duplicate-start, model/session, permissions, cancellation, and recovery contracts. |
| Foundation publication | Source-local records must be durable and traceable. | Define exact output schemas, paths, version links, source write boundaries, and interrupted-write recovery. |

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

### Definition of done

The saved breakdown covers the confirmed scope and provides bounded, assessable work with meaningful parallelism and explicit dependencies. It incorporates code findings and product-wide decisions. Merely listing tasks, generating tiny fragments, or declaring disconnected components complete is insufficient.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Record contracts | The service needs consistent fields and version relationships to validate and review outputs. | Define packet and milestone schemas, outcome/dependency links, output inventory, and version/publication rules. |
| Changed foundations or registration | Existing confirmation and work cannot silently acquire a new meaning. | Define the boundary for affected-record invalidation and replanning; do not assume automatic replanning. |

## ARC-PM3 — Review and confirm the development breakdown

**Outcome:** Independent review and bounded amendments lead to exact-version Owner confirmation, with the completed loop saved and execution left unstarted.

**Included:** Independent assignments, configured review accounting, amendments and escalation, CLI summary/full-output access, confirmation, and preservation across interruption.

**Excluded:** Automatic execution, general implementation-review policy, unlimited review, and redesign based solely on reviewer preference.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Review and amendments | `docs/maestro-architecture.md#independent-review-and-amendments` |
| Exact-version confirmation | `docs/maestro-architecture.md#confirmation-and-completion` |
| Shared process behavior | `docs/maestro-architecture.md#shared-process-definitions`; `docs/maestro-architecture.md#architecture-loop-interactions` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Saved breakdown | ARC-PM2 — Produce a bounded and parallel-ready work breakdown | Required preceding output. |
| Common review/output/confirmation handling | SVC-PM5 — Apply shared process definitions | Runtime mechanics; architecture-specific eligibility and confirmation records are delivered here. |
| Independent reviewer | `docs/agents/decision-fidelity-reviewer.md` | Defined responsibility; installed separate-session operation requires development evidence. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Review begins | A separate reviewer receives the exact confirmed sources, findings, foundations, and breakdown; checks outcome coverage, bounds, dependencies, parallelism, setup, and usable integration. | Real independent assignment, input references, review output, and justified architect amendments. | None |
| Findings or clarification arrive | Apply the activity's separate review budget, avoid duplicate counting, and route material disagreement at the limit to the Owner. Preferences do not force repeated failure. | Main passing journey and a necessary controlled review-limit/duplicate-delivery case; do not demand every failure combination. | None |
| Confirmation is requested | CLI summary and full outputs identify the exact version, outcome coverage, dependencies, parallel opportunities, and limitations requiring acceptance. Only explicit eligible Owner confirmation completes that version. | Actual CLI interaction and saved confirmation referencing the reviewed outputs. | None |
| The loop completes or is interrupted | Completion does not schedule or start execution. Interruption preserves reviewed versions, decisions, and budgets and does not fabricate confirmation. | Saved before/after records and observed service state, including one necessary confirmation/recovery case. | None |

### Definition of done

A real registration-to-architecture journey reaches independently reviewed and explicitly confirmed outputs without starting execution. Findings, foundations, packets, milestones, review records, and confirmation remain traceable. A review pass or generated summary alone does not complete this outcome.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Confirmation and recovery contract | Exact-version eligibility and partial writes must have deterministic outcomes. | Define confirmation request/receipt fields, rejection/amendment handling, publication reconciliation, and recovery behavior. |
| Later changes | Prior confirmation cannot silently authorize changed work. | Define how later registration or authorized replanning affects this breakdown's eligibility. |

## Partial-registration boundary

No narrower portion is selected. Registering a subset requires explicit selected outcomes, outside dependencies and evidence, exclusions, and acceptance coverage. The unresolved contracts above prevent a claim that the complete loop is registration-ready merely because its milestones are documented.
