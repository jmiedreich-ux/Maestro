# Development environment outcome

This outcome prepares the environment used to build Maestro itself. It does not define an environment policy for projects later run by Maestro.

## Prepare a verified development environment

**Outcome:** A developer or assigned agent can start in a clean workspace, read the assigned source, write an output, run a baseline check and exit cleanly. A single preflight identifies every unmet requirement before dispatch or assembled QA.

**Included:** Linux host and tools, installed service revision, repository access, owner and service credentials, selected model routes, sandbox mounts and permissions, ports and running dependencies, realistic test targets and data, a reusable known-good workspace, and a documented reset of run-owned data.

**Completion evidence:** Exact host and tool versions, non-secret credential and route status, one preflight with all checks passing, actual agent launch/output/exit, baseline check, and failure reports for deliberately absent prerequisites. No code outcome is claimed complete from mock routes or file presence.

**Failure behavior:** Preflight blocks only affected work and reports all missing items together. Environment failures are fixed and rechecked outside the coder's review count. Unknown access or installed state remains unverified; the developer does not improvise a substitute.

See [the development delivery rules](../planning/manual-architecture/packet-rules.md) and [the roadmap](../../plan/outcomes.md).
