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

Apply documentation review corrections directly to the authoritative documents. Do not present review results or create standalone review reports unless explicitly requested. Raise only unresolved issues that require an Owner decision. This rule does not remove review records required by Maestro's runtime or registration design.

## Cross-document alignment

Architecture owns software behavior; milestone declarations own delivery outcomes and completion evidence; the Planning Guide owns required project inputs; role files own agent responsibilities and authority; handoffs own discussion status. Keep explanations in their authoritative document and link elsewhere.

Final registration documentation alignment uses two independent passes: decision fidelity and cross-document consistency. Trace initial registration, clarification, review, confirmation, cancellation, recovery, and re-registration across the architecture, CLI and registration declarations, guide, and roles. For each journey check input origin, recipient, saved record, visible result, advancement condition, and essential failure behavior. Trace requirements to delivery criteria and criteria back to authorized requirements.

Apply corrections to authoritative documents without introducing preferred features, stronger acceptance rules, or general Execution policy through registration review. Live software verification belongs to implementation. Separate review reports are not retained unless requested.
