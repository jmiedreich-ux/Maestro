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
4. When a packet establishes a safety or ownership boundary, enforce it at every public construction, callable, and command entry path. Tests must exercise bypass paths and independently derive their expected boundary; they may not prove behavior only by comparing against the implementation constant under test.
5. Do not merge, deploy, force-push, alter protected project policy, use production credentials, or silently resolve conflicts/ambiguity.

## 3. Verify and hand off

1. Run the exact required checks without weakening or rewriting them.
2. Record changed files, commands and output, evidence artifacts, known gaps, and downstream outputs.
3. Complete every applicable done item as `PASS`, `N/A (reason)`, or `UNTESTED`.
4. Push only the designated branch/draft PR and hand it to Integration; never write directly to the project default branch.

## 4. Rework and escalation

One targeted, reviewer-requested rework cycle is allowed unless project policy says otherwise. A second failure, stale base, ownership conflict, missing decision, unexpected shared boundary, or unsafe resource condition becomes a blocked/escalated event with preserved evidence.
