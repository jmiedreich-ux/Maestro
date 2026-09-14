# Durable workshop state

Use the repository's existing equivalent state file, otherwise `docs/planning/workshop-state.json`. Start from [the state template](../assets/workshop-state.json). It is process bookkeeping, not a second architecture document.

## What to keep

- Repository identity, source revision, documentation paths, established publication route and the instruction granting it.
- Current topic, covered topics, next action, and current status: discovering, discussing, drafting, reviewing, ready, or paused.
- Decision index: stable identifier plus subject, owner agreement or architect decision, short evidence excerpt or reliable conversation locator, rationale location, canonical document/section, and supersession link when applicable.
- Open questions: subject, exact missing decision, affected outcome/source, and who can resolve it. Mark resolved or superseded; do not leave stale open duplicates.
- Inspections: source revision, inspected paths, evidence level, relevant findings, and canonical evidence location. Do not claim inspection of files that were not read.
- Review coverage: use the review-coverage record below; empty or missing traces never establish a completed pass.
- Save state: authorized delivery level, verified local paths and content hashes or documentation commit, pending paths and expected base, and separate remote publication status. Local-only completion does not require a remote revision. Exclude the state file itself from self-referential content hashes.

Use arrays for multiple items, null for unknown values, positive versions, and relative repository paths. Add records only for real work. The template's empty arrays are not evidence of completed discovery or reviews. Keep secrets and raw transcripts out.

## Saving and recovery

Save authoritative documents and decision evidence together at a topic boundary. Record a brief owner excerpt accurately; an agent paraphrase remains labeled a paraphrase. Architect choices identify the architect as authority, not the owner. Store enough evidence for a fresh reviewer to distinguish agreements from suggestions without replaying days of conversation.

Before resuming, verify the target repo and compare saved revisions with current sources. Reconcile concurrent edits rather than overwriting them. Invalidate review coverage only for changed meaning and affected dependencies; path-only moves require link checks, not new architectural judgments.

If a write outcome is uncertain, read the exact destination and compare expected content before retrying. Do not replay commits blindly. A checkpoint preserves the last known state and outstanding write, not a claim that publication succeeded.

When context is pressured, save the active topic, confirmed decisions, unresolved question, next action, and source references before summarizing. On continuation, read these sources instead of relying on compacted memory. A skill cannot guarantee host context measurement or checkpoint timing; when the host gives no warning, preserve state at normal topic boundaries.

## Configurable review bound

`review_policy.maximum_rounds_per_pass` defaults to 2 for each reviewed subject/content set. A first passing round is sufficient. A material correction can use one targeted recheck. The budget continues across resumed sessions for the same unresolved work. Repository or explicit owner policy can change it; record the change, never silently reset it.

## Review coverage record

The [review method](reviews.md) owns the procedure and completion conditions. This section owns storage fields. The JSON asset's `review_templates` are blank shapes for constructing records, not performed reviews. Actual records go in `reviews`; keep earlier coverage and correction checks as separate linked entries.

| Field | Required information |
|---|---|
| `id`, `subject`, `pass_type` | Stable record identity with plain subject; decision_fidelity, architectural_completeness, or cross_document_consistency. |
| `mode`, `parent_review_id` | full or targeted; targeted checks link to earlier full coverage. |
| `scope`, `budget_key`, `round` | Exact included scope and stable accounting key; retain existing limits and consumed rounds across sessions. |
| `reviewer` | Agent identity, separate session identity, independent or self_checked, authorship eligibility, and prohibited-input exposure. Unknown values remain null. |
| `snapshot` | Repository, commit where available, document content hashes, packet hash, filtered passages with reason, and original decision-evidence references. |
| `sources_examined` | Path, revision/hash and headings actually examined; listing a source as supplied does not prove it was read. |
| `journeys` | Every selected major journey, with one entry for every trace item in the method. Each item records status defined/missing/not_applicable/not_assessed, supporting path and heading locations, and explanation. Consistency entries include the compared representations. |
| `not_assessed`, `missing_evidence` | Explicit boundaries and unavailable evidence, with effect on the conclusion. |
| `findings` | Identity and subject, blocking/non_blocking, missing or contradictory information, location or absence, affected outcome, impact, minimum correction, disposition and canonical reference. |
| `result`, `conclusion` | pass, material_changes_required, incomplete, or evidence_unavailable; a statement limited to recorded coverage. |
| `coverage_complete`, `round_consumed` | Booleans reflecting validated coverage and the applicable existing budget. An incomplete record consumes no review round; record its attempt without calling it reviewed. |
| `correction_refs`, `invalidated_by` | Exact correction/source references and any later change making this coverage stale. |

Record original evidence references separately from document interpretations. Filtered passages identify exactly what was omitted from a fresh packet, without embedding the prohibited verdict or findings. Preserve raw evidence in its existing source; do not duplicate transcripts or create standalone reports.

Before accepting a record, verify that each selected journey contains all applicable trace categories with concrete locations or explicit absences. Missing definitions may yield a completed review with blocking findings; missing review coverage yields an incomplete pass. An unavailable source must be disclosed, never treated as agreement. A self-check cannot satisfy independent coverage.
