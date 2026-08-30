# M0-D10 — Foundry as the V1 Proving Project

**Status:** Accepted  
**Scope:** Selection and safe entry conditions for Maestro's first live
project registration and packet proof.

## Decision

Foundry, not VennueSign, is Maestro's first V1 proving project. Foundry is
already structured around bounded packets, browser checks, independent review,
and milestone acceptance. VennueSign remains a later existing-project
registration; its registration discovery will identify the organizational and
code-level work needed before it can safely accept Maestro-dispatched work.

Foundry uses `maestro project register`: read-only discovery first, then a
reviewable binding proposal and dry run. Maestro does not overwrite Foundry's
existing process or create a parallel plan.

## Initial proving sequence

1. Register Foundry read-only and produce its project binding proposal.
2. Run the non-dispatching dry run against Foundry's declared paths and gates.
3. Show Foundry's live observed state in the fresh reporting view.
4. Select one unclaimed, explicitly released Foundry packet for the first
   Maestro-controlled execution proof.
5. Apply the existing packet, review, escalation, and owner-acceptance rules
   without automatic merge.

## Current Foundry boundary

M1, M2, and M3 are complete and accepted. M4 has four remaining browser-test
packets—Popover, Menu, Tabs, and Card—followed by final review, verification,
record synchronization, and owner acceptance. M5 is the planned
cross-control release-acceptance milestone.

The active Popover packet is not claimed, modified, or rerouted by Maestro's
V1 setup. It has no committed result at this point. Its worktree is clean.
The first proof packet must instead be an unclaimed packet that is explicitly
released for Maestro after registration and dry-run success.

## Consequences

- Foundry keeps its own authoritative roadmap, code, gates, and acceptance
  records.
- Maestro adds operational visibility and controlled execution evidence; it
  does not weaken Foundry's rules.
- M5 and any future Foundry skin work remain Foundry planning decisions, not
  prerequisites for Maestro V1.
- VennueSign's archive and fresh-reporting work remain later registration
  follow-through, outside the V1 proving path.
