# Architectural analysis and independent reviews

## Architectural and gap analysis

Inspect the relevant current sources before reaching a conclusion. Trace the selected outcome from a clean starting condition to an observable usable result. Check the runtime, entry points, required access, data ownership, interfaces, lifecycle, integration, and essential failure/recovery behavior only where relevant to this project.

Map each outcome to architecture behavior and a declaration's completion evidence; trace each proposed criterion back to a supported outcome. Look for missing responsibilities, disconnected services, fake-data dependencies, undefined interactions, contradictory sources, and assumed setup. Code inspection establishes source support, not operational completion.

Classify a gap by the concrete outcome it prevents. Resolve in-scope technical detail as architect. Route outcome/scope decisions to the owner. Do not add fashionable patterns, exhaustive tests, or speculative requirements. Preserve a supported narrow scope rather than assuming an entire platform is required.

## Independent pass assignments

Use separate reviewer agents/sessions where available and permitted by the environment. Do not give them the author's desired verdict or suggested fixes. Both receive the same exact source snapshot, the guide, relevant original conversation excerpts/decision evidence, selected scope, and the affected documents. Mark missing original evidence explicitly; a decision index alone cannot prove conversation fidelity when the underlying meaning is disputed.

**Decision fidelity reviewer:** Compare the recorded owner agreements and architect decisions with the documents. Identify lost requirements, invented approval, altered scope, misleading readiness claims, or changed meanings. Check that unanswered questions remain unresolved and later corrections supersede earlier statements.

**Architecture and consistency reviewer:** Trace usable journeys, data and interface ownership, prerequisites, dependencies, milestone coverage, and references. Find material omissions or contradictions that would force implementers to invent behavior. Check existing-code claims against supplied inspection evidence. Do not demand live verification during a documentation assessment.

Ask each reviewer for: covered sources, result (pass, material changes required, or evidence unavailable), and only concrete findings with source, affected outcome, reason, and minimum correction. Do not ask for a minimum finding count.

## Disposition and limits

A blocker must identify a violated agreement, contradiction, or missing fact that prevents the selected outcome from being understood or delivered. Preference, stylistic variation, optional optimization, and speculative edge cases do not block.

The architect checks each finding against evidence. Correct a valid in-scope finding in the authoritative document and update affected declarations/state. Reject an incorrect finding with its reason. Record accepted limitations only within the owner's established authority; a reviewer cannot grant scope changes. Escalate material disagreement without forcing approval.

Use the bound in workshop state, default two rounds per pass. Recheck the correction and its affected dependencies, not the whole unchanged project. A passing first round ends that pass. If material issues remain at the bound, save them and pause only affected work for a decision. Do not restart the review counter in a new session.

Routine link checks and unchanged-content moves do not consume fidelity rounds. New evidence or changed requirements can invalidate specific prior coverage, with the reason recorded. Never use renamed work to evade the bound.

Persist coverage metadata and unresolved finding references in workshop state. Apply corrections to main documents; do not retain separate review reports unless requested. If no independent agent/session is available, label the work self-checked and independent review pending. Complete other authorized work; do not fabricate reviewer identities.
