# Architecture Loop outcomes

## Capability and scope

This outcome area delivers the manually started architecture loop after confirmed registration: initial code investigation, lasting project structure and specialist guidance, a work-packet-first breakdown, independent review, and exact-version Owner confirmation.

The [Runtime Service outcomes](runtime-service.md) owns shared storage, APIs, supervised agents, and process-definition handling. The [CLI outcomes](cli.md) owns the terminal workspace and question controls. This outcome area owns architecture-specific commands/actions and their service handlers, persistent architect-session continuation using the adapters, output schemas and publication rules, and connected loop behavior. The [registration outcomes](registration.md) supplies confirmed registration.

Scheduling, source implementation, worker dispatch, automatic execution start, command center, and mobile UI are excluded. Replanning is included only as reconciliation after confirmed re-registration and a manual architecture-loop start. Execution implementation and policy changes are excluded. An architecture-loop outcome specification describes Maestro delivery; the development milestones produced by the loop are project data.

### Dependencies and evidence

Runtime and CLI interfaces are implemented before architecture-loop integration. A real confirmed registration supplies the input. Final shared-runtime acceptance can use this loop's connected evidence without requiring that same evidence before implementation starts.

The [project overview](../project-overview.md) records existing-code evidence and its limits. No installed capability is assumed ready. Relevant source is inspected during development preparation. Each outcome needs the implementation revision, reproducible setup, actual observations, and required reviews. Apply `docs/planning-guide/README.md#verification-expectations`: main journeys and essential failures, real data where possible, and explained necessary simulation. Live verification is deferred to development.

