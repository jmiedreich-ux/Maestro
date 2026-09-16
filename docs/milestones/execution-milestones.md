# EXE — Execution Milestone Declaration

## Declaration identity

| Field | Value |
|---|---|
| Project | Maestro |
| Declaration | EXE — Execution |
| Declaration version | 2 |
| Status | Proposed delivery outcomes from the defined architecture; no implementation completion or confirmed registration claimed |
| Architecture source | `docs/architecture.md` |

## Capability and scope

This declaration delivers explicitly started Execution of a registered project's confirmed development breakdown: agent coordination, implementation, independent review, integration, milestone Quality Assurance, outcome review, promotion, recovery and recorded completion. Execution-specific CLI actions and monitoring are delivered with their corresponding service behavior.

The [Runtime Service declaration](runtime-service-milestones.md) owns the installed service, shared SQLite storage, API/event transport, agent supervision and common process handling. The [CLI declaration](cli-milestones.md) owns the terminal workspace, attention, history and linked answers. The [registration declaration](registration-milestones.md) supplies the confirmed project and repository binding; the [Architecture Loop declaration](architecture-loop-milestones.md) supplies the confirmed breakdown, specialist guidance and versioned Quality Assurance plans. This declaration owns Execution-specific handlers, records, schema installation, coder adapters and route integration, repository-operation journals, worktrees, integration queues, isolated Quality Assurance supervision, and their connected CLI behavior. It extends those foundations without expanding their declared outcomes.

Command center, mobile UI, unsolicited agent conversations, automatic initial Execution startup, changed project scope without re-registration, configurable hook frameworks, SQL backup/restore and automatically authorized production testing are excluded. Planning declarations do not start software Execution.

### Dependencies and connected acceptance

