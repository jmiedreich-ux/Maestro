# Manual development milestones

Version 3. Integration and acceptance requirements for the [packet index](work-breakdown.md), governed by [common packet rules](packet-rules.md). These are manual draft contributions, not service-allocated milestone identities, final QA plans, runtime confirmation or authorization to start Execution.

## Ordering and integration boundary

The seven milestones below have a delivery dependency on the preceding milestone's integrated usable contribution; the first has none. Individual packet code prerequisites are listed in each packet and may cross these groups. A packet may implement and test a provider contract before future domain consumers exist; it must demonstrate that boundary using actual provider code and a real minimal caller. It cannot claim the later consumer's behavior. The consumer owns its actual connection and assembled milestone acceptance proves the complete path. This avoids a circular requirement that a provider finish an unimplemented future consumer before it can be integrated.

The acceptance requirements below describe meaningful connected outcomes and essential failures, not a fixed worker schedule. For the initial product bootstrap, absent later-domain operations remain explicitly unavailable rather than blocking core service health or being represented by fake success. Building these capabilities does not assume that unfinished Maestro can already orchestrate its own development. This manual plan supplies no authorization or replacement runtime workflow for doing so.

## Milestone QA plans and runtime binding

Each milestone has a separate [manual QA plan](qa-plans/README.md) with procedures, expected results, evidence and cleanup. QA applies to the assembled milestone after its packet implementation, review and integration; packet checks remain separate. [QA resource preparation](qa-resources.md) records the verified operator repository, service App, agent tools, local models, network endpoints and isolated roots. These complete the concrete manual readiness inputs but are not service-validated catalog records. The assigned implementation packets must still deliver the service catalog consumer, final runtime QA-plan identities and binding hashes, exact setup/check commands, test Owner credential, artifact retention, cleanup/reset behavior and observed results before QA use. A missing required real path is UNTESTED and cannot pass, integrate as an accepted milestone or promote. Packet-level unit checks do not substitute for milestone QA.

## Common completion boundary

Each milestone needs all allocated packet implementations and independent reviews, exact integrated revisions, passing assembled QA for its claimed contribution, retained evidence and resolved in-scope material gaps under existing limits. Promotion follows the architecture's eligibility and authorized merge rules; no new Owner merge-approval gate is added. Project declarations remain the authority for complete outcomes. Early milestones supply partial contributions where a declaration requires later domains; only the final outcome reconciliation can claim every selected declaration complete. Nothing here records executed checks.

## Connected service and workspace

QA procedure: [Connected service and workspace](qa-plans/service-workspace.md).

Usable contribution: Installed, authenticated workspace and durable service primitives. Opening an empty project list is useful here; live Registration questions and later process views are accepted only with their producer milestones.

Integration dependency: none beyond the pinned source and separately provided authorized development environment.

Allocated packets:

- [Service persistence](work-packets/store.md)
- [Owner authentication](work-packets/owner-auth.md)
- [Durable request delivery](work-packets/requests.md)
- [Project and activity records](work-packets/activities.md)
- [Event stream](work-packets/events.md)
- [Linux installation](work-packets/install.md)
- [Terminal connection](work-packets/terminal-connection.md)
- [Terminal workspace](work-packets/terminal-workspace.md)
- [Linked questions](work-packets/questions.md)

Related project outcomes: [SVC-PM1 — Operate the persistent Maestro service](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm1--operate-the-persistent-maestro-service); [SVC-PM2 — Preserve project activity and requests](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm2--preserve-project-activity-and-requests); [SVC-PM3 — Connect the CLI to recorded service activity](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm3--connect-the-cli-to-recorded-service-activity); [CLI-PM1 — Connected multi-project CLI workspace](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm1--connected-multi-project-cli-workspace); [CLI-PM2 — Reliable project questions and answers](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm2--reliable-project-questions-and-answers).

### Connected acceptance requirements

Use the isolated Linux host and test Owner credential. Start the installed service and real terminal, reject an invalid credential, open the empty workspace and reconnect after restart. Through the authenticated API create/read project activity and a generic linked question; accept exactly one matching answer and reject a stale duplicate. Observe one committed receipt/effect/event and cursor-consistent reads; no direct SQL mutation supplies expected results.

### Data, evidence and essential failures

Fresh run-owned data root, valid/invalid test credentials and controlled connection loss. Retain install revision, health/API/terminal evidence and restart/receipt/event observations. Preserve diagnostic artifacts before approved cleanup of only run-owned resources.

### Advancement

Meet the common completion boundary for this contribution. Record exact candidate/review/QA evidence and any unavailable required path. No packet count, generated result or unbound QA proposal is evidence of this milestone passing.

