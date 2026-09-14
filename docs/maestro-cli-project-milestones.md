# CLI — Command-line Interface Milestone Declaration

## Declaration identity

| Field | Value |
|---|---|
| Project | Maestro |
| Declaration | CLI — Command-line interface |
| Declaration version | 10 |
| Status | Proposed outcomes; no recorded implementation completion |
| Architecture source | `docs/maestro-architecture.md` |

## Capability and scope

The declaration delivers a usable local terminal workspace and reliable question-linked responses through the actual Python service and SQL records. The [Runtime Service declaration](maestro-runtime-service-project-milestones.md) owns service installation, API implementation, server-side storage and request handling, and agent supervision. This declaration owns the terminal client and its interaction with those capabilities. The [project overview](maestro-project-overview.md) identifies current-state evidence.

Command center, mobile presentation, unsolicited agent conversation, cross-project draft retention, execution commands, and a complete execution engine are outside this declaration. Registration-specific intake and package actions are delivered through the [registration declaration](maestro-registration-project-milestones.md). Architecture-loop entry, progress, review, and confirmation actions are delivered through the [architecture-loop declaration](maestro-architecture-loop-project-milestones.md), using this terminal foundation. Its unresolved command contracts do not change the defined registration commands.

Verification follows `docs/planning-guide/README.md#verification-expectations`: real data and connected operation, a basic main journey and essential failures, and no exhaustive outcome-by-outcome test suite. Evidence can cover several criteria in one journey. Fake data is used only when necessary with the reason recorded; it cannot prove real registration or agent integration.

### Development order and connected acceptance

Runtime foundation, storage, and API implementation support CLI development; CLI implementation precedes registration development. An installed CLI and empty service are usable for foundation checks. Full connected acceptance of CLI-PM1 — Connected multi-project CLI workspace and CLI-PM2 — Reliable project questions and answers is completed alongside REG-PM1 — Register and confirm a project through the CLI, using real registration-created projects and questions. Registration development depends on the implemented CLI interfaces, not prior final acceptance of the integrated CLI journeys. A temporary generator is not a delivery prerequisite.

## Milestones and order

| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |
|---|---|---|---|
| 1 | CLI-PM1 — Connected multi-project CLI workspace | 6 | `docs/maestro-cli-project-milestones.md#cli-pm1--connected-multi-project-cli-workspace` |
| 2 | CLI-PM2 — Reliable project questions and answers | 5 | `docs/maestro-cli-project-milestones.md#cli-pm2--reliable-project-questions-and-answers` |

## CLI-PM1 — Connected multi-project CLI workspace

**Outcome:** A usable read-only terminal view of real service-held project activity, conversations, findings, and attention.

**Included:** CLI installation and connection configuration, HTTP client reads, receiving streamed updates, presentation of saved service records, project navigation, reading controls, keyboard and size handling, empty/failure states, reconnect, and exit.

