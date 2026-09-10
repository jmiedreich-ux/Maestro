# Owner Direction — M1-02AR One-Time Final Correction

**Date:** 2026-09-02
**Status:** Accepted

The Owner authorizes one final, direct correction from exact M1-02AR head
`27e924f2871c026e8befc236f46025e57a9a7a77` solely to close the existing
`AR-P05` / `AR-R04` observable-wiring finding.

The correction may change only
`tests/m1_02/test_schema_and_records.py`. It must replace manually inserted
relation and `V24`/`V25` labels with evidence observed from the actual existing
route behavior. It may not change production code, schema, API, semantics,
dependencies, configuration, environment, authority, routes, or any other
proof requirement.

After the correction, run the focused proof, affected M1-02 suite, and normal
regressions. Integration and one independent reviewer verify only this named
finding, the correction diff, and directly affected consistency. They do not
restart general review. If the named proof passes, the Project Architect may
accept M1-02A/AR. Any failure, new finding, or required scope change returns to
the Project Architect; no further correction is authorized.

The unreleased M1-02AR2 replacement packet is withdrawn and grants no
implementation authority.
