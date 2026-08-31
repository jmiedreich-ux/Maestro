# M0-D14 — Allowance, Context, and Usage Reporting Starts at Run Preflight

- **Status:** Accepted by the Owner on 2026-08-31; planning-only amendment
  pending fresh Decision Fidelity Review and merge
- **Scope:** Project-neutral provider-account allowance observation, context
  budgeting, token/cost measurement, worker status, and Atlas reporting from
  preflight through terminal handoff
- **Source:**
  [Context and token reporting direction](../../../sources/planning/2026-08-31-context-and-token-reporting.md)
  and the captured
  [Usage & Observability proposal](../proposed/agent-usage-observability.md)

## Context

Maestro already retained earlier requirements to fingerprint model/context/
quantization, reject insufficient context, and report cost/tokens and elapsed
time. The existing Usage Observability proposal also defines provider-account
allowance windows, tracked controlled usage, coarse registered usage, and an
unattributed remainder. Patient worker-status reporting adds the natural live
observation point. Leaving these as separate later metrics would allow Maestro
to dispatch without knowing whether the packet fits or how hosted work relates
to the Owner's visible weekly allowance.

## Decision

Every hosted or local worker attempt begins with one context-and-usage record
that remains tied to the attempt through completion. Hosted work also links to
the applicable provider/account allowance-window record when a supported
observation exists.

An allowance-window record carries the provider, non-secret account/workspace
identifier, native window type (including the ChatGPT/Codex weekly window where
shown by the supported usage surface), used/remaining amount or percentage,
reset time when supplied, precision, measurement quality, observation time, and
fresh/stale/unavailable state. Token totals must not be converted into an
allowance percentage unless the provider publishes that supported conversion.

The approved packet/model route supplies:

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

For each observed OpenAI account window, Maestro reconciles:

`tracked controlled usage + registered coarse usage + unattributed remainder = observed account change`

Per-run token facts remain useful for explaining controlled work, but they are
not treated as the weekly allowance unit. ChatGPT Work/web activity without
exact run counters may be registered as coarse usage. Concurrent or otherwise
unexplained change remains visibly unattributed. Local Qwen activity is shown as
local capacity/time and is never subtracted from the ChatGPT/Codex allowance.

Allowance pace may be calculated only from a supported used/remaining window,
known/reset timing, and recorded observation times. It is labeled as an
estimate and cannot enforce routing or stop work without a separate
Owner-approved threshold and policy.

At the packet-defined pressure boundary, the Coordinator asks the active worker
for a short structured checkpoint at a safe message boundary. The checkpoint
contains completed work, current plan/step, changed artifacts, checks/evidence,
open blocker, and next action. Maestro records it and follows the packet's
checkpoint/stop rule. It does not silently truncate context, invent a summary,
interrupt a healthy worker merely to refresh a meter, or start a replacement
session without separately approved continuation behavior.

Atlas displays the durable allowance, reconciliation, context/usage, and
worker-status projection. It does not scrape a provider UI, perform token
counting, query the worker, or control allowance/context actions.

## Alpha-04 consequence

Alpha-04 qualifies this contract using fixed OpenAI account-window, controlled/
coarse/unattributed usage, local-capacity, model/context/token/cost, and worker-
checkpoint observations. It proves window reconciliation, no false token-to-
allowance conversion, preflight rejection, reported-versus-estimated handling,
honest stale/unavailable/unknown values, pressure decisions, and Atlas-ready
records. It invokes no real provider account, model, tokenizer service, billing
API, or Atlas UI.

## Non-authorization

This decision supplies planning authority only. It does not authorize account
credentials, unsupported UI scraping, a claim of exact weekly usage where the
supported surface is coarse/unavailable, universal numeric thresholds, budget
enforcement, routing changes, credit purchases, an execution packet, model
invocation, raw prompt/trace exposure, automatic compaction/session rollover,
Atlas implementation, real-project contact, or implementation merge.
