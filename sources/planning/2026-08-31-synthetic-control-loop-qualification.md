# Synthetic Control-Loop Qualification Direction — 2026-08-31

## Source

Owner discussion with the Maestro Architect after the Alpha-03 planning and
status records merged.

## Concern raised

The Owner identified Maestro's agent control loop as a central product promise:
approved work should be assigned through the development manager and
coordinator, passed through the appropriate worker and Integration route,
independently reviewed, and stopped at the applicable owner gate. The Owner
asked when Maestro itself—not a manually coordinated chat process—would begin
proving those assignments and handoffs.

## Architect assessment presented

- Alpha-02 proves only the synthetic packet-wrapper lifecycle and stops at a
  review handoff.
- Alpha-03 proposes a fixture-only project binding and explicitly excludes
  scheduling or dispatch.
- The existing roadmap makes Foundry V1 the first end-to-end controlled loop
  and defers the fuller specialist queues, Integration routing, local-model
  assignment, and limited parallelism to V2.
- This leaves no explicit whole-loop synthetic qualification gate before a real
  Foundry packet becomes the proving subject.

## Owner-approved direction

The Owner agreed to add a separate pre-V1 synthetic control-loop qualification
stage. It must:

1. preserve Alpha-03 without silently expanding its approved packet;
2. use only fixtures and scripted local actors/observations;
3. prove eligibility, assignment, durable ownership/locks, worker handoff,
   Integration routing, independent review routing, bounded correction,
   restart/duplicate safety, and the final Owner stop;
4. prohibit real project/repository access, GitHub, credentials, network calls,
   real model or agent dispatch, merge, deployment, and successor selection;
5. complete before the first live Foundry V1 execution proof; and
6. leave V2 responsible for production specialist queues, real local-model
   routing, and limited multi-packet parallelism.

The Owner then directed the Maestro Architect to proceed with formal planning.
This source record and its derivative planning do not release Alpha-03 or any
control-loop implementation.

## Follow-up clarification — patient worker communication

The Owner supplied an example in which a Coordinator queried an active Local
Qwen session for its plan and timing before assuming the worker was inactive.
The worker reported an ordered implementation plan, named its current step, and
honestly stated that it did not yet have a reliable completion time. The Owner
confirmed that this was acceptable and clarified the governing behavior:

- the Maestro manager/Coordinator should ask an active local worker bounded
  operational questions before assuming that silence means no progress;
- it should not become impatient, interrupt, retry, or escalate merely because
  a model has not produced a terminal result yet;
- the status request should ask for the worker-reported plan, current step,
  blocker, and expected timing, allowing `unknown` when no reliable estimate
  exists; and
- Maestro should durably record the factual response so read-only Atlas can
  show it as worker-reported status, not as a guaranteed completion promise.

This clarification does not make Atlas a controller or authorize arbitrary
chat, prompt/trace exposure, infinite waiting, or operation past an approved
timeout or stop condition.
