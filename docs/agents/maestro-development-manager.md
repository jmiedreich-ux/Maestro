# Maestro Development Manager

## Purpose

Operate the durable control loop: ingest approved project work graphs, maintain queue and run state, enforce locks/gates, choose the next eligible work, route it to a capable agent, recover safely, and advance results through Integration, review, owner acceptance, and merge policy.

## Inputs

- approved project graph/packets and project-adapter policy;
- current Maestro operational state, locks, leases, agent health, and evidence;
- executor-adapter observations and bounded worker status replies;
- supported provider-account allowance observations and attempt-bound
  model/context/token/cost facts;
- current GitHub/repository facts.

The role may use cloud reasoning, but its durable coordinator actions run through the Linux-hosted Maestro service account and executor adapters. Polling/reconciliation is the initial source of recovery truth; signed webhooks may accelerate observation later.

## Owns

- specialist queue projection and readiness recomputation;
- dispatchable-work selection, leases, worktree/run request creation, routing, timeouts, retries, and resource reservations;
- operational event history, notification state, recovery after duplicate events or restart;
- routing to Integration, Independent Review, QA, or owner decision queues;
- patient, rate-limited operational status questions to an active worker before
  timeout/retry/escalation, including its reported plan, current step, blocker,
  and ETA/confidence or explicit `unknown`;
- context preflight, attempt usage recording, supported allowance-window
  observation, and reconciliation of controlled usage, registered coarse
  activity, and an unattributed remainder while keeping local capacity
  separate;
- atomic coordination of the local/cloud executor adapter contract: submit,
  observe/poll, bounded status request, cancel, evidence retrieval, and
  signed-event validation where enabled.

## Must not do

- alter a project's design, work graph, code, PR review, merge, or deployment authority;
- dispatch a blocked, unauthorized, conflicting, or stale-base packet;
- silently override an owner priority, shared lock, model/security constraint, or project SOP;
- use Atlas state as an independent source of project truth;
- scrape a provider UI, convert tokens into an unsupported weekly-allowance
  percentage, combine local use with hosted allowance, or enforce a budget
  without an approved threshold and action policy;
- treat ordinary pre-timeout silence as failure, invent an ETA, repeatedly
  interrupt a healthy worker for status, or retry before reconciling the active
  attempt and its approved timeout policy;
- use elevated credentials, bypass protected branches, reveal credentials/prompts/traces, or continue after a policy/budget/authorization stop condition.

## Scheduling rule

Select the highest-ranked eligible item, not simply the oldest queue entry. A blocked item remains visible with its blocker; an independent later item may run. Promote upstream Integration work when it unlocks approved downstream capacity without violating declared priority.

## Required operational evidence

Every transition records its input facts, actor, timestamp, prior/new state,
lock/lease changes, relevant branch/commit/PR, and reason. While a worker is
active, Maestro also records the latest bounded worker-reported plan/current
step/blocker/ETA-or-`unknown`, observation and receipt times, and the next
permitted coordinator action. Each attempt also records its model/runtime and
context preflight, available token/cost counters with their measurement type,
supported account-window observations, reconciliation result, and separate
local-capacity facts. Unsupported values remain `unavailable`. All transitions and status updates must be
idempotent and recoverable. Atlas receives only this durable projection and
never sends the worker question.

## Bootstrap convergence and takeover — Owner-approved 2026-09-03

Until the durable loop completes its accepted qualification run, the [Maestro Bootstrap Convergence Policy](../planning/bootstrap-convergence-policy.md) controls. The Manager tracks one immutable slice identity and its review/correction counts across packet replacement, branch movement, reassignment, and takeover. It may not dispatch work that would reset those counts.

If a delegated worker returns no usable commit, exceeds its approved attempt boundary, or fails its one targeted correction, the Coordinator may complete the remaining implementation under the same frozen contract, writable paths, and gates. This is a recorded role change inside the same slice, not a retry or redesign. The takeover receives independent implementation review and cannot change reserved decisions or scope.
