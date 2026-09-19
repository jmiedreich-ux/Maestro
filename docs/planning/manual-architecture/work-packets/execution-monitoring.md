# Lifecycle monitoring

Specification version: 1. Manual planning record; not a runtime allocation or permission to execute. Read [common packet rules](../packet-rules.md), which are part of this record.

## Outcome and milestone

Purpose: Show saved Execution state and available actions.

Project outcomes: [EXE-PM1 — Deliver independently reviewed work packets](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm1--deliver-independently-reviewed-work-packets); [EXE-PM5 — Pause, stop and recover Execution](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/execution-milestones.md#exe-pm5--pause-stop-and-recover-execution).

Development milestone: [Independently reviewed packet delivery](../development-milestones.md#independently-reviewed-packet-delivery). This packet contributes to those outcomes; it does not alone complete their declarations.

## Starting context

Source commit: `182bf4290ef2960d4691a7f41315ebf71d5bf85c`; later assigned base includes exact integrated prerequisite commits under [baseline rules](../packet-rules.md#starting-context-and-delivery-baseline). Read [investigation](../investigation.md#code-direction-findings), [structure](../project-structure.md), [specialist role](../../../../services/maestro/maestro/terminal/.maestro/role-terminal-workspace.md) and [starting context](../../../../services/maestro/maestro/terminal/.maestro/context.md).

Controlling behavior: [execution api state and record contract](../../../architecture.md#execution-api-state-and-record-contract).

## Included scope and interfaces

Add manager plans, review/queue/dependency/QA/gap/promotion/lifecycle views and commands from current service records. Show packet, milestone and activity timing by queue, preflight, active work, waiting, review, integration, Quality Assurance, correction, blocked and wall time; show operation counts, cause-classified correction measures and available provider usage. Parallel child time remains distinct from wall time.

Provider contract: Terminal Execution extension uses workspace and authenticated service contract, with no direct SQL or process transition logic.

Consumer connection: Each later stage adds projection data through service-owned events; stage tests verify the corresponding rendered view.

## Exclusions and stop boundary

Do not implement the work of another packet, change accepted product behavior, delete old modules/data, alter unlisted files or use test results as independent approval. Common exclusions and authority boundaries apply. Stop affected work for a missing prerequisite, schema/behavior conflict, unavailable required resource or unsafe operation; return the concrete issue through the assigned process. Technical failure does not authorize changing scope or resetting a budget.

## Dependencies and safe parallel work

- [Execution contracts and start](execution-start.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.
- [Terminal workspace](terminal-workspace.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.

Independent packets may run in parallel once their own prerequisites hold and their allocated files/resources do not overlap. Do not edit provider files to make a missing contract appear available. [Shared ownership and migration rules](../packet-rules.md#exact-permitted-outputs-and-ownership) apply; all later Execution stages implement lifecycle and recovery integration from first delivery.

## Permitted paths and required outputs

No other repository write is permitted by this record.

| Exact path | Format | Required result |
|---|---|---|
| `services/maestro/maestro/terminal/execution_views.py` | Python | Assigned behavior and integration contract |
| `tests/maestro/terminal/test_execution_monitoring.py` | Python | Real main-path and essential-failure checks |

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

1. Render real saved plans, assignments, reviews, FIFO/dependencies, QA/gaps/promotion/lifecycle and submit only available Execution commands.
2. Render saved lifecycle timing, operation counts, first-pass approval rate, specification-sufficiency rate, blocking-finding cause distribution and available provider usage for each packet, milestone and activity. Show parallel child totals separately from wall time. Unknown, stale and unobserved values show their recorded reason and never appear as zero or an estimate.
3. Reconnect reads/reconciles receipts without replay; stale/unknown measurements remain visible, and denied action is not success.
4. The included provider/consumer responsibilities use the real module/service boundary and meaningful declared outputs, with no unsupported stub or silent fallback. A provider demonstrates its boundary with a real minimal caller; later consumer implementation and assembled acceptance follow the common integration rules.
5. Mandatory checks below produce actual passing evidence for included behavior; disclose missing evidence as UNTESTED. Submit the exact scoped result for independent review under the common completion rules.

## Verification and essential failures

Preparation: isolated Python environment at the assigned base; `PYTHONPATH=services/maestro` for source-tree checks. Installed/external resources must come from the approved setup; do not install/provision or broaden access implicitly.

Exact test command:

```json
["python","-m","unittest","discover","-s","tests/maestro/terminal","-p","test_execution_monitoring.py","-v"]
```

Required assertions: completion criteria 1 through 3, plus this essential rejection/recovery boundary: Reconnect is read/reconcile; no replay; stale, unavailable or unobserved readings remain explicit. A report must not turn missing active-time evidence into zero or a commit-time estimate.

The test file must observe the real included capability. Low-level deterministic inputs may isolate component logic; any actual service/agent/Git path promised by these criteria requires real path evidence, not a fake result. Missing installed resources are recorded as UNTESTED with nonzero status; do not convert them into success using a skip. Capture actual inputs, expected/observed results, command/exit output and source revision. No tests were run when writing this specification.

## Handoff

Return the saved implementation plan, exact base/local head, changed-path list, checks and their observed results, evidence references, limitations and unresolved work to the Development Manager. Service wrapper/remote verification and a non-author review follow. This file grants no integration, promotion, Owner confirmation or Execution-start authority.
