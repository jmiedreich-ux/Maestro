# Context and Token Reporting Direction — 2026-08-31

## Earlier source already captured

The earlier VennueSign
`docs/design/proposed/maestro-dev-lead-agent-framework.md` proposed recording
the selected model, cost/tokens, elapsed time, review rounds, rework count, gate
result, and untested count for every packet. Maestro already preserved that
source as S-02 and captured its atomic requirements in
`sources/planning/maestro-alpha-1-source-inventory.md`, including:

- `L-011`: fingerprint model, context window, and quantization for every run;
- `L-015`: block dispatch when the configured context is below the required
  minimum;
- `V-014`: record model, cost/tokens, elapsed time, review/rework, gates,
  untested checks, and later QA escapes;
- `P-004`: enforce model/context preflight before launching a worker; and
- `P-007`: retain elapsed time, model/context, and outcome with run evidence.

Those choices were preserved but had not yet been consolidated into one early
runtime and reporting contract.

## Owner clarification

After adding patient worker-status communication to Alpha-04, the Owner asked
whether context size can be predicted and then directed that the existing token
reporting feature be brought together with this work "in the beginning." The
Owner clarified that the intended primary comparison is Maestro-controlled
OpenAI work against the ChatGPT/Codex weekly usage allowance, not token counts
alone. The Owner then identified the existing
`docs/agent-usage-observability` branch as the earlier discussion source.

That branch's `agent-usage-observability.md` already proposes an OpenAI
allowance card with used/remaining observation, reset time, pace, confidence,
and last refresh; controlled-run attribution; coarse registered ChatGPT Work/
web activity; and a visible unattributed remainder. It also states that a
personal ChatGPT account may not expose exact per-conversation usage through a
supported API and forbids unsupported UI scraping or invented token counts.

## Owner-approved direction

Allowance observation, context budgeting, and usage reporting begin before
assignment and stay attached to the same account-window/attempt/status records
throughout the run:

1. When a supported account surface supplies it, preflight records the active
   ChatGPT/Codex allowance window, used/remaining observation, reset time,
   precision, and observation time. If unsupported, the account state remains
   `unavailable`; Maestro does not scrape or infer it from tokens.
2. Preflight records the selected model/runtime, configured context limit,
   quantization when applicable, packet minimum context, output reserve, and
   token-count method.
3. Before dispatch, Maestro records exact known-input tokens when the selected
   model tokenizer is available, otherwise a labeled estimate/range and its
   confidence. Unknown future tool/file growth remains an estimate.
4. A run that cannot satisfy its packet minimum plus output reserve is rejected
   before worker launch.
5. During execution, runtime-reported counters replace estimates when
   available. Unsupported counters remain `unavailable`; they are not recorded
   as zero. In particular, zero or unavailable reasoning tokens never means
   zero context use.
6. Controlled OpenAI attempts are linked to the account window without claiming
   that per-run tokens directly equal allowance percentage. Supported coarse
   ChatGPT Work/web observations are registered honestly. Concurrent or
   otherwise unexplained account change remains an unattributed remainder.
7. Worker status includes current context use/remaining estimate and can request
   a short checkpoint at a configured pressure boundary. Maestro does not
   silently summarize, truncate, or start a replacement session.
8. Atlas reports the durable facts: allowance used/remaining/reset/pace where
   supported, tracked controlled usage, coarse registered usage, unattributed
   remainder, context limit, used/remaining estimate, output reserve, token
   counters, measurement type, confidence, pressure, worker plan/status,
   elapsed time, and cost as billed/estimated/not-billed/unknown. Local Qwen
   capacity remains separate from the ChatGPT/Codex allowance.
9. No raw prompt, chain-of-thought, or transcript is exposed merely to produce
   these measurements.

Global optimization thresholds are not invented before data exists. Each
approved packet/model route supplies bounded minimum, reserve, warning, and
checkpoint/stop rules. Allowance pace warnings also require an Owner-approved
threshold. This direction authorizes planning only and does not release
Alpha-03 or Alpha-04 implementation.
