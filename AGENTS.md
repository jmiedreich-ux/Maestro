# Repository Working Rules

These rules apply to every agent working in this repository.

## Plain language

Never reference a milestone, decision, work packet, review, or other coded item by its identifier alone. Always include its plainly worded subject with the identifier.

Write all repository documentation and agent responses in plain language. Keep them concise, direct, and limited to information that helps the reader act.

## Git changes

Commit every approved repository change directly to `master`. Do not create branches or pull requests unless the Owner explicitly changes this rule.

## Architecture documentation

Architecture documentation explains system structure, responsibilities, data, interfaces, runtime behavior, and failure handling. Use plain, impersonal prose. Give each rule one authoritative explanation and avoid repetition.

Keep Maestro delivery plans, milestone drafts, work assignments, and handoffs separate from architecture. Planning and milestone records may be described as system functions or data, not as Maestro delivery work. Mark unresolved mechanisms without inventing decisions.

## Milestone declarations

Follow the [Maestro Planning Guide](docs/planning-guide/README.md). Apply the conventions without repeating their explanations or migration history in declaration sheets. Keep references to other declarations limited to actual dependencies and delivery responsibility.

## Documentation review results

Apply corrections directly to authoritative documents. Do not present detailed results or create standalone review reports unless requested. Retain required coverage in existing workshop state, handoff, or runtime records under the [documentation review method](skills/project-architecture-workshop/references/reviews.md#coverage-and-findings). Incomplete coverage is not a completed review and consumes no round. This does not remove runtime review records.

## Cross-document alignment

Architecture owns software behavior; milestone declarations own delivery outcomes and completion evidence; the Planning Guide owns required project inputs; role files own authority; handoffs own discussion status. Keep each fact authoritative in one place and link elsewhere.

Use the [documentation review method](skills/project-architecture-workshop/references/reviews.md) for independent inputs, three separate passes, complete journey tracing, coverage, conclusions, and bounded corrections. Existing permissions, role authority, runtime contracts, and review limits remain unchanged.

For Maestro, selected-scope coverage includes opening and using the workspace, answering a question, initial registration, registration update, interrupted-registration recovery, and each architecture-loop stage: entry/session continuation, code investigation, project structure and specialist guidance, breakdown/clarification, review/amendment, publication/confirmation, cancellation/recovery, and reconciliation after re-registration. Record exclusions explicitly.

Apply full reviews at the method's major design checkpoints. Targeted correction checks do not substitute for full coverage. Do not introduce preferred features, stronger acceptance requirements, or general Execution policy through documentation review. Live verification belongs to implementation.
