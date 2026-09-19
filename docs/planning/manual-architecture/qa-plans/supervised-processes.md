# Supervised shared processes — milestone QA plan

Version 1. Manual acceptance procedure specification. Incorporates all [shared QA rules](README.md), including authority, resource binding, evidence, cleanup and the runtime conversion checklist. No checks have run.

## Milestone and controlling outcomes

Applies only to [Supervised shared processes](../development-milestones.md#supervised-shared-processes). Its allocated packets, integration dependencies and linked pinned project declarations define scope. Read their full acceptance criteria and definitions of done; these concrete scenarios may share evidence but do not waive an unlisted required criterion. Product behavior remains in [architecture](../../../architecture.md#milestone-quality-assurance-and-test-data).

## Entry and setup

Previous milestone accepted; Shared process policy, Agent route preflight, Agent workspace and transport, Durable supervision and Session and context continuity integrated. Actual supported Codex/Claude capabilities required by declarations must have evidence; a single fake adapter cannot stand in.

Execute the shared setup sequence and record the exact installed candidate, plan/input hashes and resolved resources before the checks. Resource names and script hashes are unresolved implementation/binding inputs, not fabricated values. No new account, host, repository or credential is provisioned by this plan.

## Test inputs and real entry paths

A small run-owned source tree with a read-only fact-finding task and one bounded real output; separately selected supported architect/reviewer tools and exact models. Inputs contain no credential or desired reviewer verdict.

Record actual input hashes/lineage and sanitization classification under the shared data rules. Use the real public path named in each check; capture failures as well as successes. Data preparation must not insert the expected result into internal state.

## Required checks

| Check | Procedure | Expected result / essential failure boundary | Required evidence |
|---|---|---|---|
| Installed policy and preflight | Load installed schema/policy bundles, save effective settings, present valid and missing/mismatched tool/model choices separately for architect and reviewer. | Valid assignments bind immutable settings/resources; missing schemas or unverifiable model/capability reject launch without silent selection. | Installed paths/hashes, effective settings and actual preflight rejection. |
| Real transport and isolation | Launch actual bounded tasks through each required supported tool route into separate protected workspaces; observe structured result and progress. | Assignment/run/model identity and permitted paths agree; inputs stay immutable and author/reviewer sessions are separate. Credentials are unavailable to agents except the temporary Owner-approved, service-profiled subscription-CLI exception recorded in the architecture; no raw credential is included in assignment, output, evidence, or logs. | Tool executable/version/model evidence, workspace hashes, actual outputs and saved progress. |
| Supervisor restart | Interrupt the supervising service while the real task is active; reconnect/restart and reconcile PID/start/session evidence before considering replacement. | No duplicate live task; completed output is validated once; unknown original state blocks replacement. | Process identities, before/after assignment records, CLI and actual result. |
| Timeout and recovery budget | Use a saved shorter test duration for an actual run; exercise a recoverable failure and intervention/manual-retry path at its configured limit. | Timeout stops or shows uncertainty without inappropriate automatic retry; counters, deadline and one-use grant persist; stale output cannot advance. | Actual stop/recovery observations, typed receipts and counts across restart. |
| Context continuation | Exercise actual supported checkpoint/continuation with the bounded task and required saved context. | Verified work, tool/model binding, cumulative usage and remaining active time persist; context handling is not failure/review allowance reset. | Checkpoint/source hashes, linked session/run and measured/unknown context status. |
| Policy snapshots and terminal evidence | Change installed configuration only in a separate approved test setup after activity snapshot; reconnect CLI and replay progress observations. | Active work retains its snapshot; new configuration is not silently substituted. Duplicate usage observations are not double-counted; unknown measurements remain unknown. | Old/new configuration hashes, replay records and terminal observations. |

## Completion and correction

Every required check must satisfy the shared PASS boundary on the same exact candidate. A required missing path, missing tool, missing observation or unavailable artifact is UNTESTED and blocks acceptance; an observed behavior defect is FAIL. Use existing correction and affected-rerun rules, not an extra QA approval round. Independent whole-milestone review remains separate and required before promotion.

This establishes supervised infrastructure. Domain-specific Registration and Architecture continuation must still be exercised through their real assignments in the later plans.

## Cleanup and reset

Stop owned task processes, verify no orphan child or unit remains, release isolated workspaces only after outputs are retained; do not stop a shared model server.

Apply the shared reset checklist. Capture evidence before cleanup, record retained/deferred resources and quarantine unsafe or uncertain environments. Do not destroy evidence or widen cleanup scope to obtain a clean result.
