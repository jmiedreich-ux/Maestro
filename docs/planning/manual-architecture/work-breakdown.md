# Maestro manual architecture — draft work breakdown

Version 1. This is a packet-first decomposition draft for the [confirmed full scope](../manual-registration.md). It is not a reviewed/confirmed development breakdown or a runnable runtime package. Source commit: `182bf4290ef2960d4691a7f41315ebf71d5bf85c`.

## Interpretation and common requirements

The architect defined the bounded contributions below before grouping them into development milestones. Plain subjects and heading links identify draft contributions; no service-generated packet or milestone number is invented. Proposed filenames name intended outputs, not existing implementation. The [investigation](investigation.md) and [project structure](project-structure.md) supply current code, reuse rationale, ownership and starting context.

Every contribution preserves the complete controlling architecture section and applicable declaration criteria, not merely its short description here. All 18 outcome identities/versions and complete acceptance requirements remain exactly those in the confirmed candidate. Implementation changes require a separately started process; these records dispatch no workers.

For every contribution, the initial manual planning source is the pinned commit plus these foundation documents. A later assigned implementation baseline must explicitly include verified integrated prerequisite revisions; it cannot silently become moving master. The named source-area specialist owns the expertise; the assigned coder authors code; a separate non-author reviewer assesses the exact result. Coding instructions, independent review and the Integration Manager handoff remain authoritative in `docs/agents/`.

Permitted paths listed below are proposals for final packet allocation. Additional edits, particularly shared schemas, packaging, terminal extensions, setup scripts and declaration evidence, require explicit final allocations; they are not implicitly permitted by a broad subject. Expected test path is `tests/maestro/<area>/test_<slug>.py`; implementation must add meaningful main-path and essential-failure checks there. No test exists merely because its destination is listed. Test commands, exact required-output records, final cross-area allocations and full Quality Assurance plans are still to be completed in the next breakdown revision.

Independent contributions may run in parallel only after their named contracts are integrated and with disjoint allocated paths. Shared store, schema, package entry and cross-area API changes have one assigned owner; consumers wait for those exact interfaces. The lists are dependency design, not a worker schedule. Lifecycle controls accompany every affected Execution stage before actual work uses it; the final acceptance group does not postpone those protections.

Quality boundary: protect only declared connected outcomes and their essential failure paths. Preserve known exclusions, including SQL backup/restore, remote interface exposure, mobile/command center and unauthorized production tests. Evidence must come from actual implemented paths and independently reviewed exact revisions. Generated inputs are allowed when identified; generated successful results are not verification. Missing required evidence remains UNTESTED, keeps the affected milestone unmerged and does not stop unrelated eligible work.

## Bounded contributions

<a id="store"></a>
### Service persistence

