# Maestro Architecture

## Purpose and boundaries

The [project overview](maestro-project-overview.md) defines project purpose, delivery scope, and current-state evidence. This architecture defines the service, agent, storage, and terminal boundaries.

This document describes system structure and behavior. It is a design specification, not a statement of implemented capability. Sections marked **provisional** describe unsettled architecture.

The initial interface is the Maestro CLI. The command center within the Reporting and Command Interface is outside the initial scope. Command-center support uses the same service operations, registration process, and record sources. Mobile presentation is undecided; neither a mobile terminal nor a separate interface is specified.

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
| Python runtime service | Own process activity, validate requests, persist records, and coordinate assigned agent operations. |
| Maestro CLI | Display service information and collect explicit commands, linked answers, and registration actions. |
| SQL database | Hold current state and durable conversation/action records. |
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

The runtime handles deterministic enforcement; assigned agents supply judgment. A successful command or an agent's message does not constitute approval or automatically change project state. State changes follow the relevant process rules.

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

Registration initiation explicitly selects Claude Code or Codex and the exact model/version for the architect. The fidelity reviewer has a separate tool and model/version selection. The service checks that the selected model/version is supported by the selected tool before that role begins. An unavailable or unverifiable selection is reported before launch; no silent substitution is permitted. Records retain the requested model and the model reported by the tool. Concrete tool support for these checks remains to be verified.

#### Agent workspaces

Workspaces are service-managed on the Linux AI box. The configurable root defaults to `/var/lib/maestro/workspaces/`; a registration attempt uses `<project-id>/<registration-attempt-id>/` beneath it. Its architect workspace contains `source/` at the exact assigned repository revision and `output/` for assessments and candidate files. The adapter starts the agent with its assigned workspace as the working directory. Separate attempt directories isolate concurrent projects.

The fidelity reviewer receives a separate workspace with read-only access to the exact source, architect assessment, and candidate under review, plus a separate writable output directory. It cannot amend the architect's files.

Completed, cancelled, and interrupted workspaces remain until explicitly removed; automatic cleanup is outside the initial behavior. Removal is permitted only when no agent uses the workspace and no pending review or recovery depends on it. Removing a workspace does not remove SQL registration history or published GitHub documents. Those durable records remain authoritative; workspace files support inspection and recovery.

#### Assignment delivery and clarification

The service prepares a structured assignment file containing:

- Project, registration activity, assignment identity, and assigned role.
- Role responsibilities and the specific task.
- Exact source revision, document paths, selected scope, recorded decisions, relevant answers, and outstanding questions.
- Prior findings and candidate references when continuing work.
- Permitted actions, writable locations, limits, and conditions requiring clarification.
- Required response format and output location.

The adapter launches the selected tool and model in the workspace with instructions to read this file. Each run receives a fixed assignment snapshot. Later answers remain recorded by the service and enter a follow-up assignment; they do not change a running assignment.

Clarification can contain several questions, several answers, and additional follow-ups. The complete exchange stays linked to the same registration activity. An agent returning clarification ends that run. A follow-up assignment supplies the relevant saved context rather than relying on prior session memory. Incomplete answers or newly identified ambiguity can produce specific follow-up questions without resetting the fidelity review budget.

The architect resumes when answers needed for its next step are available. Questions that do not prevent that step may remain open. Individual answer arrival does not itself launch another run.

#### Progress reporting

The CLI distinguishes confirmed service status from agent-reported progress. Service status describes facts such as running, waiting for answers, completed, or failed. Agent progress briefly describes work such as reading source documents, assessing architecture, preparing findings, or submitting results.

The service saves these updates in SQL before display. Progress messages establish neither completion nor approval. No estimated completion percentage is shown. During silence, the CLI retains the last update and shows elapsed time without assuming the run has stalled.

#### Completion handling

