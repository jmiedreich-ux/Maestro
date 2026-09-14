# SVC — Runtime Service Milestone Declaration

## Declaration identity

| Field | Value |
|---|---|
| Project | Maestro |
| Declaration | SVC — Runtime service |
| Declaration version | 2 |
| Status | Proposed outcomes; no recorded implementation completion |
| Architecture source | `docs/maestro-architecture.md` |

## Capability and scope

This declaration delivers the continuously running Python service on the Linux AI box. It owns installation and service configuration, durable project/activity/request records, the local API and event delivery, and the mechanics of supervising assigned agents.

The [CLI declaration](maestro-cli-project-milestones.md) owns terminal installation, presentation, navigation, input, and connection behavior. The [registration declaration](maestro-registration-project-milestones.md) owns registration intake, architectural assessment and fidelity decisions, package records and publication, confirmation, and re-registration. The [architecture-loop declaration](maestro-architecture-loop-project-milestones.md) owns its persistent-session integration, investigation, structure, breakdown, and confirmation. These processes use the shared runtime mechanisms; they do not deliver duplicate service implementations.

| Delivery owner | Included responsibility |
|---|---|
| Runtime service | Service account and startup, SQL storage and transactions, request receipts, API transport and dispatch, saved event delivery, project start reservations, agent tool adapters, run isolation, supervision, technical configuration, and recovery mechanics. |
| CLI | Terminal controls, displayed states, commands, question forms, attention navigation, and sending requests to the service. |
| Registration | Source and scope interpretation, required assessment/review content, registration eligibility and review budget, package schemas and GitHub publication, activation, registration-specific action validation, and use of runtime reservations/recovery. |

Generic service storage persists process-defined records; each process owns their meaning and required fields. SVC-PM5 — Apply shared process definitions adds common configurable handling. Registration retains its package publication policy and schemas while using shared validation, saving, and recovery mechanisms. The runtime implements shared validation/transaction mechanisms; registration supplies the process-specific rules. General software Execution policy, a full development scheduler, command center, mobile UI, and development breakdown are excluded.

### Development order and connected acceptance

The ordered service outcomes below describe implementation dependencies. Service foundation and API implementation support CLI development. CLI implementation remains before registration development. The agent-running capability must be implemented before registration can use real architect and reviewer runs.

Final connected acceptance of SVC-PM2 — Preserve project activity and requests, SVC-PM3 — Connect the CLI to recorded service activity, and SVC-PM4 — Run and recover assigned agents is shared with the relevant registration journeys. Their interfaces can be implemented and checked before final acceptance. Registration does not depend on its own completed acceptance evidence as a prerequisite to development.

Initial registration supplies real projects, questions, and agent work. REG-PM1 — Register and confirm a project through the CLI supplies the successful initial journey; REG-PM2 — Update a registration without losing approved history supplies idle-reservation evidence; REG-PM3 — Recover registration without losing decisions or exceeding limits supplies connected interruption and retry evidence. No temporary project generator, fake review, or manual database edit completes those outcomes.

Verification follows `docs/planning-guide/README.md#verification-expectations`: basic real journeys and essential failures, with necessary simulated conditions identified. Multiple criteria may share evidence. Live verification is deferred to development.

Existing-code condition remains as recorded in the [project overview](maestro-project-overview.md). Relevant source is assessed during development preparation for reuse or amendment; no existing component is assumed ready. Each completion record identifies the implementation revision, reproducible setup, observations, and required reviews. General implementation-review and acceptance authority remain provisional for separate Execution design. Unresolved behavior or authority must be settled before affected breakdown; implementation and operational checks are not prerequisites to this documentation.

## Milestones and order

| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |
|---|---|---|---|
| 1 | SVC-PM1 — Operate the persistent Maestro service | 1 | `docs/maestro-runtime-service-project-milestones.md#svc-pm1--operate-the-persistent-maestro-service` |
| 2 | SVC-PM2 — Preserve project activity and requests | 1 | `docs/maestro-runtime-service-project-milestones.md#svc-pm2--preserve-project-activity-and-requests` |
| 3 | SVC-PM3 — Connect the CLI to recorded service activity | 1 | `docs/maestro-runtime-service-project-milestones.md#svc-pm3--connect-the-cli-to-recorded-service-activity` |
| 4 | SVC-PM4 — Run and recover assigned agents | 1 | `docs/maestro-runtime-service-project-milestones.md#svc-pm4--run-and-recover-assigned-agents` |
| 5 | SVC-PM5 — Apply shared process definitions | 1 | `docs/maestro-runtime-service-project-milestones.md#svc-pm5--apply-shared-process-definitions` |

## SVC-PM1 — Operate the persistent Maestro service

