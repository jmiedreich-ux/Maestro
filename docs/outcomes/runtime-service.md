# Runtime Service outcomes

## Capability and scope

This outcome area delivers the continuously running Python service on the Linux AI box. It owns installation and service configuration, durable project/activity/request records, the local API and event delivery, and the mechanics of supervising assigned agents.

The [CLI outcomes](cli.md) owns terminal installation, presentation, navigation, input, and connection behavior. The [registration outcomes](registration.md) owns registration intake, architectural assessment and fidelity decisions, package records and publication, confirmation, and re-registration. The [architecture-loop outcomes](architecture-loop.md) owns its persistent-session integration, investigation, structure, breakdown, and confirmation. These processes use the shared runtime mechanisms; they do not deliver duplicate service implementations.

| Delivery owner | Included responsibility |
|---|---|
| Runtime service | Service account and startup, SQL storage and transactions, request receipts, API transport and dispatch, saved event delivery, project start reservations, agent tool adapters, run isolation, supervision, technical configuration, and recovery mechanics. |
| CLI | Terminal controls, displayed states, commands, question forms, attention navigation, and sending requests to the service. |
| Registration | Source and scope interpretation, required assessment/review content, registration eligibility and review budget, package schemas and GitHub publication, activation, registration-specific action validation, and use of runtime reservations/recovery. |

Generic service storage persists process-defined records; each process owns their meaning and required fields. Apply shared process definitions adds common configurable handling. Registration retains its package publication policy and schemas while using shared validation, saving, and recovery mechanisms. The runtime implements shared validation/transaction mechanisms; registration supplies the process-specific rules. Execution implementation, a full development scheduler, command center, mobile UI, and development breakdown are excluded from this outcome area.

### Development order and connected acceptance

The ordered service outcomes below describe implementation dependencies. Service foundation and API implementation support CLI development. CLI implementation remains before registration development. The agent-running capability must be implemented before registration can use real architect and reviewer runs.

Final connected acceptance of Preserve project activity and requests, Connect the CLI to recorded service activity, and Run and recover assigned agents is shared with the relevant registration journeys. Their interfaces can be implemented and checked before final acceptance. Registration does not depend on its own completed acceptance evidence as a prerequisite to development.

Initial registration supplies real projects, questions, and agent work. Register and confirm a project through the CLI supplies the successful initial journey; Update a registration without losing approved history supplies idle-reservation evidence; Recover registration without losing decisions or exceeding limits supplies connected interruption and retry evidence. No temporary project generator, fake review, or manual database edit completes those outcomes.

Verification follows `docs/planning-guide/README.md#verification-expectations`: basic real journeys and essential failures, with necessary simulated conditions identified. Multiple criteria may share evidence. Live verification is deferred to development.

