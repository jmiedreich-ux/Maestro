# Maestro Registration — Project Milestone Source

## Identity and document status

| Field | Value |
|---|---|
| Project | Maestro |
| Capability covered | Project registration |
| Repository | https://github.com/jmiedreich-ux/Maestro |
| Owner and human project architect | Jeremy Miedreich |
| Authoring role | AI assistant acting as the project architect |
| Intended reader | Maestro architect performing a later registration review |
| Document version | 3 |
| Declaration | REG — Project registration |
| Status | Proposed project milestone source for Owner review; not a registration package or approval |
| Architecture baseline | [Maestro Architecture at the reviewed source commit](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/docs/maestro-architecture.md) |

This is the project architect's input to registration. It describes project outcomes, not development milestones or work packets. The proposed milestone grouping and order below translate the agreed architecture into project planning; they do not change its requirements.

The Maestro Planning Guide's exact source format is not yet defined. This Markdown document uses consistent, plainly worded sections as a provisional source format. The machine-first JSON requirement applies to the registration package Maestro will produce, not an invented registration record in this document.

A later registration review must assess this source on its merits. Authorship by the same assistant does not count as independent review, successful registration, or Owner confirmation.

## Purpose and scope

An Owner can submit project planning material, obtain a bounded and evidence-based assessment, answer questions, and confirm an exact registration package through either the command line or command center. The process remains usable when inputs change, registration is repeated, or technical operations fail.

Included: source intake, full or partial project coverage, targeted dependency checks, genuine independent fidelity review, Owner interaction, package publication, version activation, re-registration, and recovery. Startup, repository access, agent access, and connected interfaces needed for these outcomes are included prerequisites, not assumed completed work.

Excluded: development-milestone and work-packet breakdown, implementation of the registered project's features, automatic development startup, general code audits, general architecture approval, and execution-rule overrides. Source-code working rules remain part of Execution. Registration reporting and commands are included; unrelated Reporting and Command Interface features are not.

Exclusions cannot remove an essential operation while preserving the claim that registration works. Any required narrowing of a milestone's purpose must be explicit with the Owner.

## Architecture and current state

The runtime is a Python backend running as a Linux service on the AI box, managed by `systemd`. It connects to agents through command-line tools or APIs. Python performs deterministic checks; the Maestro architect assesses meaning and scope; a separate fidelity reviewer checks its findings. The Owner alone confirms registration.

The command line and command center use the same registration process. The project's GitHub repository holds the versioned, authoritative JSON package. The command center renders those records rather than maintaining an independent copy.

The five runtime module concepts remain evolving. This source does not choose a new database design, model provider, agent harness, credential mechanism, or authentication protocol.

Targeted source inspection at the architecture baseline found:

| Existing material | Evidence and limitation |
|---|---|
| Registration command and onboarding function | [Command-line interface](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/cli.py) and [project onboarding](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/project_onboarding.py) contain registration code. The onboarding function also requires graph, work-item, and run inputs; it is not evidence of the newly agreed registration-only boundary. |
| Reporting service commands | The command route table in [reporting service](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/read_api.py) exposes decision and crash commands, not a registration entry point. |
| Agent subprocess adapter | [Executor](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/executor.py) starts a local agent and reads commit evidence. Active process handles are in memory; this alone does not establish the required recovery or GitHub push verification. |
| Linux service startup | The repository tree at the baseline contains no `.service` unit file. This does not establish what may be installed on the AI box. |

These are source observations, not operational verification. No milestone below is claimed complete. Host setup, service-account access, real agent routing, and the integrated journey have not been exercised in preparing this document. Existing components may be reused only where they meet the stated outcomes.

## Project milestone outline

All three milestones are required for the registration capability described here. The order is a proposed delivery sequence, not a development breakdown.

| Position | Project milestone | Outcome | Priority and dependency |
|---|---|---|---|
| 1 | REG-PM1 — Register and confirm a project through either interface | A real, connected initial registration reaches explicit Owner confirmation and a usable package in GitHub. | First; includes its startup, access, guide, validation, review, and publication prerequisites. |
| 2 | REG-PM2 — Update a registration without losing approved history | Re-registration safely changes coverage or project milestones and activates only the exact version the Owner confirms. | Second; depends on REG-PM1 — Register and confirm a project through either interface. |
| 3 | REG-PM3 — Recover registration without losing decisions or exceeding limits | Interrupted registration resumes correctly or pauses visibly within separate technical and review limits. | Third; depends on REG-PM1 — Register and confirm a project through either interface and REG-PM2 — Update a registration without losing approved history. |

