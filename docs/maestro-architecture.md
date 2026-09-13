# Maestro Architecture

## Document status

This document records the architecture being developed with the Owner. Confirmed foundations and evolving proposals are distinguished below. Proposals are subject to change and do not authorize implementation.

The [Maestro Information Review](maestro-information-review.md) remains separate reference material. Its rules and implementation details are not automatically decisions for this architecture.

## Confirmed foundations

- Maestro covers three major functional areas during project development: Planning, Execution, and Monitoring.
- The runtime is a Python backend running as a Linux service on the AI box, managed by `systemd`, communicating with agents through command-line tools or APIs.
- A future Maestro Planning Guide will define conventions and formats for project architects' planning outputs.
- A dedicated Maestro CLI is a foundational project milestone delivered before registration development.
- The initial version uses the Maestro CLI for the complete operator workflow. The command center is future scope.
- Maestro supports working on multiple projects concurrently from the foundation.
- Planning begins with project registration, initiated through the Maestro CLI.

The runtime's internal parts and the registration process below are evolving concepts. Planning's responsibilities and authority must be defined explicitly with the Owner, not inferred from earlier designs.

## Functional areas: working descriptions

Only the three area names are established here. These descriptions and examples are proposals, not settled responsibilities.

| Area | Working description | Proposed coverage |
|---|---|---|
| Planning | Define what should be built and how work is organized. | Requirements, architecture, scope, work breakdown, dependencies, acceptance criteria, and approved plan changes. |
| Execution | Carry out approved work. | Agent assignments, workspaces, implementation, checks, independent reviews, corrections, and authorized merges. |
| Monitoring | Show what is happening and where attention is needed. | Progress, agent activity, blockers, failures, time and resource usage, notifications, and action and decision history. |

## Unattended operation: evolving concept

A proposed loop connects the three areas: Planning supplies approved work; Execution carries it out and obtains checks and reviews; Monitoring tracks progress and problems. The runtime coordinates the next action under explicitly agreed rules.

The following response chart is retained as a proposal. It does not grant automatic replanning, acceptance, or merge authority.

| Situation | Proposed automated response |
|---|---|
| Work passes its checks and independent review | Complete it, merge if already authorized, and release dependent tasks. |
| A worker crashes or stalls | Recover or reassign within the approved retry limit. |
| Review finds an implementation defect | Send a bounded correction back to Execution. |
| Work reveals a missing dependency or flawed breakdown | Return it to Planning; revise automatically only within explicitly delegated authority. |
| A decision changes scope, architecture, or an owner-reserved requirement | Pause the affected work and ask the Owner. Unrelated approved work can continue. |
| Time, cost, or retry limits are reached | Stop the affected work and report why. |

Proposed boundaries: unattended operation has explicit authority limits; Execution does not approve its own results; Monitoring reports and routes problems rather than silently changing requirements. Planning's ability to adapt remains to be defined with the Owner.

The earlier shared-record and restart design was withdrawn as an assumed architecture. The CLI section now establishes SQL-first recording for conversation information and displayed state. Broader runtime storage and restart mechanics remain evolving concepts; this agreement does not reinstate the earlier design.

## Runtime

Maestro's runtime is a backend program written in Python, running continuously as a Linux service on the AI box.

It runs under `systemd`, which starts it when the machine boots and restarts it if it crashes. The program launches agent processes and communicates with them through their command-line tools or APIs.

### Evolving runtime concepts

These are working concepts, not fixed architectural requirements or implementation instructions. Their names, boundaries, and responsibilities may change as Maestro is designed.

| Proposed part | Working responsibility |
|---|---|
| Command handling | Receive requests to start, pause, resume, or stop work from the Maestro CLI; a future command center can use the same service interfaces. |
| Work coordination | Determine which approved action can run next and start it when the required resources are available. |
| Agent connections | Launch agents through their command-line tools or APIs, supply instructions, and receive results. |
| State storage | Record what is running, finished, or waiting to support recovery after a service restart. |
| Health supervision | Watch agent activity, deadlines, and failures, then apply agreed recovery or stopping rules. |

These parts could initially be modules within one Python service rather than separately deployed services.

The proposed boundary is mechanics versus judgment: the runtime enforces an agreed review requirement and receives and validates the assigned reviewer's result. A successful command does not itself count as approval.

Planning, Execution, and Monitoring could use these shared mechanisms. This sketch does not define their responsibilities or grant them decision-making authority; those will be defined separately.

## Maestro CLI foundation

The Maestro CLI is an installed operator application launched with `maestro`. Its foundation comes before registration development: service connection, project navigation, submitting actions, receiving responses, and reconnecting after exit. Registration then adds its specific workflow.

The initial version is CLI-only. The command center within the Reporting and Command Interface is deferred. Status, questions, written responses, candidate review, explicit confirmation, and cancellation must all remain usable through the CLI.

### Conversation-first interaction

Use one continuous terminal workspace, similar to Codex but with more interactive controls:

- A persistent input area supports typed commands.
- The main area shows agent messages, progress, findings, and results.
- Interactive choices appear in the flow for project selection, expanding findings, answering questions, comparing versions, and confirming packages.
- A persistent status area identifies the selected project, current process, and whether Maestro is working or waiting for the Owner.

Typed commands and equivalent controls invoke the same operation. Free-text answers are clearly distinguished from commands and tied to a specific question and project. A clarification does not become an accidental command or registration confirmation.

The CLI supports starting registration with a repository and scope, opening an existing process, inspecting findings and the exact candidate, submitting responses, explicitly confirming, and cancelling. The initial command names and boundaries are agreed below. Detailed argument syntax and remaining input behavior still need design.

Exiting closes the CLI connection, not the running process. Cancellation is a separate action. Reopening `maestro` retrieves the current service state and reconnects to updates.

### Agreed conversation direction

