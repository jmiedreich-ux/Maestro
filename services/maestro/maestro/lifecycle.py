"""Pure Alpha-02 lifecycle grading for controlled synthetic executor facts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .packet_contract import ApprovedPacket
from .synthetic_discovery import AREAS


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


@dataclass(frozen=True)
class LifecycleDecision:
    """The one terminal handoff the wrapper may record for a packet attempt."""

    status: str
    handoff_kind: str
    reason: str


def grade_discovery(inventory: Mapping[str, object]) -> LifecycleDecision:
    """Grade a fully-normalised synthetic discovery inventory.

    Before any decision is returned the inventory is validated against the
    canonical schema imported from :mod:`synthetic_discovery`:

    * Top-level keys are exactly ``areas``, ``summary``, ``reviewable``.
    * ``reviewable`` is a ``bool``.
    * ``areas`` contains exactly the seven area names declared in ``AREAS``,
      each holding exactly that area's declared leaves.
    * Every leaf is a ``Mapping`` whose ``status`` is one of
      ``"confirmed"``, ``"missing"``, ``"conflicting"`` and whose keys
      match the shape for that status
      (confirmed: ``status`` + ``value``;
       missing: ``status`` only;
       conflicting: ``status`` + ``observed_values``).
    * ``summary`` equals the counts derived from the 29 leaves.
    * ``reviewable`` equals ``missing == 0 and conflicting == 0``.

    Any mismatch raises ``ValueError``.  On a valid inventory the existing
    decision / reason logic applies.
    """
    # 1. Top-level key check
    expected_keys = frozenset(("areas", "summary", "reviewable"))
    if not isinstance(inventory, Mapping) or set(inventory.keys()) != expected_keys:
        raise ValueError("inventory top-level keys must be areas, summary, reviewable")

    reviewable: Any = inventory["reviewable"]
    areas: Any = inventory["areas"]
    summary: Any = inventory["summary"]

    if not isinstance(reviewable, bool):
        raise ValueError("reviewable must be a bool")
    if not isinstance(areas, Mapping):
        raise ValueError("'areas' must be a Mapping")

    # 2. Validate every area + leaf against the AREAS schema
    if set(areas.keys()) != {a for a, _ in AREAS}:
        raise ValueError("areas must contain exactly the seven declared area names")

    missing_paths: list[str] = []
    conflicting_paths: list[str] = []
    confirmed_count = 0

    for area_name, leaves_tuple in AREAS:
        area_obj: Any = areas.get(area_name)
        if not isinstance(area_obj, Mapping):
            raise ValueError(f"area '{area_name}' must be a Mapping")
        expected_leaves = {ln for ln, _ in leaves_tuple}
        if set(area_obj.keys()) != expected_leaves:
            raise ValueError(f"area '{area_name}' leaves mismatch")

        for leaf_name, _ltype in leaves_tuple:
            leaf_obj: Any = area_obj.get(leaf_name)
            if not isinstance(leaf_obj, Mapping):
                raise ValueError(f"leaf '{area_name}.{leaf_name}' must be a Mapping")
            status: Any = leaf_obj.get("status")
            if status == "confirmed":
                if set(leaf_obj.keys()) != {"status", "value"}:
                    raise ValueError(
                        f"confirmed leaf {area_name}.{leaf_name} keys must be "
                        "{{status, value}}"
                    )
                confirmed_count += 1
            elif status == "missing":
                if set(leaf_obj.keys()) != {"status"}:
                    raise ValueError(
                        f"missing leaf {area_name}.{leaf_name} keys must be "
                        "{{status}}"
                    )
                missing_paths.append(f"{area_name}.{leaf_name}")
            elif status == "conflicting":
                if set(leaf_obj.keys()) != {"status", "observed_values"}:
                    raise ValueError(
                        f"conflicting leaf {area_name}.{leaf_name} keys must "
                        "be {{status, observed_values}}"
                    )
                # Validate observed_values: non-string sequence, >= 2 distinct
                observed: Any = leaf_obj.get("observed_values")
                if isinstance(observed, str):
                    raise ValueError(
                        f"conflicting leaf {area_name}.{leaf_name} "
                        "observed_values must not be a string"
                    )
                if not isinstance(observed, (list, tuple)):
                    raise ValueError(
                        f"conflicting leaf {area_name}.{leaf_name} "
                        "observed_values must be a list or tuple"
                    )
                if len(observed) < 2:
                    raise ValueError(
                        f"conflicting leaf {area_name}.{leaf_name} "
                        "observed_values must have >= 2 entries"
                    )
                # Distinctness check that tolerates unhashable elements (lists)
                has_distinct = False
                for i in range(len(observed)):
                    for j in range(i + 1, len(observed)):
                        if observed[i] != observed[j]:
                            has_distinct = True
                            break
                    if has_distinct:
                        break
                if not has_distinct:
                    raise ValueError(
                        f"conflicting leaf {area_name}.{leaf_name} "
                        "observed_values must contain >= 2 distinct values"
                    )
                conflicting_paths.append(f"{area_name}.{leaf_name}")
            else:
                raise ValueError(
                    f"leaf {area_name}.{leaf_name} has invalid status {status!r}"
                )

    # 3. Cross-check summary and reviewable against derived counts
    total = confirmed_count + len(missing_paths) + len(conflicting_paths)
    if total != 29:
        raise ValueError(f"29 leaves required, got {total}")

    expected_summary = {
        "confirmed": confirmed_count,
        "missing": len(missing_paths),
        "conflicting": len(conflicting_paths),
    }
    if not isinstance(summary, Mapping) or dict(summary) != expected_summary:
        raise ValueError("summary counts do not match leaf statuses")

    expected_reviewable = len(missing_paths) == 0 and len(conflicting_paths) == 0
    if reviewable != expected_reviewable:
        raise ValueError(
            f"reviewable={reviewable} but derived={expected_reviewable}"
        )

    # 4. Return the existing decision / reason
    if reviewable:
        return LifecycleDecision(
            AWAITING_REVIEW, "IndependentReview",
            "complete synthetic discovery inventory awaits review",
        )

    parts: list[str] = ["incomplete synthetic discovery"]
    if missing_paths:
        parts.append(f"missing: {', '.join(missing_paths)}")
    if conflicting_paths:
        parts.append(f"conflicting: {', '.join(conflicting_paths)}")

    return LifecycleDecision(REJECTED, "CoordinatorEscalation", "; ".join(parts))


def grade_result(packet: ApprovedPacket, result: SyntheticWorkerResult) -> LifecycleDecision:
    """Apply M0-D05 mechanically, without choosing product or design work."""
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


def _in_scope(changed_paths: Sequence[str], owned_paths: Sequence[str]) -> bool:
    return all(any(path == owned or path.startswith(f"{owned}/") for owned in owned_paths) for path in changed_paths)
