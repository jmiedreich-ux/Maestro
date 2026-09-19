# Exact source intake

Specification version: 3. Manual planning record; not a runtime allocation or permission to execute. Read [common packet rules](../packet-rules.md), which are part of this record.

## Outcome and milestone

Purpose: Read explicit overview references at the chosen commit.

Project outcomes: [REG-PM1 — Register and confirm a project through the CLI](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/registration-milestones.md#reg-pm1--register-and-confirm-a-project-through-the-cli).

Development milestone: [Confirmed registration and history](../development-milestones.md#confirmed-registration-and-history). This packet contributes to those outcomes; it does not alone complete their declarations.

## Starting context

Source commit: `182bf4290ef2960d4691a7f41315ebf71d5bf85c`; later assigned base includes exact integrated prerequisite commits under [baseline rules](../packet-rules.md#starting-context-and-delivery-baseline). Read [investigation](../investigation.md#code-direction-findings), [structure](../project-structure.md), [specialist role](../../../../services/maestro/maestro/planning/.maestro/role-planning-processes.md) and [starting context](../../../../services/maestro/maestro/planning/.maestro/context.md).

Controlling behavior: [source and publication selection](../../../architecture.md#source-and-publication-selection).

## Included scope and interfaces

Use the assessed exact Git reader and the service-owned GitHub destination-authorization provider delivered by Publication journal version 2; resolve selected source once, scope/outcome versions, source consistency and missing references.

Provider contract: The publication-owned destination provider returns a non-secret allowed, blocked or unverifiable decision bound to the saved immutable effective profile snapshot, GitHub App, installation, repository, branch and policy observation. The source reader returns exact blob hashes and source inventory only after that decision is allowed. Intake saves the provider evidence and snapshot reference with the attempt and asks only genuinely missing scope, destination and role-selection questions through the service.

Consumer connection: Registration assessment consumes this inventory. Registration confirmation obtains a fresh matching provider result before publication; neither source reading nor publication receives an agent credential.

## Exclusions and stop boundary

Do not implement the work of another packet, change accepted product behavior, delete old modules/data, alter unlisted files or use test results as independent approval. Common exclusions and authority boundaries apply. Stop affected work for a missing prerequisite, schema/behavior conflict, unavailable required resource or unsafe operation; return the concrete issue through the assigned process. Technical failure does not authorize changing scope or resetting a budget.

## Dependencies and safe parallel work

- [Shared process policy](process-policy.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.
- [Publication journal](publication.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.

Independent packets may run in parallel once their own prerequisites hold and their allocated files/resources do not overlap. Do not edit provider files to make a missing contract appear available. [Shared ownership and migration rules](../packet-rules.md#exact-permitted-outputs-and-ownership) apply; all later Execution stages implement lifecycle and recovery integration from first delivery.

## Permitted paths and required outputs

No other repository write is permitted by this record.

| Exact path | Format | Required result |
|---|---|---|
| `services/maestro/maestro/planning/sources.py` | Python | Assigned behavior and integration contract |
| `services/maestro/maestro/planning/intake.py` | Python | Assigned behavior and integration contract |
| `tests/maestro/planning/test_source_intake.py` | Python | Real main-path and essential-failure checks |
| `services/maestro/maestro/planning/__init__.py` | Python | Package boundary and explicit exports |

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

1. Read an explicitly selected overview and its referenced architecture/declarations at a resolved commit, retaining ordered outcome identities/versions and selected scope.
2. Consume the publication-owned provider result and reject missing/inconsistent references, traversal, unauthorized destination or an unavailable, protected or ruleset-bound GitHub destination; moving branch head cannot retarget saved source.
3. Save and preserve the immutable effective-profile snapshot reference and non-secret provider evidence with the attempted source selection; do not replace it with a later configuration value. The included consumer responsibility uses the real module/service boundary and meaningful declared outputs, with no unsupported stub or silent fallback.
4. Mandatory checks below produce actual passing evidence for included behavior; disclose missing evidence as UNTESTED. Submit the exact scoped result for independent review under the common completion rules.

## Verification and essential failures

Preparation: isolated Python environment at the assigned base; `PYTHONPATH=services/maestro` for source-tree checks. Installed/external resources must come from the approved setup; do not install/provision or broaden access implicitly.

Exact test command:

```json
["python","-m","unittest","discover","-s","tests/maestro/planning","-p","test_source_intake.py","-v"]
```

Required assertions: completion criteria 1 and 2, plus this essential rejection/recovery boundary: Missing path, contradictory source, moving branch, unauthorized destination, unavailable App permission or branch policy cannot silently change baseline. Packet checks use a controlled provider fixture for parsing/failure behavior; the M3 Quality Assurance plan must prove the real bound GitHub App route.

The test file must observe the real included capability. Low-level deterministic inputs may isolate component logic; any actual service/agent/Git path promised by these criteria requires real path evidence, not a fake result. Missing installed resources are recorded as UNTESTED with nonzero status; do not convert them into success using a skip. Capture actual inputs, expected/observed results, command/exit output and source revision. No tests were run when writing this specification.

## Handoff

Return the saved implementation plan, exact base/local head, changed-path list, checks and their observed results, evidence references, limitations and unresolved work to the Development Manager. Service wrapper/remote verification and a non-author review follow. This file grants no integration, promotion, Owner confirmation or Execution-start authority.
