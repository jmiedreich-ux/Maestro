# Linked questions

Specification version: 1. Manual planning record; not a runtime allocation or permission to execute. Read [common packet rules](../packet-rules.md), which are part of this record.

## Outcome and milestone

Purpose: Record and route real questions and answers.

Project outcomes: [CLI-PM2 — Reliable project questions and answers](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/cli-milestones.md#cli-pm2--reliable-project-questions-and-answers); [SVC-PM2 — Preserve project activity and requests](https://github.com/jmiedreich-ux/Maestro/blob/182bf4290ef2960d4691a7f41315ebf71d5bf85c/docs/milestones/runtime-service-milestones.md#svc-pm2--preserve-project-activity-and-requests).

Development milestone: [Connected service and workspace](../development-milestones.md#connected-service-and-workspace). This packet contributes to those outcomes; it does not alone complete their declarations.

## Starting context

Source commit: `182bf4290ef2960d4691a7f41315ebf71d5bf85c`; later assigned base includes exact integrated prerequisite commits under [baseline rules](../packet-rules.md#starting-context-and-delivery-baseline). Read [investigation](../investigation.md#code-direction-findings), [structure](../project-structure.md), [specialist role](../../../../services/maestro/maestro/service/.maestro/role-service-and-transport.md) and [starting context](../../../../services/maestro/maestro/service/.maestro/context.md).

Controlling behavior: [questions and answers](../../../architecture.md#questions-and-answers).

## Included scope and interfaces

Implement saved questions, selectable suggestions/free answers, linking, follow-ups and recipient delivery; terminal rendering in a separately owned extension.

Provider contract: Question service owns correlation/version and recipient delivery; a terminal questions extension owns answer interaction.

Consumer connection: Agent transport and each process supply recipient handlers; integration tests use them when delivered, not prefilled answer rows.

## Exclusions and stop boundary

Do not implement the work of another packet, change accepted product behavior, delete old modules/data, alter unlisted files or use test results as independent approval. Owner-approved execution amendment: the terminal provider contract may be minimally extended only in `services/maestro/maestro/terminal/extensions.py` and `services/maestro/maestro/terminal/workspace.py` so this extension receives real ordinary-answer submission and choice identity; no renderer redesign or unrelated terminal change is permitted. Common exclusions and authority boundaries apply. Stop affected work for a missing prerequisite, schema/behavior conflict, unavailable required resource or unsafe operation; return the concrete issue through the assigned process. Technical failure does not authorize changing scope or resetting a budget.

## Dependencies and safe parallel work

- [Project and activity records](activities.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.
- [Terminal workspace](terminal-workspace.md): its listed provider contract must be integrated at an exact recorded commit before this packet uses it.

Independent packets may run in parallel once their own prerequisites hold and their allocated files/resources do not overlap. Do not edit provider files to make a missing contract appear available. [Shared ownership and migration rules](../packet-rules.md#exact-permitted-outputs-and-ownership) apply; all later Execution stages implement lifecycle and recovery integration from first delivery.

## Permitted paths and required outputs

No other repository write is permitted by this record.

| Exact path | Format | Required result |
|---|---|---|
| `services/maestro/maestro/service/questions.py` | Python | Assigned behavior and integration contract |
| `tests/maestro/service/test_questions.py` | Python | Real main-path and essential-failure checks |
| `services/maestro/maestro/terminal/questions.py` | Python | Assigned behavior and integration contract |
| `services/maestro/maestro/terminal/extensions.py` | Python | Minimal generic extension input/choice provider hook for linked questions |
| `services/maestro/maestro/terminal/workspace.py` | Python | Minimal generic workspace routing to that provider hook |

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

1. A real test process publishes a linked question; terminal displays choices and free answer; the service saves an answer and delivers it to that same recipient with follow-up linkage.
2. Submit duplicate/late/wrong-project/wrong-question answer and interrupt delivery; assert one saved answer and correct reconciliation.
3. The included provider/consumer responsibilities use the real module/service boundary and meaningful declared outputs, with no unsupported stub or silent fallback. A provider demonstrates its boundary with a real minimal caller; later consumer implementation and assembled acceptance follow the common integration rules.
4. Mandatory checks below produce actual passing evidence for included behavior; disclose missing evidence as UNTESTED. Submit the exact scoped result for independent review under the common completion rules.

## Verification and essential failures

Preparation: isolated Python environment at the assigned base; `PYTHONPATH=services/maestro` for source-tree checks. Installed/external resources must come from the approved setup; do not install/provision or broaden access implicitly.

Exact test command:

```json
["python","-m","unittest","discover","-s","tests/maestro/service","-p","test_questions.py","-v"]
```

Required assertions: completion criteria 1 and 2, plus this essential rejection/recovery boundary: Stale/wrong question answers reject; uncertain delivery reconciles once; no answer inferred from silence.

The test file must observe the real included capability. Low-level deterministic inputs may isolate component logic; any actual service/agent/Git path promised by these criteria requires real path evidence, not a fake result. Missing installed resources are recorded as UNTESTED with nonzero status; do not convert them into success using a skip. Capture actual inputs, expected/observed results, command/exit output and source revision. No tests were run when writing this specification.

## Handoff

Return the saved implementation plan, exact base/local head, changed-path list, checks and their observed results, evidence references, limitations and unresolved work to the Development Manager. Service wrapper/remote verification and a non-author review follow. This file grants no integration, promotion, Owner confirmation or Execution-start authority.
