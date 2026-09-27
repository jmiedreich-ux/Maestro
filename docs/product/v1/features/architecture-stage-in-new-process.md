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
- Show which features can run in parallel. Two features are parallel only if the files they touch do not overlap. When two would write the same state, split the ownership first and only then consider taking turns.
- Order the work: the foundation every later feature needs first, then removals, then the riskiest unknown, then the rest. Record a baseline before the work so the check reads "before and after".
- When retiring old code, list its callers and migrate them in the same feature that deletes it.
- Give each coder a short brief: goal, allowed and forbidden files, context, checkable criteria, how to verify, time limit, and what to report. A field the architect cannot fill means the feature is not scoped yet. Paste upstream results in full, because a coder cannot see other coders' work.
- For a new kind of feature, run one pilot packet first to test the brief, the packet size and the verification.
- A review verdict belongs to one exact version of the change. If the change moves, the verdict is void.
- A milestone is complete only when its features form an unbroken run of verified work.
- Bound the one correction: only findings that must be acted on go to the coder. "I would have done it differently" is not a finding.
- Label what is known about existing code as Direct, Supported, Inferred, Speculative or Unknown.
- Keep out: pstack's self-continuing goals, self-merging, unbounded reviewer swarms, and anything that starts a phase without the Owner.

