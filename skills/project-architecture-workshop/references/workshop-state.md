# Durable workshop state

Use the repository's existing equivalent state file, otherwise `docs/planning/workshop-state.json`. Start from [the state template](../assets/workshop-state.json). It is process bookkeeping, not a second architecture document.

## What to keep

- Repository identity, source revision, documentation paths, established publication route and the instruction granting it.
- Current topic, covered topics, next action, and current status: discovering, discussing, drafting, reviewing, ready, or paused.
- Decision index: stable identifier plus subject, owner agreement or architect decision, short evidence excerpt or reliable conversation locator, rationale location, canonical document/section, and supersession link when applicable.
- Open questions: subject, exact missing decision, affected outcome/source, and who can resolve it. Mark resolved or superseded; do not leave stale open duplicates.
- Inspections: source revision, inspected paths, evidence level, relevant findings, and canonical evidence location. Do not claim inspection of files that were not read.
- Review coverage: pass type, independent reviewer/session identity or unavailable, exact document hashes/revision, covered subjects, result, correction round, and unresolved canonical finding references.
- Save state: last verified documentation revision, pending paths and expected base, and publication status. Exclude the state file itself from self-referential content hashes.

Use arrays for multiple items, null for unknown values, positive versions, and relative repository paths. Add records only for real work. The template's empty arrays are not evidence of completed discovery or reviews. Keep secrets and raw transcripts out.

## Saving and recovery

Save authoritative documents and decision evidence together at a topic boundary. Record a brief owner excerpt accurately; an agent paraphrase remains labeled a paraphrase. Architect choices identify the architect as authority, not the owner. Store enough evidence for a fresh reviewer to distinguish agreements from suggestions without replaying days of conversation.

Before resuming, verify the target repo and compare saved revisions with current sources. Reconcile concurrent edits rather than overwriting them. Invalidate review coverage only for changed meaning and affected dependencies; path-only moves require link checks, not new architectural judgments.

If a write outcome is uncertain, read the exact destination and compare expected content before retrying. Do not replay commits blindly. A checkpoint preserves the last known state and outstanding write, not a claim that publication succeeded.

When context is pressured, save the active topic, confirmed decisions, unresolved question, next action, and source references before summarizing. On continuation, read these sources instead of relying on compacted memory. A skill cannot guarantee host context measurement or checkpoint timing; when the host gives no warning, preserve state at normal topic boundaries.

## Configurable review bound

`review_policy.maximum_rounds_per_pass` defaults to 2 for each reviewed subject/content set. A first passing round is sufficient. A material correction can use one targeted recheck. The budget continues across resumed sessions for the same unresolved work. Repository or explicit owner policy can change it; record the change, never silently reset it.

