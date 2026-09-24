# Resolve architectural gaps within authorized scope

## Outcome and result
Closes [Resolve architectural gaps within authorized scope](../../outcomes/execution.md#resolve-architectural-gaps-within-authorized-scope): a missing specialist, an architectural question or an exhausted review limit, and a milestone finding each reach their own bounded, read-only Project Architect assignment; valid results become executable through exact published records without changing confirmed scope, and the Owner decides at a limit or before re-registration.

## Existing implementation assessment
Reused as built: the Execution service and its records, the agent run service, the journaled publication to the project's publication branch, the packet review and integration review patterns, the shared Owner decision and the terminal's Execution view. Missing and built here: the support, determination and milestone-gap assignments, their configuration snapshot, the fidelity review of a new role, publication and activation of support and supplement records, the Owner decisions for support review, architectural determinations and work disposition, and the start restriction. The milestone finding producer is the next outcome (Verify milestones and publish completed Execution); here findings enter through a service operation that outcome will call.

## Features
1. Missing-specialist support: request from the Development Manager, support architect, independent fidelity review of a new role, publication and activation binding, backup route, review limit with architect recommendation and Owner decision.
2. Architectural determinations and Owner authority: packet and integration questions and exhausted review limits reach a determination assignment with a saved recommendation before the Owner's typed choice; work disposition before re-registration with the saved start restriction.
3. Milestone gaps and supplements: a recorded milestone finding reaches its own assignment; an in-scope supplement is validated, published with verified bytes and hash, and activated into correction packets; defects and scope changes route to their own paths.

## Decisions
- Support, determination and gap assignments share one durable assignment table and the run supervision already used for managers and reviewers. Each saves its configuration snapshot, inputs, route, run and result before acting; a replacement keeps the assignment and its counts.
- Configuration comes from the Execution activity's start snapshot (`execution.architectural_support`, `execution.milestone_gap_architect`); when absent the affected request stays blocked with a plain reason.
- Existing packet and integration review-limit grants now wait for the saved architect recommendation.

## Verification
Unit tests in `tests/maestro/service/`; real proof on a disposable service under `var/qa/architecture-gaps-live/` with real agents and the real repository.
