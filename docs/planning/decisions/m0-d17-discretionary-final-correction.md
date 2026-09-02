# M0-D17 — Project-Architect Discretionary Final Correction

**Status:** Accepted under Owner direction on 2026-09-02
**Scope:** Future and superseding Maestro packets released after this decision
**Source:** [Owner direction — allow one discretionary final correction](../../../sources/planning/2026-09-02-discretionary-final-correction-direction.md)
**Amends:** [M0-D05](m0-d05-rework-review-and-escalation.md) and the
one-correction language in M0-D12/M0-D15/M0-D16 and their active role carriers

## Decision

The normal first targeted correction remains automatic for a committed,
in-scope result that fails a named frozen gate. After the correction and its
targeted Integration/review results, the Project Architect may authorize one
final targeted correction only when every eligibility condition below passes.

### Final-correction eligibility

1. Every remaining finding was already named against the same frozen proof IDs
   and has the same implementation-failure classification; no new failure class
   or proof obligation appeared.
2. The first correction contains its required source commit, remains inside
   owned paths, and contains no unrelated change.
3. The remaining fix is localized to the same owned paths and needs no changed
   architecture, schema, API, product behavior, authority, dependency,
   configuration, environment, security/data/credential/external-access
   boundary, lock, or any executor, implementation, Integration, review, or
   other execution route.
4. Integration and the targeted reviewer have returned terminal results with
   immutable evidence sufficient to judge the remaining work.
5. The Project Architect records the remaining finding IDs/proof IDs, exact
   correction range, bounded expected diff, and the reason the work is close
   enough that one final correction is proportionate.

Failure of any condition ends the current packet and requires Project Architect
rematerialization. A later reassignment or Coordinator takeover may occur only
under that superseding rematerialized packet. Owner involvement is required
only when the resolution crosses an M0-D15 reserved material choice.

### Final correction and hard stop

The final correction may change only the recorded expected paths and findings.
Its follow-up verifies those findings, the correction-only diff/evidence, and
directly affected consistency. It does not restart general discovery.

Two implementation corrections are the absolute packet maximum: one normal
targeted correction and, when explicitly authorized, one discretionary final
correction. Any remaining defect, new failure class, missing/changed contract,
scope breach, non-delivery, or failed final correction freezes the result and
returns it to the Project Architect.

### Frozen-packet compatibility

A packet released before this decision keeps the correction allowance frozen in
its approved manifest. M0-D17 applies only to a later release or a superseding
packet that explicitly names it. It cannot be used to add a correction to an
active packet retroactively.

## Required operational evidence

Maestro records `StandardCorrection` or `DiscretionaryFinalCorrection`, the
Project Architect authorization when applicable, all eligibility facts,
finding/proof IDs, exact base/head ranges, targeted review coverage, outcome,
and terminal return. Atlas reports the record read-only.

## Non-authorization

This decision grants no third correction, general review restart, packet-scope
expansion, automatic merge, deployment, live-project action, external access,
or autonomous successor work.
