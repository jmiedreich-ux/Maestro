# M0-D05 — Tested Escalation and Local-Worker Routing Rule

**Status:** Accepted  
**Scope:** Maestro work packets, independent review, rework, and coordinator takeover  
**Supersedes:** The earlier generic "two-round" escalation proposal

## Decision

Maestro uses the tested escalation rule below. It distinguishes a genuine,
committed attempt that fails a named gate from a non-delivery, a scope breach,
or a packet that is invalid before review.

1. **No scoped diff or no required commit:** reject immediately. There is no
   correction round. Reassign the packet to the proven local Qwen workflow or
   escalate it to coordinator ownership.
2. **Committed, in-scope work fails a named gate:** allow one targeted
   correction only. The packet must state the exact defect to correct.
3. **The correction makes no source change, misses its commit, or remains out
   of scope:** escalate immediately. Do not loop further corrections.
4. **Independent review finds an R3/R4 contract defect:** correct it, renew
   independent review, and add the finding to the shared invariant or template
   before another similar packet is issued.
5. **Dependency, configuration, or placeholder violation:** reject before
   review. It is never accepted as a normal correction.

## Worker routing

The remote model returned no work twice. Both cases fall under rule 1, so the
remote model is no longer a production route.

Local Qwen is the active worker. The two remote-model failures were reassigned
to local Qwen; they were not coordinator takeovers and are not counted as
local-Qwen failures.

## Historical baseline

A hard escalation means that the local worker could not finish under the
packet contract and the coordinator had to complete or rebuild the work.

| Completed work | Local-origin assignments | Hard escalations to coordinator | Rate |
| --- | ---: | ---: | ---: |
| M1 | 7 | 0 | 0% |
| M2 | 3 | 2 | 67% |
| M3 | 27 | 6 | 22% |
| M4 through M4-10 | 7 | 3 | 43% |

If M3's one coordinator-commit custody case is included, M3 is 7 of 27
(26%). Across completed M1–M3 local-origin assignments, the strict historical
rate is 8 hard escalations out of 37 assignments (22%).

M4's 3 of 7 is skewed by the earlier large control packets: Popover, Tabs, and
Card. The newer small examples are 3 of 3 accepted by local Qwen: Dialog,
Drawer, and Popover. Current packet sizing is intended to keep escalations
below the earlier M2 and M4 large-packet results.

## Operating consequences

- A diff and commit are delivery prerequisites, not review feedback items.
- Named-gate feedback is the only path that permits one correction round.
- Review findings that reveal a contract weakness improve the shared packet
  design before that pattern is repeated.
- Maestro records the decision, routing, gate result, and escalation reason in
  its live operational state. Atlas may display that live state but has no
  authority to change routing or escalation.
