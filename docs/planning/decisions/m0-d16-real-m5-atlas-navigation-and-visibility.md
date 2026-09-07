# M0-D16 — Real M5: Atlas Navigation and Coordination Visibility

**Status:** Owner-approved, 2026-09-06.
**Extends:** [M0-D15](m0-d15-real-m1-m4-implementation-path.md)'s M1–M4
numbering with a fifth milestone. M0-D15 remains the citation target for
M1–M4; this decision only adds M5 to that same numbering, it does not
revise M1–M4.

## Context

While reviewing a redesign of Atlas's mobile "Now" screen, the Owner asked
for real functionality with no home in any existing milestone: a real
milestone→packet hierarchy, single-packet navigation for Now/Events,
surfacing real worker check-ins, and project-wide History/Agents views.
Checked against every planning doc (`m2-atlas-roadmap.md`'s Wave A–G,
`m3-real-execution-roadmap.md`, `maestro-master-plan.md`) — none of it is
planned anywhere. M4 was considered and rejected as the wrong home: M4
([M0-D15](m0-d15-real-m1-m4-implementation-path.md)) is the persistent
Development Manager loop itself (real integration, review, notification,
recovery), not Atlas's own navigation/visibility surface.

## Decision

Adopt **M5** — Atlas navigation and coordination visibility — as the next
milestone after M4 in the M1–M4(–M5) numbering. Decomposed in
[the M5 Atlas roadmap](../m5-atlas-navigation-roadmap.md).

## Reason

This is real, Owner-requested scope with no existing milestone to absorb
it into; M4 is a different, already-scoped concern (the coordination
engine itself, not the interface for watching it). Naming it now, rather
than folding it silently into M4 or leaving it unscoped, keeps the
M1–M4 numbering's own citability intact for future planning docs.

## Consequences

- Any future roadmap slice for this scope cites this file and
  `m5-atlas-navigation-roadmap.md`, not an ad hoc reference.
- M4 remains scoped exactly as M0-D15 defined it — this decision does not
  fold navigation/visibility work into it.
