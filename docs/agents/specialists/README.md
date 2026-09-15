# Specialist Agent Overlays

Every specialist follows the repository-wide rules in [AGENTS.md](../../../AGENTS.md), the joined project's engineering policy, the common coding instructions, and its exact approved work.

Project-specific overlays belong with the joined project when they contain live product rules or source paths. Maestro keeps the reusable template and examples only to show the expected role boundaries.

Each overlay defines:

- Purpose and architectural boundary.
- Required authority and source paths.
- Owned concepts and behavior that must be preserved.
- Allowed and prohibited change areas.
- Entry conditions, dependencies, safe parallel work, and shared resources.
- Verification, evidence, handoff, and escalation.
- Relationship to the common coding instructions.

Use the [Specialist Agent Overlay Template](specialist-overlay-template.md) for new roles.

The current examples cover [Content Platform](content-platform-agent.md), [Theme Studio](theme-studio-agent.md), [Screens](screens-agent.md), and [Display Runtime](display-runtime-agent.md). They are examples, not authority for a joined project.

Generated source-local role files use the format defined in [Architecture schema and process-definition binding](../../architecture.md#architecture-schema-and-process-definition-binding). The template below this folder implements that format; its overlay guidance is not a second role format. Example overlays remain illustrative, not alternative generated-file contracts.
