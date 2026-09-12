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

This is a working proposal, subject to change as Maestro is designed. It is not a fixed specification or an instruction to implement the process.

### Maestro Planning Guide

A future Maestro Planning Guide will define the conventions and formats project architects use for their planning outputs so Maestro can understand and use them. The guide and its required inputs remain to be designed.

### Registration entry points and purpose

Planning begins with project registration, initiated from either the command line or the command center within the Reporting and Command Interface. Both entry points would use the same registration process.

Registration would identify the project, confirm repository access, locate planning material, check compatibility with the guide, and present the result for confirmation. It checks whether Maestro can understand and work with the supplied plan; it does not approve the architecture, rewrite the plan, or start development.

### Proposed registration process

| Step | Proposed mechanism |
|---|---|
| Receive the request | The user supplies the repository location through either entry point. |
| Identify the project and confirm access | Python records the project name, repository, and responsible project architect, checks read access, and reports missing permissions. |
| Read a specific version | Python reads the repository at a recorded Git commit so the review covers a known source version. |
| Locate planning inputs | The guide could require a small registration file listing project details and the locations of planning documents and project-specific working rules. |
| Check format and completeness | Python checks required fields, file locations, document structure, and references against the guide. |
| Check meaning and consistency | An architect agent reviews the material for unclear instructions, suspected contradictions, and missing information that structural checks cannot detect. |
| Present the registration report | Maestro combines the findings into a plain summary of what was found, what needs attention, and whether the project is ready to register. Issues point to the relevant file and passage where available. |
| Resolve issues and confirm | The project architect supplies corrections, and Maestro repeats the checks. Once issues are resolved and registration is confirmed, Python saves the registration and reviewed source version. |

The architect agent reports issues; it does not resolve contradictions, invent missing answers, or rewrite the plan. The registration file, division of work, and confirmation mechanism remain subject to design.

