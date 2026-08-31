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
reporting feature be brought together with this work "in the beginning."

## Owner-approved direction

Context budgeting and usage reporting begin before assignment and stay attached
to the same attempt/status record throughout the run:

1. Preflight records the selected model/runtime, configured context limit,
   quantization when applicable, packet minimum context, output reserve, and
   token-count method.
2. Before dispatch, Maestro records exact known-input tokens when the selected
   model tokenizer is available, otherwise a labeled estimate/range and its
   confidence. Unknown future tool/file growth remains an estimate.
3. A run that cannot satisfy its packet minimum plus output reserve is rejected
   before worker launch.
4. During execution, runtime-reported counters replace estimates when
   available. Unsupported counters remain `unavailable`; they are not recorded
   as zero. In particular, zero or unavailable reasoning tokens never means
   zero context use.
5. Worker status includes current context use/remaining estimate and can request
   a short checkpoint at a configured pressure boundary. Maestro does not
   silently summarize, truncate, or start a replacement session.
6. Atlas reports the durable facts: context limit, used/remaining estimate,
   output reserve, token counters, measurement type, confidence, pressure,
   worker plan/status, elapsed time, and cost as billed/estimated/not-billed/
   unknown.
7. No raw prompt, chain-of-thought, or transcript is exposed merely to produce
   these measurements.

Global optimization thresholds are not invented before data exists. Each
approved packet/model route supplies bounded minimum, reserve, warning, and
checkpoint/stop rules. This direction authorizes planning only and does not
release Alpha-03 or Alpha-04 implementation.
