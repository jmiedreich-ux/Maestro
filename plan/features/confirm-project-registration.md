# Confirm and activate the exact registration

## Outcome and result
Complete [initial project registration](../../docs/outcomes/registration.md#register-and-confirm-a-project-through-the-cli). The Owner sees the exact published candidate and deliberately confirms it in the connected CLI. The service verifies that revision, saves one active registration reference and receipt, and retrieves the same package after service or terminal restart. Cancellation leaves no active registration. Confirmation does not start architecture or Execution automatically.

## Existing implementation to use
Adapt existing request deduplication, durable records, CLI activity/replay, source binding and GitHub read verification. The legacy `register_project` graph/run creation is incompatible with this registration boundary and must be separated from activation. Add only the activation state and remote reconciliation contract needed by the connected flow.

## Connected path
1. CLI shows candidate identity, pinned source, destination, review and publication evidence and asks for explicit confirmation of that exact revision.
2. Service checks candidate immutability and actual remote publication, records a single active reference and returns a durable receipt.
3. Duplicate confirmation returns the same result. If acknowledgment is lost, reconnect shows the stored decision and remote state; it never guesses approval or creates a second activation.
4. Cancellation before confirmation is recorded. A changed or missing candidate cannot be activated and provides a correction path.

## Dependencies and ownership
Depends on the first two features and real installed service, SQL persistence and GitHub access. Assign one owner at dispatch. Permitted implementation area: `services/maestro/maestro/project_onboarding.py`, `cli.py`, `service/`, `terminal/`, `github_client.py` and corresponding `tests/maestro/` tests, narrowed before coding. Record bounded implementation packets in this plan.

## Verification and stop
On the installed target, confirm one real published candidate, restart service and CLI, and retrieve exactly the active package and saved receipt. Exercise cancellation, repeated request, stale remote revision and lost acknowledgment. Check no graph, work packet, architecture session or Execution run was created. Stop on ambiguous remote or database state and expose reconciliation rather than claiming success.
