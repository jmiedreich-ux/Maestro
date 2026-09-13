# Maestro Repository Handoff

## Start here

- [Repository working rules](../../AGENTS.md)
- [Additional agent instructions](../../CLAUDE.md)
- [Maestro architecture](../../docs/maestro-architecture.md) — current design and evolving concepts.
- [Registration project milestones](../../docs/maestro-registration-project-milestones.md) — draft project source; needs the alignment described below.
- [Agent role library](../../docs/agents/) — reference for the upcoming role discussion.
- [Maestro information review](../../docs/maestro-information-review.md) — consolidated reference material, separate from the new architecture.
- [Repository overview](../../README.md)

## Where we stopped

The architecture now describes the foundational Maestro CLI and its communication with the runtime service. Next session continues design.

The registration project milestone document still includes the command center in initial scope and needs a separate CLI foundation before registration development. It is project-architect source material for registration review, not an approved registration package. Documentation does not prove these capabilities are implemented.

## Next session: agreed order

1. Continue the CLI design and finalize its foundational feature milestone.
2. Finalize the registration project milestones, reflecting the CLI foundation and initial CLI-only scope.
3. Finalize the Project Architect and Fidelity Reviewer agent roles.
4. Begin discussing and planning the Model Execution Adapters.

## CLI decisions to preserve

- The dedicated Maestro CLI is foundational and comes before registration development.
- The command center is outside the initial version.
- The terminal experience combines a persistent typed-command area with conversation, progress, findings, and interactive choices. It should feel similar to Codex, with more interaction.
- Typed commands and interactive controls invoke the same operations. Replies must be associated with the relevant project and question.
- Maestro must support multiple projects from the foundation. Selecting another project does not stop work on the previous one. Conversations, pending decisions, versions, and process state remain separate.
- The Python runtime service owns ongoing work. Closing the CLI disconnects the interface; stopping work is a separate action. Reopening retrieves current state and reconnects to updates.
- The CLI communicates with the local service over HTTP. Server-Sent Events carry ongoing service updates to the CLI.
- Exact commands, API endpoints, event formats, and connection configuration remain to be designed.

## Registration boundaries to preserve

Use the architecture for the complete registration design. These distinctions are especially important when revising milestones:

- Project milestones describe plainly worded outcomes. Development milestones and work packets are created in the process after registration.
- Registration includes a Maestro architect assessment and an independent fidelity review. Material blockers need evidence; minor improvements must not prevent registration.
- The configurable review limit defaults to two rounds. Unresolved material findings go to the Owner.
- Agent delegation uses a script for deterministic checks, including verifying actual GitHub commits.
- Owner responses feed back into the process. Final confirmation is distinct from answering a question.
- Registration may be rerun only when no project work is in progress. New versions preserve approved history.
- Registration output uses structured JSON with a schema and index in the project's GitHub repository.
- Review must check whether the planned scope can deliver the promised usable capability. Completion criteria must require the real connected operation described by the milestone.
- Existing code, reported capability, and operational proof must remain distinguishable.

## Outstanding document alignment

Revise the registration project milestone source after the CLI discussion. Add the foundational CLI milestone before registration development and remove initial command-center delivery requirements. Use declaration-qualified references: CLI — Command-line interface and REG — Project registration. Each declaration has its own milestone-number sequence and a separate ordered list. Preserve these qualified identities when inserting or reordering; use explicit cross-declaration dependencies. The declaration sheets use this naming model.

Keep the source document distinct from the registration package that Maestro would produce after reviewing it. Do not silently turn evolving concepts into settled requirements.

## Working rules and authority

Commit approved changes directly to `master`. Do not create branches or pull requests unless the Owner changes that instruction.

Use plain, concise language. Always accompany a coded identifier with its plainly worded subject.

Use current code and Git history for implementation facts, and the operational database for live coordination state. Documentation is authoritative only for the boundary it explicitly defines. Start new design work from the architecture document; do not treat the consolidated information review as the new architectural plan.
