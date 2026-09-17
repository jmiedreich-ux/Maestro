# Milestone QA plans

Version 1. Manual planning specifications for the seven [development milestones](../development-milestones.md). These plans describe the checks to perform on each assembled milestone. They record no test run, installed resource, passing result or runtime QA-plan identity.

## Plans and timing

| Assembled development milestone | QA plan |
|---|---|
| Connected service and workspace | [Service and workspace](service-workspace.md) |
| Supervised shared processes | [Supervised processes](supervised-processes.md) |
| Confirmed registration and history | [Registration and history](registration-history.md) |
| Confirmed development planning | [Development planning](development-planning.md) |
| Independently reviewed packet delivery | [Packet delivery](packet-delivery.md) |
| Integrated code and dependency delivery | [Integration and dependencies](integration-dependencies.md) |
| Verified milestone completion | [Milestone completion](milestone-completion.md) |

Run the applicable QA plan only after that milestone's required packets are implemented, independently reviewed and integrated at an exact milestone-branch candidate, with its dependencies satisfied. “Completed milestone” here means ready for assembled testing, not already accepted or promoted. Packet developer checks and independent code review remain distinct. QA supplies observed evidence; independent whole-milestone review supplies outcome/gap judgment. Both existing gates precede promotion. QA creates no extra approval cycle.

The accepted manual registration is candidate version 1 at `4953aa555b9e5da5b73407f62184c7905efb7898`; implementation/behavior baseline remains `182bf4290ef2960d4691a7f41315ebf71d5bf85c`. These plans extend the packet publication at `46748c05f4a807c21fd202afea1829153377fe01`. At execution time record the exact integrated candidate and prerequisite revisions; do not test a moving branch head or substitute today's master.

## Authority and setup assumptions

The architect owns test design, routine technical choices, traceability, setup requirements and tooling specifications. The operator alone provisions protected resources/credentials and confirms actual availability. The Owner need not design tests or assemble a catalog in order for this manual drafting to proceed. No resource creation, purchase, installation, network widening, credential extraction or destructive operation is authorized by writing these plans.

Use an isolated Linux test environment on the AI box, a separate test service account/data root and Owner credential, and the already selected repository name `jmiedreich-ux/Maestro-qa`. These are requirements/assumptions, not verified availability. Test repository visibility, access/profile, host isolation, supported exact tools/models, environment/secret/network catalog names and installed paths remain unknown. Never infer public visibility, create a repository or test against Maestro product master.

