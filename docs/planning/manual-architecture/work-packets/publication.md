# Publication journal

Specification version: 2. Manual planning record; not a runtime allocation or permission to execute. Read [common packet rules](../packet-rules.md), which are part of this record.

## Outcome and milestone

Purpose: Publish exact output through service-owned credentials.

Project outcomes: [REG-PM1 — Register and confirm a project through the CLI](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm1--register-and-confirm-a-project-through-the-cli); [REG-PM3 — Recover registration without losing decisions or exceeding limits](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm3--recover-registration-without-losing-decisions-or-exceeding-limits); [SVC-PM2 — Preserve project activity and requests](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm2--preserve-project-activity-and-requests).

Development milestone: [Confirmed registration and history](../development-milestones.md#confirmed-registration-and-history). This packet contributes to those outcomes; it does not alone complete their declarations.

## Starting context

Source commit: `182bf4290ef2960d4691a7f41315ebf71d5bf85c`; later assigned base includes exact integrated prerequisite commits under [baseline rules](../packet-rules.md#starting-context-and-delivery-baseline). Read [investigation](../investigation.md#code-direction-findings), [structure](../project-structure.md), [specialist role](../../../../services/maestro/maestro/foundation/.maestro/role-runtime-foundations.md) and [starting context](../../../../services/maestro/maestro/foundation/.maestro/context.md).

Controlling behavior: [candidate publication](../../../architecture.md#candidate-publication).

## Included scope and interfaces

Add executable authorized GitHub App repository profiles, service-only installation-token exchange, exact destination-policy evaluation, bounded Git calls, expected-parent journal, exact remote byte verification and uncertain-write reconciliation.

Provider contract: Foundation exposes a GitHub destination-authorization provider and publication-journal prepare, attempt, observe and reconcile operations. The provider validates the typed configured profile, mints the service-only installation token and returns non-secret allowed, blocked or unverifiable evidence. The journal accepts a fresh matching allowed result only; callers control eligibility and post-publication domain activation.

Consumer connection: Source intake consumes the provider before reading. Registration confirmation obtains a fresh matching result immediately before it invokes the journal write. Registration and architecture publication and Execution pushes/imports/promotions use the same journal primitive but retain separate policy.

## Exclusions and stop boundary

Do not implement the work of another packet, change accepted product behavior, delete old modules/data, alter unlisted files or use test results as independent approval. Common exclusions and authority boundaries apply. Stop affected work for a missing prerequisite, schema/behavior conflict, unavailable required resource or unsafe operation; return the concrete issue through the assigned process. Technical failure does not authorize changing scope or resetting a budget.

## Dependencies and safe parallel work

- [Service persistence](store.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.
- [Owner authentication](owner-auth.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.

Independent packets may run in parallel once their own prerequisites hold and their allocated files/resources do not overlap. Do not edit provider files to make a missing contract appear available. [Shared ownership and migration rules](../packet-rules.md#exact-permitted-outputs-and-ownership) apply; all later Execution stages implement lifecycle and recovery integration from first delivery.

## Permitted paths and required outputs

No other repository write is permitted by this record.

| Exact path | Format | Required result |
|---|---|---|
| `services/maestro/maestro/foundation/git_read.py` | Python | Assigned behavior and integration contract |
| `services/maestro/maestro/foundation/git_publication.py` | Python | Assigned behavior and integration contract |
| `services/maestro/maestro/foundation/github_destination.py` | Python | Typed service-owned GitHub App destination-authorization provider |
| `tests/maestro/foundation/test_publication.py` | Python | Real journal main-path and essential-failure checks |
| `tests/maestro/foundation/test_github_destination.py` | Python | Provider main-path and essential-failure checks |
| `services/maestro/maestro/foundation/credentials.py` | Python | Service-only App private-key and installation-token handling |

Non-JSON deliverables use schema reference null. JSON process schemas implement the named architecture definitions and installation mapping, not a private alternate format. No optional hidden output or broad directory permission is inferred.

## Execution requirements

```json
{
  "required_capabilities": [
    "code_edit",
    "local_command",
    "repository_search",
    "approved_network"
  ],
  "allowed_locations": [
    "local_ai_box",
    "cloud"
  ],
  "minimum_context_tokens": 32768
}
```

Actual installed route/model, permissions, credentials and workspace identity are collected and checked by the service at assignment; none is selected here. A network capability still requires explicit permitted destinations. Any host-specific integration check uses the approved Linux test environment; a cloud coding route does not substitute a different product platform.

## Completion criteria

1. Validate the typed GitHub App profile; save the immutable non-secret effective-profile snapshot, expected parent and intended content/tree/commit; create the installation token only inside the service and verify the exact App, installation, repository, branch, contents-write and Administration-read permissions and branch/ruleset policy.
2. Permit source read or remote publication only for a fresh matching allowed result on an unprotected branch with no active repository or organization ruleset. Immediately before every journal remote write, reject a stale, changed, blocked or unverifiable result; access or policy denial creates no success receipt or write.
3. Simulate lost acknowledgment and remote movement; read/reconcile before retry, never force-push or silently overwrite.
3. The included provider/consumer responsibilities use the real module/service boundary and meaningful declared outputs, with no unsupported stub or silent fallback. A provider demonstrates its boundary with a real minimal caller; later consumer implementation and assembled acceptance follow the common integration rules.
4. Mandatory checks below produce actual passing evidence for included behavior; disclose missing evidence as UNTESTED. Submit the exact scoped result for independent review under the common completion rules.

## Verification and essential failures

Preparation: isolated Python environment at the assigned base; `PYTHONPATH=services/maestro` for source-tree checks. Installed/external resources must come from the approved setup; do not install/provision or broaden access implicitly.

Exact test command:

```json
["python","-m","unittest","discover","-s","tests/maestro/foundation","-p","test_publication.py","-v"]
```

Required assertions: completion criteria 1 and 2, plus this essential rejection/recovery boundary: Denied access/moved head/lost response reconciles before retry; no local-only success.

The test file must observe the real included capability. Low-level deterministic inputs may isolate component logic; any actual service/agent/Git path promised by these criteria requires real path evidence, not a fake result. Missing installed resources are recorded as UNTESTED with nonzero status; do not convert them into success using a skip. Capture actual inputs, expected/observed results, command/exit output and source revision. No tests were run when writing this specification.

## Handoff

Return the saved implementation plan, exact base/local head, changed-path list, checks and their observed results, evidence references, limitations and unresolved work to the Development Manager. Service wrapper/remote verification and a non-author review follow. This file grants no integration, promotion, Owner confirmation or Execution-start authority.
