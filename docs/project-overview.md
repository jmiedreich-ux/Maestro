# Maestro — Project Overview

## Project identity

| Field | Value |
|---|---|
| Project | Maestro |
| Repository | https://github.com/jmiedreich-ux/Maestro |
| Owner | Jeremy Miedreich |
| Responsible architect | Jeremy Miedreich and the software architect agent |

## Purpose

Maestro coordinates project development through Planning, Execution, and Monitoring. Its persistent Linux service and terminal workspace connect project sources, decisions, assigned agent work, integration, quality checks, and current progress.

## Product scope

Included product behavior is specified in [the architecture](architecture.md) and these outcome areas: [runtime service](outcomes/runtime-service.md), [CLI](outcomes/cli.md), [registration](outcomes/registration.md), [architecture loop](outcomes/architecture-loop.md), and [Execution](outcomes/execution.md). Monitoring is included through service activity, CLI attention and Execution status. Ordinary restart and recorded-operation recovery are included.

Command center, mobile presentation, unsolicited agent conversations, cross-project draft retention, SQL backup/restore, automatic initial Execution startup, and automatically authorized production testing remain outside the initial scope. A product process does not start merely because its architecture is documented.

## Current condition

The Owner reports previous implementation through initial registration. Master contains Python source and tests for service, agent, terminal and registration paths. Assess that code for reuse and adaptation against the current outcomes before planning new implementation. Source presence and the reported extent do not establish installed or integrated acceptance; current host, credential, model-route, repository and end-to-end evidence must be checked. No outcome in the roadmap is marked completed here.

## Authoritative development sources

- [Ordered outcome roadmap](planning/outcomes.md): what building Maestro must deliver and in what dependency order.
- [Development environment](outcomes/development-environment.md): prerequisite result to prove first.
- [Feature planning](planning/manual-architecture/work-breakdown.md) and [delivery rules](planning/manual-architecture/packet-rules.md): how Maestro itself is built.
- [Current manual development registration](planning/manual-registration.md): the accepted planning boundary and source selection.
- [Architecture](architecture.md) and [product outcome details](outcomes/): what Maestro must do. These do not govern the manual development workflow.

The repository and this overview are the project entry point. Product behavior, development planning and current implementation evidence are kept separate.
