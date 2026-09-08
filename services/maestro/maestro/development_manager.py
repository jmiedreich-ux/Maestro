"""The real M4 driver loop — the missing piece.

M4.01-M4.14 built every individual real action (detect staleness,
timeout, redispatch, reconstruct coverage, route reviews, accept,
merge, notify) but nothing called them on its own. M4's own stated
goal was a *persistent* loop replacing the human standing in for
automation — a toolbox of correct, tested functions does not meet that
goal by itself. `run_cycle` is the real, single-pass driver: run it
repeatedly (a real scheduler, a cron, a `while True: sleep(...)`) and a
run's packets progress through recovery, review, acceptance, and merge
without a human invoking each step.

**Explicitly out of scope, disclosed, not silently assumed:** this
loop does not claim new packets or launch new `DispatchOrchestrator`
attempts. `DispatchOrchestrator.run()` blocks for an attempt's entire
real duration; running several concurrently is a real concurrency
design (a thread/process per attempt, or a task queue) that deserves
its own real decision, not a rushed addition here. This loop picks up
from a packet already `Leased`+dispatched (M3's own existing manual
claim/dispatch) through to `Merged`.

Every real review this loop records is **mechanical** and only ever
`Approve`, gated on `evaluate_review_readiness`'s own real `ready`
result. **Found while building this:** `_validate_review_coverage`
unconditionally requires `ready=True` for *any* review submission
(`Integration` included), so a `RequestChanges` review can never be
produced from a coverage blocker at all — the store would reject the
attempt outright. `RequestChanges` genuinely requires a human/AI
reviewer's own judgment on otherwise-ready coverage, which is real,
disclosed, out of this loop's mechanical scope; when coverage is not
ready, this loop only notifies (`notify_coverage_not_ready`) and
leaves the packet in `AwaitingIntegration` for a human.

Owner-acceptance follows M4.16's own already-ruled criterion (a): the
packet's real definition of done is met (an Initial, non-corrected
attempt reached a real `Approve`). Corrected packets are skipped here,
not silently mis-accepted — M4.09's own disclosed M1 limitation
(`correction_number==0` required) means they can never be accepted
through today's `accept_packet` at all; they surface for a human via
the real `AwaitingArchitect`/`AwaitingOwner` notification trail
already in place, not this loop.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from .config import RuntimeConfig
from .coverage_reconstruction import reconstruct_coverage
from .merge_observation import observe_merge
from .notification_delivery import deliver_pending
from .notification_triggers import notify_coverage_not_ready, notify_merge_ready
from .operational_state import Actor, OperationalStateStore
from .owner_acceptance import accept_packet
from .review_dispatch import (
    route_correction_review,
    route_independent_implementation,
    route_integration_validate_only,
)
from .auto_redispatch import redispatch_after_needs_replan
from .auto_timeout import timeout_all_stale_attempts
from .staleness_detector import find_stale_attempts


@dataclass
class CycleReport:
    timed_out: list[str] = field(default_factory=list)
    redispatched: list[str] = field(default_factory=list)
    reviewed: list[str] = field(default_factory=list)
    accepted: list[str] = field(default_factory=list)
    merged: list[str] = field(default_factory=list)
    notifications_delivered: int = 0


def _connection(config: RuntimeConfig) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0)


def _packet_ids_in_state(config: RuntimeConfig, run_id: str, state: str) -> list[str]:
    connection = _connection(config)
    try:
        rows = connection.execute(
            "SELECT packet_id FROM packets WHERE run_id=? AND state=? ORDER BY packet_id",
            (run_id, state),
        ).fetchall()
    finally:
        connection.close()
    return [str(row[0]) for row in rows]


def _succeeded_attempt(config: RuntimeConfig, packet_id: str, attempt_number: int) -> dict | None:
    connection = _connection(config)
    try:
        row = connection.execute(
            "SELECT attempt_id, result_commit FROM attempts "
            "WHERE packet_id=? AND attempt_number=? AND state='Succeeded'",
            (packet_id, attempt_number),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return {"attempt_id": str(row[0]), "result_commit": str(row[1])}


def _review(
    config: RuntimeConfig, packet_id: str, review_kind: str, head_commit: str, correction_number: int,
) -> dict | None:
    connection = _connection(config)
    try:
        row = connection.execute(
            "SELECT review_id, result FROM reviews WHERE packet_id=? AND review_kind=? "
            "AND head_commit=? AND correction_number=?",
            (packet_id, review_kind, head_commit, correction_number),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return {"review_id": str(row[0]), "result": str(row[1])}


def _approve_review(config: RuntimeConfig, packet_id: str) -> dict | None:
    connection = _connection(config)
    try:
        row = connection.execute(
            "SELECT review_id FROM reviews WHERE packet_id=? AND review_kind='IndependentImplementation' "
            "AND result='Approve' AND correction_number=0",
            (packet_id,),
        ).fetchone()
    finally:
        connection.close()
    return None if row is None else {"review_id": str(row[0])}


def _acceptance(config: RuntimeConfig, packet_id: str) -> dict | None:
    connection = _connection(config)
    try:
        row = connection.execute(
            "SELECT acceptance_id, exact_head FROM acceptance_records "
            "WHERE packet_id=? AND subject_type='Packet' AND decision='Accepted' AND sequence_number=1",
            (packet_id,),
        ).fetchone()
    finally:
        connection.close()
    return None if row is None else {"acceptance_id": str(row[0]), "exact_head": str(row[1])}


def progress_review(
    store: OperationalStateStore, config: RuntimeConfig, *, repository_path: str,
    packet_id: str, run_id: str, actor: Actor, now: str, reconstruction_commands: list[str],
) -> str | None:
    """Real, mechanical review progression for one real `AwaitingIntegration`
    packet. Returns what happened (``"RoutedIntegration"``, ``"Approved"``,
    ``"CoverageNotReady"``, or ``None`` if there was nothing real to do
    yet), never guesses.

    **Real, found-while-building constraint:** `_validate_review_coverage`
    unconditionally requires `ready=True` for *any* review submission,
    `Integration` included -- not only the final `Approve`/`RequestChanges`
    choice. A packet whose coverage is not ready (an out-of-scope path, a
    failing check) cannot have *any* real review recorded against it at
    all, so this loop can never mechanically produce a real
    `RequestChanges` from a coverage blocker -- that path genuinely
    requires a human/AI reviewer's own judgment on *ready* coverage for
    some other reason, which is real, disclosed, out of this loop's own
    mechanical scope. When coverage is not ready, this only notifies and
    stops -- it does not invent a review the store would reject anyway.
    """
    packet = store.snapshot("Packet", packet_id)
    if packet is None or packet["state"] not in ("AwaitingIntegration", "AwaitingReview"):
        return None
    is_correction = packet["correction_count"] == 1
    attempt_number = 2 if is_correction else 1
    attempt = _succeeded_attempt(config, packet_id, attempt_number)
    if attempt is None:
        return None
    head = attempt["result_commit"]
    base = None
    if is_correction:
        initial = _succeeded_attempt(config, packet_id, 1)
        base = initial["result_commit"] if initial else None

    coverage = reconstruct_coverage(
        packet, repository=repository_path, head=head, slice_id=f"MB-{run_id}-{packet_id}-cycle",
        reconstruction_commands=reconstruction_commands, base=base,
    )
    if not coverage["result"]["ready"]:
        notify_coverage_not_ready(store, run_id=run_id, packet_id=packet_id, actor=actor, now=now)
        return "CoverageNotReady"

    integration_number = 1 if is_correction else 0
    integration = _review(config, packet_id, "Integration", head, integration_number)
    if integration is None:
        if is_correction:
            route_correction_review(
                store, packet_id, packet["version"], coverage, attempt["attempt_id"],
                "development-manager-loop-integration", f"review-integration-{attempt['attempt_id']}",
                "Integration", "ValidateOnly", actor,
            )
        else:
            route_integration_validate_only(
                store, packet_id, packet["version"], coverage, attempt["attempt_id"],
                "development-manager-loop-integration", f"review-integration-{attempt['attempt_id']}", actor,
            )
        return "RoutedIntegration"

    implementation_number = 1 if is_correction else 0
    existing = _review(config, packet_id, "IndependentImplementation", head, implementation_number)
    if existing is not None:
        return None

    packet = store.snapshot("Packet", packet_id)
    review_id = f"review-independent-{attempt['attempt_id']}"
    if is_correction:
        route_correction_review(
            store, packet_id, packet["version"], coverage, attempt["attempt_id"],
            "development-manager-loop-independent", review_id, "IndependentImplementation", "Approve", actor,
        )
    else:
        route_independent_implementation(
            store, packet_id, packet["version"], coverage, attempt["attempt_id"],
            "development-manager-loop-independent", review_id, actor, result="Approve",
        )
    notify_merge_ready(store, run_id=run_id, packet_id=packet_id, actor=actor, now=now)
    return "Approved"


def run_cycle(
    store: OperationalStateStore, config: RuntimeConfig, *, repository_path: str, run_id: str,
    default_branch: str, actor: Actor, now: str, reconstruction_commands: list[str],
) -> CycleReport:
    """One real, complete pass over a run's real packets: recovery,
    review progression, acceptance (per M4.16's own criteria), and
    merge -- then real notification delivery. Safe to call repeatedly;
    every step underneath is already idempotent/version-guarded."""
    report = CycleReport()

    stale = find_stale_attempts(config, now)
    for outcome in timeout_all_stale_attempts(store, stale, actor):
        if outcome.applied:
            report.timed_out.append(outcome.packet_id)

    for packet_id in _packet_ids_in_state(config, run_id, "NeedsReplan"):
        old_packet = store.snapshot("Packet", packet_id)
        if old_packet is None or old_packet["run_id"] != run_id:
            continue
        new_packet_id = f"{packet_id}-replan-{old_packet['version']}"
        new_revision = f"{old_packet['packet_revision']}-r{old_packet['version']}"
        redispatch_after_needs_replan(
            store, packet_id, old_packet["version"], new_packet_id, new_revision, actor,
        )
        report.redispatched.append(new_packet_id)

    reviewable = (
        _packet_ids_in_state(config, run_id, "AwaitingIntegration")
        + _packet_ids_in_state(config, run_id, "AwaitingReview")
    )
    for packet_id in reviewable:
        outcome = progress_review(
            store, config, repository_path=repository_path, packet_id=packet_id,
            run_id=run_id, actor=actor, now=now, reconstruction_commands=reconstruction_commands,
        )
        if outcome:
            report.reviewed.append(packet_id)

    for packet_id in _packet_ids_in_state(config, run_id, "MergeReady"):
        packet = store.snapshot("Packet", packet_id)
        if packet is None or packet["correction_count"] != 0:
            continue  # real, disclosed M1 limitation (M4.09) -- left for a human
        approve = _approve_review(config, packet_id)
        initial = _succeeded_attempt(config, packet_id, 1)
        if approve is None or initial is None:
            continue
        accept_packet(
            store, packet_id, packet["version"], f"acceptance-{packet_id}", "Owner",
            "development-manager-loop", initial["result_commit"], approve["review_id"], actor,
        )
        report.accepted.append(packet_id)

    for packet_id in _packet_ids_in_state(config, run_id, "AwaitingOwner"):
        packet = store.snapshot("Packet", packet_id)
        acceptance = _acceptance(config, packet_id)
        if packet is None or acceptance is None:
            continue
        observe_merge(
            store, packet_id, packet["version"],
            merge_observation_id=f"merge-observation-{packet_id}",
            acceptance_id=acceptance["acceptance_id"], repository_path=repository_path,
            repository_reference=run_id, default_branch=default_branch,
            accepted_head=acceptance["exact_head"],
            source_reference=f"refs/heads/{packet['expected_branch']}",
            delegation_reference="development-manager-loop", actor=actor,
        )
        report.merged.append(packet_id)

    delivered = deliver_pending(store, config, run_id, actor, now)
    report.notifications_delivered = len(delivered)
    return report
