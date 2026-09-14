# Maestro Architecture

## Purpose and boundaries

The [project overview](maestro-project-overview.md) explains the project's purpose, delivery scope, and evidence of what exists. This architecture explains how the service, agents, storage, and terminal interface work together.

This document specifies how the system should work; it does not claim that the software is implemented. Sections marked **provisional** describe decisions that are not settled.

The initial interface is the Maestro CLI. The command center within the Reporting and Command Interface is outside the initial scope. Command-center support uses the same service operations, registration process, and record sources. Mobile presentation is undecided; neither a mobile terminal nor a separate interface is specified.

Read by subject: [runtime and agents](#runtime-and-prerequisites), [connections and data](#connections-and-data), [CLI](#cli-workspace), [registration](#registration), [journeys](#journeys-and-interactions), and [unresolved details](#constraints-and-unresolved-details).

### Functional areas

The three functional areas are established. Their detailed responsibilities and automation authority remain **provisional**.

| Area | Provisional responsibility |
|---|---|
| Planning | Interpret requirements and architecture, organize work and dependencies, define completion criteria, and handle authorized changes. |
| Execution | Assign approved work to agents, manage implementation and checks, obtain reviews, and carry out authorized corrections and merges. |
| Monitoring | Report activity, progress, failures, resource use, pending decisions, and action history. |

Registration is the entry process for Planning. The registration behavior is described separately below.

## Components and responsibilities

| Component | Responsibility |
|---|---|
| Python runtime service | Manage activities, validate requests, save records, and coordinate assigned agent work. |
| Maestro CLI | Display service information and collect explicit commands, linked answers, and registration actions. |
| SQL database | Store current state and conversation/action records that survive restarts. |
| Agent processes | Perform assigned assessment or review work; return results through the service. |
| Project repository | Supply versioned project sources and hold the authoritative registration package. |

### Internal responsibilities

The following module boundaries are **provisional**. They may remain modules within one Python service rather than separate services.

| Responsibility | Behavior |
|---|---|
| Command handling | Receive interface requests and apply the relevant operation rules. |
| Work coordination | Determine which approved action can run next and whether required resources are available. |
| Agent connections | Launch agents, supply instructions, and receive results. |
| State storage | Record running, finished, and waiting activity to support recovery. |
| Health supervision | Observe agent activity, deadlines, and failures; apply authorized recovery or stopping rules. |

The runtime enforces rules that code can check; assigned agents supply judgment. A successful command or an agent message does not grant approval or automatically change project state. Each state change must follow the relevant process rules.

## Runtime and prerequisites

The runtime is a Python backend running continuously as a Linux service on the AI box. It runs under `systemd`, which starts the service at boot and restarts it after a crash.

The installed terminal application is launched with `maestro`. It connects to the existing service; launching the CLI does not start the service. Closing the CLI disconnects that session without stopping service activity.

Agents communicate with the service through command-line tools or APIs. They do not write directly to the terminal.

### Automated coordination

The general unattended loop remains **provisional**: Planning supplies approved work, Execution performs it, and Monitoring reports progress and problems.

| Situation | Provisional response |
|---|---|
| Checks and independent review pass | Complete the work, merge where already authorized, and release dependent work. |
| A worker crashes or stalls | Recover or reassign within the authorized retry limit. |
| Review identifies an implementation defect | Request a bounded correction. |
| A dependency or work breakdown is flawed | Return the issue to Planning; automatic revision requires explicit delegated authority. |
| Scope, architecture, or an Owner-reserved requirement changes | Pause affected work and request a decision. Unrelated approved work may continue. |
| Time, cost, or retry limits are reached | Stop affected work and report the reason. |

Execution does not approve its own results. Monitoring reports and routes problems without changing requirements. This provisional loop does not grant automatic replanning, acceptance, or merge authority.

### Agent delegation

A wrapper script launches an assigned agent and performs deterministic checks around its work. For assignments requiring GitHub commits, the wrapper verifies:

- The expected repository and branch.
- Required changes committed and pushed.
- The commit's existence on GitHub.
- Changes limited to permitted files.
- Agreement between the reported commit and the actual commit.

Read-only assignments do not require commits solely to satisfy the wrapper. These checks establish observable facts; independent review assesses meaning and fidelity.

### Registration agent-work boundary

Registration runs agents to assess sources, prepare and amend candidates, and independently review their fidelity. Its assignment, supervision, permission, output-validation, publication, and recovery controls apply to that work. They do not establish the general software Execution policy.

Implementation-review authority, coding correction limits, merge authority, and development-milestone completion policy remain provisional for separate Execution design. Registration's review limits do not transfer to implementation reviews. Explicit Owner confirmation of registration and the existing role-authority boundaries remain unchanged.

### Model Execution Adapters

A Model Execution Adapter is a Python module inside the runtime service that runs a particular agent tool. The assigned role defines responsibilities and authority; the adapter supplies the mechanics of running that role. The same adapter can support architect and reviewer assignments through separate agent runs, preserving reviewer independence.

| Adapter part | Responsibility |
|---|---|
| Configuration | Identify the agent tool, model, launch settings, and configured access. |
| Assignment preparation | Supply the assigned role, exact source revision, document references, selected scope, response format, permitted access, and limits. |
| Working area | Provide access to the assigned sources and a location for output artifacts. |
| Run control | Start the agent, retain its tracking handle, check status, and support cancellation. |
| Progress collection | Return assignment-linked activity messages to the service for recording and display. |
| Result collection | Retrieve the structured response, output artifacts, and clarification requests. |
| Failure reporting | Distinguish launch failure, agent failure, missing output, and an unknown outcome following interruption. |

The shared operation boundary is:

| Operation | Expected result |
|---|---|
| Start assignment | Return a handle identifying the launched run, or a specific launch failure. |
| Report progress | Return messages linked to the assignment; progress is not completion evidence. |
| Check status | Report starting, running, completed, failed, cancelled, or unknown. Completed run status does not establish a valid result or registration approval. |
| Collect result | Return the response and artifacts for service validation; missing output is reported explicitly. |
| Cancel run | Request termination and report whether it actually stopped. A cancellation request alone is not proof of termination; saved work is not undone. |
| Reconnect after interruption | Recover run status where the tool supports it; otherwise report uncertainty. Do not silently start a replacement. |

For registration, the service supplies the software architect assignment, the adapter launches the selected tool, and the architect assesses the source and prepares the candidate package. The adapter returns progress and the final artifacts. The service validates and saves them, then arranges independent review. The adapter does not decide registration readiness.

The service retains control of content validation, durable state, review and retry budgets, question routing, and registration activation. Adapter transport and process handling do not replace deterministic wrapper checks.

#### Tool and model selection

Registration initiation explicitly selects Claude Code or Codex and the exact model/version for the architect. The fidelity reviewer has a separate tool and model/version selection. The service checks that the selected model/version is supported by the selected tool before that role begins. An unavailable or unverifiable selection is reported before launch; no silent substitution is permitted. Records retain the requested model, tool-reported model, provider, installed tool version, and capability-check result. A full provider model identifier is required; moving aliases are not accepted as exact-version selections. Provider identifiers establish the observable model version, not an undisclosed internal snapshot.

Before launch, the service checks model selection, authentication, and structured-output support using the credentials and configuration assigned to the run. This check does not read project sources. Its result records the tool version, account/provider, model, and configuration hash. A change to credentials, configuration, or tool version invalidates the check. The service also checks the model identity reported by the running tool. Missing or different identity prevents result acceptance and produces a specific integration failure. Agent-written text is not evidence of model identity.

Automatic model substitution is disabled in the effective tool configuration. A refusal remains a refusal; a different model is not used to bypass it. If the installed tool cannot enforce the selected identifier or supply the required evidence, that route is unavailable until corrected. The service does not silently weaken this requirement. [Claude model configuration](https://code.claude.com/docs/en/model-config) documents aliases and fallback; the selected settings must prevent those switches.

#### Tool transport

The Python adapter uses argument arrays and local pipes, not an interactive terminal or shell-built command string. Each run uses a fresh tool conversation. Saved session identifiers are diagnostic references, not permission to resume another project's conversation.

| Tool | Transport and result handling |
|---|---|
| Codex | Launch `codex app-server` over stdio for the run. Perform `initialize` and `initialized`, use `model/list` for catalog discovery, then `thread/start` and `turn/start` with the selected model, working directory, permission policy, assignment instruction, and `outputSchema`. Correlate thread/turn events to the run. Collect the final structured agent message after a successful `turn/completed`; use `turn/interrupt` for cooperative stopping. |
| Claude Code | Launch print mode with explicit `--model`, `--output-format stream-json`, `--verbose`, and `--json-schema`. Supply the bootstrap instruction to read the assignment file. Capture startup model/session metadata, progress, and the terminal result. Extract `structured_output` as the response; missing structured output is a failure, not a request to parse arbitrary prose. |

[Codex App Server](https://learn.chatgpt.com/docs/app-server) documents the model catalog, stdio handshake, turn schema and interruption. [Claude programmatic operation](https://code.claude.com/docs/en/headless) documents streaming and structured results; its [CLI reference](https://code.claude.com/docs/en/cli-reference) defines launch flags. These are selected integration contracts, not proof that the installed tools have passed them.

Each adapter targets an explicitly recorded, capability-checked tool release. Codex protocol validation uses the JSON Schema bundle generated by that installed release. Required fields and events must be present; an unsupported release reports an integration failure rather than guessing its output format.

#### Agent workspaces

Workspaces are service-managed on the Linux AI box. The configurable root defaults to `/var/lib/maestro/workspaces/`; a registration attempt uses `<project-id>/<registration-attempt-id>/` beneath it. Within the attempt, each launch uses `runs/<run-id>/` as its workspace, containing `source/` at the exact assigned repository revision, `input/` for immutable assigned artifacts, and `output/` for new artifacts. The adapter starts the agent with its assigned workspace as the working directory. Separate attempt and run directories prevent output collisions between projects and recovery attempts.

The fidelity reviewer has a separate workspace containing the exact source, architect assessment, and candidate under review. These files are read-only; the reviewer writes to its own output directory and cannot amend the architect's files. Both roles use a Linux mount namespace that makes source, assignment, and prior-artifact paths read-only. Only assigned output and scratch paths are writable. The agent runs without privileges to change mounts, escape its process group, or access another run's workspace. Folder names and instructions alone do not enforce these boundaries.

The service places the exact assessment and candidate in the reviewer's input area and checks their hashes. It records each artifact's original identity and assigned relative path. The reviewer returns these assigned references. Permission to write output through the agent tool does not make the source or input mounts writable.

Service-managed tool settings pre-authorize only assigned operations. An unexpected permission request is denied and reported as a missing-permission failure; it cannot hang waiting for a terminal answer. Required credentials are provisioned for the service account before use, with no secrets in assignment files or logs. Registration agents have no GitHub write credentials; package publication is a separate service-owned operation subject to wrapper checks. Repository instructions are assessment inputs and cannot expand the assigned role's permissions.

Completed, cancelled, and interrupted workspaces remain until explicitly removed; automatic cleanup is outside the initial behavior. Removal is permitted only when no agent uses the workspace and no pending review or recovery depends on it. Removing a workspace does not remove SQL registration history or published GitHub documents. Those durable records remain authoritative; workspace files support inspection and recovery.

#### Assignment delivery and clarification

The service writes UTF-8 `assignment.json` at the run workspace root and records its SHA-256 before launch. It contains:

- Project, registration activity, assignment identity, run identity, parent assignment when applicable, and assigned role.
- Role responsibilities and the specific task.
- Exact source revision, document paths, selected scope, recorded decisions, relevant answers, and outstanding questions.
- Prior findings and candidate references when continuing work.
- Permitted actions, writable locations, limits, and conditions requiring clarification.
- Required response format and output location.

The adapter launches the selected tool and model in the workspace with instructions to read this file. Each run receives a fixed assignment snapshot. Later answers remain recorded by the service and enter a follow-up assignment; they do not change a running assignment.

Clarification can contain several questions, several answers, and additional follow-ups. The complete exchange stays linked to the same registration activity. An agent returning clarification ends that run. A follow-up assignment supplies the relevant saved context rather than relying on prior session memory. Incomplete answers or newly identified ambiguity can produce specific follow-up questions without resetting the fidelity review budget.

The architect resumes when answers needed for its next step are available. Questions that do not prevent that step may remain open. Individual answer arrival does not itself launch another run.

#### Assignment and run identity

An assignment identifies one assessment or review and tracks its automatic retry budget. A run identifies one agent launch. The initial launch, automatic recovery, and manual retry each receive a different `run_id` under the same `assignment_id`. A clarification follow-up receives a new assignment linked to the previous one because its saved inputs have changed. It remains within the same registration activity and review budget.

Before launch, one SQL transaction reserves the run and marks it as the assignment's current run. The supervisor unit is created once for that reservation. Before repeating a start request, the service checks whether the unit already exists. The record contains the run kind, assignment snapshot hash, source and decision versions, model selection, duration, configuration hash, launch time, supervisor identity, and available tool session/thread/turn identifiers. The reservation prevents simultaneous dispatchers from launching the same assignment.

Responses must match both assignment and current run. A delayed result from an older run is retained as diagnostic evidence and cannot update the candidate or consume a review round. An identical replay of an accepted response returns its original receipt without repeating effects.

#### Process supervision and interruption recovery

Each run has a service-owned supervisor in a dedicated systemd unit named from the run's internal identifier. The supervisor controls the tool pipes, continuously reads stdout and stderr, and stores numbered events locally outside agent-writable paths. The runtime converts these events to Maestro's event format and saves them in SQL before sending them to the CLI. It ignores replayed events with the same run and sequence number. A locally stored event alone cannot advance registration.

The supervisor runs separately from the main Maestro service. After a service restart, Maestro checks the recorded systemd unit invocation and replays unread events without launching a replacement. It checks both the unit identity and the host boot identity; a process ID alone is insufficient. The supervisor retains the original deadline, measured by an elapsed-time clock unaffected by wall-clock changes. Restarting Maestro does not grant more time.

Stopping first uses the tool's interruption request where available. The supervisor then terminates the run's process group. The systemd unit uses `KillMode=control-group`, `TimeoutStopSec=30s`, and `SendSIGKILL=yes` to force termination after a 30-second grace period. **Stopped** means the run's control group (cgroup) is confirmed empty, including child commands. An acknowledgment, closed pipe, tool turn status, or main-process exit alone does not prove this. [systemd's process control interface](https://wiki.freedesktop.org/www/Software/systemd/dbus/) provides unit-wide signaling and control-group identity. This mechanism requires verification against the AI box's installed systemd and permissions.

If the supervisor is gone but descendants remain, terminate and confirm them before recovery. If identity or termination cannot be established, report unknown status and block replacement. Confirmed host reboot establishes that the old local processes ended, but does not establish publication success. Reconcile any external operation separately.

After a final result, the adapter closes the tool connection and requests normal exit of that run's tool server. The response remains pending until the supervisor confirms that no child work remains and the service validates the response and files. Before review, the service copies accepted artifacts into a service-owned store where they cannot be changed. A child process that remains after the tool's completed turn must be stopped; completion remains unverified. Recovery uses saved inputs and verified artifacts. Resuming a tool conversation does not prove that a process is still running or that work completed.

#### Progress reporting

The CLI distinguishes confirmed service status from agent-reported progress. Service status describes facts such as running, waiting for answers, completed, or failed. Agent progress briefly describes work such as reading source documents, assessing architecture, preparing findings, or submitting results.

The service saves these updates in SQL before display. Progress messages establish neither completion nor approval. No estimated completion percentage is shown. During silence, the CLI retains the last update and shows elapsed time without assuming the run has stalled.

#### Completion handling

The service checks that the returned response matches the assigned project, activity, source revision, and [registration response contract](#registration-agent-response-contract). Referenced files must exist in permitted locations and match their recorded hashes. Required publication must pass the [GitHub wrapper checks](#agent-delegation).

The service saves the validated response, findings, questions, and artifact references before advancing the activity. A successful tool exit alone is insufficient. Missing or invalid output enters [technical recovery](#technical-recovery).

A valid architect assessment proceeds to independent fidelity review. Clarification waits for the necessary answers. Passing review still requires registration eligibility checks and explicit final confirmation before activation.

#### Cancellation

The service records cancellation and asks the adapter to stop the active run. The CLI displays **Stopping** until termination is confirmed, then **Cancelled** for an explicit registration cancellation. A technical or timeout stop instead leaves the activity paused under recovery rules. Saved findings and files remain available; unfinished output cannot advance registration. Cancellation does not undo commits or previously accepted work.

If termination cannot be confirmed, the CLI displays **Stop unconfirmed** and the service blocks replacement runs until the original status is resolved. A completion received while cancellation is pending is retained but cannot advance the activity. Sending a stop request is not proof of termination.

#### Unresponsive runs

Silence alone does not trigger a restart. When the adapter confirms a quiet run is active, the service continues waiting within its run-duration limit. When status cannot be established, it reports uncertainty and blocks a replacement.

The registration architect and registration fidelity reviewer each default to **30 minutes per run**, configurable separately. Other planning and execution assignments require their own duration settings; they do not inherit this default. Timing starts at launch. Progress does not reset it. A clarification response ends the run, so waiting for answers consumes no run time. Each follow-up or recovery run has its own timer.

Reaching the limit requests termination, preserves available output, and pauses the activity once stopping is confirmed. Timeout alone does not trigger automatic retry: an identical run may reach the same limit. The CLI shows elapsed time, last reported progress, and whether termination was confirmed. Investigation or an appropriate duration adjustment precedes manual retry. Unknown termination status continues to block replacement.

### Returned implementation plan

For an assigned execution work packet, the agent reads and understands the packet, returns its proposed implementation plan before making changes, and then continues the assigned work. The plan states the required outcome, relevant existing code, intended changes and sequence, necessary connections, basic verification and essential failures, and any blocking missing information or conflict.

The service records and displays the plan as an assignment-linked intermediate output. It is distinct from the final result. Returning it introduces no additional review, approval, or pause before execution. A future plan-checking gate is outside the current behavior. Existing scope and authority limits still apply to actual blockers.

This behavior concerns execution work packets. A registration architect returns its assessment and candidate under the registration response contract; registration does not acquire an implementation-plan or development-work stage.

## Connections and data

### System connections

| Connection | Mechanism | Responsibility |
|---|---|---|
| CLI to service | HTTP requests to a local API on `localhost` | Retrieve information and submit commands, answers, and explicit actions. |
| Service to CLI | Server-Sent Events over a persistent connection | Deliver recorded messages, progress, findings, and input requests. |
| Service to agents | Agent command-line tools or APIs | Supply assignments and receive results. |
| Service to SQL database | Database access | Store project state and durable conversation records. |
| Registration process to project repository | GitHub | Read a specific source commit and publish versioned registration packages. |

Requests and events associated with a project carry its identity. Commands can be submitted while updates arrive. A separate agent is not required to maintain the CLI connection.


### CLI connection configuration

The CLI reads TOML from `$XDG_CONFIG_HOME/maestro/cli.toml`, or `~/.config/maestro/cli.toml` when that environment variable is unset. The optional `service_url` setting is an absolute HTTP URL with host `localhost`, `127.0.0.1`, or `[::1]` and a port from 1 through 65535, without credentials, query, fragment, or a path other than `/`. Other destinations are unsupported in this version and treated as invalid configuration. The initial service listens on loopback; remote service exposure is outside this interface design.

The default address is `http://localhost:8787`; the service installation uses the same default port. Missing, unreadable, malformed, or invalid configuration uses that fallback, with a plain explanation and the effective address visible. A valid but unreachable configured address remains selected; connection failure does not trigger fallback.

Connection attempts time out after 5 seconds; ordinary requests time out after 15 seconds. For long-running activity, the service saves the request and returns a receipt. Subsequent events report progress without keeping the HTTP request open.

After losing an established connection, automatic attempts wait 1, 2, 4, 8, 16, then 30 seconds between failed attempts, continuing at 30 seconds while the CLI remains open. Automatic attempts keep the effective address. `/retry` rereads configuration and attempts immediately, replacing any scheduled attempt. Only one attempt runs at a time. Success resets the delay. Initial startup failure waits for explicit retry.

Connection status updates in place without repeated conversation messages. Reconnection refreshes saved state and preserves valid project/activity viewing context. A changed service address clears the old service's view and input before loading the new overview. Commands and answers are never automatically replayed.

### CLI request and event contract

The local API uses UTF-8 JSON under `/api/v1`. These are interface contracts for implementation, not claims about existing endpoints.

| Operation | HTTP interface | Result |
|---|---|---|
| Initial or refreshed workspace | GET `/workspace` | Project summaries, attention, service identity, and a consistent event cursor. |
| Project conversation | GET `/projects/{project_id}/conversation?before={cursor}&limit=50` | Chronological messages, activity references, and an older-page cursor; omission of before returns the latest page. |
| Project activities | GET `/projects/{project_id}/activities` | Activity identities, names, states, and start/end times. |
| Activity detail | GET `/activities/{activity_id}` | Current state, questions, findings, and available actions. |
| Registration view | GET `/projects/{project_id}/registration` | Existing attempt or approved record; absence is explicit and starts nothing. |
| Submit an operation | POST `/requests` | Durable receipt for registration intake, an answer, or an explicit registration action. |
| Reconcile an uncertain submission | GET `/requests/{request_id}` | Saved status and result, or explicit not-found. |
| Live updates | GET `/events` | Server-Sent Events with durable cursor IDs. |

Read responses contain `data` and `event_cursor`, which identifies the corresponding position in the event stream. List responses also contain `next_cursor` for the next page, or null when no pages remain. Project summaries contain identity, plain name, registration status, activity state, and attention count. Activity records identify their project; question and finding records identify both their project and activity. Names and coded subjects remain plainly worded even when internal IDs have no readable meaning.

A submission contains `request_id`, `operation`, `project_id`, `activity_id`, `question_id`, `expected_version`, and `payload`. Context fields may be null only when inapplicable, such as initial repository intake. The service validates the required context for each operation. Operation names are `registration.start`, `question.answer`, `registration.confirm`, `registration.cancel`, and `registration.retry`. The retry payload and eligibility rules are defined under [activity retry request](#activity-retry-request). Initial intake supplies repository and overview path; saved intake questions collect missing scope and the explicit architect tool and exact model/version selection required by [tool and model selection](#tool-and-model-selection). Selection must be recorded before architect launch. Answer payloads contain text and an optional choice reference. Registration actions identify the exact candidate or attempt and its version.

Receipts contain request identity, status, and any created project/activity identities. Status is accepted, completed, or rejected; accepted means durably recorded, not completed activity. Errors contain `code`, plain `message`, and affected fields. Invalid input returns 400, unavailable access 403, missing records 404, stale context or conflicting request content 409, and unavailable service 503. No error is rendered as an empty result.

Events carry `schema_version`, `event_id`, `occurred_at` in UTC, `project_id`, `activity_id`, `type`, and `data`. Types cover project/activity changes, conversation messages, questions, findings, request outcomes, and attention changes. The service sends events only after the SQL transaction commits. Service-wide events have null project/activity context.

The initial data snapshot includes an event cursor. Replaying Server-Sent Events from that cursor supplies updates made between loading the snapshot and opening the stream. Repeated event IDs are ignored. Reconnection uses `Last-Event-ID`; if that cursor is unavailable, the CLI loads a fresh snapshot. Heartbeat comments arrive every 15 seconds. A 45-second gap with no stream traffic triggers disconnection. Heartbeats create no SQL or conversation records.

### Record ownership

| Record | Authoritative location and use |
|---|---|
| Current project state | SQL; describes current activity and waiting conditions. |
| Conversation history | SQL; stores messages, events, questions, answers, and recorded actions. |
| Project source | An exact Git commit in the supplied repository. |
| Registration package | Versioned JSON records in the registered project's GitHub repository. |
| Live CLI updates | Notifications of recorded information, not an independent source of truth. |

SQL is not merely a queue of screen output. Read-only requests display existing records without creating another status record or conversation entry.

Service events describe observable activity and state changes. Agent results contain explanations, findings, questions, and review results. Interface submissions contain commands, answers to existing questions, and explicit registration actions.

### Save and delivery sequence

Durable information follows this sequence:

1. The service receives an event, agent result, answer, or action.
2. It validates the information against the relevant project and process.
3. It saves the record in SQL.
4. It acknowledges the save and delivers the recorded update to connected interfaces.

Service-wide requests remain service-wide. Saved records remain available after CLI exit or connection loss. Startup retrieves saved state through the service; reconnection also retrieves missed updates.

Read-only lookups do not require a new durable record before handling. SQL recording does not replace registration-package publication; [publication and SQL consistency](#publication-and-sql-consistency) defines the separate durable operations.

### Identity, declarations, and ordering

Registration records declaration identity, milestone identity, delivery position, dependencies, and versions separately. Ordering changes do not change references. Reviews bind to exact record versions, and work-packet relationships use explicit references rather than encoded hierarchies.

The [Maestro Planning Guide](planning-guide/README.md#naming-ordering-and-versions) defines naming, numbering, ordering, and version conventions.

## CLI workspace

### Layout and conversation

The CLI uses a continuous terminal workspace with:

- A project selector and service connection status.
- The selected project's activity and waiting state.
- One conversation per project, with the source of each message identified.
- Visible questions requiring a response.
- A persistent input area showing its current context.

Activity sections distinguish processes such as registration, milestone planning, and execution. Routine progress remains compact. Detailed findings and reports expand within the conversation.

Opening details within the same activity preserves the selected project and question linked to the input. Switching activities follows the activity-selection rules below. Closing details restores the prior reading position. Viewing a finding does not acknowledge, resolve, or approve it.

A newly opened project shows recent messages with “Load earlier messages” above them. Current activity and pending questions remain accessible separately from history. Opening the conversation does not change project work or answer questions.

The initial scrolling behavior follows incoming messages only at the bottom. Scrolling upward holds the reading position and shows “New messages”; selecting that indicator returns to the latest content. This behavior remains subject to practical evaluation.

### Startup and connection states

Startup opens the project overview with “No project selected” above the input, including when only one project exists.

| State | Interface behavior |
|---|---|
| Connecting | Show connection progress while contacting the configured service. |
| Connected | Retrieve project information and accept available service operations. |
| Unavailable | Show the reason and Retry connection. A failed connection is not an empty project list. |
| Disconnected during use | Keep the visible conversation and mark it “Disconnected—information may be out of date.” Block new service actions and answer submissions. |

During disconnection, `/help`, `/retry`, and `/exit` remain available. Reconnection refreshes state without automatically repeating submitted commands or answers. Loss of the CLI connection does not establish that service work stopped.

### Projects and targeting

A **selected project** is the CLI's current focus. A **working project** has activity being performed by Maestro. Selection does not start or stop work.

The project overview shows each project's plain name, current activity or reason for waiting, and attention needed. Projects needing attention appear first, followed by working projects and then idle projects.

The CLI can display one project while other projects continue running. Each project has separate conversation records, process state, questions, decisions, and registration versions.

Project targeting follows these rules:

- The selected project's name remains visible above the input.
- A project-specific command targets an explicitly named project or the selected project.
- Missing targets require selection before execution.
- A named target that differs from the selected project requires explicit resolution before execution.
- Unknown or ambiguous names require resolution; conversation text is not used to guess a target.
- Service-wide commands do not inherit the selected project.

Switching projects clears unsent text. It is neither saved nor transferred. Draft retention and a warning before project switching are outside the initial behavior. The exit warning is defined with `/exit`.

### Project activities and registration labels

A project activity is a particular registration attempt or other unit of ongoing project activity, with its own questions, findings, progress, and result. It is distinct from an operating-system process. One project conversation retains these activity associations.

Opening a project shows its single current activity, including an activity waiting for an answer. If several activities are underway, the CLI shows them for explicit selection rather than guessing. If none is underway, the project is labeled Idle and opens its most recently ended activity. Earlier activities remain available; the selected activity name and state stay visible. Navigation never starts, stops, or changes project work.

Switching activities clears unsent text without saving, transferring it, or showing a warning. Input then accepts commands only. Opening an eligible question links the input to that exact question. Opening an attention item first selects its project and activity, then follows the question or activity-action rules under [attention](#attention). Opening a finding does not change its state.

Activity-specific commands use the selected activity. If none is selected, the CLI requests selection. `/registration` opens the ongoing registration attempt, or the latest registration record if no attempt is underway. It follows the same activity-switching input rules. Actions on historical activities must still meet the current eligibility rules.

Registration creates durable project and activity identities during accepted intake, before assessment or approval. Questions use those identities even before the project is registered. Repository identity prevents duplicate project entries.

| Registration condition | Project label | Activity display |
|---|---|---|
| Initial registration underway | Registering | Current step and progress. |
| Initial registration awaiting an answer | Registering | Waiting for your answer; question appears in attention. |
| Initial attempt ended without approval | Not registered | Reason and saved findings; registration can be started again. A recoverable pause still belongs to the current attempt. |
| Initial registration confirmed | Registered | Idle, with completed registration visible; no development starts. |
| Re-registration underway | Registered | Updating registration, including any waiting reason; approved version stays active until replacement confirmation. |

An empty service is a supported startup condition. Registration supplies the first real project, activity, and question records; no separate temporary project/question generator is part of the product. A project list with unapproved attempts still displays those entries rather than replacing them with an empty screen.

### Attention

The attention view lists outstanding questions, decisions, and recovery actions across projects. Each entry identifies the project, activity, requesting agent or process, and response or action needed.

A question entry opens that exact question with answer-linked input. An activity-action entry opens the exact activity, failure explanation, and available action, such as Retry activity or Retry publication. It does not create a question or link ordinary conversation input to an answer; that input remains commands-only. Any intervention text belongs to the explicit action form. Viewing the entry does not perform the action.

A notice identifies the other project and the response or action needed. It does not change focus or interrupt input. Selecting the notice uses the same attention-navigation behavior, including the project-switch rule.

Opening a question does not resolve it. It remains outstanding until the process resolves it.

### Commands

Slash commands perform defined operations. Ordinary text follows the answer rules in the next section. Equivalent typed commands and controls invoke the same operation.

| Command | Behavior |
|---|---|
| `/help` | List implemented commands and plain explanations. `/help <command>` shows syntax, required inputs, an example, and required project context. Contextually unavailable commands explain why. Help works without the service and changes no project state. |
| `/projects` | Open the project overview. Showing the list preserves selection; choosing an entry selects that project. |
| `/attention` | Open questions, decisions, and recovery actions across projects. |
| `/register <repository>` | Start registration intake for an explicit repository without assuming the selected project. The same entry handles eligible re-registration. |
| `/registration` | Open the selected project's existing registration process or record, including a candidate where available. It does not start registration. |
| `/findings` | Open blockers, non-blocking observations, and review findings for the selected project's selected activity. A selected finding exposes explanation and evidence; no review or state change is initiated. |
| `/retry` | Reread connection configuration and retry the service connection immediately. It does not start the service, repeat previous submissions, or retry project work. |
| `/exit` | Close the CLI session. Saved conversations and pending questions remain available. Unsent text triggers a warning before exit. |

The command set does not include separate `/select`, `/status`, `/respond`, `/compare`, `/confirm`, or `/cancel` shortcuts. Project selection uses the overview; status remains visible; answers use linked input. Registration comparison, confirmation, and cancellation are process-view actions.

Execution commands for starting, pausing, resuming, and stopping work are not specified.

### Questions and answers

Ordinary text is accepted only as an answer to an existing selected question. The input identifies the project or registration context, requesting agent or process, and question. Without a selected question, it accepts commands only. Unsolicited agent conversations are outside the initial interface.

Questions with clear alternatives include a plain question, a justified recommendation with its reason where appropriate, viable alternatives with tradeoffs, and a free-text option. Alternatives are not automatically labeled less recommended. Information requests use written answers rather than forced choices.

Selecting a choice fills the input without submitting it. Additional written clarification can be included before Send or Enter submits the answer.

| Submission state | Behavior |
|---|---|
| Sending | Wait for acknowledgment that the service saved the answer. |
| Not sent | Show a plain reason and retain the answer for explicit retry. Reconnection alone does not resubmit it. |
| Answer received | After save acknowledgment, show the answer in the conversation and clear the input. Receipt is not resolution. |
| Clarification required | Present a specific follow-up linked to the original question, retaining the previous answer and identifying the new question above the input. |

A lost acknowledgment may leave delivery uncertain. In that case, “Not sent” is accompanied by “Delivery not confirmed. Retrying will not submit your answer twice.” The service recognizes repeated submissions and prevents duplicate recording or effects.

Before accepting an answer, the service checks that the original question still awaits a response. A replaced question or cancelled process produces an explanation rather than rerouting the answer. An available replacement can be opened without automatically transferring the text.

Clarification explains what information is missing instead of simply repeating a question. An answer does not become registration confirmation.

Failed-answer retention applies only to the current input; it does not create saved drafts across project switches.

### Answer identity and uncertain delivery

The CLI creates a request identity for each explicit submission. Retrying the same text and choice for the same question reuses that identity. Before submitting edited content under a new identity, the CLI checks the previous request's recorded outcome. If the answer was received, it shows the receipt without replacing the answer. If the outcome is unknown, edited text remains unsent. A new explicit submission is permitted only if the earlier request is absent or rejected and the question still accepts an answer.

SQL enforces unique request identities and stores each request's submitted content and result. Repeating the same identity and content returns the saved result; reusing the identity with different content is rejected. One SQL transaction checks question eligibility, records the request, and accepts the answer. Simultaneous or delayed submissions therefore cannot both answer the same question.

An accepted answer also has a saved pending-delivery record. The receiving component uses the request identity to recognize repeat delivery and apply the answer once. A service restart cannot silently lose the accepted answer. This guarantee covers answer receipt and delivery; it does not guarantee that every external agent operation happens exactly once.

### Empty results

Empty states appear only after successful retrieval. A lookup failure is displayed as a failure, and missing project or process context follows the targeting rules.

| Result | Display |
|---|---|
| No project entries | “No projects registered,” a Register project action, and the command input. The action requests a repository and enters registration intake. |
| No attention items across projects | “No questions or decisions need your attention.” |
| No findings for the selected activity | “No findings recorded for this activity.” |
| No registration for the selected project | “No registration exists for this project,” with a Register action. |

### Keyboard and terminal behavior

| Key | Behavior |
|---|---|
| Tab / Shift+Tab | Move between controls. |
| Arrow keys | Move within a focused list or choice set. |
| Enter | Activate the focused control or submit from the answer input. Choice activation only fills the input. |
| Escape | Close a list or detail view without affecting project work. |
| Shift+Enter | Add a line to an answer. |

Focus remains visible. Multiline paste fills the input without submission. The input grows to a limited height and then scrolls internally so conversation and question context remain visible.

A minimum terminal width and height protects readable project, question, and input context. Below that size, the CLI displays “Enlarge the terminal to continue.” Resizing does not stop service work. The minimum is 80 columns by 24 rows. The answer input grows from one to six visible lines, then scrolls internally. These initial dimensions can be adjusted after practical use without changing context or submission rules.

## Registration

### Purpose and authority

Registration checks whether Maestro can understand and operate on supplied project information. It identifies the project, verifies repository access, locates source material, checks its format and meaning, and produces a versioned package for confirmation.

The project architect supplies outcomes, architecture, scope, completion requirements, and source corrections. That role may be human, an agent, or both. The [Maestro Project Architect](agents/architecture-agent.md) performs software architecture assessment of the source and prepares the candidate registration package. A separate Fidelity Reviewer checks both the assessment and the package against that source and recorded decisions. The Owner role supplies decisions and final confirmation through the CLI.

Registration does not approve the project's architecture, start development, or perform development-milestone and work-packet breakdown. Change boundaries, repository rules, coding conventions, and execution authority belong to Execution. Project-specific overrides of those rules are not part of registration.

### Source format and inputs

The [Maestro Planning Guide](planning-guide/README.md) specifies three Markdown source types: a project overview, architecture, and milestone declarations. Registration receives the repository-relative overview path. The overview identifies the authoritative architecture and declarations through explicit source references; repository scanning is not used to guess the entry document.

| Input | Required information |
|---|---|
| Identity | Plain project name, repository location, and responsible project architect. |
| Purpose and scope | Intended result, included work, and explicit exclusions. |
| Architecture | Main components, responsibilities, interactions and journeys with expected results, technical choices, constraints, and unresolved details. |
| Current state | New or existing development, reported completed capability, unfinished or broken areas, supporting evidence, and conflicting claims. |
| Work outline | Desired features or outcomes, priorities, dependencies, ordering, and supplied project milestones. |
| Completion requirements | Project-level acceptance criteria and definitions of done. |
| Source locations | Authoritative documents and their guide-compatible formats. |

Inputs must be clear enough to organize work without inventing requirements. They need not specify every implementation detail or include a complete code audit.

Project milestones describe meaningful outcomes, releases, or component boundaries. The subsequent breakdown process produces development milestones linked to those outcomes, without assuming a one-to-one relationship or redefining the project scope. Registration retains the supplied outcome structure.

### Intake and scope

Registration initiation includes [architect tool and model selection](#tool-and-model-selection) before agent launch. The intake request provides an explicit repository and repository-relative project overview path, and selects the whole supplied plan or a defined portion. An already registered repository is explicitly identified as re-registration before that process proceeds. The service records project identity, checks read access and that the repository matches the intended project, and reports missing access.

Only one registration process can be active per project. A duplicate request opens that process instead of creating a competing process or another version. This restriction does not prevent registration or work on unrelated projects.

To register a portion, the service reads guide-compatible source and displays milestone identifiers with their plain subjects. Selection can cover milestones or a narrower written boundary. The service presents the included work, exclusions, and outside dependencies for confirmation. A narrower boundary must be recorded explicitly; the service cannot expand it by inference.

The Maestro architect checks whether outside dependencies exist or need work. Missing essentials become findings for a decision. For example, a publishing outcome dependent on authentication must identify authentication as existing, included, or missing essential work. Partial registration covers only its recorded boundary.

### Source consistency

Review uses an exact Git commit shared by the Maestro architect and Fidelity Reviewer. Relevant input changes are shown before confirmation.

| Explicit source choice | Effect |
|---|---|
| Retain the reviewed source | The package covers the original requirements and excludes newer changes. |
| Include updated source | The candidate changes and affected findings are rechecked within the existing review budget. |

Unrelated commits and changes to review reports are not treated as changed planning inputs. Source versions are never silently mixed.

### Assessment and independent review

The registration loop separates format checks, architectural judgment, and independent review:

1. Python validates required fields, file locations, document structure, and references.
2. The Maestro architect assesses meaning, scope, dependencies, and evidence, then produces findings and prepares the candidate package.
3. The Fidelity Reviewer independently compares the findings and candidate package with the same source and recorded decisions, checking fidelity and whether blockers are justified.
4. The Maestro architect amends its findings or candidate package where needed. Package review stays within the same review budget.
5. Any further review covers affected findings only.

The resulting report identifies what was found, readiness, and required attention, with file and passage references where available. Source-plan contradictions and missing source answers are returned to the project architect; the Maestro architect does not resolve them by inventing requirements.

| Finding | Treatment |
|---|---|
| Blocker | Missing or contradictory information prevents reliable interpretation or operation under the applicable rules. The finding identifies what cannot proceed and cites evidence or a missing required input. |
| Non-blocking finding | Wording preferences, optional improvements, or gaps that do not prevent registration remain recorded without requiring correction. |
| Review disagreement | The assessment may be amended. Unresolved disagreement at the review limit requires an Owner decision. |

Review does not introduce new requirements. Readiness requires no remaining blockers or unresolved disagreements; minor improvements do not prevent readiness.

### Purpose and dependency checks

The assessment examines whether scope can deliver the stated outcome, rather than only whether the description is clear.

A usage walkthrough explains how to start using the capability, what it depends on, how its parts connect, and how to observe the result. Each essential dependency must already exist or be included in the supplied work and dependency structure. Excluding an essential operation requires an explicit scope decision: include the missing work or narrow the claimed outcome.

Targeted source inspection checks claimed dependencies. For authentication, relevant evidence includes route protection, application or API connections, required configuration or credentials, unfinished components, and operational results.

| Evidence level | Meaning |
|---|---|
| Reported to exist | A source claim without verification. |
| Supported by source inspection | Code appears present and connected. |
| Verified in operation | Operational evidence supports the capability. |

Source inspection is not operational proof. Unverified behavior remains identified, and the assessment is not a full code audit.

Registration records the usage walkthrough, prerequisites, and completion evidence in the supplied outcome's acceptance criteria and definition of done. Each criterion states the expected behavior, applicable conditions, required evidence, what counts as passing, and accepted exceptions. The definition of done also states required reviews and other completion obligations.

A declared usable capability requires evidence of the same journey through the actual connected system. Completed components or sample-data screens alone do not establish it. Component outcomes remain valid when identified and assessed as components. Registration assesses this expected completion path without requiring unbuilt functionality to exist already.

Detailed development criteria belong to the subsequent breakdown process and remain traceable to project criteria without weakening them. Material ambiguity encountered there requires clarification.

### Review limits and decisions

The service reads `registration.maximum_fidelity_reviews` from `/etc/maestro/agents.toml`. The setting is a positive integer and defaults to **2** when omitted. An invalid value prevents a new registration with a plain configuration error.

At initiation, the service copies the effective limit into the registration activity in SQL. That saved value governs the whole attempt. Configuration changes affect future attempts, not one already running. This budget is separate from technical retries and run durations.

| Event | Review-count effect |
|---|---|
| Architect prepares or amends an assessment | None. |
| Independent reviewer returns a valid completed review of assessment and candidate | Consume one round for both together. |
| Reviewer requests clarification without completing its review | None. |
| Agent crashes or returns invalid output | Technical recovery; no round consumed. |
| Answers or relevant source updates arrive | Preserve the existing count and limit. |
| Accepted review output is delivered again | Return the saved receipt; do not count again. |

Readiness after the first passing review does not require another review. At the saved limit, unresolved material blockers or disagreement pause registration for an Owner decision. The service neither forces approval, resets the count, nor launches another review beyond that limit.

The registration view displays the current step, working agent, round and limit, findings, failures, progress or waiting state, and required decisions.

A question identifies the relevant findings and registration version. Its recorded response is routed to the paused step; the architect can amend the report and affected findings can be rechecked within the remaining budget. Clarifications, scope decisions, and accepted limitations remain linked to their requests and affected outcomes or criteria in the package.

### Package structure

The project's own GitHub repository holds registration records under `.maestro/registrations/`. UTF-8 JSON is authoritative. The CLI renders these records instead of maintaining a separate account of their contents. Registration packages describe supplied project outcomes; they contain no generated development breakdown.

| Location | Purpose |
|---|---|
| `index.json` | Discovery index with project identity, current confirmed package reference, and references to previous confirmations. It is not a substitute for an exact package reference. |
| `versions/<registration-version>/candidates/<candidate-id>/manifest.json` | Immutable candidate identity, source and decision versions, and inventory of its record files and hashes. |
| `summary.json` within the candidate | Project purpose, selected scope, exclusions, priorities, and overall assessment. |
| `declarations/<record-key>.json` within the candidate | Declaration designation, plain subject, version, and ordered milestone references. |
| `conventions.json` within the candidate | The project's Owner-authorized declaration designations, record types, and naming prefixes with their decision references. |
| `milestones/<record-key>.json` within the candidate | One supplied project milestone per file, preserving qualified identity, plain subject, version, purpose, scope, dependencies, and completion references. Delivery order belongs to its declaration. |
| `requirements/<record-key>.json` within the candidate | Project or milestone completion requirements, expected journeys, interaction results, evidence, and accepted exceptions. |
| `assessments/<record-key>.json` within the candidate | Architect assessment, findings, affected records, source evidence, and corrections. |
| `reviews/<record-key>.json` within the candidate | Independent review outcome, exact reviewed content reference, findings, and review-round accounting. |
| `decisions/<record-key>.json` within the candidate | Relevant clarifications and answers, scope/source choices, amendments, accepted limitations, and their authority. |
| `confirmations/<confirmation-id>.json` beneath the registration root | Immutable record of the Owner's explicit confirmation of an exact published candidate. |

Record keys identify files and must be safe for filenames; they do not determine delivery order. Records pair every displayed coded identifier with its plain subject. Each attempt receives one positive-integer registration version, so cancelled attempts can leave gaps. Candidate identifiers are unique within the project. Any change to package bytes requires a new candidate identifier. Confirmed candidates are never edited.

#### Package record contract

All package files declare `schema_version: 1`. Each record file contains `record_type`, `record_id`, `subject`, positive integer `record_version`, and `data`. Required text is nonempty. Unknown record types or schema versions are rejected; optional values use explicit null and optional collections use empty arrays.

| Record type | Required data |
|---|---|
| Summary | `project_id`, `purpose`, `scope` with included and excluded outcomes, `priorities`, `assessment_outcome` (ready, clarification_required, or blocked), and references to project requirements. This outcome is not activation. |
| Declaration | `designation`, `milestone_refs` in delivery order, and `source_refs`. Its `record_version` is the declaration version. |
| Naming conventions | `declaration_designations`, `record_types`, `prefixes`, and `decision_refs`. Each entry pairs its code with a plain subject and preserves the Owner-authorized convention; registration does not invent additional prefixes. |
| Milestone | `declaration_id`, `milestone_id`, `purpose`, `included`, `excluded`, `dependencies`, `requirement_refs`, and `source_refs`. Each dependency identifies its subject, required outcome, and existing/included/missing state with supporting evidence. |
| Requirement | `applies_to`, `expected_result`, `conditions`, `pass_boundary`, `verification`, `accepted_exception`, `source_refs`, and `journey`. Journey entries identify the interaction, expected result, and essential failure behavior; noninteractive requirements use an empty journey. |
| Assessment | `assignment_id`, `run_id`, `source_commit`, `decision_version`, `summary`, and `findings`, using the registration response contract's finding structure. |
| Review | `assignment_id`, `run_id`, `reviewer_identity`, `review_round`, `review_limit`, `reviewed_content_hash`, `reviewed_assessment_ref`, `outcome`, and `findings`. The service records identity and accounting; the reviewer cannot assign its own limits. |
| Decision | `question`, ordered `answers`, `resolution`, `authority`, `affected_refs`, and `supersedes_ref`. Answers include their saved identity, author, text, and time. A decision without a question uses null; superseded decisions remain available. |

References contain `record_id`, `subject`, `record_version`, and a package-relative `path`. External references also name the repository, exact commit, and source locator. Milestone dependencies preserve qualified declaration and milestone identities. A milestone's `declaration_id` identifies membership only; the package manifest fixes the declaration record version. Declaration records own delivery order; an ordering-only change increments the declaration version without changing the versions of unchanged milestones. The convention record preserves the naming list used by this package. Reviews identify the exact declaration and milestone versions through these records. Facts are defined in their owning record and linked elsewhere.

The manifest contains `project_id`, `registration_version`, `candidate_id`, `previous_registration_ref` or null, `source_repository`, `source_commit`, `overview_path`, `decision_version`, `content_hash`, and `files`. Each file entry contains its relative path, record identity/type/version/subject, and SHA-256 of its exact UTF-8 bytes. The manifest does not list or hash itself.

To calculate `content_hash`, the service sorts summary, declaration, naming-convention, milestone, requirement, assessment, and decision files by path. Each inventory entry contains `path`, a tab, the file hash, and a newline. Review files are excluded so the reviewed content's hash does not depend on the review itself. The manifest's SHA-256 identifies the complete candidate, including its reviews. Hashes identify exact saved bytes, so formatting changes also create a different candidate.

Python checks required fields and types, unique identities and paths, hashes, references, source/decision consistency, and review coverage before publication. Absolute paths, parent traversal, duplicate record identities, and references to nonexistent records are rejected. Agent-written hashes and readiness claims are checked independently.

Changing reviewed content creates a new candidate. The affected content must be reviewed within the existing budget. Unchanged records keep their versions; changed records increment theirs. A focused recheck identifies the previously reviewed content, the review coverage that still applies, and the corrected findings. The service must verify review coverage for the entire new candidate; an old approval alone cannot approve a new hash. Rejected candidates remain retrievable and are never overwritten.

### Publication and SQL consistency

SQL stores live activity, requests, budgets, and the reference to the active version. GitHub stores published packages and confirmation records. A single transaction cannot be assumed to update both systems. The runtime therefore saves each publication operation and verifies its GitHub result before reporting success.

#### Candidate publication

1. Validate and freeze the candidate in service-owned storage. Save its manifest hash, file inventory, intended repository/branch/path, and a unique publication operation in SQL before network writes.
2. Publish the complete candidate in one Git commit on the project's authorized branch. Maestro's own repository uses `master`. Never publish a partial folder as a usable package.
3. Verify the remote commit, all expected file bytes and hashes, permitted paths, and unchanged frozen content using wrapper checks.
4. Save the verified commit and package reference in SQL, then emit the recorded publication result.

A package reference contains repository, commit, manifest path, manifest hash, registration version, and candidate identity. All later review, confirmation, and downstream use bind to this reference rather than branch HEAD or a mutable latest path. Publication does not activate registration.

Git updates check the expected branch head and never force-push over other changes. If the branch moves, publication preserves unrelated changes. It can retry only if the target paths are absent or contain exactly the intended bytes; different content pauses publication. Relevant source changes follow the explicit source-choice rules. Publication cannot silently change the assessed source.

#### Confirmation and activation

The CLI confirmation request identifies the displayed package reference and expected activity version. In a SQL transaction, the service verifies review coverage, current eligibility, unchanged candidate, and the Owner's explicit action, then records a pending confirmation and publication operation. The previous registration remains active while this operation is pending.

The service publishes an immutable confirmation receipt and updates the discovery index together in one Git commit. The receipt contains schema version, confirmation/request/project identities, the exact package reference, Owner identity, confirmation time, and the previous confirmation reference or null. The index contains `schema_version`, `project_id`, `current_confirmation_ref`, and ordered `confirmation_refs`. Receipt references identify path and SHA-256; the receipt itself pins the candidate's commit. The index points to that receipt and retains previous references. The receipt records the accepted Owner action; it does not claim SQL activation has already completed.

After verifying the receipt and index on GitHub, one SQL transaction updates the active pointer, completes the request and registration activity, and records the event for CLI delivery. Only then does the CLI report **Registered**. Initial registration stays pending until then; re-registration keeps its previous active version and Updating registration label.

While confirmation is pending, the service rejects cancellation, candidate replacement, and another confirmation as conflicts. It first establishes the pending confirmation's outcome, preventing competing actions from activating different versions. Cancellation accepted before confirmation is reserved prevents that reservation. A failed confirmation can return to a paused state that accepts actions only after the service establishes that its GitHub write did not take effect.

#### Publication recovery

The SQL publication record retains operation type, exact target bytes/hashes, expected prior index value, request identity, remote commit when known, and state: prepared, writing, verified, applied, or paused. Every transition is durable and replayable.

| Interruption | Recovery |
|---|---|
| Failure before a confirmed GitHub write | Inspect the intended target before resending. Missing expected content can be retried; matching content is reused. |
| GitHub accepted the write but acknowledgment was lost | Locate and verify the exact candidate or receipt and commit. Record that success without creating another candidate or confirmation. |
| GitHub is verified but the SQL activation transaction failed | Reapply the same SQL transaction using the saved request and receipt identities. Do not ask the Owner to confirm again. |
| Content or index conflicts with the saved operation | Pause with the exact conflict; neither adopt different bytes nor overwrite them. |
| GitHub cannot be queried | Keep the outcome unconfirmed and preserve the prior SQL active pointer. An unreachable service is not evidence that the write failed. |

One request cannot create multiple confirmations or activation events. The service resolves pending operations before accepting another write for that project. Publication recovery uses the configured automatic recovery limit, with a separate counter for each operation. It does not consume agent-launch retries or fidelity reviews, and a failed push does not rerun the architect. Reaching the limit pauses publication and preserves its evidence. Investigation and retry continue that operation without starting a new registration.

The discovery index is for navigation. Runtime work and downstream assignments use the SQL-confirmed exact package reference. A GitHub receipt awaiting SQL recovery cannot independently start work. Repository history alone cannot reconstruct unknown SQL conversation, budget, or pending-action state; database recovery must preserve those records.

### Re-registration

Registration can be rerun during a project's lifecycle only when that project has no work in progress. The service checks recorded activities, reserved starts, pending external operations, and actual run status; an idle CLI or a quiet agent is not evidence that work has ended.

The following prevent re-registration:

- Reserved or queued assignments awaiting launch.
- Running agents or reviewers.
- Unfinished work waiting for answers, correction, or recovery.
- Pending publication, merge, or activation operations.
- A stop or run status that remains uncertain.

Completed or cancelled activities do not block entry once their processes and external operations are resolved. Questions unrelated to unfinished work do not block entry. The CLI identifies each blocking activity by its plain subject and current state. Existing work must finish or be explicitly ended through its own process; re-registration never silently cancels it.

One SQL transaction holds the project's start lock, checks that the project is idle, and reserves it for re-registration. Every operation that reserves or starts project work checks this reservation in its own transaction. An uncertain run status prevents the project from being considered idle. While reserved, the project permits only assignments and operations belonging to that registration activity. Other work for that project cannot start; unrelated projects continue normally.

The reservation remains until registration has ended and its runs and external operations are resolved. Ending registration releases it without automatically restarting stopped work. The previous approved registration remains active unless its replacement was successfully confirmed. This shared start-check contract defines the interface registration requires; it does not define Execution scheduling or stopping commands.

Each rerun creates the next registration version while preserving prior versions. The Maestro architect may add or amend project milestones within the candidate package. These changes use the same source, scope, review, and decision rules; they do not authorize general source-plan rewriting or development breakdown.

### Comparison, activation, and cancellation

Comparison is an action in the registration view. It shows candidate additions, changes, and removals against the active version, including affected scope and completion requirements and reasons linked to findings or decisions.

Confirmation is a separate explicit action displaying the project and exact candidate version. The service verifies that this candidate is unchanged and eligible. A changed or ineligible candidate is rejected with an explanation; the current candidate must be opened and reviewed before another confirmation.

Successful confirmation makes the candidate the active registration version. Previously approved versions remain retrievable. Confirmed content cannot change silently, and activation does not start development.

Cancel registration displays the project, registration attempt, effects, and retained information, with Cancel registration and Go back controls. Cancellation follows [agent stopping rules](#cancellation) when a run is active; only confirmed termination ends the attempt. When no run or external operation is pending, cancellation ends the attempt directly. A pending confirmation rejects cancellation under [confirmation and activation](#confirmation-and-activation). Cancellation accepted during candidate publication prevents further registration advancement; the service reconciles any in-flight write and retains published artifacts before ending the attempt and releasing its reservation. Saved history is preserved. Failure or cancellation of re-registration leaves the previously approved version active; project work does not restart automatically.

Neither confirmation nor cancellation is preselected for submission. Deliberate focus on the relevant action is required before Enter activates it.

A lost action acknowledgment displays “Outcome not confirmed.” Reconnection checks the recorded outcome rather than automatically repeating the action. Explicit retries identify the original request and cannot duplicate effects.

### Registration agent response contract

Each assigned architect or fidelity-reviewer run returns one UTF-8 JSON object using contract version 1. Progress messages are separate from the final response. The service validates the object before recording findings, routing questions, or accepting a result. Free text is never interpreted as an approval or command.

| Field | Type and meaning |
|---|---|
| `contract_version` | Integer; 1. |
| `assignment_id`, `run_id`, `project_id`, `activity_id` | Nonempty strings copied from the service assignment. |
| `role` | `project_architect` or `fidelity_reviewer`; must match the assigned role. |
| `source_commit` | Exact source commit supplied in the assignment. |
| `decision_version` | Nonempty string identifying the assigned snapshot of recorded Owner decisions. |
| `result` | `completed`, `clarification_required`, or `technical_failure`. Completion describes the assignment, not registration activation. |
| `summary` | Nonempty plain description of the result. |
| `findings` | Array of finding objects; empty when none. |
| `questions` | Array of clarification objects; empty when none. |
| `candidate` | Immutable artifact reference for the architect's candidate or the reviewer's exact reviewed candidate; null when unavailable. |
| `assessment` | Immutable reference to the architect's assessment; required for a completed architect result, null for reviewer results, optional for partial architect output. |
| `reviewed_assessment` | Immutable assessment reference for the reviewer; null for the architect or when review could not be performed. |
| `review_outcome` | `APPROVE` or `REQUEST_CHANGES` for a completed reviewer assignment; null otherwise. Always null for the architect. |
| `failure` | Object with nonempty `code` and plain `message` for technical failure; null otherwise. |

All listed fields are required; no other top-level fields are accepted. An artifact reference contains `path` (relative to the assigned artifact root), `sha256` (64 hexadecimal characters), and `version` (nonempty string). Absolute paths and parent traversal are invalid. The wrapper verifies artifact existence, content hash, and permitted location. For repository publication it also performs the GitHub checks under [agent delegation](#agent-delegation); an artifact hash alone is not publication evidence. The adapter defines how artifacts are transported without changing these checks.

Each finding contains `local_key`, `subject`, `severity` (`blocking` or `non_blocking`), `explanation`, `impact`, `requested_correction`, `source_refs`, and `affected_items`. Text fields are nonempty. Source references contain a repository-relative `path`, `commit`, and a heading or line locator. Missing-source findings instead include a nonempty `missing_information` explanation and may have an empty source-reference list. Affected-item references include the existing identifier, plain subject, and version. Empty affected-item lists are permitted for project-wide findings.

Each question contains `local_key`, plain `subject`, `question`, `reason`, `recipient` (`project_architect` or `owner`), linked finding keys, and `options`. Options contain a local key, plain label, tradeoff, and recommendation reason or null. An empty options array requests written information; all questions allow written clarification. Questions follow existing authority boundaries and do not solicit approval for routine technical choices.

Local keys are unique within the response and only link its entries. They are not milestone, finding, or review numbers. The service assigns persistent record identities under the naming conventions and resolves local links when saving. References to existing records preserve their identities and subjects.

| Validation condition | Required result |
|---|---|
| Completed architect assignment | Assessment and candidate references present; findings may still block registration. |
| Completed reviewer assignment | Exact assigned assessment and candidate references present. APPROVE has no blocking findings or unanswered questions. REQUEST_CHANGES has at least one blocking finding. |
| Clarification required | At least one specific question; available partial candidate may be referenced. No review approval. |
| Technical failure | Failure details present; no review approval. Partial findings or artifacts are not accepted as completed work. |
| Wrong context, unknown version, malformed fields, conflicting result, or unverifiable artifact | Preserve diagnostic evidence and apply technical recovery; do not infer success or turn it into a substantive planning rejection. |
| Duplicate or late response | A matching replay of an already accepted assignment/run result returns its recorded receipt. Conflicting content, a superseded assignment, or a non-current run cannot overwrite the result or current candidate. |

The service checks the response against the assignment's source, saved decisions, and artifact versions. It saves the accepted response and resulting findings and questions together in one SQL transaction before acknowledging or displaying them. Technical response corrections use the technical retry budget; completed substantive reviews use the planning-review budget. The response cannot set review counts, grant extra rounds, activate registration, or issue execution commands.

### Technical recovery

Completed reports, reviews, decisions, and source/version references survive agent failure, failed GitHub publication, or service restart. Registration resumes from the last verified step; unverified results do not count as completed work.

Before restarting interrupted agent work, the service checks whether the original run remains active. Unknown status pauses recovery immediately and blocks a replacement. Once the run is confirmed ended, recovery supplies the saved assignment, answers, findings, and candidate files. Unfinished output remains draft until a complete response passes deterministic checks.

Technical failures do not consume planning review rounds. The separate configurable technical retry limit defaults to **two automatic recovery attempts per agent assignment**, excluding its initial run. Recovery runs retain the same assignment retry accounting. This is a maximum, not a requirement to exhaust attempts.

| Failure | Recovery behavior |
|---|---|
| Temporary tool or service interruption | Retry within the automatic limit once the original run is confirmed ended. |
| Correctable response-format or output validation failure | Supply the specific validation errors with the recovery assignment, within the automatic limit. |
| Missing access, unsupported model, or another cause requiring intervention | Pause immediately and explain the required correction. |
| Unknown cause | Pause for investigation rather than blindly repeat the run. |
| Run-duration limit | Follow [unresponsive-run handling](#unresponsive-runs); no automatic retry for timeout alone. |

After the automatic limit is exhausted, the activity pauses with a plain failure explanation, an attention item, and any known corrective action. Manual **Retry activity** is appropriate after intervention, such as restored access, corrected configuration, or recovered tool availability; it is not the default recommendation for an unchanged failure.

Each explicit manual retry permits one additional run, preserves failure history and review counts, and does not reset the automatic retry budget. Failure pauses the activity again. This activity action is distinct from the connection-only `/retry` command and cannot bypass unresolved original-run status. The [activity retry request](#activity-retry-request) records the intervention and launch reservation.

A tool or API may retry internally within the same run, but these retries do not extend its duration or consume Maestro's launch-recovery allowance. Their count and reasons are recorded separately when available. Only launching an automatic replacement consumes a Maestro recovery attempt; checking supervisor state and replaying events do not. The supervisor enforces the deadline even when the tool does not report its internal retry count.

#### Activity retry request

The paused registration activity displays **Retry activity** alongside the failure reason and any known correction. It requests a short description of the intervention, then submits `registration.retry` through `POST /api/v1/requests`. This is an explicit activity action, not a slash command or ordinary answer.

The existing request envelope supplies `request_id`, `project_id`, `activity_id`, `expected_version`, and null `question_id`. For an agent retry, its `payload` contains `assignment_id`, `failed_run_id`, and nonempty `intervention`. The text records what changed; it is not proof that access, model availability, or configuration is now valid.

In one SQL transaction the service validates that the activity is technically paused, the referenced run is the current failed run, termination is confirmed, and no retry is pending. It saves the intervention and reserves one manual run under the same assignment. Capability/access checks must pass before the agent starts. A failed check returns the activity to its explained paused state without resetting counters.

For a paused publication retry, the payload instead contains `publication_operation_id` and nonempty `intervention`; agent run fields are absent. The service validates the current operation and reserves reconciliation once under the same request identity. It queries GitHub before any write and applies [publication recovery](#publication-recovery), without launching an agent or resetting the publication counter. Each manual request permits one further write attempt after reconciliation; another failure pauses again. The view labels this action **Retry publication** so its effect is explicit.

An identical request replay returns its saved receipt. Conflicting content or a stale activity/run returns 409; no extra launch occurs. A lost acknowledgment displays **Outcome not confirmed** and is reconciled through the existing request-status endpoint. Reconnection never resubmits automatically. Cancellation, a passing result, or a fidelity disagreement cannot be bypassed with technical retry.

#### Adapter configuration

The runtime reads `/etc/maestro/agents.toml`. Installation supplies this file; a missing or invalid file disables agent launch with a plain configuration error while read-only CLI views remain available.

| Setting | Meaning |
|---|---|
| `workspace_root` | Absolute workspace root; default `/var/lib/maestro/workspaces`. |
| `automatic_recovery_attempts` | Nonnegative integer; default 2. |
| `registration_architect.run_timeout_seconds` | Positive integer; default 1800. |
| `registration_fidelity_reviewer.run_timeout_seconds` | Positive integer; default 1800. |
| `tools.codex.executable`, `tools.claude_code.executable` | Absolute installed tool paths. |
| `tools.<tool>.credential_profile` | Reference to provisioned service credentials, never the secret itself. |
| `tools.<tool>.settings_profile` | Reference to service-managed tool settings and permitted operations. |
| `tools.<tool>.allowed_model_ids` | Full provider identifiers allowed for explicit role selection; not default model choices. |

Effective configuration is hashed and recorded for each assignment/run. Changes affect new runs after validation, never a running agent. Changing configuration does not reset an assignment's recovery count. No duration default is assigned to other planning or execution roles. The registration fidelity-review setting in [review limits and decisions](#review-limits-and-decisions) is stored in the same file but has separate accounting and is fixed for each registration attempt.


## Journeys and interactions

The following journeys connect the behavior defined in the sections above. Each row identifies the interaction, result, and essential failure behavior; linked sections own the detailed rules. These scenarios define expected behavior, not a requirement for a separate test per row.

### Open and use the workspace

**Starting condition:** The CLI is installed; a configured or fallback service address is available. The service may have no projects. Populated views use its saved records.

**Entry:** Launch `maestro`.

**Expected journey result:** The project overview and selected conversation display recorded service information. Navigation changes interface focus without controlling project work.

| Sequence and interaction | Trigger | System behavior | Expected result | Essential failure behavior |
|---|---|---|---|---|
| Launch | `maestro` | Contact the configured service; use [startup states](#startup-and-connection-states). | Connected overview, with no project selected; no automatic service start. | Unavailable state and retry option; no false empty list. |
| Inspect commands | `/help` or command-specific help | Use the [command definitions](#commands). | Available syntax and context guidance, also offline; no state change. | Unimplemented commands are excluded; context limitations are explained. |
| Select a project | Project control or `/projects`, followed by selection | Apply [project targeting](#projects-and-targeting). | Correct conversation and visible selected project; unsent text clears on a switch. | Missing, ambiguous, or conflicting targets require resolution. |
| Read history and findings | Load earlier, New messages, `/findings`, or expand/close details | Use [conversation behavior](#layout-and-conversation). | Recorded content, stable context, and correct reading position; viewing changes no finding state. | Failed retrieval is distinct from [empty results](#empty-results). Activity selection follows [project activity rules](#project-activities-and-registration-labels). |
| Open attention | `/attention` or another-project notice | Follow [attention routing](#attention). | The selected question or activity action opens in its project; a notice alone does not pull focus or perform an action. | Disconnection blocks service retrieval; no items is shown only after successful lookup. |
| Reconnect | `/retry` after connection loss | Refresh saved state and missed updates under [connection rules](#startup-and-connection-states). | Current information restored without replaying earlier submissions. | Stale-marked conversation remains until connection succeeds. |
| Exit | `/exit` | Close the CLI session. | Service activity and saved records remain; a new launch selects no project. | Unsent text triggers the defined exit warning. |
| Use terminal controls | Focus keys, resize, or paste | Apply [keyboard and terminal behavior](#keyboard-and-terminal-behavior). | Focused control activation, readable context, and paste without automatic submission. | An undersized terminal requests enlargement without stopping service work. |

### Answer a project question

**Starting condition:** A connected service has an identified question awaiting an answer; the question is selected in its project or registration context.

**Entry:** Open the question from attention or the conversation.

**Expected journey result:** An explicit answer is recorded once against the original question and delivered to its process. Receipt and resolution remain separate.

| Sequence and interaction | Trigger | System behavior | Expected result | Essential failure behavior |
|---|---|---|---|---|
| Prepare an answer | Select a choice or enter text | Apply [question input rules](#questions-and-answers). | Choice fills the input; optional clarification and new lines remain unsent. | Without a selected question, ordinary text is not accepted; invalid context cannot execute. |
| Send | Send or Enter in answer input | Validate the original question and follow [save and delivery](#save-and-delivery-sequence). | Sending becomes Answer received only after SQL save acknowledgment; answer appears and input clears. | Not sent retains text for explicit retry. A stale question is explained, not rerouted. |
| Retry an uncertain answer | Explicit resubmission | Recognize the original request. | At most one recorded answer and process effect. | Lost acknowledgment is identified as unconfirmed delivery; reconnect alone does not resubmit. |
| Resolve clarification | A process asks a linked follow-up | Retain the original answer and identify the missing information. | New question/input context is explicit. | Ambiguity remains a clarification request, not an approval. |

### Register a project or selected portion

**Starting condition:** The service and CLI are connected; repository and overview path are available. Actual assessment requires configured agents, source access, and package publication access.

**Entry:** `/register <repository>` or Register project, with the required overview path and scope supplied during intake.

**Expected journey result:** A ready package becomes active only after explicit confirmation of the exact candidate. Development does not start.

| Sequence and interaction | Trigger | System behavior | Expected result | Essential failure behavior |
|---|---|---|---|---|
| Supply entry, scope, and architect selection | Registration request | Read overview references, apply [intake and scope](#intake-and-scope), and record the explicit [tool and model selection](#tool-and-model-selection). | Intended project, confirmed whole/partial boundary, and supported architect selection before launch; an existing process is reused. | Missing access, source, or required clarity is reported; unsupported or unverifiable model selection prevents launch. No guessed documents or silent scope expansion. |
| Assess source | Validated intake | Use [assessment and review](#assessment-and-independent-review), [dependency checks](#purpose-and-dependency-checks), and [review limits](#review-limits-and-decisions). | Source-backed findings, non-blocking observations, and readiness or a specific needed decision. | Material blockers or unresolved disagreement pause at the configured limit; technical failure follows recovery rules. |
| Inspect or answer | `/registration`, findings, or a linked question | Render the process and [package records](#package-structure); use the answer journey. | Exact findings, versions, limits, and retained decision records are visible. | Missing records and retrieval failures remain distinct; receipt is not package approval. |
| Handle changed source | Relevant source commit changes | Apply [source consistency](#source-consistency). | Explicit choice to retain reviewed source or recheck updated source within the existing budget. | No mixed source versions or silent budget reset. |
| Confirm | Deliberately focused Confirm registration | Apply [activation rules](#comparison-activation-and-cancellation). | Exact eligible candidate active and retrievable from GitHub. | Changed/ineligible candidate is rejected; uncertain delivery shows Outcome not confirmed. |
| Cancel or go back | Explicit cancellation or Go back | Apply the same action rules. | Confirmed cancellation ends the attempt and retains saved history; Go back does not cancel. | No accidental action from ordinary conversation Enter; unknown outcome is reconciled from saved records. |

### Update a registration

**Starting condition:** A project has an active registration. Its work must finish or be explicitly stopped before re-registration.

**Entry:** Registration intake for the already registered project.

**Expected journey result:** A reviewed revision can replace the active version while preserving history.

| Interaction | Trigger | System behavior | Expected result | Essential failure behavior |
|---|---|---|---|---|
| Begin re-registration | Explicit request | Apply [re-registration rules](#re-registration). | Request identified as re-registration; new starts blocked until it ends. | Existing work prevents entry; unrelated projects are unaffected. |
| Compare candidate | Compare action | Apply [version comparison](#comparison-activation-and-cancellation). | Additions, changes, removals, and reasons shown against the active version. | Exact version checks prevent silent substitution. |
| Review and resolve | Assessment, answer, confirmation, or cancellation | Reuse the registration and answer journeys above. | Confirmed new version or retained prior active version, with history preserved. | Failure/cancellation retains prior active registration and does not restart project work. |

### Recover an interrupted registration

**Starting condition:** Registration has saved process, source, review, and decision records.

**Entry:** Agent failure, publication failure, service restart, or an uncertain confirmation/cancellation outcome.

**Expected journey result:** Activity resumes from the last verified step or pauses visibly at a configured limit, without false completion or duplicate effects.

| Interaction | Trigger | System behavior | Expected result | Essential failure behavior |
|---|---|---|---|---|
| Resume verified work | Technical interruption | Apply [technical recovery](#technical-recovery). | Reports, answers, versions, and review budget survive; unverified results stay incomplete. | Technical retry limit pauses activity and raises attention. |
| Verify publication | Candidate or confirmation publication | Apply [publication and SQL consistency](#publication-and-sql-consistency) and [delegation checks](#agent-delegation). | Required commit and permitted changes verified on GitHub. | A reported or local-only commit cannot establish publication. |
| Reconcile an action | Connection returns after unknown action outcome | Query saved outcome under [activation rules](#comparison-activation-and-cancellation). | Recorded result displayed; explicit retry cannot duplicate effects. | No automatic replay or inferred success. |

## Constraints and unresolved details

The following architectural mechanisms remain unresolved:

| Area | Unspecified detail |
|---|---|
| Service interface | CLI and package reference contracts are defined above; executable request and package validators remain implementation work. |
| Setup and access | Concrete installation, configured agent routes, required access, and startup instructions are not yet verified on the AI box. |
| Persistence | Physical SQL schema, broader runtime recovery internals, and database backup/restore procedures. Package publication and activation consistency are defined above. |
| Agent integration | Tool/model selection and shared adapter behavior are defined above. Tool transports, artifact handling, process supervision, and retry requests are specified above. Installed tool capability checks, model identity evidence, filesystem isolation, and systemd behavior require operational verification. Registration role responsibilities and response fields are defined; executable validation schemas remain implementation work. |
| Registration formats | Package records, index, and locations are defined above. Executable JSON Schemas and detailed source validation mechanics remain implementation work. Markdown source templates are defined in the Planning Guide. |
| Execution policy | Implementation-review authority, coding correction limits, merge authority, and development completion policy remain provisional and require separate Execution design. Registration controls do not settle them. |
| Terminal behavior | Practical evaluation of message scrolling and the initial terminal dimensions. |

