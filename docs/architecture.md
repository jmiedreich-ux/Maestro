# Maestro Architecture

## Purpose and boundaries

The [project overview](project-overview.md) explains the project's purpose, delivery scope, and evidence of what exists. This architecture explains how the service, agents, storage, and terminal interface work together.

SQL backup and restore are out of scope. They are not an open decision or a delivery prerequisite. Ordinary service-restart and interrupted-operation recovery remain in scope.

This document specifies how the system should work; it does not claim that the software is implemented. Sections marked **provisional** describe decisions that are not settled.

The initial interface is the Maestro CLI. The command center within the Reporting and Command Interface is outside the initial scope. Command-center support uses the same service operations, registration process, and record sources. Mobile presentation is undecided; neither a mobile terminal nor a separate interface is specified.

Read by subject: [runtime and agents](#runtime-and-prerequisites), [connections and data](#connections-and-data), [CLI](#cli-workspace), [registration](#registration), [architecture loop](#architecture-loop), [journeys](#journeys-and-interactions), and [unresolved details](#constraints-and-unresolved-details).

### Functional areas

The three functional areas are established. Execution behavior and authority are defined in [Execution](#execution); implementation evidence remains outstanding. Planning and Monitoring retain only the responsibilities defined by their process sections and do not gain authority from this summary.

| Area | Responsibility |
|---|---|
| Planning | Interpret requirements and architecture, organize work and dependencies, define completion criteria, and handle authorized changes. |
| Execution | Assign approved work to agents, manage implementation and checks, obtain reviews, and carry out authorized corrections and merges. |
| Monitoring | Report activity, progress, failures, resource use, pending decisions, and action history. |

Registration is the entry process for Planning. After registration confirmation, the separately started [architecture loop](#architecture-loop) investigates the code and prepares development milestones and work packets.

## Project-wide review boundary

Every Maestro review is limited to its assigned scope and agreed requirements. This applies to documentation, decision fidelity, architectural completeness, consistency, registration, architecture breakdown, specialist support, packet implementation, integration changes and whole-milestone outcomes. A reviewer is not required to find something; a valid review may return no findings or pass with recorded non-blocking limitations.

Require correction only for a concrete in-scope issue that prevents the required outcome or violates an agreed requirement. A risk is blocking only when its credible impact on the required outcome is explained. Each blocking finding identifies the controlling requirement, affected content or behavior, impact and minimum necessary correction. An opportunity to improve something is not by itself a blocker.

Record non-blocking limitations and optional improvements in the existing review/result or handoff record, with their location, practical impact and why the required outcome is still satisfied. They do not prevent approval, integration or promotion, trigger another review round, or become implementation work automatically. A desired scope expansion follows the existing change authority. Required failed or unverified behavior cannot be relabeled as a limitation to obtain a pass.

Reviews do not add requirements, demand perfection, reopen unchanged work over preference or expand tests to cover every conceivable edge case. Apply the [verification expectations](planning-guide/README.md#verification-expectations). Stop once the assigned requirements, necessary connections and proportionate evidence are covered. Necessary correction checks cover the correction and affected dependencies, retaining valid unaffected coverage. Existing independence, evidence, authority and process-specific review/recovery limits remain unchanged; logging a limitation grants no extra attempt or waiver.

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

The unattended coordination contract is: Planning supplies approved work, Execution performs it under the defined gates, and Monitoring reports progress and problems.

| Situation | Response |
|---|---|
| Checks and independent review pass | Complete the work, merge where already authorized, and release dependent work. |
| A worker crashes or stalls | Recover or reassign within the authorized retry limit. |
| Review identifies an implementation defect | Request a bounded correction. |
| A dependency or work breakdown is flawed | Report the affected work. Replanning requires confirmed re-registration followed by a manual architecture-loop start; reporting a problem grants no automatic revision authority. |
| Scope, architecture, or an Owner-reserved requirement changes | Pause affected work and request a decision. Unrelated approved work may continue. |
| Time, cost, or retry limits are reached | Stop affected work and report the reason. |

Implementation and integration authors cannot approve their own changes. Monitoring reports and routes problems without changing requirements. The specific [Execution review and merge rules](#independent-implementation-review) govern delivery; this overview grants no additional authority or automatic replanning.

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

Execution review, correction, integration, Quality Assurance, merge and completion boundaries are defined under [Execution](#execution). Registration's review limits do not transfer to implementation reviews. Explicit Owner confirmation of registration and the existing role-authority boundaries remain unchanged.

### Installed validation schemas

Maestro owns the schemas for its process definitions and saved records. Installation places them in `schemas/` inside the Maestro installation folder, not inside a managed project. A project's application and API schemas remain separate.

Each installed bundle has a stable name and positive integer version. Configuration uses the exact reference `<name>@<version>`, not a repository path or a moving latest version. The architecture-loop bundle is `architecture-loop@1`, installed at `schemas/architecture-loop/1/schema.json` relative to the Maestro installation folder; its source remains [the repository schema](schemas/architecture-loop.schema.json). The installer supplies the bundle and its required local references. The service resolves the installation folder from its installed runtime, never the current working directory or a project's files. Schema resolution does not download files.

The architecture-loop `saved_outputs.schema` setting is `"architecture-loop@1"`. Its process-definition validator and output validators use that bundle's named definitions. Other processes follow the same installed-bundle convention when their schema contracts are supplied; this does not declare an unprovided registration schema complete.

Before an activity starts, the service verifies that its bundle exists, is supported and can resolve all required definitions. SQL saves the exact bundle reference and SHA-256 of its installed bytes with the effective process-definition snapshot. Bundles with external local references also retain those dependency hashes. Installation must retain versions needed by unfinished activities; published bundle versions are immutable.

Continuation and recovery use the recorded version and hashes. A missing, unsupported or changed bundle blocks the affected process or its continuation with a clear error while preserving saved work and read-only views. It never falls back to another version, a repository file or a project's schema. Restoring the required bundle does not restart review or recovery budgets. Schema validation checks record structure; semantic checks and independent fidelity review retain their separate responsibilities.

### Shared process definitions

Registration and the architecture loop use the same relative configuration layout: `<process>.architect.run_timeout_seconds`, `<process>.fidelity_reviewer.run_timeout_seconds`, `<process>.recovery.automatic_recovery_attempts`, and `<process>.maximum_fidelity_reviews`, with `registration` or `architecture_loop` as the process name. Values and consumed allowances remain separate for each process and activity. Shared tool and workspace settings remain outside these sections. Legacy top-level registration timeout and recovery keys are invalid, not aliases. Defaults and accounting remain defined in the process-specific settings and review-limit sections.

The runtime uses one service-owned TOML file, `/etc/maestro/agents.toml`, for shared settings and process definitions. Registration and the architecture loop use separate sections in that file. The file describes how each process uses runtime capabilities; it is not limited to numeric settings.

The runtime implements common initiation, agent-session handling, output validation and saving, review accounting, confirmation, and recovery. Each process supplies its requirements for those capabilities. Process-specific judgment and record meaning remain in the relevant handler, schema, and agent instructions. A section name does not supply behavior that has not been implemented.

| Process section | Declared requirements | Runtime responsibility |
|---|---|---|
| `initiation` | Supported entry operation, prerequisites, and start restrictions. | Validate the request and enforce the declared prerequisites before creating work. |
| `agent_session` | Role references, tool/model selection rules, session mode, and applicable limits. | Launch or continue the correct isolated session and retain its identity. |
| `saved_outputs` | Required output types, format/schema references, destination rules, and version policy. | Check outputs and their identities, save through the supported destination handler, and record verified references. |
| `review` | Independent reviewer role, review limit, and supported amendment policy. | Route exact outputs, count completed reviews, and enforce the process's limit. |
| `confirmation` | The versioned result being confirmed, required authority, eligibility checks, and completion action. | Verify the exact result and record confirmation without unauthorized advancement. |
| `recovery` | Supported recovery policy, retry limits, and stopping conditions. | Reconcile saved state and apply only the allowed recovery action. |

Sections sit under `registration` and `architecture_loop`, for example `registration.saved_outputs` and `architecture_loop.saved_outputs`. Shared tool paths, credential references, and workspace settings retain the fields under [adapter configuration](#adapter-configuration). The registration review limit remains `registration.maximum_fidelity_reviews`; the registration review section uses that value rather than maintaining a second copy. The architecture-loop limit is `architecture_loop.maximum_fidelity_reviews`.

Each definition identifies its schema version and uses [installed validation schemas](#installed-validation-schemas). Section fields select supported policies, schemas, and destination handlers; they do not contain shell commands or arbitrary executable instructions. Required sections depend on the process contract. Unknown fields, unsupported policies, invalid types, conflicting settings, or missing required sections produce a plain configuration error before that process starts. Read-only views remain available. Omitted optional values use only documented defaults; registration-specific defaults do not automatically apply to other processes.

The service validates and saves the effective process definition and its hash with each new activity. That snapshot governs the activity through answers, reviews, confirmation, and recovery. Editing the file changes future activities, not in-progress authority, outputs, or budgets. Tool availability and credential checks still apply to each launch as specified by the adapter contract; the snapshot does not preserve revoked access. Per-run evidence includes the activity's definition hash and the effective tool configuration hash.

### Shared output handling and process boundaries

A saved-output definition identifies the required record type, schema and format, supported location rule, and version policy. It may refer to a named output set rather than duplicating a detailed record schema inside TOML. Schema validation establishes structure; the relevant process validator checks meaning and references. Independent review checks fidelity.

The common handler verifies project/activity identity, allowed destination, required outputs, schema validity, and version references before reporting the output set saved. SQL records the operation and its result; repository writes use verified publication and recovery handling. A partial external write cannot be presented as a completed output set. Existing accepted versions remain available.

For registration, the output set is the [registration package](#package-structure), with its existing publication, hashing, review, confirmation, and activation rules. Configuration references that contract; it does not replace its schemas, relocate records arbitrarily, or bypass eligibility. The same handlers apply the architecture-loop output definitions and publication rules below.

Architecture-loop outputs include the investigation, code-direction decisions, project structure, specialist definitions and starting context, development milestones, work packets, and their review and confirmation references. Specialist roles and any maintained memory remain close to the relevant source. A location rule such as source-local placement requires a resolved permitted path; a descriptive label alone is not a valid destination. Their record fields, paths, and publication rules are defined under [architecture output locations and records](#architecture-output-locations-and-records) and [publication, recovery, and cancellation](#publication-recovery-and-cancellation).

A shared handler does not make all process rules interchangeable. Registration retains fresh agent conversations, except for capacity-only continuation within the same assignment, and its package activation rules; the architecture loop requires a persistent architect session and confirms a breakdown. Both stop at their defined completion boundary. Execution remains a separate manual start and its policies are not supplied by these definitions.

### Whole-product architectural evaluation

Architectural evaluation continues throughout investigation, breakdown, clarification, and amendments. Each local decision is checked against the whole product: existing capabilities, shared services, interfaces, data ownership, dependencies, and other agents' work.

The architect identifies repeated needs and selects shared runtime capabilities with process-specific definitions where that reduces duplication and preserves clear boundaries. It evaluates the effects of reuse, replacement, and new abstractions across the product rather than optimizing one feature in isolation. Shared configuration is used only where the runtime has a defined behavior to apply.

Findings and reasons are saved with the affected decisions. Routine technical choices within scope remain the architect's responsibility. Changes to established direction follow replanning; changed outcomes, scope, or reserved decisions require the appropriate Owner decision. Continuous evaluation does not recreate settled foundations, reopen decisions over preference, or grant scheduling and execution authority.

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

Registration intake collects separate, explicit tool and exact model/version choices for the architect and fidelity reviewer before the architect starts. Each role selects Claude Code or Codex independently; the reviewer does not inherit the architect's choice. Saved intake questions collect either missing selection, and SQL records both against the activity before launch. The service checks that the selected model/version is supported by the selected tool before that role begins. An unavailable or unverifiable selection is reported before launch; no silent substitution is permitted. Records retain the requested model, tool-reported model, provider, installed tool version, and capability-check result. A full provider model identifier is required; moving aliases are not accepted as exact-version selections. Provider identifiers establish the observable model version, not an undisclosed internal snapshot.

Before launch, the service checks model selection, authentication, and structured-output support using the credentials and configuration assigned to the run. This check does not read project sources. Its result records the tool version, account/provider, model, and configuration hash. A change to credentials, configuration, or tool version invalidates the check. The service also checks the model identity reported by the running tool. Missing or different identity prevents result acceptance and produces a specific integration failure. Agent-written text is not evidence of model identity.

Each installed route also names a non-secret settings profile with a nonempty, exact permitted-destination list. Every destination records the HTTPS hostname and port used by that provider route; wildcards and implicit destinations are invalid. The route configuration hash includes this list, so a changed destination policy invalidates preflight and cannot be substituted during a run. Credentials remain a separate service-only profile and are never written into this settings record.

Automatic model substitution is disabled in the effective tool configuration. A refusal remains a refusal; a different model is not used to bypass it. If the installed tool cannot enforce the selected identifier or supply the required evidence, that route is unavailable until corrected. The service does not silently weaken this requirement. [Claude model configuration](https://code.claude.com/docs/en/model-config) documents aliases and fallback; the selected settings must prevent those switches.

#### Tool transport

The Python adapter uses argument arrays and local pipes, not an interactive terminal or shell-built command string. Each registration run uses a fresh tool conversation except capacity-only continuation within the same assignment under [context management](#checkpoints-and-safe-continuation). A supported continuation may retain that exact conversation after compaction; this grants no general registration-session persistence. Its saved session identifiers are diagnostic references, not permission to resume another project's conversation. The architecture loop instead requires its own [persistent architect session](#persistent-architect-session); its continuation and event contract is defined under [persistent-session adapter contract](#persistent-session-adapter-contract).

| Tool | Transport and result handling |
|---|---|
| Codex | Launch `codex app-server` over stdio for the run. Perform `initialize` and `initialized`, use `model/list` for catalog discovery, then `thread/start` and `turn/start` with the selected model, working directory, permission policy, assignment instruction, and `outputSchema`. Correlate thread/turn events to the run. Collect the final structured agent message after a successful `turn/completed`; use `turn/interrupt` for cooperative stopping. |
| Claude Code | Launch print mode with explicit `--model`, `--output-format stream-json`, `--verbose`, and `--json-schema`. Supply the bootstrap instruction to read the assignment file. Capture startup model/session metadata, progress, and the terminal result. Extract `structured_output` as the response; missing structured output is a failure, not a request to parse arbitrary prose. |

[Codex App Server](https://learn.chatgpt.com/docs/app-server) documents the model catalog, stdio handshake, turn schema and interruption. [Claude programmatic operation](https://code.claude.com/docs/en/headless) documents streaming and structured results; its [CLI reference](https://code.claude.com/docs/en/cli-reference) defines launch flags. These are selected integration contracts, not proof that the installed tools have passed them.

Each adapter targets an explicitly recorded, capability-checked tool release. Codex protocol validation uses the JSON Schema bundle generated by that installed release. Required fields and events must be present; an unsupported release reports an integration failure rather than guessing its output format.

#### Agent workspaces

Workspaces are service-managed on the Linux AI box. The configurable root defaults to `/var/lib/maestro/workspaces/`; a registration attempt uses `<project-id>/<activity-id>/` beneath it. The registration attempt ID is the registration activity ID, not a second identity. Existing references to `<registration-attempt-id>` mean this same value; the registration version and individual run IDs remain separate. Within the attempt, each launch uses `runs/<run-id>/` as its workspace, containing `source/` at the exact assigned repository revision, `input/` for immutable assigned artifacts, and `output/` for new artifacts. The adapter starts the agent with its assigned workspace as the working directory. Separate attempt and run directories prevent output collisions between projects and recovery attempts.

The fidelity reviewer has a separate workspace containing the exact source, architect assessment, and candidate under review. These files are read-only; the reviewer writes to its own output directory and cannot amend the architect's files. Both roles use a Linux mount namespace that makes source, assignment, and prior-artifact paths read-only. Only assigned output and scratch paths are writable. The agent runs without privileges to change mounts, escape its process group, or access another run's workspace. Folder names and instructions alone do not enforce these boundaries.

The service places the exact assessment and candidate in the reviewer's input area and checks their hashes. It records each artifact's original identity and assigned relative path. The reviewer returns these assigned references. Permission to write output through the agent tool does not make the source or input mounts writable.

Service-managed tool settings pre-authorize only assigned operations. An unexpected permission request is denied and reported as a missing-permission failure; it cannot hang waiting for a terminal answer. Required credentials are provisioned for the service account before use, with no secrets in assignment files or logs. **Temporary Owner-approved exception, 2026-09-18:** the subscription login files required by an approved Codex or Claude CLI route may be mounted read-only only into that route’s isolated runtime. The service records only the named profile and approval, never a secret value; the exception grants no GitHub or Owner authority and applies only until a credential-broker transport replaces it. Registration agents have no GitHub write credentials; package publication is a separate service-owned operation subject to wrapper checks. Repository instructions are assessment inputs and cannot expand the assigned role's permissions.

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

The registration architect and registration fidelity reviewer each default to **30 minutes per run**, configurable separately. Other planning and Execution assignments use their process-specific duration settings. They do not inherit this registration default. Timing starts at launch. Progress does not reset it. A clarification response ends the run, so waiting for answers consumes no run time. Each follow-up or failure-recovery run has its own timer. Capacity-only continuation instead preserves remaining active time under [context management](#checkpoints-and-safe-continuation).

Reaching the limit requests termination, preserves available output, and pauses the activity once stopping is confirmed. Timeout alone does not trigger automatic retry: an identical run may reach the same limit. The CLI shows elapsed time, last reported progress, and whether termination was confirmed. Investigation or an explicitly recorded next-run duration exception precedes manual retry; editing configuration alone cannot change the current activity's snapshotted duration. Unknown termination status continues to block replacement.

### Returned implementation plan

For an assigned execution work packet, the agent reads and understands the packet, returns its proposed implementation plan before making changes, and then continues the assigned work. The plan states the required outcome, relevant existing code, intended changes and sequence, necessary connections, basic verification and essential failures, and any blocking missing information or conflict.

The service records and displays the plan as an assignment-linked intermediate output. It is distinct from the final result. Returning it introduces no additional review, approval, or pause before execution. A future plan-checking gate is outside the current behavior. Existing scope and authority limits still apply to actual blockers.

This behavior concerns execution work packets. A registration architect returns its assessment and candidate under the registration response contract; registration does not acquire an implementation-plan or development-work stage.

## Agent performance and context management

Performance records and context management apply to every supported agent route, including persistent architect sessions. Qwen is the primary coder in the [Execution design](#work-planning-and-coder-selection); its adapter contract is defined under [Execution configuration](#execution-process-definition-and-configuration), while implementation and installed verification remain outstanding. It is not selectable in the registration or architecture-loop contracts. The same capacity handling applies when implemented; context exhaustion is not an agent-performance failure. They do not select new models, change role authority, or define general Execution policy. Each adapter declares its supported measurements and continuation operations; unsupported capabilities remain explicit.

### Performance records

The service records facts in SQL before display. Each record carries a schema version, stable event identity, UTC observation time, project, activity, assignment, run, session, role, tool, and exact model identity. Service observations and provider measurements remain distinguishable from agent-reported progress.

| Measurement | Meaning |
|---|---|
| Time | Active elapsed run time, waiting time, and total assignment elapsed time, in seconds. Active time includes provider backoff and tools, not only model generation. Waiting reasons distinguish Owner input, review, and service-managed continuation. |
| Result | Validated completion, blocked, failed, or cancelled, with a recorded cause. A capacity transition is not an assignment's terminal result. |
| Rework | Technical recovery, output correction, and fidelity-review counts use their existing accounting records, not inferred message counts. |
| Tokens | Input and output tokens separately, with cached input and reasoning tokens when reported. Preserve provider definitions: subset counters are not added again to totals. |
| Cost | Provider-reported charge and currency when available. A calculated estimate records its rate source, effective date, currency, and covered token categories. Missing charges are unknown, including subscription-based and local runs; no invented zero cost. |
| Context | Effective capacity, latest occupied tokens and percentage, observation time, measurement quality, and highest observed usage per context segment and logical session. |

Usage events identify their provider request or tool event, counter scope, and whether values are deltas or cumulative snapshots. Deduplicate by run and source event identity; cumulative readings replace the previous reading for that scope rather than being summed. Session totals spanning several runs contribute only verified increments. Counter resets start a new recorded scope. Missing intervals make totals partial; estimates and partial coverage remain labeled.

Durations use monotonic elapsed measurements while running and saved state transitions across restarts. Do not double-count overlapping run intervals as assignment wall time. Preserve uncertainty when an interval cannot be reconstructed. Store unavailable numeric fields as null with a reason, never zero.

The service retains time and usage across capacity continuations. It records capacity-event counts separately from failures, corrections, and reviews. No single agent score or automatic model ranking is defined. Capacity stops do not lower quality or success measures; time and resource consumption remain visible. Source insufficiency, permissions, provider faults, and invalid output retain distinct causes.

### Context readings and thresholds

Context occupancy is not cumulative token consumption. The effective context limit is the usable limit of the exact model and its configured runtime session, which may be lower than the model's advertised maximum. Record the limit's source and configuration identity. A model name alone is insufficient evidence.

Each reading contains `context_segment_id`, nullable positive integer `limit_tokens`, nullable nonnegative integer `used_tokens`, nullable numeric `used_percent`, `quality` (`reported`, `estimated`, or `unavailable`), `observed_at`, and a source or unavailability reason. Percentage is occupied tokens divided by effective limit times 100, only when the values describe the same context scope. Do not clamp a reported over-limit value. Track the peak observed percentage and token occupancy with the limit that applied.

Read context at session attachment, before each service-controlled model turn, after returned turns, and whenever the adapter reports a change. During active work, request a supported read-only sample at most every 10 seconds; this never sends a model prompt or scrapes a provider UI. Mark a reading stale after 30 seconds without an update while running. A stale low reading cannot establish that the next input fits.

The sampling interval is a request cadence, not a guarantee of fresh measurements. An adapter that receives occupancy only with message or turn events cannot supply a new reading between those events. Retain the actual observation time; polling or replay must not make an old reading fresh. A long autonomous turn may cross a threshold before the service observes it. Threshold handling occurs at the next supported observation and safe control boundary; it cannot guarantee prevention of context exhaustion. Unsupported sampling remains explicit, and an observed capacity error follows capacity handling without a performance penalty or consumed failure allowance.

An adapter may estimate occupancy only with a suitable tokenizer and visibility of the actual context, including instructions, tool material, and retained history. Partial visible conversation alone cannot establish free capacity. Without reliable measurements, show unknown and retain checkpoints at safe boundaries. A reported context-limit error still invokes capacity handling.

The shared `context_management` section in `/etc/maestro/agents.toml` has these defaults, snapshotted with the activity:

| Setting | Default and effect |
|---|---|
| `warning_percent` | 75: save a warning and prepare a continuation checkpoint at the next safe boundary. |
| `handoff_percent` | 85: checkpoint and compact or replace context before further substantive work. |
| `resume_below_percent` | 70: target maximum occupancy after compaction or reconstruction, leaving space for continued work. |
| `sample_interval_seconds` | 10: minimum interval between supported active read requests. |
| `stale_after_seconds` | 30: flag aging active readings. |

Thresholds must satisfy 0 < resume < warning < handoff < 100; intervals are positive and staleness is no shorter than sampling. Invalid settings prevent new affected activities. Adapter-specific lower thresholds may be configured; the effective policy is recorded. Before a service-controlled turn, include the proposed input plus reserved output and checkpoint space in the fit check. The adapter supplies its supported output reservation and measurement basis. If that full budget cannot fit, act before the percentage threshold. Do not submit a predictably oversized request.

### Checkpoints and safe continuation

The service owns a versioned SQL checkpoint linked to the assignment and context segment. It records exact source/registration/decision versions, verified output references and hashes, completed and remaining work, unresolved questions, pending external operations, current workspace references, and unchanged attempt counts. An agent's summary is supporting context, not proof of completed work. Checkpoints contain no secrets and never replace project artifacts.

At a service-controlled safe boundary, save that checkpoint before an intentional compaction or replacement. For autonomous tool turns, use supported interruption/checkpoint controls; when unavailable, preserve already verified records and apply the existing supervised stop procedure. Never rely on a nearly full model having enough space to generate a fresh summary. Reconcile pending writes and confirm child termination before launching replacement work. Unknown effects pause continuation.

Use supported native compaction when it preserves the exact conversation identity and authoritative input bindings. Otherwise create a linked replacement session with the same role, tool, and exact model. Supply a new immutable continuation envelope under the same assignment identity, referencing the verified checkpoint and only relevant authoritative material. Its run/session bindings identify the continuing process; original budgets and outcome identity remain unchanged. Store the envelope and checkpoint input snapshot in a service-assigned read-only continuation directory without overwriting the original assignment. Existing assignment instructions identify the checkpoint input path; no agent-authored registration or architecture response fields are added. Preserve the logical session lineage while assigning a new context segment after compaction or replacement. A new process or run alone does not reset context occupancy. Reviewer context remains independent from architect context.

Record capacity handling as a service event with reason `context_capacity` and disposition `checkpointing`, `continuing`, or `paused`. These are supervisor metadata, not new agent success responses or process completion states. An intentionally capacity-stopped partial run need not return a final JSON response; that absence is not a missing-output failure. Its partial artifacts remain unaccepted drafts. Continuing work must still return the required complete, validated response before any process advancement; a capacity checkpoint never substitutes for it. Existing process views use running during checkpoint work and paused when continuation is unsafe, with a plain reason. Capacity classification requires adapter evidence or the service's fit/threshold check; agent prose alone cannot bypass failure accounting.

Resume automatically only after verified checkpoint recovery, safe stopping where needed, unchanged source eligibility, and adequate capacity. Prefer a fresh reported or supported estimated reading below the resume threshold. If the runtime cannot report post-reset occupancy, a verified empty-context reset plus a supported token-budget check of the complete reconstructed input is sufficient, labeled estimated. If neither is available, pause for a technical remedy instead of repeatedly restarting.

A capacity continuation consumes no technical-retry, correction, or fidelity-review allowance and does not repeat accepted work. It also cannot replenish time: continuations within the same uninterrupted assignment work phase share the original remaining active-time budget, including checkpoint/compaction work. A new process receives only that remainder, not a fresh full timeout. This is a specific exception to the ordinary new-retry-run timer rule. Time exhaustion still follows timeout handling.

If one compaction or replacement does not restore adequate room, pause with the specific oversized input or unsupported capability. Do not repeat the same ineffective transition. Further capacity transitions are allowed after real progress consumes available space; they are not quality failures. Failure to save a checkpoint or launch a continuation is recorded separately and follows existing cause-based recovery without relabeling the original capacity event as an agent failure.

### Visibility and delivery boundary

Existing activity details show active and waiting time, input/output tokens, latest context used/limit/percentage with timestamp and quality, and capacity-continuation status. GET `/activities/{activity_id}` returns these observations in a `runtime` object with `runs`, `sessions`, and `assignment_totals` arrays keyed by their saved identities. Each entry includes measurement coverage and observation time; no runs yields empty arrays, not fabricated zero measurements. Existing activity-change events identify the changed activity and prompt a refreshed read. Service-owned runtime details carry these records alongside process data; they do not alter architecture or registration artifact schemas. SQL-backed activity updates carry changes through existing API/event delivery. Unknown and stale measurements are explicit. A capacity percentage is not a work-completion percentage.

Runtime implementation owns persistence, adapter measurement normalization, thresholds, checkpoint validation, and safe continuation. CLI implementation owns displaying those recorded facts. Registration and the architecture loop use this common handling without separate accounting implementations. Persistent-session integration must demonstrate that context and totals survive successive runs and that verified findings, decisions, and pending answers survive continuation.

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

### Local Owner identity and credentials

This version has one configured Owner and a local CLI. The service derives Owner identity from a verified credential, never from an identity supplied in a request body. Loopback access alone is not proof of Owner authority.

Installation generates a cryptographically random 32-byte secret encoded as 64 lowercase hexadecimal characters. The CLI reads it from `$XDG_CONFIG_HOME/maestro/owner.token`, or `~/.config/maestro/owner.token`; `owner_credential_file` in CLI configuration may select another absolute path. The file is owned by the operator with mode 0600, under a private directory. It is outside repositories and agent workspaces. The service's TOML stores `owner.id` and `owner.token_sha256`, the SHA-256 of the ASCII token without a trailing newline; it stores no plaintext token.

The CLI sends `Authorization: Bearer <token>` on service requests only to its validated loopback service address. It does not follow redirects with credentials. The service uses a timing-safe digest comparison, records the configured Owner identity on accepted mutations, and requires the credential for CLI reads and writes. Missing or invalid credentials return 401; a valid caller lacking permission for an action receives 403. Offline help and exit still work. Missing CLI credentials show a setup error rather than a token prompt inside an agent conversation. Logs, events, receipts, and subprocess arguments never contain the secret.

The operator OS account and its programs are trusted with this local credential. Agent processes use a separate unprivileged execution identity and cannot read the operator's files, service configuration, or credentials. Existing workspace restrictions and credential provisioning must enforce that separation. The runtime's internal adapter-result channel is not an Owner request channel; an agent's output cannot create a confirmation or allowance grant.

Credential replacement is an installation/administration operation: write a new protected CLI token and service digest, then reload validated Owner settings. Old credentials cease to authorize new requests; already recorded actions retain their actor identity and recovery records. This grants no remote access or multiple-user administration.

### CLI request and event contract

The local API uses UTF-8 JSON under `/api/v1`. These are interface contracts for implementation, not claims about existing endpoints.

| Operation | HTTP interface | Result |
|---|---|---|
| Initial or refreshed workspace | GET `/workspace` | Project summaries, attention, service identity, and a consistent event cursor. |
| Project conversation | GET `/projects/{project_id}/conversation?before={cursor}&limit=50` | Chronological messages, activity references, and an older-page cursor; omission of before returns the latest page. |
| Project activities | GET `/projects/{project_id}/activities` | Activity identities, names, states, and start/end times. |
| Activity detail | GET `/activities/{activity_id}` | Current state, questions, findings, available actions, and service-owned runtime performance/context details. |
| Architecture view | GET `/projects/{project_id}/architecture` | Existing architecture activity or latest confirmed breakdown; absence is explicit and starts nothing. |
| Registration view | GET `/projects/{project_id}/registration` | Existing attempt or approved record; absence is explicit and starts nothing. |
| Submit an operation | POST `/requests` | Durable receipt for registration/architecture initiation, an answer, or an explicit process action. |
| Reconcile an uncertain submission | GET `/requests/{request_id}` | Saved status and result, or explicit not-found. |
| Live updates | GET `/events` | Server-Sent Events with durable cursor IDs. |

Read responses contain `data` and `event_cursor`, which identifies the corresponding position in the event stream. List responses also contain `next_cursor` for the next page, or null when no pages remain. Project summaries contain identity, plain name, registration status, activity state, and attention count. Activity records identify their project; question and finding records identify both their project and activity. Names and coded subjects remain plainly worded even when internal IDs have no readable meaning.

A submission contains `request_id`, `operation`, `project_id`, `activity_id`, `question_id`, `expected_version`, and `payload`. Context fields may be null only when inapplicable, such as initial repository intake. The service validates the required context for each operation. Operation names are `registration.start`, `project.bootstrap`, `question.publish`, `question.answer`, `registration.confirm`, `registration.cancel`, `registration.retry`, the shared `owner.decision` operation defined below, the `architecture.start`, `architecture.confirm`, `architecture.cancel`, and `architecture.retry` operations defined under [architecture API operations](#architecture-api-operations), and `execution.start`, `execution.status`, `execution.pause`, `execution.resume`, `execution.stop`, and `execution.retry` defined under the [Execution API](#execution-api-state-and-record-contract). The retry payload and eligibility rules are defined under [activity retry request](#activity-retry-request). Initial intake supplies repository and overview path, with optional `source_ref` and `publication_branch` under [source and publication selection](#source-and-publication-selection); saved intake questions collect missing scope and the separate architect and reviewer tool and exact model/version selections required by [tool and model selection](#tool-and-model-selection). Both selections must be recorded before architect launch. Answer payloads contain text and an optional choice reference. Registration actions identify the exact candidate or attempt and its version.

Receipts contain request identity, status, and any created project/activity identities. Status is accepted, completed, or rejected; accepted means durably recorded, not completed activity. Errors contain `code`, plain `message`, and affected fields. Invalid input returns 400, missing or invalid Owner credentials 401, unavailable access 403, missing records 404, stale context or conflicting request content 409, and unavailable service 503. No error is rendered as an empty result.

Events carry `schema_version`, `event_id`, `occurred_at` in UTC, `project_id`, `activity_id`, `type`, and `data`. Types cover project/activity changes, conversation messages, questions, findings, request outcomes, and attention changes. The service sends events only after the SQL transaction commits. Service-wide events have null project/activity context.

The initial data snapshot includes an event cursor. Replaying Server-Sent Events from that cursor supplies updates made between loading the snapshot and opening the stream. Repeated event IDs are ignored. Reconnection uses `Last-Event-ID`; if that cursor is unavailable, the CLI loads a fresh snapshot. Heartbeat comments arrive every 15 seconds. A 45-second gap with no stream traffic triggers disconnection. Heartbeats create no SQL or conversation records.

### SQLite storage

SQLite is the runtime database on the AI box. The service owns all database writes; agents, the CLI, and run supervisors submit information through service interfaces rather than opening the database. Multiple projects and agent sessions can run concurrently while the service serializes their short write transactions.

The shared `/etc/maestro/agents.toml` file uses `storage.engine = "sqlite"` and `storage.path = "/var/lib/maestro/maestro.sqlite3"` by default. Only SQLite is supported in this design; the path must be absolute on local storage. Installation grants the service account access to the database directory and journal files. Invalid or inaccessible storage prevents service readiness; it never causes an empty replacement database or an in-memory fallback.

Use WAL journaling and FULL synchronous writes. Readers may overlap a writer, but SQLite permits only one writer at a time. Keep read transactions short and retain automatic checkpoints. These constraints follow [SQLite's WAL documentation](https://sqlite.org/wal.html).

Project eligibility checks and start reservations share one write transaction, as do the related records already required by each request or activation contract. Acquire the write transaction before checking state that will be changed; competing requests recheck committed state after acquiring it. Do not hold a transaction open while waiting for an agent, GitHub, or user input. Failed writes cannot acknowledge success or emit committed-state events. Database contention follows the existing request failure and same-request reconciliation rules, not agent recovery budgets. [SQLite transaction behavior](https://sqlite.org/lang_transaction.html) supplies the database locking boundary; SQL/GitHub publication remains governed by [publication and SQL consistency](#publication-and-sql-consistency).

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
| `/architecture start` | Start the selected project's eligible architecture loop; request project selection if none is selected. An existing unfinished architecture activity is opened rather than duplicated. |
| `/architecture` | Open the selected project's current architecture activity or latest confirmed breakdown; request selection if needed. If neither exists, show a genuine empty result without starting work. |
| `/registration` | Open the selected project's existing registration process or record, including a candidate where available. It does not start registration. |
| `/findings` | Open blockers, non-blocking observations, and review findings for the selected project's selected activity. A selected finding exposes explanation and evidence; no review or state change is initiated. |
| `/retry` | Reread connection configuration and retry the service connection immediately. It does not start the service, repeat previous submissions, or retry project work. |
| `/exit` | Close the CLI session. Saved conversations and pending questions remain available. Unsent text triggers a warning before exit. |

The command set does not include separate `/select`, `/status`, `/respond`, `/compare`, `/confirm`, or `/cancel` shortcuts. Project selection uses the overview; status remains visible; answers use linked input. Registration comparison, confirmation, and cancellation are process-view actions. Architecture confirmation and cancellation likewise use explicit actions in its activity view.

Architecture start and view commands are defined above. The later Execution entry is `/execution start`, with its request contract defined under [execution initiation](#execution-initiation) and the [Execution API](#execution-api-state-and-record-contract). It remains outside the existing CLI milestone declaration and is not claimed as implemented.

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

Project milestones describe meaningful outcomes, releases, or component boundaries. The [architecture loop](#architecture-loop) produces development milestones linked to those outcomes, without assuming a one-to-one relationship or redefining the project scope. Registration retains the supplied outcome structure.

### Intake and scope

Registration initiation includes [architect and reviewer tool and model selection](#tool-and-model-selection) before architect launch. The intake request provides an explicit repository and repository-relative project overview path, and selects the whole supplied plan or a defined portion. An already registered repository is explicitly identified as re-registration before that process proceeds. The service records project identity and applies [source and publication selection](#source-and-publication-selection) before reading project sources.

Only one registration process can be active per project. A duplicate request opens that process instead of creating a competing process or another version. This restriction does not prevent registration or work on unrelated projects.

To register a portion, the service reads guide-compatible source and displays milestone identifiers with their plain subjects. Selection can cover milestones or a narrower written boundary. The service presents the included work, exclusions, and outside dependencies for confirmation. A narrower boundary must be recorded explicitly; the service cannot expand it by inference.

The Maestro architect checks whether outside dependencies exist or need work. Missing essentials become findings for a decision. For example, a publishing outcome dependent on authentication must identify authentication as existing, included, or missing essential work. Partial registration covers only its recorded boundary.

### Source and publication selection

Registration records which repository revision is assessed and where its outputs may be published. These are separate choices; the source branch need not be the publication branch.

| Intake field | Selection and default |
|---|---|
| `source_ref` | Optional string: a full `refs/heads/...` branch, `refs/tags/...` tag, or full 40-character commit SHA. Short or ambiguous refs are rejected. On initial registration, omission selects the repository's current default branch. On re-registration, omission reuses the active registration's saved selector and resolves it again. |
| `publication_branch` | An existing branch name without the `refs/heads/` prefix. Use an explicit authorized caller selection or the active registration's retained authorization. If neither exists, a saved intake question collects the Owner's choice before assessment; the repository default branch may be suggested but is not authorization. Maestro's own repository remains fixed to `master`. |

The verified caller supplies these fields in `registration.start.payload` or answers the linked intake question. The service rejects a destination that conflicts with an applicable project publication rule; changing that rule follows existing authority. A writable branch or an agent's recommendation is not Owner authorization. Existing authorization is reused without asking for it again.

Before reading the overview or launching an agent, the service validates the repository and selector, resolves the selected branch/tag to its commit, and verifies that commit and the overview are readable. A commit selector is verified directly. It checks that the publication branch exists and that service access and repository protections permit the required direct writes. Missing access, an empty repository, an unresolved ref or an incompatible branch rule prevents assessment with a specific intake error. No branch is created, protection bypassed or alternate target silently selected.

The service saves the normalized `source_ref`, resolved `source_commit`, `publication_branch`, resolution time and selection provenance in SQL before source use. Provenance identifies the verified caller request/answer or inherited authorization, and distinguishes an applied default from an explicit Owner choice. The CLI shows the repository, selector, exact commit, destination and whether each choice was supplied, inherited or defaulted. These appear in existing intake/scope and final confirmation views; they add no separate approval gate.

A service-built Decision record preserves this selection and its authority in the candidate. The manifest carries `source_ref`, `publication_branch` and `selection_decision_ref` alongside its existing `source_commit`; the decision reference uses the package-local record reference format. The service checks that manifest values match that decision and SQL. Because the decision is included in reviewed content, changing a selection cannot silently reuse approval of different inputs.

Assignments read source at the saved commit, never a moving branch or the commit that later publishes the package. Each publication operation copies the saved repository and branch into its journal and checks current access and expected branch head before writing. Recovery uses those saved selections; it does not resolve the source again or change the destination after a lost acknowledgment.

For a symbolic source ref, the service checks for relevant input changes before confirmation under [source consistency](#source-consistency); a deleted or unreadable ref makes that check unresolved. A commit selector remains intentionally pinned. Including updated source resolves and saves a new explicit selector/commit choice; changing the destination records new authorization. Either change creates a new candidate with affected review coverage and the same remaining budgets. Pending external writes must be reconciled before changing their target. Completed historical packages are never redirected or rewritten.

Re-registration displays inherited choices and permits authorized amendments during intake. It resolves the chosen selector for the new attempt; a missing inherited branch/ref is an error, not permission to fall back. The previous active registration keeps its selections until replacement confirmation succeeds.

The architecture loop obtains its source baseline from the SQL-confirmed registration manifest's `source_commit` and its publication destination from that manifest's `source_repository` and `publication_branch`. It verifies the referenced manifest and decision before binding the activity and assignments. Registration package commits and later specialist/output commits do not advance the code baseline; separately published inputs retain their own exact references. A different baseline or destination requires confirmed re-registration and a manual architecture start. Unavailable or unverifiable saved inputs pause affected work without substitution.

The repository credential profile comes from the operator-provisioned `repository_bindings` configuration under [adapter configuration](#adapter-configuration), not an agent or Execution request. Before the first repository read, registration matches the normalized repository identity to exactly one configured binding, resolves its named `repositories.<profile>` entry, and validates its credential reference and repository allowlist. After destination collection it also checks the branch allowlist and actual required access. Missing, duplicate, unknown or incompatible bindings stop intake with a setup error; the service does not choose among profiles or fall back to an agent credential.

Intake saves `repository_profile`, the binding identity, configuration hash and operator-configuration provenance with the attempt in SQL. The service-built selection Decision records these non-secret references alongside the source/destination selections. Package confirmation activates that exact profile in the project binding after normal publication verification. Initial publication uses the saved attempt profile; architecture and Execution use the confirmed project binding. Re-registration resolves the configured binding for its new attempt and shows any change with the existing source/destination comparison; the prior confirmed binding remains active until replacement confirmation. Recovery retains the original attempt/operation profile and rechecks access without silently adopting a configuration edit.

### Source consistency

Review uses the exact Git commit fixed by [source and publication selection](#source-and-publication-selection), shared by the Maestro architect and Fidelity Reviewer. Relevant input changes are shown before confirmation.

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

### Registration process-definition binding

The service validates the effective `registration` table in `/etc/maestro/agents.toml` using `processDefinition` in [Registration process configuration](schemas/registration-process.schema.json). Installation supplies this configuration-only bundle as `registration-process@1` at `schemas/registration-process/1/schema.json` inside the Maestro installation folder. The registration handler selects this fixed validator before creating an activity; its reference and hashes follow [installed validation schemas](#installed-validation-schemas).

All sections and fixed fields below are required. Only the four numeric settings may be omitted: the review limit, both role durations, and automatic recovery limit. Apply their documented defaults before validation; do not create an omitted section. Reject unknown fields, wrong types, unsupported policy values and legacy keys before starting registration. Booleans are not integers. Shared tool, workspace and storage settings remain outside this table.

| Field within `registration` | Accepted value and behavior |
|---|---|
| `schema_version` | `1`; version of this configuration contract. |
| `maximum_fidelity_reviews` | Positive integer; default and accounting under [review limits and decisions](#review-limits-and-decisions). |
| `architect.run_timeout_seconds`, `fidelity_reviewer.run_timeout_seconds` | Positive integers; defaults under [adapter configuration](#adapter-configuration). |
| `initiation.policy` | `registration_intake_or_idle_update`; apply [intake and scope](#intake-and-scope), including source and both role selections, and the idle reservation rules for [re-registration](#re-registration). Duplicate requests return the existing activity. |
| `initiation.start_operation` | `registration.start`; the existing CLI request operation. |
| `agent_session.policy` | `fixed_assignment_followups`; apply [assignment delivery and clarification](#assignment-delivery-and-clarification). Each run reads a fixed assignment; follow-ups receive saved context, not an assumed persistent session. |
| `agent_session.architect_role`, `agent_session.reviewer_role` | `project_architect` and `fidelity_reviewer`; existing role responsibilities and independent workspaces apply. These are roles, not tool/model defaults. |
| `saved_outputs.policy` | `versioned_registration_package`; validate and publish under [package structure](#package-structure) and [publication and SQL consistency](#publication-and-sql-consistency). |
| `saved_outputs.contract` | `registration_package_v1`; binds the handler to [package record contract](#package-record-contract) and [registration agent response contract](#registration-agent-response-contract). |
| `saved_outputs.root` | `.maestro/registrations`; in the registered project's repository, using its saved authorized destination. |
| `review.policy` | `bounded_independent_fidelity`; apply [assessment and independent review](#assessment-and-independent-review), using this table's single review limit. No mandatory second review after a pass. |
| `confirmation.policy` | `explicit_exact_candidate_activation`; apply [confirmation and activation](#confirmation-and-activation), preserving exact candidate, Owner authority and publication-before-activation checks. |
| `confirmation.on_complete` | `stop`; confirmation starts neither the architecture loop nor execution. |
| `recovery.policy` | `reconcile_preserved_registration`; apply [technical recovery](#technical-recovery), [publication recovery](#publication-recovery) and the existing manual retry actions. |
| `recovery.automatic_recovery_attempts` | Nonnegative integer; default under [adapter configuration](#adapter-configuration). Agent assignments and publication operations use the same configured maximum with separate counters; neither consumes the other's allowance. |

These names select implemented registration handlers; configuration cannot replace their semantic checks or grant additional authority. The `registration_package_v1` output contract is a handler contract, not a claim that a complete output JSON Schema bundle exists. The supplied registration-process schema validates configuration only. Required record and response validation remains mandatory in the handler; a missing validator blocks the affected process rather than accepting unchecked output.

Save the effective table, its hash and validator reference with the activity under [shared process definitions](#shared-process-definitions). Clarifications, candidate amendments, manual retries and restarts retain that snapshot and consumed counts. Registration has no separate automatic output-correction allowance: response-format failures use technical recovery, while substantive amendments follow the existing fidelity-review rules. Architecture-loop correction settings cannot be copied into registration.

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

Readiness after the first passing review does not require another review. At the saved limit, unresolved material blockers or disagreement pause registration for an Owner decision. The service neither forces approval nor resets the count. Another review requires an explicit one-attempt Owner grant under [Owner decisions at a process limit](#owner-decisions-at-a-process-limit), recorded separately from the original limit.

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

The manifest contains `project_id`, `registration_version`, `candidate_id`, `previous_registration_ref` or null, `source_repository`, `source_commit`, `overview_path`, `decision_version`, `content_hash`, and `files`, plus the selection fields defined under [source and publication selection](#source-and-publication-selection). Each file entry contains its relative path, record identity/type/version/subject, and SHA-256 of its exact UTF-8 bytes. The manifest does not list or hash itself.

To calculate `content_hash`, the service sorts summary, declaration, naming-convention, milestone, requirement, assessment, and decision files by path. Each inventory entry contains `path`, a tab, the file hash, and a newline. Review files are excluded so the reviewed content's hash does not depend on the review itself. The manifest's SHA-256 identifies the complete candidate, including its reviews. Hashes identify exact saved bytes, so formatting changes also create a different candidate.

Python checks required fields and types, unique identities and paths, hashes, references, source/decision consistency, and review coverage before publication. Absolute paths, parent traversal, duplicate record identities, and references to nonexistent records are rejected. Agent-written hashes and readiness claims are checked independently.

Changing reviewed content creates a new candidate. The affected content must be reviewed within the existing budget. Unchanged records keep their versions; changed records increment theirs. A focused recheck identifies the previously reviewed content, the review coverage that still applies, and the corrected findings. The service must verify review coverage for the entire new candidate; an old approval alone cannot approve a new hash. Rejected candidates remain retrievable and are never overwritten.

### Publication and SQL consistency

SQL stores live activity, requests, budgets, and the reference to the active version. GitHub stores published packages and confirmation records. A single transaction cannot be assumed to update both systems. The runtime therefore saves each publication operation and verifies its GitHub result before reporting success.

#### Candidate publication

1. Validate and freeze the candidate in service-owned storage. Save its manifest hash, file inventory, intended repository/branch/path, and a unique publication operation in SQL before network writes.
2. Publish the complete candidate in one Git commit on the branch recorded under [source and publication selection](#source-and-publication-selection). Never publish a partial folder as a usable package.
3. Verify the remote commit, all expected file bytes and hashes, permitted paths, and unchanged frozen content using wrapper checks.
4. Save the verified commit and package reference in SQL, then emit the recorded publication result.

A registration package reference uses the shared `registrationRef` definition in [the schema bundle](schemas/architecture-loop.schema.json): `repository`, `commit`, `registration_version`, `candidate_id`, `manifest_path`, and `manifest_sha256`. Registration emits this exact object; the architecture loop consumes it unchanged. The commit identifies the published candidate, not the assessed code baseline. The service verifies the manifest bytes and candidate/version identity in that repository, and compares all fields with the SQL-confirmed reference before architecture entry. The same shape applies to previous-registration references when present and to `registration_ref` and `validated_registration_ref` throughout architecture records. All later review, confirmation, and downstream use bind to this reference rather than branch HEAD or a mutable latest path. Publication does not activate registration.

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

One request cannot create multiple confirmations or activation events. The service resolves pending operations before accepting another write for that project. Publication recovery uses `registration.recovery.automatic_recovery_attempts` under [registration process-definition binding](#registration-process-definition-binding), with a separate counter for each operation. The initial write is not an automatic recovery attempt; reserve and count each automatic replacement write once before dispatch. Queries, matching-content reuse and SQL-only replay do not consume another write attempt. An uncertain GitHub outcome must be reconciled before another write; exhausting the write allowance does not prevent read-only reconciliation. It does not consume agent-launch retries or fidelity reviews, and a failed push does not rerun the architect. Reaching the limit pauses publication and preserves its evidence. Investigation and retry continue that operation without starting a new registration.

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

A tool or API may retry internally within the same run, but these retries do not extend its duration or consume Maestro's launch-recovery allowance. Their count and reasons are recorded separately when available. Only launching an automatic failure-recovery replacement consumes a Maestro recovery attempt; capacity continuations follow [context management](#checkpoints-and-safe-continuation) without consuming that allowance; checking supervisor state and replaying events do not. The supervisor enforces the deadline even when the tool does not report its internal retry count.

#### Activity retry request

The paused registration activity displays **Retry activity** alongside the failure reason and any known correction. It requests a short description of the intervention, then submits `registration.retry` through `POST /api/v1/requests`. This is an explicit activity action, not a slash command or ordinary answer.

The existing request envelope supplies `request_id`, `project_id`, `activity_id`, `expected_version`, and null `question_id`. For an agent retry, its `payload` contains `assignment_id`, `failed_run_id`, and nonempty `intervention`. The text records what changed; it is not proof that access, model availability, or configuration is now valid.

In one SQL transaction the service validates that the activity is technically paused, the referenced run is the current failed run, termination is confirmed, and no retry is pending. It saves the intervention and reserves one manual run under the same assignment. Capability/access checks must pass before the agent starts. A failed check returns the activity to its explained paused state without resetting counters.

For a paused publication retry, the payload instead contains `publication_operation_id` and nonempty `intervention`; agent run fields are absent. The service validates the current operation and reserves reconciliation once under the same request identity. It queries GitHub before any write and applies [publication recovery](#publication-recovery), without launching an agent or resetting the publication counter. Each manual request permits one further write attempt after reconciliation; another failure pauses again. The view labels this action **Retry publication** so its effect is explicit.

An identical request replay returns its saved receipt. Conflicting content or a stale activity/run returns 409; no extra launch occurs. A lost acknowledgment displays **Outcome not confirmed** and is reconciled through the existing request-status endpoint. Reconnection never resubmits automatically. Cancellation, a passing result, or a fidelity disagreement cannot be bypassed with technical retry.

#### Adapter configuration

The runtime reads `/etc/maestro/agents.toml`. Installation supplies this file. A missing file, invalid TOML syntax, or invalid shared launch settings disable all agent launch with a plain configuration error. In an otherwise valid file, a process-specific definition error blocks only new activities for that process. Read-only CLI views remain available.

| Setting | Meaning |
|---|---|
| `workspace_root` | Absolute workspace root; default `/var/lib/maestro/workspaces`. |
| `registration.recovery.automatic_recovery_attempts` | Nonnegative integer; default 2; preserves the existing registration assignment recovery accounting. |
| `registration.architect.run_timeout_seconds` | Positive integer; default 1800. |
| `registration.fidelity_reviewer.run_timeout_seconds` | Positive integer; default 1800. |
| `tools.codex.executable`, `tools.claude_code.executable`, `tools.qwen.executable` | Absolute installed tool paths. |
| `tools.<tool>.credential_profile` | Reference to provisioned service credentials, never the secret itself. |
| `tools.<tool>.settings_profile` | Reference to service-managed tool settings and permitted operations. |
| `tools.<tool>.allowed_model_ids` | Full provider identifiers allowed for explicit role selection; not default model choices. |
| `repositories.<profile>.credential_profile` | Provisioned service Git credential reference used by registration, architecture and Execution publication/merge operations when the saved project binding selects that profile. |
| `repositories.<profile>.allowed_repositories`, `.allowed_branch_patterns` | Required allowlists checked before every service Git read or write. |
| `repository_bindings.<binding_id>.repository`, `.profile` | Operator-provisioned normalized repository identity and named `repositories.<profile>` entry. Exactly one binding may match a repository. Registration collects and saves it under [source and publication selection](#source-and-publication-selection); it contains no secret. |

Effective tool configuration is hashed and recorded for each assignment/run. Tool-setting changes affect new runs after validation, never a running agent. Process behavior is fixed by the activity snapshot under [shared process definitions](#shared-process-definitions). Changing configuration does not reset an assignment's recovery count. No duration default is assigned to other planning or execution roles. The registration fidelity-review setting in [review limits and decisions](#review-limits-and-decisions) is stored in the same file but has separate accounting and is fixed for each registration attempt.


## Architecture loop

### Entry and responsibility

The architecture loop is a Planning process started with `/architecture start` for the selected project after confirmed registration. No selection prompts project selection. `/architecture` opens its current activity or latest confirmed breakdown without starting work. Confirmation of registration never starts this loop automatically.

Start requires no unfinished work on that project: reserved or queued assignments, running agents, work waiting for answers or review, pending saves or external operations, and uncertain stopping or recovery all prevent entry. The CLI explains the blocking activities. A repeated start request opens the existing unfinished architecture activity rather than creating another session.

The service uses the shared project start lock to check eligibility and reserve the project atomically. Only that architecture activity's assignments and operations may start while reserved; execution and re-registration cannot start for the same project. Other projects continue normally. The reservation remains until the loop ends and its runs and pending operations are resolved. The loop reads the exact confirmed registration and develops the work needed for its outcomes. Its code baseline and publication destination follow [source and publication selection](#source-and-publication-selection).

The architect checks information sufficiency, investigates existing code, establishes project structure and specialist guidance, and produces development milestones and work packets. It designs dependencies and opportunities for parallel work. Execution owns scheduling and subsequent implementation.

### Persistent architect session

The service starts a persistent architecture agent session for the loop. The session retains context while reading registration files, investigating code, handling answers, creating the breakdown, and responding to review findings. The independent reviewer uses a separate session and does not share authorship.

Persistent context is not the only record of the work. Findings, decisions, questions, answers, project structure, specialist definitions, breakdown versions, and review results must be saved so the loop does not depend on the agent remembering them. The service records activity and clarification through the existing SQL-first flow before presenting updates in the CLI.

Initiation explicitly selects Claude Code or Codex and the architect's exact model/version, with a separate reviewer selection. Apply the existing exact-model and capability checks. The architect keeps the same session through clarification and review corrections; the reviewer remains independent.

When that session is unavailable, a replacement may continue with the same role and exact model from verified saved records. It preserves completed investigation, decisions, outputs, and review counts. Uncertain completed work pauses the loop with a specific explanation instead of triggering a fresh investigation. Session memory never overrides authoritative records.

Each active architect or reviewer run has a separately configurable 30-minute default. Waiting for Owner answers or confirmation does not consume active-run time. The service records run deadlines and waiting states; restart cannot create extra running time. The persistent session can span multiple bounded active runs.

#### Persistent-session adapter contract

One service session identity binds the project, activity, role, selected tool/model, source baseline, tool conversation ID, and tool-state location. Only one active run may use it. A reviewer receives a different session and read-only copies of exact reviewed inputs; it never resumes the architect's conversation.

The workspace root contains `<project-id>/<activity-id>/sessions/<session-id>/`. Each session has a stable `source/` working directory, immutable `input/<assignment-id>/` snapshots, retained tool state, and `runs/<run-id>/output/` plus scratch. The service fixes tool state to that session's configured profile/location; a profile shared across project conversations is not used for lookup. Each run grants write access only to its own output/scratch and tool-required session storage. Prior outputs and supplied inputs remain read-only; session storage is untrusted conversation history, never an authoritative output. The supervisor retains its existing spool and control-group tracking.

| Tool | First run and subsequent runs |
|---|---|
| Codex | Start App Server over stdio and perform `initialize` then `initialized`. First use `thread/start` and record the returned thread ID; subsequent processes use `thread/resume` with that exact ID. Submit `turn/start` with the thread ID, selected model, fixed working directory, current assignment-file instruction, and response `outputSchema`. Record its turn ID. |
| Claude Code | First invoke print mode with a service-assigned UUID through `--session-id`. Later invoke print mode with `--resume <exact-session-id>`. Every invocation supplies the explicit model, `--output-format stream-json`, `--verbose`, `--json-schema`, and the current assignment-file instruction. Record and verify session metadata. Never use latest-session lookup or `--continue`. |

These selected operations follow [Codex App Server](https://learn.chatgpt.com/docs/app-server), [Claude programmatic operation](https://code.claude.com/docs/en/headless), and the [Claude CLI reference](https://code.claude.com/docs/en/cli-reference). Installed-release capability checks remain required; documentation does not prove a route works on the AI box. The adapters preserve the existing exact-model and permission checks on every run.

For Codex, correlated `turn/started` and item/delta events record activity; only a matching successful `turn/completed` allows final response validation. An interrupted or failed turn is not completion. For Claude, `system/init` identifies the session/model; assistant and streaming events are progress. Only a terminal successful `result` containing `structured_output`, followed by process completion, allows validation. Inner tool messages, partial JSON, or an agent saying it is done cannot complete the assignment.

Each active run receives a newly saved immutable assignment file. The prompt explicitly identifies that file and the authoritative input references; resumed historical instructions do not replace it. Answers are saved and delivered only in the next assignment, not injected into an active turn. Context compaction cannot change authoritative records.

The runtime starts a run's deadline when it reserves and launches that run, covering startup and internal provider retries. Mechanical allocation exchanges remain within that same active-run deadline; they cannot create unlimited fresh turns. It stops/releases the run after collecting terminal output, draining the spool, and verifying child termination. The Codex process may end between turns while its disk-backed thread persists; the next process resumes that exact thread. A saved clarification response plus confirmed stopping enters `waiting_for_answers`. Waiting for review or confirmation likewise has no running architect. Silence, a quiet stream, or provider backoff never counts as waiting for the Owner and never suspends a deadline.

| Accepted result or event | Service state and next action |
|---|---|
| New eligible activity | `preparing`, then `running` after launch reservation. |
| Terminal response | `validating`; schema, context, output, and stale-data checks run before advancement. |
| Valid partial or completed outputs | `publishing`; only verified publication updates the working reference. |
| Clarification | Save specific linked questions and partial verified work, stop the run, then `waiting_for_answers`. Resume when required answers for the next step are available. |
| Ready breakdown | Stop the architect, then `waiting_for_review`; launch the independent assignment within the saved budget. |
| Valid review coverage and eligible working version | `waiting_for_confirmation`; only the explicit Owner action advances. |
| Error or uncertain process/publication state | `paused`, with reason and eligible recovery action. |
| Cancellation | `cancelling` until processes and writes reconcile, then `cancelled`. |
| Applied confirmation | `completed`; execution remains unstarted. |

Recovery first checks the original supervisor, spool, and SQL launch record. It does not resubmit an uncertain turn or start a second process against the same session. After confirmed stopping, resume a usable conversation with the same tool/model. If the conversation is unusable, record a replacement session linked to the prior one and reconstruct only from verified assignments, decisions, manifests, and saved answers. A validated response already recorded is not generated again. Unknown completion pauses rather than guessing. Reattaching to the same run preserves its deadline. A permitted new failure-recovery replacement or retry run gets its own configured duration; capacity-only continuation retains the remaining budget. Both preserve assignment, retry, correction, and review accounting; the distinction is defined under [run deadlines and duration exceptions](#run-deadlines-and-duration-exceptions).

#### Architecture assignment and response contract

[Architecture-loop JSON Schema](schemas/architecture-loop.schema.json) defines the exact version-1 shapes. Its `assignment` and `agentResponse` definitions are separate from registration's contract. All declared properties are required unless explicitly nullable; unknown properties are rejected. Output references use paths relative to the assigned output root. The service validates full schemas itself even when a provider needs an equivalent bundled response schema with local references expanded.

Assignments contain fixed identities, the selected role/tool/model, source and registration references, recorded decisions and answers, current manifest/input references, required output paths and schemas, writable paths, remaining allowances, definition hash, and deadline. They identify the task as investigation, breakdown, amendment, or independent review. Service-owned IDs, subjects, versions, and paths are supplied in `required_outputs` before output creation. If more records are needed, the agent returns `allocation_required` with `allocations`: unique local keys, proposed subjects, record types, and a source area for specialist records. The service validates these against scope, reserves stable sequential IDs and permitted paths, and returns `allocation_bindings` in the next assignment. Replaying the same allocation keys returns the same bindings. This mechanical exchange is not an Owner question, correction attempt, or fidelity review, and cannot extend an exhausted assignment deadline.

The agent returns the assigned identities, session, source and decision version, input manifest, a plain summary, findings/questions, output artifact references, and one result: `completed`, `clarification_required`, `allocation_required`, or `technical_failure`. Reviewer results also identify `reviewed_set` and `review_outcome`. Progress remains a separate event stream.

| Semantic validation | Required behavior |
|---|---|
| Completed architect | Required task outputs exist at assigned paths; `reviewed_set` and `review_outcome` are null. Completion of an assignment does not approve the loop. |
| Completed reviewer | Exact assigned set and coverage are identified. APPROVE has no blocking finding or unresolved required question; REQUEST_CHANGES contains a justified blocking finding. |
| Clarification | At least one specific question; no review approval. Verified partial outputs may be saved. |
| Allocation required | Nonempty allocation requests, no review outcome or failure; other result types have an empty allocations array. Allocate only within assigned scope and return the bindings automatically. |
| Technical failure | Failure code/message present; no review approval or completed-work claim. |
| All other results | `failure` is null. Identity, source, input manifest, role, and allowed outputs match the assignment. |
| Duplicate response | Canonically equal already-accepted content returns its saved receipt; conflicting or stale output cannot overwrite current records. |

Use the common finding/question meanings already defined for registration, with the exact architecture schema fields. Empty optional lists remain arrays; an inapplicable scalar/object is null only where the schema allows it. Technical errors go through bounded correction/recovery, not a substantive fidelity rejection. Review counts change only for accepted completed reviews.

### Architecture API operations

The existing `/api/v1` request envelope, error statuses, SQL-first events, and request reconciliation apply. The schema's `request`, `receipt`, and `view` definitions supply exact architecture payloads and results.

| Interface | Required action and result |
|---|---|
| GET `/projects/{project_id}/architecture` | Return the current activity or latest confirmed breakdown and authoritative working/confirmed references; `data: null` means none exists. Reading starts nothing. |
| `architecture.start` | Require project and exact active registration reference, architect selection, and separate reviewer selection. Activity, question, and expected-version fields are null for this request. Check/reserve idle state atomically and return the created activity. An existing unfinished architecture activity is returned without changing its inputs or selections. |
| `architecture.confirm` | Require activity, expected activity version, and exact expected working reference plus explicitly accepted limitation references. Apply the existing version comparison and publication journal. |
| `architecture.cancel` | Require activity, expected activity version, and a plain reason. Record the cancellation request, then stop/reconcile before reporting it complete. |
| `architecture.retry` | Require activity and expected activity version. Payload targets `agent` with assignment ID or `publication` with operation ID; the other ID is null. Require recorded intervention text and current retry eligibility. It does not replenish automatic budgets. |

The start form collects any missing exact selections before submission using the existing explicit form interaction. A historical registration reference cannot start new work. Conflicting source/selection data on a different start request for an existing activity returns that activity with its actual recorded inputs; it never silently reconfigures it. Same request ID with different content returns 409.

`expected_version` on architecture actions is the activity's positive integer revision, incremented for accepted state/action changes. Questions still use the existing `question.answer` operation and question version. Confirmation separately compares the full working reference and content hash. Receipt status describes the submitted operation, not approval of all project work.

The activity view exposes state, current references, review count/limit and coverage validity, blocking reasons, eligible actions, and the allowance/decision fields under [Owner decisions at a process limit](#owner-decisions-at-a-process-limit). Detailed questions/findings remain in the existing activity detail and conversation endpoints. During pending publication/confirmation, source-changing actions cannot advance. Stale context returns 409 with current references for refresh; malformed payloads, access failures, missing records, and unavailable service use the existing error map. Request replay and SSE refresh never start duplicate runs.

Manual retry uses the registration principle of one intervention-backed additional run after confirmed stopping, preserving automatic recovery and correction accounting. It cannot bypass an exhausted output-correction or fidelity allowance; additional allowance requires an explicit recorded Owner decision. The action is unavailable when its conditions are unmet.

### Architecture schema and process-definition binding

The JSON Schema bundle is the authoritative field/type contract; prose defines semantic checks and process transitions. Required record names and paths remain those under [architecture output locations and records](#architecture-output-locations-and-records). Validate project identity, current manifest/assignment context, unique identities and paths, valid dependency links, no prerequisite cycles, and exact inventory hashes. A record's activity, registration, and source fields describe its origin. Newly authored records match the current assignment; unchanged carried-forward records retain their original metadata and versions. Each retained record has a manifest `carried_forward` entry with its exact published reference, the current registration/source against which applicability was checked, and the reason it remains valid. This does not authorize stale inputs: changed dependencies still invalidate affected work and review coverage. Specialist records must match assigned source-local paths and ownership; JSON path validation alone is insufficient. Markdown role files begin with the role title and contain `Responsibility`, `Authority`, `Source area`, and `Inputs and outputs` headings. Context files contain `Verified facts`, `Source references`, and `Knowledge gaps`; optional memory files contain dated `Entries` with verified facts and source references. Their identity, version, and ownership are recorded in the manifest, not invented in prose.

For `reviewed_content_hash`, build an object containing `registration_ref`, `source_commit`, `decision_version`, the within-set `decision_ref`, sorted `input_refs` and `carried_forward` entries, and the manifest inventory excluding review and confirmation entries. Sort inventory by repository-relative path and then identity; sort dependency/reference arrays by path, identity, and version. Sort carry-forward entries by their record reference's path, identity, and version. Include specialist commit references; set same-publication inventory commits to null. Serialize with [RFC 8785 JSON Canonicalization](https://www.rfc-editor.org/rfc/rfc8785) and hash its UTF-8 bytes with SHA-256. Individual file hashes cover the exact saved bytes. Reject duplicate JSON keys, invalid Unicode, and unsupported schema versions rather than normalize away a mismatch.

The `processDefinition` schema validates the effective `architecture_loop` TOML table after the documented optional numeric defaults have been applied. Its supported policy names bind to the handlers specified above; they are not arbitrary code. Required section policies are `confirmed_registration_idle_project`, `persistent_exact_session`, `versioned_architecture_set`, `bounded_independent_fidelity`, `exact_reviewed_working_version`, and `reconcile_preserved_work`. Shared tool settings stay outside this process table. The effective table and schema version are hashed and snapshotted before initiation.



### Initial code investigation

The architect investigates relevant existing source code when the loop starts, using the confirmed outcomes to bound the investigation. It examines responsibilities, interfaces, dependencies, setup, and actual connections before defining the work.

| Finding | Required result |
|---|---|
| Existing code supports the outcome | Identify the code, supporting evidence, and any integration or verification still needed. |
| Existing code needs changes | Explain what must change and why; carry the changes into the breakdown. |
| Replacement or retirement is the stronger path | Record the reasoning, affected dependencies, and work needed to preserve the required outcome. |
| A capability or prerequisite is missing | Include the necessary work or raise clarification when the decision is outside the architect's authority. |

Reuse is not presumed preferable to replacement. The architect chooses the strongest path to the intended outcome based on the investigation. Source inspection establishes what the code supports; it does not by itself prove operation. Actual code changes, moves, and retirement are execution work.

### Lasting project structure and specialist guidance

The architect creates an AI-friendly project structure that makes feature locations, shared code, responsibilities, and boundaries clear to other agents. For existing source, the structure identifies both current locations and intended changes so a proposed layout is not mistaken for code already moved.

The architect also creates specialist agent definitions for the code areas that need that expertise. Each definition contains the role description, responsibility boundary, and starting context with established findings and relevant source references. Role files and any maintained memory files belong within the source tree, close to the feature or code area they cover. Creating a specialist definition does not dispatch a worker.

Specialists build knowledge through subsequent work. Starting context distinguishes established facts from gaps; specialist status does not imply knowledge that has not yet been acquired. Useful discoveries can update maintained context without recreating the role or project structure.

Code-direction findings, the project structure, and specialist definitions are persistent project records. Subsequent passes use them instead of generating replacements from scratch. Replanning governs changes to established structure and direction; reasons and affected records remain traceable. Memory updates preserve relevant knowledge rather than silently changing architectural decisions.

The architect applies [whole-product architectural evaluation](#whole-product-architectural-evaluation) throughout this work and owns code best practices and architectural consistency. It applies established patterns where they fit, defines clear responsibilities, and keeps unnecessary duplication low through appropriate shared code. These decisions are carried into the structure, specialist guidance, and packet requirements. Shared abstractions must serve a concrete need without unnecessary complexity.

### Information sufficiency and clarification

Before declaring the breakdown ready, the architect confirms that the information can support the promised outcomes. Routine technical choices within the agreed scope remain the architect's responsibility.

Questions affecting intended outcomes, scope, conflicting requirements, or Owner-reserved decisions go through the service. The service saves the questions, presents them through the CLI, records answers and follow-ups, and returns the relevant information to the persistent architect session. The architect amends the affected records, packets, and milestones. Missing information is not replaced by an unsupported assumption.

This follows registration's linked clarification pattern. Answers remain associated with their project, activity, and question; a clarification answer is not confirmation of the breakdown.

### Work-packet-first breakdown

The architect designs the smallest bounded work packets first, then organizes them into development milestones. Each packet has a clear scope, expected result, and completion criteria. Smallest bounded means a meaningful contribution that can be implemented and assessed sensibly; arbitrary fragmentation does not improve the breakdown.

Development milestones may differ from project milestones. Their relationships must still show how all confirmed project outcomes will be delivered. Grouping work differently does not change the approved scope.

Parallel work is a first-class design concern. The architect identifies independent contributions, shared-code boundaries, integration points, and explicit dependencies so execution can use parallelism effectively. The breakdown describes what may run independently and what must precede other work; it does not assign start times, reserve execution slots, or schedule workers.

Packet requirements include necessary setup, access, integration, and basic verification. Completion criteria describe the usable result and its essential failure behavior, using the [Planning Guide's verification expectations](planning-guide/README.md#verification-expectations). Disconnected components or passing fake-data checks do not establish the promised capability.

### Architecture output locations and records

The registered project's GitHub repository holds versioned architecture documents. SQL holds activities, authoritative working and confirmed references, assigned versions and hashes, questions and answers, review and correction counts, and pending operations. The local workspace is an assigned working copy, not the authority.

The output contract supplies exact filenames and paths to agents. Agents cannot invent alternative names, rename files, or create differently named replacements. The runtime rejects unexpected paths and names. An authorized rename must update the contract, manifest, and affected references explicitly.

| Repository path | Required content |
|---|---|
| `.maestro/architecture/index.json` | Discovery links to published versions; not an alternative to SQL's authoritative references. |
| `.maestro/architecture/versions/<version>/manifest.json` | File inventory, record identities and subjects, versions, exact references, hashes, and dependencies. |
| `.maestro/architecture/versions/<version>/investigation.json` | Code findings, source evidence, code-direction decisions, and reasons. |
| `.maestro/architecture/versions/<version>/decisions.json` | Service-generated snapshot of architectural decisions supporting this version. |
| `.maestro/architecture/versions/<version>/project-structure.json` | Current and intended code locations, ownership, shared components, and specialist-file references. |
| `.maestro/architecture/versions/<version>/development-milestones/<milestone-id>.json` | One record per development milestone. |
| `.maestro/architecture/versions/<version>/qa-plans/<milestone-id>.json` | One Quality Assurance plan per development milestone. |
| `.maestro/architecture/versions/<version>/work-packets/<packet-id>.json` | One record per bounded work packet. |
| `.maestro/architecture/versions/<version>/reviews/<review-id>.json` | Independent findings and exact reviewed references. |
| `.maestro/architecture/versions/<version>/confirmation.json` | Owner confirmation of the exact eligible breakdown. |

Version values and record identifiers are assigned by the service under the naming conventions. Filenames use assigned identifiers; record contents, references, and displays pair each identifier with its plain subject. No agent-chosen numbering is permitted.

Specialist files live under `<source-area>/.maestro/`. The fixed role filename is `role-<role-title>.md`, with lowercase words separated by hyphens, such as `role-registration-architect.md`. The architect assigns and records the exact title and path. `context.md` contains starting context and maintained knowledge; `memory.md` is optional. Each context/memory path has one recorded specialist owner; a colliding ownership request must be resolved explicitly rather than overwriting another specialist's file.

The architect maintains the role definition and creates starting context. Specialists may update their assigned context and memory during execution with verified discoveries and source references, without changing role authority, scope, or architectural decisions. Updates are committed and compare the expected current file version before writing. A conflict prevents overwrite and returns the current reference for reconciliation. This is a bounded knowledge-maintenance permission, not general merge or execution authority.

#### Architecture record contract

JSON records use `schema_version: 1`. Common record metadata contains `project_id`, `activity_id`, `id`, `subject`, `version`, `registration_ref`, and `source_commit`. Other published record references use `publishedRef`: identity and subject, version, repository-relative path, SHA-256, and exact Git commit. Registration package references instead follow [candidate publication](#candidate-publication); they are not converted to generic file references. Within one output set, links use identity, subject, version, and relative path; their hashes resolve through the manifest inventory. This avoids circular hashes between a milestone and its packets. The publishing commit is supplied by the set's verified publication reference rather than embedded before it exists.

Individual registered outcome references are distinct from the package reference. On architecture entry, the service reads the SQL-confirmed candidate and its verified manifest inventory and converts its milestone/requirement references for `project_outcome_refs` and investigation `outcome_refs`: `record_id` becomes `id`, `record_version` becomes `version`, and `subject` is preserved. Prefix the package-relative path with `.maestro/registrations/versions/<registration-version>/candidates/<candidate-id>/`; take `sha256` from that file's verified inventory entry and `commit` from the exact confirmed package publication reference, not the product source commit or current branch head. The service verifies the file bytes and embedded identity, subject, type and version against the inventory, saves the mapping with architecture inputs in SQL, and supplies it to architect and reviewer assignments. Output validation requires an exact mapping to an included confirmed outcome; missing, mismatched, out-of-scope or stale references block the affected output. Registration's own package-local references and its package-level `registrationRef` remain unchanged. Re-registration requires a newly verified mapping for the new activity while retaining earlier mappings as history.

| Record | Required fields beyond common metadata |
|---|---|
| Decisions | `decision_version` and saved decision entries with identity, subject, version, source question/finding, answer, authority, and affected work. |
| Investigation | `findings` with code locations and evidence, `decisions` with reuse/update/replace/retire/missing-work disposition and rationale, and affected outcome references. |
| Project structure | Current and intended locations, responsibilities, shared-component boundaries, planned moves, and specialist role/context/memory references. |
| Development milestone | `outcome`, `project_outcome_refs`, `included_scope`, `exclusions`, `work_packet_refs`, `qa_plan_ref`, `dependencies`, `integration_points`, and `completion_criteria` for the connected result. |
| Quality Assurance plan | `milestone_ref`, versioned `setup_steps`, `support_processes`, `environment_refs`, `secret_refs`, `allowed_network_dependencies`, `project_binding_hash`, `data_requirements`, `checks`, `artifact_requirements`, `cleanup_steps`, and `reset_check`. |
| Work packet | `purpose`, `project_outcome_refs`, `development_milestone_ref`, `included_scope`, `exclusions`, `permitted_paths`, `starting_context`, `dependencies`, `shared_code_constraints`, `parallel_opportunities`, `execution_requirements`, `completion_criteria`, `verification`, `essential_failure_checks`, and `required_outputs` with exact destinations. |
| Review | Reviewer assignment/run, exact reviewed references and content hash, outcome, justified findings with affected references, and retained prior coverage where applicable. |
| Confirmation | Operation/request identity, Owner identity, timestamp, exact expected working reference and reviewed-content hash, accepted limitations, and supporting review references. |

Starting context names the exact source revision, document references, existing-code findings, and specialist role. Packet dependencies identify prerequisites without scheduling them. `execution_requirements` contains `required_capabilities`, `allowed_locations`, and positive `minimum_context_tokens`. Capability values are the `execution@1` identifiers `code_edit`, `local_command`, `repository_search`, `image_inspection`, and `approved_network`; locations are `local_ai_box` and `cloud`. A packet requests only capabilities its accepted work actually needs. Any approved network destination remains separately constrained by the project's environment and tool policy. A Quality Assurance plan uses only repository-relative script references with exact hashes or argument arrays; each support process names its health condition and port allocation rule. Data requirements identify dataset or generator, hash, classification, sanitization, setup operation, real input path, expected result and actual capability path. Checks identify the user journey, failure cases and required artifacts. Cleanup and reset conditions are explicit. Secret references are names only, never secret values. The service validates the plan during breakdown publication and supplies its exact confirmed version to QA; a changed plan requires a new reviewed and confirmed breakdown version.

A milestone's packet completion is necessary but does not by itself prove the connected outcome; its own completion criteria establish that result. Packet deliverables use the schema's separate `packetDeliverable` shape: plain subject, exact path, format such as Python, TypeScript, JSON, or a named artifact format, and a schema reference or null when not applicable. The architecture-agent `requiredOutput` shape remains restricted to its JSON/Markdown planning artifacts; it does not restrict what code a packet may deliver.

The manifest records every required output's type, path, identity/subject, version, SHA-256, and dependencies, plus the exact registration and input references. Its stage identifies required outputs: foundations require the investigation, decisions snapshot, structure, and assigned specialist files; breakdown additionally requires milestones, their Quality Assurance plans, and packets; reviewed and confirmed stages add their evidence. Saving foundations is not a declaration that a full breakdown is review-ready. Source-local specialist files include exact commit and hash. The manifest does not hash itself. The service calculates `reviewed_content_hash` from a canonical inventory of the investigation, structure, milestones, packets, specialist inputs, and relevant recorded decisions; reviews and confirmation are excluded from that content hash so recording a review does not invalidate itself. The manifest inventory still records review and confirmation files when present. SQL and the discovery index identify the exact publishing commit and manifest hash.

A published content file is immutable at that version. Content amendments create the next output-set version, retaining stable record identities and incrementing changed record versions only. Review records and the single confirmation receipt may be added to a version after its content is published; those additions update the manifest and publication reference without changing reviewed content. Prior Git commits remain available.

### Saved findings and architecture decisions

Response-local finding keys are transport keys only. On first acceptance, the service allocates each finding a stable identity, plain subject, and version, and saves the mapping from assignment/run/local key to that identity. Duplicate results reuse that mapping. Follow-up assignments carry `finding_bindings` from response local keys to existing exact `findingRef` records. Corrections resolve those bindings before allocating any new identity; a new run key alone cannot create a replacement finding. Conflicting or stale bindings fail validation. Corrections preserve identity and increment the finding version only when its content changes; unchanged findings keep their version.

Findings remain embedded in their investigation or review record. Saved records use `savedFinding`; responses use `finding`. A `findingRef` identifies the finding and its version plus the exact containing document's identity, version, path, commit, and hash. The service checks both the container and the nested finding before resolving it. Packets and accepted limitations use this reference, not a guessed standalone finding path.

Agent-authored investigation and review files use `preparedInvestigation` and `preparedReview` in assignment `required_outputs.schema_ref`; their findings use response-local keys. The wrapper verifies the agent's exact-byte artifact hashes and prepared schemas first. Response findings and artifact findings with the same local key must agree. It then resolves existing bindings or allocates new identities, validates the resulting `investigation` or `review` saved schema, and calculates new hashes for the saved bytes. Prepared and saved hashes remain distinct in the operation journal; publication and later references use only the saved hash.

The service performs the local-to-saved mapping before publication. If an agent needs to cite a newly saved finding, publish its containing record first and supply the verified reference in a follow-up assignment before creating dependent records. The service never edits already-published bytes to insert an identity. New versions retain prior references for history and stale-data checks.

Every architecture version includes `decisions.json` at `.maestro/architecture/versions/<version>/decisions.json`. The service builds this snapshot from recorded architectural decisions in SQL; agents do not choose its name or publish a second source of authority. Each decision has identity, subject, version, source question or finding when applicable, answer, authority and identity, and affected work. An architect's routine technical decision may have neither a question nor finding; its recorded authority and rationale remain required.

SQL owns the live exchange and actions; the snapshot captures the exact decisions supporting that output version. The manifest's `decision_ref` is a within-set reference resolved through the inventory hash and the verified publishing commit, avoiding a future-commit dependency. It replaces an unbound list of published decision references. The decision snapshot is included in reviewed content, so changing a supporting decision invalidates affected coverage.

An operational allowance, duration exception, or final confirmation is an action receipt in SQL, not a change to architectural content by itself. Such actions do not rewrite `decisions.json` or trigger another fidelity round unless they change a supporting architectural decision. Confirmation separately records accepted limitations by their exact finding references.

If a new decision cites an unpublished finding, first publish the finding's containing artifact as journaled intermediate work, then create the snapshot with its verified reference before advancing the complete working set. Investigation code-direction entries retain their detailed evidence; the decision snapshot gives the corresponding decision identity and disposition without inventing alternative policy.

### Owner decisions at a process limit

When a review, output-correction, or manual-recovery allowance is exhausted, the service saves a pending decision linked to its activity, exact assignment or external operation, affected work, reason, base limit, used attempts, prior grants, and architect recommendation when one is required. A re-registration work-disposition decision uses the same typed interface but is not an allowance grant.

The canonical linked decision interface is `owner.decision` through POST `/requests`; no process-specific Owner-decision operation or slash command exists. The request includes project, activity, question, expected activity version, decision identity/version, target, assignment or operation identity, selected choice, optional next-run duration, and verified Owner identity.

Stable targets and choices are:

| Target | Permitted choices and effect |
|---|---|
| `fidelity_review` | `grant_one` or `remain_paused` for registration or architecture-loop fidelity review. |
| `output_correction` | `grant_one` or `remain_paused` for an architecture-loop correction assignment. |
| `execution_packet_review` | `grant_one` or `remain_paused` for the exact packet review; the packet stays unapproved and any queue entry stays ineligible until it passes. |
| `execution_integration_change_review` | `grant_one` or `remain_paused` for the exact Integration Manager change review; a blocked FIFO head remains at the head. |
| `execution_milestone_review` | `grant_one` or `remain_paused` for the exact milestone outcome review; the milestone remains ineligible for promotion. |
| `execution_support_fidelity_review` | `grant_one` or `remain_paused` for the exact architectural-support assignment's role/context review; affected packets remain blocked until reviewed activation. |
| `execution_manual_retry` | `grant_one` or `remain_paused` for the exact failed assignment or journaled external operation after recorded intervention. |
| `execution_work_disposition` | One of `continue_unaffected`, `finish_safe_work`, `stop_affected_or_all`, or `finish_current_for_replanning`; effects are defined under [work disposition before re-registration](#work-disposition-before-re-registration). |

For review and correction targets, the CLI offers `grant_one` or `remain_paused`; neither is preselected. An Execution review grant is created only after the applicable architect recommendation has been saved. It adds one completed-review allowance to that exact assignment and review type. It cannot force approval, move a FIFO entry, make a milestone mergeable, transfer to other work, or change scope. Choosing `remain_paused` preserves the blocker and current queue/milestone state while unrelated eligible work continues.

For `execution_manual_retry`, automatic recovery must be exhausted or a recorded intervention must establish why another run or operation is now appropriate. The pending decision binds the failed run or journal operation, failure classification, intervention evidence, original configuration snapshot, remaining configured manual-retry maximum, and any proposed next-run timeout. A grant may approve that positive timeout for the next run only; otherwise the snapshotted timeout remains. The service never creates more manual grants than `execution.recovery.manual_retry_attempts` for that assignment or operation.

In one SQL transaction, the service validates the pending decision, context, expected versions, target-specific choice, authority and remaining allowance, then saves the Owner action. A grant becomes a single unconsumed grant record. `execution.retry` atomically reserves that record against its idempotency key. Agent preflight failure before launch, or external preflight failure before a journal attempt, releases the reservation without consumption. Confirmed agent launch or transition of the exact external operation to attempted consumes it. A lost response returns the saved reservation or attempt; another request cannot reuse the grant.

Effective review allowance is the snapshotted base limit plus recorded grants minus completed rounds. A consumed decision cannot grant another attempt under a different request ID. For manual retry, another decision exists only while the snapshotted manual-attempt maximum remains. For review or output correction, a new decision may be created only after the previously granted allowance was consumed and the same exact work remains blocked; every extra round still requires a new explicit Owner action. Conflicting or stale submissions return 409 with current state. Work-disposition decisions change restrictions, not review or retry counts.

Registration uses this handler for fidelity-review grants; the architecture loop uses it for fidelity-review and output-correction grants; Execution uses it for packet, integration-change, milestone and architectural-support review limits, manual retry, and re-registration disposition. The Execution-specific targets and response validation belong to `execution@1`; they do not extend the architecture-loop schema's process-local target enum. Registration response corrections retain their existing technical-recovery budget and `registration.retry` action. Cancellation, pause, stop and restart preserve every grant, reservation and consumption record.

After the saved receipt, the CLI refreshes the authoritative activity view to obtain base limits, grants, consumption, remaining allowance, and `owner_decisions`. Linked free-text answers cannot create a grant or disposition.

### Run deadlines and duration exceptions

Recovering supervision of the same run preserves its original deadline. Except for capacity continuations, which retain the remaining work-phase budget under [context management](#checkpoints-and-safe-continuation), starting a new permitted retry or replacement creates a new run identity and a full active-run allowance from the activity's saved duration, 30 minutes by default for the configured planning roles. Waiting for the Owner consumes no active-run time. Internal provider retries and mechanical allocation exchanges stay within their run's deadline. None of these operations reset assignment-level attempt counters.

After timeout, stopping must be confirmed and investigation or intervention must justify another run. A duration change for the current activity requires a separate pending Owner decision with target `run_duration`, assignment, proposed positive `duration_seconds`, and reason. Its choices are `set_next_run_duration` with the proposed positive duration or `remain_paused` with null duration. The same credential, version, replay, and transaction checks apply.

An accepted exception applies only to the next eligible run of that assignment. It does not extend an active or expired run, replenish attempts, or change the activity's original configuration. The launch transaction consumes the exception once and records the applied duration/deadline. New configuration values otherwise affect only future activities. If retry allowance is also exhausted, a duration exception alone cannot authorize another attempt.

### Replanning after re-registration

Replanning can occur only after re-registration has been confirmed. It has no independent command, automatic trigger, or separately delegated entry. Re-registration first requires no unfinished project work under its existing idle-only rule.

A subsequent manual `/architecture start` reconciles the existing breakdown with that newer confirmed registration. Preserve valid investigations, project structure, specialist guidance, milestones, and packets; revise only affected records and dependent work. Review and exact-version confirmation use this architecture loop's existing rules. Execution still requires its separate manual start.

Routine clarification, necessary corrections within the current registration, session recovery, and a restart after cancellation continue the same agreed work; they cannot be used to change established scope or direction without re-registration. If a completed breakdown is already based on the current registration and no cancelled work needs continuation, another start returns that breakdown rather than creating an independent replan. Proposed changes requiring replanning remain recorded issues until re-registration is confirmed.

### Current versions and stale-data prevention

SQL stores two separate references: the current working version, which is the latest validated and published work used for continuation and review, and the confirmed version approved by the Owner. Saving work never grants confirmation.

Each assignment records its exact registration, source baseline, input versions, paths, and hashes. Before accepting output or resuming a session, the runtime verifies those dependencies against their authoritative references. Stale results cannot overwrite current work. Missing or mismatched files pause affected work instead of causing guessed filenames or silent recreation.

Changes mark affected dependent records as needing revision and invalidate affected review coverage. Unaffected records and valid coverage carry forward. Comparing relevant input identities and hashes—not merely a change to repository HEAD—determines staleness; publishing the activity's own documents must not invalidate its unchanged source baseline.

A later confirmed registration preserves the prior breakdown as history but marks affected milestones and packets as needing architectural review. Affected work is ineligible for execution until reconciled. The architect carries forward unaffected work and revises only what changed requirements demand. This does not regenerate work or start the architecture loop automatically; its manual start and idle checks still apply.

### Deterministic packet checks and correction

Before independent review, the wrapper checks required fields and formats, identifier/subject references, permitted paths, dependency resolution, assigned input validity, required outputs, and required GitHub commit evidence. It checks observable requirements only; it does not judge whether the architecture will deliver the promised outcome.

The wrapper returns precise errors through the service to the architect, identifying the failed rule and affected output. The architect corrects its output; the wrapper reruns the affected checks and directly related references before review. The wrapper may assign service-owned identities and calculate hashes. It must not guess requirements, rewrite scope, or select replacement dependencies.

Automatic output correction has its own configurable maximum of two attempts per architect assignment. An actual correction attempt consumes the allowance; simply rerunning checks does not. These technical corrections do not consume fidelity review rounds. Returning the same error without a relevant correction pauses early. At the limit, preserve the outputs and show the unresolved error. Recovery, reassignment, or activity restart cannot reset the allowance for the same unresolved work.

### Independent review and amendments

Agent assignments and review use the same general practices as registration: explicit inputs and authority, deterministic wrapper checks where applicable, independent fidelity judgment, recorded clarification, and architect amendments. This does not import registration-specific package schemas, activation rules, timeouts, or retry settings.

The independent reviewer checks the investigation, persistent foundations, and breakdown against the confirmed registration and recorded decisions:

- Every confirmed outcome has development-milestone and work-packet coverage.
- Each packet has bounded scope, an expected result, and clear completion criteria.
- Dependencies, integration points, and opportunities for parallel work are explicit.
- Existing-code decisions have supporting findings and are reflected in the work.
- Setup and essential connections are included so the combined result is usable.
- Project structure, specialist guidance, and architectural quality decisions are consistent with the breakdown.

The architecture loop has its own configurable maximum of **two fidelity reviews by default**, separate from registration. The architect can amend the work in response to valid findings. Unresolved material disagreement at the review limit goes to the Owner; preferences alone do not prevent completion. The service reads the positive integer `architecture_loop.maximum_fidelity_reviews` from the shared TOML file; omission uses the stated default, and an invalid value blocks initiation. The activity snapshot fixes that limit. A valid completed independent review consumes one round; clarification, architect amendments, technical failures, and duplicate delivery do not. The first passing review can proceed to confirmation without using the remaining round. Technical recovery and output correction use the separate allowances below. The provisional execution work-item correction limit does not govern this review.

Review is not a search for improvements. A blocking finding must identify a concrete omission, contradiction, or defect that prevents an agreed outcome or violates a requirement. Wording preferences, alternative designs, and optional improvements do not trigger rework, another review, or blocked confirmation.

Reviews bind to exact versions and hashes. Changed reviewed content loses automatic approval coverage; follow-up review checks the required correction and affected dependencies within the remaining budget. Unchanged adequately reviewed work stays covered. Broad re-review is justified only by material effects on that coverage, not the existence of an amendment.

### Confirmation and completion

The CLI presents a concise summary with access to the full breakdown: development milestones and intended outcomes, grouped work packets, coverage of confirmed project outcomes, dependencies, parallel opportunities, and any limitations requiring Owner acceptance.

The view also shows the exact version and whether independent review coverage is valid. Confirmation is eligible only for the unchanged published working version with valid coverage and no unresolved material blocker except a limitation explicitly accepted within Owner authority. Review approval and clarification answers do not substitute for confirmation.

The confirmation request carries the expected working reference and content hash. The service compares them before reserving the operation. If they changed, reject the stale request, explain the change, and present the updated version; never confirm it silently. A successful confirmation saves that exact version and completes the loop. The underlying investigation, structure, and specialist records remain traceable.

Completion does not start or schedule execution. `/execution start` uses the separate [execution initiation](#execution-initiation) rules.

### Publication, recovery, and cancellation

Architecture operations inherit the confirmed registration's destination under [source and publication selection](#source-and-publication-selection). They use the shared publication journal with an operation identity, intended exact bytes, expected prior references, verified Git commit, and SQL application state. The service owns repository writes; agents prepare outputs in permitted working areas and cannot publish arbitrary source changes. Source and assigned inputs remain read-only to the agent; only assigned output and scratch paths are writable.

Foundation preparation is staged when new specialist files are needed. An initial architect assignment returns the assigned role/context artifacts. The service verifies their permitted source-local paths and expected file versions, commits them, and records the verified references. A follow-up immutable assignment supplies those published references to the same architect session before it creates `project-structure.json` and dependent records. The architecture manifest then includes those exact references. Neither agent nor schema is expected to predict a future Git commit. Intermediate publications remain journaled work; they are not proof that the complete output set is current.

For a content save, first publish and verify the required files and manifest. Then publish the discovery index in a separate commit pointing to that known content commit and manifest hash. Both commits belong to the same journaled operation. Advance SQL's working reference only after both are verified; the index never embeds its own future commit.

For confirmation, first save the accepted Owner request and reserve its exact target in SQL. Publish and verify the receipt and manifest update, then publish and verify a separate index commit pointing to that known receipt/manifest commit. Apply the confirmed reference and completed state in SQL only afterward. Content must remain unchanged while confirmation is pending. The prior confirmed reference remains authoritative until application completes.

An interrupted operation is reconciled from GitHub and SQL using the same identity and intended bytes. Complete its remaining recording without creating another version, rerunning completed agent work, or requesting another confirmation when the Owner's decision is already saved. Uncertainty pauses the loop with an explanation. Neither working nor confirmed references advance on an assumption.

Cancellation stops the agents and preserves saved work, history, and any prior confirmed breakdown. It does not confirm unfinished work or start execution. The project stays reserved until stopping is verified and pending external operations are reconciled. A pending accepted confirmation must first be reconciled; a cancellation request cannot erase a recorded confirmation or undo a completed one.

After cancellation has fully resolved, `/architecture start` creates a new activity, carries forward valid saved work, and checks it against current registration and source inputs. Only affected work is revised. The service links the prior activity and assignment accounting. Cancellation/restart cannot reset exhausted review, technical recovery, or correction budgets for the same unresolved work; an additional allowance requires an explicit recorded decision.

| TOML setting | Architecture-loop meaning |
|---|---|
| `architecture_loop.architect.run_timeout_seconds` | Positive integer; active architect-run limit, default 1800. |
| `architecture_loop.fidelity_reviewer.run_timeout_seconds` | Positive integer; active reviewer-run limit, default 1800. |
| `architecture_loop.recovery.automatic_recovery_attempts` | Nonnegative integer; default two recovery attempts after the initial run, counted per assignment. |
| `architecture_loop.recovery.maximum_output_corrections` | Nonnegative integer; default two automatic output-correction attempts per architect assignment. |

These settings use the activity's validated definition snapshot and do not alter registration defaults. Recovery follows the same cause-based principles as registration: retry only a recoverable failure, require intervention for permission/configuration problems or unknown causes, and never replace a run whose stopping is uncertain. A timeout pauses after confirmed stopping rather than automatically retrying. Review counts, correction attempts, and technical recovery counts stay distinct. Reserve a correction attempt when its corrective run starts, count it once, and retain that identity through recovery. A launch failure before correction starts consumes no correction attempt; a run failure uses recovery accounting without counting the same correction twice.

### Architecture-loop interactions

| Starting condition and trigger | Service and agent behavior | Saved record and visible result | Advancement or essential failure |
|---|---|---|---|
| An explicit CLI start request targets a project | Check confirmed registration before starting the persistent architect session and reading its files. | Record the loop's source registration and activity; display its progress. | Unconfirmed registration cannot start the loop; explain the reason. Idle-only eligibility and repeated-start behavior apply as defined above. |
| The architect investigates and prepares work | Record findings and decisions, establish structure and specialist guidance, and derive bounded packets and milestones. | Saved outputs support continued work and review; CLI progress follows recorded activity. | Unsupported assumptions do not establish readiness; missing authority or information follows clarification. |
| A linked question receives answers or follow-ups | Save responses and return relevant context to the persistent session. | The CLI shows recorded answers and subsequent activity. | Amend affected work when sufficient information is available; unresolved required information remains visible. |
| A breakdown is submitted for independent review | Give a separate reviewer the exact sources and outputs; return justified corrections to the architect. | Save the reviewed version, findings, amendments, and review outcome. | Use the architecture-loop review limit; material disagreement at the limit reaches the Owner. |
| The reviewed breakdown is presented for confirmation | Show the summary and full version for an explicit Owner decision. | Save confirmation of that exact version and show loop completion. | No automatic execution; unresolved material findings cannot be hidden as approval. |

### Architecture-loop implementation boundary

Session operations, state transitions, assignments, responses, API payloads, saved-record schemas, and replanning entry are defined above. Implementing those contracts and verifying installed tool support belong to development; no separate replanning-design prerequisite remains.

The supplied `docs/schemas/architecture-loop.schema.json` does not yet represent all fields in [Architecture record contract](#architecture-record-contract): work-packet `execution_requirements`, milestone `qa_plan_ref`, and Quality Assurance plan records and inventory entries remain executable-schema alignment work. Their meanings are defined in that contract. Architecture-loop delivery must extend the producer schema, allocation and response/output inventory, and validation/publication handling before a breakdown containing those required inputs can be confirmed or consumed by Execution. The existing schema alone is not evidence of a valid Execution-ready breakdown.

General Execution scheduling, implementation review, and merge authority remain outside this loop. A documentation readiness check does not confirm a live registration or establish implementation completion.

## Execution

The Execution contracts below define initiation, work planning, coder routing, independent review, product integration, milestone Quality Assurance and review, authorized merges, correction supplements, cross-milestone source delivery, stopping, recovery and completion. Registration and architecture-loop controls remain separate and do not supply or change Execution budgets.

### Execution initiation

The selected project's execution begins only through an explicit `/execution start`. Before acceptance, the service checks that the confirmed architectural breakdown belongs to the current registration; no registration, architecture activity, unresolved publication or uncertain agent run conflicts with starting; required execution configuration and agent access are available; and at least one packet is eligible to run.

The service records the execution activity before dispatching work. Repeating the command opens the existing execution activity rather than creating another. Other projects can continue independently. Starting authorizes only work within the confirmed breakdown, not scope changes or replanning.

The start process collects a configured route for the Maestro Development Manager. After acceptance, the service launches that agent first. Coder selections are separate decisions made during work planning.

The service derives the product code baseline from the exact confirmed breakdown's `source_commit` and verifies that it equals the current confirmed registration's pinned source baseline. The Owner's registration source selection is the originating choice; `/execution start` cannot supply a replacement baseline. Before accepting start, the service verifies those records and the source object, reads product `master` and records its current head separately as `product_master_start_commit`. That observed merge target does not replace the approved code baseline. In the start transaction, SQL saves both commits, their confirmed input references and the observation time. Missing objects, inconsistent source bindings or a failed current-input check block start. Lazy milestone-branch creation consumes the saved product baseline; packet branches use the recorded current milestone head. Separately published specialist and QA inputs retain their exact references. Changed merge targets follow reconciliation and affected review; a change to the approved code baseline requires the existing re-registration and architecture-confirmation path.

### Execution process definition and configuration

Execution uses the installed `execution@1` schema bundle. Installation resolves it as `schemas/execution/1/schema.json` relative to the Maestro installation folder; its repository source is `schemas/execution.schema.json`. The source schema and executable validators are implementation work. A missing, unsupported or changed installed bundle blocks new Execution work and continuation that cannot verify its recorded bundle hash; read-only status remains available. The service saves the exact bundle reference, dependency hashes and effective Execution configuration hash with each activity.

The shared `/etc/maestro/agents.toml` file contains the following Execution settings. Exact model values are installation choices, not architecture defaults.

| Setting | Contract |
|---|---|
| `execution.saved_outputs.schema` | Required literal `"execution@1"`. |
| `execution.development_manager.routes.<route_id>.tool`, `.model`, `.backup_route_id` | Named permitted Development Manager route, exact full model identifier and configured backup. `/execution start` selects one route ID. |
| `execution.development_manager.run_timeout_seconds` | Required positive duration for one planning action; idle persistent-session time does not consume it. |
| `execution.integration_manager.primary.tool`, `.model`, `backup.tool`, `backup.model` | Required exact primary and backup routes for the persistent Integration Manager. |
| `execution.integration_manager.run_timeout_seconds` | Required positive duration for one Integration Manager action; idle persistent-session time does not consume it. |
| `execution.reviewers.packet.*`, `execution.reviewers.integration_change.*`, `execution.reviewers.milestone.*` | Separate primary and backup `tool` and exact `model` pairs for each independent-review assignment type. Each type also requires positive `run_timeout_seconds`. |
| `execution.quality_assurance.primary.*`, `backup.*` | Primary and backup `tool` and exact `model` for milestone Quality Assurance, plus positive `run_timeout_seconds`. |
| `execution.milestone_gap_architect.primary.*`, `backup.*` | Primary and backup `tool` and exact `model` for bounded milestone-gap determination, plus positive `run_timeout_seconds`. |
| `execution.coder_default_route_id` | Required route ID for the local Qwen primary coder. |
| `execution.coder_routes.<route_id>.*` | Required `adapter`, exact `model`, `location`, nonempty `capabilities`, positive `context_limit_tokens`, positive `maximum_concurrent_runs`, positive `run_timeout_seconds`, and optional configured `backup_route_id`. |
| `execution.reviews.packet.maximum_completed_rounds` | Positive integer; default 2. |
| `execution.reviews.integration_change.maximum_completed_rounds` | Positive integer; default 2. |
| `execution.reviews.milestone.maximum_completed_rounds` | Positive integer; default 2. |
| `execution.recovery.automatic_recovery_attempts` | Nonnegative integer; default 2 per role assignment after its initial run. |
| `execution.recovery.manual_retry_attempts` | Nonnegative integer; default 1 after the applicable intervention and linked Owner action. |
| `execution.qa.environment_root` | Absolute local path for isolated Quality Assurance environments. |
| `execution.qa.maximum_parallel_environments` | Positive integer; default 1. |
| `execution.qa.startup_timeout_seconds`, `shutdown_timeout_seconds` | Required positive service-supervision durations. |
| `execution.qa.artifact_root` | Absolute service-owned root for Quality Assurance evidence artifacts. |
| `execution.qa.artifact_retention_days_after_close` | Positive days retained after Execution closes; default 90. Artifacts are never deleted before closure. |
| `execution.qa.maximum_artifact_bytes_per_run` | Positive per-run capture limit; exceeding it stops further capture and makes any required missing artifact `UNTESTED`. |

`adapter` is one of `local_qwen_qwen_cli`, `codex_cli`, or `claude_code_cli`; `location` is `local_ai_box` or `cloud`; and each capability is one of the `execution@1` identifiers defined by the work-packet contract. For a coder launch, the service requires the packet's capabilities to be a subset of the route's capabilities, the route location to be allowed, `context_limit_tokens` to meet `minimum_context_tokens`, capacity to remain, and the planning result's model to equal the route's snapshotted exact model. A mismatch rejects the request without reservation or silent fallback.

Primary and backup pairs for a role must differ. The service validates the selected tool, exact model, capability, credentials, workspace access and structured-output support before launch and verifies the running tool's reported identity before accepting output. No moving alias, implicit downgrade or unconfigured substitution is allowed. Backup routing follows the existing cause-based recovery boundary: a preflight failure may choose the configured backup without consuming a run-recovery attempt; a failure after launch requires confirmed stopping and preserves all consumed counts. A failed review never triggers a route switch merely to seek another verdict.

The local Qwen coder route uses adapter `local_qwen_qwen_cli`. It launches the installed `qwen` executable against the configured local Ollama model in the isolated packet worktree, using an argument array and a prompt that directs the agent to the service-written assignment file. The current source contains a local Qwen CLI adapter; reuse requires code assessment and installed verification rather than assuming that source is production-ready. Codex and Claude Code routes use the shared [tool transport](#tool-transport).

Every configured Execution `run_timeout_seconds` is snapshotted when the activity starts. Timing begins only after launch is confirmed, progress does not reset it, and the absolute deadline and elapsed active time are saved. Service restart resumes supervision against that deadline and never grants a fresh duration. A persistent manager's idle session consumes no run time; follow-up and recovery runs receive their own recorded deadline. Confirmed timeout stopping follows [unresponsive runs](#unresponsive-runs).

Execution does not select a second Git credential. It uses the repository profile already saved in the project binding under `repositories.<profile>`. Before start and every Git operation, the service verifies that the bound repository and intended branch match that profile's allowlists and records the resolved profile in the activity and journal. A missing profile, mismatch, or attempted per-Execution override blocks the action; agents never receive the credential.

Configuration is snapshotted when an Execution activity starts. Route availability is rechecked at each launch, but later file edits do not change the activity's permitted routes, exact models, timeouts, review limits or recovery allowances. A new confirmed registration and new Execution activity may use a newer valid snapshot.

### Execution API, state and record contract

Execution operations use the common request envelope and idempotency rules. The process-specific operations are:

| Operation | Required input and effect |
|---|---|
| `execution.start` | Project identity, exact confirmed registration and breakdown references, expected project version, selected Development Manager route ID and idempotency key. Atomically validates eligibility, snapshots configuration and creates or returns the one active activity. |
| `execution.status` | Project or activity identity; returns saved state, restrictions, active work, queues, blockers, review counts, milestone evidence and completion reference without changing state. |
| `execution.pause` | Expected activity version and Owner identity; snapshots the in-progress set and prevents new packet reservations under [pause and graceful-stop settlement](#pause-and-graceful-stop-settlement). |
| `execution.resume` | Expected paused activity version and Owner identity; permits new reservations only when no stronger saved restriction, re-registration transition or unresolved unsafe condition applies. |
| `execution.stop` | Expected activity version and Owner identity; enters `finishing`, snapshots the in-progress set, settles only its permitted downstream lifecycle, and publishes a stopped-closure record. Unsafe work uses the linked disposition action and supervised stop instead. |
| `execution.retry` | Exact failed assignment or external operation, expected version, unconsumed `execution_manual_retry` grant and idempotency key; reserves and applies that grant under the shared Owner-decision rules without resetting other counts. |
| `owner.decision` (shared) | Applies typed Execution review-limit, manual-retry, or work-disposition decisions using the stable targets and choices under [Owner decisions at a process limit](#owner-decisions-at-a-process-limit). |

Activity states are `starting`, `running`, `paused`, `finishing`, `blocked`, `closing`, `completed` and `stopped`. `blocked` means no eligible progress can run; it does not convert failed or unfinished work into completion. Pause and graceful stop restrictions survive service restart. A repeated operation with the same idempotency key returns the saved receipt; a stale expected version returns current state without applying the action.

SQL owns live Execution state. The service is the only writer. At minimum it stores the following linked records:

| Record | Required contents |
|---|---|
| Execution activity | Project, registration and breakdown references; configuration/schema hashes; product baseline; state/version; start, pause, stop and closure data. |
| Role route and session | Role, selected primary/backup, exact model/tool evidence, assignment/run/session identity, context checkpoint and recovery counts. |
| Packet assignment | Packet/version, milestone, branch/base, specialist role, coder route, plan/result references, permitted paths, state and dependency bindings. |
| Review assignment | Type, exact reviewed revisions and evidence hashes, reviewer independence/tool/model, findings, outcome, completed count and configured limit. |
| Integration queue entry | Durable sequence, packet and milestone, source/target revisions, active/blocked/resolved state, Integration Manager changes and review references. |
| Dependency delivery | Providing packet/milestone and commit, consuming milestone, allowed dependency closure, import operation and readiness/invalidation state. |
| Correction supplement | Finding, original breakdown/milestone, versioned packet definitions, publication and activation references. |
| Architectural determination | Triggering packet/integration question or review-limit decision, exact inputs, configured architect assignment, validated determination/recommendation and routing receipt under [Execution architectural determinations](#execution-architectural-determinations). |
| Quality Assurance run | Exact milestone revision, environment/configuration, data lineage, checks, evidence artifacts, result and cleanup state. |
| Repository operation | Intended repository/ref/head, operation kind, input hashes, idempotency key, attempt state and verified remote result. |
| Milestone completion | Exact branch and merge revisions, packet/integration/review/Quality Assurance references, dependency deliveries, observations and publication state. |
| Execution completion | All authorized milestone-completion references, final merge references, unresolved-work assertion, non-blocking observations and published successful-completion record. |
| Execution stop | Completed milestones, exact unfinished packets/milestones/queue entries and reasons, final reconciled master, restrictions, non-blocking observations and published stopped-closure record. |

Planning, coder, review, integration and Quality Assurance responses are validated named definitions in `execution@1`. Every response carries `schema_version: 1`, project/activity/assignment identity, exact input versions, run identity and result state. Planning results include requested launches with route/model/reason, priorities, blockers, questions and checkpoint. Coder results include plan/result revisions, changed paths, checks, evidence and limitations. Review results include exact reviewed range, independence, finding classification, minimum correction and count/limit. Integration results include source and target revisions, changes, checks and dependency effects. Milestone-gap results include exact finding and evidence references, affected closure, disposition (`implementation_defect`, `in_scope_supplement`, or `reregistration_required`), rationale, Owner recommendation when applicable, and the supplement payload when selected. Quality Assurance and completion fields follow their sections below.

External Git operations use a durable SQL journal. Before a branch creation, merge or record publication, the service saves the exact intended repository, credential profile reference, expected remote heads, input object hashes and idempotency key. After the operation it reads the remote refs and bytes before recording success. A lost acknowledgment reconciles the same intent; changed heads or conflicting bytes pause without force, overwrite or duplicate effects. SQL state advances only after verified external success.

### Development Manager preparation and continuity

The Development Manager coordinates execution within the current registration and confirmed breakdown. It cannot change scope, redesign architecture or initiate replanning.

At first launch, it reads the registration, confirmed breakdown, packets, dependencies and recorded execution state. It returns a concise understanding of intended outcomes, existing progress and blockers before requesting work. A resumed project is not assumed to be new.

Each project's execution activity has a persistent Development Manager session. Persistence retains useful understanding between planning actions; the agent is idle between actions and does not continuously poll or consume model tokens. The service resumes it with relevant events and current saved state, with only one planning action active in that session at a time.

The working context contains current milestones, eligible and blocked packets, active assignments, available capacity and relevant recent decisions. Detailed records remain accessible when needed. Handled events are not repeatedly included as new input. Checkpoints preserve decisions, reasons and unresolved issues rather than duplicate transcripts. Decisions are saved through the service; session memory is not authoritative. The shared [context-management rules](#agent-performance-and-context-management) govern compaction and replacement from verified records and a checkpoint when capacity fills or a session becomes unusable.

### Work planning and coder selection

The Development Manager selects packets and requests assignments. The service checks current eligibility, dependencies, resource and parallel-work boundaries, rejects stale, blocked, conflicting or unauthorized requests, and reserves accepted work before launch. Agent judgment chooses work; the service enforces the rules.

Qwen is the primary coder and default route. The manager may choose a cloud coder directly when packet complexity, required capabilities, context needs or available capacity justify it; Qwen does not have to fail first. The manager chooses Codex or Claude Code and the appropriate configured model level/version, recording a brief reason.

Maestro uses the snapshotted `execution.coder_routes` registry. The manager selects only a permitted route whose declared capabilities, context capacity, execution location and live concurrency allow the packet. The service checks availability before reservation and launch and reports an unavailable selection without silent substitution. The configured local Qwen route remains the default; an unavailable default does not by itself authorize an unconfigured cloud route.

Scheduling favors packets that unblock dependent work or enable useful parallel work, while considering declared delivery order and available coder capacity. Independent work may proceed while another packet is blocked. Each choice records its reason. The confirmed architecture supplies dependencies, parallel opportunities, shared-code boundaries and integration points; the manager uses them with live progress instead of rewriting the plan. Missing or contradictory dependencies are raised for architectural attention.

Planning continually reassesses pending work as progress, dependencies and resources change. The service notifies the manager when a packet completes, becomes blocked or fails, a relevant answer arrives, or coder availability changes. Related events may be grouped; every progress message does not require another planning action. Recalculation does not automatically interrupt or reassign running work.

### Planning results and questions

Each planning pass returns a structured result containing requested packet launches with coder route, exact model version and reason; pending priorities and blockers; questions or architectural issues; and a concise continuity checkpoint. The service validates requests against current saved state before reservation. If state changed during planning, it returns the affected rejection reasons for reconsideration rather than accepting stale work.

Development Manager questions use the [existing CLI question flow](#questions-and-answers), linked to project and execution activity. The service saves a question before displaying it and saves answers before supplying them to the manager's next planning pass. Only dependent work waits; unrelated eligible work can continue. Planning responses and delivered events use the [Execution response contract](#execution-api-state-and-record-contract); handled event identities are checkpointed so a resumed session does not treat old events as new.

### Coder preparation and submitted results

Each coder follows the [common coding instructions](agents/coding-agent-sop.md), the exact packet and the applicable project specialist role. Specialist guidance adds source-area knowledge without duplicating or weakening common rules. The unrelated example roles currently in this repository's specialists folder are not assignment options for this work.

Before implementation, the coder returns the [implementation plan](#returned-implementation-plan) through the service. It identifies intended changes, relevant existing code, necessary connections, basic verification and blockers. The service saves it and exposes it to the CLI and Development Manager. There is no separate plan-approval gate; material conflicts or missing prerequisites block affected work.

The final structured result explains changes against the expected outcome, exact source/result revisions, changed files, checks and results, evidence, limitations, blockers and unfinished work. The service validates the response and referenced artifacts, records it and notifies the Development Manager. A coder's completion claim means ready for independent review, not packet acceptance or merge permission.

### Execution workspaces and repository writes

The service creates each Execution checkout under `<workspace_root>/execution/<execution-activity-id>/<assignment-id>/` as a clean worktree of the exact recorded base commit and assigned branch. Packet coders and the Integration Manager run as constrained identities that can write only their assigned worktree and permitted paths. They receive a local Git author identity but no repository credential, service state, other assignment workspace, or secret store access.

A writing agent produces local commits on its assigned branch. The wrapper verifies the expected base, branch, commit graph, changed paths, required result identity and absence of uncommitted output. The service then journals and pushes that exact commit with the project's bound repository profile. It supplies the credential only to the privileged Git operation, reads the remote ref afterward, and records success only when it equals the intended object. A lost acknowledgment reconciles the same intended commit; a changed remote head or unexpected object quarantines the workspace and pauses without force-push, rebase or overwrite.

Each independent reviewer receives a separate read-only checkout of the exact base and result commits plus immutable evidence copies. It never reuses the author's worktree, receives no write credential, and cannot change the reviewed branch. QA receives its separate environment under the QA contract rather than a coder worktree. Workspace identity, base/head, permissions, local commit, push journal and cleanup state are saved with the assignment.

A worktree remains until its local and remote outcomes are reconciled and no review, correction, audit or completion record needs it. Cleanup verifies the recorded path and assignment identity before removal. Unknown state, path mismatch, failed cleanup or evidence conflict marks the workspace quarantined for operator attention and cannot establish completion.

### Independent implementation review

The [Independent Implementation Reviewer](agents/independent-review-agent.md) examines the exact submitted changes against the packet, relevant architecture, common coding rules, assigned project specialist role and verification evidence. It checks promised outcomes, essential connections, scope compliance and basic meaningful verification. The reviewer works read-only and cannot have authored the implementation.

Material defects identify an unmet requirement, affected code, impact and minimum correction. Preferences and optional improvements are non-blocking. Results pass through the service to the Development Manager. Clear implementation defects return to the coder; missing or contradictory architectural decisions use [Execution architectural determinations](#execution-architectural-determinations). Reviewers do not edit code, dispatch corrections or authorize merges.

An approved exact packet revision becomes eligible for Integration. Independent review remains before Integration; the Integration Manager does not replace this stage.

#### Packet and integration-change review limits

Packet implementation review and review of Integration Manager code changes have separate configurable limits. Each defaults to a maximum of two completed rounds for the exact assignment: the initial review and, when required, one targeted correction review. One passing round is sufficient.

A valid completed review consumes a round. Malformed output, interrupted review and technical recovery do not consume a completed round or establish approval. The service saves the effective limit and consumed count. Reassigning the author, replacing the reviewer, starting a new session, renaming the work or moving the workspace does not reset the limit.

The packet coder corrects packet findings; the Integration Manager corrects findings in its own integration changes. The correction review covers the named findings and affected behavior while retaining valid coverage of unchanged work. Neither author can approve its own correction.

If blocking findings remain at the applicable limit, the affected work pauses unapproved and unmerged. The Project Architect supplies a recommendation and the Owner is notified through the CLI. No automatic extra review is allowed. Unrelated eligible work continues. Registration, architecture-loop, architectural-support and milestone-review budgets remain separate and do not supply extra rounds.

#### Execution architectural determinations

A saved Execution-planning, packet or integration-change architectural question, or blocking findings at either review limit, causes the service to create an `execution_architectural_determination` assignment. The Development Manager supplies the affected work and question/finding through its normal structured result; exhaustion is also detected directly from the saved review count. Duplicate triggers for the same work, finding versions and limit decision reuse the saved assignment. Missing-specialist requests retain their separate support process, and failed milestone QA/outcome findings retain the milestone-gap process.

This read-only Project Architect assignment reuses the primary/backup routes and timeout of `execution.milestone_gap_architect` from the parent Execution snapshot, with the existing `execution.recovery` allowances; it does not resume the architecture loop. Inputs include the exact registration/breakdown, triggering planning result and affected packets or Integration Manager change, source/target revisions, role and architecture references, question/findings, prior review evidence, affected queue/dependency state, base limits, completed rounds, prior grants and remaining allowances. The service saves these bindings, assignment/run identity and configured route before launch. Replacement preserves the assignment, inputs and counts under the shared stopping/recovery rules.

The named `execution_architectural_determination` response in `execution@1` carries the common response identities and exact input versions, affected-work references, finding/question references, rationale and one determination: `within_confirmed_design` with an interpretation of existing authority; `implementation_defect` with the minimum correction for the original author; or `reregistration_required` with the affected scope and recommended work disposition. It also carries the required Owner-facing recommendation, either `grant_one` or `remain_paused`, when the triggering review allowance is exhausted; otherwise that field is null. An interpretation cannot change a confirmed outcome, packet, responsibility or dependency. This assignment cannot publish a supplement, dispatch code, approve work or grant an allowance.

The service validates scope, reference freshness and the result against the assignment, then atomically saves the determination and links it to the affected work and pending decision. Identical replay returns the saved receipt; stale or conflicting results cannot overwrite it. A valid interpretation answers the linked architectural question; a defect returns to the packet coder or Integration Manager through the Development Manager, subject to existing allowances. Re-registration uses the existing Owner work-disposition process. At an exhausted review limit, work remains blocked until the recommendation is saved and the typed Owner choice is applied; the recommendation itself permits no extra review. Malformed output or unavailable routes use bounded technical recovery and otherwise leave a specific CLI blocker. Restart recovers the same assignment and decision linkage without resetting counts.

### Integration management and queue

The [Integration Manager](agents/integration-agent.md) is the project's code manager; the Development Manager is its process manager. The service owns queues and durable assignment state rather than agents retaining pending work only in conversation memory. The Development Manager uses recorded progress, dependencies and capacity to manage work flow.

Each project has a persistent Integration Manager session and a first-in, first-out queue of independently approved packets. Only one integration assignment is active for the project at a time, across all its development milestones. Queue order is the service's durable enqueue order. The active assignment retains its position through integration review and necessary corrections; the next starts only after it is resolved. A blocked assignment is not silently skipped. Other projects integrate independently, and coding and packet review may continue where dependencies and shared-code boundaries permit.

Each assignment uses the latest accepted target state and the exact approved packet revisions. The Integration Manager checks compatibility, shared interfaces, dependencies, necessary connections and the assembled outcome. It may make code changes needed to achieve the packet or larger confirmed outcome, including code-level integration fixes. It cannot change confirmed scope or established architectural direction; those issues go to architectural attention.

Its own integration changes require independent review of the new changes and affected product behavior. Valid coverage of unchanged packet code is retained. Findings return through the service and Development Manager to the Integration Manager for correction. It cannot approve its own changes. When no code changes are made, record the integration evidence without automatically repeating packet review.

The persistent session uses the configured Integration Manager primary/backup route and the shared context-management rules. Saved source revisions, review results, queue state and handled event identities remain authoritative; a replacement session starts from those records and the latest valid checkpoint.

Strict FIFO has no automatic skip. If the active entry blocks, later entries for that project remain queued while unrelated coding, packet review and other projects may continue. The active entry leaves the head only after a verified merge, an Owner-authorized stop whose external operations have reconciled, or supersession following confirmed re-registration and architectural reconciliation. Withdrawal records the exact reason and preserved work; moving or renaming the same entry cannot bypass its review limit or queue position.

### Milestone branches and product integration

Each development milestone has its own integration branch created from the recorded product baseline. Each work packet has a separate branch created from its milestone branch and returns its reviewed work to that milestone branch. Branches are not literally nested: recorded source and destination relationships establish the hierarchy.

The service owns these fixed branch patterns, using validated service-assigned identifiers and collision checks:

- `maestro/<execution-activity-id>/milestone/<milestone-id>`
- `maestro/<execution-activity-id>/packet/<packet-id>`
- `maestro/<execution-activity-id>/integration/<queue-entry-id>`
- `maestro/<execution-activity-id>/dependency/<dependency-delivery-id>`

Milestone branches are created lazily from their recorded baseline. A packet branch is created from the then-current milestone head recorded with its assignment. When an approved packet reaches the FIFO head, the service creates an integration branch from the current milestone head and merges the exact approved packet head into it. The Integration Manager resolves conflicts and makes any necessary in-scope integration changes on that branch. Independent review binds to its exact head. After approval, the service performs a non-fast-forward merge into the milestone branch and verifies the remote result.

Milestone promotion uses a non-fast-forward merge into product `master` after the required Quality Assurance and milestone review pass. Reviewed branches are never rebased, squashed, force-pushed or amended. A changed target head requires reconciliation and affected review before merge. Branches and worktrees remain until the activity closes and no recovery, audit or pending operation needs them; later retention cleanup is recorded separately and cannot change completion evidence.

The delivery sequence is:

1. The coder submits a completed implementation from the packet branch.
2. Independent review approves its exact revision.
3. The packet enters the project's FIFO integration queue.
4. The Integration Manager integrates it into the milestone branch, with independent review of any integration code changes.
5. Once the milestone's work is complete, its assembled branch receives milestone Quality Assurance and an independent outcome review and gap analysis against the milestone's completion criteria, confirmed project outcomes, dependencies and required connections.
6. Only completed required Quality Assurance with no failed or unverified required path, together with a passing milestone review and gap analysis, makes that branch eligible to merge into product `master`.

Packet approvals alone do not establish milestone completion. The milestone check must establish coverage of the connected promised outcome, not merely a completed packet list. Failed checks go to the architecture agent to determine a correction within confirmed scope and direction or the need for re-registration and replanning. That finding does not itself grant a scope change or start replanning. The review assignment, configured reviewer route, limits and result contract follow [milestone outcome review](#milestone-outcome-review) and the [Execution configuration](#execution-process-definition-and-configuration).

### Milestone outcome review

The service starts a fresh session of the [Independent Implementation Reviewer](agents/independent-review-agent.md) to review the complete assembled milestone branch and perform its gap analysis. The assignment includes exact branch revisions, agreed milestone outcomes, relevant architecture, dependencies and completion evidence. The reviewer checks that the packets work together and that the usable outcome has no missing required parts. It must not have authored or integrated any code under review. The Integration Manager prepares the branch and supporting evidence but cannot approve its own work.

Findings distinguish blocking defects from non-blocking observations. A blocking finding prevents the agreed outcome or its required evidence; preferences and optional improvements do not block merging or require another round. The service records the findings and routes failures to the Project Architect for determination:

| Finding | Correction path |
|---|---|
| Implementation defect within the confirmed design | The Integration Manager corrects it, with process coordination by the Development Manager. |
| Missing work needed for the agreed outcome, within confirmed scope and direction | The architect defines the necessary bounded correction packets; the Development Manager schedules them. |
| Change requiring replanning | Use re-registration and the existing Owner-selected work-disposition process. |

In-scope correction packets are recorded as supplements linked to the original breakdown, milestone and finding; they do not silently replace confirmed records or authorize changed outcomes, dependencies or architectural direction. Those changes still require re-registration.

#### Milestone-gap architectural assignment

Each failed milestone QA or outcome-review finding creates a bounded Project Architect assignment using `execution.milestone_gap_architect`. It is a new session for that finding, not a resumed architecture loop or the missing-specialist support process. The architect may have authored the confirmed design but cannot act as the independent reviewer of implementation or of its own later code.

The assignment includes the exact confirmed registration and breakdown, milestone and branch commits, QA plan and results, review finding, dependency deliveries, existing supplements, affected work state and remaining review allowances. The service supplies a read-only source view and the configured route/model, timeout and original recovery allowances. Replacement follows the shared backup rule and preserves the same assignment identity and counts.

The result uses the milestone-gap definition in `execution@1`. It identifies affected work and evidence, selects `implementation_defect`, `in_scope_supplement`, or `reregistration_required`, explains the boundary, supplies the exact supplement payload when applicable, and gives the Owner-facing recommendation required at a process limit. The service validates and saves the result before routing a defect, activating a supplement, or presenting a disposition. This assignment cannot dispatch code, change scope, approve the milestone, or start re-registration.

#### Correction-supplement activation

The service assigns a supplement identity and positive version before the Project Architect drafts it. The architect returns the exact triggering finding, confirmed registration and breakdown references, affected milestone, bounded correction packets, permitted paths, dependencies, acceptance evidence, and a plain explanation of why the work remains within confirmed scope and direction.

Deterministic validation rejects missing links, duplicate packet identities, unsatisfied ownership, changed outcomes, dependency cycles, unbounded paths or work that requires re-registration. No separate Owner approval or extra packet-definition review is added for a valid in-scope supplement; its implemented packets still receive normal packet, integration, Quality Assurance and milestone review.

SQL owns the working and active supplement state. Immutable UTF-8 JSON is published under `.maestro/execution/<execution-activity-id>/supplements/<supplement-id>/versions/<version>/supplement.json`. It carries `schema_version: 1`, exact project/activity/registration/breakdown/milestone/finding identities, packet definitions, dependency changes limited to those packets, architect assignment/run/model evidence and validation result. The service journal calculates and stores the SHA-256 of the final UTF-8 bytes outside `supplement.json`, then verifies the authorized repository and publication branch, expected head, remote bytes and hash before one SQL transaction activates the version and releases its eligible packets to the Development Manager.

An identical replay returns the saved activation. Conflicting remote content, stale findings or changed inputs pause without overwrite. A supplement may be superseded before any of its packets starts by publishing and activating the next version. Once work starts, its active version is immutable; a material change uses the normal disposition and re-registration path. A supplement and its packets do not reset the milestone review count.

A corrected milestone receives a targeted check of the named corrections and their affected dependencies and product behavior. Valid approval remains for unchanged, unaffected work. If a correction affects a wider part of the product, the reviewer records why the affected coverage must broaden. A correction check does not automatically repeat the whole milestone review.

The `execution.reviews.milestone.maximum_completed_rounds` setting defaults to two: the initial review and, if required, one correction review. One passing round is sufficient. The service saves the effective limit and consumed count for the milestone; replacement reviewers, new sessions, renamed work and corrections do not reset them. Invalid or interrupted review output is not a completed round or approval; technical recovery does not grant additional completed reviews. Results use the milestone-review definition in `execution@1`.

After the configured limit, unresolved blocking findings keep the milestone unmerged and reach the Owner through the CLI with the architect's recommendation. No automatic extra review or merge is permitted. This milestone limit does not define packet or integration review budgets.

### Milestone Quality Assurance and test data

Quality Assurance runs against the assembled milestone, not against individual work packets or Integration Manager changes. Coders verify their own changes, and independent reviewers assess packet changes, Integration Manager changes, and the whole-milestone outcome and gap analysis. Quality Assurance separately exercises the assembled product's user journeys, connected behavior, and failure cases. Its findings use the existing correction path, followed by the affected checks; it does not create another approval loop.

Quality Assurance may start the product and required supporting services in an isolated test environment when that is needed to exercise the actual behavior. The architecture loop publishes the exact versioned [Quality Assurance plan](#architecture-output-locations-and-records) for each milestone, including required data sources, preparation and setup, expected results, artifacts, cleanup and the actual capability paths that must be exercised. If a required data source or setup tool does not exist, creating it is planned work with an explicit dependency. Quality Assurance must not improvise missing setup capability.

Quality Assurance prepares or uses the required data and records its origin, how it entered the system, the actual result path, expected and actual results, and known limitations. Test data may supply inputs, but it must not replace the capability being verified. For example, directly inserting an expected result cannot prove the service or user journey that should create it. Mocks or generated data may assist development, but they cannot establish milestone completion for a bypassed product path.

Every bypassed required step remains `UNTESTED`; it cannot support a pass or milestone completion. If required verification is unavailable, the result is neither a defect nor a pass. The milestone remains unmerged, the CLI shows the specific blocker, and unrelated eligible work may continue. Once the prerequisite is available, Quality Assurance runs the affected verification.

#### Project Quality Assurance bindings

The operator provisions project-specific test resources in `/etc/maestro/agents.toml` under `execution.qa.project_bindings.<project_id>`, using the stable registered project identity. This is runtime setup, not a new registration input or approval gate. Its `environments.<name>` entries contain `classification: test`, a non-secret string map `variables`, and arrays `secret_names` and `network_dependency_names`. Each `secrets.<name>` entry contains `classification: test`, `credential_ref` in the service credential store and the receiving `environment_variable`; values are never stored in this file. Each `network_dependencies.<name>` entry contains the exact `host`, `protocol` and allowed `ports`. Selected variables and secrets are injected only into the setup/support processes naming that environment; conflicting variable names are rejected. Every environment and credential binding is explicitly classified `test`; production bindings are rejected. Names are unique within each table. The operator installs referenced test credentials in the existing service credential store. Agents cannot provision credentials or widen these allowlists.

Before drafting a milestone QA plan, the service validates and collects this project binding, saves an immutable non-secret SQL snapshot with operator-configuration provenance and SHA-256 of its UTF-8 JSON with sorted object keys and no insignificant whitespace, and supplies the architect a read-only catalog of names, non-secret settings and permissions. The service writes `qa-catalog.json` in the assignment's service-owned read-only input directory and names its path and project-binding hash in the existing assignment `instructions`; SQL binds its file hash to the assignment and catalog snapshot. Reviewer assignments receive the same exact catalog through that mechanism. This local input is not a Git `publishedRef`. Credential-store locators remain service-only. The architect selects needed environment, secret and network names from that catalog into `environment_refs`, `secret_refs` and `allowed_network_dependencies`; the plan's `project_binding_hash` identifies the saved snapshot. Each setup/support-process entry identifies which selected environment it uses. Secret and network selections must be permitted by that environment. An entirely self-contained plan with all three reference lists empty uses null for `project_binding_hash` and needs no project binding.

The service checks plan selections and hash against the saved catalog before publication and confirmation, and supplies the same non-secret selection evidence to the independent reviewer. Unknown names, missing credentials, production classification, conflicting settings or unauthorized destinations block affected QA-plan completion with a linked setup question identifying what the operator must provide. Operator provisioning grants access within the existing policy; the Owner's normal exact-breakdown confirmation approves the plan. No additional confirmation is introduced. A changed selected binding requires the affected plan to be amended, reviewed and confirmed through that existing process; the same name cannot silently designate a new environment.

Execution startup retains the exact confirmed plan and its binding snapshot/hash with the activity; each QA run records those references and resolved non-secret credential version identities in SQL. The service resolves secret values only into the isolated processes that need them. Before every setup/use it rechecks availability, current authorization and test classification. A revoked, missing or changed binding blocks affected QA as `UNTESTED` without substituting a current configuration or exposing secrets. Operator restoration of the exact binding permits the affected checks to run; a changed plan uses the existing confirmed-breakdown/re-registration boundaries. Restart reuses the saved binding references and reconciles existing environments before any new setup.

#### Isolated Quality Assurance environment

Each Quality Assurance run receives a service-owned environment identity and a clean directory under `execution.qa.environment_root`. Setup uses only versioned scripts or argument-array commands referenced by the confirmed architecture and exact milestone source; agent-supplied arbitrary shell text is not a setup contract. The service starts required product and support processes, checks declared health conditions, captures process identities and ports, and stops them after the run.

The environment uses separate storage and test credentials resolved through [Project Quality Assurance bindings](#project-quality-assurance-bindings). Secrets remain in the service credential store and are not written to repository records, prompts or logs. Outbound network access is denied unless the confirmed setup names an allowed dependency. Production endpoints, production credentials and production data are prohibited in automatic milestone Quality Assurance. A production or deployed-environment run requires its separate existing authorization and is not substituted for an isolated run without that authority.

Data setup records the dataset or generator identity and hash, source classification, sanitization when applicable, setup operation, actual entry path and cleanup requirement. Generated or copied data may be input to the real capability path; it cannot directly create the result whose path is being verified. Reusable environments must pass the declared reset check before another run. Failed shutdown, cleanup or reset marks the environment quarantined and blocks reuse without changing the Quality Assurance result.

The Quality Assurance result records exact milestone commit, QA-plan version/hash, environment/configuration hashes, process and health evidence, data-lineage entries, each expected and actual result, artifact identity/path/hash/size/media type, `PASS`, `FAIL` or `UNTESTED`, limitations, start/finish time and cleanup state.

The service writes artifacts beneath `<execution.qa.artifact_root>/<execution-activity-id>/<qa-run-id>/<artifact-id>`. Capture first uses a service-owned temporary file, then verifies size, scans configured secret patterns, calculates SHA-256 and atomically publishes the final file. SQL owns artifact identity, access classification, path, hash, size, media type, creating check and retention state. QA agents receive write handles only for their run; CLI retrieval requires the project's normal Owner authorization.

Required artifacts remain durable until Execution closes and then for `execution.qa.artifact_retention_days_after_close`. Scheduled deletion verifies identity/path, records time and reason, and leaves a tombstone with the original hash and completion reference. Missing or hash-mismatched required evidence before closure invalidates the affected QA check and makes it `UNTESTED` until recaptured; it can never be accepted from an agent claim. Failed capture, capacity exhaustion, deletion or restart recovery is recorded. Repository completion records carry bounded hashes and references, not secrets or embedded logs.

### Dependency readiness and automatic continuation

An independently approved packet that has completed integration may satisfy a declared dependency before its milestone merges into master. The architect explicitly identifies dependencies that require a completed milestone instead. Review approval alone, before integration, is insufficient.

For an early code dependency, the service records the providing packet, source milestone head after its verified integration, accumulated integrated packet set and consuming milestone. It checks that the accumulated set is within the consuming milestone's declared dependency closure. If not, the dependency waits for source-milestone completion rather than importing undeclared code.

For a dependency requiring milestone completion, including an early packet delivery held by that closure check, the service waits for the provider's verified promotion and immutable completion record. The delivery then names that record, its exact passing milestone-branch head and the included provider milestone/dependency set. Completion permits delivery of the accepted provider milestone as a unit under the declared dependency; it does not authorize unrelated code from later or other product-master history. The service verifies that the head was the reviewed/tested input to the recorded promotion, is contained in the verified merge, and includes only the completed provider and its confirmed dependency closure. Missing or inconsistent evidence leaves readiness blocked. It imports that exact head through the same FIFO dependency-import path below, never a moving master head and never a readiness flag alone. Even a consumer branch created after provider completion must receive this import because its initial baseline remains pinned. If the exact source is already contained in the consumer head, the service verifies and records that containment and completion evidence as the idempotent delivery result. Dependent starts require this saved delivery; provider completion by itself is insufficient. Replacement and invalidation use the same transitive rules as early imports.

An eligible delivery creates a FIFO `dependency_import` entry and a branch from the consuming milestone head using the fixed dependency branch pattern. The service merges the exact providing commit with both histories preserved. The Integration Manager resolves conflicts or necessary connection changes; any new code receives integration-change review. After a verified non-fast-forward merge into the consuming milestone branch, SQL binds readiness to the source commit, import result and included packet set. Dependent packet branches are created only from that updated head.

An import creates a promotion dependency: the consuming milestone cannot merge to product `master` before the providing milestone has merged, unless the confirmed architecture explicitly assigns the imported outcome to the consuming milestone instead.

Changed or inaccessible source evidence atomically invalidates the delivery and its transitive consumer closure: packets whose declared dependencies reach it, their queued/integrated descendants, and QA or milestone-review evidence produced from a branch containing that import. The service blocks new affected starts, merges, QA and promotion. An affected running assignment may finish only to preserve work; its result is quarantined and cannot advance until reconciliation. Unaffected work and exact review coverage whose source objects and dependency behavior are unchanged remain valid.

A replacement uses a new recorded dependency delivery and FIFO import. The service compares the old and replacement commits, rebases nothing, and reconciles the consuming milestone through the normal integration branch. Changed connection code receives integration-change review. Affected packet or integration evidence is re-reviewed, and QA/milestone review is rerun when its exact tested branch or behavior changed. SQL rebinds readiness only after the replacement merge and required affected checks pass. Prior approvals and branches remain historical; no operation silently retargets them.

Execution automatically continues with eligible work across confirmed milestones within its already authorized scope. A blocked milestone does not stop unrelated eligible work. Active stop or finish-current-work instructions still prevent new starts as defined by their disposition.

A failed milestone review immediately prevents new work that depends on the failed outcome from starting. Already-running affected work follows the existing work-disposition process; unrelated eligible work continues. The service records changed readiness and notifies the Development Manager to recalculate pending assignments.

Once all authorized milestones have merged and their required checks have passed, the service automatically closes Execution and notifies the Owner through the CLI with a completion summary. No additional Owner approval is required. Closure verifies that no required correction, active run or unresolved merge remains; missing or uncertain evidence is not completion.

### Pause and graceful-stop settlement

The transaction accepting `execution.pause`, `execution.stop`, `finish_safe_work`, or `finish_current_for_replanning` records the exact in-progress set: every reserved or running packet; queue or dependency-import entry derived from those packets; active review, Integration Manager, QA, milestone-gap, architectural-determination, support or repository operation; and any milestone whose remaining required packets are all already in that set. Later work cannot join the set by renaming, reassignment or a new supplement.

Members may perform only the downstream stages needed to settle their already-authorized work: coder completion; architectural clarification and required limit recommendations for those members; packet review and in-budget correction; FIFO integration and integration-change review/correction; required dependency reconciliation; and QA, milestone review, promotion and completion publication only for a milestone whose entire remaining work was in the recorded set. Technical recovery and an Owner-granted review or manual retry retain their normal limits. A newly discovered correction supplement, packet outside the set, or unrelated milestone cannot start while the restriction applies.

All other pending packet reservations are refused. Existing queue entries outside the set become `held` for pause and `unfinished` for stop. Strict FIFO remains: if a held or unfinished head prevents a set member behind it, that later entry also settles as blocked rather than skipping the head. Known failure or review exhaustion remains an explicit unfinished result; unsafe work uses the supervised stop disposition.

After the set has no active or uncertain run, environment, queue transition or external operation, pause enters `paused` and preserves held work for an eligible `execution.resume`. Graceful stop remains `finishing` until the same condition, then publishes a stopped-closure record and enters `stopped`. Restart reloads the set, restriction and per-record disposition exactly; it cannot reopen membership or reset allowances.

### Execution completion and recovery

A milestone becomes complete only after its required packets and supplements are resolved, dependency imports are valid, Quality Assurance has no failed or unverified required path, the milestone outcome review passes, and the verified milestone-to-master merge exists. The service publishes immutable UTF-8 JSON under `.maestro/execution/<execution-activity-id>/milestones/<milestone-id>/completion/versions/<version>/completion.json`.

The milestone record contains `schema_version: 1`; project, activity, registration, breakdown and milestone identities; configuration/schema hashes; baseline, branch and final merge commits; packet and integration queue results; review counts and references; supplement versions; dependency deliveries; Quality Assurance run and artifact references; non-blocking observations; repository-operation references; and start/completion times. SQL marks the milestone complete only after publication bytes and the remote merge are verified.

Successful Execution completion and stopped closure are different record variants:

| Variant | Eligibility and path | Required contents |
|---|---|---|
| `execution-completion@1` | Every authorized milestone has a verified completion record; no packet, correction, queue entry, run, question, stop action or external operation is active or uncertain; all branches are reconciled. Publish `.maestro/execution/<execution-activity-id>/completion/versions/<version>/completion.json`. | Exact registration/breakdown, configuration/schema hashes, ordered milestone-completion references and hashes, product-master start/final commits, unresolved-work assertion, retained non-blocking observations and `kind: "completed"`. |
| `execution-stop@1` | The recorded graceful-stop set has settled with no active or uncertain operation. Publish `.maestro/execution/<execution-activity-id>/stop/versions/<version>/stop.json`. | Exact registration/breakdown and configuration/schema hashes; completed milestone references; final reconciled master; every unfinished milestone, packet, supplement, queue/dependency entry and reason; final restrictions; retained observations; repository-operation references; and `kind: "stopped"`. It has no all-milestones-complete assertion. |

Publication uses the repository-operation journal. SQL advances to `completed` only after verifying the successful-completion bytes and every required remote merge; it advances to `stopped` only after verifying the stopped-closure bytes and the settled-set invariants. A lost acknowledgment reconciles the same version. Conflicting bytes or a changed final master head pause closure. The CLI renders a completion or stopped summary from SQL with the immutable repository reference and never presents a stopped closure as successful delivery.

Service restart reloads the activity, restrictions, settlement set, sessions, queue, review counts, environment/workspace cleanup state, artifact state, grants and pending repository journal. Known completed steps are not repeated. Unknown agent or Git outcomes remain blocked until observed or reconciled. Automatic recovery and configured manual retry retain the original assignment, source, target, deadline, review and allowance identities. Recovery cannot change models except through the configured backup rule, reset a review count, skip FIFO or weaken completion criteria.

### Authorized integration merges

The Integration Manager requests the packet-to-milestone merge after applicable integration checks and independent review pass. The service checks the exact approved result revision, current destination branch and standing project authorization before performing the merge. The same checks apply to milestone-to-master promotion after its outcome review and gap analysis pass. The Development Manager records the process outcome; it does not provide code approval.

Routine authorized merges at both levels do not require another Owner approval. This includes a passing milestone branch merging into `master`. A target change that invalidates integration or milestone evidence returns the affected assignment for reconciliation; approval of an earlier baseline cannot silently cover different code. The service must verify the remote result before recording merge success. No agent self-approval, protection bypass or unverified merge is permitted.

These are Execution code-delivery branches. Registration and architecture-package publication still use their saved authorized destination. Current Maestro documentation edits remain direct commits to `master`; writing this design does not create branches or launch implementation. Branch patterns, merge strategy, journal behavior and completion records are defined above; executable Git handlers and installed verification remain implementation work.

### Specialist assignment and architectural support

The Development Manager selects the applicable specialist role alongside the coder route and model. The service supplies and validates the exact packet, role, relevant starting context, source revision and permitted change boundaries before launch. Role descriptions and source-local context established by the architecture phase remain the basis of specialization; the manager cannot silently rewrite their authority.

If no role adequately covers a packet, the manager records the issue against that packet. The completed architecture loop's agent is not assumed still running. The service starts a bounded architectural-support assignment with the packet, existing roles and relevant confirmed architecture.

The architect determines whether an existing role covers the work. If none does, it may create a role and starting context within the already confirmed scope and architectural boundaries. The service validates and saves the result and notifies the manager to reconsider the packet; unrelated work continues. This support assignment does not restart the architecture loop.

A solution that changes scope, established responsibilities or the confirmed breakdown requires replanning under [replanning after re-registration](#replanning-after-re-registration). In-scope role additions follow [support validation and publication](#support-validation-and-publication); they do not rewrite the confirmed breakdown.

### Work disposition before re-registration

Determining that re-registration is required is separate from deciding whether current execution can continue. The architect recommends a disposition with reasons and affected work. The service presents the four choices as a linked CLI decision for the Owner. The Development Manager adjusts pending work to the recorded choice; the service enforces authorized stopping actions. Work already identified as blocked remains ineligible while awaiting the answer. Choosing a disposition does not itself start re-registration or replanning.

| Disposition | Effect |
|---|---|
| Continue unaffected work | Block affected packets and their dependants while valid unrelated work continues. |
| Stop new starts and finish safe running work | Let valid running assignments finish to reach idle state where the architectural issue requires a transition to re-registration. |
| Stop affected or all running work | Stop where continuing could produce invalid changes or undermine shared assumptions. |
| Finish current work and prioritize replanning | Deliberately stop all new packet starts even when unaffected queued work could continue; let running assignments finish and record their results so replanning can proceed promptly. |

The fourth choice is available regardless of whether further queued work is viable; it does not require waiting until execution is blocked. Work already identified as unsafe or invalid to continue still requires an explicit stopping decision.

For either finish-current-work disposition, the service prevents new packet starts. Already-started packets complete only the downstream lifecycle permitted by [pause and graceful-stop settlement](#pause-and-graceful-stop-settlement), including bounded review, correction and recovery. This is not limited to letting the current agent process exit. There is no special failure policy, retry prohibition or additional retry question for this transition. The Development Manager remains available to track results and unresolved operations.

The start restriction is saved with the execution activity and checked atomically when reserving a packet's first launch. Packets already reserved for launch at that decision are included in the recorded in-progress set; later stages for that set may continue. Queued packets without a reservation do not start. Restart preserves the restriction and membership. The existing lifecycle handles failures; failed or unresolved work is never marked complete merely to reach idle.

Once this set has settled under the normal lifecycle and all associated runs, support work and pending external operations are resolved, the service ends the execution activity and releases its project reservation. Unstarted packets remain unfinished for replanning and are no longer queued or reserved for execution. The service records this transition and reports that the project is ready for re-registration. An unknown run status or unresolved operation prevents that report.

The linked `owner.decision` action uses target `execution_work_disposition` and records request, project, execution activity, question and recommendation identities, expected activity version, selected choice, affected packet references and verified Owner identity. Stable choice values are `continue_unaffected`, `finish_safe_work`, `stop_affected_or_all` and `finish_current_for_replanning`, paired with the plain labels above. In one SQL transaction, validate the current recommendation and scope, save the choice and apply its pending-start restrictions. An identical replay returns the saved receipt; a stale or conflicting choice requires a refreshed decision. A written clarification alone does not authorize a stopping action. Process stopping is supervised and reconciled after that saved decision, never inside the transaction.

Re-registration still uses its explicit entry and existing idle checks. Re-registration, manual architecture start, confirmation and explicit execution start remain separate steps. General pause, resume, graceful stop, retry and completion behavior follows the [Execution API and state contract](#execution-api-state-and-record-contract) and [Execution completion and recovery](#execution-completion-and-recovery).

### Architectural-support configuration and fallback

The shared `/etc/maestro/agents.toml` uses `execution.architectural_support` for this bounded process. The following fields are relative to that table. At support-assignment creation, the service copies its configuration from the parent Execution activity's startup snapshot and saves that provenance with the assignment's remaining allowances. It does not reread later file edits as new routes, models, timeouts or limits. Replacement preserves the same assignment snapshot and consumed counts.

| Field | Type and meaning |
|---|---|
| `architect.primary.tool`, `architect.backup.tool` | Required `codex` or `claude_code`. |
| `architect.primary.model`, `architect.backup.model` | Required exact permitted model identifiers; no moving aliases or implicit model level. |
| `fidelity_reviewer.primary.tool`, `fidelity_reviewer.backup.tool` | Required `codex` or `claude_code`, independently configured from the architect. |
| `fidelity_reviewer.primary.model`, `fidelity_reviewer.backup.model` | Required exact permitted model identifiers. |
| `architect.run_timeout_seconds`, `fidelity_reviewer.run_timeout_seconds` | Required positive integers; deliberately selected for this process, not inherited from registration. |
| `maximum_fidelity_reviews` | Positive integer; default 2 completed reviews per support assignment. |
| `recovery.automatic_recovery_attempts` | Nonnegative integer; default 2 per role assignment after its initial run, shared across its primary and backup routes. |

Both role sections and their route fields are required; primary and backup must identify distinct tool/model pairs within each role. Unknown fields, invalid values or unavailable required runtime capabilities block affected support work with a clear error. Temporary primary-route unavailability is handled by fallback below, not mistaken for malformed configuration. Shared tool executable, permission and credential profiles remain under [adapter configuration](#adapter-configuration); agents do not receive service publication credentials.

The service checks model support, permissions, structured responses and actual model identity before accepting a run's result. Backup use is an explicitly configured selection, never a silent substitution. The separate Development Manager model selected at execution start and coder-route registry are not changed by this support configuration.

| Situation | Route handling |
|---|---|
| Primary unavailable, rate-limited or unable to provide the required capability before launch | Check and use the configured backup. A failed preflight without an agent launch does not consume a run-recovery attempt. |
| Failure during active work | Apply cause-based recovery first. Any replacement must wait for confirmed stopping. Use a backup only when recovery evidence establishes the primary cannot continue appropriately and the backup can; preserve consumed allowances. |
| Unsatisfactory assessment or failed fidelity review | Follow correction and review handling; do not switch models to obtain a different verdict. |
| Neither route is usable, or original stopping is uncertain | Pause affected work and display the reason through the CLI. No concurrent replacement or invented third route. |

A backup launch gets a new run and session identity linked to the prior run. It receives the same role assignment, exact source and artifact references, recorded decisions, verified progress and reason for switching. Unfinished output is diagnostic or draft evidence, not completed work. No failure, correction or review allowance restarts. A replacement launched for failure consumes the existing role-assignment recovery allowance; switching routes grants no additional attempts. Capacity-only continuation retains the shared context-management accounting.

The support architect uses its own session for this support assignment; it does not resume the completed architecture loop as new authority. A reviewer uses a separate session and cannot have authored or corrected the reviewed role. Its backup must also be eligible. Common model/provider use does not make shared author history independent. Reviewer handoff preserves reviewed input identities and remaining allowance; prior verdicts or author conclusions are not supplied as instructions for a fresh review. A targeted correction check receives only its authorized correction scope and evidence.

### Support validation and publication

Selecting an existing unchanged role requires validation of applicability and exact references, not another review of its contents. A newly created role and starting context require independent fidelity review against the confirmed architecture and affected packet. The architect corrects material findings; wording preferences do not force rework.

A valid completed review consumes one support review round. One pass is sufficient. Clarification, malformed output, technical failure and replay do not consume a completed-review round; technical failures retain recovery accounting. Review the role and starting context together, without another budget for each file. After a material amendment, recheck affected content and dependencies. At the configured limit, unresolved material issues keep the affected packet blocked and reach the Owner through the CLI; unrelated work continues. No automatic extra round, model switch or replacement assignment resets that limit.

At that limit, the service supplies the support architect the exact reviewed support version, findings, completed count and prior grants in a read-only follow-up under the same support assignment and configuration. The `support_limit_recommendation` response in `execution@1` carries the common response identities, exact support version/review references, count/grant snapshot, recommendation and rationale; stale or mismatched responses are rejected. It saves the architect's `grant_one` or `remain_paused` recommendation with rationale in SQL, then presents `owner.decision` with target `execution_support_fidelity_review`, bound to that support identity, version and review allowance. The typed grant adds one completed-review allowance only to that support assignment; it cannot activate the role, approve its contents or replenish another budget. `remain_paused`, missing recommendation or failed bounded recovery preserves the blocker. Replayed decisions cannot grant twice. A later exhausted grant requires another explicit Owner choice under the shared limit rules; no extra review is automatic.

The service assigns the support identity and permitted source-local paths before drafting, using the existing `role-<role-title>.md` and `context.md` formats. The architect returns the role, starting context, packet coverage and rationale. It cannot replace an existing role's authority or move source boundaries through this path. Deterministic checks verify required headings, identities, exact inputs, hashes, path permissions and absence of conflicts.

SQL owns the current support state, requests, questions, route history, review counts and active role bindings. Immutable UTF-8 JSON support records are published under `.maestro/execution/<execution-activity-id>/architectural-support/<support-id>/versions/<version>/` in the project's repository. Record identities are service-assigned, versions are positive integers, and coded references include plain subjects. The fixed files are `support.json`, `review.json` when a completed review exists, and `activation.json` when eligible. Each file carries `schema_version: 1`, project/activity/support identity, its version and exact input references. These are record contracts; executable validators remain implementation work.

| Record | Required contents |
|---|---|
| `support.json` | Exact registration and confirmed-breakdown references, affected packet references, source commit, assignment/run identities, configuration hash, chosen primary/backup routes and switch reasons, disposition (`use_existing`, `create_role` or `replanning_required`), plain rationale, role/context path-and-hash inventory, and preserved verified progress references. |
| `review.json` | Exact reviewed support version and inventory hashes, reviewed source/packet references, reviewer assignment/run and tool/model evidence, independence record, outcome (`APPROVE` or `REQUEST_CHANGES`), findings with impact and minimum correction, and completed-review count/limit. |
| `activation.json` | Support version, exact role/context references, affected packet bindings, review reference for a new role or explicit unchanged-role validation evidence, and the publication-operation identity. |

References to existing records use their established exact-reference formats. File inventories use repository-relative paths and SHA-256 hashes; published references include the exact Git commit. Files created in the same publication refer to one another by relative path and hash; the verified publication journal supplies their commit afterward, avoiding a self-referential commit field. The service publishes role/context files and eligible support records to the authorized project branch using wrapper checks and a durable publication journal. It verifies remote bytes before atomically recording the active support binding and notification in SQL. Lost acknowledgments reconcile the same intended bytes; conflicting content pauses without overwrite or duplicate activation.

This binding supplements the confirmed breakdown for the named packets; it does not edit their records or the confirmed manifest. New assignments carry both the unchanged confirmed reference and the exact activated support reference. Before use, the service rechecks applicability, review coverage and hashes. Changed relevant inputs invalidate that binding for affected work. A source or responsibility change requiring a new breakdown uses re-registration instead.

Only after required validation, review and publication verification does the service notify the Development Manager that the role is available. Partial drafts, an agent's completion claim or a successful review alone cannot dispatch a coder. No Owner approval is added for an in-scope role that satisfies this contract.

### Internal hooks

Required checks remain explicit in the service and wrappers. Internal Python hooks may organize genuinely shared behavior during implementation. A configurable hook framework is outside current scope. Hooks cannot make mandatory checks optional, create extra retries or become another source of process state or authority.

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
| Supply entry, scope, and both role selections | Registration request | Read overview references, apply [intake and scope](#intake-and-scope), and record the explicit [tool and model selection](#tool-and-model-selection). | Intended project, confirmed whole/partial boundary, and supported architect and reviewer selections before architect launch; an existing process is reused. | Missing access, source, or required clarity is reported; unsupported or unverifiable model selection prevents launch. No guessed documents or silent scope expansion. |
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
| Persistence | SQLite is selected under [SQLite storage](#sqlite-storage); physical tables and validators remain implementation work. SQL backup and restore are out of scope; ordinary service-restart and interrupted-operation recovery remain included. |
| Agent integration | Tool/model selection and shared adapter behavior are defined above. Tool transports, artifact handling, process supervision, and retry requests are specified above. Installed tool capability checks, model identity evidence, filesystem isolation, and systemd behavior require operational verification. Registration role responsibilities and response fields are defined; executable validation schemas remain implementation work. |
| Registration formats | Package records, index, and locations are defined above. Executable JSON Schemas and detailed source validation mechanics remain implementation work. Markdown source templates are defined in the Planning Guide. |
| Architecture loop | Behavioral and machine-readable contracts are defined above. Installed compatibility and implementation evidence remain under [architecture-loop implementation boundary](#architecture-loop-implementation-boundary). |
| Execution implementation | Execution behavior, configuration, records, review, integration, Quality Assurance, stopping, recovery and completion are defined under [Execution](#execution). The `execution@1` schema, API handlers, Git journals, adapters, isolated-environment supervisor, physical SQL tables and installed operational evidence remain implementation work. |
| Terminal behavior | Practical evaluation of message scrolling and the initial terminal dimensions. |
