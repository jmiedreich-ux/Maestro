# Maestro Architecture

## Document status

This document records the architecture being developed with the Owner. Confirmed foundations and evolving proposals are distinguished below. Proposals are subject to change and do not authorize implementation.

The [Maestro Information Review](maestro-information-review.md) remains separate reference material. Its rules and implementation details are not automatically decisions for this architecture.

## Confirmed foundations

- Maestro covers three major functional areas during project development: Planning, Execution, and Monitoring.
- The runtime is a Python backend running as a Linux service on the AI box, managed by `systemd`, communicating with agents through command-line tools or APIs.
- A future Maestro Planning Guide will define conventions and formats for project architects' planning outputs.
- Planning begins with project registration, initiated through the command line or the command center.

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

The earlier shared-record and restart design was withdrawn as an assumed architecture. State storage and restart recovery appear below only as evolving runtime concepts, not as an agreed storage design.

## Runtime

Maestro's runtime is a backend program written in Python, running continuously as a Linux service on the AI box.

It runs under `systemd`, which starts it when the machine boots and restarts it if it crashes. The program launches agent processes and communicates with them through their command-line tools or APIs.

### Evolving runtime concepts

These are working concepts, not fixed architectural requirements or implementation instructions. Their names, boundaries, and responsibilities may change as Maestro is designed.

| Proposed part | Working responsibility |
|---|---|
| Command handling | Receive requests to start, pause, resume, or stop work from the Reporting and Command Interface. |
| Work coordination | Determine which approved action can run next and start it when the required resources are available. |
| Agent connections | Launch agents through their command-line tools or APIs, supply instructions, and receive results. |
| State storage | Record what is running, finished, or waiting to support recovery after a service restart. |
| Health supervision | Watch agent activity, deadlines, and failures, then apply agreed recovery or stopping rules. |

These parts could initially be modules within one Python service rather than separately deployed services.

The proposed boundary is mechanics versus judgment: the runtime enforces an agreed review requirement and receives and validates the assigned reviewer's result. A successful command does not itself count as approval.

Planning, Execution, and Monitoring could use these shared mechanisms. This sketch does not define their responsibilities or grant them decision-making authority; those will be defined separately.

## Planning: evolving registration concepts

This section records agreed registration concepts and explicitly labeled proposals. The design can evolve through further agreement; it is not an instruction to implement the process.

### Maestro Planning Guide

A future Maestro Planning Guide will define the conventions and formats project architects use for their planning outputs so Maestro can understand and use them. The agreed input categories are below. The guide's detailed formats remain to be designed.

### Registration entry points and purpose

Planning begins with project registration, initiated from either the command line or the command center within the Reporting and Command Interface. Both entry points would use the same registration process.

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
| Receive the request | The Owner supplies the repository location and selects the whole plan or a defined portion through either entry point. If registration is already active, show its status instead of starting another. |
| Identify the project and confirm access | Python records the project name, repository, and responsible project architect, checks read access and that the repository belongs to the intended project, and reports missing permissions. |
| Read a specific version | Python reads the repository at a recorded Git commit shared by both reviewers. Relevant source changes are flagged for an explicit Owner choice before confirmation. |
| Locate planning inputs | The guide could require a small registration file listing project details and the locations of authoritative planning documents. Working rules belong to Execution, not registration. |
| Check format and completeness | Python checks required fields, file locations, document structure, and references against the guide. |
| Check meaning and consistency | The Maestro architect reviews milestone purpose and scope, outside dependencies, and claimed existing capabilities through targeted source checks. It reports unclear instructions, contradictions, missing essentials, and the level of supporting evidence. |
| Independently review the findings | A separate reviewer checks fidelity to the project's source material and whether blockers are justified. The Maestro architect can amend its report; rechecks cover affected findings only, within the configured review limit. |
| Present the registration report | Maestro combines the findings into a plain summary of what was found, what needs attention, and whether the project is ready to register. Issues point to the relevant file and passage where available. |
| Resolve issues and confirm | The project architect supplies needed source corrections. Maestro rechecks affected findings within the configured review limit. When no blockers or unresolved disagreements remain, the Owner confirms the versioned registration package through the command line or command center, making it active. Non-blocking findings do not prevent registration. |

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

The Owner gives final confirmation through either the command line or command center. Confirmation accepts the registration package and activates that registration version; it does not start development.

### Machine-first package storage

Store the registration package in the project's own GitHub repository, with a separate folder for each registration version. The Maestro Planning Guide defines the folder location and consistent filenames.

Optimize the package for agents and Python:

- Structured JSON is authoritative, with a defined schema.
- A small index identifies records, registration and source versions, and relationships through explicit references and relative links.
- Use small, focused files so agents load only what they need.
- Keep plain-language descriptions inside the structured records.
- Python validates required fields and references.

Each fact has one authoritative location. The command center renders the same package; human-readable reports are generated from it, not maintained as competing sources of truth. The next planning process uses the exact confirmed package version.

### Source changes during review

Each review uses an exact Git commit. The Maestro architect and independent fidelity reviewer use the same source version.

If relevant planning inputs change, Maestro flags that the reviewed version is no longer current and shows the changes before confirmation. It does not silently mix source versions.

| Owner choice | Treatment |
|---|---|
| Finish with the reviewed source version | Registration explicitly covers the original requirements. Newer changes are not included. |
| Include the updated source version | Update the candidate package and recheck affected findings within the existing review limit. Do not silently reset the two-round limit. |

This applies to changes in planning inputs, not unrelated commits or the registration reports themselves.

### Duplicate registration requests

Only one registration process may be active per project. A second request from either interface shows the existing process's current status rather than starting a competing process or creating another version.

### Registration visibility and Owner responses

Both the command line and command center show:

- The current step and working agent.
- The review round and configured limit.
- Blockers, non-blocking findings, and technical failures.
- Whether registration is progressing, paused, or waiting for the Owner.
- Decisions needed from the Owner and the relevant findings.

A decision request provides a specific question, relevant findings, and the affected registration version. The Owner submits a choice or written clarification through either interface.

Maestro records the response against that request in the registration package. The runtime routes it to the paused step; the architect amends its report if needed, and affected findings are rechecked within the existing review limit.

If a response is ambiguous, Maestro asks for clarification rather than treating it as approval. Answering a question is not final registration confirmation; confirmation remains a separate explicit action.

### Changes presented for confirmation

Before re-registration confirmation, compare the candidate package with the active registration version. Show:

- What was added, changed, or removed.
- Affected project milestones, scope boundaries, and completion requirements.
- Why each change was made, with links to findings or Owner decisions.

The Owner confirms the exact candidate version shown. That confirmed package must not silently change afterward.

### Partial-project registration

Through either interface, the Owner chooses the whole supplied project plan or specific project milestones.

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