The approved visual direction is a terminal interface, not a command-center dashboard: project switching at the top, one continuous conversation per project, prominent pending questions, and a fixed input area with a clearly displayed recipient.

Every message identifies its source: the Owner, the speaking agent, or the Maestro service. Major activities such as registration, milestone planning, and execution have clear section markers. Routine progress stays compact; findings and reports can be expanded. The conversation is the interaction history; the persistent status area shows current state without requiring backward scrolling.

In this version, ordinary text is limited to answering an existing selected question. The input shows the project or registration context, requesting agent or process, and question. Without a selected question, the input accepts commands only. Starting a separate conversation with an agent is outside this version; the earlier recipient-selection concept is deferred. The mockup's sample messages and command hints are illustrative, not additional workflow decisions.

### Startup and service connection

Launching `maestro` attempts to connect to the configured service. It does not start the service automatically.

| Connection state | Display and behavior |
|---|---|
| Connecting | Show that the connection is being established. |
| Connected | The service responds; the CLI can request project information. |
| Unavailable | Show a plain reason and a retry option. Do not present an empty project list as though no projects exist. |

Startup opens the project overview, not a project's conversation. It provides service connection status, the project list, outstanding questions or decisions, and a persistent command input.

The project list shows each project's plain name, current activity or reason for waiting, and whether it needs attention. Order projects needing attention first, working projects next, and idle projects last. Selecting a project opens its conversation without starting, stopping, or otherwise changing project work.

### Questions needing attention

The startup attention section shows each outstanding question or decision, its project, and the agent or process asking. Selecting an item opens the correct project conversation at that question and links the input to it.

Opening a question does not answer or resolve it. It remains outstanding until resolved.

When a question has clear alternatives, present:

- A plainly worded question.
- A recommended option with a short reason, when there is a justified recommendation.
- Other viable options with their tradeoffs, not automatic labels of “less recommended.”
- A free-text response so the Owner can provide a different answer or amend an option.

When information is needed rather than a choice, request a written answer instead of forcing multiple choices.

### Answer submission and clarification

Selecting a choice fills the answer area; it does not submit it. The Owner can add written clarification, then explicitly submit with Send or Enter. Choices and written answers use the same submission step.

| Stage | CLI behavior |
|---|---|
| Sending | Show “Sending” while waiting for the service to confirm that the answer was saved. |
| Sending fails or delivery is unconfirmed | Show “Not sent” with a plain reason and retain the answer in the input for explicit retry. Reconnecting alone does not resubmit it. |
| Saved acknowledgment received | Show the answer in the conversation and clear the input. Mark the question “Answer received,” not “Resolved,” until the process evaluates it. |
| Clarification needed | Ask a specific follow-up linked to the original question. Keep the previous answer visible and identify the new question above the input. Explain what needs clarification rather than simply repeating the question or treating the answer as approval. |

If the connection drops before acknowledgment, explain: “Delivery not confirmed. Retrying will not submit your answer twice.” The “Not sent” label does not establish that the service never received it.

The service must recognize a repeated submission so a retry cannot record or act on the same answer twice, including when the original acknowledgment was lost. The technical mechanism remains to be designed.

Retaining a failed answer in the current input does not introduce draft storage: switching projects still clears unsent text under this version's rule. Receipt, evaluation, resolution, and explicit registration confirmation remain distinct.

### Explicit project targeting

Before project selection, the startup input supports service-wide actions, including selecting a project or beginning registration, and clearly displays “No project selected.”

- Every startup begins with no selected project, even when only one project exists.
- Selecting a project sets the selected project. Its name remains visible above the input.
- A project-specific command uses the explicitly named project or, when none is named, the selected project.
- If neither is available, request project selection and do not execute.
- If the explicitly named project differs from the selected project, require the Owner to resolve the mismatch before execution.
- Unknown or ambiguous project names must be resolved before execution.
- Switching projects must not silently transfer an unsent message or pending answer to the new project.
- Service-wide commands do not inherit a project target.
- Do not guess a command's or message's project from conversation text.

A selected project is the CLI's focus; a working project is one where Maestro is performing work. Do not use “active project” to mean either. This terminology does not change the meaning of an active registration version.

In this version, switching projects clears unsent text. It is not saved, restored, or transferred to another project. Draft retention and a project-switch safeguard are deferred. The separate warning about unsent text when exiting remains required.

### Initial command list

These commands are agreed for future delivery as their functionality is built. This list does not claim implementation or authorize development. Commands use a leading slash; ordinary replies remain separate from operational commands.

| Command | Purpose and boundary |
|---|---|
| `/help` | List implemented commands with plain explanations. `/help <command>` shows syntax, required inputs, an example, and whether project selection is required. Explain contextual unavailability. Help works without a service connection and changes no project state. |
| `/projects` | Open the startup-style project overview from any conversation. This is the typed equivalent of opening the project selector. Showing the list does not change selection; choosing an entry selects that project and opens its conversation. Neither action starts or stops work. Read through the service without adding a conversation entry; show connection failure rather than an empty list. |
| `/attention` | Open outstanding questions and decisions across projects. Selecting one switches to its project, opens the question, and links the reply input. |
| `/register <repository>` | Begin registration using an explicit repository, without assuming the selected project. Request the whole plan or a defined portion and open the registration conversation. Reuse this command for eligible re-registration. |
| `/registration` | Open the selected project's existing registration process or registration record, including the candidate when available. Do not start registration. |
| `/findings` | Open a compact list of blockers, non-blocking observations, and review findings for the selected project's current process. Selecting a finding opens its explanation and evidence. Unlike attention, findings need not require an Owner response. Do not start a review or change project state. |
| `/retry` | Retry a failed service connection without exiting the CLI. Equivalent to the Retry connection control. Do not start or restart the service, repeat submitted commands, or retry project work. |
| `/exit` | Disconnect this CLI session without stopping service or project work. Preserve saved conversations and pending questions. Warn before exiting if unsent text would be lost. |