The service checks that the returned response matches the assigned project, activity, source revision, and [registration response contract](#registration-agent-response-contract). Referenced files must exist in permitted locations and match their recorded hashes. Required publication must pass the [GitHub wrapper checks](#agent-delegation).

The service saves the validated response, findings, questions, and artifact references before advancing the activity. A successful tool exit alone is insufficient. Missing or invalid output enters [technical recovery](#technical-recovery).

A valid architect assessment proceeds to independent fidelity review. Clarification waits for the necessary answers. Passing review still requires registration eligibility checks and explicit final confirmation before activation.

#### Cancellation

The service records cancellation and asks the adapter to stop the active run. The CLI displays **Stopping** until termination is confirmed, then **Cancelled**. Saved findings and files remain available; unfinished output cannot advance registration. Cancellation does not undo commits or previously accepted work.

If termination cannot be confirmed, the CLI displays **Stop unconfirmed** and the service blocks replacement runs until the original status is resolved. A completion received while cancellation is pending is retained but cannot advance the activity. Sending a stop request is not proof of termination.

#### Unresponsive runs

Silence alone does not trigger a restart. When the adapter confirms a quiet run is active, the service continues waiting within its run-duration limit. When status cannot be established, it reports uncertainty and blocks a replacement.

Maximum run duration is configurable by role; starting durations remain undecided. Progress messages do not reset the limit. Reaching the limit requests termination. Recovery can start only after termination is confirmed and remains subject to the technical retry budget.

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

Connection attempts time out after 5 seconds; ordinary requests time out after 15 seconds. Long-running activity is accepted as a durable request and followed through events rather than holding an HTTP request open.

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

Read responses contain `data` and `event_cursor`. List responses include `next_cursor`, null when exhausted. Project summaries include identity, plain name, registration status, activity state, and attention count. Activity records include their project identity; question and finding records include both project and activity identities. Names and coded subjects remain human-readable even when internal IDs are opaque.

A submission contains `request_id`, `operation`, `project_id`, `activity_id`, `question_id`, `expected_version`, and `payload`. Context fields may be null only when inapplicable, such as initial repository intake. The service validates the required context for each operation. Operation names are `registration.start`, `question.answer`, `registration.confirm`, and `registration.cancel`. Initial intake supplies repository and overview path; missing scope is collected through saved intake questions. Answer payloads contain text and an optional choice reference. Registration actions identify the exact candidate or attempt and its version.

Receipts contain request identity, status, and any created project/activity identities. Status is accepted, completed, or rejected; accepted means durably recorded, not completed activity. Errors contain `code`, plain `message`, and affected fields. Invalid input returns 400, unavailable access 403, missing records 404, stale context or conflicting request content 409, and unavailable service 503. No error is rendered as an empty result.

Events carry `schema_version`, `event_id`, `occurred_at` in UTC, `project_id`, `activity_id`, `type`, and `data`. Types cover project/activity changes, conversation messages, questions, findings, request outcomes, and attention changes. Events are emitted only after SQL commit. Service-wide events have null project/activity context. The initial snapshot cursor and SSE replay prevent gaps between loading and subscribing; repeated event IDs are ignored. Reconnect uses `Last-Event-ID`; an unavailable cursor requires a fresh snapshot. Heartbeat comments arrive every 15 seconds; 45 seconds without stream traffic triggers disconnection. Heartbeats create no SQL or conversation records.

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

Read-only lookups do not require a new durable record before handling. SQL recording does not replace registration-package publication; the relationship between SQL updates and GitHub package updates is not yet specified.

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

Switching activities clears unsent text without saving, transfer, or warning, and puts input into commands-only mode. Explicitly opening an eligible question links input to that exact question. Opening attention selects its project and activity before linking the question. Opening a finding changes no finding state. Activity-specific commands use the selected activity; missing activity context requests selection. `/registration` opens an ongoing registration attempt, or the latest registration record when none is underway, and applies the same activity-switching input rules. Historical activity actions remain subject to current eligibility.

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

The attention view lists outstanding questions and decisions across projects, identifying the project, requesting agent or process, and response needed. Selecting an entry opens the corresponding project, activity, and question with the input linked to it.

A notice identifies the other project and the response needed. It does not change focus or interrupt input. Selecting the notice uses the same attention-navigation behavior, including the project-switch rule.

Opening a question does not resolve it. It remains outstanding until the process resolves it.

### Commands

Slash commands perform defined operations. Ordinary text follows the answer rules in the next section. Equivalent typed commands and controls invoke the same operation.

| Command | Behavior |
|---|---|
| `/help` | List implemented commands and plain explanations. `/help <command>` shows syntax, required inputs, an example, and required project context. Contextually unavailable commands explain why. Help works without the service and changes no project state. |
| `/projects` | Open the project overview. Showing the list preserves selection; choosing an entry selects that project. |
| `/attention` | Open questions and decisions across projects. |
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

Each explicit submission receives a client-generated request identity. Retrying unchanged text and choice for the same question reuses that identity. Edited content receives a new identity only after the previous submission is reconciled. If the earlier answer was received, show its receipt without replacing it. If its outcome remains unknown, retain edited text as unsent. If the earlier request is absent or rejected and the question remains eligible, an explicit new submission can proceed.

SQL enforces unique request identities and stores their payload and result. Same identity and same payload returns the recorded result; same identity with different payload is rejected. Request recording, question eligibility, and answer acceptance occur atomically so racing or delayed submissions cannot both answer the same question. Saved answers are routed through a durable pending-delivery record. Consumers use request identity to recognize repeated delivery and apply the answer once; a service restart cannot silently lose the accepted answer. This receipt contract does not claim that arbitrary external agent operations are exactly-once.

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

Inputs require sufficient clarity to organize work without inventing requirements, not a fully specified implementation or a complete code audit.

Project milestones describe meaningful outcomes, releases, or component boundaries. The subsequent breakdown process produces development milestones linked to those outcomes, without assuming a one-to-one relationship or redefining the project scope. Registration retains the supplied outcome structure.

### Intake and scope

Registration initiation includes [architect tool and model selection](#tool-and-model-selection) before agent launch. The intake request provides an explicit repository and repository-relative project overview path, and selects the whole supplied plan or a defined portion. An already registered repository is explicitly identified as re-registration before that process proceeds. The service records project identity, checks read access and that the repository matches the intended project, and reports missing access.

Only one registration process can be active per project. A duplicate request opens that process instead of creating a competing process or another version. This restriction does not prevent registration or work on unrelated projects.

Defined-portion selection interprets guide-compatible source, displays milestone identifiers with their plain subjects, and accepts selected milestones or a narrower written boundary. The interpreted inclusions, exclusions, and outside dependencies are presented for confirmation. A narrower portion requires a recorded description, not an inferred expansion.

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

A usage walkthrough identifies how the capability is entered, its prerequisites and connections, and how its result is observed. Each essential dependency must already exist or be included in the supplied work and dependency structure. An exclusion cannot remove an essential operation while preserving the same completion claim; the missing work or a narrower outcome requires an explicit scope decision.

Targeted source inspection checks claimed dependencies. For authentication, relevant evidence includes route protection, application or API connections, required configuration or credentials, unfinished components, and operational results.

| Evidence level | Meaning |
|---|---|
| Reported to exist | A source claim without verification. |
| Supported by source inspection | Code appears present and connected. |
| Verified in operation | Operational evidence supports the capability. |

Source inspection is not operational proof. Unverified behavior remains identified, and the assessment is not a full code audit.

Registration records the usage walkthrough, prerequisites, and completion evidence in the supplied outcome's acceptance criteria and definition of done. Each criterion identifies expected behavior and conditions, verification evidence, the pass boundary, and accepted exceptions. The definition of done also includes required reviews and other completion obligations.

A declared usable capability requires evidence of the same journey through the actual connected system. Completed components or sample-data screens alone do not establish it. Component outcomes remain valid when identified and assessed as components. Registration assesses this expected completion path without requiring unbuilt functionality to exist already.

Detailed development criteria belong to the subsequent breakdown process and remain traceable to project criteria without weakening them. Material ambiguity encountered there requires clarification.

### Review limits and decisions

A configuration file sets the maximum planning review rounds. The default is **two rounds**:

- One architect report followed by one independent review constitutes a round.
- An amended report sent for another review consumes the next round.
- Registration may reach readiness after the first round.
- Source updates and clarifications do not silently reset the budget.

At the limit, unresolved blockers or disagreement pause registration for an Owner decision. The limit neither forces approval nor starts another automatic review.

The registration view displays the current step, working agent, round and limit, findings, failures, progress or waiting state, and required decisions.

A question identifies the relevant findings and registration version. Its recorded response is routed to the paused step; the architect can amend the report and affected findings can be rechecked within the remaining budget. Clarifications, scope decisions, and accepted limitations remain linked to their requests and affected outcomes or criteria in the package.

### Package structure

A registration package is stored in the project's own GitHub repository, with a separate folder per registration version.

| Record group | Contents |
|---|---|
| Summary | Project identity, exact source references, findings, and registration outcome. |
| Project outcome outline | Supplied milestones, purposes, scope, priorities, and dependencies. |
| Completion requirements | Project-level criteria, definitions of done, usage walkthroughs, and required evidence. |
| Review and decision records | Architect findings, independent reviews, amendments, retained non-blocking findings, linked clarifications, scope decisions, and accepted limitations. |

Structured JSON is authoritative. Small, focused files contain plain descriptions and explicit relationships. An index identifies records, versions, and relative references. Python validates required fields and links against the schema.

Each fact has one authoritative location. The CLI and generated human-readable reports render package records instead of maintaining competing copies. Exact content versions remain identifiable; downstream processing consumes the confirmed package version rather than mutable latest files.

### Re-registration

Registration can be rerun during a project's lifecycle only when that project has no work in progress. Existing work must finish or be explicitly stopped. New project work is blocked until re-registration ends.

Each rerun creates the next registration version while preserving prior versions. The Maestro architect may add or amend project milestones within the candidate package. These changes use the same source, scope, review, and decision rules; they do not authorize general source-plan rewriting or development breakdown.

### Comparison, activation, and cancellation

Comparison is an action in the registration view. It shows candidate additions, changes, and removals against the active version, including affected scope and completion requirements and reasons linked to findings or decisions.

Confirmation is a separate explicit action displaying the project and exact candidate version. The service verifies that this candidate is unchanged and eligible. A changed or ineligible candidate is rejected with an explanation; the current candidate must be opened and reviewed before another confirmation.

Successful confirmation makes the candidate the active registration version. Previously approved versions remain retrievable. Confirmed content cannot change silently, and activation does not start development.

Cancel registration displays the project, registration attempt, effects, and retained information, with Cancel registration and Go back controls. Cancellation follows [agent stopping rules](#cancellation) when a run is active; only confirmed termination ends the attempt. When no run is active, cancellation ends the attempt directly. Saved history is preserved. Failure or cancellation of re-registration leaves the previously approved version active; project work does not restart automatically.

Neither confirmation nor cancellation is preselected for submission. Deliberate focus on the relevant action is required before Enter activates it.

A lost action acknowledgment displays “Outcome not confirmed.” Reconnection checks the recorded outcome rather than automatically repeating the action. Explicit retries identify the original request and cannot duplicate effects.

### Registration agent response contract

Each assigned architect or fidelity-reviewer run returns one UTF-8 JSON object using contract version 1. Progress messages are separate from the final response. The service validates the object before recording findings, routing questions, or accepting a result. Free text is never interpreted as an approval or command.

| Field | Type and meaning |
|---|---|
| `contract_version` | Integer; 1. |
| `assignment_id`, `project_id`, `activity_id` | Nonempty strings copied from the service assignment. |
| `role` | `project_architect` or `fidelity_reviewer`; must match the assigned role. |
| `source_commit` | Exact source commit supplied in the assignment. |
| `decision_version` | Nonempty string identifying the assigned snapshot of recorded Owner decisions. |
| `result` | `completed`, `clarification_required`, or `technical_failure`. Completion describes the assignment, not registration activation. |
| `summary` | Nonempty plain description of the result. |
| `findings` | Array of finding objects; empty when none. |
| `questions` | Array of clarification objects; empty when none. |
| `candidate` | Immutable artifact reference for the architect's candidate or the reviewer's exact reviewed candidate; null when unavailable. |
| `reviewed_assessment` | Immutable assessment reference for the reviewer; null for the architect or when review could not be performed. |
| `review_outcome` | `APPROVE` or `REQUEST_CHANGES` for a completed reviewer assignment; null otherwise. Always null for the architect. |
| `failure` | Object with nonempty `code` and plain `message` for technical failure; null otherwise. |

All listed fields are required; no other top-level fields are accepted. An artifact reference contains `path` (relative to the assigned artifact root), `sha256` (64 hexadecimal characters), and `version` (nonempty string). Absolute paths and parent traversal are invalid. The wrapper verifies artifact existence, content hash, and permitted location. For repository publication it also performs the GitHub checks under [agent delegation](#agent-delegation); an artifact hash alone is not publication evidence. The adapter defines how artifacts are transported without changing these checks.

Each finding contains `local_key`, `subject`, `severity` (`blocking` or `non_blocking`), `explanation`, `impact`, `requested_correction`, `source_refs`, and `affected_items`. Text fields are nonempty. Source references contain a repository-relative `path`, `commit`, and a heading or line locator. Missing-source findings instead include a nonempty `missing_information` explanation and may have an empty source-reference list. Affected-item references include the existing identifier, plain subject, and version. Empty affected-item lists are permitted for project-wide findings.

Each question contains `local_key`, plain `subject`, `question`, `reason`, `recipient` (`project_architect` or `owner`), linked finding keys, and `options`. Options contain a local key, plain label, tradeoff, and recommendation reason or null. An empty options array requests written information; all questions allow written clarification. Questions follow existing authority boundaries and do not solicit approval for routine technical choices.

Local keys are unique within the response and only link its entries. They are not milestone, finding, or review numbers. The service assigns persistent record identities under the naming conventions and resolves local links when saving. References to existing records preserve their identities and subjects.

| Validation condition | Required result |
|---|---|
| Completed architect assignment | Candidate reference present; findings may still block registration. |
| Completed reviewer assignment | Exact assigned assessment and candidate references present. APPROVE has no blocking findings or unanswered questions. REQUEST_CHANGES has at least one blocking finding. |
| Clarification required | At least one specific question; available partial candidate may be referenced. No review approval. |
| Technical failure | Failure details present; no review approval. Partial findings or artifacts are not accepted as completed work. |
| Wrong context, unknown version, malformed fields, conflicting result, or unverifiable artifact | Preserve diagnostic evidence and apply technical recovery; do not infer success or turn it into a substantive planning rejection. |
| Duplicate or late response | A matching replay of an already accepted assignment result returns its recorded receipt. Conflicting content or a superseded assignment cannot overwrite the result or current candidate. |

The service validates against the assignment's source, decision snapshot, and artifact versions. It records accepted responses and their resulting findings/questions atomically before acknowledgment or CLI delivery. Technical response correction follows the technical retry budget; substantive completed reviews consume the existing planning-review budget. The agent cannot set review counts, grant extra rounds, activate registration, or issue execution commands through this object.

### Technical recovery

Completed reports, reviews, decisions, and source/version references survive agent failure, failed GitHub publication, or service restart. Registration resumes from the last verified step; unverified results do not count as completed work.

Before restarting interrupted agent work, the service checks whether the original run remains active. Unknown status pauses recovery immediately and blocks a replacement. Once the run is confirmed ended, recovery supplies the saved assignment, answers, findings, and candidate files. Unfinished output remains draft until a complete response passes deterministic checks.

Technical failures do not consume planning review rounds. The separate configurable technical retry limit defaults to **two automatic recovery attempts per agent assignment**, excluding its initial run. Recovery runs retain the same assignment retry accounting. After both attempts fail, the activity pauses with a plain explanation, an attention item, and an explicit retry action in the CLI. This action does not bypass an unresolved original-run status. Its concrete request interface and post-limit retry accounting remain to be specified.

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
| Open attention | `/attention` or another-project notice | Follow [attention routing](#attention). | Selected question opens in its project; a notice alone does not pull focus. | Disconnection blocks service retrieval; no items is shown only after successful lookup. |
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
| Supply entry and scope | Registration request | Read overview references and apply [intake and scope](#intake-and-scope). | Intended project and confirmed whole/partial boundary; an existing process is reused. | Missing access, source, or required clarity is reported; no guessed documents or silent scope expansion. |
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
| Verify publication | Agent assignment requires a commit | Apply [delegation checks](#agent-delegation). | Required commit and permitted changes verified on GitHub. | A reported or local-only commit cannot establish publication. |
| Reconcile an action | Connection returns after unknown action outcome | Query saved outcome under [activation rules](#comparison-activation-and-cancellation). | Recorded result displayed; explicit retry cannot duplicate effects. | No automatic replay or inferred success. |

## Constraints and unresolved details

The following architectural mechanisms remain unresolved:

| Area | Unspecified detail |
|---|---|
| Service interface | CLI contracts are defined above; operation-specific registration package payloads depend on the registration schema. |
| Setup and access | Concrete installation, configured agent routes, required access, and startup instructions are not yet verified on the AI box. |
| Persistence | SQL schema, broader runtime recovery internals, registration checkpoint internals, and SQL-to-GitHub package update consistency. |
| Agent integration | Tool/model selection and shared adapter behavior are defined above. Concrete Claude Code and Codex launch/status/cancellation interfaces, artifact transport, and recovery capabilities remain to be verified. Registration role responsibilities and response fields are defined; executable validation schemas remain implementation work. |
| Registration formats | JSON package schema, package index details, package folder locations and filenames, and detailed source validation mechanics. Markdown source templates are defined in the Planning Guide. |
| Configuration | Review and technical retry configuration location and format; initial per-role run-duration limits; explicit post-limit retry request and accounting. |
| Terminal behavior | Practical evaluation of message scrolling and the initial terminal dimensions. |

