# Project Planning Guide

## Purpose

This guide describes the source material project architects supply for registration. The sources explain the project, how its capabilities work, and the outcomes to deliver. The workshop develops these sources for a later registration or development-breakdown process. It does not execute that process or generate implementation work packets.

## Required sources

| Source | Contents | Template |
|---|---|---|
| Project overview | Identity, purpose, overall scope, current state, and authoritative source locations. | [Project overview](../assets/templates/project-overview.md) |
| Architecture | Components, connections, data, journeys, interaction results, failure behavior, and constraints. | [Architecture](../assets/templates/architecture.md) |
| Roadmap of Product Outcomes | The ordered list of outcomes with a "You see" line, status, evidence level, order, dependencies and alternatives considered. | [Roadmap](../assets/templates/roadmap-of-product-outcomes.md) |
| Outcome documents | One per outcome: scope, architecture references, dependencies, acceptance criteria with a Result column, and definition of done. | [Outcome](../assets/templates/outcome.md) |

Sources are Markdown files in the project repository, using the templates' consistent headings and tables. File and folder names are project-specific. Template prompts are replaced with project facts; unresolved details are identified explicitly rather than presented as completed work. Additional detail can be added under the relevant headings.

The templates prepare planning sources suitable for registration assessment. They do not generate a runtime registration package or establish a successful registration.

## Entry document and source references

Registration requires the repository and the repository-relative path to the project overview. For example, a repository may use `docs/project-overview.md`. The workshop reads that entry document and follows its source references rather than scanning folders or guessing which documents are authoritative.

The overview lists the architecture and the roadmap. The roadmap links each outcome document, and each outcome identifies the specific architecture sections that explain its behavior and journeys. Dependency references use the outcome's plain subject.

Source-location fields contain repository-relative paths, optionally followed by a heading fragment, such as `docs/architecture.md#service-startup`. These location values are interpreted from the repository root. Any additional clickable Markdown links must resolve to those same files from the document containing the link.

One fact has one authoritative location. Other documents reference it rather than maintaining copies. Reviews use the same exact source revision plus document content hashes for unpublished drafts, or the same published commit when available. Freeze the reviewed snapshot so both passes assess identical bytes. Missing references or contradictory sources are flagged for clarification, not silently resolved.

## Project overview

The overview contains:

- Plain project name, repository, and responsible architect: a person, agent, or both.
- Intended purpose and overall inclusions and exclusions.
- Existing capability, incomplete or broken areas, and supporting evidence.
- The locations of the authoritative architecture and roadmap.

The overview is the entry point, not a duplicate architecture or outcome catalogue. Detailed dependency evidence can remain at its authoritative location and be referenced.

## Architecture

The architecture explains system behavior in plain, impersonal language:

| Subject | Required explanation |
|---|---|
| Structure | Components and their responsibilities. |
| Connections and data | How components communicate, where records are stored, and which records are authoritative. |
| Journeys | The path from entry to the usable outcome, including essential prerequisites and connections. |
| Interactions | Starting condition, trigger, component behavior, expected result, and essential failure behavior. |
| Constraints and unresolved details | Established technical boundaries, provisional concepts, and gaps affecting behavior. |

Every expected journey has an explained result. Every associated interface interaction also has an expected outcome; naming a command or control alone is insufficient.

| Interaction field | Required detail |
|---|---|
| Starting condition | What already exists or must be true. |
| Trigger | The command, action, or event that starts the interaction. |
| System behavior | What the relevant components do. |
| Expected result | What appears, changes, or is recorded, and any relevant state that remains unchanged. |
| Essential failure behavior | What happens when the interaction cannot complete, including the visible failure or request for input. |

A journey connects these interactions. Architecture contains behavior, not delivery assignments. The detail must support development breakdown without inventing behavior or assuming a missing service or connection.

## Roadmap of Product Outcomes

