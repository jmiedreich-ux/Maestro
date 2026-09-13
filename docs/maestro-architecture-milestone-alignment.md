# Architecture and Milestone Alignment

## Purpose

Architecture and project milestone declarations together provide sufficient information to create development milestones that deliver the expected usable outcome.

## Responsibilities

| Document or record | Responsibility |
|---|---|
| Architecture | Explain how the capability works: components, responsibilities, interactions, data, normal behavior, and failure handling. |
| Project milestone declaration | Define the usable outcome, delivery scope, dependencies, acceptance criteria, and evidence required for completion. |
| Development milestone | Define a manageable contribution to that outcome, linked to its project milestone and relevant architecture sections. |

Architecture describes system behavior without delivery assignments. Project milestones reference the architecture rather than repeating it. Development milestones organize the work without inventing behavior or changing the promised outcome.

## Connection between documents

Each project milestone references the architecture sections that explain its required behavior. Together, the sources cover the complete usage journey, essential prerequisites, and connections needed to make the capability usable.

Development milestones retain explicit links to the project outcome and supporting architecture. Their acceptance criteria support the project-level criteria and definition of done rather than weakening them.

## Sufficient information for breakdown

Clarification is required before the affected development breakdown proceeds if it would otherwise require:

- Inventing behavior that the architecture does not define.
- Assuming a required service, dependency, or connection exists without supporting information.
- Choosing an undefined scope or completion boundary.
- Resolving a contradiction between the architecture and declared outcome.

Clarifications belong in the document responsible for that information. The breakdown must not hide missing source decisions inside implementation assignments.

## Completion

Completion requires evidence that the promised outcome works across its required connections. A completed task list or a collection of finished components does not replace the defined usable outcome.