[Project QA bindings](../../../architecture.md#project-quality-assurance-bindings) remains controlling: before runtime plan publication/confirmation the service must supply the validated non-secret catalog and snapshot hash; selections must be authorized test bindings. The manual runbooks here may be prepared with explicit assumptions, but are not catalog-bound executable records. This distinction does not defer the runtime binding gate until after confirmation or waive it before testing.

## Resource resolution and responsibility

| Requirement | Selection, saved evidence and validation | Consumer |
|---|---|---|
| Linux test environment | Architect states isolation needs; authorized operator provisions/identifies actual test environment; service collects catalog before runtime-plan drafting, validates test classification, records provenance/hash. Architect then selects exact environment names. | Every setup/support entry names a selected environment. |
| Test Owner access | Operator-approved setup creates a separate test credential; service stores/resolves it privately. Record only public secret name and non-secret version identity. Check missing/invalid credential rejection without logging values. | Test CLI and authorized requests only; never agents. |
| Repository access | Use selected QA repository only; operator supplies authorized test profile and branches. Service verifies authorization and snapshot; architect selects permitted secret/network names from catalog. | Real source reads, publication, integration and test-project promotion. |
| Tools/models | For Registration/Architecture, collect architect and reviewer selections separately through actual intake; service validates and saves both before launch. For Execution collect permitted manager selection; manager selects coder with reason under Qwen-default policy. Exact model/adapter evidence is required, not “latest.” | Real assignments, independent reviews and supervision checks. |
| Network | Deny outbound by default. Exact host/protocol/ports and receiving environment must be provided and authorized; no guessed provider hosts or wildcard allowance. | Only named product/support processes. |
| Candidate, plan and scripts | QA coordinator reads exact integrated candidate and versioned plan; records commit and SHA-256 of plan, config, setup/data scripts and inputs before running. Missing script is a setup dependency, not permission to improvise it. | Setup, checks and evidence correlation. |

No plan is self-contained merely because its reference lists are unresolved. Do not replace unknown resource selections with empty lists/null binding hash to obtain validation. The exception for genuinely self-contained plans in the architecture remains unchanged.

## Common setup sequence

1. Verify the milestone is eligible, the candidate is immutable for the run, all required packet reviews/integrations are current and prerequisite evidence is valid. Capture starting remote refs without modifying them.
2. Resolve approved test resources and permissions. Recheck current authorization before each use. A changed binding requires the existing plan amendment/review/confirmation process; restoration of the exact binding permits affected checks.
3. Allocate a run identity and isolated working/data roots. Record ownership, available space and distinct service/agent identities. Protect the operator's normal service, credentials, processes and repository.
4. Install the exact candidate using the instructions delivered by [Linux installation](../work-packets/install.md). Record the actual versioned installer command array, interpreter, hash and configuration; unsupported flags or guessed commands are prohibited. Missing documented isolated installation is a tooling blocker.
5. Start only required services. Systemd status/logs establish service health; authenticated API read establishes connected readiness. Do not invent a new health endpoint. Use the architecture's configured loopback address inside the isolated environment. If sharing a host requires a different supported address, reserve an authorized free loopback port and record it; never kill an unrelated listener or silently alter the product default.
6. Prepare the specific input data below, recording origin and hashes. Supply inputs through the real CLI/API/repository path, never by inserting expected result/approval/confirmation rows into SQL.
7. Run the milestone's checks against those same candidate/resources. Record expected and observed results and essential failure/recovery behavior. Freeze or invalidate affected evidence if the candidate changes.

## Support processes and bootstrap boundary

| Process | Required health, ownership and port rule | Shutdown |
|---|---|---|
| Installed Maestro test service | Expected test identity, installed revision, systemd state and startup diagnostics; actual authenticated read where supported. Use isolated loopback namespace/default configured port or explicitly authorized reserved port. | Stop only the recorded run-owned service after evidence capture; verify no surviving child. |
| Actual tool/model service | Required from Supervised shared processes onward; verify supported executable/model identity and configured readiness. Use its approved configured endpoint; reserve a distinct endpoint when isolation is needed. Never restart a shared model service without authority. | Stop only run-owned tool processes; shared providers remain untouched. |
| QA runner and artifact service | Required as product capabilities in Verified milestone completion; use confirmed binding/environment identity, explicit health and service-owned evidence handles. | Reconcile active checks/capture before stop, then cleanup/reset/quarantine. |
| GitHub test repository | External dependency, not a local support daemon. Verify exact repository/profile/ref permissions through authorized access; no local port or startup command applies. | Retain run-owned evidence refs unless a separate approved retention/cleanup policy permits removal. |

Before Maestro's own QA automation exists, these are manual **acceptance procedure specifications**, not permission to operate an alternate controller or simulate runtime records. A separately authorized bootstrap execution arrangement must provide the actual isolation, observation, approved setup tools and external evidence retention. Its exact commands/hashes and authority must be bound before a run; this document does not invent that arrangement. Early milestones do not depend on the last milestone's acceptance harness for their manual checks. If no authorized setup/driver exists, the affected check is UNTESTED and the milestone cannot pass. This is a recorded implementation/setup dependency, not a request for the Owner to design the QA.

Existing packet owners remain: Linux installation supplies install/start/stop instructions; each domain packet supplies its real public entry point and bounded verification; [Connected acceptance tooling](../work-packets/acceptance-tooling.md) later automates these assembled journeys; [Isolated QA setup](../work-packets/qa-environment.md), [QA data and check runner](../work-packets/qa-checks.md) and [Durable QA artifacts](../work-packets/qa-artifacts.md) deliver the runtime facilities. No new code path or packet write permission is assigned here. If fulfilling setup needs an extra output, amend its packet explicitly before implementation.

## Data rules

All test documents/projects are synthetic **inputs**, clearly labeled test-only and containing no personal or production data. Capture generator identity/version/hash or exact authored input file hashes, seed/parameters, source classification, sanitization (not needed for wholly generated input, with reason), setup operation, real entry path, expected result and cleanup ownership. A generator may create source documents/code; it cannot create Maestro registration packages, reviews, confirmations, QA results or completion records.

Use separate run-owned projects/branches for scenarios that need a clean state. Controlled faults target the actual isolated process/network/publication boundary; record what was interrupted and why. Do not manufacture agent/model output or edit internal counters to make a limit check appear real. A short explicitly configured test deadline may exercise actual timeout handling; save that config and its difference from normal defaults.

## Evidence and results

Every check records: subject; candidate commit; plan version/hash; exact setup/input/tool/config/catalog references; actor/assignment/run/request identities as applicable; expected/observed result; start/finish; PASS, FAIL or UNTESTED; limitations; and evidence references. Capture CLI observation plus actual underlying service/API/events, process or remote Git evidence as appropriate. Read-only database inspection may corroborate service writes; it may never supply them. Secrets are redacted before capture; never place credentials in command arguments, prompts or committed logs.

Required evidence includes run manifest, setup/health/port observations, data lineage, each check's result, actual agent/reviewer identity where used, remote Git references where used, failure/recovery observations and cleanup/reset status. Each artifact has identity, path, SHA-256, size and media type. Automatic QA uses the architecture's service-owned artifact store and configured retention; a manually authorized bootstrap run must retain equivalent external evidence without pretending it has service-assigned SQL identities. Missing required evidence is UNTESTED, not a pass.

PASS requires every required check for this contribution to pass on the exact candidate, with no missing required path or artifact. An observed defect is FAIL; unavailable prerequisites or bypassed/unobservable paths are UNTESTED. A setup blocker is not itself a product defect. Either prevents QA acceptance and promotion. A failed check follows the existing architect/Integration/correction route; rerun affected checks and dependencies, retain valid unaffected evidence and existing allowances. QA does not approve code or add an Owner approval gate.

## Cleanup and reset

Capture and verify durable evidence first. Reconcile pending writes, stop recorded run-owned processes, confirm termination, revoke/release only run-created test credentials through the authorized operator/service mechanism, and release owned port reservations. Remove disposable local inputs/data only within the exact validated run root and under approved cleanup authority. Never use a broad directory, production database, product branch or whole repository as a cleanup target.

Remote branches/commits containing evidence are retained by default; repository-name selection grants no deletion permission. Record any deferred cleanup and its owner. Do not erase failed-run evidence to make a rerun look clean. Required artifacts remain until Execution closure plus configured retention in automatic QA; bootstrap retention must be explicitly authorized and at least preserve all open acceptance evidence until its disposition.

Reset check: no owned process remains, no run port is held, no transient credential is usable, isolated disposable data is removed or quarantined, remote/evidence refs match the retained manifest and a new run cannot read prior transient data. Failed shutdown, cleanup or reset quarantines the environment and blocks reuse without rewriting the recorded QA result.

## Runtime binding checklist

The architect/implementation team completes these technical steps; the Owner is asked only for a missing reserved choice, permission or inaccessible resource:

- Bind each milestone and QA plan to actual allocated identities/versions and exact published references.
- Resolve actual catalog names into `environment_refs`, `secret_refs`, `allowed_network_dependencies` and the exact `project_binding_hash`; bind each setup/support operation to its selected environment.
- Replace manual setup/check descriptions with approved versioned script references/hashes or exact argument arrays, including support health/port rules and actual data generator/input hashes. These scripts are not written by this documentation change.
- Validate the producer schema/inventory, acquire the applicable full-content review coverage and exact Owner confirmation before using the plans as runtime inputs; recheck current resource authorization before setup/use.

This checklist records genuine unresolved binding/tooling work. It is not evidence that the full architecture breakdown is ready for confirmation and does not reopen the already settled QA repository name.
