# CLI — Command-line Interface Milestone Declaration

## Declaration identity

| Field | Value |
|---|---|
| Project | Maestro |
| Declaration | CLI — Command-line interface |
| Declaration version | 6 |
| Status | Proposed outcomes; no recorded implementation completion |
| Architecture source | `docs/maestro-architecture.md` |

## Capability and scope

The declaration delivers a usable local terminal workspace and reliable question-linked responses through the actual Python service and SQL records. The [project overview](maestro-project-overview.md) identifies current-state evidence.

Command center, mobile presentation, unsolicited agent conversation, cross-project draft retention, execution commands, and a complete execution engine are outside this declaration. Registration-specific intake and package actions are delivered through the [registration declaration](maestro-registration-project-milestones.md).

Verification follows `docs/planning-guide/README.md#verification-expectations`: real data and connected operation, a basic main journey and essential failures, and no exhaustive outcome-by-outcome test suite. Evidence can cover several criteria in one journey. Fake data is used only when necessary with the reason recorded; it cannot prove real registration or agent integration.

## Milestones and order

| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |
|---|---|---|---|
| 1 | CLI-PM1 — Connected multi-project CLI workspace | 3 | `docs/maestro-cli-project-milestones.md#cli-pm1--connected-multi-project-cli-workspace` |
| 2 | CLI-PM2 — Reliable project questions and answers | 3 | `docs/maestro-cli-project-milestones.md#cli-pm2--reliable-project-questions-and-answers` |

## CLI-PM1 — Connected multi-project CLI workspace

**Outcome:** A usable read-only terminal view of real service-held project activity, conversations, findings, and attention.

**Included:** Installed CLI, Linux service connection and necessary setup, HTTP reads, streamed updates, SQL records, project navigation, reading controls, keyboard and size handling, empty/failure states, reconnect, and exit.

**Excluded:** Answer submission and actual registration. A read-only workspace is not a completed registration interface.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Open and use the workspace | `docs/maestro-architecture.md#open-and-use-the-workspace` |
| Component and runtime boundaries | `docs/maestro-architecture.md#components-and-responsibilities` |
| Actual deployment and connection | `docs/maestro-architecture.md#runtime-and-prerequisites` |
| Record ownership and live delivery | `docs/maestro-architecture.md#connections-and-data` |
| Detailed CLI behavior | `docs/maestro-architecture.md#cli-workspace` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Running service and readable project/event records | `docs/maestro-architecture.md#runtime-and-prerequisites` | Operational readiness unknown; required service/API/SQL setup is included in this milestone. |
| Record provisioning before registration exists | `docs/maestro-architecture.md#constraints-and-unresolved-details` | Mechanism unresolved; a usable source must be defined before affected implementation. |
| Existing component evidence | `docs/maestro-project-overview.md#current-state` | Earlier source observations are not proof of current integrated operation. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Service and CLI are installed using documented instructions | The Python service runs under `systemd`; boot start and crash restart are demonstrated. `maestro` connects to the existing service without starting it. Required configuration and access are documented. | Commands used, installed revision, service state, connection results, and configuration references without secret values. | None |
| Startup succeeds or connection fails | The overview starts with visible “No project selected,” even with one project. Connecting, connected, unavailable, and retry behavior are distinguishable. A failed lookup is not an empty list. | Connected and unavailable journeys, including successful retry without reopening the CLI. | None |
| Multiple projects are present | The overview orders attention-needed, working, then idle projects. Selection opens the correct conversation without changing work. Project names and record associations remain distinct. | At least two separately identified service-held projects, their before/after state, and selection captures. | None |
| Messages and state change | Actual service/SQL records feed HTTP reads and streamed updates. Messages identify their source; read-only requests create no duplicate status or conversation records. | Correlated API, SQL, and displayed records; service-generated updates for both projects. Hardcoded terminal sample data is insufficient. | None |
| Earlier content or findings are opened | Recent history and Load earlier messages work while current activity or waiting state and pending questions remain accessible. Details expand inline, preserve the selected project and question linked to input, and restore reading position when closed. Viewing does not acknowledge or resolve a finding. At the bottom, messages follow; above it, New messages appears without pulling the reading position. | Captures of each state and unchanged finding/process state after viewing. | None |
| Another project needs attention | The notice names the project and required response without switching focus. The attention list covers all projects; selecting an entry opens its project and question. | Notice while another project is selected, followed by explicit navigation to the correct record. | None |
| A successful lookup contains no results | Correct empty messages appear for projects, attention, and findings. Retrieval failure and missing context remain distinct. Registration-specific empty actions are completed with registration integration. | Actual empty-query and failed-query observations, with current context identified. | None |
| The connection drops during use | Visible content remains marked disconnected and potentially stale. Service actions are unavailable; local help, retry, and exit remain. Reconnect retrieves recorded changes without replaying earlier submissions. | Disconnect/reconnect record and uninterrupted independent service activity. | None |
| Keyboard or terminal size changes | Visible focus, Tab/Shift+Tab, arrows, Enter activation, and Escape behave as specified. Below the chosen minimum size, the enlargement message appears while service work continues. | Recorded terminal dimensions and keyboard-only walkthrough. | None |
| Commands are invoked | Help, projects, attention, findings, retry, and exit work within this milestone's read-only scope. Help documents actual syntax and context requirements, excludes unimplemented commands, and works offline. | Each command exercised against its real path; exit leaves service work and saved records available. | None |

