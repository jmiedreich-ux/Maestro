# M0-D09 — VennueSign Fresh Reporting Start

**Status:** Accepted  
**Scope:** VennueSign's first Maestro operational reporting view and its
relationship to the separate Atlas repository.

## Decision

VennueSign starts with a fresh Maestro reporting view. No Atlas application
code, stored state, control behavior, or legacy data model is migrated into
that first view.

The new view reads only Maestro's local operational service. It receives live
updates from Maestro's event stream and uses a snapshot refresh when it
reconnects. It is reporting-only: it cannot dispatch, stop, retry, reroute,
approve, merge, edit project records, or write directly to the database.

## Boundary

- Atlas remains a separate repository and historical source to be assessed or
  archived under the archive policy.
- VennueSign's code, planning, and engineering history remain authoritative
  in VennueSign.
- Maestro owns the operational state and the local read-only service contract.
- The first reporting view runs Linux-first with Maestro; no public service or
  Windows dependency is introduced by this decision.

A later reuse of a specific Atlas idea or component requires an explicit
decision and a clean compatibility/security review. It is not implied by the
existence of the Atlas repository.

## Consequence

VennueSign registration will define the reporting data it needs from Maestro
without inheriting legacy Atlas assumptions. The archive inventory happens
during that registration work, not as a prerequisite for Maestro M0.
