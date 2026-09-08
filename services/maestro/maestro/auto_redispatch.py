"""M4.04 — real auto-redispatch after a recovery-driven NeedsReplan.

Real replanning logic, not a reuse of two existing commands as-is:
`record_and_close_needs_replan` only cancels the old packet, it never
creates a replacement, and a real redispatch is structurally a new
`packet_id`/`packet_revision` — `packets`' own
`UNIQUE(run_id,work_item_id,packet_revision)` constraint and
`attempts`' 2-attempt cap mean the old packet's own id can never be
reused. This constructs a full new packet definition from the
cancelled packet's own real, already-stored facts (owned paths, checks,
branch, context policy — nothing re-typed or guessed), then closes the
old one and materializes the new one — the exact real pattern this
session's own manual redispatches used (CG-M4-19, CG-M4-20), now
triggered automatically instead of a human deciding to.
"""

from __future__ import annotations

from .dispatch_orchestrator import now_iso
from .operational_state import Actor, InvalidRecord, OperationalStateStore


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


def redispatch_after_needs_replan(
    store: OperationalStateStore,
    packet_id: str,
    expected_packet_version: int,
    new_packet_id: str,
    new_packet_revision: str,
    actor: Actor,
) -> dict:
    """Closes ``packet_id`` (must be real, currently `NeedsReplan`) and
    materializes ``new_packet_id`` as its real replacement, carrying
    forward every real fact the old packet's own row already has —
    never inventing owned paths, checks, or policy the old packet
    didn't already carry. Returns the new packet's real state.
    """
    old_packet = store.snapshot("Packet", packet_id)
    if old_packet is None:
        raise InvalidRecord(f"unknown packet: {packet_id}")

    now = now_iso()
    store.record_and_close_needs_replan(
        packet_id, expected_packet_version,
        _reason("REDISPATCH_AFTER_RECOVERY_TIMEOUT"),
        f"close-{packet_id}-for-{new_packet_id}", actor, now,
    )
    new_packet = store.materialize_packet(
        {
            "packet_id": new_packet_id,
            "run_id": old_packet["run_id"],
            "work_item_id": old_packet["work_item_id"],
            "packet_revision": new_packet_revision,
            "authority_reference": old_packet["authority_reference"],
            "base_commit": old_packet["base_commit"],
            "current_head": None,
            "expected_branch": old_packet["expected_branch"],
            "role_contract_reference": old_packet["role_contract_reference"],
            "sop_reference": old_packet["sop_reference"],
            "executor_class": old_packet["executor_class"],
            "integration_route": old_packet["integration_route"],
            "reviewer_route": old_packet["reviewer_route"],
            "owned_paths_json": old_packet["owned_paths_json"],
            "forbidden_paths_json": old_packet["forbidden_paths_json"],
            "checks_json": old_packet["checks_json"],
            "resource_claims_json": old_packet["resource_claims_json"],
            "context_policy_json": old_packet["context_policy_json"],
            "state": "Planned",
            "correction_count": 0,
        },
        f"materialize-{new_packet_id}", actor, now,
    )
    return new_packet
