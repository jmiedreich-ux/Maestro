"""Steps 3 and 4 of starting Maestro: claim a real `Dispatchable` packet
and run its real attempt. Requested 2026-09-08 after the Owner asked for
the missing commands.

**Honest scope:** `claim_packet` does not *decide* which packet or
worker — the operator names them in the request. The real scheduler
(which packet next, for which worker) was designed at M0
(`agent-workforce-control-plane.md`) and never built in any milestone;
this command turns the manual `claim_packet_assignment` call this
session typed by hand into a real command, nothing more. Every real
version number is read from the store's own snapshots, never re-typed.

`run_attempt` drives M4.01's real `DispatchOrchestrator` against a real
`ExecutorAdapter` (the local `qwen` CLI by default; overridable so a
real subprocess stand-in can prove the path without Ollama installed).
It blocks for the attempt's whole real duration.
"""

from __future__ import annotations

from pathlib import Path

from .dispatch_orchestrator import DispatchOrchestrator, DispatchRequest, DispatchResult, iso_plus
from .executor import ExecutorAdapter, ExecutorPreflight, LocalQwenExecutorAdapter
from .operational_state import Actor, InvalidRecord, OperationalStateStore


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


def claim_packet(store: OperationalStateStore, request: dict, actor: Actor, now: str) -> dict:
    """Real claim. ``request``: ``packet_id``, ``lease`` (``lease_id``,
    ``holder_id``, ``executor_route``, ``worktree_path``,
    ``expires_in_seconds``), ``locks`` (list of ``lock_id``/``lock_kind``/
    ``resource_key``), ``attempt`` (``attempt_id``, ``model_identity``,
    ``runtime_identity``). The packet's real current version comes from
    the store, not the request."""
    packet = store.snapshot("Packet", request["packet_id"])
    if packet is None:
        raise InvalidRecord(f"unknown packet: {request['packet_id']}")
    # Real, found via a real failure: a claim requires a Running run,
    # and register-project leaves it Planned. The first claim is the
    # moment real work begins, so start the run here (Planned -> Running
    # is always legal per _RUN_TRANSITIONS).
    run = store.snapshot("Run", packet["run_id"])
    if run is not None and run["state"] == "Planned":
        store.transition_run(
            run["run_id"], run["version"], "Running", _reason("FIRST_CLAIM"),
            f"run-running-{run['run_id']}", actor, now,
        )
    lease_request = dict(request["lease"])
    expires_in = lease_request.pop("expires_in_seconds", 3600)
    lease = {**lease_request, "expires_at": iso_plus(expires_in)}
    return store.claim_packet_assignment(
        request["packet_id"], packet["version"], lease, list(request["locks"]), dict(request["attempt"]),
        _reason("OPERATOR_CLAIM"), f"claim-{request['attempt']['attempt_id']}", actor, now,
    )


def run_attempt(
    store: OperationalStateStore, request: dict, actor: Actor, *, executor: ExecutorAdapter | None = None,
) -> DispatchResult:
    """Real execution of one already-claimed attempt. ``request``:
    ``attempt_id``, ``instructions``; optional ``heartbeat_interval_
    seconds``, ``lease_extension_seconds``, ``poll_interval_seconds``.
    Everything else (packet, lease, versions, paths, branch, model) is
    read from the store's own real rows."""
    attempt = store.snapshot("Attempt", request["attempt_id"])
    if attempt is None:
        raise InvalidRecord(f"unknown attempt: {request['attempt_id']}")
    packet = store.snapshot("Packet", attempt["packet_id"])
    lease = store.snapshot("Lease", attempt["lease_id"])
    if packet is None or lease is None:
        raise InvalidRecord("attempt is missing its real packet or lease")

    preflight = ExecutorPreflight(
        base_commit=packet["base_commit"],
        worktree_path=Path(lease["worktree_path"]),
        allowed_paths=tuple(packet["owned_paths_json"]),
        forbidden_paths=tuple(packet["forbidden_paths_json"]),
        model_identity=attempt["model_identity"],
    )
    dispatch = DispatchRequest(
        attempt_id=attempt["attempt_id"],
        lease_id=lease["lease_id"],
        expected_attempt_version=attempt["version"],
        expected_packet_version=packet["version"],
        expected_lease_version=lease["version"],
        expected_lease_expires_at=lease["expires_at"],
        preflight=preflight,
        instructions=request["instructions"],
        expected_result="AwaitingIntegration",
        expected_branch=packet["expected_branch"],
    )
    orchestrator = DispatchOrchestrator(
        store, executor or LocalQwenExecutorAdapter(), actor,
        heartbeat_interval_seconds=request.get("heartbeat_interval_seconds", 30.0),
        lease_extension_seconds=request.get("lease_extension_seconds", 600.0),
        poll_interval_seconds=request.get("poll_interval_seconds", 5.0),
    )
    return orchestrator.run(dispatch)
