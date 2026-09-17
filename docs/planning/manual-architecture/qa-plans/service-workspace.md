# Connected service and workspace — milestone QA plan

Version 1. Manual acceptance procedure specification. Incorporates all [shared QA rules](README.md), including authority, resource binding, evidence, cleanup and the runtime conversion checklist. No checks have run.

## Milestone and controlling outcomes

Applies only to [Connected service and workspace](../development-milestones.md#connected-service-and-workspace). Its allocated packets, integration dependencies and linked pinned project declarations define scope. Read their full acceptance criteria and definitions of done; these concrete scenarios may share evidence but do not waive an unlisted required criterion. Product behavior remains in [architecture](../../../architecture.md#milestone-quality-assurance-and-test-data).

## Entry and setup

Linux installation, Service persistence, Owner authentication, Durable request delivery, Project and activity records, Event stream, Terminal connection, Terminal workspace and Linked questions must be integrated. Use no actual agent or external repository path for this early contribution.

Execute the shared setup sequence and record the exact installed candidate, plan/input hashes and resolved resources before the checks. Resource names and script hashes are unresolved implementation/binding inputs, not fabricated values. No new account, host, repository or credential is provisioned by this plan.

## Test inputs and real entry paths

Fresh isolated test installation and empty database; two distinct test request identities; a generic linked-question input delivered through the implemented service interface. This input tests infrastructure only; real two-project Registration evidence is required later.

Record actual input hashes/lineage and sanitization classification under the shared data rules. Use the real public path named in each check; capture failures as well as successes. Data preparation must not insert the expected result into internal state.

## Required checks

| Check | Procedure | Expected result / essential failure boundary | Required evidence |
|---|---|---|---|
| Install and restart | Follow the candidate's documented installation, start it, close the CLI, perform controlled service restart/crash recovery and the approved boot check. | Correct test account/files/schema resources are used; systemd starts/restarts the service independently of the terminal. Startup diagnostics distinguish failed/running/restarting from process readiness. | Installed revision, systemd status/logs, identity/permission observations and before/after saved-request evidence. |
| Authentication and storage | Open the installed terminal using the separate test Owner credential; repeat without it and with an invalid one. Attempt Owner-credential access as the configured agent identity. | Authorized reads work; missing/invalid access is rejected; agent cannot read/use Owner credentials. Actual configured SQLite uses WAL/FULL/foreign keys and survives restart. | Redacted CLI/API results, filesystem access-denial evidence and read-only connection/configuration observations. |
| Empty workspace and navigation | Read an empty workspace; switch views, edit/discard input, scroll/page history, then make the service unreachable. | Empty is distinct from failed/offline. Current project/activity and input behavior follow the CLI architecture; disconnect does not imply work stopped or resubmit input. | Terminal captures and correlated requests/events; no fabricated project status. |
| Connection selection | Test malformed configuration, a valid but unreachable configured URL, retry/reload and a changed service address. | Fallback is used only where defined; valid unreachable URL remains selected, initial failure waits for retry, reconnect uses bounded backoff and address change clears old input. | Effective address, timing/configuration and actual connection attempts. |
| Durable request and answer | Use one real service request to create a supported generic activity/question, answer with correct identity/version, lose its acknowledgment, retry identically and then with conflicting content; restart. | Receipt/effect/event commit together; identical retry returns saved result, conflict/stale/wrong-project answer is rejected; pending delivery survives. Do not claim this proves Registration-specific questions. | Request/question/version/receipt identities, durable observations and visible response. |
| Event continuity | Disconnect while actual supported activity changes, reconnect from snapshot/cursor and observe quiet-connection heartbeat/loss handling. | Only committed changes appear; no missing saved updates or duplicate event application; history pagination is stable. | Snapshot/cursor/SSE identities and correlated terminal state. |
| Startup failure and isolation | Use a separate test instance with an invalid configuration or inaccessible test data location, then restore it. | Clear failure with no silent fallback/replacement database or production access; correction restores only the test instance. | Actual error, unchanged protected paths and corrected startup evidence. |

## Completion and correction

Every required check must satisfy the shared PASS boundary on the same exact candidate. A required missing path, missing tool, missing observation or unavailable artifact is UNTESTED and blocks acceptance; an observed behavior defect is FAIL. Use existing correction and affected-rerun rules, not an extra QA approval round. Independent whole-milestone review remains separate and required before promotion.

This milestone accepts installed infrastructure and workspace behavior only. Runtime/CLI outcomes that require real projects, questions and agents are completed using Registration and later assembled evidence, not synthetic records here.

## Cleanup and reset

Stop only the isolated service and any owned clients; preserve durable request/event evidence before removing disposable test data. Verify a fresh installation starts empty and old credentials cannot authenticate.

Apply the shared reset checklist. Capture evidence before cleanup, record retained/deferred resources and quarantine unsafe or uncertain environments. Do not destroy evidence or widen cleanup scope to obtain a clean result.
