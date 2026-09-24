# Current Maestro development state

- Scope: [manual development registration](../../docs/planning/manual-registration.md) and [ordered outcomes](../../docs/planning/outcomes.md).
- Status: [verified development environment milestone](../../docs/planning/milestones.md) evidence recorded 2026-09-23 in the [prerequisite pass](../../docs/planning/prerequisite-pass.md). Codex, Claude Code and local Qwen each ran twice through the real workspace, isolation and egress path at the pinned revision, and a removed prerequisite blocked dispatch. The milestone is not accepted.
- Next: Codex reviews the evidence and the local branch `feature/verify-development-environment`. Then assess the persistent service.
- Open: protected-branch case unverified on the private QA repository; ordinary GitHub write not exercised; Claude setup token lifetime unverified (the token was pasted into a chat and should be revoked and re-issued); agent-written run files need an elevated reset; the installed service does not yet include the Qwen route.
- Progress updates: a host-local Slack update loop delivers receipts; the older packet loop and `LocalDurable` are not used as evidence.
