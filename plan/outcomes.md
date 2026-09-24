# Maestro development outcomes

This is the ordered roadmap for building Maestro. The linked outcome specifications describe the product's required behavior; this roadmap and the [delivery rules](../docs/planning/manual-architecture/packet-rules.md) govern how Maestro itself is developed. Product work packets and milestones created later by Maestro are separate runtime data.

## Ordered outcomes

| Order | Outcome | Observable result |
|---|---|---|
| 1 | [Prepare a verified development environment](../docs/outcomes/development-environment.md#prepare-a-verified-development-environment) | A developer can start a real agent in a clean workspace, read its inputs, write an output and exit cleanly; one preflight reports all prerequisites required for the selected feature, including host, credential, route, repository and test-data checks. |
| 2 | [Operate the persistent Maestro service](../docs/outcomes/runtime-service.md#operate-the-persistent-maestro-service) | The installed Linux service starts, reports failed setup, and restarts independently of the terminal. |
| 3 | [Preserve project activity and requests](../docs/outcomes/runtime-service.md#preserve-project-activity-and-requests) | Project activity, requests, questions, and identities survive restarts without duplicate effects or cross-project leakage. |
| 4 | [Connect the CLI to recorded service activity](../docs/outcomes/runtime-service.md#connect-the-cli-to-recorded-service-activity) | The local API serves saved state, accepts supported requests, and replays events after reconnection. |
| 5 | [Connected multi-project CLI workspace](../docs/outcomes/cli.md#connected-multi-project-cli-workspace) | The Owner can open and navigate a connected workspace for multiple projects and see current activity and attention. |
| 6 | [Reliable project questions and answers](../docs/outcomes/cli.md#reliable-project-questions-and-answers) | The Owner can answer the intended question once and see a durable receipt and any correction needed. |
| 7 | [Run and recover assigned agents](../docs/outcomes/runtime-service.md#run-and-recover-assigned-agents) | Selected agents run in isolated workspaces with validated results, progress, stop and recovery behavior. |
| 8 | [Apply shared process definitions](../docs/outcomes/runtime-service.md#apply-shared-process-definitions) | Installed process definitions direct shared runtime behavior while process-specific rules remain distinct. |
| 9 | [Register and confirm a project through the CLI](../docs/outcomes/registration.md#register-and-confirm-a-project-through-the-cli) | The Owner can register and confirm an exact project scope from real repository sources. |
| 10 | [Update a registration without losing approved history](../docs/outcomes/registration.md#update-a-registration-without-losing-approved-history) | The Owner can update an idle registration and select a new active version without losing approved records. |
| 11 | [Recover registration without losing decisions or exceeding limits](../docs/outcomes/registration.md#recover-registration-without-losing-decisions-or-exceeding-limits) | An interrupted registration resumes or fails clearly without duplicate approval or exhausted limits being reset. |
| 12 | [Establish the project's architectural foundations](../docs/outcomes/architecture-loop.md#establish-the-projects-architectural-foundations) | A confirmed project can start a persistent architect session that saves investigated structure and specialist guidance. |
| 13 | [Produce a bounded and parallel-ready work breakdown](../docs/outcomes/architecture-loop.md#produce-a-bounded-and-parallel-ready-work-breakdown) | The architect can produce a bounded, dependency-aware development breakdown with required QA inputs for a registered project. |
| 14 | [Review and confirm the development breakdown](../docs/outcomes/architecture-loop.md#review-and-confirm-the-development-breakdown) | An independently reviewed architecture result can be amended and confirmed at an exact revision without starting Execution. |
| 15 | [Deliver independently reviewed work packets](../docs/outcomes/execution.md#deliver-independently-reviewed-work-packets) | Explicit Execution start can coordinate real assigned implementation, review and visible progress. |
| 16 | [Integrate work and deliver declared dependencies](../docs/outcomes/execution.md#integrate-work-and-deliver-declared-dependencies) | Approved results integrate in verified order and make declared dependencies available. |
| 17 | [Resolve architectural gaps within authorized scope](../docs/outcomes/execution.md#resolve-architectural-gaps-within-authorized-scope) | In-scope architectural gaps get bounded support, correction and Owner decisions. |
| 18 | [Verify milestones and publish completed Execution](../docs/outcomes/execution.md#verify-milestones-and-publish-completed-execution) | Assembled results pass isolated QA and outcome review before promotion and recorded completion. |
| 19 | [Pause, stop and recover Execution](../docs/outcomes/execution.md#pause-stop-and-recover-execution) | The Owner can pause, resume or stop work, with interrupted work recovered from saved facts. |

The order states dependencies, not a fixed worker schedule. Shared foundations can be implemented before a consuming flow supplies final connected evidence. Recovery and essential errors belong inside the feature they protect. Monitoring is observable through the service and CLI outcomes and through Execution progress; it is not a separate speculative application.

## Prerequisite pass

Before the next feature is detailed, verify the prerequisites it actually needs: Linux host and installed tools, Owner identity and credentials, GitHub repository access, selected model routes, sandbox mounts, test-data reset, and observability. Check running service and ports when a feature depends on them; service installation is itself an outcome. Record each assumption and its proving feature or explicit exclusion. Unknown operational condition stays unverified. Installation, agent route and real GitHub integration must use actual targets to claim readiness.

## Development planning boundary

Begin by mapping the next outcome to existing source, tests, entry paths and installed behavior. Record what can be reused as it stands, what needs adaptation, and the specific gap that requires new code. Preserve working behavior and choose replacement only when a concrete incompatibility makes adaptation unsuitable. Define end-to-end features against the real code only for the next usable checkpoint. Each has an entry point, saved or visible result, permitted paths, dependencies, owner, verification, and failure recovery. A bounded pseudocode or feasibility walkthrough finds missing contracts before coding. The feature owner records small work packets inside the saved feature plan during implementation; there is no repository packet inventory or fixed packet count.

Place a development milestone only after its features form a usable assembled result, then specify QA and branch integration for that checkpoint. No milestone is preallocated by this registration. One review and one targeted correction are the default for a connected feature; unresolved scope or outcome changes return to the architect and Owner. A passed checkpoint closes.

## Current state and next planning work

The Owner reports previous implementation through initial registration. Master contains service, agent, terminal and registration source and tests; the exact current behavior and installed condition still require assessment against the outcome specifications. Outcomes through initial registration are reuse and adaptation candidates, not automatic rebuild tasks. The first feature planning pass checks the environment contract, traces the actual code and connected flow, and plans only the verified gaps. This roadmap does not mark an outcome delivered from source presence or the report alone.
