# Maestro manual architecture — work breakdown

Draft version 3. The Owner-confirmed manual registration covers 18 project outcomes. This index expands that scope into 42 proposed coding packets and seven development milestones. It is not a runtime assignment, a complete confirmed architecture breakdown or permission to start implementation.

## Controlling records

- [Common packet rules](packet-rules.md): exact baseline, authority, common interfaces, file ownership, execution requirements and completion evidence. Incorporated into every packet.
- [Development milestones](development-milestones.md): allocation, delivery order, connected acceptance requirements and outcome completion boundary.
- [Investigation](investigation.md) and [project structure](project-structure.md): inspected evidence and source boundaries.
- [Seven milestone QA plans](qa-plans/README.md): assembled checks, expected results, test data, evidence and cleanup; verified operator bindings and remaining implementation-time runtime conversion are explicit.
- [QA resource preparation](qa-resources.md): verified QA repository, service App, installed agent routes, local models, isolated roots and remaining service/setup implementation.

Each linked packet is the canonical specification for its purpose, required inputs, architecture/outcome references, dependencies, exact outputs, execution requirements, success criteria and verification command. This index intentionally does not duplicate those fields.

## Packet allocation

### Connected service and workspace

- [Service persistence](work-packets/store.md)
- [Owner authentication](work-packets/owner-auth.md)
- [Durable request delivery](work-packets/requests.md)
- [Project and activity records](work-packets/activities.md)
- [Event stream](work-packets/events.md)
- [Linux installation](work-packets/install.md)
- [Terminal connection](work-packets/terminal-connection.md)
- [Terminal workspace](work-packets/terminal-workspace.md)
- [Linked questions](work-packets/questions.md)

### Supervised shared processes

- [Shared process policy](work-packets/process-policy.md)
- [Agent route preflight](work-packets/agent-routes.md)
- [Agent workspace and transport](work-packets/agent-transport.md)
- [Durable supervision](work-packets/supervision.md)
- [Session and context continuity](work-packets/sessions.md)

### Confirmed registration and history

- [Exact source intake](work-packets/source-intake.md)
- [Publication journal](work-packets/publication.md)
- [Registration assessment](work-packets/registration-assessment.md)
- [Registration confirmation](work-packets/registration-confirmation.md)
- [Registration update and recovery](work-packets/registration-recovery.md)

### Confirmed development planning

- [QA resource catalog](work-packets/qa-catalog.md)
- [Architecture session entry](work-packets/architecture-entry.md)
- [Architecture foundations](work-packets/architecture-foundations.md)
- [Breakdown schema and validation](work-packets/breakdown-records.md)
- [Architecture review and confirmation](work-packets/architecture-confirmation.md)
- [Architecture reconciliation](work-packets/architecture-recovery.md)

### Independently reviewed packet delivery

- [Execution contracts and start](work-packets/execution-start.md)
- [Development Manager planning](work-packets/work-planning.md)
- [Coder plan and result delivery](work-packets/coder-delivery.md)
- [Independent packet review](work-packets/packet-review.md)
- [Execution architectural determinations](work-packets/determinations.md)
- [Pause and graceful stop](work-packets/execution-stop.md)
- [Lifecycle monitoring](work-packets/execution-monitoring.md)

### Integrated code and dependency delivery

- [Integration queue](work-packets/integration-queue.md)
- [Dependency delivery](work-packets/dependencies.md)
- [Missing specialist support](work-packets/specialist-support.md)

### Verified milestone completion

- [Isolated QA setup](work-packets/qa-environment.md)
- [QA data and check runner](work-packets/qa-checks.md)
- [Durable QA artifacts](work-packets/qa-artifacts.md)
- [Milestone gaps and correction](work-packets/milestone-gaps.md)
- [Milestone promotion](work-packets/promotion.md)
- [Execution recovery and completion](work-packets/execution-recovery.md)
- [Connected acceptance tooling](work-packets/acceptance-tooling.md)

## Outcome traceability

This table identifies contributing packets, not delivered outcomes. Read the complete pinned declaration for its dependencies, acceptance and definition of done. The final milestone reconciles all 18 outcomes against assembled evidence.