The [project overview](../project-overview.md#current-state) records source evidence and its limits. Required runtime, CLI, registration and architecture-loop interfaces must be implemented and verified for the consuming journey; no installed service, agent route, credential, repository permission or environment is assumed ready. Relevant existing source is assessed during development preparation before reuse. The declaration makes no new source-readiness claim.

The order below organizes usable outcomes, not development tasks or a fixed serial work schedule. The architecture loop determines development milestones, smallest work packets and safe parallelism. Foundations may be implemented before all connected evidence exists. A shared journey can complete evidence for several outcomes, but a missing producer, handler, review or completion path remains unverified; a stub does not satisfy it.

EXE-PM3 — Resolve architectural gaps within authorized scope uses findings produced by EXE-PM4 — Verify milestones and publish completed Execution. Their interfaces can be built independently; final finding-to-correction acceptance is shared. EXE-PM5 — Pause, stop and recover Execution verifies lifecycle behavior across every earlier outcome. Its required stopping and recovery controls must accompany the affected implementation before actual work depends on them; its position does not authorize an unsafe interim engine.

Apply `docs/planning-guide/README.md#verification-expectations` and `docs/architecture.md#milestone-quality-assurance-and-test-data`: use actual connected paths and proportionate main-journey and essential-failure evidence. Necessary controlled inputs or fault simulation are identified, with origin and limitations. They cannot replace the service, agent, Git, review, setup or result-producing path being verified. Required missing or bypassed paths remain `UNTESTED`. Each definition of done also requires implementation revision, reproducible setup, actual observations and applicable independent implementation review, milestone Quality Assurance, outcome review and promotion evidence under the existing Execution rules. Documentation review alone satisfies none of these implementation gates.

## Milestones and order

| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |
|---|---|---|---|
| 1 | EXE-PM1 — Deliver independently reviewed work packets | 1 | `docs/milestones/execution-milestones.md#exe-pm1--deliver-independently-reviewed-work-packets` |
| 2 | EXE-PM2 — Integrate work and deliver declared dependencies | 2 | `docs/milestones/execution-milestones.md#exe-pm2--integrate-work-and-deliver-declared-dependencies` |
| 3 | EXE-PM3 — Resolve architectural gaps within authorized scope | 2 | `docs/milestones/execution-milestones.md#exe-pm3--resolve-architectural-gaps-within-authorized-scope` |
| 4 | EXE-PM4 — Verify milestones and publish completed Execution | 2 | `docs/milestones/execution-milestones.md#exe-pm4--verify-milestones-and-publish-completed-execution` |
| 5 | EXE-PM5 — Pause, stop and recover Execution | 2 | `docs/milestones/execution-milestones.md#exe-pm5--pause-stop-and-recover-execution` |

## EXE-PM1 — Deliver independently reviewed work packets

**Outcome:** An explicit CLI start uses a confirmed project breakdown to coordinate real coder work and return exact independently reviewed packet revisions, with saved progress, questions and evidence.

**Included:** Execution entry/status, configuration and installed `execution@1` validation bundle, process-specific SQLite records and API handlers, persistent Development Manager integration, coder routes and adapters, packet worktrees and credentialed publication, implementation plans, independent packet review and bounded corrections, and associated CLI monitoring.

**Excluded:** Packet-to-milestone integration, milestone acceptance, automatic startup after architecture confirmation, and approval based on coder claims alone.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Explicit start, exact configuration and durable activity | `docs/architecture.md#execution-initiation`; `docs/architecture.md#execution-process-definition-and-configuration`; `docs/architecture.md#execution-api-state-and-record-contract` |
| Persistent coordination, route choice and linked questions | `docs/architecture.md#development-manager-preparation-and-continuity`; `docs/architecture.md#work-planning-and-coder-selection`; `docs/architecture.md#planning-results-and-questions` |
| Plan, implementation, branch publication and independent review | `docs/architecture.md#coder-preparation-and-submitted-results`; `docs/architecture.md#execution-workspaces-and-repository-writes`; `docs/architecture.md#independent-implementation-review`; `docs/architecture.md#packet-and-integration-change-review-limits` |
| Credentials, supervision and monitoring | `docs/architecture.md#local-owner-identity-and-credentials`; `docs/architecture.md#adapter-configuration`; `docs/architecture.md#agent-performance-and-context-management`; `docs/architecture.md#cli-workspace` |
| Saved authority and branch identity | `docs/architecture.md#sqlite-storage`; `docs/architecture.md#milestone-branches-and-product-integration`; `docs/architecture.md#owner-decisions-at-a-process-limit` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Installed runtime, storage, transport and agent supervision | SVC-PM1 — Operate the persistent Maestro service; SVC-PM2 — Preserve project activity and requests; SVC-PM3 — Connect the CLI to recorded service activity; SVC-PM4 — Run and recover assigned agents; SVC-PM5 — Apply shared process definitions | Planned foundations; this outcome adds Execution-specific schemas, handlers and persistent manager/coder integration. Generic launch alone is insufficient. |
| Terminal and linked responses | CLI-PM1 — Connected multi-project CLI workspace; CLI-PM2 — Reliable project questions and answers | Implemented foundations required; Execution actions and views are owned here. |
| Confirmed project, exact breakdown and source-local specialist inputs | REG-PM1 — Register and confirm a project through the CLI; ARC-PM3 — Review and confirm the development breakdown | Actual published/confirmed inputs required, including packet execution requirements and source/repository bindings. ARC-PM2 — Produce a bounded and parallel-ready work breakdown owns the missing producer-schema extensions; confirmation and Execution consumption require that delivered validation, not the older schema alone. |
| Working installed coder and reviewer routes and repository access | `docs/architecture.md#execution-process-definition-and-configuration`; `docs/architecture.md#execution-workspaces-and-repository-writes` | This outcome supplies Execution setup and verification, including local Qwen CLI/Ollama, configured Codex/Claude routes, exact model evidence, constrained worktrees and service-only Git credentials. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| The Owner starts eligible work | `/execution start` collects the permitted Development Manager route; validates current registration/breakdown, configuration, access and eligible work; derives and saves the approved code baseline and separately observed product-master start head under the architecture; atomically records one activity. Repeated start opens it. Ineligible or conflicting work is rejected without dispatch. | Actual CLI-to-service start, manager response, saved references/hashes and an essential rejection/replay case. | None |
| Configuration and typed results are consumed | The installed bundle resolves from its declared source, and exact route/model, deadline, capability, location, context and concurrency checks run before use. Missing or unverifiable configuration blocks affected work while status remains readable. Saved settings are not silently replaced by later edits. | Installed bundle hash and configuration evidence, actual model identity and structured results; essential invalid configuration or route mismatch rejection. | None |
| The manager plans and revises work | It reads current outcomes and blockers, retains one persistent session with one planning action at a time, requests eligible assignments and records selection reasons. Service reservations enforce dependencies, capacity and shared-code limits. Unrelated eligible work continues; stale requests cannot start. | Real multi-packet planning and event-driven reconsideration, correlated reservations and state, plus one linked question/answer; no polling model loop. | None |
| A coder delivers its assigned change | The permitted route executes the exact packet and specialist context. Qwen remains the default; justified configured cloud selection needs no prior Qwen failure. The plan is saved and visible before work continues without a new approval gate. Result, local commit, scoped diff and service-verified remote revision agree. | Actual coder outputs, plan, checks, clean worktree, wrapper checks and Git journal; demonstrate local Qwen and configured cloud transport without requiring every model combination. | None |
| Independent packet review completes or reaches its limit | A non-author reviews exact revisions in a separate read-only workspace. Valid findings return for correction; counts survive reassignment and technical recovery. Approval makes only that revision eligible for integration. Limit exhaustion stays unapproved and uses the architect recommendation and typed Owner decision. | Real review and affected correction evidence; essential exhausted-limit/grant handling may share EXE-PM3 — Resolve architectural gaps within authorized scope evidence. | None |
| Monitoring follows saved work | CLI shows current work, plans, questions, blockers, review counts, activity history and available runtime measurements from saved service records. Unknown/stale measurements and disconnection remain explicit; reconnect does not replay mutations. Agent progress is distinguishable from validated results. | Correlated CLI/API/SQL/events and actual runtime readings, with one unavailable-reading or reconnect case. | None |

### Definition of done

A real confirmed breakdown reaches independently reviewed, remotely verified packet revisions through the installed CLI, service and actual agent routes. The shared evidence requirements above apply. Planning output, a local commit, successful agent exit or a review of another revision cannot complete this outcome. Missing later integration and milestone evidence is not presented as complete Execution.

### Unresolved details

Executable schemas, physical SQL tables, route installation and installed capability checks are delivery work owned here. Exact permitted model values and positive runtime durations are installed configuration inputs under the architecture. No new Owner behavior decision is proposed; an unavailable required capability remains a specific blocker.

## EXE-PM2 — Integrate work and deliver declared dependencies

**Outcome:** Independently approved packets are integrated into the correct milestone branches in durable project FIFO order, and eligible integrated code reaches dependent milestones with traceable readiness.

**Included:** Persistent Integration Manager, branch/merge handlers, integration-change review, journaled remote verification, dependency imports and invalidation, queue and dependency visibility, and retained workspace/branch identities.

**Excluded:** Skipping a blocked FIFO head, treating review alone as dependency readiness, importing undeclared code, and promotion without milestone gates.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Integration queue and independent change review | `docs/architecture.md#integration-management-and-queue`; `docs/architecture.md#packet-and-integration-change-review-limits` |
| Branches, exact revisions and service-owned merges | `docs/architecture.md#milestone-branches-and-product-integration`; `docs/architecture.md#execution-workspaces-and-repository-writes`; `docs/architecture.md#authorized-integration-merges` |
| Dependency delivery and invalidation | `docs/architecture.md#dependency-readiness-and-automatic-continuation` |
| Durable Git effects and state | `docs/architecture.md#execution-api-state-and-record-contract`; `docs/architecture.md#execution-completion-and-recovery` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Actual approved packet revisions and shared Execution substrate | EXE-PM1 — Deliver independently reviewed work packets | Supplies exact revisions, review evidence, service credentials, worktrees, configuration and journals; this outcome adds integration and import operations. |
| Declared dependency closure and promotion requirements | ARC-PM3 — Review and confirm the development breakdown | Exact confirmed packet/milestone dependencies and shared-code boundaries; insufficient declarations block affected work. |
| Later promotion and lifecycle evidence | EXE-PM4 — Verify milestones and publish completed Execution; EXE-PM5 — Pause, stop and recover Execution | Those outcomes supply milestone gates and stopped/restarted queue journeys. Final shared evidence is not a prerequisite to writing integration code. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Approved packets reach integration | One project-wide persistent Integration Manager consumes durable FIFO entries, one active across its milestones. A blocked head remains first; permitted coding/review and other projects may continue. Departure requires one of the recorded architecture-authorized resolutions. | Actual queue, two entries, assignment/session identities and essential blocked-head behavior. | None |
| Integration requires connection changes | The exact approved packet is merged on the service-assigned integration branch from the current milestone head. New integration code receives independent change review and bounded corrections; unchanged packet coverage is retained. No-change integration does not trigger automatic duplicate packet review. | Real branch graph, integration result, review references and verified non-fast-forward milestone merge. | None |
| Remote effects are uncertain or the target changes | The journal binds intended objects and expected heads; service verifies remote state before advancement. Changed targets require reconciliation and affected review; no force-push, rebase, squash, overwrite or unverified success. | Actual repository reads and essential lost-response or changed-head evidence through the real handlers. | None |
| A dependent milestone needs integrated code early | Only an eligible accumulated packet set within the declared dependency closure is imported through its FIFO entry and dependency branch. Readiness binds verified source/import commits; dependent packet branches use the updated consumer head. Source milestone promotion remains a prerequisite unless the confirmed architecture assigns the outcome otherwise. | Connected producer-to-consumer branch history, closure check, readiness record and promotion dependency; ineligible import remains waiting. | None |
| Source evidence changes | Atomically invalidate affected transitive consumers and branch-bound QA/review evidence. Affected starts and merges stop; running results are quarantined until reconciliation. Replacement import and affected checks restore readiness without retargeting old approvals. | Essential invalidation/replacement journey with retained old records, real merge evidence and unaffected work remaining eligible. | None |
| A dependency requires source-milestone completion | After verified promotion/completion, deliver the exact passing provider milestone head and confirmed dependency closure through FIFO import, or verify existing containment. A completion flag or moving master head cannot release dependent work. | Real completed-provider delivery, including an early import held for excess closure, saved completion/source/import references and an essential mismatch rejection. | None |

### Definition of done

Real reviewed code reaches the intended milestone branches and an eligible dependent milestone through the actual service, Git operations and independent integration review. Queue, branch and dependency records agree with verified remote revisions. Full promotion depends on EXE-PM4 — Verify milestones and publish completed Execution; packet integration alone does not complete a milestone.

### Unresolved details

Git handlers, persistent Integration Manager integration and dependency state are implementation work under the cited contracts. Installed repository permissions and essential reconciliation behavior require evidence; source availability is not assumed.

## EXE-PM3 — Resolve architectural gaps within authorized scope

**Outcome:** Missing specialist coverage and milestone findings reach the correct bounded architect assignment, and valid corrections become executable without altering confirmed scope or silently replacing approved records.

**Included:** Missing-role support and independent fidelity review, support publication/bindings, milestone-gap determination, correction supplements, review-limit recommendations, and linked Owner disposition before re-registration.

**Excluded:** Automatic scope changes, restarting the architecture loop as support, self-review, extra review allowances without the existing authority, or automatic re-registration/replanning.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Missing specialist and bounded support | `docs/architecture.md#specialist-assignment-and-architectural-support`; `docs/architecture.md#architectural-support-configuration-and-fallback`; `docs/architecture.md#support-validation-and-publication` |
| Milestone finding determination and supplement activation | `docs/architecture.md#milestone-gap-architectural-assignment`; `docs/architecture.md#correction-supplement-activation`; `docs/architecture.md#milestone-outcome-review` |
| Packet/integration architectural questions and review-limit recommendations | `docs/architecture.md#execution-architectural-determinations` |
| Owner authority and re-registration transition | `docs/architecture.md#owner-decisions-at-a-process-limit`; `docs/architecture.md#work-disposition-before-re-registration`; `docs/architecture.md#replanning-after-re-registration` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Saved assignments, review records, linked questions and repository operations | EXE-PM1 — Deliver independently reviewed work packets; EXE-PM2 — Integrate work and deliver declared dependencies | Implemented interfaces required; support, architectural-determination and supplement record semantics and handlers are owned here. |
| Current confirmed roles, source and breakdown | ARC-PM3 — Review and confirm the development breakdown | Actual references and source-local ownership bound to the assignment. |
| Actual milestone findings and correction verification | EXE-PM4 — Verify milestones and publish completed Execution | Supplies QA/outcome-review findings and verifies corrected behavior. Shared final acceptance must use that real path, not injected successful results. |
| Work settlement and later re-registration | EXE-PM5 — Pause, stop and recover Execution; REG-PM2 — Update a registration without losing approved history | Execution owns disposition and settlement; registration owns its later explicit idle-only update. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| A packet lacks adequate specialist guidance | A separate bounded support assignment validates an existing role or supplies an in-scope role/context. A new role receives independent fidelity review; its validated, remotely verified activation binds exact files to affected packets before reconsideration. Existing unchanged roles need applicability checks, not a new content review. | Actual missing-coverage request, architect response, new-role review and publication/activation records; no overwritten confirmed breakdown. | None |
| A support route is unavailable or output fails | Assignment configuration comes from the parent Execution snapshot despite later file edits. Only configured eligible fallback is used, with stopping confirmed where needed and counters preserved. A failed assessment/review does not justify verdict-seeking model substitution. Neither usable route or uncertain stopping pauses affected work. | Actual configuration and route evidence plus essential cause-based fallback or blocked-route case. | None |
| Milestone QA or outcome review reports a defect or gap | A distinct read-only milestone-gap assignment receives exact evidence and remaining allowances. Its validated result routes implementation defects to Integration, missing in-scope work to bounded supplements, and scope changes to Owner disposition. It cannot approve or dispatch code. | Actual finding-to-determination journey shared with EXE-PM4 — Verify milestones and publish completed Execution, including saved affected-work references. | None |
| An in-scope supplement is produced | Service-assigned identity/version, bounded paths, ownership, dependencies and exact finding references validate. Journaled publication verifies remote bytes/hash before atomic activation. Identical replay does not duplicate work; started versions remain immutable. Implemented corrections follow normal review and integration without resetting milestone counts. | Real supplement, external hash/journal, activation, correction packet and affected verification records; essential stale/conflicting or invalid payload rejection. | None |
| Findings reach a process limit or need replanning | Packet/integration architectural questions and exhausted-review findings produce the configured bounded determination and validated saved recommendation; failed milestone findings use their distinct milestone-gap assignment. CLI presents the exact architect recommendation and typed Owner choices. Support-review exhaustion uses its own typed target and same-assignment architect recommendation. A grant remains bound to its review/assignment; disposition enforces the selected affected-work restrictions. Unrelated eligible work continues where allowed. Free text is not approval and a disposition does not start registration. | Linked decision, durable receipt, unchanged scope/counters and actual service enforcement; later idle transition shares lifecycle evidence. | None |

### Definition of done

A real missing-role request and a real milestone finding are resolved through the correct separate assignments and exact published records. Valid in-scope corrections proceed through their required checks; out-of-scope or exhausted work remains blocked for its authorized decision. Final evidence includes both the finding producer and the corrected capability path.

### Unresolved details

Support and supplement validators, publication handlers and connected assignment integration remain implementation work. This declaration supplies no new architectural authority or default model selection.

## EXE-PM4 — Verify milestones and publish completed Execution

**Outcome:** An assembled milestone is exercised in an isolated environment, independently reviewed against its promised outcome, promoted only when both gates pass, and included in verified milestone and Execution completion records visible through the CLI.

**Included:** Versioned QA-plan consumption, isolated setup and supervision, test-data lineage, durable evidence and retention, independent outcome review/gap analysis, correction-path integration, promotion checks, automatic eligible continuation and completion publication.

**Excluded:** Packet-level QA, production testing without separate authorization, completion from packet counts alone, or passing a required path bypassed by test data or mocks.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Confirmed QA inputs and test-data limits | `docs/architecture.md#architecture-output-locations-and-records`; `docs/architecture.md#milestone-quality-assurance-and-test-data` |
| Project test bindings, environment, evidence and cleanup | `docs/architecture.md#project-quality-assurance-bindings`; `docs/architecture.md#isolated-quality-assurance-environment` |
| Independent outcome review and corrections | `docs/architecture.md#milestone-outcome-review`; `docs/architecture.md#milestone-gap-architectural-assignment`; `docs/architecture.md#correction-supplement-activation` |
| Promotion, continuation and completion records | `docs/architecture.md#milestone-branches-and-product-integration`; `docs/architecture.md#authorized-integration-merges`; `docs/architecture.md#dependency-readiness-and-automatic-continuation`; `docs/architecture.md#execution-completion-and-recovery` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Integrated exact milestone branch and dependencies | EXE-PM2 — Integrate work and deliver declared dependencies | Must be verified and current; target changes or invalidated imports invalidate affected evidence. |
| In-scope correction and scope-change handling | EXE-PM3 — Resolve architectural gaps within authorized scope | Required for real finding disposition and corrected acceptance; implementation can share the connected journey. |
| Versioned QA plan, data/setup requirements and completion criteria | ARC-PM3 — Review and confirm the development breakdown | Supplies the exact confirmed plan after ARC-PM2 — Produce a bounded and parallel-ready work breakdown delivers its QA-plan/packet schema and inventory extensions. Missing product setup tooling is declared packet/dependency work, not improvised QA. |
| Installed environment supervisor, artifact store and QA/reviewer routes | `docs/architecture.md#execution-process-definition-and-configuration`; `docs/architecture.md#isolated-quality-assurance-environment` | This outcome installs and verifies Execution-specific facilities over the runtime foundation, including operator provisioning, the service QA binding catalog and exact snapshot/credential resolution. ARC-PM2 — Produce a bounded and parallel-ready work breakdown owns plan selection/validation against that catalog; neither side assumes pre-existing references. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| A milestone is ready for QA | Service resolves the confirmed plan against its saved project binding/hash, checks current test-only authorization, records non-secret credential version identities, creates isolated storage and starts declared product/support processes with health checks. Network access and secret handling follow the approved plan; no production target is silently used. | Actual operator-provisioning-to-plan-to-run journey, source/binding/configuration hashes, process/port/health evidence and test credential references without secret values; essential revoked or changed-binding rejection. | None |
| Actual user journeys run | Data provenance, setup, actual input/result paths, expected/actual results and limitations are recorded. Required bypassed or unavailable paths remain `UNTESTED`, block promotion and appear as specific CLI blockers. Failed paths use the existing correction route and affected reruns. | Real connected product journey and essential failure, plus a missing prerequisite/bypassed-path case demonstrating that it cannot pass. | None |
| Artifacts and environments are retained safely | Required evidence has service-owned identity/hash/size/media type and authorized retrieval. Capture/retention and tombstones follow configuration; missing required evidence before closure invalidates the check. Cleanup/reset failures quarantine the environment and block reuse. | Actual artifact write/read/hash, cleanup and essential missing-evidence or failed-reset handling; retention scheduling may use a controlled clock with its limitation recorded. | None |
| Whole-milestone review completes | A fresh non-author/non-integrator independently checks exact assembled revisions, connected outcomes, dependencies and QA evidence. Blocking findings use the architect determination; targeted correction retains unaffected coverage and original review counts. Non-blocking preferences add no gate. | Actual outcome review and gap analysis, plus shared finding/correction evidence and configured-limit enforcement. | None |
| Both milestone gates pass | Only no failed/unverified required QA path plus passing outcome review permits the exact authorized non-fast-forward merge to product master. Dependency promotion order and current target evidence are checked. No further Owner approval is requested for an eligible merge. | Verified remote merge, exact gate/evidence references and an essential stale-target or unsatisfied-gate rejection. | None |
| Milestone and overall work finish | Immutable milestone records are published and verified before SQL completion. Eligible work continues within confirmed scope; all authorized milestones and outstanding work must reconcile before successful Execution completion publication and CLI notification. A lost response reconciles the same version; conflicts pause. | Real milestone completion and overall completion bytes/hashes, remote refs, SQL state and CLI summary; no unfinished/uncertain work hidden by closure. | None |

### Definition of done

The full installed path delivers a real confirmed outcome through integration, isolated QA, independent milestone review, verified promotion and published completion. Findings have a working correction path. Completion evidence is retrievable, agrees with SQL and remote Git, and distinguishes unavailable verification from failure or success. Shared declaration evidence requirements apply.

### Unresolved details

QA supervision, artifact capture/retention, executable completion validators and Git/SQL handlers are implementation work. Product-specific setup and data come from the confirmed QA plan; referenced credentials come from its service-resolved project binding; missing prerequisites stay planned and unverified rather than being supplied by a fabricated passing result.

## EXE-PM5 — Pause, stop and recover Execution

**Outcome:** The Owner can pause, resume or gracefully stop real Execution, and service/agent/repository interruptions recover from saved facts without duplicated effects, lost work, reset allowances or false completion.

**Included:** Execution lifecycle CLI actions and handlers, exact settlement-set persistence, supervised stopping, cause-based automatic recovery, typed manual retry, persistent-session/context recovery, workspace/environment reconciliation, stopped-closure publication and transition to explicit re-registration.

**Excluded:** Immediate termination disguised as graceful completion, automatic replacement while original state is unknown, changed scope/models outside existing rules, automatic re-registration and SQL backup/restore.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Versioned actions and settlement | `docs/architecture.md#execution-api-state-and-record-contract`; `docs/architecture.md#pause-and-graceful-stop-settlement` |
| Owner disposition, manual grants and timing | `docs/architecture.md#work-disposition-before-re-registration`; `docs/architecture.md#owner-decisions-at-a-process-limit`; `docs/architecture.md#run-deadlines-and-duration-exceptions` |
| Restart, external effects and stopped closure | `docs/architecture.md#execution-completion-and-recovery`; `docs/architecture.md#execution-workspaces-and-repository-writes`; `docs/architecture.md#process-supervision-and-interruption-recovery` |
| Capacity continuation and UI recovery | `docs/architecture.md#checkpoints-and-safe-continuation`; `docs/architecture.md#visibility-and-delivery-boundary`; `docs/architecture.md#startup-and-connection-states` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Real Execution stages to settle and recover | EXE-PM1 — Deliver independently reviewed work packets; EXE-PM2 — Integrate work and deliver declared dependencies; EXE-PM3 — Resolve architectural gaps within authorized scope; EXE-PM4 — Verify milestones and publish completed Execution | Controls are developed with affected stages; final connected evidence exercises actual assignments, queue/evidence and journal operations. |
| Shared supervision and durable transport | SVC-PM2 — Preserve project activity and requests; SVC-PM3 — Connect the CLI to recorded service activity; SVC-PM4 — Run and recover assigned agents | Runtime provides persistence/supervision primitives; this outcome implements Execution-specific recovery and lifecycle semantics. |
| Explicit later registration and architecture reconciliation | REG-PM2 — Update a registration without losing approved history; ARC-PM3 — Review and confirm the development breakdown | These processes retain their own authority and budgets. Connected transition evidence needs their actual implementations, not an assumed successful update. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Pause or graceful stop is accepted | Versioned Owner action atomically saves the exact in-progress set and restrictions. No outside packet/supplement joins; only permitted downstream settlement proceeds. Held/unfinished FIFO heads cannot be skipped. Pause reaches paused only after uncertainty settles; eligible resume preserves state. | Actual lifecycle requests during active work, before/after settlement records, refusal of new reservations and essential stale/replayed action handling. | None |
| Work is stopped or prepared for re-registration | The chosen disposition enforces its exact affected scope, retains active architectural determinations in settlement, and distinguishes safe finishing from supervised unsafe stopping. Unstarted work remains unfinished. A verified stopped record lists completed and unfinished work; SQL/CLI never label it successful delivery. Idle is reported only after runs and external operations reconcile. | Real stopped-closure bytes and UI, settlement evidence, and explicit idle-only re-registration followed by separately started architecture and Execution steps. | None |
| Service, agent or Git response is interrupted | Reload saved sessions, deadlines, counters, queue position, restrictions, grants, environments, artifacts and journals. Reconcile existing effects before replacement or advancement. Verified completed steps are not repeated; unknown outcomes remain blocked. | Essential real restart/lost-response journey with correlated process/Git/SQL evidence; controlled fault inputs cannot replace actual recovery handlers. | None |
| Recovery reaches its configured limit | Cause-based recovery and configured backup preserve assignment identity and allowances. Manual retry requires its typed unconsumed grant, recorded intervention and eligible operation; launch/attempt consumption is atomic and cannot be replayed. Duration exceptions cannot extend active work or replenish attempts. | Actual saved recovery/decision records and essential rejection of reused or unauthorized grants; one permitted manual retry through the real service path. | None |
| Persistent context fills or a session is lost | Shared checkpoint/continuation recovers verified work and exact bindings. Capacity handling preserves remaining active-time budget and does not consume failure/review allowances or lower performance status. Unsafe or ineffective continuation pauses visibly. | Actual supported Execution-session continuation, occupancy quality and retained decisions/counters; unavailable capabilities remain explicit blockers. | None |
| CLI reconnects or resources require cleanup | Saved current state and history are restored without resubmitting mutations or implying that disconnected work stopped. Workspaces, branches, artifacts and environments retain their required evidence; failed reconciliation/cleanup is quarantined and visible. | Real reconnect and essential cleanup/reconciliation evidence, with retained exact references and unchanged work outcomes. | None |

### Definition of done

The installed engine completes meaningful active-work pause/resume, stopped closure and interruption/recovery journeys across its real components. Saved restrictions, deadlines, counts, branch/evidence references and unfinished work survive. Connected re-registration/replanning remains explicit. Earlier outcomes' implementation and evidence gates are retained; recovered or stopped work is never promoted by inference.

### Unresolved details

Installed supervision and provider continuation behavior require verification during implementation. Any unsupported required capability is reported against its affected outcome; no substitute success, new allowance or weakened stopping guarantee is authorized here.

## Partial-registration boundary

No narrower portion is selected by this declaration. Any later partial registration names its included outcomes, architecture, outside dependencies and their evidence explicitly. A partial implementation or isolated component check does not establish the complete Execution engine.
