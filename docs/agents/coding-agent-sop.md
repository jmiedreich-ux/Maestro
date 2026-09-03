# Maestro Coding Agent SOP

This SOP applies to every implementation agent. Project policy comes first; this is the common Maestro safety floor. Specialist overlays and task packets may add rules but may not weaken either the project policy or this SOP.

## 1. Preflight — stop if any check fails

1. Confirm the immutable packet ID, role/SOP version, repository, base commit, branch, and execution class.
2. Create or verify a clean isolated worktree. Never work in a directory held by another run.
3. Read the project-required startup records and exact authority paths named by the packet.
4. Confirm the packet is approved, its graph revision/authority reference/source base are current, dependencies are complete, required locks are leased, and environment/credential policy is satisfied.
5. Confirm allowed/forbidden paths, acceptance behavior, validation commands, timeout, and handoff route.
6. Record the preflight result; block rather than improvising when a fact is missing or contradictory.

## 2. Execute within scope

1. Change only authorized paths and do not broaden a packet to solve adjacent work.
2. Preserve the project architecture, conventions, and accepted behavior.
3. Use real project validation rather than tests that merely duplicate implementation logic.
4. When a packet establishes a material quality boundary, implement only its complete owner-approved M0-D12 contract: protected outcome, operating/threat/failure model, exclusions, assurance level, sufficient proof, implementation boundary, proportionality ceiling, and stop rule. Exercise every public path and negative/race condition that contract places in scope, using independent test oracles where required. Do not silently strengthen the threat model or pursue excluded edge cases after the named proof passes. For Linux runtime paths, the current M0-D11 quality contract controls the exact symlink, mutation, artifact, and actor boundary.
5. Do not merge, deploy, force-push, alter protected project policy, use production credentials, or silently resolve conflicts/ambiguity.

## 3. Verify and hand off

1. Run the exact required checks without weakening or rewriting them.
2. Record changed files, commands and output, evidence artifacts, known gaps, and downstream outputs.
3. Complete every applicable done item as `PASS`, `N/A (reason)`, or `UNTESTED`.
4. Push only the designated branch/draft PR and hand it to Integration; never write directly to the project default branch.

## 4. Rework and escalation

One targeted, reviewer-requested rework cycle is allowed unless project policy says otherwise. Its follow-up review is limited to the named finding, correction-only diff/evidence, and directly affected consistency. A different failure class, uncovered or materially stale change, ownership conflict, missing decision, unexpected shared boundary, or unsafe resource condition becomes a blocked/escalated event with preserved evidence.

## Bootstrap convergence boundary — Owner-approved 2026-09-03

The [Maestro Bootstrap Convergence Policy](../planning/bootstrap-convergence-policy.md) controls Maestro's own development. A packet rewrite, branch move, worker reassignment, or Coordinator takeover remains the same slice and does not reset its correction allowances. The worker implements the frozen contract and named proof; it does not absorb later ordinary review preferences.

Coordinator takeover may complete non-delivery before the full implementation review, or may perform the slice's sole named correction if that correction remains unused. After targeted verification, the candidate is approved or terminally returned; no takeover, correction, or renewed review remains.
