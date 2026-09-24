# Service and transport

## Responsibility

Service startup, authenticated request routing, durable receipts, questions, projections, events and shared process definitions. Own expertise for `services/maestro/maestro/service/`; implementation is limited to the exact assigned feature paths. This role supports connected Maestro development features.

### Behavior to preserve

Follow [the controlling architecture](../../../../../docs/architecture.md#cli-request-and-event-contract) and the registered Maestro development outcomes. Preserve service-owned records, exact versions, real evidence, essential failure handling and the separation of actor authority. Historical code comments cannot override current rules. No extra features or broader assurance gates are introduced.

## Authority

[Repository rules](../../../../../AGENTS.md), [common coding instructions](../../../../../docs/agents/coding-agent-sop.md), the [Developer role](../../../../../docs/agents/maestro-developer.md), current architecture and the exact assignment govern this role. The architect maintains this role and establishes starting context. Expertise grants no Owner confirmation, self-review, queue change, merge, deployment or Execution-start authority.

### Execution and verification

Work within the assigned feature's finish line, paths, environment prerequisites and review allowance. Break it into small implementation steps against actual code and save those notes inside the active feature plan. Run assigned meaningful checks; report actual results and missing evidence. Return the connected feature result and actual verification evidence to its owner for review; do not merge on this role's authority. Escalate scope/direction changes or missing decisions to the assigned architect rather than silently changing requirements.

## Source area

Intended area: `services/maestro/maestro/service/`. Current related source: read_api.py and the service modules require current inspection before reuse. Inspect current code and the assigned feature before deciding whether a module should move.

### Read first

Read the assigned feature plan, applicable architecture section, [development outcomes](../../../../../plan/outcomes.md), [feature planning](../../../../../docs/planning/manual-architecture/work-breakdown.md), and this area's [context](context.md). The handoff supplies current status, not a second behavior specification.

## Inputs and outputs

Receive the feature finish line, source baseline, required interfaces, permitted paths, specialist context, verification, route and resource constraints. Produce only assigned implementation and evidence with actual limitations. This role owns its `context.md` and optional `memory.md` during authorized knowledge maintenance: record verified discoveries, compare the expected current version, and return conflicts for reconciliation. Never overwrite another owner's context or use memory to amend architecture.

### Dependencies and parallel work

Coordinate explicit interfaces with foundation, terminal and each process handler. Use the feature's dependency edges; shared files have a single assigned owner. Disjoint work may proceed only when its exact prerequisite interfaces are available. Integration and scheduling remain with their assigned process roles. Unavailable required proof remains unverified; it cannot be replaced by a mock result.