Project-specific commands follow the explicit targeting rules above. Listing or opening information is not approval or a request to start work.

Do not add separate `/select`, `/status`, `/respond`, `/compare`, `/confirm`, or `/cancel` commands to this starting list. Project selection belongs in the project overview, current status remains visible, and answers use question-linked input. Comparison, confirmation, and cancellation belong in the registration view as described below.

Execution commands such as start, pause, resume, and stop remain deferred until their operations are defined. Extend the command list through further agreement, not speculative additions.

### Registration entry and scope selection

The repository supplied to `/register <repository>` is explicit. If registration is already underway for that project, show its existing process rather than starting a duplicate. If already registered, clearly identify the request as re-registration and enforce the no-project-work-in-progress restriction.

The entry flow asks whether to register the whole supplied plan or selected milestones or a defined portion. Registration review does not start development.

Defined-portion selection reads planning source formatted according to the Maestro Planning Guide:

1. Identify the supplied project milestones and their boundaries.
2. Present milestones with both their identifiers and plain subjects.
3. Let the Owner select milestones or describe a narrower portion.
4. Present the interpreted inclusions, exclusions, and outside dependencies for confirmation.

Whole-milestone selections use explicit milestone references. A narrower portion requires a recorded scope description; an agent must not silently decide what the Owner's words include. Detailed source format and selection mechanics remain to be designed.

### Actions inside the registration view

| Action | Behavior |
|---|---|
| Compare registration versions | Compare the candidate with the currently approved registration version. Show additions, changes, removals, and reasons, tied to the exact versions reviewed. |
| Confirm registration | Explicitly identify the project and exact candidate version being accepted. Confirmation activates that version but does not start development. Ordinary conversation replies never count as confirmation. |
| Cancel registration | Identify the project and registration process, explain the effect, and request explicit confirmation. End that registration attempt while preserving saved history and any previously approved registration version. Do not automatically restart project work. |

Cancellation is not CLI exit or a general stop-development command. These actions remain within the terminal registration view rather than standalone slash commands.

### Reading conversations, findings, and reports

Opening a project shows recent messages first, with “Load earlier messages” above them. Current activity and pending questions remain visible separately. Opening a conversation does not answer questions or change project work.

Findings and reports expand within the project conversation. Opening details preserves the selected project and question linked to the input; closing details returns to the same conversation position. Viewing does not acknowledge, resolve, or approve a finding.

At the bottom, the conversation follows new messages. When the Owner scrolls up, retain the reading position and show a “New messages” indicator. Selecting it returns to the latest messages. This is the initial behavior and may be revised after practical use.

When another project needs attention, show its name and the response needed without switching projects or interrupting input. Selecting the notice opens the question using the same behavior as `/attention`; the agreed project-switch rule still clears unsent text.

### Disconnection and empty views

If an open CLI loses its service connection, keep the displayed conversation visible and mark it “Disconnected—information may be out of date.” Do not accept new service actions or answers while disconnected. Keep `/help`, `/retry`, and `/exit` available.

Reconnection refreshes state and retrieves missed messages; it does not automatically resubmit previous commands or answers. A disconnected CLI does not establish that project work has stopped.

Show empty results only after a successful lookup. Failed retrieval must show a failure, not an empty result.

| Successful lookup result | Display |
|---|---|
| No projects registered | “No projects registered,” a Register project action, and the command input. The action requests a repository and enters the same flow as `/register <repository>`. |
| No outstanding questions or decisions across projects | “No questions or decisions need your attention.” This is the scope of `/attention`, not only the selected project. |
| No findings for the current process | “No findings recorded for this process.” |
| No registration for the selected project | “No registration exists for this project,” with a Register action. |

These empty states do not resolve missing project or process context; project targeting rules still apply.

### Keyboard, longer answers, and terminal size

| Key | Behavior |
|---|---|
| Tab / Shift+Tab | Move between available controls. |
| Arrow keys | Move through a focused list or choice set. |
| Enter | Activate the focused control; in the answer input, submit the answer. Selecting a choice still fills the answer area without submitting. |
| Escape | Close an open list or detail view without changing project work. |
| Shift+Enter | Insert a new line in an answer. |

Keep keyboard focus clearly visible. Pasting multiple lines only fills the input; it never submits automatically. The input grows to a limited height and then scrolls internally, keeping the conversation and question visible. The exact height remains to be chosen.

Set a minimum supported terminal width and height so project identity, the question, and input remain readable. Below it, show “Enlarge the terminal to continue,” without stopping service work. Choose actual dimensions during practical use, not in this draft.

A possible mobile view is undecided and is not an initial-version requirement. Neither a mobile-terminal approach nor a separate interface has been selected.

### Question and action validity

Before accepting an answer, the service checks that the original question is still awaiting an answer. If the question was replaced or its registration cancelled, explain what changed and do not apply the answer to another question. If a replacement exists, offer to open it without transferring the answer automatically.

The confirmation screen shows the project, exact candidate version, and Confirm registration action. If that candidate changed or is no longer eligible, reject the confirmation and explain why. The Owner must open and review the current candidate before confirming again; do not silently substitute a newer version.

The cancellation screen shows the project and registration attempt, explains what remains saved, and offers Cancel registration or Go back. Confirmation and cancellation are not preselected for submission. An ordinary Enter press in the conversation cannot trigger them; deliberately focus the relevant action first.

If confirmation or cancellation loses its connection before the result arrives, show “Outcome not confirmed,” not success or failure. On reconnection, check the recorded outcome with the service. Do not automatically repeat the action. An explicit retry must be recognized as the same request so it cannot cause duplicate effects.

### Multiple projects

The CLI can focus on one project while others continue running. Each project keeps separate conversations, process state, pending decisions, and registration versions.

