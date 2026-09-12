# Project Registration Principles

Registration connects Maestro to a project without transferring ownership of the project's architecture, plans, code, or delivery rules.

## Discovery

Registration begins with read-only discovery of an exact repository revision. Existing repository files and Git state must not be changed during discovery.

Maestro records confirmed, missing, and conflicting facts. Missing information is never guessed or replaced with convenient defaults.

## Required facts

A registration must identify:

- The project and repository.
- The exact source revision.
- The project's authoritative architecture, planning, rules, and handoff paths.
- Build, test, integration, and user-interface verification commands.
- Branch, review, merge, deployment, rollback, and owner-acceptance rules.
- Agent roles, execution restrictions, resource limits, notifications, and declared exceptions.
- Environment and secret reference names.

Documentation may contain secret reference names, but never credentials or secret values.

## Authority

The project repository remains the source of truth for its architecture, plans, rules, code, reviews, and delivery evidence. Maestro stores only the binding and operational state needed to coordinate work.

Accepted facts must remain separate from proposals, open questions, and historical information.

## Approval boundary

Registration is blocked when required facts are missing, conflicting, unsafe, or not tied to an exact source revision.

The Owner must approve the proposed registration before it becomes active. Registration confirms that Maestro can safely understand and coordinate the project. It does not approve implementation work.

Historical experiments and proving runs may provide evidence, but they do not define the current registration workflow.
