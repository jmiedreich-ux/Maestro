# M0-D17 — M4.16: Real Ruling-Loop Classification Criteria

**Status:** Architect-authored, 2026-09-08, under the Owner's standing
2026-09-08 authorization to complete M4 end-to-end.
**Is:** the real decision content M4.16 (A0) exists to produce — a
concrete test, not code. Per `m4-development-manager-roadmap.md` and
`m4-packet-breakdown.md`'s own explicit note, no implementation packet
for the ruling loop itself is proposed until this criteria is real.

## The three-tier authority model (Owner ruling, 2026-09-08)

1. **Worker/Reviewer** — routine execution inside an already-approved
   packet's own owned paths and checks. No classification needed; this
   tier never escalates a decision, only reports facts.
2. **Project Architect** — the role this session has been playing.
   Absorbs escalations from tier 1. Two real powers, both self-granted,
   no Owner round-trip required:
   - **Slot pre-approved scope into the process.** Real work the Owner
     already approved in substance (a design, a roadmap, a feature) but
     that has no milestone/packet home yet. The Architect decides where
     it goes and keeps work moving. **Worked example:** M5 — Atlas
     screens the Owner had already approved; M4 was the wrong home,
     the Architect created M5 rather than stopping.
   - **Durability additions.** New store commands, schema-adjacent
     plumbing, or process infrastructure needed to deliver
     already-approved scope, where the addition doesn't change what the
     product does or who can accept what. **Worked example:** this
     session's own `record_notification_outcome` (M4.12) and the
     earlier CG-M4-19 `acceptance_authority` field fix — both real gaps
     in already-approved M1/M4 scope, fixed without an Owner round-trip.
3. **Owner** — the real residual. Three things are explicitly named as
   Owner-only and never self-grantable by the Architect:
   - **Changes what the project means** (product scope, not
     infrastructure).
   - **Redefines what a role is allowed to accept** (e.g., who may
     grant Owner-acceptance, under what real criteria — this is why
     M4.09's own criteria for self-granted acceptance needed an
     explicit Owner ruling before I0 could be built on it).
   - **Decides the ruling loop's own authority boundary** — this
     document itself. The Architect cannot self-amend what tier 2 may
     self-grant; only the Owner can move that line.
   Owner-acceptance of a *packet* (the real M4.09/`accept_packet` act)
   is itself real tier-2 scope once the Owner's own criteria are met —
   see below — it is not the same thing as the three items above.

## The real test: which tier does a given decision belong to?

Ask, in order:

1. **Does it change what the project *means*** (adds/removes real
   product scope, changes who a feature is for, changes what "done"
   means for the product)? → **Owner.**
2. **Does it redefine what a role may accept**, or **touch the ruling
   loop's own boundary** (this document)? → **Owner.**
3. Otherwise: is it **durability/process infrastructure** needed to
   deliver scope the Owner already approved (a new store command, a
   wiring module, a milestone/packet-home decision for already-approved
   work)? → **Architect**, self-granted, logged in the relevant
   packet-breakdown doc (as this session has done throughout M4) so the
   Owner can review after the fact — never silently.
4. Otherwise (routine execution inside an already-approved packet's
   own scope, checks, and owned paths) → **Worker/Reviewer**, no
   escalation at all.

## Real, standing invariant this criteria must never violate

**There is always a minimum of one real review before acceptance or
merge** (Owner instruction, 2026-09-08, reconfirmed against the
already-built state machine). This is not new policy — it was already
mechanically enforced before this document existed:
`_REVIEW_ROUTES`/`_CORRECTION_REVIEW_ROUTES` require a real
`Integration`/`ValidateOnly` review before any `IndependentImplementation`
review can route at all (`operational_state.py`), and both
`record_and_accept_packet` (M4.09) and `observe_merge` (M4.11) require a
real, named `Approve` review to exist. No tier — not even the Owner
acting through a delegated identity — may accept or merge a packet with
zero real reviews on record. A future ruling-loop implementation must
treat this as a hard floor, not a tunable.

## Owner-acceptance's own real criteria (already ruled, 2026-09-08)

Restated here since it is the concrete precedent for what "tier 2 may
self-grant" means in practice: the ruling loop (Architect tier) may
call `accept_packet` (M4.09) itself, without an Owner round-trip, once
**(a)** the packet's own real definition of done is met (its owned
paths' real checks pass, a real reviewer approved), **or** **(b)** any
real limitations are judged acceptable because the delivered
product/feature meets basic needs and those limitations are tracked on
a real backlog rather than silently dropped. Both still require the
minimum-one-review floor above; this criteria only ever narrows what
already passed review, it never substitutes for review.

## What this document deliberately does not do

No ruling-loop *implementation* packet is proposed here. Building
execution before this criteria was real would have meant guessing at
what it is allowed to decide — the same discipline this session applied
to the acceptance-criteria question before building M4.09.
