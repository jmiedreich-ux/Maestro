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

**Delegation is this loop's own job** (Owner correction, 2026-09-08):
an earlier version of this module deferred worker dispatch as
"concurrency scope" and made it a separate operator command. That was
wrong — delegating an assigned packet to its agent is precisely what a
development manager *is*. `run_cycle` now picks up every real `Leased`
packet whose attempt is still `Planned` and launches its real
`DispatchOrchestrator` run on its own thread (`DispatchPool`), so one
blocking worker never stalls the cycle or the other packets.

**Still explicitly out of scope, disclosed:** *deciding* which packet
goes to which worker. The Project Architect claims packets (`maestro
claim-packet`) and thereby chooses what runs in parallel; the real
auto-scheduler designed at M0 (`agent-workforce-control-plane.md`) is
unbuilt in every milestone. This loop delegates what is already
assigned, it does not assign.

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

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Callable

from .attempt_onboarding import run_attempt
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
    delegated: list[str] = field(default_factory=list)
    timed_out: list[str] = field(default_factory=list)
    redispatched: list[str] = field(default_factory=list)
    reviewed: list[str] = field(default_factory=list)
    accepted: list[str] = field(default_factory=list)
    merged: list[str] = field(default_factory=list)
    notifications_delivered: int = 0


def _connection(config: RuntimeConfig) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0)


class DispatchPool:
    """Real, per-attempt worker threads. `DispatchOrchestrator.run()`
    blocks for a worker's entire real duration, so the loop must never
    call it inline — one slow packet would stall recovery, review, and
    every other packet. Each real attempt gets its own thread; the pool
    refuses to launch a second thread for an attempt it is already
    running, so repeated cycles never double-dispatch."""

    def __init__(self) -> None:
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()
        self.failures: dict[str, str] = {}

    def active(self) -> set[str]:
        with self._lock:
            for attempt_id, thread in list(self._threads.items()):
                if not thread.is_alive():
                    del self._threads[attempt_id]
            return set(self._threads)

    def launch(self, attempt_id: str, target: Callable[[], None]) -> bool:
        with self._lock:
            existing = self._threads.get(attempt_id)
            if existing is not None and existing.is_alive():
                return False

            def _run() -> None:
                try:
                    target()
                except Exception as error:  # a real worker failure must not kill the loop
                    self.failures[attempt_id] = f"{type(error).__name__}: {error}"

            thread = threading.Thread(target=_run, name=f"dispatch-{attempt_id}", daemon=True)
            self._threads[attempt_id] = thread
            thread.start()
            return True

    def join_all(self, timeout: float | None = None) -> None:
        for thread in list(self._threads.values()):
            thread.join(timeout)


def _undispatched_attempts(config: RuntimeConfig, run_id: str) -> list[dict]:
    """Real, read-only: every attempt still `Planned` on a real `Leased`
    packet in this run — that is, assigned by the Architect but not yet
    delegated to its agent."""
    connection = _connection(config)
    try:
        rows = connection.execute(
            "SELECT a.attempt_id, a.packet_id FROM attempts a "
            "JOIN packets p ON p.packet_id = a.packet_id "
            "WHERE p.run_id=? AND p.state='Leased' AND a.state='Planned' "
            "ORDER BY a.attempt_id",
            (run_id,),
        ).fetchall()
    finally:
        connection.close()
    return [{"attempt_id": str(row[0]), "packet_id": str(row[1])} for row in rows]


def _work_item(config: RuntimeConfig, work_item_id: str) -> dict | None:
    connection = _connection(config)
    try:
        row = connection.execute(
            "SELECT title, specialist_role, task_reference, input_contract_json, output_contract_json "
            "FROM work_items WHERE work_item_id=?",
            (work_item_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return {
        "title": str(row[0]), "specialist_role": str(row[1]), "task_reference": str(row[2]),
        "input_contract": json.loads(str(row[3])), "output_contract": json.loads(str(row[4])),
    }


def build_instructions(packet: dict, work_item: dict) -> str:
    """Real delegation brief, derived only from facts the store already
    holds — the work item's own title/contracts and the packet's own
    owned paths, forbidden paths, and checks. Nothing invented."""
    lines = [
        f"Task: {work_item['title']}",
        f"Role: {work_item['specialist_role']}",
        f"Reference: {work_item['task_reference']}",
        f"Contract in: {json.dumps(work_item['input_contract'], sort_keys=True)}",
        f"Contract out: {json.dumps(work_item['output_contract'], sort_keys=True)}",
        f"Role contract: {packet['role_contract_reference']}",
        f"SOP: {packet['sop_reference']}",
        f"You may only change these paths: {', '.join(packet['owned_paths_json'])}",
        f"You must not change these paths: {', '.join(packet['forbidden_paths_json'])}",
        f"These checks must pass: {', '.join(packet['checks_json'])}",
        "Commit your work when the checks pass. Do not merge.",
    ]
    return "\n".join(lines)


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
    executor_factory: Callable[[], object] | None = None, pool: DispatchPool | None = None,
) -> CycleReport:
    """One real, complete pass over a run's real packets: delegation,
    recovery, review progression, acceptance (per M4.16's own criteria),
    and merge -- then real notification delivery. Safe to call
    repeatedly; every step underneath is already idempotent/version-
    guarded.

    Pass ``executor_factory`` and ``pool`` to enable real delegation:
    every `Leased` packet whose attempt is still `Planned` is handed to
    its own real worker on its own thread. Without them the cycle only
    drives already-running work (used by tests that drive attempts
    themselves)."""
    report = CycleReport()

    if executor_factory is not None and pool is not None:
        running = pool.active()
        for candidate in _undispatched_attempts(config, run_id):
            if candidate["attempt_id"] in running:
                continue
            packet = store.snapshot("Packet", candidate["packet_id"])
            if packet is None:
                continue
            work_item = _work_item(config, packet["work_item_id"])
            if work_item is None:
                continue
            instructions = build_instructions(packet, work_item)
            request = {"attempt_id": candidate["attempt_id"], "instructions": instructions}
            launched = pool.launch(
                candidate["attempt_id"],
                lambda request=request: run_attempt(store, request, actor, executor=executor_factory()),
            )
            if launched:
                report.delegated.append(candidate["attempt_id"])

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
