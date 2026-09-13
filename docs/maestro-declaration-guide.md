# Maestro Declaration Guide

## Purpose

This guide defines Maestro's declaration naming, ordering, and version conventions. Declaration sheets apply these conventions without repeating their explanation or naming-change history.

Architecture documents describe system behavior. Declaration sheets contain project outcomes, delivery positions, dependencies, scope, acceptance criteria, and completion evidence. Handoffs remain separate. Documentation review results are reported in the conversation rather than retained as standalone repository reports.

## References and ordering

Registration associates project milestones with a named declaration. Each declaration has a stable designation unique within its project. A project can have several declarations, regardless of the order in which their contents were authored.

A project-milestone reference combines the declaration designation, the milestone type and number, and a plain subject. Numbers are assigned sequentially within that declaration, not across the project. The number identifies the milestone; it does not determine its delivery position.

| Record | Format example |
|---|---|
| Declaration | APP — Application |
| Project milestone | APP-PM1 — Application startup · version 2 |
| Development milestone | DM1 — Project registration · version 3 |
| Planning document | PD1 — API contract · version 2 |
| Work packet | WP1 — Implement registration input checks · version 1 |
| Review | RV1 — Registration findings fidelity review · round 1 |
| Replan | RP1 — Revise registration delivery sequence |

These examples describe record formats, not Maestro delivery assignments. Subjects accompany coded references wherever displayed or referenced.

Each declaration stores an ordered list of its milestone references. Inserting a milestone assigns its next unused identifier and places that reference at the required position. Reordering changes the list, not milestone identities. Dependencies between qualified references determine prerequisites across declarations; declaration creation order imposes no delivery order.

An identifier remains stable when an item moves in delivery order or its title or content changes. Retired identifiers are not reused. Non-milestone record types retain their sequential per-type, per-project numbering. Random assignment and unexplained assignment gaps are prohibited.

One naming-convention list supports Owner-authorized additions of declaration designations, record types, and prefixes. Versions are separate from identities and ordering: changed records receive their next version, and previous versions remain available. An ordering change updates the declaration version, not unchanged milestone versions. Reviews identify the exact item and declaration versions reviewed; review rounds remain separate from document versions.

Relationships are explicit references rather than encoded hierarchies. Each work packet has its own identity and a link to its development milestone. Moving it does not require a new identifier. Replans record reasons and affected records.

## Declaration content

A declaration identifies its designation, capability, source architecture, and status. Its ordered milestone table identifies position, qualified reference, plain subject, outcome, and dependencies.

Each milestone states its purpose, scope, usage journey, acceptance criteria, required evidence, and definition of done. Unresolved details and external dependencies remain explicit.

Version values belong in metadata. Explanations of past renumbering, convention migrations, and comparisons of naming between declarations do not belong in the milestone content. Other declarations are referenced only where needed to express actual dependencies or delivery responsibility.

This guide covers declaration conventions; it does not define the complete Maestro Planning Guide source format or registration JSON schema.
