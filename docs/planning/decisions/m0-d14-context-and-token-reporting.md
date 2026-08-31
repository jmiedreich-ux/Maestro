# M0-D14 — Context and Token Reporting Starts at Run Preflight

- **Status:** Accepted by the Owner on 2026-08-31; planning-only amendment
  pending fresh Decision Fidelity Review and merge
- **Scope:** Project-neutral context budgeting, token/cost measurement, worker
  status, and Atlas reporting from preflight through terminal handoff
- **Source:**
  [Context and token reporting direction](../../../sources/planning/2026-08-31-context-and-token-reporting.md)

## Context

Maestro already retained earlier requirements to fingerprint model/context/
quantization, reject insufficient context, and report cost/tokens and elapsed
time. Patient worker-status reporting adds the natural live observation point.
Leaving these as separate later metrics would allow Maestro to dispatch without
knowing whether the packet fits and would make Atlas explain progress without
showing whether the worker is running out of usable context.

## Decision

Every worker attempt begins with one context-and-usage record that remains tied
to the attempt through completion. The approved packet/model route supplies:

- selected model and runtime identity;
- configured context limit and quantization when applicable;
- packet minimum context requirement;
- reserved completion/output tokens;
- warning and checkpoint/stop thresholds;
- tokenizer/counting method and permitted estimation fallback; and
- token/cost availability policy for that runtime.

Before launch, Maestro records known input tokens using the selected model's
tokenizer when available. Future tool/file growth is a bounded estimate or
range, never a false exact value. Dispatch is rejected when the configured
context or known starting payload cannot satisfy the packet minimum and output
reserve.

During execution, Maestro preserves runtime-reported input, output, cached
input, reasoning, and total counters when the runtime supplies them. An
unsupported value is `unavailable`, not zero. Estimated values remain labeled
as estimates with confidence and observation time; runtime-reported values take
precedence for the same measurement period.

Cost is recorded as one of billed amount/currency, estimated amount/currency,
`not_billed`, or `unknown`. Local execution is not silently called zero-cost;
elapsed time and relevant resource facts remain separate.

At the packet-defined pressure boundary, the Coordinator asks the active worker
for a short structured checkpoint at a safe message boundary. The checkpoint
contains completed work, current plan/step, changed artifacts, checks/evidence,
open blocker, and next action. Maestro records it and follows the packet's
checkpoint/stop rule. It does not silently truncate context, invent a summary,
interrupt a healthy worker merely to refresh a meter, or start a replacement
session without separately approved continuation behavior.

Atlas displays the durable measurement and worker-status projection. It does
not perform token counting, query the worker, or control context actions.

## Alpha-04 consequence

Alpha-04 qualifies this contract using fixed model/context/token/cost and
worker-checkpoint observations. It proves preflight rejection, reported-versus-
estimated handling, honest unavailable/unknown values, pressure decisions, and
Atlas-ready records. It invokes no real model, tokenizer service, billing API,
or Atlas UI.

## Non-authorization

This decision supplies planning authority only. It does not set universal
numeric thresholds, release an execution packet, invoke a model, expose raw
prompts/traces, authorize automatic compaction/session rollover, build Atlas,
contact a real project, or merge implementation.