- Purpose and result: Deliver configured SQLite storage and atomic service writes.
- Included: Reuse assessed transaction/path techniques; add validated installed settings, WAL/FULL, migrations, receipts and event records without opening agent/CLI writers.
- Controlling behavior: [sqlite storage](../../architecture.md#sqlite-storage).
- Proposed code outputs: `services/maestro/maestro/foundation/database.py`, `services/maestro/maestro/foundation/settings.py`; meaningful checks at `tests/maestro/foundation/test_store.py`.
- Prerequisites: No other contribution; use pinned architecture and investigated source.
- Essential failure check: Reject invalid or unsupported storage without replacement; rollback an interrupted transition and publish no event.

<a id="owner-auth"></a>
### Owner authentication

- Purpose and result: Authenticate the configured local Owner.
- Included: Implement installation-token digest validation, authority derived from the credential, rotation and read/write protection.
- Controlling behavior: [local owner identity and credentials](../../architecture.md#local-owner-identity-and-credentials).
- Proposed code outputs: `services/maestro/maestro/service/authentication.py`; meaningful checks at `tests/maestro/service/test_owner_auth.py`.
- Prerequisites: [Service persistence](#store)
- Essential failure check: Missing/invalid token is 401; wrong authority is 403; body actor cannot impersonate Owner.

<a id="requests"></a>
### Durable request delivery

- Purpose and result: Save requests before acknowledging work.
- Included: Implement /api/v1 receipts, idempotent operations, expected-version rejection and uncertain-submit lookup.
- Controlling behavior: [cli request and event contract](../../architecture.md#cli-request-and-event-contract).
- Proposed code outputs: `services/maestro/maestro/service/requests.py`, `services/maestro/maestro/service/receipts.py`; meaningful checks at `tests/maestro/service/test_requests.py`.
- Prerequisites: [Service persistence](#store); [Owner authentication](#owner-auth)
- Essential failure check: Same request with different payload conflicts; dropped response reconciles without repeating the action.

<a id="activities"></a>
### Project and activity records

- Purpose and result: Expose consistent project activity and attention.
- Included: Store/read project, activity, question, finding and conversation projections with a consistent event cursor.
- Controlling behavior: [record ownership](../../architecture.md#record-ownership).
- Proposed code outputs: `services/maestro/maestro/service/activities.py`, `services/maestro/maestro/service/projections.py`; meaningful checks at `tests/maestro/service/test_activities.py`.
- Prerequisites: [Service persistence](#store); [Durable request delivery](#requests)
- Essential failure check: Cross-project context and stale version reject without corrupting another activity.

<a id="events"></a>
### Event stream

- Purpose and result: Deliver committed progress and replay.
- Included: Implement authenticated SSE, stable cursor, snapshots, heartbeat and missing-cursor recovery.
- Controlling behavior: [cli request and event contract](../../architecture.md#cli-request-and-event-contract).
- Proposed code outputs: `services/maestro/maestro/service/events.py`; meaningful checks at `tests/maestro/service/test_events.py`.
- Prerequisites: [Project and activity records](#activities)
- Essential failure check: No event before commit; duplicate events ignored by consumer; unavailable cursor requests refresh.

<a id="install"></a>
### Linux installation

- Purpose and result: Install and supervise the persistent service.
- Included: Package service entry, systemd unit, installed resources and validated config; operator/service/agent identity separation and startup evidence.
- Controlling behavior: [runtime and prerequisites](../../architecture.md#runtime-and-prerequisites).
- Proposed code outputs: `services/maestro/maestro/service/main.py`; meaningful checks at `tests/maestro/service/test_install.py`.
- Prerequisites: [Owner authentication](#owner-auth); [Event stream](#events)
- Essential failure check: Invalid setup is visibly not ready; CLI close leaves service running; restart reconciles durable state.

<a id="terminal-connection"></a>
### Terminal connection

- Purpose and result: Connect the installed terminal to the service.
- Included: Implement config/fallback, credential loading, fixed timeouts, reconnect and offline help/exit.
- Controlling behavior: [cli connection configuration](../../architecture.md#cli-connection-configuration).
- Proposed code outputs: `services/maestro/maestro/terminal/connection.py`, `services/maestro/maestro/terminal/main.py`; meaningful checks at `tests/maestro/terminal/test_terminal_connection.py`.
- Prerequisites: [Durable request delivery](#requests)
- Essential failure check: Unreachable valid URL does not fall back; changed address clears prior context; no automatic command replay.

<a id="terminal-workspace"></a>
### Terminal workspace

- Purpose and result: Show projects, activities, history and attention.
- Included: Implement selected-project workspace, scrolling/input/key behavior, activities and empty/error states from service records.
- Controlling behavior: [cli workspace](../../architecture.md#cli-workspace).
- Proposed code outputs: `services/maestro/maestro/terminal/workspace.py`, `services/maestro/maestro/terminal/rendering.py`; meaningful checks at `tests/maestro/terminal/test_terminal_workspace.py`.
- Prerequisites: [Terminal connection](#terminal-connection); [Event stream](#events)
- Essential failure check: Disconnect and project switch preserve only permitted context; errors cannot look like empty success.

<a id="questions"></a>
### Linked questions

- Purpose and result: Record and route real questions and answers.
- Included: Implement saved questions, selectable suggestions/free answers, linking, follow-ups and recipient delivery; terminal rendering in a separately owned extension.
- Controlling behavior: [questions and answers](../../architecture.md#questions-and-answers).
- Proposed code outputs: `services/maestro/maestro/service/questions.py`; meaningful checks at `tests/maestro/service/test_questions.py`.
- Prerequisites: [Project and activity records](#activities); [Terminal workspace](#terminal-workspace)
- Essential failure check: Stale/wrong question answers reject; uncertain delivery reconciles once; no answer inferred from silence.

<a id="process-policy"></a>
### Shared process policy

- Purpose and result: Bind each process to exact installed policy and schemas.
- Included: Implement definition validation, immutable effective settings, handler registry and shared bookkeeping with process-specific rules.
- Controlling behavior: [shared process definitions](../../architecture.md#shared-process-definitions).
- Proposed code outputs: `services/maestro/maestro/service/processes.py`, `services/maestro/maestro/service/resources.py`; meaningful checks at `tests/maestro/service/test_process_policy.py`.
- Prerequisites: [Service persistence](#store); [Durable request delivery](#requests)
- Essential failure check: Missing/mismatched resource or invalid duration blocks the affected activity; restart retains its snapshot.

<a id="agent-routes"></a>
### Agent route preflight

- Purpose and result: Validate exact tool/model choices and capabilities.
- Included: Collect process-supplied architect/reviewer selections separately; validate installed transport, exact model, permissions, output and assigned location/context requirements.
- Controlling behavior: [tool and model selection](../../architecture.md#tool-and-model-selection).
- Proposed code outputs: `services/maestro/maestro/agents/routes.py`, `services/maestro/maestro/agents/preflight.py`; meaningful checks at `tests/maestro/agents/test_agent_routes.py`.
- Prerequisites: [Shared process policy](#process-policy)
- Essential failure check: Unknown/mismatched identity or capability blocks launch; no provider default silently substitutes.

<a id="agent-transport"></a>
### Agent workspace and transport

- Purpose and result: Deliver exact assignments in isolated workspaces.
- Included: Implement configured supported transport protocols, read-only review sources, bounded writable outputs, structured results and linked clarification.
- Controlling behavior: [tool transport](../../architecture.md#tool-transport).
- Proposed code outputs: `services/maestro/maestro/agents/transport.py`, `services/maestro/maestro/agents/workspaces.py`; meaningful checks at `tests/maestro/agents/test_agent_transport.py`.
- Prerequisites: [Agent route preflight](#agent-routes); [Linked questions](#questions)
- Essential failure check: Malformed/stale result or out-of-scope write rejects; tool output cannot act as Owner.

<a id="supervision"></a>
### Durable supervision

- Purpose and result: Recover agent launches without duplicate work.
- Included: Journal launch intent/PID/start identity; supervise finish/cancel/deadline/stall and reconcile uncertain launch/restart with configured allowances.
- Controlling behavior: [process supervision and interruption recovery](../../architecture.md#process-supervision-and-interruption-recovery).
- Proposed code outputs: `services/maestro/maestro/agents/supervisor.py`, `services/maestro/maestro/agents/recovery.py`; meaningful checks at `tests/maestro/agents/test_supervision.py`.
- Prerequisites: [Agent workspace and transport](#agent-transport)
- Essential failure check: Crash before/after launch, unresponsive run and cancellation preserve saved operation/counts.

<a id="sessions"></a>
### Session and context continuity

- Purpose and result: Continue persistent sessions from saved evidence.
- Included: Implement session creation/resume/replacement, serialized actions, occupancy, context thresholds/checkpoints and accurate usage/performance records.
- Controlling behavior: [agent performance and context management](../../architecture.md#agent-performance-and-context-management).
- Proposed code outputs: `services/maestro/maestro/agents/sessions.py`, `services/maestro/maestro/agents/measurements.py`; meaningful checks at `tests/maestro/agents/test_sessions.py`.
- Prerequisites: [Durable supervision](#supervision)
- Essential failure check: Capacity continuation preserves remaining active-time and budgets; unknown/stale measurements remain labeled.

<a id="source-intake"></a>
### Exact source intake

- Purpose and result: Read explicit overview references at the chosen commit.
- Included: Use assessed exact Git reader; resolve selected source once, scope/outcome versions, source consistency and missing references.
- Controlling behavior: [source and publication selection](../../architecture.md#source-and-publication-selection).
- Proposed code outputs: `services/maestro/maestro/planning/sources.py`, `services/maestro/maestro/planning/intake.py`; meaningful checks at `tests/maestro/planning/test_source_intake.py`.
- Prerequisites: [Shared process policy](#process-policy)
- Essential failure check: Missing path, contradictory source, moving branch or unauthorized destination cannot silently change baseline.

<a id="publication"></a>
### Publication journal

- Purpose and result: Publish exact output through service-owned credentials.
- Included: Add authorized repository profiles, bounded Git calls, expected-parent journal, exact remote byte verification and uncertain-write reconciliation.
- Controlling behavior: [candidate publication](../../architecture.md#candidate-publication).
- Proposed code outputs: `services/maestro/maestro/foundation/git_read.py`, `services/maestro/maestro/foundation/git_publication.py`; meaningful checks at `tests/maestro/foundation/test_publication.py`.
- Prerequisites: [Service persistence](#store); [Owner authentication](#owner-auth)
- Essential failure check: Denied access/moved head/lost response reconciles before retry; no local-only success.

<a id="registration-assessment"></a>
### Registration assessment

- Purpose and result: Prepare and independently review a registration candidate.
- Included: Bind full/partial scope and exact selections; architect assessment, completion mapping, package/response validators and actual independent fidelity/correction loop.
- Controlling behavior: [assessment and independent review](../../architecture.md#assessment-and-independent-review).
- Proposed code outputs: `services/maestro/maestro/planning/registration.py`, `services/maestro/maestro/planning/registration_records.py`; meaningful checks at `tests/maestro/planning/test_registration_assessment.py`.
- Prerequisites: [Exact source intake](#source-intake); [Agent workspace and transport](#agent-transport)
- Essential failure check: Missing essential scope/dependency or exhausted material review blocks candidate readiness; no execution work is created.

<a id="registration-confirmation"></a>
### Registration confirmation

- Purpose and result: Confirm the exact published candidate.
- Included: Publish package/index and atomically activate only Owner-confirmed eligible version with saved history; add registration CLI actions/views.
- Controlling behavior: [confirmation and activation](../../architecture.md#confirmation-and-activation).
- Proposed code outputs: `services/maestro/maestro/planning/registration_confirmation.py`; meaningful checks at `tests/maestro/planning/test_registration_confirmation.py`.
- Prerequisites: [Registration assessment](#registration-assessment); [Publication journal](#publication); [Terminal workspace](#terminal-workspace)
- Essential failure check: Unpublished/stale/ambiguous confirmation and conflicting activity reject without replacing prior approval.

<a id="registration-recovery"></a>
### Registration update and recovery

- Purpose and result: Update and recover registration without losing decisions.
- Included: Implement idle reservation, comparison, preserved approval, cancellation, retry and SQL/Git recovery with existing counts.
- Controlling behavior: [re registration](../../architecture.md#re-registration).
- Proposed code outputs: `services/maestro/maestro/planning/registration_recovery.py`; meaningful checks at `tests/maestro/planning/test_registration_recovery.py`.
- Prerequisites: [Registration confirmation](#registration-confirmation); [Durable supervision](#supervision)
- Essential failure check: Crash at publication/activation and concurrent start retain exact versions and prior approval.

<a id="qa-catalog"></a>
### QA resource catalog

- Purpose and result: Collect and validate project test resources.
- Included: Implement operator registry validation, non-secret immutable catalog, assignment input transport, names/permissions/hash and selection checks.
- Controlling behavior: [project quality assurance bindings](../../architecture.md#project-quality-assurance-bindings).
- Proposed code outputs: `services/maestro/maestro/quality/catalog.py`, `services/maestro/maestro/quality/bindings.py`; meaningful checks at `tests/maestro/quality/test_qa_catalog.py`.
- Prerequisites: [Service persistence](#store); [Shared process policy](#process-policy)
- Essential failure check: Production, conflicting, unknown, unavailable or unauthorized binding blocks affected plan; credentials stay private.

<a id="architecture-entry"></a>
### Architecture session entry

- Purpose and result: Start architecture separately from registration.
- Included: Implement idle/current-confirmation checks, separate persistent architect activity, outcome-reference conversion and exact assignment inputs.
- Controlling behavior: [entry and responsibility](../../architecture.md#entry-and-responsibility).
- Proposed code outputs: `services/maestro/maestro/planning/architecture.py`, `services/maestro/maestro/planning/architecture_inputs.py`; meaningful checks at `tests/maestro/planning/test_architecture_entry.py`.
- Prerequisites: [Registration update and recovery](#registration-recovery); [Session and context continuity](#sessions)
- Essential failure check: Registration confirmation does not auto-start; stale/unmapped outcome references block; no guessed current master.

<a id="architecture-foundations"></a>
### Architecture foundations

- Purpose and result: Save investigated structure and specialist records.
- Included: Implement bounded source investigation output, decisions, current/intended structure, role/context ownership and foundations manifest validation.
- Controlling behavior: [initial code investigation](../../architecture.md#initial-code-investigation).
- Proposed code outputs: `services/maestro/maestro/planning/architecture_foundations.py`; meaningful checks at `tests/maestro/planning/test_architecture_foundations.py`.
- Prerequisites: [Architecture session entry](#architecture-entry)
- Essential failure check: Unexpected path, colliding context owner or stale source rejects; saved foundations do not imply a complete breakdown.

<a id="breakdown-records"></a>
### Breakdown schema and validation

- Purpose and result: Validate packets, milestones and QA-plan records together.
- Included: Extend supplied schema, allocation/output inventories, execution requirements, qa_plan_ref and QA-plan producer/consumer validation; graph/outcome/parallel checks.
- Controlling behavior: [architecture record contract](../../architecture.md#architecture-record-contract).
- Proposed code outputs: `services/maestro/maestro/planning/breakdown.py`, `services/maestro/maestro/planning/breakdown_validation.py`; meaningful checks at `tests/maestro/planning/test_breakdown_records.py`.
- Prerequisites: [Architecture foundations](#architecture-foundations); [QA resource catalog](#qa-catalog)
- Essential failure check: Cycle, missing output, stale outcome, missing required capability/QA reference or invalid catalog selection blocks publication.

<a id="architecture-confirmation"></a>
### Architecture review and confirmation

- Purpose and result: Review and confirm an exact development breakdown.
- Included: Implement actual independent review, amendments, content inventory/hash, publication, exact confirmation and CLI view/actions.
- Controlling behavior: [independent review and amendments](../../architecture.md#independent-review-and-amendments).
- Proposed code outputs: `services/maestro/maestro/planning/architecture_confirmation.py`; meaningful checks at `tests/maestro/planning/test_architecture_confirmation.py`.
- Prerequisites: [Breakdown schema and validation](#breakdown-records); [Publication journal](#publication)
- Essential failure check: Changing reviewed content invalidates affected approval; no confirmation of old/schema-invalid output; no Execution auto-start.

<a id="architecture-recovery"></a>
### Architecture reconciliation

- Purpose and result: Recover and replan architecture from confirmed inputs.
- Included: Implement publication/cancel/retry recovery, stale inputs and later-registration invalidation/reconciliation under retained counts.
- Controlling behavior: [replanning after re registration](../../architecture.md#replanning-after-re-registration).
- Proposed code outputs: `services/maestro/maestro/planning/architecture_recovery.py`; meaningful checks at `tests/maestro/planning/test_architecture_recovery.py`.
- Prerequisites: [Architecture review and confirmation](#architecture-confirmation); [Durable supervision](#supervision)
- Essential failure check: Unconfirmed replacement registration does not trigger replan; restart neither resets counts nor guesses receipts.

<a id="execution-start"></a>
### Execution contracts and start

- Purpose and result: Start one eligible Execution with exact snapshots.
- Included: Implement execution@1 schemas/records/API/CLI, explicit start, baseline/master distinction, settings and plan/catalog bindings.
- Controlling behavior: [execution initiation](../../architecture.md#execution-initiation).
- Proposed code outputs: `services/maestro/maestro/execution/contracts.py`, `services/maestro/maestro/execution/start.py`; meaningful checks at `tests/maestro/execution/test_execution_start.py`.
- Prerequisites: [Architecture reconciliation](#architecture-recovery); [Shared process policy](#process-policy)
- Essential failure check: Ineligible or duplicate start cannot duplicate dispatch; changed settings do not replace startup snapshot.

<a id="work-planning"></a>
### Development Manager planning

- Purpose and result: Reserve eligible work through a persistent manager.
- Included: Implement event-driven planning, exact coder selection reasons, required capabilities/context, dependencies/capacity and linked questions.
- Controlling behavior: [work planning and coder selection](../../architecture.md#work-planning-and-coder-selection).
- Proposed code outputs: `services/maestro/maestro/execution/manager.py`, `services/maestro/maestro/execution/reservations.py`; meaningful checks at `tests/maestro/execution/test_work_planning.py`.
- Prerequisites: [Execution contracts and start](#execution-start); [Session and context continuity](#sessions)
- Essential failure check: Stale/conflicting reservation rejects atomically; unrelated eligible work continues; no model polling loop.

<a id="coder-delivery"></a>
### Coder plan and result delivery

- Purpose and result: Collect plans and remotely verified packet revisions.
- Included: Implement assigned worktrees, recorded returned plan, actual local Qwen/configured cloud routes and service-verified commit/diff/push evidence.
- Controlling behavior: [coder preparation and submitted results](../../architecture.md#coder-preparation-and-submitted-results).
- Proposed code outputs: `services/maestro/maestro/execution/coders.py`, `services/maestro/maestro/execution/worktrees.py`; meaningful checks at `tests/maestro/execution/test_coder_delivery.py`.
- Prerequisites: [Development Manager planning](#work-planning); [Publication journal](#publication)
- Essential failure check: No scoped diff/commit, wrong branch, failed declared check or absent remote result stays incomplete.

<a id="packet-review"></a>
### Independent packet review

- Purpose and result: Obtain non-author review of the exact packet revision.
- Included: Separate deterministic checks from actual reviewer judgment; original-author correction, configured counts and exhaustion recommendation/Owner decision.
- Controlling behavior: [packet and integration change review limits](../../architecture.md#packet-and-integration-change-review-limits).
- Proposed code outputs: `services/maestro/maestro/execution/reviews.py`, `services/maestro/maestro/execution/review_limits.py`; meaningful checks at `tests/maestro/execution/test_packet_review.py`.
- Prerequisites: [Coder plan and result delivery](#coder-delivery)
- Essential failure check: Self-review, stale approval and exhausted unapproved correction cannot enter integration.

<a id="integration-queue"></a>
### Integration queue

- Purpose and result: Integrate approved revisions in project FIFO order.
- Included: Persistent Integration Manager and durable queue; target milestone branch, exact inputs, bounded conflict/code changes and independent change review.
- Controlling behavior: [integration management and queue](../../architecture.md#integration-management-and-queue).
- Proposed code outputs: `services/maestro/maestro/execution/integration.py`, `services/maestro/maestro/execution/queue.py`; meaningful checks at `tests/maestro/execution/test_integration_queue.py`.
- Prerequisites: [Independent packet review](#packet-review); [Publication journal](#publication)
- Essential failure check: Blocked FIFO head holds later entries; unresolved conflict and unreviewed integration edit cannot merge.

<a id="dependencies"></a>
### Dependency delivery

- Purpose and result: Deliver declared provider code before releasing consumers.
- Included: Journal early/completed-provider imports, exact commits, closure/hash, destination containment, invalidation and continuation after provider completion.
- Controlling behavior: [dependency readiness and automatic continuation](../../architecture.md#dependency-readiness-and-automatic-continuation).
- Proposed code outputs: `services/maestro/maestro/execution/dependencies.py`, `services/maestro/maestro/execution/imports.py`; meaningful checks at `tests/maestro/execution/test_dependencies.py`.
- Prerequisites: [Integration queue](#integration-queue)
- Essential failure check: Approval or completion flag alone cannot unblock; unrelated code/master tip cannot replace declared provider.

<a id="determinations"></a>
### Execution architectural determinations

- Purpose and result: Route implementation questions through bounded architecture authority.
- Included: Implement saved determination assignments, parent-snapshot settings, original-author routing and typed limit recommendations without unauthorized supplements.
- Controlling behavior: [execution architectural determinations](../../architecture.md#execution-architectural-determinations).
- Proposed code outputs: `services/maestro/maestro/execution/determinations.py`; meaningful checks at `tests/maestro/execution/test_determinations.py`.
- Prerequisites: [Independent packet review](#packet-review); [Session and context continuity](#sessions)
- Essential failure check: Missing/stale finding or unbound grant rejects; determination neither approves failed code nor changes scope.

<a id="specialist-support"></a>
### Missing specialist support

- Purpose and result: Resolve missing specialist inputs within confirmed direction.
- Included: Select existing role or publish independently reviewed role/context additions via bounded support assignments; inherited config/counts and typed exhaustion handling.
- Controlling behavior: [specialist assignment and architectural support](../../architecture.md#specialist-assignment-and-architectural-support).
- Proposed code outputs: `services/maestro/maestro/execution/specialist_support.py`; meaningful checks at `tests/maestro/execution/test_specialist_support.py`.
- Prerequisites: [Execution architectural determinations](#determinations); [Publication journal](#publication)
- Essential failure check: Scope/direction change uses Owner disposition and re-registration; new name cannot reset review counts.

<a id="qa-environment"></a>
### Isolated QA setup

- Purpose and result: Run declared setup and support processes in isolated test environments.
- Included: Implement catalog-bound setup argument arrays/script hashes, test identities/storage, health/port conditions, authorized network and reset/quarantine.
- Controlling behavior: [isolated quality assurance environment](../../architecture.md#isolated-quality-assurance-environment).
- Proposed code outputs: `services/maestro/maestro/quality/environment.py`, `services/maestro/maestro/quality/support.py`; meaningful checks at `tests/maestro/quality/test_qa_environment.py`.
- Prerequisites: [QA resource catalog](#qa-catalog); [Durable supervision](#supervision)
- Essential failure check: Changed/revoked binding, missing tool or failed cleanup blocks reuse; no production substitution.

<a id="qa-checks"></a>
### QA data and check runner

- Purpose and result: Exercise real assembled-milestone journeys.
- Included: Implement exact plan consumption, lineage, actual result paths, expected/actual assertions and PASS/FAIL/UNTESTED distinctions.
- Controlling behavior: [milestone quality assurance and test data](../../architecture.md#milestone-quality-assurance-and-test-data).
- Proposed code outputs: `services/maestro/maestro/quality/runner.py`, `services/maestro/maestro/quality/lineage.py`; meaningful checks at `tests/maestro/quality/test_qa_checks.py`.
- Prerequisites: [Isolated QA setup](#qa-environment); [Integration queue](#integration-queue)
- Essential failure check: Bypassed producer or unavailable verification remains UNTESTED; fixtures cannot directly install expected outcomes.

<a id="qa-artifacts"></a>
### Durable QA artifacts

- Purpose and result: Keep verifiable evidence through completion and retention.
- Included: Implement run-owned capture, size/secret checks, hashing, atomic publish, authorized retrieval, retention and tombstones.
- Controlling behavior: [isolated quality assurance environment](../../architecture.md#isolated-quality-assurance-environment).
- Proposed code outputs: `services/maestro/maestro/quality/artifacts.py`, `services/maestro/maestro/quality/retention.py`; meaningful checks at `tests/maestro/quality/test_qa_artifacts.py`.
- Prerequisites: [Isolated QA setup](#qa-environment); [Project and activity records](#activities)
- Essential failure check: Missing/mismatched required evidence invalidates check; interrupted write, full storage and cleanup failure recorded.

<a id="milestone-gaps"></a>
### Milestone gaps and correction

- Purpose and result: Resolve assembled outcome gaps without changing approved scope.
- Included: Run exact milestone QA/outcome review, classify findings, bounded architect payload, service-validated supplements and cross-milestone correction dependencies.
- Controlling behavior: [milestone gap architectural assignment](../../architecture.md#milestone-gap-architectural-assignment).
- Proposed code outputs: `services/maestro/maestro/execution/milestone_review.py`, `services/maestro/maestro/execution/corrections.py`; meaningful checks at `tests/maestro/execution/test_milestone_gaps.py`.
- Prerequisites: [QA data and check runner](#qa-checks); [Durable QA artifacts](#qa-artifacts); [Execution architectural determinations](#determinations); [Dependency delivery](#dependencies)
- Essential failure check: Failed/UNTESTED gate stays unmerged; scope change requires re-registration; exhausted limit needs typed Owner action.

<a id="promotion"></a>
### Milestone promotion

- Purpose and result: Promote only the exact passing milestone head.
- Included: Journal branch containment/order/review/QA/artifact checks, code delivery and verified remote master result under authorized merge rules.
- Controlling behavior: [milestone branches and product integration](../../architecture.md#milestone-branches-and-product-integration).
- Proposed code outputs: `services/maestro/maestro/execution/promotion.py`; meaningful checks at `tests/maestro/execution/test_promotion.py`.
- Prerequisites: [Milestone gaps and correction](#milestone-gaps); [Dependency delivery](#dependencies); [Publication journal](#publication)
- Essential failure check: Moved head or changed dependency invalidates affected checks; uncertain promotion reconciles before retry.

<a id="execution-stop"></a>
### Pause and graceful stop

- Purpose and result: Settle current work and honor Owner disposition.
- Included: Implement pause/resume/stop API/CLI, saved lifecycle intent and checkpoints at dispatch/review/integration/import/QA/promotion boundaries.
- Controlling behavior: [pause and graceful stop settlement](../../architecture.md#pause-and-graceful-stop-settlement).
- Proposed code outputs: `services/maestro/maestro/execution/lifecycle.py`; meaningful checks at `tests/maestro/execution/test_execution_stop.py`.
- Prerequisites: [Execution contracts and start](#execution-start); [Durable supervision](#supervision)
- Essential failure check: Stop racing an in-flight operation reconciles it; resume cannot duplicate work or revive stale inputs.

<a id="execution-recovery"></a>
### Execution recovery and completion

- Purpose and result: Recover interrupted delivery and record genuine completion.
- Included: Reconcile every journal/queue/session/QA stage; retain budgets and typed actions; completion requires all declared gates and publication evidence.
- Controlling behavior: [execution completion and recovery](../../architecture.md#execution-completion-and-recovery).
- Proposed code outputs: `services/maestro/maestro/execution/recovery.py`, `services/maestro/maestro/execution/completion.py`; meaningful checks at `tests/maestro/execution/test_execution_recovery.py`.
- Prerequisites: [Milestone promotion](#promotion); [Pause and graceful stop](#execution-stop); [Missing specialist support](#specialist-support)
- Essential failure check: Restart never resets counts or accepts unknown remote effect; cancelled/paused/UNTESTED work cannot auto-complete.

<a id="acceptance-tooling"></a>
### Connected acceptance tooling

- Purpose and result: Supply reproducible real-journey setup and evidence capture.
- Included: Implement versioned test-project input generators, CLI drivers, failure injection at actual boundaries, artifact collection and cleanup for all declared journeys.
- Controlling behavior: [journeys and interactions](../../architecture.md#journeys-and-interactions).
- Proposed code outputs: `services/maestro/maestro/quality/acceptance.py`; meaningful checks at `tests/maestro/quality/test_acceptance_tooling.py`.
- Prerequisites: [QA data and check runner](#qa-checks); [Durable QA artifacts](#qa-artifacts)
- Essential failure check: Generator supplies inputs only; missing actual agent/service/Git path remains UNTESTED.

<a id="execution-monitoring"></a>
### Lifecycle monitoring

- Purpose and result: Show saved Execution state and available actions.
- Included: Add manager plans, review/queue/dependency/QA/gap/promotion/lifecycle views and commands from current service records.
- Controlling behavior: [execution api state and record contract](../../architecture.md#execution-api-state-and-record-contract).
- Proposed code outputs: `services/maestro/maestro/terminal/execution_views.py`; meaningful checks at `tests/maestro/terminal/test_execution_monitoring.py`.
- Prerequisites: [Execution contracts and start](#execution-start); [Terminal workspace](#terminal-workspace)
- Essential failure check: Reconnect is read/reconcile; no replay; stale or unavailable readings remain explicit.

## Development milestone grouping

These seven groupings organize the contributions; they do not replace the 18 project outcomes. A group may establish a partial capability before a later connected journey supplies final project-outcome evidence. No project outcome is marked complete from grouping alone.

Every group integrates the exact named contributions and cross-group prerequisites, then exercises the actual entry, durable effect and visible result under its declarations. Retain essential failure/recovery evidence, independent reviews, a passing assembled QA plan and outcome review before promotion. Final QA setup/catalog references and explicit promotion dependencies remain unfinished.

### Connected service and workspace

Outcome: The installed terminal reads a persistent authenticated service, displays real project/activity state and delivers a linked answer. Final registration-produced evidence remains shared with the registration milestone.

Contributions: [Service persistence](#store); [Owner authentication](#owner-auth); [Durable request delivery](#requests); [Project and activity records](#activities); [Event stream](#events); [Linux installation](#install); [Terminal connection](#terminal-connection); [Terminal workspace](#terminal-workspace); [Linked questions](#questions).

### Supervised shared processes

Outcome: Actual configured agents receive bounded assignments, return validated results and resume/recover without losing evidence or process budgets. Final multi-process evidence is shared with registration and architecture.

Contributions: [Shared process policy](#process-policy); [Agent route preflight](#agent-routes); [Agent workspace and transport](#agent-transport); [Durable supervision](#supervision); [Session and context continuity](#sessions).

### Confirmed registration and history

Outcome: A real CLI registration reaches reviewed, published, explicitly confirmed scope; update/cancellation/restart preserves approved history.

Contributions: [Exact source intake](#source-intake); [Publication journal](#publication); [Registration assessment](#registration-assessment); [Registration confirmation](#registration-confirmation); [Registration update and recovery](#registration-recovery).

### Confirmed development planning

Outcome: A separately started architecture activity investigates real source, publishes packet-first work and catalog-bound QA plans, and receives exact confirmation without starting Execution.

Contributions: [QA resource catalog](#qa-catalog); [Architecture session entry](#architecture-entry); [Architecture foundations](#architecture-foundations); [Breakdown schema and validation](#breakdown-records); [Architecture review and confirmation](#architecture-confirmation); [Architecture reconciliation](#architecture-recovery).

### Independently reviewed packet delivery

Outcome: Explicit Execution delivers real remotely verified and independently reviewed packet revisions with visible plans/questions and lifecycle settlement.

Contributions: [Execution contracts and start](#execution-start); [Development Manager planning](#work-planning); [Coder plan and result delivery](#coder-delivery); [Independent packet review](#packet-review); [Execution architectural determinations](#determinations); [Pause and graceful stop](#execution-stop); [Lifecycle monitoring](#execution-monitoring).

### Integrated code and dependency delivery

Outcome: Approved code reaches milestone branches in FIFO order, declared dependencies reach consumers, and missing-specialist support preserves scope and review authority.

Contributions: [Integration queue](#integration-queue); [Dependency delivery](#dependencies); [Missing specialist support](#specialist-support).

### Verified milestone completion

Outcome: Real assembled checks/outcome review, bounded corrections, exact promotion and restart evidence establish complete Execution without bypassed required paths.

Contributions: [Isolated QA setup](#qa-environment); [QA data and check runner](#qa-checks); [Durable QA artifacts](#qa-artifacts); [Milestone gaps and correction](#milestone-gaps); [Milestone promotion](#promotion); [Execution recovery and completion](#execution-recovery); [Connected acceptance tooling](#acceptance-tooling).

## Project-outcome coverage

| Confirmed project outcome | Planned contribution coverage and final evidence |
|---|---|
| SVC-PM1 — Operate the persistent Maestro service | Service persistence, Owner authentication and Linux installation; actual boot/restart, storage/access failure and CLI-independent operation. |
| SVC-PM2 — Preserve project activity and requests | Durable requests, project/activity records, linked questions and all process handlers; final real initial/update-registration evidence. |
| SVC-PM3 — Connect the CLI to recorded service activity | Event stream, terminal connection/workspace, linked questions and process views; real CLI/API/SQL/event agreement and replay rejection. |
| SVC-PM4 — Run and recover assigned agents | Route preflight, transport, supervision and sessions; real architect/reviewer and later coder/manager runs with preserved recovery. |
| SVC-PM5 — Apply shared process definitions | Shared process policy plus actual registration and architecture handlers; both consume exact saved policy/schema bindings. |
| CLI-PM1 — Connected multi-project CLI workspace | Terminal connection/workspace, project records/events and actual registration-created state; startup, selection, history, attention, empty/error/reconnect paths. |
| CLI-PM2 — Reliable project questions and answers | Linked questions, all actual process recipients and terminal delivery; duplicate/stale/wrong-context and uncertain-answer cases. |
| REG-PM1 — Register and confirm a project through the CLI | Exact source intake, registration assessment/confirmation and publication; actual independent assessment, remote bytes and deliberate Owner confirmation. |
| REG-PM2 — Update a registration without losing approved history | Registration update/recovery, reservations and architecture reconciliation; prior approval remains intact until eligible exact replacement. |
| REG-PM3 — Recover registration without losing decisions or exceeding limits | Registration recovery, shared supervision and publication journal; interrupted stages retain questions, source, policy and counts. |
| ARC-PM1 — Establish the project's architectural foundations | Architecture entry/foundations, source reader and specialist ownership; real confirmed inputs and saved investigation/structure. |
| ARC-PM2 — Produce a bounded and parallel-ready work breakdown | QA catalog, breakdown schema/validation and actual architect; packets, milestones, setup work, dependency closure and executable producer inventory. |
| ARC-PM3 — Review and confirm the development breakdown | Architecture review/confirmation/reconciliation, publication and actual changed registration; exact content and stale rejection without automatic Execution. |
| EXE-PM1 — Deliver independently reviewed work packets | Execution start, work planning, coder delivery, actual packet review, determinations and monitoring; local Qwen and configured cloud paths under actual bindings. |
| EXE-PM2 — Integrate work and deliver declared dependencies | Integration queue, dependency delivery and promotion; FIFO, reviewed conflict changes, exact import/containment and invalidation. |
| EXE-PM3 — Resolve architectural gaps within authorized scope | Determinations, specialist support and milestone gaps; real producer-to-correction/supplement path and scope-change/limit handling. |
| EXE-PM4 — Verify milestones and publish completed Execution | QA environment/checks/artifacts, milestone gaps, promotion, acceptance tooling and completion; actual assembled paths and durable evidence. |
| EXE-PM5 — Pause, stop and recover Execution | Pause/stop plus every consuming stage's settlement contract, recovery/completion and monitoring; real interruption and restart across delivery stages. |

## Work remaining before review and confirmation

The operator resource input described in [QA resource preparation](qa-resources.md) is unavailable. It blocks final non-self-contained QA plans. This draft also still needs final per-packet path/output/execution-requirement records, exact verification commands, source-outcome references on each packet, complete milestone integration/promotion dependencies and QA plans. These are preparation tasks, not new scope questions or permission requests. Continue them while the operator input is collected; do not claim they are complete from this outline.

The full architecture content will receive separate decision-fidelity, architectural-completeness and consistency reviews under the existing bounded method once it is a reviewable breakdown. No new review round or runtime identity has been consumed by creating this draft. The Owner then confirms the exact published breakdown. This document cannot start implementation or act as a runtime assignment.
