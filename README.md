# Maestro

Maestro is a project-neutral development-operations system for controlled AI-assisted engineering work.

It provides the shared process, durable execution state, local Atlas reporting, and project adapters needed to take one approved milestone through bounded work, evidence, review, and owner acceptance.

Current status (2026-09-09): **a substantial implementation exists, and the
product does not yet function end to end.** The durable state layer — schema,
validated commands, idempotency, optimistic versioning, immutability triggers —
is built and heavily tested. Most of the *actors* that would call those commands
in production are not: six of the nine designed agent roles exist only as string
literals, nothing parses the work graph, and Maestro's own loop has never driven
a packet from dispatch to acceptance. One packet (`CG-M4-19`, against Foundry,
2026-09-06) was completed by a real model, hand-driven through the CLI.

The development-manager loop currently **records its own approval**
(`services/maestro/maestro/development_manager.py:329-334` writes
`result="Approve"` from a readiness boolean under the actor literal
`development-manager-loop-independent`), so durable records asserting an
independent review and an Owner acceptance for M4 packets do not reflect a
review that happened. Treat them as a known defect, not as evidence.

**Read [M0-D18](docs/planning/decisions/m0-d18-real-wiring-audit-authority-and-architect-loop.md)
for governing authority and
[M0-D19](docs/planning/decisions/m0-d19-next-milestone-round.md) for the current
plan before scoping any Maestro work.** They supersede earlier planning
documents on conflict, including
[the master plan](docs/planning/maestro-master-plan.md), which remains useful
for design intent and history.

The planned agent organization, specialist queues, parallel scheduler, Atlas control plane, and standard operating procedure are in [Agent Workforce Control Plane](docs/planning/agent-workforce-control-plane.md) and the [Agent Role Library](docs/agents/). The reconciled M0 inputs are recorded in the [Source Inventory](docs/planning/m0-source-inventory.md), including the preserved [agent-workforce planning source](sources/planning/2026-08-29-agent-workforce-conversation.md) and its [independent audit](docs/planning/agent-workforce-capture-audit.md); the current continuation point is [Current Handoff](ai/handoffs/current.md).