Switching projects does not stop their work. Every project-specific command, response, and event clearly identifies its target project. The CLI surfaces when another project needs attention without mixing its decisions into the selected project's conversation.

The single active registration restriction applies per project, not across Maestro. Re-registration's no-work-in-progress restriction also applies to that project; it does not stop unrelated projects.

### Communication with the service

The Python service provides a local API. The CLI connects to `localhost` on the AI box.

| Direction | Mechanism | Purpose |
|---|---|---|
| CLI to service | HTTP requests | Start registration, submit an Owner response, confirm a candidate, cancel a process, or retrieve current status. |
| Service to CLI | Server-Sent Events over a persistent connection | Stream agent messages, progress, findings, and requests for input. |

Each project-specific request and event carries the project's identity. The CLI can send commands while receiving streamed updates.

The service owns the running work. Closing the terminal does not stop service activity; reconnecting retrieves authoritative current state and resumes updates. A separate agent process is not needed merely to maintain this connection.

API endpoint names, connection configuration, and event schemas remain implementation details to define.

### Information sources and SQL-first delivery

The CLI conversation receives information from three sources:

| Source | Information |
|---|---|
| Maestro service | Factual events and state changes, including work starting, waiting, stopping, or failing. |
| Agents | Messages, explanations, findings, questions, and review results returned through assigned work. |
| Owner | Commands, answers and written direction linked to existing questions, and explicit registration-view confirmations. This does not permit unsolicited agent chat. |

Agents do not write directly to the terminal. The service validates, records, and delivers information to the appropriate project conversation. An agent message does not itself change project state; the service determines and records changes under the agreed process rules.

For durable actions, answers, messages, and state changes, record information in SQL before acknowledging it as saved or delivering the saved update:

1. The service receives the agent result, service event, or Owner input requiring durable recording.
2. It validates the information and records it against the appropriate project and conversation. Service-wide inputs remain service-wide.
3. Only after saving succeeds does it acknowledge or publish the recorded information to the CLI.

SQL stores current project state and durable conversation history; it is not merely a queue of screen output. Live delivery notifies the CLI of recorded changes.

Read-only requests retrieve and display existing state without creating another status record or conversation entry. They do not require durable recording merely to be handled. This qualifies the save-first rule above; viewing state is different from changing it.

SQL is the durable record for this conversation information and displayed state. Startup retrieves saved state through the service, then receives subsequent updates. Reconnection retrieves missed information; closing the CLI or losing its connection does not discard saved conversation history.

For Owner input, distinguish “sending” from “saved.” Do not imply the service has received and saved an answer until it confirms that recording succeeded.

This does not replace the authoritative versioned registration package in the project's GitHub repository. Registration decisions and responses still belong in that package as specified below. SQL schema, delivery mechanics, and the relationship between SQL records and package updates remain to be designed. Structured agent response formats have not yet been agreed.


## Draft project milestone — Usable multi-project CLI foundation

**Status:** Draft for Owner review, not a finalized milestone, implementation authorization, or completion claim. No identifier is assigned here; incorporate it into the project's sequential naming list when the milestone source is revised. This draft describes a project outcome, not development milestones or work packets.

**Purpose:** The Owner can use the installed `maestro` terminal application to connect to the real Python service, navigate multiple projects, read durable activity, and answer service-delivered questions without cross-project confusion or accidental work changes.

**Order:** Deliver this foundation before registration development. Registration later supplies its actual intake, source interpretation, agent reviews, package publication, confirmation, cancellation, and re-registration workflow through this CLI. The full eight-command list is an eventual capability list, not a claim that registration already works at foundation completion.

**Included:** The terminal workspace and local service connection; HTTP requests and streamed service updates; SQL-backed conversation and state access; project selection and attention; generic question, finding, and response handling; keyboard controls; empty and disconnected states; bounded terminal layout; reconnect and exit behavior. The service endpoints and durable recording needed to exercise these capabilities are included prerequisites, not assumed to exist.

**Excluded or deferred:** Command center; undecided mobile view; unsolicited agent conversations; draft retention across project switches; execution commands and a complete execution engine; actual registration review and package lifecycle, which belong to registration milestones. Agent-role definitions and Model Execution Adapters remain separate upcoming design work.

**Usage walkthrough:** Follow documented Linux service and CLI setup, including a documented way to create demonstration project and question records through the real service. Start the service separately, then launch `maestro`. Observe the connected project overview, select one project, read service-recorded messages and findings, answer a linked question, and receive acknowledgment only after SQL saving. Open another project's attention item without mixing records or controlling work. Disconnect and reconnect to recover missed updates, then exit without stopping service work.

### Draft acceptance and evidence

Every row requires observed behavior from the connected CLI and service, with records or captures sufficient to verify its stated boundary. These are proposed milestone criteria derived from the agreed CLI design, for Owner review.

| Capability | Required result and evidence |
|---|---|
| Install and connect | Document and exercise the Linux service and CLI setup, required configuration and access. Launch connects without starting the service. Show connecting, connected, and unavailable states, including retry. Record actual service/API connection evidence without secret values. |
| Project separation | Demonstrate at least two separately identified projects. Startup selects none; overview and attention selection focus the correct conversation without starting or stopping work. Show target validation, visible project identity, and no transferred drafts or answers. |
| Real durable information | Demonstrate service events and questions saved in SQL and delivered to the CLI, with source labels and consistent project references. Reads do not create replacement status records or conversation entries. Reopen and recover saved history and missed updates. Screens backed only by hardcoded sample data do not satisfy this criterion. |
| Answer lifecycle | Demonstrate choice-to-input, optional written clarification, explicit sending, save acknowledgment, “Answer received,” linked follow-up, stale-question rejection, and explicit retry without duplicate effects after lost acknowledgment. Ordinary text is limited to selected questions. |
| Reading and notifications | Demonstrate recent and earlier messages, inline findings, preserved reading and input context, the new-message indicator, and cross-project attention notices that do not pull focus automatically. |
| Controls and empty states | Demonstrate keyboard focus and navigation, multiline input and safe paste, exit warning, no-project and empty-result messages after successful reads, and visibly distinct retrieval failures. |
| Disconnection and size | Demonstrate retained but stale-marked display, unavailable service actions, local help/retry/exit, and reconnection without replay. Exercise the minimum terminal size chosen during implementation; resizing or CLI exit must not stop service work. |
| Honest capability boundary | Expose only implemented commands in help. Demonstrate the foundation's implemented command paths; registration-specific commands and activation/cancellation remain unavailable until their real process exists. Record their remaining delivery responsibility rather than demonstrating fabricated approval. |

