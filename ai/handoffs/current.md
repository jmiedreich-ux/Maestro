# Current Maestro development state

- Scope: [manual development registration](../../docs/planning/manual-registration.md) and [ordered outcomes](../../docs/planning/outcomes.md).
- Status: [verified development environment milestone](../../docs/planning/milestones.md) evidence recorded 2026-09-23 in the [prerequisite pass](../../docs/planning/prerequisite-pass.md). Codex, Claude Code and local Qwen ran through the real workspace, isolation and egress path, and the automatic upgrade to a passed revision, with rollback, was exercised on the installed service. The Owner accepted the milestone on 2026-09-24.
- Closed 2026-09-24: [Operate the persistent Maestro service](../../docs/outcomes/runtime-service.md#operate-the-persistent-maestro-service), accepted by the Owner with recorded limitations (boot and crash restart unobserved; agent routes not validated at startup), filed as accepted exceptions on its acceptance criteria.
- Next: [Preserve project activity and requests](../../docs/outcomes/runtime-service.md#preserve-project-activity-and-requests), the next outcome in roadmap order; assess it against existing code and installed behavior.
- Progress updates: a host-local Slack update loop delivers receipts; the older packet loop and `LocalDurable` are not used as evidence.