| Project outcome | Contributing packet specifications |
|---|---|
| [ARC-PM1 — Establish the project's architectural foundations](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm1--establish-the-projects-architectural-foundations) | [Session and context continuity](work-packets/sessions.md); [Architecture session entry](work-packets/architecture-entry.md); [Architecture foundations](work-packets/architecture-foundations.md) |
| [ARC-PM2 — Produce a bounded and parallel-ready work breakdown](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm2--produce-a-bounded-and-parallel-ready-work-breakdown) | [QA resource catalog](work-packets/qa-catalog.md); [Breakdown schema and validation](work-packets/breakdown-records.md) |
| [ARC-PM3 — Review and confirm the development breakdown](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/architecture-loop-milestones.md#arc-pm3--review-and-confirm-the-development-breakdown) | [Architecture review and confirmation](work-packets/architecture-confirmation.md); [Architecture reconciliation](work-packets/architecture-recovery.md) |
| [CLI-PM1 — Connected multi-project CLI workspace](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm1--connected-multi-project-cli-workspace) | [Project and activity records](work-packets/activities.md); [Event stream](work-packets/events.md); [Terminal connection](work-packets/terminal-connection.md); [Terminal workspace](work-packets/terminal-workspace.md) |
| [CLI-PM2 — Reliable project questions and answers](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm2--reliable-project-questions-and-answers) | [Linked questions](work-packets/questions.md) |
| [EXE-PM1 — Deliver independently reviewed work packets](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm1--deliver-independently-reviewed-work-packets) | [Execution contracts and start](work-packets/execution-start.md); [Development Manager planning](work-packets/work-planning.md); [Coder plan and result delivery](work-packets/coder-delivery.md); [Independent packet review](work-packets/packet-review.md); [Lifecycle monitoring](work-packets/execution-monitoring.md) |
| [EXE-PM2 — Integrate work and deliver declared dependencies](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm2--integrate-work-and-deliver-declared-dependencies) | [Integration queue](work-packets/integration-queue.md); [Dependency delivery](work-packets/dependencies.md); [Milestone promotion](work-packets/promotion.md) |
| [EXE-PM3 — Resolve architectural gaps within authorized scope](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm3--resolve-architectural-gaps-within-authorized-scope) | [Execution architectural determinations](work-packets/determinations.md); [Missing specialist support](work-packets/specialist-support.md); [Milestone gaps and correction](work-packets/milestone-gaps.md) |
| [EXE-PM4 — Verify milestones and publish completed Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm4--verify-milestones-and-publish-completed-execution) | [QA resource catalog](work-packets/qa-catalog.md); [Isolated QA setup](work-packets/qa-environment.md); [QA data and check runner](work-packets/qa-checks.md); [Durable QA artifacts](work-packets/qa-artifacts.md); [Milestone gaps and correction](work-packets/milestone-gaps.md); [Milestone promotion](work-packets/promotion.md); [Execution recovery and completion](work-packets/execution-recovery.md); [Connected acceptance tooling](work-packets/acceptance-tooling.md) |
| [EXE-PM5 — Pause, stop and recover Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm5--pause-stop-and-recover-execution) | [Pause and graceful stop](work-packets/execution-stop.md); [Execution recovery and completion](work-packets/execution-recovery.md); [Lifecycle monitoring](work-packets/execution-monitoring.md) |
| [REG-PM1 — Register and confirm a project through the CLI](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm1--register-and-confirm-a-project-through-the-cli) | [Exact source intake](work-packets/source-intake.md); [Publication journal](work-packets/publication.md); [Registration assessment](work-packets/registration-assessment.md); [Registration confirmation](work-packets/registration-confirmation.md) |
| [REG-PM2 — Update a registration without losing approved history](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm2--update-a-registration-without-losing-approved-history) | [Registration update and recovery](work-packets/registration-recovery.md) |
| [REG-PM3 — Recover registration without losing decisions or exceeding limits](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm3--recover-registration-without-losing-decisions-or-exceeding-limits) | [Publication journal](work-packets/publication.md); [Registration update and recovery](work-packets/registration-recovery.md) |
| [SVC-PM1 — Operate the persistent Maestro service](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm1--operate-the-persistent-maestro-service) | [Service persistence](work-packets/store.md); [Owner authentication](work-packets/owner-auth.md); [Linux installation](work-packets/install.md) |
| [SVC-PM2 — Preserve project activity and requests](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm2--preserve-project-activity-and-requests) | [Service persistence](work-packets/store.md); [Durable request delivery](work-packets/requests.md); [Project and activity records](work-packets/activities.md); [Linked questions](work-packets/questions.md); [Publication journal](work-packets/publication.md) |
| [SVC-PM3 — Connect the CLI to recorded service activity](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm3--connect-the-cli-to-recorded-service-activity) | [Owner authentication](work-packets/owner-auth.md); [Durable request delivery](work-packets/requests.md); [Project and activity records](work-packets/activities.md); [Event stream](work-packets/events.md); [Terminal connection](work-packets/terminal-connection.md) |
| [SVC-PM4 — Run and recover assigned agents](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm4--run-and-recover-assigned-agents) | [Agent route preflight](work-packets/agent-routes.md); [Agent workspace and transport](work-packets/agent-transport.md); [Durable supervision](work-packets/supervision.md); [Session and context continuity](work-packets/sessions.md) |
| [SVC-PM5 — Apply shared process definitions](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm5--apply-shared-process-definitions) | [Shared process policy](work-packets/process-policy.md); [Agent route preflight](work-packets/agent-routes.md) |

## Remaining full-breakdown work

The seven manual milestone QA procedures are specified and the concrete operator QA resources are verified. Runtime conversion, service validation, setup scripts and test results remain assigned implementation work, not missing manual design. The 42 packet specifications and seven development milestones retain their completed independent review coverage. Exact Owner confirmation is now required before considering this manual architecture breakdown confirmed. Confirmation does not import runtime records or start Execution. Current discussion, publication and review coverage remain in the handoff.