**Excluded:** Service installation, server API/SQL implementation, answer submission, and actual registration. A read-only workspace is not a completed registration interface.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Open and use the workspace | `docs/maestro-architecture.md#open-and-use-the-workspace` |
| Component and runtime boundaries | `docs/maestro-architecture.md#components-and-responsibilities` |
| Actual deployment and connection | `docs/maestro-architecture.md#runtime-and-prerequisites` |
| Record ownership and live delivery | `docs/maestro-architecture.md#connections-and-data` |
| Activity selection and labels | `docs/maestro-architecture.md#project-activities-and-registration-labels` |
| Request and event formats | `docs/maestro-architecture.md#cli-request-and-event-contract` |
| Detailed CLI behavior | `docs/maestro-architecture.md#cli-workspace` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Running service and readable project/event records | SVC-PM1 — Operate the persistent Maestro service; SVC-PM2 — Preserve project activity and requests; SVC-PM3 — Connect the CLI to recorded service activity | Runtime Service owns server installation, API, SQL, and event delivery. Implemented interfaces support CLI development; final connected evidence is shared, not a prerequisite loop. |
| Real project and question records | REG-PM1 — Register and confirm a project through the CLI | Registration supplies records for final connected acceptance; foundation development supports an empty service. |
| Existing component evidence | `docs/maestro-project-overview.md#current-state` | Earlier source observations are not proof of current integrated operation. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| The CLI is installed and the runtime service is available | CLI instructions install the terminal client and its connection configuration. `maestro` connects to the existing service without starting it. Service account, systemd startup, and crash-restart delivery belong to SVC-PM1 — Operate the persistent Maestro service. | CLI installation and connection results, installed revision, and runtime prerequisite evidence without secret values. | None |
| Startup succeeds or connection fails | The overview starts with visible “No project selected,” even with one project. Connecting, connected, unavailable, and retry behavior are distinguishable. A failed lookup is not an empty list. | Connected and unavailable journeys, including configuration fallback, unreachable valid address, and successful retry after rereading configuration without reopening the CLI. | None |
| Multiple projects are present | The overview orders attention-needed, working, then idle projects. Selection opens the correct conversation without changing work. Project names and record associations remain distinct. | At least two separately identified service-held projects, their before/after state, and selection captures. | None |
| Messages and state change | Actual service/SQL records feed HTTP reads and streamed updates. Messages identify their source; read-only requests create no duplicate status or conversation records. | Correlated API, SQL, and displayed records; service-generated updates for both projects. Hardcoded terminal sample data is insufficient. | None |
| Earlier content or findings are opened | Recent history and Load earlier messages work while current activity or waiting state and pending questions remain accessible. Details within the same activity expand inline, preserve the selected project and question linked to input, and restore reading position when closed. Viewing does not acknowledge or resolve a finding. At the bottom, messages follow; above it, New messages appears without pulling the reading position. | Captures of each state and unchanged finding/process state after viewing. | None |
| Another project needs attention | The notice names the project and required response or action without switching focus. The attention list covers all projects. A question entry opens its exact project/activity/question with answer-linked input; a recovery entry opens its project/activity, failure explanation, and available action with commands-only conversation input. Viewing never performs the action. | Notice while another project is selected, followed by explicit navigation to the correct record. Recovery-action routing uses REG-PM3 — Recover registration without losing decisions or exceeding limits for connected evidence and is outside this milestone's initial-registration acceptance. | None |
| A successful lookup contains no results | Correct empty messages appear for projects, attention, and findings. Retrieval failure and missing context remain distinct. Registration-specific empty actions are completed with registration integration. | Actual empty-query and failed-query observations, with current context identified. | None |
| The connection drops during use | Visible content remains marked disconnected and potentially stale. Service actions are unavailable; local help, retry, and exit remain. Automatic reconnect follows the documented delay schedule; explicit retry attempts immediately. Reconnect retrieves recorded changes without replaying earlier submissions. | Disconnect/reconnect record and uninterrupted independent service activity. | None |
| Keyboard or terminal size changes | Visible focus, Tab/Shift+Tab, arrows, Enter activation, and Escape behave as specified. Below the chosen minimum size, the enlargement message appears while service work continues. | Recorded terminal dimensions and keyboard-only walkthrough. | None |
| Commands are invoked | Help, projects, attention, findings, retry, and exit work within this milestone's read-only scope. Help documents actual syntax and context requirements, excludes unimplemented commands, and works offline. | Each command exercised against its real path; exit leaves service work and saved records available. | None |
| Project activities and registration states are displayed | Opening a project selects its single current activity, offers selection when several are underway, or shows the latest ended activity with Idle. Waiting remains current. Registration labels and attention targeting follow the architecture; unapproved attempts remain accessible. | Real initial registration attempts demonstrate current, waiting, ended, and historical views, with correct input context. The Updating registration label is verified with REG-PM2 — Update a registration without losing approved history and is outside this milestone's initial-registration acceptance. Multiple concurrent activity selection may use a necessary isolated check until another activity type exists; it does not prove execution. | None |

### Definition of done

The main connected journey and essential failure cases provide evidence for all criteria using the installed CLI, service, and SQL. Setup is reproducible; registration supplies real project/event records without hidden manual database edits. The implementation revision, instructions, actual observations, and required implementation review evidence are available.

Final evidence uses actual registration activity. Basic isolated checks can precede integration, but generated records do not complete connected acceptance.

### Unresolved details

No additional CLI behavior decision is required for these criteria. Registration role and package contracts remain dependencies of connected acceptance.

## CLI-PM2 — Reliable project questions and answers

**Outcome:** An explicit answer reaches the correct question and process, is saved before acknowledgment, and cannot silently become approval or a duplicate effect.

**Included:** Question rendering, recommendations and alternatives, linked text/choice input, multiline behavior, client context checks, request submission, displaying saved receipts and clarification, stale-question handling, explicit retry, and unsent-input handling. Runtime Service owns server validation, SQL saving, deduplication, and durable delivery; registration owns question meaning and process eligibility.