The ordered outcomes build the loop progressively. Foundation or breakdown completion alone does not mean the loop can be confirmed. Unresolved behavioral contracts must be resolved before affected development breakdown; writing executable validators and performing installed checks are implementation work. Implementation review, milestone Quality Assurance, promotion and completion authority follow the defined [Execution architecture](../architecture.md#execution) when generated work is later executed; they are not part of this architecture-loop outcome area.

## Outcomes

## Establish the project's architectural foundations

**Outcome:** A manual CLI request starts a persistent architect session from a confirmed registration and produces a saved code investigation, project structure, and specialist guidance.

**Included:** Architecture entry/status integration, persistent-session continuation and isolation, relevant code investigation, evidence-based code direction, source-local role/context creation, and lasting foundation records.

**Excluded:** Source-code modification or retirement, launching specialist workers, scheduling, and claiming that source inspection proves operation.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Entry and persistent session | `docs/architecture.md#entry-and-responsibility`; `docs/architecture.md#persistent-architect-session` |
| Code investigation and lasting foundations | `docs/architecture.md#initial-code-investigation`; `docs/architecture.md#lasting-project-structure-and-specialist-guidance` |
| Exact session transport and output shapes | `docs/architecture.md#persistent-session-adapter-contract`; `docs/architecture.md#architecture-assignment-and-response-contract` |
| Session limits, cancellation, and replacement | `docs/architecture.md#publication-recovery-and-cancellation` |
| Exact document locations and ownership | `docs/architecture.md#architecture-output-locations-and-records` |
| Whole-product evaluation and shared output handling | `docs/architecture.md#whole-product-architectural-evaluation`; `docs/architecture.md#shared-output-handling-and-process-boundaries` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Confirmed registration | Register and confirm a project through the CLI | Required real input; this outcome delivers the verified package-record to architecture outcome-reference mapping under `docs/architecture.md#architecture-record-contract`. Registration confirmation does not start this loop. |
| Runtime and process definitions | Run and recover assigned agents; Apply shared process definitions | Runtime supplies launch/supervision and common handling. This outcome owns persistent architecture-session integration, which fresh registration runs do not establish. |
| Terminal workspace | Connected multi-project CLI workspace | Supplies the implemented client foundation; architecture-specific entry and status are delivered here. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception | Result |
|---|---|---|---|---|
| A manual request targets a project | `/architecture start` requires a selected, registered project with no unfinished work and reserves it atomically. Repeated start opens the existing activity; `/architecture` only views it. Execution/re-registration for that project are blocked while reserved; other projects continue. Registration confirmation alone starts nothing. | Actual CLI/service/agent journey and essential unconfirmed-input rejection. | None | Done 2026-09-24. Revision 1d2fd74 on feature/architecture-foundations (merge revision in the handoff). Real service, terminal `/architecture start` on the registered Tideline Two project (Maestro-qa-2): `/architecture` with no activity only views; start reserved the project (`verify-evidence.json`: reservation held by the activity); a repeated start returned the same activity (duplicate true); re-registration was refused `project_reserved`; confirmation alone started nothing (`foundations-evidence.json`, first line). Seen in `tui-foundations-evidence.json` steps 1-7. Start refused while other work is unfinished is proved by unit test only (`tests/maestro/service/test_architecture.py`): the live attempt collided with a test row. Execution start does not exist yet. |
| Confirmed outcomes become architecture inputs | Service maps package record identities, paths, hashes and exact publication commit into architecture outcome references without substituting the code baseline. | Actual confirmed-package mapping and assignment inputs, with essential mismatched-reference rejection under `docs/architecture.md#architecture-record-contract`. | None | Done 2026-09-24. Revision 1d2fd74 on feature/architecture-foundations (merge revision in the handoff). Start with an older registration version, a wrong manifest hash and an unknown project were refused (409 `registration_ref_stale` twice, 404) in `foundations-evidence.json`. The activity records the confirmed candidate, commit and manifest hash and the separate source commit (`tui-foundations-evidence.json` step 1: source a3653f3c77f1); published manifest `.maestro/architecture/versions/2/manifest.json` on `qa/registration-published`. |
| The architect investigates existing source | Findings identify supported reuse, amendment, replacement, retirement, or missing work with reasons and relevant connections. Evaluate effects across the product. | Real repository revision, findings and cited source; distinguish observed code from operational claims. | None | Done 2026-09-24. Revision 1d2fd74 on feature/architecture-foundations (merge revision in the handoff). Real Codex architect (gpt-5.6-sol) read the code-bearing source `qa/architecture-inputs` and saved 4 findings with reasons and source paths checked against the tree; a wrong citation and a repository-root specialist were rejected and corrected in the same conversation (runs in `foundations-evidence.json`, `watch1.out`). Published `investigation.json`. The findings say what the code shows, not that it runs. |
| Foundations are created | Saved structure maps current and intended locations. Specialist files follow the exact manifest paths under their source area, including `role-<role-title>.md`, `context.md`, and optional `memory.md`. The architect owns the role and starting context; verified specialist knowledge updates cannot alter authority or overwrite another current version. | Actual saved files and repository references; no worker launch or source implementation. | None | Done 2026-09-24. Revision 1d2fd74 on feature/architecture-foundations (merge revision in the handoff). Published on `jmiedreich-ux/Maestro-qa-2` branch `qa/registration-published`: `project-structure.json`, `tideline/.maestro/role-cli-store-specialist.md` + `context.md`, `tests/.maestro/role-acceptance-test-specialist.md` + `context.md`, three journaled commits (55cf964, 4f23897, e95908b). No worker was launched and no source changed. Updating existing specialist files by a later activity is refused as a conflict (Claude run in `watch3.out`); the later outcomes own reuse. |
| Work continues after clarification or interruption | Retain established findings, structure, and specialist records. Keep the same session across answers and corrections; when unavailable, use the same role and exact model in a replacement from verified records or pause on uncertainty. Enforce separate active-run deadlines without charging waiting for the Owner; do not silently recreate foundations. | Basic real continuation and necessary interruption evidence with preserved record identities. | Real Owner answer during the session; a replacement after lost history (unit-tested only); findings handed to a replacement after clarification. | Done with exception 2026-09-24. Revision 1d2fd74 on feature/architecture-foundations (merge revision in the handoff). Interruption: a killed agent unit and a service restart were recovered in the same conversation (Codex thread 01a0d3ce in `foundations.out`; Claude session 312897c2 resumed for two more runs, `watch3.out`); a second restart during a Claude run recovered on its own (`tui-claude-evidence.json`). In the first Claude restart, two recovery runs failed with "Claude startup identity is missing" and the activity paused for the Owner, as allowed when the cause is uncertain (`tui-foundations-evidence.json` steps 9-12); cause not found and not repeated. Not shown live: an Owner answer during the session, and a replacement session for lost history; both are unit-tested only (`test_architecture.py`, `test_session_state.py`). Known gap from the independent review: after a clarification, a replacement session would not be given the findings saved so far; fix belongs with the breakdown outcome's questions. |
| Findings and supporting decisions are retained | Publish stable embedded finding identities and a service-built fixed `decisions.json` snapshot under the architecture version. Preserve unchanged identities and versions; bind references to exact containing artifacts. | Actual investigation and snapshot records conform to `docs/architecture.md#saved-findings-and-architecture-decisions` and its schema. | None | Done 2026-09-24. Revision 1d2fd74 on feature/architecture-foundations (merge revision in the handoff). Version 2 published with stable finding ids and the service-built `decisions.json` (`.maestro/architecture/versions/2/`), validated against the installed `architecture-loop@1` schema, indexed in `.maestro/architecture/index.json` (commit e95908b). Keeping ids when a later run repeats a finding is done in code (`service/architecture.py`) and not shown live. |
| A persistent session approaches its context limit | Use shared context handling without resetting occupancy on each run. Preserve verified findings, decisions, pending answers, work progress and accounting through compaction or linked replacement. | Connected continuation and saved input/output references follow `docs/architecture.md#checkpoints-and-safe-continuation`; no repeated investigation or capacity-related quality penalty. | Context-limit compaction not observable with these tools. | Accepted exception 2026-09-24. Revision 1d2fd74 on feature/architecture-foundations (merge revision in the handoff). Codex and Claude Code report no context occupancy for these runs (`context unknown` in `tui-foundations-evidence.json`), so no limit was approached. Findings, structure and decisions are stored outside the session, so a linked replacement can continue from them. Compaction and a tool-reported capacity failure (now an ordinary recovery) come with the breakdown outcome, where long sessions occur. Decisions in `decisions.json` do not yet name a source finding (`source_finding_ref` is null, allowed by the schema). |

### Definition of done

A real confirmed project reaches saved, inspectable foundations through the CLI and persistent architect session. Context exists outside session memory, source-local files are actually saved, and code-direction choices consider the whole product. Generic agent launch alone is insufficient.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Installed adapter verification | Continuation operations and event mapping are specified. | Implement and verify the selected protocols against the installed tool releases during development. |
| Validator integration | The supplied `docs/schemas/architecture-loop.schema.json` supports existing shapes; the Execution-facing additions are identified under `docs/architecture.md#architecture-loop-implementation-boundary`. | Integrate foundation checks here; Produce a bounded and parallel-ready work breakdown owns the additional packet and QA-plan schema delivery. No new Owner behavior decision is identified. |

## Produce a bounded and parallel-ready work breakdown

**Outcome:** The architect turns confirmed outcomes and investigated foundations into the smallest bounded work packets, organized into development milestones with explicit dependencies and parallel opportunities.

**Included:** Information sufficiency, recorded questions and follow-ups, packet/milestone records and outcome links, versioned Quality Assurance plans, their producer-schema and inventory extensions, integration requirements, architectural quality decisions, and persistent amendments.

**Excluded:** Work scheduling, worker assignment or dispatch, source implementation, and changing confirmed outcomes without the required authority.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Development breakdown and parallelism | `docs/architecture.md#development-breakdown-and-dependencies` |
| Questions and answers | `docs/architecture.md#information-sufficiency-and-clarification` |
| Ongoing product coherence | `docs/architecture.md#whole-product-architectural-evaluation` |
| Exact schemas and allocation | `docs/architecture.md#architecture-schema-and-process-definition-binding`; `docs/architecture.md#architecture-assignment-and-response-contract` |
| Fixed packet and milestone fields | `docs/architecture.md#architecture-record-contract` |
| Wrapper validation and bounded corrections | `docs/architecture.md#deterministic-packet-checks-and-correction` |
| Saved identities | `docs/architecture.md#identity-declarations-and-ordering`; `docs/architecture.md#shared-output-handling-and-process-boundaries` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Persistent session and foundations | Establish the project's architectural foundations | Required preceding capability; use its saved findings and structure. |
| Linked question controls | Reliable project questions and answers | Supplies client interaction; architecture-specific routing into the persistent session is delivered here. |
| Shared persistence and definition handling | Apply shared process definitions | Shared validation/saving mechanics; architecture owns record meaning and schema. |
| Operator-provisioned QA binding catalog | Verify milestones and publish completed Execution | Execution owns test-resource setup and service resolution; this outcome owns architect collection/selection, snapshot provenance and QA-plan validation. Shared evidence must exercise the real producer and consumer. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception | Result |
|---|---|---|---|---|
| The architect derives work | Packets are designed first with bounded scope, expected results, and completion criteria; milestone grouping preserves all confirmed outcomes without assuming one-to-one correspondence. | Actual saved breakdown and traceable source-outcome links. | None | Done 2026-09-24. Revision 00746b0 on feature/architecture-breakdown (merge revision in the handoff). Real service, real Codex and real Claude Code architects, real Tideline Two repository. Both runs turned the two confirmed outcomes (capture, search) into 2 milestones and 4 bounded packets with links back to the outcomes; all outcomes covered, no unresolved links (`var/qa/architecture-live/breakdown-claude-evidence.json` checks; Codex run in `watch-b1.out`, terminal view in `tui-breakdown-evidence.json`). |
| Work can run independently or shares dependencies | Record dependencies, shared-code boundaries, integration points, and justified parallel opportunities without scheduling workers. | A real project's dependency structure and code-area references; no artificial requirement to parallelize inherently dependent work. | None | Done 2026-09-24. Revision 00746b0 on feature/architecture-breakdown (merge revision in the handoff). In the saved breakdown search depends on capture, each packet depends on the one that creates the code it uses, and packet paths are recorded (`structure` in `breakdown-claude-evidence.json`). The architect marked no packets parallel because they share `tideline/cli.py`; the checker requires a stated boundary when parallel packets share paths (unit tests `test_dependencies_must_resolve_without_cycles_and_parallel_work_must_be_independent`). Nothing was scheduled. |
| Information is missing | Routine technical choices are resolved and recorded. Material questions reach the CLI, answers and follow-ups return to the same architect context, and affected work is amended. | Real linked clarification and updated outputs with preserved unrelated decisions. | Accepted 2026-09-24: no real breakdown-stage question was asked because the two real architects found no missing material information on this project. Tried: two real runs on different tools. Covered by the unit test and the foundations-stage real question; the review and amendment outcome exercises a real answer loop. | Accepted exception (see column 4). Routine technical choices were resolved and recorded: 6 decisions in the Claude run, one traced to a finding (`decisions` in `breakdown-claude-evidence.json`). The real question path (question, answer, same session) is proven at the foundations stage and by the unit test `test_a_breakdown_question_reaches_the_owner_and_the_answer_returns_to_the_same_session`; neither real agent asked a question on this project. |
| A local design affects shared capabilities | The breakdown incorporates necessary setup, integration, appropriate architectural patterns, and shared code without unsupported readiness claims or unnecessary duplication. | Investigation-to-packet links, recorded tradeoffs, and completion evidence that establishes usable outcomes. | None | Done 2026-09-24. Revision 00746b0 on feature/architecture-breakdown (merge revision in the handoff). The 4 packets link to 6 saved findings (each finding found in its hashed container, `finding_traces` in `breakdown-claude-evidence.json`); packet 1 puts the shared note store first and later packets depend on it; a decision records searching in the existing command line tool rather than a new module. |
| Execution inputs are produced | Packet `execution_requirements`, milestone `qa_plan_ref`, and versioned QA plans are accepted by the extended producer schema, inventoried, hashed and published under `docs/architecture.md#architecture-record-contract`. QA selections and `project_binding_hash` resolve through the operator-provisioned catalog under `docs/architecture.md#project-quality-assurance-bindings`. Missing required setup tooling is planned with explicit dependencies. | Actual saved packet/milestone/QA-plan set, binding collection/provenance and selected-reference validation, and manifest references; unknown or changed bindings block affected completion. Readiness requires the delivered schema and real bindings. | None | Done 2026-09-24. Revision 00746b0 on feature/architecture-breakdown (merge revision in the handoff). Packets carry `execution_requirements`, milestones a `qa_plan_ref`, and 2 versioned QA plans were saved and hashed; every record and the manifest pass `architecture-breakdown@1` with no errors (`manifest_schema`, `record_schema_errors`). QA selections come from the operator catalog (environment `local`, binding hash in `qa`); an unknown selection is rejected (unit test `test_qa_plan_selections_come_from_the_operator_catalog_and_scripts_are_exact`). Records were read back from GitHub and their hashes matched. |
| Outputs are validated before review | Required fields, paths, identities, dependencies, input versions, and required commits pass deterministic checks. The architect corrects precise errors within its separate allowance; unchanged errors pause early, and checks alone consume no correction or fidelity round. | Actual output correction and recheck, with assigned counts and one essential stale/misnamed-output rejection. | None | Done 2026-09-24. Revision 00746b0 on feature/architecture-breakdown (merge revision in the handoff). Real rejections and corrections: the Codex run had one output rejected and corrected in the same conversation (`watch-b1.out` 11:29 to 11:33). The Claude run was rejected three times for `cleanup_steps` written as objects, paused with the recovery limit used (`watch-b2.out`); the architect instruction was clarified, retry accepted and the fourth output passed and published (`watch-b3.out`). Checks alone consumed no review round. |
| Inputs or reviewed records change | Manifest and SQL references prevent stale overwrite. Mark affected dependencies and coverage for revision while retaining valid unaffected work. | Exact versions and hashes before/after a relevant change; no reliance on session memory as authority. | Accepted 2026-09-24: no real change to reviewed inputs was made; a real changed-input update belongs to the review and amendment outcome, which changes reviewed records. Covered here by unit tests only. | Accepted exception (see column 4). Carry-forward by exact reference and rewrite of only changed records are proven by the unit test `test_identities_are_stable_and_an_amendment_rewrites_only_records_that_changed`; the published breakdown carries the foundation records forward by reference (`manifest` in `verify_breakdown.py` output). |
| A packet uses a finding or architectural decision | Resolve the exact finding and container; include the decisions snapshot in manifest inventory and reviewed content. Changed supporting decisions invalidate affected coverage without rewriting published history. | Trace a real packet to its finding and decision records, including one affected-content update. | Accepted 2026-09-24 for the affected-content update after a changed decision only; needs the amendment path from the review and amendment outcome. | Done 2026-09-24 for tracing; the changed-decision update is an accepted exception. Revision 00746b0 on feature/architecture-breakdown (merge revision in the handoff). Packets trace to saved findings and their containers with matching hashes (6 of 6), and the decisions snapshot is in the manifest inventory (`breakdown-claude-evidence.json`). |

### Definition of done

The saved breakdown covers the confirmed scope and provides bounded, assessable work with meaningful parallelism and explicit dependencies. It incorporates code findings and product-wide decisions. Merely listing tasks, generating tiny fragments, or declaring disconnected components complete is insufficient.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Record validation implementation | Packet execution requirements, milestone QA-plan references, QA-plan records and inventory support are defined in prose but missing from the supplied executable schema. | Extend `docs/schemas/architecture-loop.schema.json`, allocation and response/output inventories, semantic validation and publication under `docs/architecture.md#architecture-loop-implementation-boundary`; verify real output sets during development. |
| Replanning implementation | Reconciliation is permitted only after confirmed re-registration. | Implement the existing manual architecture entry and affected-record preservation rules; no separate trigger or design prerequisite. |

## Review and confirm the development breakdown

**Outcome:** Independent review and bounded amendments lead to exact-version Owner confirmation, with the completed loop saved and execution left unstarted.

**Included:** Independent assignments, configured review accounting, amendments and escalation, CLI summary/full-output access, confirmation, and preservation across interruption.

**Excluded:** Automatic execution, general implementation-review policy, unlimited review, and redesign based solely on reviewer preference.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Review and amendments | `docs/architecture.md#independent-review-and-amendments` |
| API and re-registration-only replanning | `docs/architecture.md#architecture-api-operations`; `docs/architecture.md#replanning-after-re-registration` |
| Current versus confirmed data and invalidation | `docs/architecture.md#current-versions-and-stale-data-prevention` |
| Publication, cancellation, and restart | `docs/architecture.md#publication-recovery-and-cancellation` |
| Exact-version confirmation | `docs/architecture.md#confirmation-and-completion` |
| Shared process behavior | `docs/architecture.md#shared-process-definitions`; `docs/architecture.md#architecture-loop-interactions` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Later registration update | Update a registration without losing approved history | Supplies the real update for shared changed-registration/invalidation evidence. Implemented interfaces support integration; prior final acceptance of that shared evidence is not a prerequisite to development. |
| Saved breakdown | Produce a bounded and parallel-ready work breakdown | Required preceding output. |
| Common review/output/confirmation handling | Apply shared process definitions | Runtime mechanics; architecture-specific eligibility and confirmation records are delivered here. |
| Independent reviewer | `docs/agents/decision-fidelity-reviewer.md` | Defined responsibility; installed separate-session operation requires development evidence. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Review begins | A separate reviewer receives the exact confirmed sources, findings, foundations, and breakdown; checks outcome coverage, bounds, dependencies, parallelism, setup, and usable integration. | Real independent assignment, input references, review output, and justified architect amendments. | None |
| Findings or clarification arrive | Apply the separate review budget; one passing review is sufficient. Only outcome-blocking omissions, contradictions, or requirement violations justify rework. Check necessary corrections and affected dependencies without reopening unchanged reviewed work. Route material disagreement at the limit to the Owner. | Main passing journey and a necessary controlled review-limit/duplicate-delivery case; do not demand every failure combination. | None |
| Confirmation is requested | CLI summary and full outputs identify the exact version, outcome coverage, dependencies, parallel opportunities, and limitations requiring acceptance. Required Execution input fields and QA-plan references must have passed the producer validation owned by Produce a bounded and parallel-ready work breakdown. Show review validity and compare the expected version/hash on submission. A changed version is rejected and redisplayed; only explicit eligible Owner confirmation completes that exact version. | Actual CLI interaction and saved confirmation referencing the reviewed outputs. | None |
| The loop completes or is interrupted | Completion does not schedule or start execution. Interruption reconciles the same publication/confirmation operation without a new version, repeated completed agent work, or another Owner confirmation already recorded. Advance SQL references only after verified publication; unknown outcomes pause. | Saved before/after records and observed service state, including one necessary confirmation/recovery case. | None |
| The loop is cancelled or later restarted | Preserve saved work and prior confirmation; retain the project reservation until agents and pending operations resolve. A new activity reuses valid work and carries the same unresolved-work budgets rather than resetting them. | Actual cancellation/restart and linked accounting records, with no automatic execution. | None |
| A later registration changes outcomes | Preserve the prior breakdown as history, mark affected work ineligible pending architectural reconciliation, and retain unaffected records and valid review coverage. | Version and dependency evidence across a real registration update; architecture restarts only manually after that re-registration is confirmed; a same-registration completed breakdown is viewed rather than replanned. | None |
| An allowance is exhausted or a run times out | The linked Owner decision applies one extra attempt or a separate next-run duration exception with unchanged base limits and counts. Same-run recovery retains its deadline; capacity-only continuation retains remaining active time, while an eligible failure-recovery run follows the configured duration rule. Operational receipts alone do not invalidate architectural review. | Connected limit-response and recovery evidence follows `docs/architecture.md#owner-decisions-at-a-process-limit` and `docs/architecture.md#run-deadlines-and-duration-exceptions`; unauthorized or replayed actions cannot add grants. | None |

### Definition of done

A real registration-to-architecture journey reaches independently reviewed and explicitly confirmed outputs without starting execution. Findings, foundations, packets, milestones, review records, and confirmation remain traceable. A review pass or generated summary alone does not complete this outcome.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Connected contract verification | Request/response schemas and tool continuation are defined. | Implement and verify their integration with confirmation and recovery during development. |
| Later registration integration | Confirmed re-registration is the only replanning entry. | Verify reconciliation through manual architecture start with affected invalidation and retained unaffected coverage. |

## Partial-registration boundary

No narrower portion is selected. Registering a subset requires explicit selected outcomes, outside dependencies and evidence, exclusions, and acceptance coverage. Documentation sufficiency permits registration assessment; only the separate registration process can produce and confirm its actual registration package.