**Cross-declaration prerequisite:** CLI-PM2 — Reliable project questions and answers in the [CLI declaration](maestro-cli-project-milestones.md), following CLI-PM1 — Connected multi-project CLI workspace, precedes registration development.

**Scope status:** The both-interface registration scope and startup allocation remain draft material requiring alignment with the CLI-only architecture.

## REG-PM1 — Register and confirm a project through either interface

**Purpose:** The Owner can register a whole project or defined portion without assembling disconnected components by hand.

**Scope:** The Planning Guide needed for source preparation; service startup and access; intake; source and dependency checks; bounded reviews; naming; status and decisions; exact package publication and confirmation.

**Usage walkthrough:** Start the Python service using documented Linux setup. Provide a readable project repository and scope from either interface. Observe Python checks and two distinct agent roles. Resolve a genuine finding through the interface. Inspect the candidate package, confirm it, and retrieve the exact confirmed version from GitHub. Repeat the journey from the other interface.

### Acceptance criteria

| Condition | Required result and pass boundary | Verification and evidence |
|---|---|---|
| The Owner follows startup and access instructions | The Python service runs under `systemd`, starts on boot, and can reach the configured agents and project repository using real authorized access. No missing service account or unpublished manual command is needed to reach intake. | Startup and connection evidence from the AI box, including a service restart and boot-start verification; record configuration references without secret values. |
| Source prepared using the Planning Guide is submitted | Python can locate and validate identity, scope, architecture, current state, project milestones, project-level completion requirements, and authoritative document locations. The responsible project architect may be a person, an agent, or both. Missing required inputs are identified specifically. | Guide and validation-format references, source commit, accepted input record, and a rejected-input example identifying the missing field or document. Coding rules are not demanded as registration inputs. |
| Whole-project or partial-project scope is selected | The candidate records included outcomes, explicit exclusions, partial-milestone boundaries, and outside dependencies. Missing essentials produce a finding, not a silent scope expansion. | Inspect candidate boundaries and a dependency finding. Include a targeted source check distinguishing reported existence, source-supported implementation, and operationally verified behavior. No full code audit is required. |
| A milestone promises a usable capability | The architect records its usage journey, prerequisite coverage, and completion evidence. Essential operations cannot be excluded while the completion claim remains unchanged. Optional improvements do not block. | A source-backed assessment showing how required connections are covered and why each blocker prevents the stated purpose; a non-blocking finding retained without preventing readiness. |
| The architect submits findings for review | A separate agent performs fidelity review against the same source commit. The architect may amend its report. Rechecks cover affected findings only. With the configured initial maximum of two rounds, unresolved blockers or disagreement pause and reach the Owner; readiness may occur after one round. | Distinct architect and reviewer results, source references, amendments, and round counts. No invented reviewer approval, extra requirements, automatic third round, or forced approval. |
| The Owner needs to understand or answer registration | Both interfaces show the current step, working agent, round and limit, findings, failures, and progress or waiting state. A choice or written clarification is recorded against its question and version, routed back to the paused step, and retained with affected milestones or criteria. Ambiguous responses request clarification. | Connected command-line and command-center records of the same process, including a decision and resumed step. Answering a question does not confirm registration. |
| A second registration request arrives for the same project | Either interface shows the existing active process; no competing process or new registration version is created. | Submit duplicate requests across both interfaces and inspect the single process and candidate. |
| Relevant planning inputs change during review | Both agents retain a consistent source version. Before confirmation, the Owner sees the change and chooses to retain the reviewed source or update the candidate and recheck affected findings. The two-round limit is not silently reset. Unrelated commits or report updates do not count as input changes. | Before-and-after source references, Owner choice, resulting candidate, and unchanged review-budget accounting. |
| A candidate is ready for confirmation | The package contains the summary, supplied project milestone outline, project-level completion requirements, review records, and retained Owner decisions. Exact content versions are identified. It contains no generated development breakdown. | Inspect the JSON package against the defined output schema and index; validate required fields and references. |
| The Owner confirms from either interface | Only explicit confirmation makes the exact candidate active. That version is available in the project's GitHub repository; confirmation does not launch development. The confirmed contents cannot silently change afterward. | Owner confirmation tied to the candidate, authoritative GitHub commit and package location, active-version record, and evidence that no development was started. |

