# Service persistence

Specification version: 1. Manual planning record; not a runtime allocation or permission to execute. Read [common packet rules](../packet-rules.md), which are part of this record.

## Outcome and milestone

Purpose: Deliver configured SQLite storage and atomic service writes.

Project outcomes: [SVC-PM1 — Operate the persistent Maestro service](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm1--operate-the-persistent-maestro-service); [SVC-PM2 — Preserve project activity and requests](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm2--preserve-project-activity-and-requests).

Development milestone: [Connected service and workspace](../development-milestones.md#connected-service-and-workspace). This packet contributes to those outcomes; it does not alone complete their declarations.

## Starting context

Source commit: `182bf4290ef2960d4691a7f41315ebf71d5bf85c`; later assigned base includes exact integrated prerequisite commits under [baseline rules](../packet-rules.md#starting-context-and-delivery-baseline). Read [investigation](../investigation.md#code-direction-findings), [structure](../project-structure.md), [specialist role](../../../../services/maestro/maestro/foundation/.maestro/role-runtime-foundations.md) and [starting context](../../../../services/maestro/maestro/foundation/.maestro/context.md).

Controlling behavior: [sqlite storage](../../../architecture.md#sqlite-storage).

## Included scope and interfaces

Reuse assessed transaction/path techniques; add validated installed settings, WAL/FULL, migrations, receipts and event records without opening agent/CLI writers.

Provider contract: foundation/database.py exports a transaction boundary and domain migration registration; service/domain callers use it rather than connecting directly.

Consumer connection: service/requests.py and all process domain repositories consume the same transaction object, canonical record helpers and version checks.

## Exclusions and stop boundary

Do not implement the work of another packet, change accepted product behavior, delete old modules/data, alter unlisted files or use test results as independent approval. Common exclusions and authority boundaries apply. Stop affected work for a missing prerequisite, schema/behavior conflict, unavailable required resource or unsafe operation; return the concrete issue through the assigned process. Technical failure does not authorize changing scope or resetting a budget.

## Dependencies and safe parallel work

No prior packet is required; use the pinned source and governing contracts.

Independent packets may run in parallel once their own prerequisites hold and their allocated files/resources do not overlap. Do not edit provider files to make a missing contract appear available. [Shared ownership and migration rules](../packet-rules.md#exact-permitted-outputs-and-ownership) apply; all later Execution stages implement lifecycle and recovery integration from first delivery.

## Permitted paths and required outputs

No other repository write is permitted by this record.

| Exact path | Format | Required result |
|---|---|---|
| `services/maestro/maestro/foundation/database.py` | Python | Assigned behavior and integration contract |
| `services/maestro/maestro/foundation/settings.py` | Python | Assigned behavior and integration contract |
| `tests/maestro/foundation/test_store.py` | Python | Real main-path and essential-failure checks |
| `services/maestro/maestro/foundation/__init__.py` | Python | Package boundary and explicit exports |
| `services/maestro/maestro/foundation/contracts.py` | Python | Assigned behavior and integration contract |

Non-JSON deliverables use schema reference null. JSON process schemas implement the named architecture definitions and installation mapping, not a private alternate format. No optional hidden output or broad directory permission is inferred.

## Execution requirements

```json
{
  "required_capabilities": [
    "code_edit",
    "local_command",
    "repository_search"
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

1. A validated local storage configuration opens one service-owned database; a command saves its request, domain effect and outbox event in one transaction. Reopen observes the committed effect. A failed transaction leaves all three absent.
2. Exercise two competing writers on the same expected version: exactly one transition applies; the other observes a conflict. Assert WAL, FULL synchronous writes and foreign keys on actual connections. No in-memory fallback.
3. The included provider/consumer responsibilities use the real module/service boundary and meaningful declared outputs, with no unsupported stub or silent fallback. A provider demonstrates its boundary with a real minimal caller; later consumer implementation and assembled acceptance follow the common integration rules.
4. Mandatory checks below produce actual passing evidence for included behavior; disclose missing evidence as UNTESTED. Submit the exact scoped result for independent review under the common completion rules.

## Verification and essential failures

Preparation: isolated Python environment at the assigned base; `PYTHONPATH=services/maestro` for source-tree checks. Installed/external resources must come from the approved setup; do not install/provision or broaden access implicitly.

Exact test command:

```json
["python","-m","unittest","discover","-s","tests/maestro/foundation","-p","test_store.py","-v"]
```

Required assertions: completion criteria 1 and 2, plus this essential rejection/recovery boundary: Reject invalid or unsupported storage without replacement; rollback an interrupted transition and publish no event.

The test file must observe the real included capability. Low-level deterministic inputs may isolate component logic; any actual service/agent/Git path promised by these criteria requires real path evidence, not a fake result. Missing installed resources are recorded as UNTESTED with nonzero status; do not convert them into success using a skip. Capture actual inputs, expected/observed results, command/exit output and source revision. No tests were run when writing this specification.

## Handoff

Return the saved implementation plan, exact base/local head, changed-path list, checks and their observed results, evidence references, limitations and unresolved work to the Development Manager. Service wrapper/remote verification and a non-author review follow. This file grants no integration, promotion, Owner confirmation or Execution-start authority.