**Outcome:** The service can be installed, started, inspected, and restarted on the Linux AI box without relying on an open CLI session.

**Included:** Python service installation, service account, filesystem access, systemd unit, startup configuration, boot/crash behavior, and clear startup failures.

**Excluded:** Terminal UI, project workflows, agent dispatch, and a new health dashboard or health API.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Continuous service and CLI independence | `docs/maestro-architecture.md#runtime-and-prerequisites` |
| Service responsibilities | `docs/maestro-architecture.md#components-and-responsibilities` |
| Agent configuration and launch availability | `docs/maestro-architecture.md#adapter-configuration` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Linux AI box and systemd | `docs/maestro-architecture.md#runtime-and-prerequisites` | Installed condition unverified; service setup and required access are delivered here. |
| Service configuration | `docs/maestro-architecture.md#adapter-configuration` | Contract specified; installation supplies applicable settings and credential references without exposing secrets. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Installation instructions are followed | Service software, account, configuration locations, and required filesystem permissions are installed without hidden setup steps. | Installed revision, documented steps, actual account and access checks without secret values. | None |
| The machine boots or the service crashes | systemd starts or restarts the service as specified. Service operation does not depend on a terminal session. | Basic boot and controlled crash/restart observations with systemd status and startup logs. | None |
| Startup or configuration fails | The failure is visible and identifies the missing prerequisite. Agent configuration errors disable launch as specified, not silently select other settings. | A necessary configuration/access failure with its actual error and recovery after correction. | None |
| The operator inspects service health | systemd status and service logs distinguish running, failed, and restarting behavior; a running process is not reported as proof of registration readiness. | Actual service status and startup diagnostics. Connected API readiness is accepted under SVC-PM3 — Connect the CLI to recorded service activity. | None |

### Definition of done

Installation and systemd operation work on the AI box with reproducible setup and essential failure evidence. This establishes the persistent host service only; it does not claim working registration or connected agent execution. Completion evidence follows the common requirements above.

### Unresolved details

No additional service-lifecycle behavior is proposed. Exact installation packaging, unit settings, and permission setup are implementation work against the architecture. General delivery-review authority remains provisional as described above.

## SVC-PM2 — Preserve project activity and requests

**Outcome:** Project records and accepted requests survive service restarts, retain their identities, and cannot be applied twice or to the wrong project.

**Included:** Physical SQL storage, project/activity identities, conversations, questions and results, transactional request acceptance, pending delivery, event records, and atomic project start reservations.

**Excluded:** Registration-specific schema meaning, source assessment, GitHub package publication, and general Execution scheduling.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Authoritative records and save order | `docs/maestro-architecture.md#record-ownership`; `docs/maestro-architecture.md#save-and-delivery-sequence` |
| Answers, identity, and recovery | `docs/maestro-architecture.md#answer-identity-and-uncertain-delivery` |
| Project start reservation | `docs/maestro-architecture.md#re-registration` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Persistent service | SVC-PM1 — Operate the persistent Maestro service | Required implementation predecessor. |
| Connected read/write access | SVC-PM3 — Connect the CLI to recorded service activity | Downstream interface for final acceptance, not an implementation prerequisite for storage. |
| Real registration records and idle checks | REG-PM1 — Register and confirm a project through the CLI; REG-PM2 — Update a registration without losing approved history | Registration defines and produces process records and applies idle-only rules; connected evidence is shared. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Two projects exchange questions and answers | SQL saves project/activity/question/request identities and content before acknowledgment. No answer or result crosses project boundaries. | Real initial-registration records correlated with API requests and CLI output for both projects. | None |
| A receipt is lost or a request is repeated | Same request/content returns its saved result; conflicting content is rejected. An answer is accepted once and pending delivery survives restart. | Necessary lost-acknowledgment and restart observations using real service records. | None |
| The service restarts after saving | Accepted conversations, decisions, request results, and pending delivery remain retrievable. Read-only retrieval does not create duplicate records. | Before/after SQL and service responses connected to the CLI. | None |
| Re-registration competes with a project start | One transaction checks/reserves the project; simultaneous starts cannot slip through. Unknown run state is not idle. Other projects remain available. | Actual service-boundary contention and the REG-PM2 — Update a registration without losing approved history journey; no extra execution command is assumed. | None |

### Definition of done

Connected CLI and registration evidence demonstrates durable records, isolated projects, and nonduplicated request effects. A database existing or isolated table checks alone are insufficient. Storage and reservation mechanics are implemented here; registration decides when its process may reserve or release the project.

### Unresolved details

Physical SQL tables and storage implementation remain development work. Database backup/restore procedures are still unresolved in the architecture; restart evidence must not be presented as proof of disaster recovery. General delivery-review authority remains provisional.

