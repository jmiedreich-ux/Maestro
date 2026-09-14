# Documentation review method

This is the authoritative documentation-review method for the workshop and repositories that reference it. It defines review evidence and procedure, not role authority, runtime response schemas, publication permission, or new implementation requirements. Existing process-specific budgets govern runtime assignments; the workshop's existing bound is defined in [workshop state](workshop-state.md#configurable-review-bound).

## Independent inputs and eligibility

Freeze a review packet containing the selected scope, exact document snapshot (commit or content hashes), applicable Owner requirements, original decision evidence, decision-index entries, and accepted deferrals. Record source availability and any omissions. Requirements and decisions are evidence, not the author's claim that the documents satisfy them.

Do not supply the author's conclusions, expected verdict, suspected defects, prior review findings on the same content, or suggested fixes to a fresh reviewer. Start a separate context without the drafting conversation. If source files contain prior review results or readiness conclusions, exclude those passages from the input packet, record their original location and the filtered packet hash, and supply the remaining text unchanged. Do not hide requirements or deferrals when filtering conclusions. A reviewer who accidentally receives prohibited material cannot count as the fresh independent pass; record the limitation.

A reviewer who authored or corrected any reviewed document is ineligible, including for correction checks. A separate agent/session must be available and permitted. Otherwise label the pass self-checked and independent review pending, with no fabricated identity. One agent may perform multiple pass types only in separate sessions with separate outputs.

## Three pass assignments

| Pass | Distinct question |
|---|---|
| Decision fidelity | Are agreed requirements and decisions preserved without omissions, invented approval, altered meaning, or silently resolved open questions? |
| Architectural completeness | Could an implementer build and operate the described capability without inventing a missing architectural decision? Ask where it is defined, not whether it reads well. |
| Cross-document consistency | Do architecture, milestone declarations, guides, schemas, roles, and handoffs agree, including configuration keys/defaults, record formats, and file layouts? |

Each pass returns its own coverage and findings. Do not combine completeness and consistency into one verdict. A fidelity reviewer cannot establish completeness merely by finding no changed decisions. All passes use the common journey trace; fidelity checks the controlling decision, completeness the defining behavior, and consistency the agreement of all applicable representations.

## Complete journey trace

Enumerate every major journey in the selected scope before reviewing. For each journey, record a path and heading defining each item below, plus schema keys or code evidence where relevant. A shared definition may be referenced from several journeys; it is not assumed to apply without checking.

| Trace item | Required examination |
|---|---|
| Starting conditions | Prerequisites, setup, entry conditions, and the responsibility for making them available. |
| Input and recipient | Where input originates, which component receives it, and how it reaches that component. |
| Configuration and selections | Every needed value and default; which actor chooses each tool, exact model, source ref/commit, publication branch, or path, and when that selection is saved and validated. |
| Credentials and authority | The credential source and action authority for every actor, including the service itself; an agent credential does not automatically authorize service publication. |
| Storage and transactions | Authoritative owner/writer, selected engine or explicit engine requirements, concurrency assumptions, atomic boundaries, and durability behavior. |
| Interfaces and state | Request/response contracts, records, schemas, state transitions, identity/version checks, and mappings between prose and executable definitions. |
| Results and completion | Visible result, saved effect, advancement conditions, and evidence needed to establish the promised usable outcome. |
| Failure and recovery | Essential rejection, interruption, unknown-outcome, retry, cancellation, and recovery behavior across the journey. |

If no location defines an applicable item, record a completeness finding even when every document is silent. Agreement between documents cannot establish completeness when they share an omission. Explain why the absent decision matters; a justified not-applicable item is recorded with its reason, not silently skipped. A known pending decision or accepted deferral remains traceable and is not silently resolved.

Inspect existing code only where a readiness or reuse claim depends on it. Distinguish source-supported behavior from verified operation. Do not demand live verification, exhaustive tests, optional resilience, or preferred architectural patterns during documentation review. An explicit out-of-scope feature is not a missing requirement unless the agreed included outcome depends on it.

## Coverage and findings

Use the record fields in [workshop state](workshop-state.md#review-coverage-record). Each pass records sources/revisions examined, journeys traced, supporting path/heading locations for each item, and areas not assessed or lacking evidence. A conclusion without this record is incomplete and consumes no review round. Record the incomplete attempt so repeating it cannot masquerade as reviewed coverage; pause if the required evidence cannot be obtained.

For each finding state: missing or contradictory information, location or explicit absence, affected outcome, why it matters, minimum correction, and classification. Blocking means it prevents understanding or delivery of the agreed outcome; other findings are non-blocking. There is no minimum or maximum finding count.

Conclude with what was reviewed, what was found, and what remains unverified or outside scope. Say “no gaps found within the recorded coverage” when supported, never “no gaps remain.” Documentation review is not proof of implementation or operation.

## Full reviews and targeted correction checks

Before registration assessment, architecture-loop confirmation, or a handoff declaring sources sufficient, review the complete agreed scope independently through all three pass assignments. In a project without those stages, use the equivalent documentation-readiness checkpoint. This is a documentation method; it does not add runtime review rounds or change confirmation authority.

A targeted recheck receives the named findings, corrected snapshot, and directly affected dependencies. This necessary correction packet is the explicit exception to withholding prior findings from a fresh review. Label it targeted, not fresh or full. It verifies only those corrections and dependencies and never expands into a new full review. If evidence calls broader coverage into question, record affected coverage as stale and return for separate scope/budget disposition rather than expanding the recheck.

Keep existing bounded rounds. A passing first round ends that pass. Preserve consumption across renamed work, replacement sessions, and resumed workshops. Separating review responsibilities does not grant extra rounds to a runtime process that already shares a budget. Do not reopen unchanged decisions over preferences. Missing evidence is not a passing result.

## Disposition and retention

The architect checks findings against controlling evidence. Apply valid in-scope corrections to the authoritative documents and update affected references. Reject an incorrect finding with its reason. Accepted limitations and changed outcomes require the existing authority; reviewers cannot change scope, grant extra attempts, or force approval.

At the existing bound, retain unresolved material issues and pause only affected work for a decision. Continue useful unrelated work. Preserve the full-review coverage separately from targeted checks; corrected content is covered only through an explicit link to the valid earlier coverage and the completed recheck.

Return coverage and findings as agent output and retain the required coverage record in existing workshop state or the established handoff/runtime record. Do not create standalone review-report files. Normal user responses raise unresolved decisions and give bounded status; detailed review results are presented only when requested.