### Definition of done

Every acceptance row passes with recorded evidence from the connected system. The package is retrievable from GitHub, renders from the same data in the command center, and can be read by the next process without depending on mutable latest files. Actual downstream milestone breakdown is not required or performed here.

Startup, credentials, agent calls, Owner responses, and publication are exercised—not replaced by test-data screens or manually fabricated approvals. Required reviews and evidence are complete. Any accepted limitation is recorded explicitly and cannot remove an essential operation while this milestone retains its purpose.

## REG-PM2 — Update a registration without losing approved history

**Purpose:** The Owner can revise an existing registration while preserving the prior approved version and controlling exactly what becomes active.

**Scope:** Idle-only re-registration, project milestone additions or amendments, version history, candidate comparison, and explicit activation or cancellation.

**Usage walkthrough:** With an active registration, attempt re-registration while project work is active. Finish or explicitly stop that work, then rerun registration. Review an added or amended project milestone and the comparison with the active package. Confirm one candidate; separately demonstrate a failed or cancelled candidate leaving the previous version active.

### Acceptance criteria

| Condition | Required result and pass boundary | Verification and evidence |
|---|---|---|
| Project work is active | Re-registration cannot begin until all active work finishes or is explicitly stopped. Once re-registration begins, no new project work can start until it ends. | Runtime work-state evidence and rejected start attempts through the supported interfaces. The work-state and start-inhibition connection is an explicit dependency, not a checkbox supplied by the reviewer. |
| An idle project is re-registered | Create the next registration version while preserving previous versions. Additions or amendments concern project milestones, not development milestones or work packets. Apply the same fidelity loop and two-round configured limit. | Successive version folders, source and milestone versions, and real review records. |
| A candidate differs from the active version | Show additions, changes, removals, affected scope or completion requirements, and reasons linked to findings or Owner decisions. | Comparison visible before confirmation, tied to the exact candidate. |
| The Owner confirms the candidate | The candidate becomes active only on explicit confirmation. Previous records remain retrievable. Item identities remain stable; changed items increment versions and unchanged items retain theirs. | Confirmation, version references, and GitHub history comparison. |
| Re-registration fails or is cancelled | The previous registration remains active. Project work does not automatically restart. | Failure or cancellation record, unchanged active-version reference, and observed stopped-work state. |

### Definition of done

All acceptance rows pass against the registration delivered by REG-PM1 — Register and confirm a project through either interface. Retained history and candidate comparison are usable through both interfaces. The actual work-state and start-inhibition connection is demonstrated; absent execution controls cannot be disguised as successful enforcement. No complete project execution engine is required beyond that bounded dependency.

## REG-PM3 — Recover registration without losing decisions or exceeding limits

**Purpose:** Technical interruptions cannot erase completed review work, fabricate completion, or create unlimited retries.

**Scope:** Recovery checkpoints, wrapper checks, separate technical retry limits, visible pauses, and continuity of both initial and repeated registration.

**Usage walkthrough:** Interrupt an agent operation, a GitHub publication, and the service itself during controlled non-production exercises. Resume from the last verified step, preserving reports and Owner responses. Demonstrate the configured technical limit being reached without consuming planning review rounds or falsely activating a candidate.

### Acceptance criteria

| Condition | Required result and pass boundary | Verification and evidence |
|---|---|---|
| An agent crashes, a push fails, or the service restarts | Preserve completed reports, reviews, and Owner decisions. Resume from the last verified step; unverified results are not treated as completed. | Before-and-after records for each interruption, resumed step, and retained exact source and candidate versions. |
| A delegated operation requires a GitHub commit | The wrapper checks the expected repository and branch, committed and pushed changes, remote commit existence, permitted changed files, and agreement with the reported commit. A local commit or agent assertion alone cannot pass. Read-only reviews do not require unnecessary commits. | Wrapper results and remote GitHub evidence for successful publication and a deliberately unsuccessful publication. |
| Technical retries occur | A separate configurable technical limit applies. Technical failures do not consume planning review rounds. At the recorded technical limit, registration pauses and alerts the Owner instead of retrying indefinitely. | Configuration value used, retry count, unchanged planning-review count, and visible Owner alert. No numeric default is invented by this source. |
| Recovery concerns a re-registration candidate | Preserve the previous active registration until explicit confirmation of the recovered candidate. Failure or cancellation does not restart project work. Duplicate requests still return the existing process. | Active and candidate version records, duplicate-request result, and work-state evidence after recovery. |

