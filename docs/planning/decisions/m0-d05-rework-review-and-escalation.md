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

## Review renewal scope

The first independent review of a proposal or implementation examines the full
approved range. A follow-up after correction is a **targeted verification**, not
a new full review.

The same independent reviewer may and normally should perform the follow-up
because it already owns the findings and did not author the correction. The
follow-up verifies only:

1. every named finding retains its recorded Project Architect disposition and
   every `correct now` finding received the exact required correction;
2. the correction diff contains no unrelated change;
3. the correction creates no direct contradiction in the immediately affected
   records, code, tests, or evidence; and
4. every `correct now` finding is resolved, while each unchanged `accept known
   limitation` finding retains its truthful result and has the required linked
   backlog evidence, rationale, revisit trigger, and exact-head integrity.

The reviewer must use the smallest review scope that can prove those facts and
stop when they are proven. A new out-of-scope observation is non-blocking and is
recorded separately unless the correction itself introduced it or it proves a
direct material violation of the approved contract.

A full renewed review is required only when the base or reviewed range changes,
the correction includes unrelated work, the correction materially redesigns a
shared contract, prior evidence becomes unreliable, or reviewer independence is
lost. The reason for reopening full scope must be recorded.

This targeted-follow-up rule preserves quality while preventing every
correction from restarting discovery from zero.

## Complete review coverage and freshness

Anything merged to a default branch must have complete independent review
coverage.

Complete coverage means:

- one full review covers an exact base/head range;
- every later correction-only diff receives targeted verification;
- the union of the full reviewed range and all targeted-reviewed correction
  diffs equals the exact final merge candidate; and
- no unrelated or unreviewed change exists between the covered head and merge.

The merge gate records the covered base, each reviewed head/diff, and the exact
final head. Approval becomes stale when an uncovered commit appears, the final
head differs from the covered chain, prior evidence is invalidated, or the base
changes in a way that materially affects the reviewed result.

A correction-only change receives targeted review. A new unrelated change
reopens affected or full scope. A materially changed base requires rebase and
review of the impacted areas; a base change with no relevant effect may retain
coverage only when the reviewer records that conclusion.

This rule guarantees that every merged change has been reviewed while avoiding
a redundant full reread of unchanged material.

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

## Forecast for remaining M4 browser-spec packets

This is a planning forecast, not a completed-work metric. For the four remaining
local-Qwen browser-spec packets, M4-18 through M4-21:

| Estimate | Basis |
|---|---|
| About 1 hard escalation | Comparable M3 browser packets had 2 hard escalations in 10 packets (20%). |
| Likely range: 0–2 hard escalations | The sample is small; one packet may need coordinator completion. |
| About 1 review/correction per packet | Local work is usually close, but source review commonly finds a bounded omission. |
| 3–4 local-Qwen accepted outcomes | The expected case is that most of the four finish locally under the existing gates. |

Across M1–M3, hard escalation was 8 of 37 local-origin assignments (22%), or
roughly one in every four to five assignments. For these tightly bounded browser
tests, the comparable evidence supports an approximately 20% forecast.

## Operating consequences

- A diff and commit are delivery prerequisites, not review feedback items.
- Named-gate feedback is the only path that permits one correction round.
- Review findings that reveal a contract weakness improve the shared packet
  design before that pattern is repeated.
- Maestro records the decision, routing, gate result, and escalation reason in
  its live operational state. Atlas may display that live state but has no
  authority to change routing or escalation.

## Bootstrap convergence amendment — Owner-approved 2026-09-03

The [Maestro Bootstrap Convergence Policy](../bootstrap-convergence-policy.md) controls Maestro's own development until the durable loop completes its accepted qualification run. Its slice-wide identity, frozen-contract rule, bounded review sequence, correction budgets, terminal return behavior, Coordinator takeover, and learning quarantine override any conflicting earlier language in this decision.

For one bootstrap slice, packet replacement, branch movement, reassignment, or takeover does not reset the one planning-correction or one implementation-correction allowance. R3/R4 findings are learning candidates and do not amend shared invariants or templates during the active slice. A new ordinary finding after the complete set is non-blocking; only the policy's named critical exceptions may interrupt the frozen slice.

## Risk-based disposition amendment — Owner-approved 2026-09-04

A reviewer `REQUEST_CHANGES` does not itself authorize rework. Before dispatch,
the Project Architect applies the
[risk-based finding disposition](../bootstrap-convergence-policy.md#risk-based-finding-disposition).
Only `correct now` consumes the slice's one implementation correction.
`accept known limitation` requires the recorded backlog issue, advances the
unchanged reviewed candidate as `accepted-with-known-limitations`, consumes no
correction, and requires no targeted implementation verification. The reviewer
finding remains recorded. Critical exceptions, reserved Owner risks, and
primary-outcome failures cannot use this path. This prospective rule does not alter prior terminal or
completed slices.
