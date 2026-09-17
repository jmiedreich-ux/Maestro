# Manual work-packet specification rules

Version 2. These rules and the 42 linked packet records expand the Owner-confirmed manual planning scope. They are authoring specifications, not runtime assignments, implementation permission or a confirmed architecture output set.

## Exact inputs and authority

The registered scope is [candidate version 1](https://github.com/jmiedreich-ux/Maestro/blob/4953aa555b9e5da5b73407f62184c7905efb7898/docs/planning/manual-registration.md), accepted by the actual Owner response retained in the handoff. The unchanged code/behavior baseline is `182bf4290ef2960d4691a7f41315ebf71d5bf85c`. This preparation began from documentation master `e4d4ec4adba6a2088a19dedd20fad7f2039f3612`. These commits have different purposes; publication of this specification does not retarget the code baseline.

The Owner also selected the QA repository name `jmiedreich-ux/Maestro-qa`; existence, visibility, credentials, exact installed model routes and test-resource catalog remain unverified. See [QA resources](qa-resources.md). No secret is requested here.

Each packet includes its source outcome links and controlling architecture section. Read the complete linked outcome's scope, dependencies, acceptance criteria and definition of done, including its declaration's common evidence rules, at the pinned source commit. Packet summaries do not replace those requirements. [Investigation](investigation.md) supplies named inspected code and evidence limits; [project structure](project-structure.md) supplies intended boundaries. Uninspected helpers are not declared reusable.

The repository's [coding instructions](../../../docs/agents/coding-agent-sop.md), [Developer role](../../../docs/agents/maestro-developer.md), [architect authority](../../../docs/agents/architecture-agent.md), [review role](../../../docs/agents/independent-review-agent.md) and [Integration role](../../../docs/agents/integration-agent.md) remain controlling.

## Manual records versus runtime records

A subject-based filename is a manual planning handle, not a fabricated service-assigned packet identity. A later live import must allocate real identities/versions, convert the confirmed registration outcome references, validate the delivered schemas and publish the required runtime records/manifests. No Markdown document claims JSON Schema validity, SQL confirmation or service-owned allocation. Missing runtime references may not be filled from guessed identifiers or current master.

This specification set may be reviewed for its scoped planning content while final non-self-contained milestone QA plans remain blocked. A passing packet-specification review cannot confirm the entire architecture breakdown or authorize implementation. The final full content set must receive the required review coverage and exact Owner confirmation; retain applicable coverage instead of silently treating an earlier partial pass as sufficient.

## Starting context and delivery baseline

For each packet, read its record, these rules, its named specialist role/context, the investigation row for its source area, controlling architecture and mapped outcome sections. The initial source is the pinned baseline. When implementation is separately authorized, the assigned base must include the verified integrated commits of every named prerequisite; save those exact references and the assigned milestone/packet branch. Do not guess a commit before the prerequisite exists.

Before coding, return a concise implementation plan through the service: affected code, necessary connections, checks and blockers. This is not an extra Owner approval gate. A routine implementation choice within the specified boundary belongs to the assigned developer; scope, conflicting architecture or unavailable authority goes to the architect. Missing resources pause only affected work.

## Exact permitted outputs and ownership

The packet's output table is its complete proposed repository write set. Python and SQL outputs have no JSON schema; JSON schema definitions validate the named process formats; TOML/package metadata and deployment files follow their named format. Tests are required functional outputs, not optional documentation. Required files must contain the specified behavior; do not add empty stubs merely to satisfy the list.

No packet may edit `docs/architecture.md`, project declarations, another packet's code, another specialist's context, unlisted package metadata, production data, credentials, historical modules or service-owned runtime records. A necessary additional path goes to the architect for an explicit amendment; it is not silently added. No source deletion or retirement is authorized by these packets. New production entry points must not invoke the historical synthetic wrapper, mechanical approval driver or direct default-branch merge workflow.

Domain persistence is implemented in the listed domain modules using the shared transaction API; foundation owns connection setup and migration orchestration. Each domain module supplies versioned migration definitions for its own records through the installed process registry. It cannot open a second SQLite writer or change another domain's tables. The listed code outputs therefore include their domain record/migration definitions; separate unlisted SQL files are not implicitly authorized. Registry integration tests must prove transactional schema installation, stable ordering and rejection of conflicting migration identities.

Package initializers are allocated once to the first named owner of each area. The installer owns `pyproject.toml`, service/deployment entry points and the resource-copy convention. Other packets do not compete for those files: domain plugin modules declare their installed routes, validators, migrations and bundle resources through the common process registry. The registry loads only application-owned built-in modules, not user-supplied executable paths or arbitrary TOML handlers. Missing later-domain implementations disable those operations explicitly; they cannot masquerade as complete installed capability. Core service readiness and process-specific bundle readiness remain distinct.

## Integration contracts between packets

| Provider | Contract to deliver | Consumer and integration proof |
|---|---|---|
| Service persistence | Service-owned transaction context, canonical identities/versions, ordered domain migration registration and commit-visible outbox | Request/domain handlers commit receipt, effect and event together; failure rolls back all, with no external wait inside a transaction. |
| Durable request delivery | Fixed validated operation registry, verified actor/context, idempotent receipt and lookup, typed HTTP errors | Domain plugins register approved operations and validators; integration tests call actual /api/v1 routes, not a substitute direct mutation. |
| Project/activity records and Event stream | Consistent read snapshot/cursor, linked records, committed SSE and bounded pagination | Terminal and process-specific projections observe the same saved effect. |
| Shared process policy | Installed-domain descriptor for schemas/routes/migrations/policies, immutable config snapshots and resource resolution | Each domain plugin registers its own descriptors. Installation copies referenced local bundle trees at exact installed names; missing/hash-mismatched resource blocks that process. |
| Terminal workspace | Internal extension registration for named commands/views using the authenticated client and projected state | Questions, registration, architecture and Execution own separate extension modules; actual terminal tests prove dispatch/rendering without direct SQL. |
| Agent workspace/transport and Durable supervision | Exact assignment/result contract, constrained paths, durable launch/session identity, cancellation/deadline observations | Domain agents and managers retain semantic validators and budgets; transport cannot approve their results or impersonate Owner. |
| Publication journal | Bound-profile authorization, intended source/target/commit, bounded attempt and read-after-write reconciliation | Registration/architecture publish records; Execution pushes/imports/promotes code under their own eligibility and atomicity rules. |
| QA resource catalog | Read-only non-secret names/settings/permissions, assignment provenance and immutable hash | Architecture validates selections; QA rechecks exact catalog and live authorization. Do not expose credential locators. |
| Pause and graceful stop | Saved lifecycle admission/settlement checks around each irreversible action | Coder dispatch depends on this packet. Every later review/integration/import/QA/promotion stage implements these checks and its own restart reconciliation before live use. |

These are delivery interfaces, not new end-user behavior. Their named record fields, operations, settings and failure semantics remain defined in the pinned architecture. A provider delivers its interface tests using actual provider code and a real minimal caller; consumers add actual call-path tests in their allocated test file. A provider's packet completion does not require a future consumer to exist or claim that consumer is implemented. The assembled milestone proves later connections, as specified in [milestone ordering](development-milestones.md#ordering-and-integration-boundary).

## Execution requirements and parallelism

Each record gives `required_capabilities`, `allowed_locations` and `minimum_context_tokens` using the architecture's literal identifiers. Values are planned requirements, not a route/model selection or evidence that a worker exists. Minimum context is sized for the bounded packet and its relevant excerpts: 32,768 tokens normally and 65,536 for the named multi-contract packets. The service must still verify actual input/output reserve and route capacity; split or clarify a packet that does not fit rather than bypassing the bound.

The Development Manager selects the actual permitted route/model with a reason under the unchanged Qwen-default policy. A listed cloud location does not authorize unconfigured cloud use; a listed approved_network capability does not grant any destination or credential. Tests requiring installed Linux identities, systemd or protected local environments run on the AI box. No work start, time slot, concurrency reservation or fixed worker assignment is specified here.

Two packets may run in parallel only when both have integrated prerequisite contracts, disjoint permitted paths and no conflicting declared runtime resource. Their exact output sets are checked for overlap. Shared runtime test environments require separate run identities/ports/data roots, or serialized use if isolation cannot be established. All packet dependency edges describe code availability, not blanket completion of every mapped project outcome.

## Verification and completion

Use an isolated prepared Python environment with the project installed from the assigned worktree. Environment preparation is supplied by Linux installation; earlier library packet checks can use `PYTHONPATH=services/maestro` and the standard library test runner without installing the whole future product. Commands below are argument arrays or literal non-shell assignments, never arbitrary shell text supplied by a model.

Each packet's exact command runs its allocated `unittest` file through discovery and exits nonzero on failure. Required unavailable external/installed checks must exit nonzero with an explicit UNTESTED result, not silently skip to a green suite. Generated sample inputs and controlled faults are allowed with identified origin; they must not manufacture the saved outcome, reviewer judgment or Git result under verification. Assertions use actual implementation records, API/event outputs, filesystem/Git observations and tool evidence as relevant.

Packet-level checks are coder verification. Milestone QA is separate and exercises the assembled usable outcome. A full-product acceptance harness is not a prerequisite for every early unit/component test. The packet's completion claims require its included behavior and mandatory allocated checks; any missing external evidence is disclosed and prevents the affected completion claim. No mock can satisfy a required actual agent/repository path.

Return the structured coder result with exact base/head, changed paths, implementation plan, command/exit/output evidence, fulfilled criteria, failures, limitations and unfinished work. Test stdout/stderr is captured by the service-assigned evidence channel; do not commit secrets or raw logs to the repository. The wrapper verifies local scope/clean state and the service journals exact remote publication. A separate non-author reviewer assesses the exact revision. Approval means eligible for Integration, never self-authorized merge or project-outcome completion.

The assurance level is proportionate main-journey and essential-failure coverage, not an exhaustive audit. Preserve the existing threat model, resource/retry/review limits and exclusions. Stop/escalate a scope conflict, unavailable authority, stale prerequisite, unsafe target, failed required check or exhausted allowance. Passing a documented check does not strengthen requirements or waive known blockers.

## Open full-breakdown boundary

Operator test-resource catalog and actual access/model configuration are not available here. [QA resource preparation](qa-resources.md) preserves those limits. Milestone sections and [seven manual QA plans](qa-plans/README.md) specify concrete acceptance procedures, not fabricated executable QA bindings. The architect owns routine test/setup design; operator-only provisioning remains separate. A final plan still needs actual selected references, binding provenance, exact setup/support commands, data/source hashes, artifacts and cleanup/reset conditions. This packet set does not clear that boundary.
