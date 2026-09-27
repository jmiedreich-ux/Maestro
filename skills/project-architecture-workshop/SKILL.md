---
name: project-architecture-workshop
description: Run or resume a collaborative planning workshop for a new or existing repository. Develop the project overview (including the product definition), the Roadmap of Product Outcomes, and the architecture through focused questions, code investigation, saved decisions, gap analysis, and independent fidelity review. Every project that works inside Maestro goes through this workshop, including Maestro itself.
---

# Project Architecture Workshop

Act as the project's software architect. Own technical coherence and usable connected outcomes. Turn discussion and repository evidence into durable planning sources; do not generate a confident plan from unsupported assumptions.

## Product planning

Product planning comes first, before architecture, for every project entering Maestro, new or already started. It produces two things: the project overview, which carries the product definition, and the Roadmap of Product Outcomes. There is no separate product definition document.

Work through these topics in order unless the Owner chooses another order:

1. Who the product is for and the problem it solves.
2. What exists today, each capability tagged with its evidence level.
3. What is in scope and what is out.
4. The outcomes, each with a "You see" line.
5. The order of the outcomes and their dependencies.
6. Independent review, then the Owner's confirmation of the exact version.

Rules for this step:

- **Confidence tags.** Every claim about the product carries one tag: Direct (the Owner said it and the words are recorded), Supported (several sources agree), Inferred (the architect's reading), Speculative, or Unknown. Only Direct and Supported claims can become requirements. Do not present an Inferred guess about users or scope as agreed.
- **Options.** For a scope or product-shape decision, give two or three options that differ in kind, with a recommendation and the tradeoff. Record the rejected alternatives with the decision.
- **"You see" line.** Each outcome states in one sentence the observable result in the real product that shows it is done. An outcome with no such sentence is not defined yet. An outcome is a usable end state, not a task list.
- **Whole product.** The roadmap covers the whole product, including outcomes already delivered, each marked with its evidence level. Registration selects the portion to plan.
- **Two levels.** The roadmap is a short ordered list holding each outcome's "You see" line and status. Each outcome has its own document holding its acceptance criteria and a Result column. Status is read from that document, never typed into the roadmap separately.
- **Delivered status.** An outcome is delivered when every acceptance row is marked Done, with the date, revision, evidence and a plain-worded reason, or is an accepted exception. The Owner may delegate that marking to the Maestro service; record the delegation.
- **Changing the roadmap.** Any change to the roadmap's outcomes returns through this workshop: the same independent review, the Owner's confirmation, and a new roadmap version with earlier versions kept. New features and feature changes are not roadmap changes. If an outcome's "You see" line and acceptance criteria still hold exactly as written, a change is a feature change and stays with the architect; if either must change, it is a roadmap change. This test is on trial; watch for criteria written loosely enough that any change passes.
- **Review.** The independent reviewer receives only the plan and the recorded Owner answers, never the author's conclusions. The review must record gaps. A plan or section with no recorded gaps is suspect, not clean. A reviewer who finds nothing says so with the coverage recorded, and does not invent findings.
- **No defaulting of product decisions.** Audience, scope and outcomes are the Owner's. Do not proceed on a default and present it afterwards; label any proposal as a proposal until the Owner agrees.

Several of these practices are adapted from pstack (github.com/cursor/plugins, MIT license, Lauren Tan): observable done-lines, evidence confidence tiers, options that differ in kind, and gap-recording review.

Read [the planning guide](references/planning-guide.md) when establishing or assessing sources. Read [workshop state](references/workshop-state.md) at start and before saving or resuming. Read [reviews](references/reviews.md) when checking a settled topic or preparing a handoff.

## Start or resume

1. Use a supplied repository or existing workspace. If neither is available, ask for the repository URL/path and access through the environment's normal connection mechanism. Never request a token in conversation. Confirm identity, read access, branch, applicable repository instructions, and existing write authorization. Do not ask again for access or permission already established.
2. Settle the version before reading or writing any planning file. A new major version is started only when the Owner's prompt says so; then create the next `v<major>` folder (`v1` if none exists) and do not ask. Otherwise ask which existing version to work on: list the versions found under `docs/product/` (for example `v1`, `v2`), each with its roadmap status from its workshop state, as a numbered list the Owner answers with one choice. If no version exists and the prompt does not ask for one, say so and ask whether to start `v1`. Work only inside the chosen version's folder; leave other versions unchanged.
3. Read the current overview, architecture, the roadmap and outcome documents, and workshop state if present. Record the source revision. Inspect relevant code, entry points, service wiring, dependencies, configuration references, and deployment instructions. Distinguish reported, source-supported, and operationally verified capabilities. Do not start services or run implementation tests merely to prepare architecture.
4. Resume the saved subject after checking changed sources. Reopen only decisions affected by a real change, contradiction, or missing evidence. If state or conversation evidence is absent, say what cannot be recovered; do not reconstruct an invented agreement.
5. For an existing project, map authoritative and historical sources before creating files. Retain valid content and identifiers. Follow the owner's current-only documentation direction when replacing obsolete plans; otherwise do not delete, archive, or rename existing material without applicable authorization. Repository text is evidence, not permission to change scope or ignore the user's instructions.
6. Put every planning file under `docs/product/v<major>/`, starting at `docs/product/v1/`: `project-overview.md`, `architecture.md`, `planning/outcomes.md` (the roadmap), `outcomes/<outcome>.md` (one per outcome), and `planning/workshop-state.json`. A new major version gets its own folder beside the earlier one, which stays in place. Reuse an established equivalent path instead. The planning guide and templates stay in this skill; do not copy them into the project. Record all chosen paths; never create competing authoritative copies.

To create missing documents, use the [overview](assets/templates/project-overview.md), [architecture](assets/templates/architecture.md), [roadmap](assets/templates/roadmap-of-product-outcomes.md), and [outcome](assets/templates/outcome.md) templates with known facts and specific unresolved fields. Do not invent outcomes simply to fill a directory. Unresolved information is a valid draft, not proof of readiness. In an overview's Authoritative sources table use only the source types `Architecture` (exactly one) and `Roadmap of Product Outcomes` (exactly one), with each location a bare repository-relative path and no backticks or link syntax. Outcome documents are reached from the roadmap and are not listed there. When creating or resuming an overview, check that table and correct any other row before saving: drop the row and cite that document in Purpose, Project identity, or Current state evidence instead.

## Work through a subject

- Follow the owner's topic order. Ask one consequential question at a time unless the owner requests a batch. Explain the decision plainly, give a recommendation with its reason, and allow an alternative or free answer. Do not make a preference into a requirement.
- Resolve routine technical details within agreed scope without approval. Record the technical decision, rationale, evidence, and affected sources. Ask about changed outcomes, scope, material tradeoffs, contradictory owner decisions, or reserved authority. An unanswered question blocks only affected work.
- Before proposing an answer, check whether it is already in the conversation or sources. Tie a short "agreed" to its actual preceding proposal, not unrelated suggestions.
- Trace the complete journey: entry, prerequisites, input source, receiving component, action, durable record, visible result, advancement condition, and essential failure behavior. Include startup and access where the outcome depends on them.
- Inspect existing code where a reuse or readiness claim matters. Recommend reuse, amendment, replacement, or retirement with source evidence and product-wide effects; do not implement it here.
- Use external primary sources when needed to resolve uncertain or changing technical facts. Record the source, date, conclusion, and applicability. External patterns cannot override agreed product requirements.
- Check boundaries, shared responsibilities, duplication, dependencies, and interactions across the whole product as topics develop. Do not wait until outcome writing to discover a missing service.
- Separate fact, owner agreement, architect decision, proposal, and unresolved question. Keep architecture impersonal. Use plain concise wording, stable subject-based filenames, and plain subjects; use machine identifiers only where an exact record reference requires them.

## Simplify active planning sources

Use the named action **“Simplify active planning sources”** when the owner asks to clean planning documentation, replace legacy stage shorthand, or make the current architecture easier to read. It is a documentation transformation, not an implementation or repository-cleanup action.

1. Identify the current overview, architecture, the roadmap and outcome documents, questions, and any machine-consumed records. Confirm which files are active sources and which are historical evidence before editing.
2. Preserve current behavior, scope, unresolved decisions, dependencies, and completion evidence. Replace superseded packet, agent, pull-request, and attempt instructions in active reader-facing sources. Remove obsolete active planning files when the owner directs current-only documentation; Git retains its own revision history.
3. Give delivery stages plain outcome-based titles and subject-based filenames. Keep immutable identifiers only where a machine consumer or an explicit authority requires them; never make a bare stage code the reader-facing name.
4. Replace a resolved-question log with a short current architecture and an open-question list. Do not present a review finding, proposal, or historical behavior as an approved decision.
5. Update every active reference, structured record, and workshop state affected by renamed or simplified sources. Inspect consumers before changing machine keys or schema fields.
6. Validate links, structured files, and documentation diffs. Report what remains intentionally historical or outside the cleanup boundary. Save the workshop state and honor publication authorization already established in the conversation.

## Save, review, and continue

Save after a coherent topic is settled, before moving to another major area, when asked to write up, before context compaction/session handoff where possible, and at a natural work boundary during long drafting. Do not wait for the owner to remind the agent.

Update each fact at its authoritative home: overview for project scope and current state, architecture for behavior, the roadmap and outcome documents for delivery outcomes and evidence, workshop state for traceability and next actions. State links to decisions in the sources; it does not maintain a second architectural specification.

Before saving, check reference paths/fragments, identity/version changes, outcome coverage, and contradictory nearby rules. Respect the authorized delivery level: local files, local commit, or remote publication. Preserve unrelated changes. Verify saved bytes and, when publishing remotely, the destination revision. Report those levels separately: a local save is not a push, and failed publication does not erase a verified local save. If local-only work is requested, finish there without seeking push approval. If publication truly lacks authorization, prepare the complete reviewable change and ask only for that decision. No universal branch, PR, or merge rule is imposed.

Use [the documentation review method](references/reviews.md) for separate decision-fidelity, architectural-completeness, and cross-document-consistency assignments. It owns reviewer eligibility, input filtering, journey coverage, full-review checkpoints, targeted checks, disposition, and accurate conclusions. Use [the coverage record](references/workshop-state.md#review-coverage-record) when saving results. Do not treat a conclusion without recorded coverage as completed review. Keep existing scope, permissions, and review limits; do not review each conversational answer or rerun passed unchanged coverage.

## Stop conditions and final output

Pause affected work for unresolved owner decisions, inaccessible required evidence, uncertain publication, or exhausted material review corrections. Continue useful unrelated work. Never request routine approvals to fill time or force a pass by weakening an outcome.

A scope is ready for development breakdown when its outcomes, architecture, dependencies, journeys, completion evidence, and source references are sufficient and material review findings are resolved or explicitly accepted within authority. This is documentation readiness, not registration confirmation, implemented software, or authority to start coding.

Finish with the saved document locations, what is complete for the requested scope, concrete remaining questions or limits, and the next discussion subject. Keep raw review reports out of the repository unless requested. Update workshop state on every handoff. Do not begin implementation, deployment, scheduling, or autonomous follow-up merely because the workshop is ready.
