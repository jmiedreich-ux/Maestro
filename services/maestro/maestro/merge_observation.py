"""M4.11 (I2) — real observation wiring.

Calls `merge_executor.perform_merge` (I1) and then the already-real,
already-tested `record_and_observe_merge` immediately after, instead
of a human running the merge and then hand-typing the observation (as
done for CG-M4-19, this doc's own commits, and every merge this
session before this).

The merge executor is definitionally a `DelegatedIdentity` per
`merge_observations.performed_by_authority`'s own real constraint —
this module always records `performed_by_authority="DelegatedIdentity"`
with a real, non-null `delegation_reference` naming the service
account and the real authorization this module's own caller acted
under; a human directly running a merge is a separate, still-manual
path this module does not cover.
"""

from __future__ import annotations

from .dispatch_orchestrator import now_iso
from .merge_executor import perform_merge
from .operational_state import Actor, InvalidRecord, OperationalStateStore


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


def observe_merge(
    store: OperationalStateStore,
    packet_id: str,
    expected_packet_version: int,
    *,
    merge_observation_id: str,
    acceptance_id: str,
    repository_path: str,
    repository_reference: str,
    default_branch: str,
    accepted_head: str,
    source_reference: str,
    delegation_reference: str,
    performed_by_reference: str = "maestro-merge-service-account",
    actor: Actor,
    reason_code: str = "AUTOMATIC_MERGE",
) -> dict:
    """Performs the real merge (I1), then records the real observation
    against the packet's own real, materialized `run_id` — pulled from
    the packet's current snapshot, not passed in, so this can never
    disagree with the store's own real fact."""
    packet = store.snapshot("Packet", packet_id)
    if packet is None:
        raise InvalidRecord("unknown packet")

    acceptance = store.snapshot("Acceptance", acceptance_id)
    if acceptance is None or acceptance["exact_head"] != accepted_head:
        # Real, cheap pre-check before any real git write: the store
        # itself enforces this exact equality (see
        # `record_and_observe_merge`'s own acceptance-lookup guard), but
        # checking here first means a bad `accepted_head` never causes a
        # real (wasted, or worse, partially-applied) merge attempt.
        raise InvalidRecord(
            "merge observation accepted_head does not match the acceptance record exact_head"
        )

    merge_commit = perform_merge(repository_path, default_branch, accepted_head)

    merge_observation = {
        "merge_observation_id": merge_observation_id,
        "run_id": packet["run_id"],
        "packet_id": packet_id,
        "acceptance_id": acceptance_id,
        "repository_reference": repository_reference,
        "default_branch": default_branch,
        "accepted_head": accepted_head,
        "merge_commit": merge_commit,
        "source_kind": "Git",
        "source_reference": source_reference,
        "performed_by_authority": "DelegatedIdentity",
        "performed_by_reference": performed_by_reference,
        "delegation_reference": delegation_reference,
        "review_coverage_json": None,
    }
    return store.record_and_observe_merge(
        packet_id, expected_packet_version, merge_observation,
        _reason(reason_code), f"observe-merge-{merge_observation_id}", actor, now_iso(),
    )