## Supervised shared processes

QA procedure: [Supervised shared processes](qa-plans/supervised-processes.md).

Usable contribution: Real supervised agent assignments using shared installed process policy, with durable session continuation. This is infrastructure acceptance, not proof that a future domain process is complete.

Integration dependency: [Connected service and workspace](#connected-service-and-workspace).

Allocated packets:

- [Shared process policy](work-packets/process-policy.md)
- [Agent route preflight](work-packets/agent-routes.md)
- [Agent workspace and transport](work-packets/agent-transport.md)
- [Durable supervision](work-packets/supervision.md)
- [Session and context continuity](work-packets/sessions.md)

Related project outcomes: [SVC-PM4 — Run and recover assigned agents](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm4--run-and-recover-assigned-agents); [SVC-PM5 — Apply shared process definitions](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm5--apply-shared-process-definitions).

### Connected acceptance requirements

Load actual installed policy/schema resources and inspect the immutable selection snapshot. Collect and save exact supported tool/model selections separately for author and reviewer test assignments; launch an actual bounded assignment through the configured adapter, validate its result and observe status in the workspace. Interrupt/restart supervision; prove retained assignment/session identity and deadlines/budgets, reject stale results and missing resources without an uncontrolled launch.

### Data, evidence and essential failures

Approved installed routes, isolated worktree and a bounded actual task with observable output. Retain tool/model/version and non-secret selection provenance, launch/result evidence and restart records. Missing tool access leaves that route UNTESTED; deterministic adapter tests alone cannot pass this milestone.

### Advancement

Meet the common completion boundary for this contribution. Record exact candidate/review/QA evidence and any unavailable required path. No packet count, generated result or unbound QA proposal is evidence of this milestone passing.

## Confirmed registration and history

QA procedure: [Confirmed registration and history](qa-plans/registration-history.md).

Usable contribution: A person can register, confirm, update and recover a project through the connected CLI while preserving exact source, approval and history.

Integration dependency: [Supervised shared processes](#supervised-shared-processes).

Allocated packets:

- [Exact source intake](work-packets/source-intake.md)
- [Publication journal](work-packets/publication.md)
- [Registration assessment](work-packets/registration-assessment.md)
- [Registration confirmation](work-packets/registration-confirmation.md)
- [Registration update and recovery](work-packets/registration-recovery.md)

Related project outcomes: [REG-PM1 — Register and confirm a project through the CLI](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm1--register-and-confirm-a-project-through-the-cli); [REG-PM2 — Update a registration without losing approved history](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm2--update-a-registration-without-losing-approved-history); [REG-PM3 — Recover registration without losing decisions or exceeding limits](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm3--recover-registration-without-losing-decisions-or-exceeding-limits); [CLI-PM1 — Connected multi-project CLI workspace](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm1--connected-multi-project-cli-workspace); [CLI-PM2 — Reliable project questions and answers](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm2--reliable-project-questions-and-answers).

### Connected acceptance requirements

Use actual test Git repository sources and the real terminal. Collect repository, overview path, exact source revision, publication branch/profile and separate architect/reviewer tool/model selections through defined input steps. Complete assessment and non-author review; publish and confirm the exact displayed candidate. Update source, then register the update and prove old approved history remains accessible. Interrupt publication and restart; reconcile the exact intended commit without replaying confirmation or resetting rounds. Answer a real assessment clarification in the same project.

### Data, evidence and essential failures

Generated source documents are legitimate input, not prewritten registration output. Retain input Git hashes, request/selection records, actual agent/review evidence, remote package/confirmation hashes and visible history. Reject stale confirmation, inaccessible sources and unauthorized publication. Cleanup may not erase approved history used as evidence.

### Advancement

Meet the common completion boundary for this contribution. Record exact candidate/review/QA evidence and any unavailable required path. No packet count, generated result or unbound QA proposal is evidence of this milestone passing.

## Confirmed development planning

QA procedure: [Confirmed development planning](qa-plans/development-planning.md).

Usable contribution: The confirmed registration can produce investigated structure, specialist guidance and a reviewed, published, exactly confirmed development breakdown through the architecture process.

Integration dependency: [Confirmed registration and history](#confirmed-registration-and-history).

Allocated packets:

- [QA resource catalog](work-packets/qa-catalog.md)
- [Architecture session entry](work-packets/architecture-entry.md)
- [Architecture foundations](work-packets/architecture-foundations.md)
- [Breakdown schema and validation](work-packets/breakdown-records.md)
- [Architecture review and confirmation](work-packets/architecture-confirmation.md)
- [Architecture reconciliation](work-packets/architecture-recovery.md)

Related project outcomes: [ARC-PM1 — Establish the project's architectural foundations](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm1--establish-the-projects-architectural-foundations); [ARC-PM2 — Produce a bounded and parallel-ready work breakdown](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm2--produce-a-bounded-and-parallel-ready-work-breakdown); [ARC-PM3 — Review and confirm the development breakdown](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm3--review-and-confirm-the-development-breakdown).

### Connected acceptance requirements

Start from the exact confirmed registration. Exercise session entry/continuation, source investigation, specialist role/context records, clarification, packet/milestone schemas and catalog binding. Produce a genuine scoped sample breakdown via actual agents and review it independently; amend within existing bounds, publish and confirm exact files/hashes. Cancel/restart and re-register changed scope; prove stale architecture cannot start Execution and reconciliation retains prior evidence.

### Data, evidence and essential failures

A small generated test project, actual test catalog and separately selected architect/reviewer tools/models. Retain investigations, role/context headings, schema validation, catalog provenance/hash, review/amendment lineage and exact confirmation references. Missing catalog entries or mismatched bindings reject affected plans. The sample project's confirmed plan is test evidence, not confirmation of this Maestro manual breakdown.

### Advancement

Meet the common completion boundary for this contribution. Record exact candidate/review/QA evidence and any unavailable required path. No packet count, generated result or unbound QA proposal is evidence of this milestone passing.

## Independently reviewed packet delivery

QA procedure: [Independently reviewed packet delivery](qa-plans/packet-delivery.md).

Usable contribution: Separately started Execution delivers exact packet revisions with implementation plans and actual non-author semantic review; lifecycle controls are usable throughout.

Integration dependency: [Confirmed development planning](#confirmed-development-planning).

Allocated packets:

- [Execution contracts and start](work-packets/execution-start.md)
- [Development Manager planning](work-packets/work-planning.md)
- [Coder plan and result delivery](work-packets/coder-delivery.md)
- [Independent packet review](work-packets/packet-review.md)
- [Execution architectural determinations](work-packets/determinations.md)
- [Pause and graceful stop](work-packets/execution-stop.md)
- [Lifecycle monitoring](work-packets/execution-monitoring.md)

Related project outcomes: [EXE-PM1 — Deliver independently reviewed work packets](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm1--deliver-independently-reviewed-work-packets); [EXE-PM3 — Resolve architectural gaps within authorized scope](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm3--resolve-architectural-gaps-within-authorized-scope); [EXE-PM5 — Pause, stop and recover Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm5--pause-stop-and-recover-execution).

### Connected acceptance requirements

From a genuine confirmed sample breakdown, start Execution with the required saved selections and configuration. Observe Development Manager assignment, coder plan/result, scoped local/remote revision and independent review. Exercise bounded correction and a real architect determination; monitoring shows the same durable state. Pause/resume and graceful-stop an active coder/review path: no forbidden new work or publication occurs, in-flight settlement follows the documented policy and remaining allowances survive restart.

### Data, evidence and essential failures

Actual configured coder and independent reviewer routes, scoped repository credentials and sample work with a meaningful change. Retain plans, exact base/head, changed paths, tool evidence, semantic review and lifecycle records. Canned agent judgments, mechanical approval or direct default-branch merge cannot pass. This milestone does not claim product integration or completed Execution.

### Advancement

Meet the common completion boundary for this contribution. Record exact candidate/review/QA evidence and any unavailable required path. No packet count, generated result or unbound QA proposal is evidence of this milestone passing.

## Integrated code and dependency delivery

QA procedure: [Integrated code and dependency delivery](qa-plans/integration-dependencies.md).

Usable contribution: Reviewed work is integrated in the declared order and required dependency deliveries and missing-specialist support reach their consumers without bypassing scope.

Integration dependency: [Independently reviewed packet delivery](#independently-reviewed-packet-delivery).

Allocated packets:

- [Integration queue](work-packets/integration-queue.md)
- [Dependency delivery](work-packets/dependencies.md)
- [Missing specialist support](work-packets/specialist-support.md)

Related project outcomes: [EXE-PM2 — Integrate work and deliver declared dependencies](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm2--integrate-work-and-deliver-declared-dependencies); [EXE-PM3 — Resolve architectural gaps within authorized scope](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm3--resolve-architectural-gaps-within-authorized-scope); [EXE-PM5 — Pause, stop and recover Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm5--pause-stop-and-recover-execution).

### Connected acceptance requirements

Deliver independent reviewed sample packets into one milestone queue; prove serialized FIFO Git application with exact eligibility/base checks. Exercise declared dependency delivery, source containment and consumer reconciliation; reject wrong revisions or paths. Trigger the defined missing-specialist support path and consume its bounded result without expanding packet permissions. Interrupt an unknown Git outcome, restart and reconcile remote state before retry. Repeat pause/stop around integration and dependency import.

### Data, evidence and essential failures

At least two real eligible packet revisions plus a declared dependency and a controlled conflict. Retain queue order, Git journal, remote ancestry/delivery evidence, specialist authority and exact consumer state. Do not inject approvals or pretend a dependency is present. Conflict/unsafe target remains blocked, with diagnostic evidence preserved.

### Advancement

Meet the common completion boundary for this contribution. Record exact candidate/review/QA evidence and any unavailable required path. No packet count, generated result or unbound QA proposal is evidence of this milestone passing.

## Verified milestone completion

QA procedure: [Verified milestone completion](qa-plans/milestone-completion.md).

Usable contribution: Assembled milestones undergo genuine isolated QA, bounded gap correction and authorized promotion; all included outcome evidence is evaluated before completed Execution is published.

Integration dependency: [Integrated code and dependency delivery](#integrated-code-and-dependency-delivery).

Allocated packets:

- [Isolated QA setup](work-packets/qa-environment.md)
- [QA data and check runner](work-packets/qa-checks.md)
- [Durable QA artifacts](work-packets/qa-artifacts.md)
- [Milestone gaps and correction](work-packets/milestone-gaps.md)
- [Milestone promotion](work-packets/promotion.md)
- [Execution recovery and completion](work-packets/execution-recovery.md)
- [Connected acceptance tooling](work-packets/acceptance-tooling.md)

Related project outcomes: [EXE-PM4 — Verify milestones and publish completed Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm4--verify-milestones-and-publish-completed-execution); [EXE-PM5 — Pause, stop and recover Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm5--pause-stop-and-recover-execution); [SVC-PM1 — Operate the persistent Maestro service](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm1--operate-the-persistent-maestro-service); [SVC-PM2 — Preserve project activity and requests](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm2--preserve-project-activity-and-requests); [SVC-PM3 — Connect the CLI to recorded service activity](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm3--connect-the-cli-to-recorded-service-activity); [SVC-PM4 — Run and recover assigned agents](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm4--run-and-recover-assigned-agents); [SVC-PM5 — Apply shared process definitions](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm5--apply-shared-process-definitions); [CLI-PM1 — Connected multi-project CLI workspace](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm1--connected-multi-project-cli-workspace); [CLI-PM2 — Reliable project questions and answers](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm2--reliable-project-questions-and-answers); [REG-PM1 — Register and confirm a project through the CLI](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm1--register-and-confirm-a-project-through-the-cli); [REG-PM2 — Update a registration without losing approved history](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm2--update-a-registration-without-losing-approved-history); [REG-PM3 — Recover registration without losing decisions or exceeding limits](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm3--recover-registration-without-losing-decisions-or-exceeding-limits); [ARC-PM1 — Establish the project's architectural foundations](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm1--establish-the-projects-architectural-foundations); [ARC-PM2 — Produce a bounded and parallel-ready work breakdown](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm2--produce-a-bounded-and-parallel-ready-work-breakdown); [ARC-PM3 — Review and confirm the development breakdown](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm3--review-and-confirm-the-development-breakdown); [EXE-PM1 — Deliver independently reviewed work packets](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm1--deliver-independently-reviewed-work-packets); [EXE-PM2 — Integrate work and deliver declared dependencies](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm2--integrate-work-and-deliver-declared-dependencies); [EXE-PM3 — Resolve architectural gaps within authorized scope](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm3--resolve-architectural-gaps-within-authorized-scope).

### Connected acceptance requirements

Bind the exact operator test catalog, set up isolated resources and run the declared checks against the actual milestone candidate. Record real input lineage and artifacts, retain UNTESTED distinctly and prove it cannot promote. Report a genuine gap, perform scoped correction with retained budgets, reintegrate and rerun affected evidence. Promote only an eligible passing exact revision under existing merge authority. Interrupt QA/promotion, reconcile and resume without duplicate effects; completed Execution and monitoring cite durable evidence and exact product history.

### Data, evidence and essential failures

Actual approved test environments, secret/network names and QA repository access. Retain setup/check/cleanup status, inputs/hashes, run artifacts, gap/review/correction lineage, promotion Git evidence and final outcome matrix. Reset/cleanup is limited to approved run-owned targets; required evidence survives cleanup. Re-run the earlier connected journeys against the assembled product through the acceptance harness.

### Advancement

Meet the common completion boundary for this contribution. Record exact candidate/review/QA evidence and any unavailable required path. No packet count, generated result or unbound QA proposal is evidence of this milestone passing.
