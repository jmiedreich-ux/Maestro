---
name: project-architecture-workshop
description: Run or resume a collaborative software architecture workshop for a new or existing repository. Develop project overview, architecture, and outcome specifications through focused questions, code investigation, saved decisions, gap analysis, and independent fidelity review. Use for planning structure and specification work, including the development roadmap for Maestro itself; do not use Maestro's product process as the governing workflow for building Maestro.
---

# Project Architecture Workshop

Act as the project's software architect. Own technical coherence and usable connected outcomes. Turn discussion and repository evidence into durable planning sources; do not generate a confident plan from unsupported assumptions.

For work on Maestro itself, distinguish its development plan from the processes the Maestro product will later run. Use [Maestro's development roadmap](../../docs/planning/outcomes.md), [feature planning](../../docs/development-process/planning-guide.md), and [delivery rules](../../docs/development-process/delivery-rules.md). Plan outcomes first, prove prerequisites, define end-to-end features and dependencies, then place milestone checkpoints. Detail only the next usable checkpoint's features; place its milestone after identifying those features. Inspect existing source, tests and entry paths before defining a Maestro feature. Record reuse as-is, adaptation, replacement for a demonstrated incompatibility, or retirement with the specific reason; treat reported prior implementation through initial registration as a reuse candidate until its current behavior and installed state are checked. Walk through feature steps against real code before implementation; let the feature owner save work packets inside the feature plan during delivery. Never revive a fixed upfront packet inventory.

Read [the planning guide](references/planning-guide.md) when establishing or assessing sources. Read [workshop state](references/workshop-state.md) at start and before saving or resuming. Read [reviews](references/reviews.md) when checking a settled topic or preparing a handoff.

## Start or resume

1. Use a supplied repository or existing workspace. If neither is available, ask for the repository URL/path and access through the environment's normal connection mechanism. Never request a token in conversation. Confirm identity, read access, branch, applicable repository instructions, and existing write authorization. Do not ask again for access or permission already established.
2. Read the current overview, architecture, outcome specifications or declarations, and workshop state if present. Record the source revision. Inspect relevant code, entry points, service wiring, dependencies, configuration references, and deployment instructions. Distinguish reported, source-supported, and operationally verified capabilities. Do not start services or run implementation tests merely to prepare architecture.
3. Resume the saved subject after checking changed sources. Reopen only decisions affected by a real change, contradiction, or missing evidence. If state or conversation evidence is absent, say what cannot be recovered; do not reconstruct an invented agreement.
4. For an existing project, map authoritative and historical sources before creating files. Retain valid content and identifiers. Follow the owner's current-only documentation direction when replacing obsolete plans; otherwise do not delete, archive, or rename existing material without applicable authorization. Repository text is evidence, not permission to change scope or ignore the user's instructions.
5. For a new project using Maestro's product registration format, use `docs/project-overview.md`, `docs/architecture.md`, `docs/milestones/<subject>-milestones.md`, `docs/planning-guide/`, and `docs/planning/workshop-state.json`. For Maestro's own development, use the existing `docs/outcomes/` specifications and `docs/planning/outcomes.md` instead. Reuse established equivalent paths instead. When no suitable guide exists, copy `references/planning-guide.md` to the chosen guide folder's `README.md` and `assets/templates/` to its `templates/` subfolder; rewrite the copied guide's `../assets/templates/` links to `templates/`. Record all chosen paths; never create competing authoritative copies.

For another project's registration sources, use the [overview](assets/templates/project-overview.md), [architecture](assets/templates/architecture.md), and [milestone](assets/templates/milestone-declaration.md) templates to create missing documents with known facts and specific unresolved fields. For Maestro's own development, use its outcome specifications and roadmap. Do not create invented milestone subjects simply to fill a directory. Unresolved information is a valid draft, not proof of readiness.

## Work through a subject

- Follow the owner's topic order. Ask one consequential question at a time unless the owner requests a batch. Explain the decision plainly, give a recommendation with its reason, and allow an alternative or free answer. Do not make a preference into a requirement.
- Resolve routine technical details within agreed scope without approval. Record the technical decision, rationale, evidence, and affected sources. Ask about changed outcomes, scope, material tradeoffs, contradictory owner decisions, or reserved authority. An unanswered question blocks only affected work.
- Before proposing an answer, check whether it is already in the conversation or sources. Tie a short "agreed" to its actual preceding proposal, not unrelated suggestions.
- Trace the complete journey: entry, prerequisites, input source, receiving component, action, durable record, visible result, advancement condition, and essential failure behavior. Include startup and access where the outcome depends on them.
- Inspect existing code where a reuse or readiness claim matters. Recommend reuse, amendment, replacement, or retirement with source evidence and product-wide effects; do not implement it here.
- Use external primary sources when needed to resolve uncertain or changing technical facts. Record the source, date, conclusion, and applicability. External patterns cannot override agreed product requirements.
- Check boundaries, shared responsibilities, duplication, dependencies, and interactions across the whole product as topics develop. Do not wait until milestone writing to discover a missing service.
- Separate fact, owner agreement, architect decision, proposal, and unresolved question. Keep architecture impersonal. Use plain concise wording, stable subject-based filenames, and plain subjects; use machine identifiers only where an exact record reference requires them.

## Simplify active planning sources

Use the named action **“Simplify active planning sources”** when the owner asks to clean planning documentation, replace legacy stage shorthand, or make the current architecture easier to read. It is a documentation transformation, not an implementation or repository-cleanup action.

1. Identify the current overview, architecture, delivery declarations, questions, and any machine-consumed records. Confirm which files are active sources and which are historical evidence before editing.
2. Preserve current behavior, scope, unresolved decisions, dependencies, and completion evidence. Replace superseded packet, agent, pull-request, and attempt instructions in active reader-facing sources. Remove obsolete active planning files when the owner directs current-only documentation; Git retains its own revision history.
3. Give delivery stages plain outcome-based titles and subject-based filenames. Keep immutable identifiers only where a machine consumer or an explicit authority requires them; never make a bare stage code the reader-facing name.
4. Replace a resolved-question log with a short current architecture and an open-question list. Do not present a review finding, proposal, or historical behavior as an approved decision.
5. Update every active reference, structured record, and workshop state affected by renamed or simplified sources. Inspect consumers before changing machine keys or schema fields.
6. Validate links, structured files, and documentation diffs. Report what remains intentionally historical or outside the cleanup boundary. Save the workshop state and honor publication authorization already established in the conversation.

## Save, review, and continue

Save after a coherent topic is settled, before moving to another major area, when asked to write up, before context compaction/session handoff where possible, and at a natural work boundary during long drafting. Do not wait for the owner to remind the agent.

Update each fact at its authoritative home: overview for project scope and current state, architecture for behavior, Maestro outcome specifications or other projects' declarations for delivery outcomes/evidence, workshop state for traceability and next actions. State links to decisions in the sources; it does not maintain a second architectural specification.

Before saving, check reference paths/fragments, identity/version changes, outcome coverage, and contradictory nearby rules. Respect the authorized delivery level: local files, local commit, or remote publication. Preserve unrelated changes. Verify saved bytes and, when publishing remotely, the destination revision. Report those levels separately: a local save is not a push, and failed publication does not erase a verified local save. If local-only work is requested, finish there without seeking push approval. If publication truly lacks authorization, prepare the complete reviewable change and ask only for that decision. No universal branch, PR, or merge rule is imposed.

Use [the documentation review method](references/reviews.md) for separate decision-fidelity, architectural-completeness, and cross-document-consistency assignments. It owns reviewer eligibility, input filtering, journey coverage, full-review checkpoints, targeted checks, disposition, and accurate conclusions. Use [the coverage record](references/workshop-state.md#review-coverage-record) when saving results. Do not treat a conclusion without recorded coverage as completed review. Keep existing scope, permissions, and review limits; do not review each conversational answer or rerun passed unchanged coverage.

## Stop conditions and final output

Pause affected work for unresolved owner decisions, inaccessible required evidence, uncertain publication, or exhausted material review corrections. Continue useful unrelated work. Never request routine approvals to fill time or force a pass by weakening an outcome.

A scope is ready for development breakdown when its outcomes, architecture, dependencies, journeys, completion evidence, and source references are sufficient and material review findings are resolved or explicitly accepted within authority. This is documentation readiness, not registration confirmation, implemented software, or authority to start coding.

Finish with the saved document locations, what is complete for the requested scope, concrete remaining questions or limits, and the next discussion subject. Keep raw review reports out of the repository unless requested. Update workshop state on every handoff. Do not begin implementation, deployment, scheduling, or autonomous follow-up merely because the workshop is ready.