Existing-code condition remains as recorded in the [project overview](../project-overview.md). Relevant source is assessed during development preparation for reuse or amendment; no existing component is assumed ready. Each completion record identifies the implementation revision, reproducible setup, observations, and required reviews. Implementation review, milestone Quality Assurance, promotion and completion authority follow the defined [Execution architecture](../architecture.md#execution) when this work is later executed; they are not additional runtime-service milestone scope. Unresolved behavior or authority must be settled before affected breakdown; implementation and operational checks are not prerequisites to this documentation.

## Outcomes

## Operate the persistent Maestro service

**Outcome:** The service can be installed, started, inspected, and restarted on the Linux AI box without relying on an open CLI session.

**Included:** Python service installation, service account, filesystem access, systemd unit, startup configuration, boot/crash behavior, and clear startup failures.

**Excluded:** Terminal UI, project workflows, agent dispatch, and a new health dashboard or health API.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Continuous service and CLI independence | `docs/architecture.md#runtime-and-prerequisites` |
| Service responsibilities | `docs/architecture.md#components-and-responsibilities` |
| Agent configuration and launch availability | `docs/architecture.md#adapter-configuration` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Linux AI box and systemd | `docs/architecture.md#runtime-and-prerequisites` | Installed condition unverified; service setup and required access are delivered here. |
| Service configuration | `docs/architecture.md#adapter-configuration` | Contract specified; installation supplies applicable settings and credential references without exposing secrets. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Installation instructions are followed | Service software, account, configuration locations, required filesystem permissions, and the schema bundles specified by [installed validation schemas](../architecture.md#installed-validation-schemas) are installed without hidden setup steps. | Installed revision, documented steps, actual account and access checks without secret values. | None |
| The machine boots or the service crashes | systemd starts or restarts the service as specified. Service operation does not depend on a terminal session. | Basic boot and controlled crash/restart observations with systemd status and startup logs. | Boot and crash restart are configured (enabled at boot, restart on failure after 5 seconds) but not yet observed. Observing them needs a controlled crash test and a reboot; addressed later. |
| Startup or configuration fails | The failure is visible and identifies the missing prerequisite. Agent configuration errors disable launch as specified, not silently select other settings. | A necessary configuration/access failure with its actual error and recovery after correction. | The service does not yet validate agent routes at startup, so an invalid route is not reported as a launch-disabling error. Agent launch is outside this outcome; addressed with agent dispatch. |
| The operator inspects service health | systemd status and service logs distinguish running, failed, and restarting behavior; a running process is not reported as proof of registration readiness. | Actual service status and startup diagnostics. Connected API readiness is accepted under Connect the CLI to recorded service activity. | Only the running state has been observed; the failed and restarting states follow the crash test above. |
| Owner access is installed | Provision the protected local CLI credential and service digest; agent identities cannot read or use the Owner credential. Follow `docs/architecture.md#local-owner-identity-and-credentials`. | Actual installation and essential access-denial evidence without exposing secrets. | None |

### Definition of done

Installation and systemd operation work on the AI box with reproducible setup and essential failure evidence. This establishes the persistent host service only; it does not claim working registration or connected agent execution. Completion evidence follows the common requirements above.

### Unresolved details

No additional service-lifecycle behavior is proposed. Exact installation packaging, unit settings, and permission setup are implementation work against the architecture. Delivery review and acceptance follow the defined Execution architecture when this outcome is implemented.

## Preserve project activity and requests

**Outcome:** Project records and accepted requests survive service restarts, retain their identities, and cannot be applied twice or to the wrong project.

**Included:** SQLite storage under [SQLite storage](../architecture.md#sqlite-storage), project/activity identities, conversations, questions and results, transactional request acceptance, pending delivery, event records, and atomic project start reservations.

**Excluded:** Registration-specific schema meaning, source assessment, GitHub package publication, and general Execution scheduling.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Authoritative records and save order | `docs/architecture.md#record-ownership`; `docs/architecture.md#save-and-delivery-sequence` |
| Answers, identity, and recovery | `docs/architecture.md#answer-identity-and-uncertain-delivery` |
| Project start reservation | `docs/architecture.md#re-registration` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Persistent service | Operate the persistent Maestro service | Required implementation predecessor. |
| Connected read/write access | Connect the CLI to recorded service activity | Downstream interface for final acceptance, not an implementation prerequisite for storage. |
| Real registration records and idle checks | Register and confirm a project through the CLI; Update a registration without losing approved history | Registration defines and produces process records and applies idle-only rules; connected evidence is shared. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Two projects exchange questions and answers | SQL saves project/activity/question/request identities and content before acknowledgment. No answer or result crosses project boundaries. | Real initial-registration records correlated with API requests and CLI output for both projects. | None |
| A receipt is lost or a request is repeated | Same request/content returns its saved result; conflicting content is rejected. An answer is accepted once and pending delivery survives restart. | Necessary lost-acknowledgment and restart observations using real service records. | None |
| The service restarts after saving | Accepted conversations, decisions, request results, and pending delivery remain retrievable. Read-only retrieval does not create duplicate records. | Before/after SQL and service responses connected to the CLI. | None |
| Re-registration competes with a project start | One transaction checks/reserves the project; simultaneous starts cannot slip through. Unknown run state is not idle. Other projects remain available. | Actual service-boundary contention and the Update a registration without losing approved history journey; no extra execution command is assumed. | None |
| Findings and Owner decisions are saved | Preserve stable finding mappings, exact versions, action receipts and allowance consumption through replay and restart. | Shared registration and architecture-loop records show unchanged identities and no duplicate grants. | None |
| Runtime performance observations arrive or replay | SQL records exact role/tool/model and work identities, time, input/output usage, context readings and measurement quality. Normalize counter scopes without double-counting; incomplete totals stay partial. | Main real run plus replay/restart evidence under `docs/architecture.md#agent-performance-and-context-management`; unknown readings are not zero. | None |

### Definition of done

Connected CLI and registration evidence demonstrates durable records, isolated projects, and nonduplicated request effects. A database existing or isolated table checks alone are insufficient. Storage and reservation mechanics are implemented here; registration decides when its process may reserve or release the project.

### Unresolved details

SQLite tables and storage implementation remain development work. Delivery evidence must show the configured local database, service-owned writes, committed records surviving service restart, and competing project-start requests producing only one reservation under [SQLite storage](../architecture.md#sqlite-storage). SQL backup and restore are out of scope. Ordinary service restart and recorded-operation recovery remain included. Delivery review and acceptance follow the defined Execution architecture.

## Connect the CLI to recorded service activity

**Outcome:** The CLI can retrieve real project activity, send supported requests, and receive saved updates through the local service API.

**Included:** Loopback HTTP service, defined reads and request envelope, operation dispatch, error responses, SSE delivery, cursors, replay, and heartbeat behavior.

**Excluded:** Terminal rendering and input controls; registration-specific operation decisions and package payload validation.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Local connection and API contract | `docs/architecture.md#system-connections`; `docs/architecture.md#cli-request-and-event-contract` |
| Connection loss and recorded updates | `docs/architecture.md#cli-connection-configuration`; `docs/architecture.md#open-and-use-the-workspace` |
| Answer journey | `docs/architecture.md#answer-a-project-question` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Saved records and request acceptance | Preserve project activity and requests | Required implementation predecessor. |
| CLI workspace and answers | Connected multi-project CLI workspace; Reliable project questions and answers | CLI owns the client; interfaces are developed before shared final integration. |
| Real registration operations | Register and confirm a project through the CLI | Registration supplies operation handlers and records for final connected acceptance. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| An installed CLI connects to an empty service | The configured loopback API returns a genuine empty workspace. Failure returns a clear error, not an empty result. | Installed CLI/service connection, empty state, and necessary failure observation. | None |
| Real activity exists | Defined reads return correct identities, data, and cursors; requests dispatch to the proper process and return saved receipts or specified errors. | Actual registration activity and question/answer journey through CLI, API, and SQL. | None |
| Updates occur during connection or reconnection | Events are sent only after SQL commit; snapshot plus replay loses no recorded updates, and repeated event IDs are ignored. | Basic disconnect/reconnect while real activity changes, with correlated event identities and visible CLI results. | None |
| A connection becomes quiet or breaks | Heartbeats and loss detection follow the architecture. Client exit does not stop service work or replay submissions. | Defined heartbeat timing and actual CLI exit/reconnection; service continues independently. | None |
| The CLI presents a credential | Validate the credential, derive the configured Owner identity and return the specified authorization errors; agent results cannot act as Owner requests. | Actual authorized request and essential missing/invalid credential checks. | None |

### Definition of done

The actual CLI uses the implemented service API and saved events for the main initial-registration and answer journeys. Endpoint stubs, sample responses, or streamed text without saved records do not establish completion. The CLI owns its presentation checks; shared journey evidence can satisfy both declarations.

### Unresolved details

No new API behavior is introduced. Executable API validation and transport handling are implementation work; registration handlers remain an explicit dependency. Delivery review and acceptance follow the defined Execution architecture.

## Run and recover assigned agents

**Outcome:** The service runs the selected registration architect or reviewer in the correct workspace, returns validated outputs, and stops or recovers work without losing records or launching duplicates.

**Included:** Codex and Claude Code adapters, exact model checks, immutable assignments, protected workspaces, separate run identities, supervisor units, output collection, progress, timeouts, technical retries, stopping, and supervisor recovery.

**Excluded:** Agent judgment, registration review/activation decisions, package publication policy, software implementation agents, and Execution implementation or policy changes.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Launch, model checks, and workspaces | `docs/architecture.md#model-execution-adapters` |
| Process supervision and restart | `docs/architecture.md#process-supervision-and-interruption-recovery` |
| Response identity and validation | `docs/architecture.md#registration-agent-response-contract` |
| Technical limits and retries | `docs/architecture.md#technical-recovery`; `docs/architecture.md#activity-retry-request` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Storage and connected interface | Preserve project activity and requests; Connect the CLI to recorded service activity | Required implementation foundation and interface for recorded progress/results. |
| Installed tools and credentials | `docs/architecture.md#tool-and-model-selection`; `docs/architecture.md#adapter-configuration` | Current readiness unknown; installing and configuring both selected tool routes is included here. |
| Real role assignments and recovery actions | Register and confirm a project through the CLI; Recover registration without losing decisions or exceeding limits | Registration supplies role contracts, process decisions, and connected journey evidence; adapter implementation precedes its use. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Registration supplies an assignment | Selected tool/model evidence, exact source, fixed assignment, and isolated run/output identities match. Unsupported or unverifiable configuration prevents acceptance as specified. | Real architect and independent reviewer runs; exercise both tool routes without requiring every tool/model combination. | None |
| An agent reads inputs and returns work | Inputs remain read-only, permitted output is writable, and another run's workspace is inaccessible. The exact assessment/candidate and structured response reach registration validation. | Actual file access results and verified artifact identities/hashes; agent prose alone is insufficient. | None |
| Agent progress or completion arrives | Progress is recorded before CLI display. A successful tool exit or progress message cannot substitute for validated completion; stale run output cannot update current work. | Correlated supervisor, SQL, and CLI records, including one necessary invalid or late-result case. | None |
| Stopping or a deadline occurs | Apply the registration-only 30-minute defaults and specified stopping behavior; child termination is confirmed before replacement. Unknown state blocks replacement. | Basic real stop and controlled timeout evidence; a shorter configured duration may exercise timeout behavior. | None |
| A run or the main service is interrupted | Reconcile the original supervisor/run, preserve the deadline and retry count, and replay saved events once. Recovery follows cause-based limits; manual retry does not reset them. | Connected Recover registration without losing decisions or exceeding limits evidence for crash, restart, recovery attention/action, and no duplicate run. | None |
| A permitted new run follows recovery | Same-run recovery keeps its deadline; a new eligible run receives its own saved duration. A recorded next-run exception is consumed once without resetting attempts. | Correlated run identities, deadlines, exception and counter records under `docs/architecture.md#run-deadlines-and-duration-exceptions`. | None |
| Context fills during an agent assignment | Apply configured thresholds, save a verified checkpoint, compact or safely replace context, and continue the same work without charging failure/correction/review allowances. Preserve remaining active-time budget, totals and source bindings. Unsafe or ineffective continuation pauses visibly. | One supported real capacity-continuation journey and essential inability-to-resume evidence; share persistent-session evidence with Establish the project's architectural foundations. Record the adapter's actual observation and control boundaries under [context readings and thresholds](../architecture.md#context-readings-and-thresholds), including stale readings during a long turn. Threshold enforcement does not promise mid-turn visibility or prevention of every capacity error. Provider-specific support is verified during implementation, not assumed. | None |

### Definition of done

Real registration agent assignments use the service adapters and return usable verified outputs. Connected recovery evidence demonstrates the agreed limits and actual child-process stopping. Tool installation or a standalone model response is insufficient. The service supplies mechanics; registration retains judgment, review budgets, and activation authority.

### Unresolved details

Installed capability and isolation checks are development verification. If a tool cannot meet the specified exact-model or stopping contract, report the concrete limitation rather than silently weaken it. Execution implementation and policy changes remain outside this outcome.

## Apply shared process definitions

**Outcome:** Registration and the architecture loop use one validated TOML file to direct common runtime behavior while preserving their different process rules.

**Included:** Process-definition validation and snapshots; shared initiation, output, review, confirmation, and recovery dispatch; supported policy/schema/destination references; process-specific integration.

**Excluded:** New execution policy, arbitrary scripted workflows, process-specific architectural judgment, and separate copies of registration or architecture-loop record schemas.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Configuration drives supported runtime capabilities | `docs/architecture.md#shared-process-definitions` |
| Installed schema selection and recovery | `docs/architecture.md#installed-validation-schemas` |
| Correct output validation, storage, and process boundaries | `docs/architecture.md#shared-output-handling-and-process-boundaries` |
| Registration integration | `docs/architecture.md#registration-process-definition-binding` |
| Architecture-loop integration | `docs/architecture.md#architecture-loop` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Records, transport, and supervised agents | Preserve project activity and requests; Connect the CLI to recorded service activity; Run and recover assigned agents | Shared implementation foundation; new process dispatch is delivered here. |
| Registration policies and package meaning | Register and confirm a project through the CLI; Recover registration without losing decisions or exceeding limits | Registration supplies its handlers, schemas, and connected evidence. |
| Persistent-session and breakdown use | Establish the project's architectural foundations; Review and confirm the development breakdown | Architecture loop owns its session continuation and process-specific outputs; shared handlers are delivered here. |

Implement the common interfaces before their process integrations. Final acceptance uses those integrations together; prior final acceptance of a dependent process is not an implementation prerequisite.

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| A configured process starts | Its validated sections select the correct prerequisites, role/session rules, outputs, review, confirmation, and recovery handlers. Registration and architecture retain their different behavior. | Real registration and architecture-loop activities, effective definitions and correlated runtime records. | None |
| Configuration is invalid or changes during work | Invalid definitions prevent the affected new process with a clear error. An active process retains its definition, budget, and authority snapshot; read-only views remain available. | One essential invalid-definition case and an edit between activity starts showing preserved versus new snapshots. | None |
| An activity starts or resumes after installation changes | Resolve the exact installed schema bundle under `docs/architecture.md#installed-validation-schemas`; preserve the saved version and hashes during recovery. | Installed bundle location, activity snapshot, and one missing or changed bundle rejection without substitution or lost work. | None |
| A process returns its required outputs | Shared handling validates structure, identities, permitted locations, versions, and process-specific meaning before reporting the set saved. | Actual registration package and architecture output records; necessary missing/invalid-output rejection. | None |
| Review, publication, or confirmation is repeated or interrupted | Use the selected process contract without duplicate effects, budget resets, unverified publication, or unintended execution. | Basic connected recovery evidence shared with the process declarations, not an exhaustive failure suite. | None |
| Architecture inputs or operations repeat | Enforce exact paths, relevant input hashes, separate working/confirmed references, and correction/review/recovery counters. Reconcile identical operations without stale overwrite, duplicated confirmation, or reset allowances. | Shared evidence from Establish the project's architectural foundations, Produce a bounded and parallel-ready work breakdown, and Review and confirm the development breakdown. | None |
| An Owner responds at a process limit | Apply the shared typed decision once to the exact assignment, retain base limits and counts, and expose the saved disposition. A duration exception does not grant an attempt. | Connected registration and architecture actions, including replay, follow `docs/architecture.md#owner-decisions-at-a-process-limit`. | None |

### Definition of done

Both real processes use the common runtime handling and their own recorded definitions. Evidence checks the matching process-relative settings layout under [shared process definitions](../architecture.md#shared-process-definitions), rejection of legacy registration keys, and separate process budgets without reset. Merely parsing TOML, hardcoding a separate output path for each process, or completing registration alone does not satisfy this outcome. Evidence follows the outcome area's common requirements; live verification belongs to development.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Architecture-loop integration | Exact continuation, response, output, and API contracts are specified in the architecture and schema bundle. | Implement the shared handlers and verify installed compatibility during development; no further process-design decision is identified. |
| Executable definition schema and handler mapping | The runtime must validate and execute the documented behavior. | Use [registration process-definition binding](../architecture.md#registration-process-definition-binding) and the architecture-loop mapping with their supplied configuration schemas. Verify default application, required sections, unsupported values and activity snapshots; implement output validators against their separate record contracts. |

## Partial-registration boundary

No narrower portion is declared. A subset must identify its included outcomes, external dependencies, relevant journeys, and acceptance coverage before registration confirmation. Acceptance of the service foundation alone does not establish the complete runtime, CLI, or registration capability.
