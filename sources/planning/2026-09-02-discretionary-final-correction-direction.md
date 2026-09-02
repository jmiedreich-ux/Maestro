# Owner Direction — Allow One Discretionary Final Correction

**Date:** 2026-09-02
**Status:** Accepted Owner direction
**Scope:** Maestro correction judgment after the normal targeted correction

## Direction

A universal one-correction limit is too rigid when committed, in-scope work is
clearly close. Maestro must retain a hard loop boundary while allowing the
Project Architect to distinguish a small remaining implementation defect from a
packet or architecture failure.

1. The first targeted correction remains the normal correction for committed,
   in-scope work failing a named gate.
2. After its targeted Integration/review results are complete, the Project
   Architect may authorize one final correction only when all remaining
   findings are the same failure class and frozen proof IDs, the change remains
   small and correction-only inside the existing owned paths, and no
   architecture, schema, API, authority, dependency, configuration, security,
   external-access, or scope change is required.
3. The Project Architect records the exact remaining findings, why the work is
   close, and why one final correction is proportionate. This is routine
   delegated judgment; it is not an Owner decision.
4. The final correction receives targeted verification only. It cannot add
   scope, proof obligations, or unrelated cleanup.
5. There is a hard maximum of two implementation corrections per packet. A new
   failure class, failed/out-of-scope correction, non-delivery, contract defect,
   or failure after the final correction ends the current packet and requires
   Project Architect rematerialization. Any later reassignment or takeover
   operates only under that superseding packet.
6. The Owner is involved only if resolution itself crosses an M0-D15 reserved
   material boundary.

Already released packets retain their frozen correction contract. This rule
applies when a new or superseding packet is released under the amended policy;
it cannot silently change an active packet's definition of done.
