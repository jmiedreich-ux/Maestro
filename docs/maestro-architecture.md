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

Opening details preserves the selected project and question linked to the input. Closing details restores the prior reading position. Viewing a finding does not acknowledge, resolve, or approve it.

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

### Attention

The attention view lists outstanding questions and decisions across projects, identifying the project, requesting agent or process, and response needed. Selecting an entry opens the corresponding project and question with the input linked to it.

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
| `/findings` | Open blockers, non-blocking observations, and review findings for the selected project's current process. A selected finding exposes explanation and evidence; no review or state change is initiated. |
| `/retry` | Retry the service connection. It does not start the service, repeat previous submissions, or retry project work. |
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

### Empty results

Empty states appear only after successful retrieval. A lookup failure is displayed as a failure, and missing project or process context follows the targeting rules.

| Result | Display |
|---|---|
| No registered projects | “No projects registered,” a Register project action, and the command input. The action requests a repository and enters registration intake. |
| No attention items across projects | “No questions or decisions need your attention.” |
| No findings for the current process | “No findings recorded for this process.” |
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

A minimum terminal width and height protects readable project, question, and input context. Below that size, the CLI displays “Enlarge the terminal to continue.” Resizing does not stop service work. Exact dimensions and input-height limits are unspecified.

## Registration

### Purpose and authority

Registration checks whether Maestro can understand and operate on supplied project information. It identifies the project, verifies repository access, locates source material, checks its format and meaning, and produces a versioned package for confirmation.

The project architect supplies outcomes, architecture, scope, completion requirements, and source corrections. That role may be human, an agent, or both. The Maestro architect assesses the source; a separate Fidelity Reviewer checks the assessment. The Owner role supplies decisions and final confirmation through the CLI.

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

The intake request provides an explicit repository and repository-relative project overview path, and selects the whole supplied plan or a defined portion. An already registered repository is explicitly identified as re-registration before that process proceeds. The service records project identity, checks read access and that the repository matches the intended project, and reports missing access.

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
2. The Maestro architect assesses meaning, scope, dependencies, and evidence, then produces findings.
3. The Fidelity Reviewer independently compares the findings with the source and checks whether blockers are justified.
4. The Maestro architect amends its findings where needed.
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

Cancel registration displays the project, registration attempt, effects, and retained information, with Cancel registration and Go back controls. Cancellation ends that attempt and preserves its saved history. Failure or cancellation of re-registration leaves the previously approved version active; project work does not restart automatically.

Neither confirmation nor cancellation is preselected for submission. Deliberate focus on the relevant action is required before Enter activates it.

A lost action acknowledgment displays “Outcome not confirmed.” Reconnection checks the recorded outcome rather than automatically repeating the action. Explicit retries identify the original request and cannot duplicate effects.

### Technical recovery

Completed reports, reviews, decisions, and source/version references survive agent failure, failed GitHub publication, or service restart. Registration resumes from the last verified step; unverified results do not count as completed work.

Technical failures do not consume planning review rounds. Technical retries have a separate configurable limit. Reaching it pauses registration and produces an attention item. The technical retry default is unspecified.

## Journeys and interactions

The following journeys connect the behavior defined in the sections above. Each row identifies the interaction, result, and essential failure behavior; linked sections own the detailed rules. These scenarios define expected behavior, not a requirement for a separate test per row.

### Open and use the workspace

**Starting condition:** The CLI is installed; the service connection is configured. Connected views require readable service-held project and conversation records.

**Entry:** Launch `maestro`.

**Expected journey result:** The project overview and selected conversation display recorded service information. Navigation changes interface focus without controlling project work.

| Sequence and interaction | Trigger | System behavior | Expected result | Essential failure behavior |
|---|---|---|---|---|
| Launch | `maestro` | Contact the configured service; use [startup states](#startup-and-connection-states). | Connected overview, with no project selected; no automatic service start. | Unavailable state and retry option; no false empty list. |
| Inspect commands | `/help` or command-specific help | Use the [command definitions](#commands). | Available syntax and context guidance, also offline; no state change. | Unimplemented commands are excluded; context limitations are explained. |
| Select a project | Project control or `/projects`, followed by selection | Apply [project targeting](#projects-and-targeting). | Correct conversation and visible selected project; unsent text clears on a switch. | Missing, ambiguous, or conflicting targets require resolution. |
| Read history and findings | Load earlier, New messages, `/findings`, or expand/close details | Use [conversation behavior](#layout-and-conversation). | Recorded content, stable context, and correct reading position; viewing changes no finding state. | Failed retrieval is distinct from [empty results](#empty-results). Missing current-process selection rules remain unresolved below. |
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
| Service interface | API endpoint names, connection configuration, and request/event schemas. |
| Source of initial project activity | The supported way to supply real project, event, and question records before registration exists is not defined. |
| Process context | Selection among historic or concurrent processes, and question context during pre-project registration intake, needs explicit rules. |
| Setup and access | Concrete installation, configured agent routes, required access, and startup instructions are not yet verified on the AI box. |
| Persistence | SQL schema, broader runtime recovery internals, duplicate-request recognition, and SQL-to-GitHub package update consistency. |
| Agent integration | Detailed Project Architect and Fidelity Reviewer contracts, structured agent response formats, and Model Execution Adapters. |
| Registration formats | JSON package schema, package index details, package folder locations and filenames, and detailed source validation mechanics. Markdown source templates are defined in the Planning Guide. |
| Configuration | Review configuration location and format; numeric technical retry default. |
| Terminal behavior | Remaining argument syntax, input-height limit, minimum supported dimensions, and practical evaluation of message scrolling. |

