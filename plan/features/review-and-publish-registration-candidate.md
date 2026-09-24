# Review and publish a registration candidate

## Outcome and result
Continue the saved [initial registration](../../docs/outcomes/registration.md#register-and-confirm-a-project-through-the-cli). A separate reviewer examines the architect's assessment against the pinned source and overview, bounded corrections are resolved, and a validated candidate is published to the chosen GitHub destination. The Owner can inspect the exact candidate revision and review evidence before confirmation. Publication alone does not activate it.

## Existing implementation to use
Use shared `ProcessPolicyService`, route checks, agent supervision and persistent sessions; preserve the saved assessment and question receipts. `github_client.py` already reads GitHub data, but its observed surface does not yet publish content; extend it narrowly for authorized writes and reconciliation. Reuse source loader and records. Do not treat a generic test stub or same model route as an independent reviewer.

## Connected path
1. Start only from a saved assessment and source snapshot. Reviewer is distinct from architect and receives the same pinned evidence.
2. Save reviewer findings and a bounded architect correction cycle under the installed registration policy. Re-review corrected material when required; exhausted limits stop visibly.
3. Validate package structure, scope, links and destination permissions, then publish the candidate with an idempotent GitHub write and durable commit or content identity.
4. CLI displays the candidate, review result, exact revision, unresolved questions and publication receipt. Changed source or conflicting remote content blocks confirmation until reconciled.

## Dependencies and ownership
Depends on the first feature and its proven source, service, agent and GitHub prerequisites. Assign one owner at dispatch. Permitted implementation area: `services/maestro/maestro/github_client.py`, `service/`, `agents/`, `terminal/` and corresponding `tests/maestro/` tests, narrowed to exact files before coding. Record implementation packet notes within this plan.

## Verification and stop
With real distinct routes and authorized test GitHub destination, inspect reviewer evidence, bounded corrections and the actual published commit and package. Retry after interrupted or uncertain write without duplicate candidate effects. Test stale source, conflicting destination, reviewer failure and limit exhaustion. Stop if real publication or independent review cannot be evidenced.