### Definition of done

Each interruption has been exercised against the connected registration process, with evidence that records and review budgets remain correct. REG-PM1 — Register and confirm a project through either interface and REG-PM2 — Update a registration without losing approved history still behave as specified after recovery. Recovery capability is not complete merely because retry functions exist.

## Required prerequisite coverage

These dependencies are not claimed ready merely because related files exist.

| Dependency | Coverage |
|---|---|
| Running Python service, Linux startup, GitHub access, agent availability, and both registration interfaces | Included in REG-PM1 — Register and confirm a project through either interface. Account setup and access instructions must make the real journey possible; this source does not choose a credential mechanism. |
| Planning Guide, source conventions, output schema, index, and package location | Included in REG-PM1 — Register and confirm a project through either interface. Detailed format selection is implementation specification work, not an assumed existing validator. |
| Sequential identifiers with plainly worded subjects, stable identities, separate item versions and review rounds, non-reused retired identifiers, and an Owner-extendable naming list | Required across the milestones, using the architecture's naming conventions. Relationships remain explicit rather than encoded into identifiers. |
| Live project work-state reporting and prevention of new starts | Required by REG-PM2 — Update a registration without losing approved history. If not already available, the bounded connection must be delivered; a complete downstream execution workflow is outside this source. |
| Checkpoint persistence and separate technical retry configuration | Included in REG-PM3 — Recover registration without losing decisions or exceeding limits. Storage internals and the technical retry value remain explicit implementation choices. |

## Package expectations for the delivered capability

The produced registration package belongs in the registered project's GitHub repository, in a separate folder per registration version. Its authoritative records are small, focused JSON files with plain descriptions, schema validation, an index, exact source and record versions, and valid relative references. Human-readable views are generated from those records, not separately maintained truth.

Package coverage is the chosen portion of a project, not an implicit claim about the whole project. Owner clarifications, scope decisions, and accepted limitations remain linked and available to later agents.

## Specification boundaries

This source does not assign an exact JSON schema, package-folder path, agent provider, credential mechanism, technical retry default, or database implementation. Their required behavior is defined above; choosing and documenting workable details is included in the relevant milestone before it can be declared complete.

No automatic registration approval, review outcome, execution authorization, or operational success is recorded by this document. No accepted implementation exceptions have been supplied for these milestones. Proposed implementation exceptions must be recorded and explicitly accepted; they cannot silently weaken the purpose.

## Source fidelity and preparation check

The author manually checked the source against the architecture's registration requirements and the seven agreed input categories. This is a project-architect preparation check, not an independent fidelity review or a registration result.

| Architecture subject | Where covered |
|---|---|
| Identity, scope, architecture, current state, planned work, acceptance, document locations | Identity through project milestone sections and the linked architecture baseline |
| Shared planning; breakdown after registration | Scope, milestone outline, and REG-PM1 — Register and confirm a project through either interface |
| Naming and stable versions | Project milestone outline, prerequisite coverage, and REG-PM2 — Update a registration without losing approved history |
| Purpose walkthroughs; good-enough findings; independent review; two-round limit | REG-PM1 — Register and confirm a project through either interface |
| Machine-first outputs; source changes; partial scope; targeted source checks | REG-PM1 — Register and confirm a project through either interface and package expectations |
| Both interfaces; duplicate requests; Owner responses and retained decisions; final confirmation | REG-PM1 — Register and confirm a project through either interface |
| Idle-only re-registration; comparisons; history; activation | REG-PM2 — Update a registration without losing approved history |
| Wrapper evidence; interrupted work; separate technical retries | REG-PM3 — Recover registration without losing decisions or exceeding limits |
| No full audit, execution-rule overrides, automatic development start, or invented missing requirements | Scope, acceptance criteria, and specification boundaries |

The architecture remains the design authority. If a later source revision changes a requirement, review the affected milestone and retain the exact source version rather than silently mixing versions.
