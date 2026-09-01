"""Lifecycle grading for controlled synthetic executor facts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .packet_contract import ApprovedPacket


AWAITING_REVIEW = "AwaitingReview"
REJECTED = "Rejected"
CORRECTION_ELIGIBLE = "CorrectionEligible"


@dataclass(frozen=True)
class SyntheticWorkerResult:
    """Controlled fixture result; it is not a real agent or subprocess result."""

    exit_code: int
    commit: str | None
    scoped_diff: tuple[str, ...]
    gate_results: Mapping[str, bool]
    violations: tuple[str, ...]
    log: str
    inventory: dict[str, Any] | None = None
    proposed_binding: dict[str, Any] | None = None
    fixture_digest: str | None = None


@dataclass(frozen=True)
class LifecycleDecision:
    """The one terminal handoff the wrapper may record for a packet attempt."""

    status: str
    handoff_kind: str
    reason: str


def grade_result(packet: ApprovedPacket, result: SyntheticWorkerResult) -> LifecycleDecision:
    """Apply M0-D05 mechanically, without choosing product or design work."""
    if packet.is_discovery:
        return _grade_discovery(packet, result)
    return _grade_alpha02(packet, result)


def _grade_alpha02(packet: ApprovedPacket, result: SyntheticWorkerResult) -> LifecycleDecision:
    if not result.commit:
        return LifecycleDecision(REJECTED, "CoordinatorEscalation", "missing required commit")
    if not result.scoped_diff:
        return LifecycleDecision(REJECTED, "CoordinatorEscalation", "missing scoped diff")
    if result.violations:
        return LifecycleDecision(
            REJECTED,
            "CoordinatorEscalation",
            f"dependency/configuration/placeholder violation: {result.violations[0]}",
        )
    if not _in_scope(result.scoped_diff, packet.owned_paths):
        return LifecycleDecision(REJECTED, "CoordinatorEscalation", "out-of-scope result")

    failed_gates = [gate.name for gate in packet.gates if not result.gate_results.get(gate.name, False)]
    if failed_gates:
        return LifecycleDecision(
            CORRECTION_ELIGIBLE,
            "TargetedCorrection",
            f"one eligible targeted correction: named gate failed: {failed_gates[0]}",
        )
    return LifecycleDecision(AWAITING_REVIEW, "IndependentReview", "valid result awaits independent review")


def _grade_discovery(packet: ApprovedPacket, result: SyntheticWorkerResult) -> LifecycleDecision:
    if result.inventory is not None and result.inventory.get("reviewable", False):
        return LifecycleDecision(AWAITING_REVIEW, "IndependentReview", "complete synthetic discovery inventory awaits review")
    reason_parts = result.log if result.log else "missing or conflicting facts"
    return LifecycleDecision(REJECTED, "CoordinatorEscalation", reason_parts)


def _in_scope(changed_paths: Sequence[str], owned_paths: Sequence[str]) -> bool:
    return all(any(path == owned or path.startswith(f"{owned}/") for owned in owned_paths) for path in changed_paths)
