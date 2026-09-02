# Alpha-04 Readiness Direction — 2026-09-01

## Source

Owner discussion with the Maestro Architect after Alpha-03 closeout and after
reviewing the merged Alpha-04 control-loop sequence.

## Owner direction

The Owner directed the Maestro Architect to proceed with Alpha-04 readiness.
The Owner also required every Alpha-04 stop or escalation to state clearly when
control returns to the **Project Architecture Agent**, rather than using an
unqualified `escalate` result.

## Readiness boundary

This direction lifts the earlier pause only for readiness work: current-source
inspection, predecessor reconciliation, exact execution-packet drafting, and
preparation for Decision Fidelity Review. It does not by itself approve the
draft packet, release implementation, dispatch Local Qwen, create Maestro
operational queue state, invoke a real actor or provider, access Foundry, merge,
or select successor work.

The packet must distinguish:

- routine operational handling that remains with the Coordinator;
- an exact `ProjectArchitectReturn` when authority, graph meaning, packet
  boundaries, architecture contracts, or the permitted correction path cannot
  determine one safe next action; and
- `AwaitingOwner` or an Owner decision requested through the Project Architect
  when the project policy requires material Owner judgment.

Every `ProjectArchitectReturn` must preserve the reason, evidence references,
required decision, whether Owner judgment is required, and the safe no-further-
assignment/no-further-mutation disposition.

## Follow-up authorization

After reviewing the readiness result, the Owner directed the Architect to
proceed with the next gate. This authorizes committing the draft packet and
routing its exact range to a fresh independent GPT-5.6 Sol Decision Fidelity
Reviewer. It does not approve the review outcome in advance or release
implementation.

## Predecessor fact to preserve

Alpha-03 is complete by explicit Owner acceptance at corrected implementation
head `f21e4a2ff25cead8b972b4433da33f0e9910efc5` and merged through
`8aa4cb517dcb902060cf5acd1d58806787e03841`. Its independent implementation
reviews returned `REQUEST_CHANGES`; readiness must not relabel that result as an
independent-review approval. Alpha-04 must use a valid repository-owned binding
fixture and must preserve the accepted Alpha-only malformed-conflict limitation
without broadening any rejection claim.
