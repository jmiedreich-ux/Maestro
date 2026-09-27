# Make outcome criteria and evidence stronger

## Outcome and result
Maestro's outcome documents, and the workshop templates that produce them, carry sharper acceptance criteria and stronger evidence rules, using engineering practice from pstack (github.com/cursor/plugins, MIT).

## Existing implementation assessment
The outcome template has acceptance criteria with a Result column and a definition of done. It has no list of entry points, no standard checks for repeated or interrupted runs, and no scale for how strong evidence is.

## Ideas to consider
- List every way in for an outcome (a command, a key, an API call). Each criterion says which entry point it proves. A skipped entry point is never reported as verified through another path; an unreachable one is reported with the attempted command and the missing precondition. **Adopted 2026-09-27.**
- Write each criterion as a named starting state, an action, and an exact visible result. **Adopted 2026-09-27.**
- Any criterion that saves something needs a read-back from a second place. **Adopted 2026-09-27.**
- For anything that changes state or loops, add two standard rows: run it twice, and stop it mid-run then restart. Both must end in the same state. **Adopted 2026-09-27.**
- Rate the strength of evidence. "Someone said so" and "I read the code" never count as met. "I ran it in the real app" does.
- Allow the results blocked, inconclusive and product gap. Never edit a criterion to match the product.
- The evidence column names a command that can be run again, and the artifact it saves survives cleanup.
- A test would still pass if everything it imports returned nothing? Then it proves nothing. Expected results are literal values from outside the code under test.
- Mocks only where a production boundary already isolates the outside system, and the reason is written down.
- For a fix, the evidence is the original repro run before and after, on the same surface.
- For a number, the pass boundary is a target plus a noise rule, and the check is shown to tell good from bad.
- Nothing in the evidence comes from a check or baseline changed in the same slice.
- Start feature definitions from two or three realistic user journeys, with one named alternative and a list of open questions. Watch for a state layer built without the parts that use it.
- Keep out: prototype results filling a Result cell, and Cursor-specific tooling.
