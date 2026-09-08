"""M4.06/M4.07/M4.08 — real review dispatch.

Wires M4.05's real coverage (`coverage_reconstruction.py`) into the
already-real, already-tested `record_and_route_review`/`record_and_
route_correction_review`. Scope, deliberately minimal (per the packet
breakdown): the caller supplies the review's own real `result` and
`findings` — this does not auto-generate a finding from a failing
check (that is real, separate fault-triage logic this session did by
hand once for CG-M4-19's own correction, out of scope for these three
small wiring packets).
"""

from __future__ import annotations

from .dispatch_orchestrator import now_iso
from .operational_state import Actor, OperationalStateStore

_REVIEWER_ROLE = {
    "Integration": "IntegrationAgent",
    "IndependentImplementation": "IndependentImplementationReviewer",
}


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


def _review_payload(
    *, review_id: str, attempt_id: str | None, review_kind: str, reviewer_instance: str,
    coverage: dict, result: str, findings: list[dict], correction_number: int,
) -> dict:
    real_result = coverage["result"]
    return {
        "review_id": review_id,
        "attempt_id": attempt_id,
        "review_kind": review_kind,
        "reviewer_role": _REVIEWER_ROLE[review_kind],
        "reviewer_instance": reviewer_instance,
        "base_commit": real_result["resolved_base"],
        "head_commit": real_result["resolved_head"],
        "result": result,
        "findings_json": findings,
        "coverage_json": coverage,
        "correction_number": correction_number,
    }


def route_integration_validate_only(
    store: OperationalStateStore, packet_id: str, expected_packet_version: int,
    coverage: dict, attempt_id: str | None, reviewer_instance: str, review_id: str,
    actor: Actor,
) -> dict:
    """M4.06 — the real `Integration`/`ValidateOnly` review
    `_REVIEW_ROUTES` requires before any `IndependentImplementation`
    review can route at all (`AwaitingIntegration -> AwaitingReview`)."""
    review = _review_payload(
        review_id=review_id, attempt_id=attempt_id, review_kind="Integration",
        reviewer_instance=reviewer_instance, coverage=coverage, result="ValidateOnly",
        findings=[], correction_number=0,
    )
    return store.record_and_route_review(
        packet_id, expected_packet_version, review,
        _reason("MECHANICAL_GRADING_PASSED"), f"review-{review_id}", actor, now_iso(),
    )


def route_independent_implementation(
    store: OperationalStateStore, packet_id: str, expected_packet_version: int,
    coverage: dict, attempt_id: str | None, reviewer_instance: str, review_id: str,
    actor: Actor, *, result: str = "Approve", findings: list[dict] | None = None,
) -> dict:
    """M4.07 — the real `IndependentImplementation` review
    (`AwaitingReview -> MergeReady` on `Approve`)."""
    review = _review_payload(
        review_id=review_id, attempt_id=attempt_id, review_kind="IndependentImplementation",
        reviewer_instance=reviewer_instance, coverage=coverage, result=result,
        findings=findings or [], correction_number=0,
    )
    return store.record_and_route_review(
        packet_id, expected_packet_version, review,
        _reason("INDEPENDENT_REVIEW_COMPLETE"), f"review-{review_id}", actor, now_iso(),
    )


def route_correction_review(
    store: OperationalStateStore, packet_id: str, expected_packet_version: int,
    coverage: dict, attempt_id: str | None, reviewer_instance: str, review_id: str,
    review_kind: str, result: str, actor: Actor, *, findings: list[dict] | None = None,
) -> dict:
    """M4.08 — the real correction-path review (`record_and_route_
    correction_review`), for either `review_kind`. The caller must have
    built ``coverage`` with M4.05's own `base=` override set to the
    Initial attempt's real `result_commit` — this function does not
    re-derive it."""
    review = _review_payload(
        review_id=review_id, attempt_id=attempt_id, review_kind=review_kind,
        reviewer_instance=reviewer_instance, coverage=coverage, result=result,
        findings=findings or [], correction_number=1,
    )
    return store.record_and_route_correction_review(
        packet_id, expected_packet_version, review,
        _reason("CORRECTION_REVIEW_COMPLETE"), f"correction-review-{review_id}", actor, now_iso(),
    )
