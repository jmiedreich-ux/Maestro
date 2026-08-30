# Proposed Feature — Agent Usage Observability

**Status:** Proposed for consideration — **not approved**  
**Implementation authority:** None  
**Approval authority:** Owner  
**Discussion date:** 2026-08-30  
**Current-program effect:** None. This proposal does not change Alpha-01,
Alpha-01-R1, M0-D11/M0-D12 reconciliation, the current handoff, any agent role,
model routing, review scope, merge authority, or the next authorized action.

## 1. Proposal summary

Consider adding usage observability to Maestro so the owner can understand where
the shared weekly ChatGPT Work/Codex allowance is being consumed across
architecture, planning, coordination, implementation, review, corrections,
integration, QA, and subagent work.

A related candidate practice is to conduct substantial repository-related
architecture conversations in Codex CLI when practical because local Codex
surfaces can expose structured token measurements and naturally associate the
conversation with repository context. ChatGPT Work/web would remain available
when owner interaction, visual work, connected apps, or mobile access provides
material value.

Neither the feature nor the candidate CLI-first practice is approved by this
record.

## 2. Problem to investigate

ChatGPT Work and Codex share usage limits. Architecture conversations therefore
consume the same allowance as implementation and review work. OpenAI exposes
structured token facts for controlled Codex runs, but a personal ChatGPT account
does not currently expose a supported API that gives Maestro exact usage for
every web conversation.

Without a Maestro record, the owner can see the remaining weekly allowance but
cannot reliably answer:

- how much usage went to architecture/planning versus implementation;
- how much was consumed by initial review, correction, or renewed review;
- whether subagents, high reasoning, Fast mode, long context, or failed attempts
  caused unusual consumption;
- which model and execution surface were used for each job; or
- how much account usage remains unattributed to a controlled run.

## 3. Candidate operating practice

If later approved, substantial repository-related architecture and planning
conversations would default to Codex CLI when practical.

Potential exceptions include:

- quick owner questions or decisions;
- visual design and rendered artifacts;
- connected-app work unavailable in the CLI;
- mobile access; and
- another surface that provides a documented material advantage.

A web conversation would still be registered under its honest work category.
The system would not repeat an entire conversation on a second surface merely to
manufacture telemetry. Accepted outcomes would still be preserved in versioned
planning records under the existing authority model.

Whether this practice should be mandatory, recommended, or omitted remains an
owner decision.

## 4. Candidate usage record

A future design could assign every controlled agent or architecture run a stable
Maestro job ID and capture:

- project, workstream, graph node or packet, role, work category, and parent job;
- execution surface and location;
- thread/conversation identifier, start/end time, and outcome;
- model, reasoning level, speed/service tier, and authentication/billing mode;
- input, cached-input, output, and separately reported reasoning-token detail;
- measured or estimated credits with rate-card version and effective date;
- retries, stalls, corrections, targeted follow-ups, renewed full reviews, and
  first-pass acceptance; and
- measurement provenance: `measured`, `estimated`, `account-delta-only`, or
  `unavailable`.

Candidate work categories are:

1. architecture and planning;
2. coordination and packet preparation;
3. implementation;
4. Independent Decision Fidelity Review;
5. Independent Implementation Review;
6. correction and targeted follow-up review;
7. integration;
8. QA; and
9. general or unattributed ChatGPT Work usage.

Prompt and source contents would be redacted from telemetry by default. A future
approved design must define retention, privacy, and access before implementation.

## 5. Candidate capture sources

- `codex exec --json` exposes a final `turn.completed.usage` object for
  non-interactive Codex runs.
- Codex OpenTelemetry can emit token counts on `response.completed` events for
  supported local clients.
- `/usage weekly`, `/status`, and the ChatGPT usage dashboard expose
  account/session-level observations supported by the active account and surface.
- ChatGPT Work/web conversations without per-conversation telemetry would remain
  explicitly `account-delta-only` or `unavailable`. The proposal does not endorse
  unsupported UI scraping or invented token counts.

Current OpenAI reference points:

- [Codex non-interactive JSON output](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Codex observability](https://learn.chatgpt.com/docs/config-file/config-advanced)
- [Codex usage commands](https://learn.chatgpt.com/docs/developer-commands)
- [ChatGPT Work/Codex pricing and usage](https://learn.chatgpt.com/docs/pricing)

These product contracts and rates can change. Any approved implementation would
need versioned adapters and rate-card provenance.

## 6. Candidate authority boundary

If approved later:

- joined repositories/GitHub would remain authority for architecture, plans,
  packets, code, reviews, and acceptance;
- Maestro's operational database would own observed usage measurements,
  calculations, provenance, reconciliation, and run relationships; and
- Atlas would display a read-only projection and would not control routing,
  spending, agents, plans, reviews, or merge.

Usage data would be operational evidence, not a second writable engineering
truth.

## 7. Candidate reconciliation

A future implementation could reconcile each account allowance window as:

`tracked controlled usage + tracked web/task usage + unattributed usage = observed account usage change`

If the account surface reports only a remaining percentage or another coarse
value, Maestro would preserve the raw observation and its precision. Concurrent
work that cannot be separated would remain visibly unattributed.

## 8. Candidate Atlas views

- weekly allowance pace and remaining observation;
- usage by project, role, work category, model, reasoning level, and surface;
- architecture/planning versus implementation/review/integration/QA;
- parent and subagent/child-run consumption;
- first-pass accepted, failed/stalled, correction, targeted-follow-up, and
  renewed-review usage;
- cached-input share and context growth;
- measured versus estimated usage; and
- the unattributed reconciliation remainder.

These views would inform future routing and process decisions. They would not
weaken Decision Fidelity Review, Independent Implementation Review, required
evidence, owner acceptance, or model-quality requirements.

## 9. Decisions required before approval

1. Approve, revise, defer, or reject the feature.
2. Decide whether CLI-first architecture work is mandatory, recommended, or not
   part of the feature.
3. Choose the earliest eligible delivery stage without changing the current
   authorized Alpha work.
4. Define which execution surfaces must provide exact telemetry and which may
   remain estimated/unattributed.
5. Define rate-card versioning and account-window reconciliation.
6. Define telemetry retention, privacy, redaction, and Atlas access.
7. Define whether usage can only inform recommendations or may enforce future
   owner-approved budgets.
8. Provide the complete M0-D12 bounded quality contract before any implementation
   packet is dispatched.

## 10. Explicit non-authorizations

This proposal does not authorize:

- implementation, database schema changes, telemetry configuration, or Atlas UI;
- changing the current Architecture Agent job role or required work surface;
- moving an active conversation or duplicating work for measurement;
- API-key billing or purchase of ChatGPT credits;
- automatic model rerouting, budget enforcement, or reduced review scope;
- unsupported scraping of ChatGPT account data;
- a change to Alpha-01/Alpha-01-R1 or its exact next gate; or
- merge, deployment, or successor work.