### Draft definition of done

All foundation acceptance rows have connected evidence, and the Owner has reviewed the usable journey and any explicitly accepted limitations. Record the implementation revision, setup instructions, configuration references, service/SQL evidence, and any remaining registration dependencies. No essential connection may be left to an undocumented manual step.

Do not claim the foundation delivers registration. Registration milestones must demonstrate the full real CLI registration journey, including source selection, genuine agent reviews, version comparison, guarded confirmation/cancellation, stale-candidate rejection, and recovery of uncertain action outcomes. These are not optional because the foundation is delivered first.

Controlled demonstration inputs may exercise generic questions and events, but they must traverse the actual service, SQL, and CLI. Label them as demonstrations; they are not evidence that the pending agent roles, adapters, registration, or execution workflows exist.

### Remaining design and source alignment

Exact API endpoints, SQL/event schemas, duplicate-request mechanism, input limits, terminal dimensions, and the SQL-to-GitHub-package update relationship remain explicit design work. The draft does not select a UI toolkit, model provider, credential mechanism, or mobile implementation.

The [registration project milestone source](maestro-registration-project-milestones.md) predates the CLI-only decision and still needs its planned revision. Its both-interface requirements and placement of startup inside registration must not override this architecture. Finalizing that source follows Owner review of this foundation draft; retain existing item identities when revising it.

## Independent CLI fidelity review

**Result:** Passed for documentation fidelity. A separate read-only reviewer checked the visible CLI conversation, the prior architecture, and this proposed consolidation and foundation draft. This is not implementation verification, milestone completion, registration approval, or Owner acceptance of the new milestone.

**Baseline:** Architecture content blob `d91b623629def6d8f20183f65e5c690131b03ed9`. Repository working rules and additional agent instructions were read. The review covered retained decisions, newly agreed interactions, deferred scope, and whether the foundation's promised outcome could be demonstrated honestly.

| Conversation subject | Fidelity result |
|---|---|
| CLI foundation before registration; Python Linux service; multiple projects | Preserved. Initial scope remains CLI-only; command center excluded and mobile undecided. |
| Attributed project conversation and fixed input | Preserved. Current status is separate; unsolicited agent chats are excluded. |
| SQL-first durable records; HTTP and streamed updates | Preserved. Read-only requests do not create status/history duplicates. SQL does not replace the authoritative GitHub registration package. |
| Startup and connection | Preserved. No project selected at startup; launch does not start the service. Connection failures are not empty lists. |
| Project overview and targeting | Preserved. Attention-first ordering, selected versus working terminology, explicit targeting, and no guessing remain. |
| Attention and question choices | Preserved. Cross-project scope, linked answers, justified recommendations, tradeoffs, and free-text alternatives remain. |
| Eight starting commands | Preserved. Dropped shortcuts stay excluded; commands appear as implemented functionality becomes available. |
| Registration entry and portion selection | Preserved. Explicit repository, guide-readable milestone subjects, confirmed boundaries, duplicate prevention, and idle-only re-registration remain later registration integration. |
| Question-only ordinary text | Preserved. Written direction is linked to an existing question, not unrestricted agent conversation. |
| Unsent text | Preserved. Project switching clears it; draft retention and switch safeguard are deferred; exit warning remains. |
| Answer submission and clarification | Preserved. Choice fills input, explicit send, “Sending,” “Not sent,” “Answer received,” linked clarification, and duplicate-safe retry remain distinct from approval. |
| Inline findings and reports | Added faithfully. Context and reading position are preserved; viewing does not approve or resolve. |
| Scroll-follow and new messages | Added faithfully as initial behavior subject to practical feedback. |
| Other-project notice | Added faithfully. Names project and needed response without forced switching or input interruption. |
| Disconnection | Added faithfully. Visible stale data, blocked service submissions, local help/retry/exit, and reconnect without replay. |
| Recent history and empty states | Added faithfully. Earlier history remains accessible; empty results require successful lookup, and attention's empty result covers all projects. |
| Confirmation and cancellation | Added faithfully. Exact project/candidate or attempt, visible effects, no preselected submission, and deliberate focus. |
| Keyboard, multiline input, and terminal size | Added faithfully. Paste never sends; dimensions remain open. Mobile implementation is not selected. |
| Stale questions and candidates | Added faithfully. No answer rerouting or silent candidate substitution. The existing explicit choice to retain reviewed source is preserved. |
| Uncertain action outcome | Added faithfully. “Outcome not confirmed,” recorded-outcome lookup, no automatic replay, and duplicate-safe explicit retry. |

### Milestone review and limitations

The draft requires an actual CLI/service/SQL connection and a documented way to supply demonstration records. Controlled inputs prove that foundation only; they cannot establish completed agent reviews, registration, package publication, or execution. Registration-specific commands and actions must be delivered with their real workflow rather than exposed as fabricated completed functionality.

No material CLI agreement was found omitted or contradicted in the reviewed revision. The author clarified the Owner-input source as question-linked direction and made demonstration setup explicit. These are fidelity clarifications, not new workflow authority.