## SVC-PM3 — Connect the CLI to recorded service activity

**Outcome:** The CLI can retrieve real project activity, send supported requests, and receive saved updates through the local service API.

**Included:** Loopback HTTP service, defined reads and request envelope, operation dispatch, error responses, SSE delivery, cursors, replay, and heartbeat behavior.

**Excluded:** Terminal rendering and input controls; registration-specific operation decisions and package payload validation.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Local connection and API contract | `docs/maestro-architecture.md#system-connections`; `docs/maestro-architecture.md#cli-request-and-event-contract` |
| Connection loss and recorded updates | `docs/maestro-architecture.md#cli-connection-configuration`; `docs/maestro-architecture.md#open-and-use-the-workspace` |
| Answer journey | `docs/maestro-architecture.md#answer-a-project-question` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Saved records and request acceptance | SVC-PM2 — Preserve project activity and requests | Required implementation predecessor. |
| CLI workspace and answers | CLI-PM1 — Connected multi-project CLI workspace; CLI-PM2 — Reliable project questions and answers | CLI owns the client; interfaces are developed before shared final integration. |
| Real registration operations | REG-PM1 — Register and confirm a project through the CLI | Registration supplies operation handlers and records for final connected acceptance. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| An installed CLI connects to an empty service | The configured loopback API returns a genuine empty workspace. Failure returns a clear error, not an empty result. | Installed CLI/service connection, empty state, and necessary failure observation. | None |
| Real activity exists | Defined reads return correct identities, data, and cursors; requests dispatch to the proper process and return saved receipts or specified errors. | Actual registration activity and question/answer journey through CLI, API, and SQL. | None |
| Updates occur during connection or reconnection | Events are sent only after SQL commit; snapshot plus replay loses no recorded updates, and repeated event IDs are ignored. | Basic disconnect/reconnect while real activity changes, with correlated event identities and visible CLI results. | None |
| A connection becomes quiet or breaks | Heartbeats and loss detection follow the architecture. Client exit does not stop service work or replay submissions. | Defined heartbeat timing and actual CLI exit/reconnection; service continues independently. | None |

### Definition of done

The actual CLI uses the implemented service API and saved events for the main initial-registration and answer journeys. Endpoint stubs, sample responses, or streamed text without saved records do not establish completion. The CLI owns its presentation checks; shared journey evidence can satisfy both declarations.

### Unresolved details

No new API behavior is introduced. Executable API validation and transport handling are implementation work; registration handlers remain an explicit dependency. General delivery-review authority remains provisional.

## SVC-PM4 — Run and recover assigned agents

**Outcome:** The service runs the selected registration architect or reviewer in the correct workspace, returns validated outputs, and stops or recovers work without losing records or launching duplicates.

**Included:** Codex and Claude Code adapters, exact model checks, immutable assignments, protected workspaces, separate run identities, supervisor units, output collection, progress, timeouts, technical retries, stopping, and supervisor recovery.

**Excluded:** Agent judgment, registration review/activation decisions, package publication policy, software implementation agents, and general Execution policy.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Launch, model checks, and workspaces | `docs/maestro-architecture.md#model-execution-adapters` |
| Process supervision and restart | `docs/maestro-architecture.md#process-supervision-and-interruption-recovery` |
| Response identity and validation | `docs/maestro-architecture.md#registration-agent-response-contract` |
| Technical limits and retries | `docs/maestro-architecture.md#technical-recovery`; `docs/maestro-architecture.md#activity-retry-request` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Storage and connected interface | SVC-PM2 — Preserve project activity and requests; SVC-PM3 — Connect the CLI to recorded service activity | Required implementation foundation and interface for recorded progress/results. |
| Installed tools and credentials | `docs/maestro-architecture.md#tool-and-model-selection`; `docs/maestro-architecture.md#adapter-configuration` | Current readiness unknown; installing and configuring both selected tool routes is included here. |
| Real role assignments and recovery actions | REG-PM1 — Register and confirm a project through the CLI; REG-PM3 — Recover registration without losing decisions or exceeding limits | Registration supplies role contracts, process decisions, and connected journey evidence; adapter implementation precedes its use. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Registration supplies an assignment | Selected tool/model evidence, exact source, fixed assignment, and isolated run/output identities match. Unsupported or unverifiable configuration prevents acceptance as specified. | Real architect and independent reviewer runs; exercise both tool routes without requiring every tool/model combination. | None |
| An agent reads inputs and returns work | Inputs remain read-only, permitted output is writable, and another run's workspace is inaccessible. The exact assessment/candidate and structured response reach registration validation. | Actual file access results and verified artifact identities/hashes; agent prose alone is insufficient. | None |
| Agent progress or completion arrives | Progress is recorded before CLI display. A successful tool exit or progress message cannot substitute for validated completion; stale run output cannot update current work. | Correlated supervisor, SQL, and CLI records, including one necessary invalid or late-result case. | None |
| Stopping or a deadline occurs | Apply the registration-only 30-minute defaults and specified stopping behavior; child termination is confirmed before replacement. Unknown state blocks replacement. | Basic real stop and controlled timeout evidence; a shorter configured duration may exercise timeout behavior. | None |
| A run or the main service is interrupted | Reconcile the original supervisor/run, preserve the deadline and retry count, and replay saved events once. Recovery follows cause-based limits; manual retry does not reset them. | Connected REG-PM3 — Recover registration without losing decisions or exceeding limits evidence for crash, restart, recovery attention/action, and no duplicate run. | None |

