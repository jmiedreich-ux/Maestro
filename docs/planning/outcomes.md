# Maestro development outcomes

This is the ordered roadmap for building Maestro. The linked outcome specifications describe the product's required behavior; this roadmap and the [delivery rules](../development-process/delivery-rules.md) govern how Maestro itself is developed. Product work packets and milestones created later by Maestro are separate runtime data.

## Ordered outcomes

| Order | Outcome | Observable result |
|---|---|---|
| 1 | [Prepare a verified development environment](../outcomes/development-environment.md#prepare-a-verified-development-environment) | A developer can start a real agent in a clean workspace, read its inputs, write an output and exit cleanly; one preflight reports all prerequisites required for the selected feature, including host, credential, route, repository and test-data checks. |
| 2 | [Operate the persistent Maestro service](../outcomes/runtime-service.md#operate-the-persistent-maestro-service) | The installed Linux service starts, reports failed setup, and restarts independently of the terminal. |
| 3 | [Preserve project activity and requests](../outcomes/runtime-service.md#preserve-project-activity-and-requests) | Project activity, requests, questions, and identities survive restarts without duplicate effects or cross-project leakage. |
| 4 | [Connect the CLI to recorded service activity](../outcomes/runtime-service.md#connect-the-cli-to-recorded-service-activity) | The local API serves saved state, accepts supported requests, and replays events after reconnection. |
| 5 | [Connected multi-project CLI workspace](../outcomes/cli.md#connected-multi-project-cli-workspace) | The Owner can open and navigate a connected workspace for multiple projects and see current activity and attention. |
| 6 | [Reliable project questions and answers](../outcomes/cli.md#reliable-project-questions-and-answers) | The Owner can answer the intended question once and see a durable receipt and any correction needed. |
| 7 | [Run and recover assigned agents](../outcomes/runtime-service.md#run-and-recover-assigned-agents) | Selected agents run in isolated workspaces with validated results, progress, stop and recovery behavior. |
| 8 | [Apply shared process definitions](../outcomes/runtime-service.md#apply-shared-process-definitions) | Installed process definitions direct shared runtime behavior while process-specific rules remain distinct. |
| 9 | [Register and confirm a project through the CLI](../outcomes/registration.md#register-and-confirm-a-project-through-the-cli) | The Owner can register and confirm an exact project scope from real repository sources. |
| 10 | [Update a registration without losing approved history](../outcomes/registration.md#update-a-registration-without-losing-approved-history) | The Owner can update an idle registration and select a new active version without losing approved records. |
| 11 | [Recover registration without losing decisions or exceeding limits](../outcomes/registration.md#recover-registration-without-losing-decisions-or-exceeding-limits) | An interrupted registration resumes or fails clearly without duplicate approval or exhausted limits being reset. |
| 12 | [Establish the project's architectural foundations](../outcomes/architecture-loop.md#establish-the-projects-architectural-foundations) | A confirmed project can start a persistent architect session that saves investigated structure and specialist guidance. |
| 13 | [Produce a bounded and parallel-ready work breakdown](../outcomes/architecture-loop.md#produce-a-bounded-and-parallel-ready-work-breakdown) | The architect can produce a bounded, dependency-aware development breakdown with required QA inputs for a registered project. |
| 14 | [Review and confirm the development breakdown](../outcomes/architecture-loop.md#review-and-confirm-the-development-breakdown) | An independently reviewed architecture result can be amended and confirmed at an exact revision without starting Execution. |
| 15 | [Deliver independently reviewed work packets](../outcomes/execution.md#deliver-independently-reviewed-work-packets) | Explicit Execution start can coordinate real assigned implementation, review and visible progress. |
| 16 | [Integrate work and deliver declared dependencies](../outcomes/execution.md#integrate-work-and-deliver-declared-dependencies) | Approved results integrate in verified order and make declared dependencies available. |
| 17 | [Resolve architectural gaps within authorized scope](../outcomes/execution.md#resolve-architectural-gaps-within-authorized-scope) | In-scope architectural gaps get bounded support, correction and Owner decisions. |
| 18 | [Verify milestones and publish completed Execution](../outcomes/execution.md#verify-milestones-and-publish-completed-execution) | Assembled results pass isolated QA and outcome review before promotion and recorded completion. |
| 19 | [Pause, stop and recover Execution](../outcomes/execution.md#pause-stop-and-recover-execution) | The Owner can pause, resume or stop work, with interrupted work recovered from saved facts. |

The order states dependencies, not a fixed worker schedule. Shared foundations can be implemented before a consuming flow supplies final connected evidence. Recovery and essential errors belong inside the feature they protect. Monitoring is observable through the service and CLI outcomes and through Execution progress; it is not a separate speculative application.

## Prerequisite pass

Use the [single environment contract](../development-process/environment-contract.md) and record the [prerequisite pass](prerequisite-pass.md) before confirming a feature plan. For each assumption ask what must exist, how it will be proved, and what happens when it is absent. Cover the full contract, mark each category applicable or excluded with a reason, and identify the proving feature. Unknown operational condition stays unverified. Service installation is an outcome; installed service checks apply when a feature needs it.

## Development planning boundary

Begin by mapping the next outcome to existing source, tests, entry paths and installed behavior. Record what can be reused as it stands, what needs adaptation, and the specific gap that requires new code. Preserve working behavior and choose replacement only when a concrete incompatibility makes adaptation unsuitable. Define end-to-end features against the real code only for the next usable checkpoint. Each has an entry point, saved or visible result, permitted paths, dependencies, owner, verification, and failure recovery. A bounded pseudocode or feasibility walkthrough finds missing contracts before coding. The feature owner records small work packets inside the saved feature plan during implementation; there is no repository packet inventory or fixed packet count.

Place a development milestone only after its features form a usable assembled result, then specify QA and branch integration for that checkpoint. The first checkpoint is now planned in [development milestones](milestones.md), beginning with outcome 1. One review and one targeted correction are the default for a connected feature; unresolved scope or outcome changes return to the architect and Owner. A passed checkpoint closes.

## Current state and next planning work

The Owner reports previous implementation through initial registration. Master contains service, agent, terminal and registration source and tests; the exact current behavior and installed condition still require assessment against the outcome specifications. Outcomes through initial registration are reuse and adaptation candidates, not automatic rebuild tasks. The next [checkpoint](milestones.md) starts with a verified development environment. After that checkpoint passes, assess the persistent service as the next named outcome and continue in order. Existing source through registration remains a reuse and adaptation baseline, including the legacy registration path that creates graph work and a run; this does not establish installed behavior. The host, routes and external effects are unverified. This roadmap does not mark an outcome delivered from source presence or the Owner's implementation report alone.
