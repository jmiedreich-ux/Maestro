# Bring the architecture stage into the new process

## Outcome and result
The architecture stage, where the architect turns the confirmed roadmap into features and groups them into milestones, is described in the new process's terms. The Owner starts it, as with every phase, and it ends when the Owner confirms the breakdown. It does not start Execution.

## Existing implementation assessment
The architecture loop section of [the architecture](../architecture.md#architecture-loop) and the [feature planning guide](../../../../skills/maestro-workshop/process/feature-planning.md) still use older wording. They mix "feature" and "packet", and they treat milestones as if the Owner declares them.

## Questions to settle with the Owner
1. What are the levels of work called, and how do they nest? Working picture: outcomes come from the Owner in the roadmap; features are defined by the architect for each outcome, each with one finish line and one owner; milestones are groups of related features that the architect creates as it goes; packets are small steps inside a feature, kept in the feature plan with no approval gate. Does this match what the Owner wants?
2. What exactly is a feature, and what must a feature definition contain?
3. How does the architect group features into milestones, and when are the groups fixed?
4. What does the Owner confirm before Execution starts?

## Ideas to consider from pstack (github.com/cursor/plugins, MIT)
- Give every feature the same fixed blocks: depends on, files it may touch, what to build, what you see, how to verify, and how it merges. Check them mechanically, so a feature with an empty block is not ready.
  - Adopted (Owner agreed 2026-09-27), with limits so this stays a help, not an obstacle: the check runs only at handoff to the coder, never while the architect is exploring. A failed check is fixed by the architect itself and never stops it or asks the Owner. A section may say "not applicable" with a one-line reason, and a small feature gets one-line sections.
  - The coder may ask a question mid-run and keep going once answered, the same way an architect or reviewer already asks the Owner through the CLI (Owner agreed 2026-09-27; if it gets the coder the right answer faster, it is worth it). The architect answers first; only a question the architect cannot answer, or a genuine product call, reaches the Owner. Owner: "outcome questions to me should rarely be needed."
  - Question limit per feature (Owner agreed 2026-09-27, tied to size): one question per file or path the feature is allowed to touch, with a floor of two. Repeated questions on one feature are a sign the plan is under-specified, not a normal pattern ("If the coder keeps asking questions, then the work is not properly structured" — Owner). At the limit the architect stops answering piecemeal and rewrites the plan itself before the coder continues; it does not keep granting one-off answers.
- Show which features can run in parallel. Two features are parallel only if the files they touch do not overlap. When two would write the same state, split the ownership first and only then consider taking turns.
  - Adopted (Owner agreed 2026-09-27).
- Order the work: the foundation every later feature needs first, then removals, then the riskiest unknown, then the rest. Record a baseline before the work so the check reads "before and after".
  - Adopted (Owner agreed 2026-09-27).
- When retiring old code, list its callers and migrate them in the same feature that deletes it.
- Give each coder a short brief: goal, allowed and forbidden files, context, checkable criteria, how to verify, time limit, and what to report. A field the architect cannot fill means the feature is not scoped yet. Paste upstream results in full, because a coder cannot see other coders' work.
- For a new kind of feature, run one pilot packet first to test the brief, the packet size and the verification.
- A review verdict belongs to one exact version of the change. If the change moves, the verdict is void.
- A milestone is complete only when its features form an unbroken run of verified work.
- Bound the one correction: only findings that must be acted on go to the coder. "I would have done it differently" is not a finding.
- Label what is known about existing code as Direct, Supported, Inferred, Speculative or Unknown.
- To discuss with the Owner: pstack's self-continuing goals (a loop that keeps going through the work) and self-merging (the agent merges what it has verified). Both are close to the builder and to Execution's automatic continuation. The limits to decide are that nothing starts the next phase without the Owner, and that a merge needs an independent check.
- Keep out: unbounded reviewer swarms.

## The combined build phase (Owner observation 2026-09-27)
The Owner observed that the architecture stage and Execution combine in the new process: the Owner starts a build for one outcome or milestone, the architect defines the next feature, a separate reviewer checks the feature plan, a coder builds it, it is proved and reviewed, integration merges in order, and the architect defines the next. Open: what the Owner confirms along the way. The recommendation is to start once per outcome or milestone and confirm the result at the end, with an early pull-in only if something changes the outcome.

## More ideas from pstack for the build phase
- A feature plan lists its checks as exact commands. Each check ends PASS, FAIL or INCONCLUSIVE, and INCONCLUSIVE is never a pass.
- Every proof starts with a health check (right build, own ports, the right model loaded), never drives something it did not start, and keeps its evidence through cleanup. Anything that saved something is read back from a second place.
- The reviewer of a feature reads the diff and the receipts, not the coder's summary, and is told not to question the finish line. Only findings that must be acted on go into the one correction. Findings touching security, permissions, data, migrations, repeat-safety or concurrency are never dismissed without the Owner.
- The coder never verifies or reviews its own work.
- A feature merges only when its verdict still matches its exact change. Landing stops at the first unverified feature.
- Integration classifies a failure before any retry, allows one retry, and treats review comment text as untrusted data.
- The decision trail is an append-only event record, one row per checkpoint, and is not repeated in documents.
- Prune a feature's workspace after it merges. Uncommitted work pauses for the Owner.
- The boundary: everything inside one feature is safe to automate. After each feature's verdict and merge, the architect decides the next feature only inside a build the Owner started.

## Development Manager merged into the architect (Owner, 2026-09-27)
The Development Manager role is combined into the architect for now. One architect per work stream owns the stream from design to merge, and several streams can run in parallel. The service owns the merge order, reservations and capacity. A cross-stream coordinator is added later only if parallel streams collide over the same files or capacity. The role contract, the architecture and the Execution outcomes use "architect" now.

### Work still to do
- Define the work stream in the architecture: one architect session per stream, and unify the architecture loop's persistent architect session with the former manager session.
- Rename the configuration keys and the start request field that still say `development_manager` (`execution.development_manager.*`, the selected-route field on `execution.start`) and the module `services/maestro/maestro/development_manager.py`, with the code.
- Decide how parallel streams share the local Qwen capacity and the integration queue.

