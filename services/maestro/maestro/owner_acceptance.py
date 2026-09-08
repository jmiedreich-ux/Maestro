"""M4.09 — real Owner-acceptance command wiring.

`record_and_accept_packet` is real and already tested, but had zero
real callers anywhere in this codebase before this — not even a CLI
command. This exposes it as a real, callable function; per the Owner's
own 2026-09-08 ruling (see `m4-development-manager-roadmap.md`), Owner
acceptance is real 90%-tier scope the ruling loop may grant itself once
the packet's own real definition of done is met, or its limitations
are judged acceptable and tracked on a real backlog — this module
makes the real command reachable, it does not itself decide who calls
it or under what real criteria (that judgment belongs to M4.16's own
criteria, not this wiring).

Real, checked shape — `review_coverage_json` for an acceptance is
**not** M4.05's `"review-readiness-coverage"` wrapper: it is a bare
reference, `{"kind": "acceptance-review-coverage", "review_id": ...}`,
which `record_and_accept_packet` looks up directly and requires to
name a real `IndependentImplementation`/`Approve` review with
`correction_number == 0`.

**Real, pre-existing M1 limitation, disclosed, not worked around:**
that `correction_number == 0` check is unconditional — a packet that
went through even one real correction (M4.08) can never be accepted
through `record_and_accept_packet` as it exists today, since its own
real Approve review always carries `correction_number == 1`. This is
an existing gap in already-shipped M1 code, out of scope for M4 (which
wires to existing commands, not new M1 logic) to silently work around.
`accept_packet` below will honestly raise whatever real `InvalidRecord`
the store itself raises for such a packet — it does not attempt a
workaround.
"""

from __future__ import annotations

from .dispatch_orchestrator import now_iso
from .operational_state import Actor, OperationalStateStore


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


def accept_packet(
    store: OperationalStateStore,
    packet_id: str,
    expected_packet_version: int,
    acceptance_id: str,
    required_authority: str,
    authority_reference: str,
    exact_head: str,
    approve_review_id: str,
    actor: Actor,
    *,
    reason_code: str = "DEFINITION_OF_DONE_MET",
) -> dict:
    """``exact_head`` must be the real, Succeeded *Initial* attempt's
    own `result_commit` — `record_and_accept_packet` checks this
    unconditionally, even for a packet with a real correction attempt.
    ``approve_review_id`` is the real `review_id` of the packet's own
    `IndependentImplementation`/`Approve` review (`correction_number`
    must be 0 — see this module's own doc comment).
    """
    acceptance = {
        "acceptance_id": acceptance_id,
        "subject_type": "Packet",
        "subject_id": packet_id,
        "packet_id": packet_id,
        "run_id": None,
        "sequence_number": 1,
        "supersedes_acceptance_id": None,
        "required_authority": required_authority,
        "decision": "Accepted",
        "authority_reference": authority_reference,
        "exact_head": exact_head,
        "review_coverage_json": {"kind": "acceptance-review-coverage", "review_id": approve_review_id},
        "reason_payload_json": _reason(reason_code),
    }
    return store.record_and_accept_packet(
        packet_id, expected_packet_version, acceptance,
        _reason(reason_code), f"accept-{acceptance_id}", actor, now_iso(),
    )
