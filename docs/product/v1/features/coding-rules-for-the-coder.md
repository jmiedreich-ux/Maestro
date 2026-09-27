# Coding rules for the coder brief

## Outcome and result
The brief given to the coding agent (a local Qwen model, writing Python) carries a short set of code-quality rules, taken from pstack (github.com/cursor/plugins, MIT), so the code it writes is smaller, safer and easier to check.

## Existing implementation assessment
The coding agent instructions in [coding-agent-sop.md](../../../../skills/maestro-workshop/process/agents/coding-agent-sop.md) carry no code-quality rules of this kind. pstack's code-level advice is the closest source found.

## The ten rules to always include
1. Model states as a small set of named variants, not a bag of flags that must stay in sync.
2. Put logic in small pure functions and keep the code that touches the outside world thin.
3. Make illegal states impossible to build. If a comment has to explain when a combination of fields is valid, the type is too loose.
4. Parse outside data (JSON, environment, CLI input, database rows, model output) into a typed object at the edge, and pass that inward instead of raw dictionaries.
5. Validate only where data crosses a boundary. Inside, trust the types and do not add "should never happen" checks.
6. Never silence a crash with a guard. Trace it to its cause, reproduce it first, and fix every instance of the same pattern.
7. Every operation that changes state must survive running twice and crashing halfway. Check for existing state before creating it.
8. Tests call the code the way its users do and assert a literal expected value. A test that would still pass if every function it imports returned nothing is rewritten or deleted.
9. Make the smallest change that solves the problem. Prefer deleting, and keep a change from pushing a file past about 1,000 lines without a strong reason.
10. When replacing an interface, move every caller and delete the old one in the same change, with no compatibility shims.

## More rules worth considering
- Wrap meaningful values (an agent id, a path) so they cannot be swapped, and validate them once at creation.
- Do not use type-checker escapes (`# type: ignore`, unchecked casts).
- Give each concurrent writer its own file or key, and only take a lock when one shared writer is a real requirement.
- Prefer local variables over fields, fields over module state, and derive values instead of syncing them.
- For a bug fix, write the failing test first and confirm it fails for the intended reason.
- Do not mock what can be run locally.
- Keep the chain of calls flat: if answering "where does this come from" takes more than three files, flatten it.
- Delete dead code and needless validators before adding new code.
- Delete comments that narrate the code, and never leave commented-out code. Rename or restructure surprising code instead of explaining it.
- Use the real names from the codebase, one name per thing.
- In review, do not approve only because the behavior works. Check for ad hoc branching in unrelated flows, needless abstraction, duplicated helpers and logic in the wrong layer.

## Not to borrow
Rules specific to TypeScript, comment and writing style guides, and the advice to be ambitious about large rewrites, which works against the small-change rule for a small model.
