"""M4.01 — real dispatch orchestration.

No code anywhere before this owned both a real `ExecutorAdapter`
(`executor.py`) and the real attempt/lease version state
`operational_state.py`'s `start_attempt_execution`/
`heartbeat_attempt_execution`/`finish_attempt_execution` require —
every real dispatch this session (CG-M4-19, CG-M4-20) glued the two
together by hand, once, in a throwaway script. `DispatchOrchestrator`
is that glue, built once and reusable.

Real scope, twice corrected before this was written (see
`docs/planning/m4-packet-breakdown.md`'s own M4.01 entry): submit to
the executor, heartbeat on a real interval while it runs, and — the
gap the second correction caught — determine a real outcome and call
`finish_attempt_execution` on normal completion. It does **not** handle
a stale/silent worker; that is real recovery's own separate concern
(M4.02/M4.03), which races safely against this loop via the same
optimistic-version checks `operational_state.py` already enforces (a
late `heartbeat_attempt_execution` here and a `finish_attempt_execution`
called by the recovery path can never both win — the loser gets a real
`StaleState`, never a silent overwrite).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .executor import ExecutorAdapter, ExecutorPreflight
from .operational_state import Actor, OperationalStateStore


def now_iso() -> str:
    """A real canonical UTC timestamp, in the exact format `operational_state.py`'s own `_timestamp` requires."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def iso_plus(seconds: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _add_seconds(timestamp: str, seconds: float) -> str:
    """Extend a real canonical UTC timestamp by a real duration — always
    strictly later than ``timestamp`` itself (given ``seconds > 0``),
    regardless of how it compares to wall-clock now. Real bug this
    fixes: computing a heartbeat's new lease expiry as ``iso_plus(...)``
    (fresh from now) could land *before* an already-generous lease's own
    current expiry, and `heartbeat_attempt_execution` correctly rejects
    a heartbeat that doesn't advance it — extending from the lease's own
    last known expiry instead makes forward progress unconditional.
    """
    parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    return (parsed + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


@dataclass(frozen=True)
class DispatchRequest:
    """Real facts identifying one already-claimed, ready-to-run attempt.

    The caller (whatever already ran `claim_packet_assignment`) supplies
    the real current versions and the real lease id — this class does
    not claim an assignment itself, only drives one that already exists.
    """

    attempt_id: str
    lease_id: str
    expected_attempt_version: int
    expected_packet_version: int
    expected_lease_version: int
    expected_lease_expires_at: str
    preflight: ExecutorPreflight
    instructions: str
    expected_result: str
    expected_branch: str


@dataclass(frozen=True)
class DispatchResult:
    outcome: str
    """``"Succeeded"`` or ``"Failed"`` — never invented from silence."""
    result_commit: str | None
    execution_handle: str
    attempt_version: int
    packet_version: int
    lease_version: int


class DispatchOrchestrator:
    def __init__(
        self,
        store: OperationalStateStore,
        executor: ExecutorAdapter,
        actor: Actor,
        *,
        heartbeat_interval_seconds: float = 30.0,
        lease_extension_seconds: float = 600.0,
        poll_interval_seconds: float = 5.0,
    ) -> None:
        if heartbeat_interval_seconds <= 0 or poll_interval_seconds <= 0 or lease_extension_seconds <= 0:
            raise ValueError("orchestrator intervals must be positive")
        self._store = store
        self._executor = executor
        self._actor = actor
        self._heartbeat_interval_seconds = heartbeat_interval_seconds
        self._lease_extension_seconds = lease_extension_seconds
        self._poll_interval_seconds = poll_interval_seconds

    def run(self, request: DispatchRequest) -> DispatchResult:
        handle = self._executor.submit(request.preflight, request.instructions)

        started = self._store.start_attempt_execution(
            request.attempt_id,
            request.expected_attempt_version,
            request.expected_packet_version,
            handle,
            request.expected_result,
            _reason("EXECUTOR_LAUNCHED"),
            f"start-{request.attempt_id}-{handle}",
            self._actor,
            now_iso(),
        )
        attempt_version = int(started["attempt"]["version"])
        packet_version = int(started["packet"]["version"])
        lease_version = request.expected_lease_version
        lease_expires_at = request.expected_lease_expires_at

        last_heartbeat = time.monotonic()
        while True:
            observation = self._executor.observe(handle)
            if not observation.running:
                break
            if time.monotonic() - last_heartbeat >= self._heartbeat_interval_seconds:
                new_expiry = _add_seconds(lease_expires_at, self._lease_extension_seconds)
                beat = self._store.heartbeat_attempt_execution(
                    request.attempt_id,
                    attempt_version,
                    lease_version,
                    handle,
                    new_expiry,
                    _reason("WORKER_ALIVE"),
                    f"heartbeat-{request.attempt_id}-{int(time.time() * 1000)}",
                    self._actor,
                    now_iso(),
                )
                attempt_version = int(beat["attempt"]["version"])
                lease_version = int(beat["lease"]["version"])
                lease_expires_at = new_expiry
                last_heartbeat = time.monotonic()
            time.sleep(self._poll_interval_seconds)

        handoff = self._executor.retrieve_evidence(handle, branch_name=request.expected_branch)
        succeeded = handoff.completed and handoff.commit_sha is not None
        outcome = "Succeeded" if succeeded else "Failed"
        evidence_reference = str(request.preflight.worktree_path.parent / f"{handle}.log")

        finished = self._store.finish_attempt_execution(
            request.attempt_id,
            attempt_version,
            packet_version,
            lease_version,
            handle,
            outcome,
            handoff.commit_sha if succeeded else None,
            evidence_reference,
            _reason("WORK_COMPLETED" if succeeded else "EXECUTOR_REPORTED_FAILURE"),
            f"finish-{request.attempt_id}-{handle}",
            self._actor,
            now_iso(),
        )
        return DispatchResult(
            outcome=outcome,
            result_commit=handoff.commit_sha if succeeded else None,
            execution_handle=handle,
            attempt_version=int(finished["attempt"]["version"]),
            packet_version=int(finished["packet"]["version"]),
            lease_version=lease_version,
        )