### Definition of done

The main connected journey and essential failure cases provide evidence for all criteria using the installed CLI, service, and SQL. Setup and project/event provisioning are reproducible without hidden manual database edits. The implementation revision, instructions, actual observations, and required implementation review evidence are available.

Real service activity is preferred. If controlled data is necessary before registration exists, the reason and limit are explicit; only the workspace connection is demonstrated. It cannot establish agent reasoning, registration, or execution completion. No accepted limitation removes the usable-workspace outcome.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Initial records and process selection | The entry to project views and the meaning of current process are not complete. | Resolve the corresponding items in `docs/maestro-architecture.md#constraints-and-unresolved-details`. |
| API/SQL/event contracts and setup | Connections cannot be built from assumed formats or access. | Specify contracts and reproducible setup before implementation. |
| Terminal choices | Dimensions, input limits, and detailed argument behavior need practical definition. | Record choices against the architectural behavior before completion. |

## CLI-PM2 — Reliable project questions and answers

**Outcome:** An explicit answer reaches the correct question and process, is saved before acknowledgment, and cannot silently become approval or a duplicate effect.

**Included:** Question rendering, recommendations and alternatives, linked text/choice input, multiline behavior, context validation, SQL recording, routing, receipt, clarification, stale-question handling, explicit retry, and unsent-input handling.

**Excluded:** Unsolicited agent conversations and actual registration assessment or activation. Generic response transport does not establish agent judgment.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Answer a project question | `docs/maestro-architecture.md#answer-a-project-question` |
| Input and receipt rules | `docs/maestro-architecture.md#questions-and-answers` |
| Project targeting | `docs/maestro-architecture.md#projects-and-targeting` |
| Save before acknowledgment | `docs/maestro-architecture.md#save-and-delivery-sequence` |
| Keyboard and paste | `docs/maestro-architecture.md#keyboard-and-terminal-behavior` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Connected workspace | CLI-PM1 — Connected multi-project CLI workspace | Required preceding outcome, not yet claimed complete. |
| Supported question producer and consuming process | `docs/maestro-architecture.md#constraints-and-unresolved-details` | Unresolved before registration exists; required generic service-side path is included here. |
| Question identity, request identity, and durable delivery | `docs/maestro-architecture.md#questions-and-answers` | Required behavior is defined; technical contracts and duplicate-recognition mechanism remain unspecified. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| A question requests a choice or information | Clear alternatives include a justified recommendation where appropriate, tradeoffs, and a written alternative. Information requests allow writing without forced choices. | Actual service-delivered examples of both question types; no hardcoded display-only questions. | None |
| Input has or lacks a selected question | Project or registration context, requester, and question are visible. Ordinary text is accepted only for that question; otherwise input is commands-only. Missing, unknown, conflicting, or ambiguous project targets cannot execute by guessing. | Submitted context and service validation results, including rejection of an invalid target. | None |
| A choice is activated | The choice fills the input without submission. Optional text can be added. Send or Enter submits explicitly. | No service submission on choice selection; one submission after explicit send. | None |
| A long answer is entered | Shift+Enter adds a line; multiline paste does not submit. The input grows to its documented limit then scrolls internally. | Keyboard and paste walkthrough with preserved question/conversation visibility. | None |
| An answer is submitted | Commands and answers can be submitted while streamed updates arrive without changing their target or disrupting input. Sending remains until the service confirms SQL saving. The saved answer appears in the conversation, input clears, and the question shows Answer received rather than Resolved. | Request, saved record, acknowledgment, and displayed state linked to the same question. | None |
| Clarification is required | The service/process receives the recorded answer. A specific follow-up explains the missing information, links the original question and answer, and sets the new input context. It does not count as registration confirmation. | Response routing record, follow-up, original answer, and unchanged approval state. | None |
| Sending fails or acknowledgment is lost | Not sent and a plain reason appear; uncertain delivery includes the agreed explanation. The current input retains the answer for explicit retry. Reconnection alone never resubmits. A repeated submission cannot record or act twice. | Lost-acknowledgment observation with one durable answer and one process effect after explicit retry. | None |
| The question has been replaced or its process cancelled | The original question's eligibility is checked before acceptance. The reason is shown, no answer is applied elsewhere, and an available replacement is offered without transferring text. | Stale-question submission and unaffected replacement record. | None |
| Projects are switched or the CLI exits | Switching clears unsent text without saving or transfer. Exit warns about unsent text. Saved records remain retrievable after reopening; startup again selects no project. | Before/after input and record observations for switch, exit, and reopen. | None |

### Definition of done

The connected answer journey and essential failure cases establish the criteria, including lost acknowledgment and stale-question rejection, without an exhaustive test matrix. Evidence links submission, saved record, receipt, and process effect to the same question. The preceding workspace remains usable.

Question creation and response consumption use the actual service and SQL. Necessary controlled inputs are identified and justified; they prove only this response component. Real agent and registration behavior require their own connected integration evidence.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Question source and context | Submission cannot rely on guessed recipients or a not-yet-available registration process. | Resolve the initial-record and process-context items in `docs/maestro-architecture.md#constraints-and-unresolved-details`. |
| Same request versus edited response | Retry must avoid duplicate effects without confusing a new answer with a prior submission. | Specify the request identity and recovery contract. |

## Partial-registration boundary

No narrower portion is declared. Any selected subset requires explicit scope, outside dependencies, relevant journey references, and acceptance coverage before registration confirmation.
