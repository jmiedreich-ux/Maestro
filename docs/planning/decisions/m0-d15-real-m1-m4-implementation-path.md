# M0-D15 — Real M1–M4 Implementation Path (reconstructed)

> **Corrected 2026-09-10.** This file's reconstruction note below claims the
> original "no longer exists on origin and no trace of the file survives in any
> local clone, reflog, or other branch." That is false — it was on the local
> branch `architecture/m1-m4-packets` the whole time. The original is now
> restored at
> `m0-d15-original-real-m1-m4-implementation-and-non-live-proving-path.md` and
> is the authority. This file is kept because other records cite its filename.

- **Status:** Accepted by the Owner on 2026-09-01 (original, per
  `maestro-master-plan.md` line 17's own citation date — corrected here from
  an earlier draft's 2026-08-31, caught during the M3 Decision Fidelity
  check); reconstructed and re-confirmed by the Architect with Owner
  sign-off on 2026-09-06.
- **Scope:** Supersedes the Alpha/V1/V2/V3 phasing in `maestro-master-plan.md`
  §9 with a real M1–M4 numbering.

## Reconstruction note

The original M0-D15 was authored and Owner-approved on 2026-08-31 on the
unmerged branch `architecture/m1-m4-packets`. That branch no longer exists on
`origin` and no trace of the file survives in any local clone, reflog, or
other branch — confirmed by search during M3 scoping on 2026-09-06. Only
`maestro-master-plan.md`'s own remap note (added when the numbering was
adopted, itself citing this decision) survives as source text.

Per Owner decision during the 2026-09-06 M3 scoping session: rather than
leave a dead citation in force, or block M3 scoping on a full archaeological
reconstruction, this file recaptures the surviving remap-note prose as a
properly-formed decision record under `maestro-master-plan.md` §5's own
Decision schema (context, options, choice, reason, consequences), reusing
the original `m0-d15` filename since nothing else can be citing the real one.
No content beyond what `maestro-master-plan.md` already stated is asserted
here as invented; where a consequence below is Architect judgment rather
than surviving source text, it is marked as such.

## Context

`maestro-master-plan.md` §9 (unchanged since M0) still describes the
original M0 / Alpha qualification / V1 / V2 / V3 phasing. Every slice
actually merged since M1-01 has instead used an M1–M4 numbering, with no
decision record in force to explain the switch except the master plan's own
inline remap note.

## Options considered

1. **Reconstruct the remap note as a real decision record** (this file),
   using the master plan's own surviving text as source of truth.
2. **Leave the dead citation in force** and keep relying on the inline
   master-plan note alone. Rejected: every subsequent milestone roadmap
   (`m2-atlas-roadmap.md`, this M3 roadmap) cites `M0-D15` by path for the
   M4 Development Manager loop and the M1–M4 definitions; an uncitable
   decision undermines the planning model's own traceability requirement
   (§5: "every source item must link to a requirement, decision, task,
   question, explicit deferral, or not-applicable record").
3. **Pause all M3 scoping to fully re-derive the original decision's
   options/consequences from scratch.** Rejected by the Owner as
   disproportionate: the surviving master-plan text is unambiguous and
   already Owner-approved; re-deriving it from nothing would not change its
   content, only delay M3.

## Decision

Adopt, as the current M1–M4 implementation path:

- **M1** — the Linux service core and durable operational records
  (surviving master-plan text, verbatim). *Architect judgment, not
  surviving source text:* in practice this has meant run lifecycle,
  packet/attempt/review state, guarded commands, and notification/recovery
  primitives — named here only as descriptive gloss on what "durable
  operational records" turned out to mean once M1 was actually built, not
  as a claim the original decision itself enumerated these.
- **M2** — Atlas as the local operator interface: live reporting plus the
  operator-action commands named in
  [M0-D01's amendment](m0-d01-operational-database.md#atlas-operator-action-amendment--owner-approved-2026-09-05),
  decomposed wave-by-wave in [the M2 Atlas roadmap](../m2-atlas-roadmap.md).
  (Surviving master-plan text, verbatim.)
- **M3** — replaces fixture execution with a real packet compiler, a real
  agent executor, and mechanical grading (surviving master-plan text,
  verbatim), decomposed in
  [the M3 real-execution roadmap](../m3-real-execution-roadmap.md) (link
  added 2026-09-06 — the surviving text obviously predates that roadmap).
- **M4** — completes the persistent Development Manager loop: real
  Integration, review, notification, and recovery (surviving master-plan
  text, verbatim). *Architect judgment, not surviving source text:* the
  claim that this includes "the autonomous Architect ruling loop" is an
  inference from `m2-atlas-roadmap.md`'s own decision-card entry, which
  attributes that loop to M4 by name — it is not stated in the surviving
  master-plan remap note itself, and should be confirmed as a real M4-scope
  decision when M4 is actually scoped, not assumed here.

This numbering supersedes `maestro-master-plan.md` §9's Alpha/V1/V2/V3
phasing for all planning going forward; §9 itself is retained as historical
record and has not been rewritten to match (per the master plan's own
standing note).

## Reason

This is the numbering every slice merged since M1-01 has actually used in
practice; formalizing it as a citable decision closes the traceability gap
the dead branch left open, without changing any already-Owner-approved
content.

## Consequences

- `M0-D15` is again a valid citation target for any planning doc that needs
  to reference the M1–M4 definitions or the M4 autonomous Architect loop.
- `maestro-master-plan.md` §9's old phasing remains unrewritten and should
  be read as historical, not current (Architect judgment, consistent with
  the master plan's own existing caveat).
- Any future roadmap slice for M3 or M4 cites this file rather than the
  master plan's inline note directly, matching how `m2-atlas-roadmap.md`
  already does.
