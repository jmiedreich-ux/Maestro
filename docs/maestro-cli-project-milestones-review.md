# Maestro CLI — Milestone Detail Review

## Result and scope

**The proposed milestones are suitable for review. All implementation details are not yet defined.**

Three independent reviews assessed the [CLI project milestone source](maestro-cli-project-milestones.md): architecture fidelity, missing details, and usable completion boundaries. The design baseline is [Maestro Architecture](https://github.com/jmiedreich-ux/Maestro/blob/bf12a1b95f696c8190b5756189bf025cd1aff26d/docs/maestro-architecture.md), content blob `a5dea960a97370099efc5a338813775944163558`.

The reviews found no remaining material fidelity or outcome-coverage omission after the clarifications below. The outcomes remain proposals; neither implementation readiness, successful registration, nor completed software is established.

| Review | Result |
|---|---|
| Architecture fidelity | Passed after acceptance wording made simultaneous submissions/updates and initial-registration protections explicit. |
| Detail completeness | Suitable outcome definitions; prerequisite mechanisms and integration contracts remain unresolved. |
| Usable completion boundary | Passed after reading-state and input-context preservation were made explicit. Actual service/SQL evidence is required; sample screens cannot establish completion. |

No source-code execution or operating-environment inspection was performed. Existing implementation readiness remains unknown.

## Coverage

| Architectural behavior | Milestone coverage |
|---|---|
| Installed CLI, separate service startup, local API, systemd lifecycle | PM4 — Connected multi-project CLI workspace: setup, connection, and real service evidence. |
| SQL records, HTTP reads, streamed events, no history mutation from reads | PM4 — Connected multi-project CLI workspace: durable information and live updates. |
| No startup selection, multiple projects, overview order, selected versus working | PM4 — Connected multi-project CLI workspace: project separation and visible context. |
| Recent/earlier history, inline findings, reading position, visible activity/questions | PM4 — Connected multi-project CLI workspace: reading and findings acceptance. |
| Cross-project attention without forced focus | PM4 — Connected multi-project CLI workspace: notice contents and explicit navigation. |
| Disconnected display, local commands, retry, empty result versus failure | PM4 — Connected multi-project CLI workspace: connection and lookup cases. |
| Keyboard, minimum size, multiline input, paste | Workspace controls in PM4 — Connected multi-project CLI workspace; answer controls in PM5 — Reliable project questions and answers. |
| Question-only text, recommendations, alternatives, choice then explicit send | PM5 — Reliable project questions and answers: question and input cases. |
| Saving before acknowledgment, linked routing, receipt versus resolution | PM5 — Reliable project questions and answers: submission and follow-up evidence. |
| Lost acknowledgments, explicit retry, no duplicate effect, stale questions | PM5 — Reliable project questions and answers: failure and validity cases. |
| Concurrent updates and submissions | PM5 — Reliable project questions and answers: targets and input remain stable while streamed updates arrive. |
| Clearing drafts on switch; warning on exit | PM5 — Reliable project questions and answers: switch, exit, and reopen cases. |
| All eight agreed commands | Six workspace commands in PM4 — Connected multi-project CLI workspace; registration commands connect with actual registration. Unimplemented commands remain excluded from help. |
| Scope interpretation, actual reviews, confirmation, cancellation, comparisons, recovery | Explicit registration integration coverage, using real source and package workflows. These are not claimed complete by the CLI foundation. |

Command center, unsolicited agent conversations, retained cross-project drafts, removed shortcuts, and execution commands remain excluded. Mobile remains undecided. The source does not introduce development milestones, work packets, an agent provider, or a database implementation.

## Details still required

These gaps are visible design prerequisites, not reasons to add unrelated product features.

| Category | Missing detail | Consequence |
|---|---|---|
| Foundation prerequisite | A documented mechanism to create project, process, event, and question records before registration exists. | A CLI demonstration otherwise depends on unavailable registration or undisclosed manual preparation. It must use actual service/SQL behavior. |
| Context behavior | An unambiguous current-process rule for historical or concurrent activity, question selection, and registration intake before project selection. | Findings or responses could target the wrong process even with a known project. The rule must be specified before that behavior is built. |
| Shared implementation contract | HTTP payloads, event records, SQL relationships, status values, and save acknowledgments. | The CLI and service cannot be implemented independently against assumed formats. These can be designed without changing the outcome scope. |
| Recovery contract | Missed-update retrieval and identity for a repeated submission versus a new or edited answer. | A reconnect could miss information or a retry could duplicate an effect. The mechanism is required before response recovery implementation. |
| Deployment detail | Runtime dependencies, installation/configuration paths, service access, and reproducible operational setup. | Existing files do not prove a usable launch path. The service manager and local connection model are already specified; those decisions need not be reopened. |
| Practical implementation choice | Terminal toolkit, remaining command syntax, history loading, input height, and minimum size. | Choices must be recorded and verified before completion; exact dimensions need not be invented during milestone authoring. |
| Registration dependency | Guide/package formats, agent-role and adapter contracts, actual work-state restrictions, and SQL/GitHub consistency. | These prevent claiming complete registration integration, but do not invalidate a bounded CLI workspace or generic response component. |

The most useful next design work is the pre-registration record source and project/process/question selection. Those establish what the CLI is connected to and how input reaches the intended process. Service and storage contracts can then be specified against that behavior.

## Corrections made during review

- Initial registration and re-registration both return an existing process for duplicate requests and reject confirmation of changed or ineligible candidates.
- Submission remains possible while streamed updates arrive, without changing its target or disrupting input.
- Earlier-history reading retains access to current activity, waiting state, and pending questions.
- Expanding findings preserves the selected project and the question linked to input.

Each reviewing agent rechecked the relevant correction. These clarifications preserve existing architecture; no new workflow authority was added.

## Dependency and completion assessment

PM4 — Connected multi-project CLI workspace and PM5 — Reliable project questions and answers have separate useful component boundaries and both precede registration development. Their provisioning prerequisite prevents a circular dependency on registration.

Controlled service-generated events and questions can demonstrate those components only when the actual service, SQL, and CLI are exercised. They cannot prove agent reasoning, registration assessment, GitHub publication, or activation.

The existing [registration project milestone source](maestro-registration-project-milestones.md) still has both-interface wording and needs alignment with CLI-only scope and the preceding CLI foundation. Its stable identifiers remain unchanged. The new CLI source records the required integration coverage without pretending that the older source has already been finalized.

All milestone acceptance rows still require operational evidence. The project source format remains provisional until the Maestro Planning Guide is specified. The review therefore establishes a faithful, reviewable draft with identified gaps—not a fully specified implementation package or a registration pass.