The separate registration milestone source remains stale: its reviewed content blob is `595a78dd3e92ca9f923c43def0ea315db2b52a7e`, and PM1 — Register and confirm a project through either interface still includes both-interface requirements and CLI prerequisites. That source is explicitly flagged for the next milestone revision, not approved by this review.

API/event/SQL formats, duplicate-request mechanics, the SQL-to-package relationship, and terminal dimensions remain open. The foundation milestone remains a draft for Owner review with no invented identifier. No source-code execution or operational capability was verified in this documentation review.

## Planning: evolving registration concepts

This section records agreed registration concepts and explicitly labeled proposals. The design can evolve through further agreement; it is not an instruction to implement the process.

### Maestro Planning Guide

A future Maestro Planning Guide will define the conventions and formats project architects use for their planning outputs so Maestro can understand and use them. The agreed input categories are below. The guide's detailed formats remain to be designed.

### Registration entry points and purpose

Planning begins with project registration through the Maestro CLI. A future command center will use the same service process. References to future command-center support do not make it a requirement for the initial version.

Registration would identify the project, confirm repository access, locate planning material, check compatibility with the guide, and present the result for confirmation. It checks whether Maestro can understand and work with the supplied plan; it does not approve the architecture or start development. Re-registration permits milestone additions and amendments as described below, not a general rewrite of the project's plan.

### Agreed registration inputs

Registration needs enough clear, consistent information to organize the work without inventing requirements. It does not require every implementation detail to be decided.

| Input | Required information and boundary |
|---|---|
| Project identity | Plain project name, repository location, and responsible project architect: a person, an agent, or both. Maestro checks that the repository is readable and belongs to the intended project. |
| Purpose and scope | What the project should accomplish, what is included in the work being registered, and what is explicitly excluded. |
| Architecture | Major components and their responsibilities, interactions, and decided technical choices and constraints. Distinguish settled decisions from details left open. Enough structure is needed to organize work without inventing architectural decisions, not a fully detailed design. |
| Current state | Whether the project is new or already under development; what exists and is considered complete; what is unfinished, partially working, or known to be broken. Distinguish reported status from verified facts and flag conflicting status information. Registration does not require a full code audit. |
| Planned work | Desired features or outcomes, relative priorities, and known dependencies or required ordering. Planning uses the shared milestone model below. |
| Acceptance and completion | Explicit project-level acceptance criteria and definitions of done. Development-level criteria and completion requirements are created in the next process after registration. |
| Document locations and format | Identify authoritative planning documents and format their contents according to the Maestro Planning Guide so Maestro can find and interpret them consistently. |

### Shared planning and milestones

Planning is shared between the project architect and the Maestro architect, similar to the collaborative process used to design Maestro itself.

| Perspective | Milestone meaning and responsibility |
|---|---|
| Project architect | Defines meaningful project outcomes and delivery boundaries. A project milestone can represent a usable capability, release, or architectural foundation. |
| Maestro architect | In the next process after registration, organizes the work into manageable development milestones that contribute to those project outcomes. |

Registration retains the supplied project milestones without breaking them into development milestones or work packets. That breakdown belongs to the next process after registration.

When the breakdown is performed, project milestones and development milestones are explicitly linked; they do not need a one-to-one relationship. One project milestone can contain several development milestones. Maestro must not quietly redefine a project outcome or release boundary when organizing development.

### Planning identifiers, names, and versions

Registration establishes a consistent naming scheme for planning items. This concerns planning identifiers and subjects, not source-code conventions, which remain part of Execution.

Use a short item-type prefix, a sequential number, and a plain subject. Always display the subject alongside the identifier; never refer to a coded item by its identifier alone.

| Item type | Example |
|---|---|
| Project milestone | PM1 — First usable release · version 2 |
| Development milestone | DM1 — Project registration · version 3 |
| Planning document | PD1 — API contract · version 2 |
| Work packet | WP1 — Implement registration input checks · version 1 |
| Review | RV1 — Registration findings fidelity review · round 1 |
| Replan | RP1 — Revise registration delivery sequence |

These are naming examples, not actual project records.

Numbers are assigned sequentially within each item type for each project. Agents must not invent numbers. No random numbering, reused identifiers, or unexplained numbering jumps are permitted. Retired identifiers are never reused.

Keep identity separate from version:

- An item keeps its identifier when its title or content changes.
- Versions increase sequentially only when that item changes; preserve earlier versions.
- Each work packet has its own identifier and an explicit link to its development milestone.
- Reviews record the exact item versions reviewed. Review rounds are separate from document versions.
- Replans record why the plan changed and which items were added or revised. Unchanged items keep their identifiers and versions.

Store relationships explicitly rather than encoding the full hierarchy into names. Moving a work packet between milestones does not require a new identifier.

Maintain one naming-convention list that the Owner can extend with new item types and prefixes as the project develops. The initial list does not need to cover everything.

### Acceptance criteria and definition of done

The project architect defines what makes each project milestone successful. In the next process after registration, the Maestro architect develops detailed criteria for development milestones, traceable to project criteria without adding requirements.

Each acceptance criterion states:

- Expected result: what must happen and under which conditions.
- Verification: how it will be checked and what evidence is required.
- Pass boundary: the exact result or threshold that counts as success.
- Exceptions: explicitly accepted limitations.

Acceptance criteria state what must be true. The definition of done states everything required to declare the milestone complete, including required reviews and evidence. Passing acceptance criteria is not enough if other completion requirements remain unmet. Development milestones must support, not weaken, the project milestone's definition of done.

During registration, only ambiguity affecting the work or its acceptance blocks registration; optional improvements do not. If the later milestone breakdown exposes ambiguity, Maestro returns it for clarification rather than silently choosing an interpretation.

### Working rules belong to Execution

Change boundaries, decision authority, repository rules, and coding conventions belong in the Execution phase, not the required registration inputs.

Project-specific overrides of execution rules are a future possibility only. They are not being designed or required for registration now.

