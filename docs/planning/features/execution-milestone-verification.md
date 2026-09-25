# Verify milestones and publish completed Execution

## Outcome and result
Closes [Verify milestones and publish completed Execution](../../outcomes/execution.md#verify-milestones-and-publish-completed-execution): an assembled milestone branch is exercised in an isolated environment by a real Quality Assurance agent, reviewed as a whole by a fresh independent reviewer, merged to the product's default branch only when both pass, and recorded in immutable milestone and Execution completion records that the terminal shows.

## Existing implementation assessment
Reused as built: the Execution service and its records, milestone branches and heads kept by integration, the run supervision used for managers and reviewers, the journaled Git handlers and remote verification, the milestone-gap assignment and supplement path, the shared Owner decision and the terminal's Execution view. Missing and built here: the `execution@3` schema bundle (`execution@1` and `execution@2` stay installed), Quality Assurance and milestone-review configuration, the isolated environment, the Quality Assurance and milestone reviewer assignments and their result contracts, artifact storage, the promotion merge, and milestone and Execution completion publication.

## Features
1. Milestone Quality Assurance: resolve the confirmed plan for a finished milestone, run its setup as argument arrays in a clean directory, run a real Quality Assurance agent through the plan's journeys, store artifacts with identity, hash and size, and record `PASS`, `FAIL` or `UNTESTED` per check. Bypassed or unavailable required paths stay `UNTESTED` and block promotion.
2. Milestone outcome review and promotion: a fresh non-author reviewer checks the exact assembled head against the milestone's criteria and the Quality Assurance evidence; blocking findings enter the milestone-gap path; a passing review with passing Quality Assurance permits the non-fast-forward merge to the product's default branch, verified on the remote; a changed target or unsatisfied gate is refused.
3. Completion: immutable milestone completion records, then the Execution completion record, are published and verified before SQL marks them complete; the terminal shows the summary and blockers.

## Decisions
- Quality Assurance and milestone review use the same durable assignment and run supervision as other reviewers; each saves its configuration snapshot, inputs, route, run and result before acting.
- Setup runs only commands from the confirmed plan; the agent cannot supply new setup text.
- A plan that names project bindings, secrets or network dependencies is `UNTESTED` unless the operator's binding resolves; self-contained plans need none.

## Verification
Unit tests in `tests/maestro/service/`; real proof on a disposable service under `var/qa/verify-live/` with real agents and the real repository.
