"""The real "start Maestro" path, requested 2026-09-08 after the Owner
asked for plain steps to start it and there was no real command for
either of the first two: register a real project, and create a real
packet. Both existed only as Python call sequences this session typed
by hand (`m4_fixtures.py`'s own setup); this module is that sequence,
made callable and CLI-exposed (`cli.py`'s `register-project` and
`materialize-packet` commands).

**Real, disclosed gap this does not close:** claiming a materialized
packet (`Dispatchable -> Leased`, real lease/lock/attempt allocation)
still has no command — that is a real resource-allocation decision
(M3's own territory), not addressed here. `materialize_and_ready_packet`
gets a packet to real `Dispatchable`; a human (or a future real
dispatcher) still claims and dispatches it before
`development-manager-loop` (M4.17) has anything to drive.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .config import RuntimeConfig
from .operational_state import Actor, OperationalStateStore
from .project_authority import ProjectAuthorityLoader
from .storage import SQLiteFoundation


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


def register_project(
    foundation: SQLiteFoundation, store: OperationalStateStore, request: dict, actor: Actor, now: str,
) -> dict:
    """Real registration: loads real project authority from the real
    repository at ``request['commit']`` (or real current HEAD if
    omitted), records the real binding, registers the project, records
    a real graph projection with its real work items, and creates the
    real run. Returns ``{"binding": ..., "graph_projection": ...,
    "run": ...}``. Every field the loader itself derives (source_commit,
    manifest_digest, authority_reference) is filled in here, never
    re-typed by the caller."""
    repository_path = Path(request["repository_path"])
    commit = request.get("commit") or _resolve_head(repository_path)
    load_result = ProjectAuthorityLoader(foundation).load(
        repository_path, commit, request["github_reference"],
    )

    binding_request = request["binding"]
    binding_row = {
        **binding_request,
        "project_id": request["project_id"],
        "source_commit": load_result.source_commit,
        "manifest_digest": load_result.manifest_digest,
        "authority_reference": load_result.request_id,
        "activated_at": None,
        "superseded_at": None,
    }
    binding = store.record_binding(binding_row, f"register-binding-{binding_row['binding_id']}", actor, now)
    foundation.register_project(request["project_id"], binding_row["binding_id"])

    graph_request = request["graph"]
    work_items = [
        {**item, "graph_projection_id": graph_request["graph_projection_id"]}
        for item in request["work_items"]
    ]
    source_hash = hashlib.sha256(
        (graph_request["graph_projection_id"] + "".join(sorted(item["work_item_id"] for item in work_items))).encode("utf-8")
    ).hexdigest()
    graph_row = {
        **graph_request,
        "project_id": request["project_id"],
        "binding_id": binding_row["binding_id"],
        "authority_reference": load_result.request_id,
        "source_base_sha": load_result.source_commit,
        "source_hash": source_hash,
        "observed_at": now,
    }
    graph_projection = store.record_graph_projection(
        graph_row, work_items, f"register-graph-{graph_row['graph_projection_id']}", actor, now,
    )

    run_request = request["run"]
    run_row = {
        **run_request,
        "run_fingerprint": hashlib.sha256(run_request["run_id"].encode("utf-8")).hexdigest(),
        "project_id": request["project_id"],
        "binding_id": binding_row["binding_id"],
        "graph_projection_id": graph_row["graph_projection_id"],
        "approved_authority_reference": load_result.request_id,
        "current_head": None,
        "current_head_source_reference": None,
        "candidate_head": None,
        "candidate_head_source_reference": None,
        "state": "Planned",
    }
    run = store.create_run(run_row, f"register-run-{run_row['run_id']}", actor, now)

    return {"binding": binding, "graph_projection": graph_projection, "run": run}


def _resolve_head(repository_path: Path) -> str:
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(repository_path), "rev-parse", "HEAD"],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.decode("ascii").strip()


def materialize_and_ready_packet(store: OperationalStateStore, request: dict, actor: Actor, now: str) -> dict:
    """Real packet creation: materializes the packet, then walks it
    through the real, mechanical, always-legal eligibility chain
    (`Planned -> Waiting -> Ready -> Dispatchable`) -- exactly the same
    three transitions `m4_fixtures.py`'s own setup performed by hand,
    now callable directly. Stops at `Dispatchable`; claiming is real,
    disclosed, out-of-scope follow-up (see this module's own docstring).
    """
    packet = store.materialize_packet(request, f"materialize-{request['packet_id']}", actor, now)
    version = packet["version"]
    for target in ("Waiting", "Ready", "Dispatchable"):
        result = store.transition_packet_eligibility(
            request["packet_id"], version, target, _reason("PACKET_READY"),
            f"ready-{request['packet_id']}-{target}", actor, now,
        )
        version = result["version"]
    return result