### Proposed registration process

| Step | Proposed mechanism |
|---|---|
| Receive the request | The Owner supplies the repository location and selects the whole plan or a defined portion through the Maestro CLI. If registration is already active, show its status instead of starting another. |
| Identify the project and confirm access | Python records the project name, repository, and responsible project architect, checks read access and that the repository belongs to the intended project, and reports missing permissions. |
| Read a specific version | Python reads the repository at a recorded Git commit shared by both reviewers. Relevant source changes are flagged for an explicit Owner choice before confirmation. |
| Locate planning inputs | The guide could require a small registration file listing project details and the locations of authoritative planning documents. Working rules belong to Execution, not registration. |
| Check format and completeness | Python checks required fields, file locations, document structure, and references against the guide. |
| Check meaning and consistency | The Maestro architect reviews milestone purpose and scope, outside dependencies, and claimed existing capabilities through targeted source checks. It reports unclear instructions, contradictions, missing essentials, and the level of supporting evidence. |
| Independently review the findings | A separate reviewer checks fidelity to the project's source material and whether blockers are justified. The Maestro architect can amend its report; rechecks cover affected findings only, within the configured review limit. |
| Present the registration report | Maestro combines the findings into a plain summary of what was found, what needs attention, and whether the project is ready to register. Issues point to the relevant file and passage where available. |
| Resolve issues and confirm | The project architect supplies needed source corrections. Maestro rechecks affected findings within the configured review limit. When no blockers or unresolved disagreements remain, the Owner confirms the versioned registration package through the Maestro CLI, making it active. Non-blocking findings do not prevent registration. |

The Maestro architect may amend its own findings report. During re-registration, it can add or amend project milestones within the reviewed registration package, but development-milestone and work-packet breakdown remains in the next process. This does not authorize it to resolve source-plan contradictions, invent missing answers, or otherwise rewrite the project's plan. The project architect supplies source corrections. The registration-file format remains subject to design.

### Registration outputs and final confirmation

Successful registration produces one versioned package:

| Output | Contents |
|---|---|
| Registration summary | Project identity, source documents and their reviewed versions, findings, and registration outcome. |
| Project milestone outline | Supplied project milestones with purposes, scope, priorities, and dependencies, without development-milestone or work-packet breakdown. |
| Project-level completion requirements | Acceptance criteria, definitions of done, usage walkthroughs, and required completion evidence. |
| Review record | Architect findings, independent fidelity reviews, amendments, retained non-blocking findings, and linked Owner decisions, clarifications, and accepted limitations. |

The package identifies the exact versions of its contents rather than relying on whichever files happen to be latest.

The Owner gives final confirmation through the Maestro CLI. Confirmation accepts the registration package and activates that registration version; it does not start development.

### Machine-first package storage

Store the registration package in the project's own GitHub repository, with a separate folder for each registration version. The Maestro Planning Guide defines the folder location and consistent filenames.

Optimize the package for agents and Python:

- Structured JSON is authoritative, with a defined schema.
- A small index identifies records, registration and source versions, and relationships through explicit references and relative links.
- Use small, focused files so agents load only what they need.
- Keep plain-language descriptions inside the structured records.
- Python validates required fields and references.

Each fact has one authoritative location. The CLI presents the same package; human-readable reports are generated from it, not maintained as competing sources of truth. The future command center will also render these records. The next planning process uses the exact confirmed package version.

### Source changes during review

Each review uses an exact Git commit. The Maestro architect and independent fidelity reviewer use the same source version.

If relevant planning inputs change, Maestro flags that the reviewed version is no longer current and shows the changes before confirmation. It does not silently mix source versions.

| Owner choice | Treatment |
|---|---|
| Finish with the reviewed source version | Registration explicitly covers the original requirements. Newer changes are not included. |
| Include the updated source version | Update the candidate package and recheck affected findings within the existing review limit. Do not silently reset the two-round limit. |

This applies to changes in planning inputs, not unrelated commits or the registration reports themselves.

### Duplicate registration requests

Only one registration process may be active per project. A second request through the CLI, or a future command-center request, shows the existing process's current status rather than starting a competing process or creating another version.

### Registration visibility and Owner responses

The Maestro CLI shows:

- The current step and working agent.
- The review round and configured limit.
- Blockers, non-blocking findings, and technical failures.
- Whether registration is progressing, paused, or waiting for the Owner.
- Decisions needed from the Owner and the relevant findings.

A decision request provides a specific question, relevant findings, and the affected registration version. The Owner submits a choice or written clarification through the Maestro CLI.

Maestro records the response against that request in the registration package. The runtime routes it to the paused step; the architect amends its report if needed, and affected findings are rechecked within the existing review limit.

If a response is ambiguous, Maestro asks for clarification rather than treating it as approval. Answering a question is not final registration confirmation; confirmation remains a separate explicit action.

### Changes presented for confirmation

Before re-registration confirmation, compare the candidate package with the active registration version. Show:

- What was added, changed, or removed.
- Affected project milestones, scope boundaries, and completion requirements.
- Why each change was made, with links to findings or Owner decisions.

The Owner confirms the exact candidate version shown. That confirmed package must not silently change afterward.

### Partial-project registration

Through the Maestro CLI, the Owner chooses the whole supplied project plan or specific project milestones.

The candidate package records included milestones and outcomes, explicit exclusions, and dependencies outside that boundary. If only part of a milestone is included, describe that portion explicitly; an identifier alone is insufficient.

The Maestro architect checks whether outside dependencies already exist or need additional work. Present boundaries and dependencies before confirmation. Successful registration covers only the selected portion, not the whole project.

For example, registering menu creation and publishing could exclude billing. If publishing requires authentication, authentication must already exist, be included, or be identified as missing essential work. Maestro raises the dependency for a decision rather than silently expanding scope.

### Targeted source checks for dependencies

