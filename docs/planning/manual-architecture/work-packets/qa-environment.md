# Isolated QA setup

Specification version: 1. Manual planning record; not a runtime allocation or permission to execute. Read [common packet rules](../packet-rules.md), which are part of this record.

## Outcome and milestone

Purpose: Run declared setup and support processes in isolated test environments.

Project outcomes: [EXE-PM4 — Verify milestones and publish completed Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm4--verify-milestones-and-publish-completed-execution).

Development milestone: [Verified milestone completion](../development-milestones.md#verified-milestone-completion). This packet contributes to those outcomes; it does not alone complete their declarations.

## Starting context

Source commit: `182bf4290ef2960d4691a7f41315ebf71d5bf85c`; later assigned base includes exact integrated prerequisite commits under [baseline rules](../packet-rules.md#starting-context-and-delivery-baseline). Read [investigation](../investigation.md#code-direction-findings), [structure](../project-structure.md), [specialist role](../../../../services/maestro/maestro/quality/.maestro/role-milestone-quality.md) and [starting context](../../../../services/maestro/maestro/quality/.maestro/context.md).

Controlling behavior: [isolated quality assurance environment](../../../architecture.md#isolated-quality-assurance-environment).

## Included scope and interfaces

Implement catalog-bound setup argument arrays/script hashes, test identities/storage, health/port conditions, authorized network and reset/quarantine.

Provider contract: Environment supervisor enforces allowed injection/network, run identity and exact script source; it resolves secrets only into receiving processes.

Consumer connection: Runner uses this environment; artifact store persists evidence outside transient run workspace.

## Exclusions and stop boundary

Do not implement the work of another packet, change accepted product behavior, delete old modules/data, alter unlisted files or use test results as independent approval. Common exclusions and authority boundaries apply. Stop affected work for a missing prerequisite, schema/behavior conflict, unavailable required resource or unsafe operation; return the concrete issue through the assigned process. Technical failure does not authorize changing scope or resetting a budget.

## Dependencies and safe parallel work

- [QA resource catalog](qa-catalog.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.
- [Durable supervision](supervision.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.

Independent packets may run in parallel once their own prerequisites hold and their allocated files/resources do not overlap. Do not edit provider files to make a missing contract appear available. [Shared ownership and migration rules](../packet-rules.md#exact-permitted-outputs-and-ownership) apply; all later Execution stages implement lifecycle and recovery integration from first delivery.

## Permitted paths and required outputs

No other repository write is permitted by this record.

| Exact path | Format | Required result |
|---|---|---|
| `services/maestro/maestro/quality/environment.py` | Python | Assigned behavior and integration contract |
| `services/maestro/maestro/quality/support.py` | Python | Assigned behavior and integration contract |
| `tests/maestro/quality/test_qa_environment.py` | Python | Real main-path and essential-failure checks |

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
    "local_ai_box"
  ],
  "minimum_context_tokens": 32768
}
```

Actual installed route/model, permissions, credentials and workspace identity are collected and checked by the service at assignment; none is selected here. A network capability still requires explicit permitted destinations. Installed Linux/systemd or protected local supervision is required for this packet's assigned verification.

## Completion criteria

1. Create isolated run environment from exact confirmed plan/catalog, execute argument arrays or hashed scripts, start/health-check support processes and capture identities/ports.
2. Revoked binding or production setting blocks setup; failed stop/cleanup/reset quarantines environment without changing prior QA result.
3. The included provider/consumer responsibilities use the real module/service boundary and meaningful declared outputs, with no unsupported stub or silent fallback. A provider demonstrates its boundary with a real minimal caller; later consumer implementation and assembled acceptance follow the common integration rules.
4. Mandatory checks below produce actual passing evidence for included behavior; disclose missing evidence as UNTESTED. Submit the exact scoped result for independent review under the common completion rules.

## Verification and essential failures

Preparation: isolated Python environment at the assigned base; `PYTHONPATH=services/maestro` for source-tree checks. Installed/external resources must come from the approved setup; do not install/provision or broaden access implicitly.

Exact test command:

```json
["python","-m","unittest","discover","-s","tests/maestro/quality","-p","test_qa_environment.py","-v"]
```

Required assertions: completion criteria 1 and 2, plus this essential rejection/recovery boundary: Changed/revoked binding, missing tool or failed cleanup blocks reuse; no production substitution.

The test file must observe the real included capability. Low-level deterministic inputs may isolate component logic; any actual service/agent/Git path promised by these criteria requires real path evidence, not a fake result. Missing installed resources are recorded as UNTESTED with nonzero status; do not convert them into success using a skip. Capture actual inputs, expected/observed results, command/exit output and source revision. No tests were run when writing this specification.

## Handoff

Return the saved implementation plan, exact base/local head, changed-path list, checks and their observed results, evidence references, limitations and unresolved work to the Development Manager. Service wrapper/remote verification and a non-author review follow. This file grants no integration, promotion, Owner confirmation or Execution-start authority.