### Definition of done

Real registration agent assignments use the service adapters and return usable verified outputs. Connected recovery evidence demonstrates the agreed limits and actual child-process stopping. Tool installation or a standalone model response is insufficient. The service supplies mechanics; registration retains judgment, review budgets, and activation authority.

### Unresolved details

Installed capability and isolation checks are development verification. If a tool cannot meet the specified exact-model or stopping contract, report the concrete limitation rather than silently weaken it. General software Execution policy remains outside this outcome.

## SVC-PM5 — Apply shared process definitions

**Outcome:** Registration and the architecture loop use one validated TOML file to direct common runtime behavior while preserving their different process rules.

**Included:** Process-definition validation and snapshots; shared initiation, output, review, confirmation, and recovery dispatch; supported policy/schema/destination references; process-specific integration.

**Excluded:** New execution policy, arbitrary scripted workflows, process-specific architectural judgment, and separate copies of registration or architecture-loop record schemas.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Configuration drives supported runtime capabilities | `docs/maestro-architecture.md#shared-process-definitions` |
| Correct output validation, storage, and process boundaries | `docs/maestro-architecture.md#shared-output-handling-and-process-boundaries` |
| Registration integration | `docs/maestro-architecture.md#registration` |
| Architecture-loop integration | `docs/maestro-architecture.md#architecture-loop` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Records, transport, and supervised agents | SVC-PM2 — Preserve project activity and requests; SVC-PM3 — Connect the CLI to recorded service activity; SVC-PM4 — Run and recover assigned agents | Shared implementation foundation; new process dispatch is delivered here. |
| Registration policies and package meaning | REG-PM1 — Register and confirm a project through the CLI; REG-PM3 — Recover registration without losing decisions or exceeding limits | Registration supplies its handlers, schemas, and connected evidence. |
| Persistent-session and breakdown use | ARC-PM1 — Establish the project's architectural foundations; ARC-PM3 — Review and confirm the development breakdown | Architecture loop owns its session continuation and process-specific outputs; shared handlers are delivered here. |

Implement the common interfaces before their process integrations. Final acceptance uses those integrations together; prior final acceptance of a dependent process is not an implementation prerequisite.

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| A configured process starts | Its validated sections select the correct prerequisites, role/session rules, outputs, review, confirmation, and recovery handlers. Registration and architecture retain their different behavior. | Real registration and architecture-loop activities, effective definitions and correlated runtime records. | None |
| Configuration is invalid or changes during work | Invalid definitions prevent the affected new process with a clear error. An active process retains its definition, budget, and authority snapshot; read-only views remain available. | One essential invalid-definition case and an edit between activity starts showing preserved versus new snapshots. | None |
| A process returns its required outputs | Shared handling validates structure, identities, permitted locations, versions, and process-specific meaning before reporting the set saved. | Actual registration package and architecture output records; necessary missing/invalid-output rejection. | None |
| Review, publication, or confirmation is repeated or interrupted | Use the selected process contract without duplicate effects, budget resets, unverified publication, or unintended execution. | Basic connected recovery evidence shared with the process declarations, not an exhaustive failure suite. | None |

### Definition of done

Both real processes use the common runtime handling and their own recorded definitions. Merely parsing TOML, hardcoding a separate output path for each process, or completing registration alone does not satisfy this outcome. Evidence follows the declaration's common requirements; live verification belongs to development.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Architecture-loop process contracts | Full integration cannot be accepted from the high-level definition alone. | Resolve the linked architecture-loop session, output, confirmation, and initiation gaps before affected breakdown. |
| Executable definition schema and handler mapping | The runtime must validate and execute the documented behavior. | Implement schema validation and handler mappings; this does not require live checks during documentation. |

## Partial-registration boundary

No narrower portion is declared. A subset must identify its included outcomes, external dependencies, relevant journeys, and acceptance coverage before registration confirmation. Acceptance of the service foundation alone does not establish the complete runtime, CLI, or registration capability.