Registration includes targeted source-code inspection of dependencies claimed to exist, not a full code audit.

For an authentication dependency, inspect whether it is connected to the relevant application or API, protects the required routes, depends on missing configuration or credentials or unfinished components, and has evidence of working.

The report distinguishes:

| Evidence level | Meaning |
|---|---|
| Reported to exist | Claimed in supplied information, without verification. |
| Supported by source inspection | The implementation appears present and connected based on source evidence. |
| Verified in operation | Operational evidence supports that it works. |

Source inspection alone does not prove running-system behavior. Anything not verified remains explicit.

### Retained Owner decisions

Include Owner clarifications, accepted limitations, and scope decisions in the registration package, linked to their decision requests where applicable and to affected milestones and criteria. Later agents use these recorded decisions rather than reconstructing them from chat.

### Registration review loop

Registration has its own bounded loop:

1. Python checks the inputs.
2. The Maestro architect examines the source material, checks milestone purpose and scope through a usage walkthrough, and produces findings.
3. An independent fidelity reviewer checks those findings against the source material and assesses whether blockers are justified.
4. The Maestro architect amends its report if needed.
5. Any further review checks affected findings only.

The loop ends with readiness for registration confirmation, specific blockers returned to the project architect, or unresolved disagreement brought to the Owner. It must not become an endless search for reasons to fail registration.

### Milestone purpose and scope review

Registration review checks whether each supplied project milestone's scope is sufficient to deliver its stated purpose, not merely whether its description is clear. This review does not break milestones into development milestones or work packets. Completing a task list does not prove the promised capability works.

| When | Required check |
|---|---|
| During registration review, before work starts | Walk through how someone will actually use the capability. Identify the prerequisites and connections needed for that journey. Confirm that each already exists or is included in the planned work and its dependencies. |
| Before declaring the milestone complete | Demonstrate the same journey using the actual connected system. Completed components or test-data demonstrations alone do not prove an operational capability. |

The Maestro architect records the usage walkthrough, prerequisites, and required completion evidence in the milestone's acceptance criteria and definition of done. The independent fidelity reviewer checks that these support the stated purpose and that any missing essentials are justified findings. This is part of the existing registration review loop, with the same configurable two-round limit, not an additional review loop.

For a control-loop milestone, the walkthrough would cover how the service is started, how it authenticates, how a project becomes available to it, how work is initiated, and how the result is observed. These are examples of essential operations to examine, not a requirement that every milestone deliver a whole product.

A component milestone is valid, but it must be named and judged as a component. It must not be reported as a working end-to-end capability.

An exclusion cannot remove something essential to the milestone's purpose while leaving its completion claim unchanged. Include the missing work or explicitly narrow the milestone with the Owner; do not silently weaken its purpose or definition of done.

Registration checks the planned path to a usable outcome. It does not require the capability to be built already. Optional improvements remain non-blocking; a missing essential must be tied to the stated purpose, not a reviewer's preference.

### Good enough to proceed

| Finding | Treatment |
|---|---|
| Blocker | Missing or contradictory information that prevents Maestro from understanding the work or following its rules safely. Explain what Maestro cannot do because of it, with source evidence or an identified missing required input. |
| Non-blocking finding | Wording preferences, improvements, or minor gaps that do not prevent registration. Report them without requiring correction. |
| Review disagreement | Allow the Maestro architect to amend its report. If disagreement remains at the review limit, bring it to the Owner. |

Independent fidelity review checks accuracy and justified blockers; it must not introduce new requirements. “This could be better” is not grounds for failure.

### Configurable planning review limit

A configuration file will set the maximum planning review rounds. The agreed initial limit is **2 rounds**, configurable:

1. Initial Maestro architect report and independent fidelity review.
2. Amended report and independent recheck of affected findings, only if needed.

One round means an architect report followed by an independent fidelity review. Sending an amended report for review counts as the next round. Registration can pass after the first round.

At the limit, unresolved blockers or disagreements pause the registration and go to the Owner. The limit does not force approval or trigger another automatic retry. Configuration-file location and format are not specified here.

### Re-registration and registration versions

Registration may be rerun at any point in a project's lifecycle, but only when no work is in progress on that project. All active project work must finish or be explicitly stopped first. Maestro prevents new project work from starting until re-registration ends.

Each rerun creates the next registration version: registration version 2, then registration version 3, and so on. Previous registration versions are preserved rather than overwritten.

During re-registration, the Maestro architect can add project milestones or amend existing project milestones; it does not perform the subsequent development breakdown. These changes are included in the new registration version and go through the same independent fidelity-review loop.

The same configurable planning review limit applies, initially two rounds. Non-blocking findings do not prevent registration; unresolved blockers or disagreements at the limit go to the Owner.

### Failed or interrupted registration

Preserve completed reports and review results. After an agent crash, failed push, or service restart, resume from the last verified step.

Technical failures do not consume planning review rounds. Technical retries have a separate configurable limit. Reaching that limit pauses registration and alerts the Owner. The technical retry limit has no agreed numeric value yet.

### Registration version activation

A new registration version remains a candidate until the Owner confirms it. Confirmation makes it active while preserving the previous version.

If re-registration fails or is cancelled, the previous registration version remains active. Project work does not automatically restart.

### Agent delegation wrapper

The runtime delegates to an agent through a wrapper script that launches the agent and performs deterministic checks around its work.

For tasks requiring GitHub commits, the wrapper verifies:

- The expected repository and branch were used.
- Required changes were committed and pushed.
- The commit exists on GitHub.
- Only permitted files changed.
- The agent's reported commit matches the actual commit.

These checks apply when commits are required; a read-only review does not require a commit merely to satisfy the wrapper.

The wrapper verifies observable facts. The independent reviewer checks meaning and fidelity. An agent's statement that it committed successfully is not verification, and passing wrapper checks is not independent approval.
