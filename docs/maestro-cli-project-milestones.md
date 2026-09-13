# Maestro CLI — Project Milestone Source

## Identity and status

| Field | Value |
|---|---|
| Project | Maestro |
| Capability | Local terminal interface for multiple projects |
| Repository | https://github.com/jmiedreich-ux/Maestro |
| Responsible project architect | Owner and software architect |
| Document version | 3 |
| Declaration | CLI — Command-line interface |
| Status | Proposed project outcomes for review; not a registration package, development breakdown, or implementation approval |
| Design authority | [Maestro Architecture](maestro-architecture.md) |
| Reviewed architecture | [Architecture source revision](https://github.com/jmiedreich-ux/Maestro/blob/7b97a460db371877bc4feb6b899ff06cffb0b7af/docs/maestro-architecture.md), content blob `4b56bbf598ddd466376fdf182b2d5f20da5f220c` |

The architecture owns system behavior. This source defines delivery boundaries, usage journeys, acceptance evidence, and dependencies. The grouping is proposed; it does not add architecture or claim existing code satisfies the outcomes.

The source format is provisional until the Maestro Planning Guide format is defined. No development milestones or work packets are created here.

## Purpose, scope, and current state

The CLI provides an installed `maestro` terminal application connected to the Python service on the Linux AI box. It displays separately identified projects, recorded conversations, findings, and attention items, and accepts explicit answers to service-delivered questions.

The scope includes the service/API/SQL connections required for those capabilities. It is not limited to terminal rendering. HTTP requests and Server-Sent Events connect the CLI and service; SQL stores current state and durable history.

Excluded: command center, undecided mobile interface, unsolicited agent conversations, saved drafts across project switches, execution commands, and a complete project execution engine. Actual registration assessment, package publication, and activation belong to the registration outcomes; their CLI integration is mapped below.

The architecture describes intended behavior. No source-code or running-system assessment was performed for this milestone document. Existing implementation readiness is **unknown**. Reuse requires evidence of the described operation, not file names or earlier completion claims.

## Project outcomes and order

Two proposed outcomes separate a usable read-only workspace from reliable responses. Both are prerequisites to registration development.

| Position | Project milestone | Outcome | Dependency |
|---|---|---|---|
| 1 | CLI-PM1 — Connected multi-project CLI workspace | A usable terminal view of real service-held project state, conversations, findings, and attention. | First CLI outcome; includes the service and storage connections necessary for its own operation. |
| 2 | CLI-PM2 — Reliable project questions and answers | Question-linked input is saved, acknowledged, routed, and recovered without accidental actions or duplicate effects. | Depends on CLI-PM1 — Connected multi-project CLI workspace. Together they establish the CLI foundation. |

## CLI-PM1 — Connected multi-project CLI workspace

**Purpose:** A usable, read-only terminal workspace exposes live project information without mixing projects or controlling their work.

**Scope:** Linux service and CLI setup; local connection; HTTP reads and streamed updates; durable state retrieval; project navigation; conversations, findings, attention, keyboard controls, empty/error states, and reconnection.

**Usage journey:** Follow documented setup and start the service separately. Launch `maestro`, inspect the overview, select a project, read recent and earlier messages, expand findings, and inspect another project's attention item. Produce further service activity while reading history. Disconnect and reconnect, retrieve missed updates, and exit without stopping the service.

### Acceptance criteria

| Condition | Required result and pass boundary | Evidence |
|---|---|---|
| Service and CLI are installed using documented instructions | The Python service runs under `systemd`; boot start and crash restart are demonstrated. `maestro` connects to the existing service without starting it. Required configuration and access are documented. | Commands used, installed revision, service state, connection results, and configuration references without secret values. |
| Startup succeeds or connection fails | The overview starts with visible “No project selected,” even with one project. Connecting, connected, unavailable, and retry behavior are distinguishable. A failed lookup is not an empty list. | Connected and unavailable journeys, including successful retry without reopening the CLI. |
| Multiple projects are present | The overview orders attention-needed, working, then idle projects. Selection opens the correct conversation without changing work. Project names and record associations remain distinct. | At least two separately identified service-held projects, their before/after state, and selection captures. |
| Messages and state change | Actual service/SQL records feed HTTP reads and streamed updates. Messages identify their source; read-only requests create no duplicate status or conversation records. | Correlated API, SQL, and displayed records; service-generated updates for both projects. Hardcoded terminal sample data is insufficient. |
| Earlier content or findings are opened | Recent history and Load earlier messages work while current activity or waiting state and pending questions remain accessible. Details expand inline, preserve the selected project and question linked to input, and restore reading position when closed. Viewing does not acknowledge or resolve a finding. At the bottom, messages follow; above it, New messages appears without pulling the reading position. | Captures of each state and unchanged finding/process state after viewing. |
| Another project needs attention | The notice names the project and required response without switching focus. The attention list covers all projects; selecting an entry opens its project and question. | Notice while another project is selected, followed by explicit navigation to the correct record. |
| A successful lookup contains no results | Correct empty messages appear for projects, attention, and findings. Retrieval failure and missing context remain distinct. Registration-specific empty actions are completed with registration integration. | Actual empty-query and failed-query observations, with current context identified. |
| The connection drops during use | Visible content remains marked disconnected and potentially stale. Service actions are unavailable; local help, retry, and exit remain. Reconnect retrieves recorded changes without replaying earlier submissions. | Disconnect/reconnect record and uninterrupted independent service activity. |
| Keyboard or terminal size changes | Visible focus, Tab/Shift+Tab, arrows, Enter activation, and Escape behave as specified. Below the chosen minimum size, the enlargement message appears while service work continues. | Recorded terminal dimensions and keyboard-only walkthrough. |
| Commands are invoked | Help, projects, attention, findings, retry, and exit work within this milestone's read-only scope. Help documents actual syntax and context requirements, excludes unimplemented commands, and works offline. | Each command exercised against its real path; exit leaves service work and saved records available. |

### Definition of done

Every acceptance row has evidence from the installed CLI, actual service, and persistent SQL records. Project and event creation for demonstration is documented and reproducible before registration exists; no hidden manual database edits or undocumented setup are required.

Controlled service activity may demonstrate workspace behavior without a project execution engine. Such activity is labeled as a demonstration and proves only this read-only outcome. Answer submission and registration are not represented as operational at this boundary.

The keyboard and terminal choices required for use are documented, all observed failures against acceptance are resolved or explicitly accepted, and no limitation removes the stated usable-workspace purpose. Completion evidence includes the implementation revision, setup instructions, observations, and review results.

## CLI-PM2 — Reliable project questions and answers

**Purpose:** A response to a specific service-held question reaches the correct project/process, is saved before acknowledgment, and cannot silently become an approval or duplicate action.

**Scope:** Question rendering, recommendations and alternatives, input context, choice-to-input behavior, written and multiline answers, validation, SQL recording, response routing, acknowledgment, clarification, stale-question checks, and explicit retry. The generic service-side question/response path is included.

**Usage journey:** Open an attention item, select a choice, add clarification, and send. Observe save acknowledgment and the recorded answer. Obtain a linked follow-up. Repeat with a lost acknowledgment and an explicit retry, then with a question that is replaced before submission. Switch projects with an unsent answer and exit with another unsent answer.

### Acceptance criteria

| Condition | Required result and pass boundary | Evidence |
|---|---|---|
| A question requests a choice or information | Clear alternatives include a justified recommendation where appropriate, tradeoffs, and a written alternative. Information requests allow writing without forced choices. | Actual service-delivered examples of both question types; no hardcoded display-only questions. |
| Input has or lacks a selected question | Project or registration context, requester, and question are visible. Ordinary text is accepted only for that question; otherwise input is commands-only. Missing, unknown, conflicting, or ambiguous project targets cannot execute by guessing. | Submitted context and service validation results, including rejection of an invalid target. |
| A choice is activated | The choice fills the input without submission. Optional text can be added. Send or Enter submits explicitly. | No service submission on choice selection; one submission after explicit send. |
| A long answer is entered | Shift+Enter adds a line; multiline paste does not submit. The input grows to its documented limit then scrolls internally. | Keyboard and paste walkthrough with preserved question/conversation visibility. |
| An answer is submitted | Commands and answers can be submitted while streamed updates arrive without changing their target or disrupting input. Sending remains until the service confirms SQL saving. The saved answer appears in the conversation, input clears, and the question shows Answer received rather than Resolved. | Request, saved record, acknowledgment, and displayed state linked to the same question. |
| Clarification is required | The service/process receives the recorded answer. A specific follow-up explains the missing information, links the original question and answer, and sets the new input context. It does not count as registration confirmation. | Response routing record, follow-up, original answer, and unchanged approval state. |
| Sending fails or acknowledgment is lost | Not sent and a plain reason appear; uncertain delivery includes the agreed explanation. The current input retains the answer for explicit retry. Reconnection alone never resubmits. A repeated submission cannot record or act twice. | Lost-acknowledgment observation with one durable answer and one process effect after explicit retry. |
| The question has been replaced or its process cancelled | The original question's eligibility is checked before acceptance. The reason is shown, no answer is applied elsewhere, and an available replacement is offered without transferring text. | Stale-question submission and unaffected replacement record. |
| Projects are switched or the CLI exits | Switching clears unsent text without saving or transfer. Exit warns about unsent text. Saved records remain retrievable after reopening; startup again selects no project. | Before/after input and record observations for switch, exit, and reopen. |

### Definition of done

Every answer-path acceptance row passes through the actual service and SQL, including the lost-acknowledgment and stale-question cases. Generic question creation, consumption, and follow-up behavior are documented and reproducible without requiring the unfinished registration process.

Controlled service-generated questions may demonstrate this transport and interaction capability. They do not prove agent reasoning, the registration fidelity loop, or package activation. Live agent roles and Model Execution Adapters retain their separate design boundaries.

The connected workspace delivered by CLI-PM1 — Connected multi-project CLI workspace remains usable. Evidence identifies the service/CLI revision, submitted contexts, persisted results, observed process effects, and any explicitly accepted limitations.

## Registration integration coverage

This section assigns the CLI-facing integration to registration outcomes; it does not create another registration process or declare one complete.

| Registration outcome | Required CLI integration |
|---|---|
| REG-PM1 — Register and confirm a project through either interface | Amend this existing outcome to CLI-only scope while retaining its identifier. Connect `/register <repository>`, `/registration`, registration-specific findings/empty views, source scope selection, actual architect/reviewer messages, recorded answers, package inspection, explicit exact-candidate confirmation, and initial cancellation. The Register control and slash command use the same process. |
| REG-PM2 — Update a registration without losing approved history | Connect explicit re-registration identification, same-project idle enforcement, existing-process handling, version comparison, changed/ineligible candidate rejection, and confirmation/cancellation while preserving prior active history. |
| REG-PM3 — Recover registration without losing decisions or exceeding limits | Connect recovered status, saved decisions and limits, and Outcome not confirmed handling. Reconnection queries confirmation/cancellation outcomes; explicit retry cannot duplicate effects. |

Initial registration and re-registration both return the existing process for duplicate requests and reject confirmation of changed or ineligible candidates; these protections are not limited to re-registration. Registration comparison shows changes and reasons against the active version. Confirmation/cancellation are focused view actions, never standalone slash commands or ordinary text replies. Cancellation identifies effects and retained history; neither action is preselected. Confirmation does not start development, and failure/cancellation does not restart work.

Real GitHub package publication, independent agent review, source interpretation, duplicate-registration handling, and package activation must be exercised when these integration outcomes are assessed. Sample data or generic service demonstrations cannot satisfy registration completion.

The separate registration source remains an earlier draft with both-interface scope. The amendments above are required alignment, not a claim that the existing document is already corrected or approved.

## Required detail before implementation

Outcome-level behavior is largely specified. Several mechanisms and context rules still need a recorded design; this source does not silently select them.

| Detail | Why it matters | Required resolution point |
|---|---|---|
| Project and question provisioning before registration | Foundation journeys need real service-held records without relying on an unavailable registration workflow. | Define the documented bounded provisioning mechanism before CLI-PM1 — Connected multi-project CLI workspace implementation; extend it for CLI-PM2 — Reliable project questions and answers. |
| Project/process/question selection | A project can have historic or concurrent activity; “current process” must resolve unambiguously for findings and questions. Registration intake also begins before an existing project is selected. | Specify identity and selection rules before the relevant navigation or submission implementation. |
| HTTP, event, and SQL contracts | CLI and service must agree on identities, payloads, status, save acknowledgment, and reads. | Specify together before implementing their connection; endpoint names alone are insufficient. |
| Reconnect and duplicate recognition | Lost updates and uncertain sends require distinguishing the same submission from a new or edited answer. | Specify missed-update recovery and request identity before response/reconnect implementation. |
| Setup and local service access | Installation, runtime dependencies, service configuration, and actual connection access must work without omitted steps. | Document the chosen mechanism before acceptance; no credential or security model is invented here. |
| Terminal implementation | Toolkit/runtime, supported terminal behavior, remaining command arguments, history loading, input-height limit, and minimum dimensions need concrete choices. | Select during implementation; verify against the agreed behavior before completion. |
| Registration formats and roles | Source interpretation, package schema, review roles/adapters, and work-state enforcement are dependencies of actual registration. | Resolve in registration and agent design before their CLI integration is declared complete. |
| SQL and GitHub package consistency | A saved answer or action must not be confused with completed package publication or activation. | Define the record relationship and failure behavior before registration actions are integrated. |

These are delivery prerequisites or implementation choices, not extra product features. Missing mechanisms prevent a claim of implementation readiness; they do not invalidate the recorded CLI outcomes. Additional design decisions belong in the architecture, separately from milestone work.

## Review and acceptance status

The [CLI milestone detail review](maestro-cli-project-milestones-review.md) records fidelity, coverage, and unresolved details.

No milestone is currently claimed complete. Source review is not operational verification, registration acceptance, or authority to begin implementation.
