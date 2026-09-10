# Owner Direction — Make Completion Closed and Learn From Rework

**Date:** 2026-09-02
**Status:** Accepted Owner direction
**Scope:** Maestro packet readiness, review/correction behavior, return routing,
automatic resumption, and process learning

## Direction

The M1 implementation work exposed too much elapsed time for too little accepted
output. A packet described broad proof with words such as `every`, but did not
carry the finite inventory that defined what `every` meant. Integration and
independent review then discovered different omissions at different times, and
the completion target appeared to move after delivery.

Maestro must prevent this pattern in the product, not rely on a future
Coordinator or agent remembering the conversation.

1. Before dispatch, a packet must carry a closed, numbered definition-of-done
   manifest. Every authoritative requirement and named proof maps to a stable
   item with an owner, check, expected result, and required evidence.
2. Universal or completion words such as `every`, `all`, `complete`, or
   `production-ready` are invalid unless the packet freezes the finite set or
   supplies an exact, reproducible enumeration rule and source digest.
3. The packet compiler/linter rejects missing coverage, ambiguous proof,
   infeasible ownership, incompatible gates, and packets too broad to correct
   locally. Structurally separable outcomes or incompatible owners, locks,
   routes, or review units must be split before dispatch.
4. A first full reviewer returns its complete finding set against the closed
   contract. A correction follow-up is limited to named findings, the
   correction-only diff, and directly affected consistency.
5. For a committed, in-scope result that can safely be reviewed, Maestro waits
   for both Integration and independent-review terminal findings before issuing
   the one permitted correction. Non-delivery and pre-review rejection classes
   continue to follow M0-D05 immediately.
6. Passing the frozen manifest and its approved gates is the definition of
   enough. A later improvement outside that contract becomes a successor
   learning item; it does not silently enlarge the current acceptance gate.
7. A contract defect, new failure class after correction, or exhausted
   correction returns to the Project Architect. Only a choice reserved by
   M0-D15 returns to the Owner.
8. Resolution creates a durable event. The Coordinator, and later the Maestro
   Development Manager, rereads authority and operational state, recomputes
   eligibility, and resumes the highest-ranked eligible work without requiring
   a new chat message.
9. Maestro records elapsed cycle time, wait time, review rounds, correction
   cause, late-discovered requirement class, and the reusable compiler,
   template, invariant, or role-policy change created from the lesson.

This direction tightens execution of the accepted design. It does not authorize
live-project testing, scripted end-to-end judgments, automatic merge,
production deployment, or autonomous successor milestones.