The roadmap is a short ordered list of the product's outcomes. Each entry has a plain subject, a "You see" line, a status and an evidence level, and links to its outcome document. It also records the order and dependencies with the reason for each position, the alternatives considered for scope and ordering decisions, and unresolved information. It covers the whole product, including outcomes already delivered.

Each outcome has its own document containing:

- The usable outcome, its "You see" line, and included and excluded scope.
- Required dependencies, including outside capabilities with their evidence level.
- References to architecture sections and journeys.
- Acceptance criteria with observable results, verification, pass boundaries, accepted exceptions and a Result column.
- A definition of done identifying necessary evidence and reviews.

An outcome is a usable end state, not a task list. The roadmap does not list features or milestones; the architect groups features into milestones later. Architecture references explain behavior without copying it into outcome documents. Together, the architecture and outcome documents must cover the complete usage journey and the prerequisites needed to deliver it.

An outcome is delivered when every acceptance row is marked Done, with the date, revision, evidence and a plain-worded reason, or is an accepted exception. Roadmap status is read from the outcome document. The Owner may delegate that marking to the Maestro service; record the delegation.

## Naming, ordering, and versions

An outcome is identified by its plain subject, unique within the roadmap. A retired subject is not reused. Order is the list order in the roadmap. Reordering changes the roadmap version, not the outcomes. Dependencies name the outcome subject or an outside capability.

A changed outcome document or roadmap receives its next version, and previous versions remain available. Reviews identify the exact versions reviewed; review rounds remain separate from document versions.

## Current capability and dependencies

| Evidence level | Meaning |
|---|---|
| Reported | Described as existing without verification. |
| Supported by source inspection | Relevant code and connections appear present. |
| Verified in operation | Evidence shows the connected capability working. |

Existing dependency claims identify their evidence level and source. Missing setup, credentials, services, or integration work remain explicit. Source inspection alone does not prove operation, and registration preparation does not require a full code audit.

An outcome document identifies dependencies required by its outcome, including those outside its scope. An unverified dependency is not silently treated as ready.

## Partial registration

The overview may describe the whole project while registration selects specific outcomes or a defined portion. The selected boundary identifies:

- Included outcomes and exclusions.
- Relevant architecture sections and journeys.
- Outside dependencies and their current state.
- Acceptance criteria for the selected outcome.

A narrower portion has an explicit description. An essential dependency cannot simply be excluded: evidence must show it already works, or an explicit decision must address the missing work. The interpreted boundary and dependencies are presented for confirmation.

## Verification expectations

Verification is basic, meaningful, and proportionate:

- Use real data and actual connected behavior. Fake data is used only when necessary, with the reason identified.
- Cover the main journey and essential failures, not every possible outcome or edge case.
- Spend most development effort implementing the functional area rather than writing tests.
- Define expected interaction outcomes fully without requiring a separate test for each outcome.
- Do not treat a passing fake-data test as proof of a real integration.

Acceptance criteria specify results and necessary evidence. They do not require exhaustive test suites. The same verification expectations apply during Execution.

## Missing or contradictory information

| Finding | Treatment |
|---|---|
| Blocking gap | Missing information prevents understanding of the outcome, behavior, scope, dependencies, or completion boundary. Identify the source location or missing source, explain what cannot be determined, and request a specific clarification. |
| Non-blocking improvement | Wording or additional detail would help but is not needed to proceed. Record the useful improvement without preventing registration. |

Adequate information is not repeatedly rejected over preferences. The workshop does not invent missing answers, expand scope silently, or hide source contradictions inside development assignments. The workshop applies its bounded review procedure; this guide does not add a separate review loop.

## Relationship to development breakdown

Architecture describes how the capability works. The roadmap and outcome documents define the usable delivery outcomes and evidence. Development milestones, which the architect creates later, make manageable contributions linked to both.

If a breakdown requires an undefined behavior, assumed prerequisite, or unspecified completion boundary, the responsible source needs clarification before that affected breakdown proceeds. Completed task lists or disconnected components do not substitute for the promised usable outcome.

