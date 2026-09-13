# Maestro — Project Overview

## Project identity

| Field | Value |
|---|---|
| Project name | Maestro |
| Repository | https://github.com/jmiedreich-ux/Maestro |
| Responsible architect | Jeremy Miedreich and the software architect agent; human and agent responsibility |
| Document version | 1 |

## Purpose

Maestro coordinates project development through Planning, Execution, and Monitoring. A persistent service connects project information, assigned agent activity, and an operator interface so declared outcomes can be delivered and assessed through their actual usage journeys.

## Overall scope

| Boundary | Description |
|---|---|
| Included in the supplied declarations | A Linux-based CLI/service foundation for multiple projects, reliable question responses, project registration, versioned registration updates, and recovery. |
| Broader system boundary | Planning, Execution, and Monitoring are system areas. Detailed execution authority and a complete development engine are not defined by the supplied declarations. |
| Excluded from initial interface scope | Command center, mobile presentation, unsolicited agent conversations, cross-project draft retention, and execution commands. |
| Excluded from registration | Project implementation, development-milestone/work-packet breakdown, automatic work startup, general code audits, architecture approval, and execution-rule overrides. |

## Current state

| Capability or area | Current condition | Evidence level | Evidence or authoritative source | Known missing prerequisites |
|---|---|---|---|---|
| CLI/service foundation | Specified; current integrated operation not verified | Reported | `docs/maestro-cli-project-milestones.md` | Installed setup, project/question provisioning, context and connection contracts. |
| Registration and history | Specified; current integrated operation not verified | Reported | `docs/maestro-registration-project-milestones.md` | Agent/adapter contracts, publication access, package schema, work-state enforcement, persistence consistency. |
| Existing service components | Source evidence from the recorded revision below; current capability not established by that evidence | Supported by source inspection at the cited revision only | Source observations below | Current source validation and actual operational evidence before claiming dependency readiness. |
| Architecture and source documents | Supplied design material, not operational evidence | Not applicable to implementation status | Authoritative source list below | Unresolved mechanisms are identified in the architecture and declarations. |

### Source observations

The following previously recorded inspection is tied to source commit `8d1448473c7f95fa830fac9e49d36b8cdb7cf17d`. It does not establish the current source state or operation of the AI box.

| Existing material | Evidence and limitation |
|---|---|
| Registration command and onboarding function | [Command-line interface](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/cli.py) and [project onboarding](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/project_onboarding.py) contain registration code. The onboarding function also requires graph, work-item, and run inputs; it is not evidence of the newly agreed registration-only boundary. |
| Reporting service commands | The command route table in [reporting service](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/read_api.py) exposes decision and crash commands, not a registration entry point. |
| Agent subprocess adapter | [Executor](https://github.com/jmiedreich-ux/Maestro/blob/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d/services/maestro/maestro/executor.py) starts a local agent and reads commit evidence. Active process handles are in memory; this alone does not establish the required recovery or GitHub push verification. |
| Linux service startup | The repository tree at the baseline contains no `.service` unit file. This does not establish what may be installed on the AI box. |

No current service installation, account access, real agent routing, or complete CLI/registration journey is established by these source observations. Missing operational evidence is not treated as proof that the dependency is ready.

## Authoritative sources

| Source type | Subject or designation | Repository-relative location |
|---|---|---|
| Architecture | Maestro system behavior | `docs/maestro-architecture.md` |
| Milestone declaration | CLI — Command-line interface | `docs/maestro-cli-project-milestones.md` |
| Milestone declaration | REG — Project registration | `docs/maestro-registration-project-milestones.md` |

Registration entry uses `docs/maestro-project-overview.md` within the repository. The [Planning Guide](planning-guide/README.md) governs source format and conventions.

## Unresolved information

| Missing or conflicting information | Affected source or capability | Clarification needed |
|---|---|---|
| Current implementation and operational evidence | Dependencies in both declarations | Establish the actual condition before claiming existing capability. |
| Initial project/question source and process context | CLI entry and response journey | Resolve the named mechanisms in `docs/maestro-architecture.md#constraints-and-unresolved-details`. |
| Agent, persistence, and work-state interfaces | Registration journeys | Resolve the architecture mechanisms and declaration-specific dependencies before affected development breakdown. |

No narrower registration portion is selected by this overview. A registration request supplies its chosen boundary using the declaration references.