**Excluded:** Unsolicited agent conversations and actual registration assessment or activation. Generic response transport does not establish agent judgment.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Answer a project question | `docs/maestro-architecture.md#answer-a-project-question` |
| Input and receipt rules | `docs/maestro-architecture.md#questions-and-answers` |
| Project targeting | `docs/maestro-architecture.md#projects-and-targeting` |
| Save before acknowledgment | `docs/maestro-architecture.md#save-and-delivery-sequence` |
| Answer identity and reconciliation | `docs/maestro-architecture.md#answer-identity-and-uncertain-delivery` |
| Keyboard and paste | `docs/maestro-architecture.md#keyboard-and-terminal-behavior` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Connected workspace | CLI-PM1 — Connected multi-project CLI workspace | Workspace implementation precedes answer handling; their final connected acceptance is shared with initial registration integration. |
| Real question producer and consuming activity | REG-PM1 — Register and confirm a project through the CLI | Registration supplies actual questions and consumes answers for shared connected acceptance. |
| Question identity, request identity, and durable delivery | SVC-PM2 — Preserve project activity and requests; SVC-PM3 — Connect the CLI to recorded service activity | Runtime Service implements the server contracts; the CLI implements their client interaction. Registration provides process-specific eligibility. Shared evidence verifies the connection. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| A question requests a choice or information | Clear alternatives include a justified recommendation where appropriate, tradeoffs, and a written alternative. Information requests allow writing without forced choices. | Actual service-delivered examples of both question types; no hardcoded display-only questions. | None |
| Input has or lacks a selected question | Project or registration context, requester, and question are visible. Ordinary text is accepted only for that question; otherwise input is commands-only. Missing, unknown, conflicting, or ambiguous project targets cannot execute by guessing. | Submitted context and service validation results, including rejection of an invalid target. | None |
| A choice is activated | The choice fills the input without submission. Optional text can be added. Send or Enter submits explicitly. | No service submission on choice selection; one submission after explicit send. | None |
| A long answer is entered | Shift+Enter adds a line; multiline paste does not submit. The input grows to its documented limit then scrolls internally. | Keyboard and paste walkthrough with preserved question/conversation visibility. | None |
| An answer is submitted | Commands and answers can be submitted while streamed updates arrive without changing their target or disrupting input. Sending remains until the service confirms SQL saving. The saved answer appears in the conversation, input clears, and the question shows Answer received rather than Resolved. | Request, saved record, acknowledgment, and displayed state linked to the same question. | None |
| Clarification is required | The service/process receives the recorded answer. A specific follow-up explains the missing information, links the original question and answer, and sets the new input context. It does not count as registration confirmation. | Response routing record, follow-up, original answer, and unchanged approval state. | None |
| Sending fails or acknowledgment is lost | Not sent and a plain reason appear; uncertain delivery includes the agreed explanation. The current input retains the answer for explicit retry. Reconnection alone never resubmits. A repeated submission cannot record or act twice. Edited text waits for reconciliation of the original request and cannot replace an accepted answer. | Lost-acknowledgment observation with one durable answer and one process effect after explicit retry. | None |
| The question has been replaced or its process cancelled | The original question's eligibility is checked before acceptance. The reason is shown, no answer is applied elsewhere, and an available replacement is offered without transferring text. | Stale-question submission and unaffected replacement record. | None |
| Projects are switched or the CLI exits | Switching projects or activities clears unsent text without saving, transfer, or warning. Activity switching selects commands-only input until a question is explicitly opened. Exit warns about unsent text. Saved records remain retrievable after reopening; startup again selects no project. | Before/after input and record observations for switch, exit, and reopen. | None |

### Definition of done

The connected answer journey and essential failure cases establish the criteria, including lost acknowledgment and stale-question rejection, without an exhaustive test matrix. Evidence links submission, saved record, receipt, and process effect to the same question. The preceding workspace remains usable.

Question creation and response consumption use actual registration, service, and SQL. Final acceptance is shared with registration integration; isolated transport checks alone do not complete this outcome.

### Unresolved details

No additional CLI behavior decision is required for these criteria. Registration role and package contracts remain dependencies of connected acceptance.

## Partial-registration boundary

No narrower portion is declared. Any selected subset requires explicit scope, outside dependencies, relevant journey references, and acceptance coverage before registration confirmation.
