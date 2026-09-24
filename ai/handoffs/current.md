# Current Maestro development state

- Scope: [manual development registration](../../docs/planning/manual-registration.md) and [ordered outcomes](../../docs/planning/outcomes.md).
- Status: [verified development environment milestone](../../docs/planning/milestones.md) planned; [prerequisite pass](../../docs/planning/prerequisite-pass.md) unverified. Existing service, terminal, agent and registration code is available for reuse assessment, not accepted as an installed outcome.
- Next: assign the [environment feature](../../docs/planning/features/verify-development-environment.md), confirm its file allowlist, check the actual host and run the [environment contract](../../docs/development-process/environment-contract.md). Then assess the persistent service.
- Reported blockers awaiting host verification: Claude OAuth token may be expired; GitHub app may lack Administration: read permission; private QA repository branches may be protected against the required test writes; `agents.toml` route configuration may be unavailable or incorrect. Check each on the actual target; do not assume it remains broken or has been fixed.
- Other unverified conditions: installed tools, selected model identity, workspace permissions, credentials and realistic data/reset. No host check or outcome acceptance is recorded.
